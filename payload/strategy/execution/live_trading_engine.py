"""Motor de trading en vivo: el bucle central que convierte análisis en órdenes.

Modulo mas grande del proyecto y corazon operativo del bot. Coordina todo lo
que ocurre entre "hay datos de mercado" y "hay una posicion gestionada":

1. Selecciona que simbolos analizar en cada ciclo (perfiles por worker).
2. Pide el analisis multi-temporal a `MultiTimeframeAnalyzer`.
3. Aplica las PUERTAS DE ENTRADA (gates): politica de direccion, noticias de
   alto impacto, rollover, limites de posiciones, cuarentena de simbolos.
4. Consulta al motor de IA de meta-etiquetado, que puede puntuar en sombra,
   filtrar por probabilidad o priorizar entre senales simultaneas.
5. Dimensiona el riesgo y ejecuta a traves del `TradeExecutor` configurado.
6. Vigila las posiciones abiertas: break-even, trailing, extension del runner
   y cierres defensivos.

CONCEPTO CRITICO — CIERRES ESTRUCTURALES: los cierres anticipados deben
responder a una invalidacion real de la tesis (direccion opuesta, BOS/CHOCH
contrario, bloqueo HTF o fallo estructural critico). Los estados de
antiguedad de senal como `STALE_M5_SIGNAL` significan "ya no procede ABRIR
aqui" y NO se usan para cerrar lo que ya esta abierto.

CUARENTENA: un simbolo que provoca errores repetidos se aparta durante un
tiempo, guardando el estado en disco para que sobreviva a un reinicio.

MULTI-WORKER: varias instancias pueden correr en paralelo sobre perfiles de
simbolos distintos, por lo que la cuarentena y los limites de posicion usan
bloqueos y ficheros compartidos.

Vinculaciones:
- Consume `strategy.execution.multi_timeframe` para el analisis.
- Consume `strategy.ai` (meta-etiquetado, ranking) antes de ejecutar.
- Ejecuta via `strategy.execution.trade_executor` y sus implementaciones.
- Registra estados en `trade_lifecycle_manager` y persiste en `database`.
- Usa `config.symbol_policy`, `services.financial_news_service`,
  `strategy.orb.new_york_orb` y `strategy.execution.runner_extension_manager`.
"""

from __future__ import annotations

import sys
import os

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import time
import json
import threading
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig
from strategy.execution.trade_pipeline import PipelineConfig
from config.symbol_policy import direction_policy_diagnostics, is_direction_allowed, get_symbol_direction_policy
from dashboard.smc_visual_context import build_smc_visual_context
from strategy.execution.runner_extension_manager import (
    evaluate_runner_continuation,
    rr_price,
)
from strategy.orb.new_york_orb import (
    ORBConfig,
    NewYorkORBStrategy,
    classify_orb_market,
    is_orb_eligible_symbol,
    is_orb_gold_symbol,
    score_orb_gold_contract_candidate,
)
from strategy.indices.ny_index_open import (
    NYIndexOpenConfig,
    NYIndexOpenStrategy,
    is_ny_index_open_symbol,
)
from services.financial_news_service import load_economic_calendar_state
from strategy.ai import (
    MetaLabelingConfig,
    MetaLabelingEngine,
    RANKING_MODE,
    rank_signals,
)
from strategy.smc.exhaustion_reversal import (
    ExhaustionReversalConfig,
    detect_exhaustion_reversal,
)


_QUARANTINE_PROCESS_LOCK = threading.RLock()


@dataclass
class LiveTradingConfig:
    """Configuración completa del motor de trading en vivo.

    Reune en un unico objeto todos los parametros ajustables del bot. Los
    valores por defecto son los de produccion; cada worker puede sobrescribir
    los que necesite.

    Bloques principales:
    - Marcos y numero de velas por temporalidad (H1/M15/M5).
    - Riesgo: porcentaje, base equity/balance, tolerancias y topes duros de
      margen. Existe un tope POST-fill: si el riesgo real de la posicion
      supera el margen, se cierra de inmediato y el simbolo va a cuarentena.
    - Cuarentena: ruta de persistencia y ventanas de recuperacion para
      incidentes marginales frente a los que exigen intervencion manual.
    - Gestion activa: break-even con desplazamiento protector, trailing,
      extension de runner y cadencias del monitor en segundo plano.
    - Puertas de entrada: RR minimo, noticias, rollover y limites de posiciones.
    - Meta-etiquetado de IA: modo (sombra, filtro, ranking) y umbrales.

    Vinculaciones:
    - La instancia `LiveTradingEngine` la recibe en su constructor.
    - Parte de sus campos se traducen a `MultiTimeframeConfig` y
      `PipelineConfig` para configurar el analisis.
    """

    source: str = "DEMO"
    higher_timeframe: str = "H4"
    structure_timeframe: str = "H1"
    confirmation_timeframe: str = "M15"
    entry_timeframe: str = "M5"
    higher_timeframe_candle_count: int = 500
    require_h4_h1_convergence: bool = True
    structure_candle_count: int = 500
    # Los lookbacks máximos efectivos del pipeline son 100 velas (liquidez,
    # premium/discount) + 50 para retest. 500 M15 y 350 M5 conservan margen de
    # calentamiento y toda validación estructural, evitando recalcular 1000
    # velas por símbolo en cada cierre M5.
    confirmation_candle_count: int = 500
    entry_candle_count: int = 350
    risk_percent: float = 1.0
    risk_base: str = "EQUITY"  # EQUITY o BALANCE
    max_actual_risk_tolerance: float = 0.01
    # Reservamos 1% del presupuesto antes del fill para absorber el pequeño
    # desplazamiento entre precio de cálculo y ejecución real. El hard cap no
    # cambia: esta reserva reduce emergencias, no autoriza más riesgo.
    pre_fill_risk_buffer: float = 0.0
    # Hard cap post-fill: si el riesgo real de la posición supera este margen,
    # se cierra inmediatamente y el símbolo queda en cuarentena.
    # Subido de 0.02 a 0.035 tras incidente real en Step Index 500 (exceso
    # 2.36% por granularidad de lote minimo del broker, quedaba en cuarentena
    # temporal pese a ser un desvio mecanico normal de ejecucion).
    hard_risk_tolerance: float = 0.035
    emergency_risk_exit_enabled: bool = True
    quarantine_enabled: bool = True
    quarantine_path: str = "storage/risk_quarantine.json"
    # Un breach marginal compatible con granularidad/slippage se mantiene
    # bloqueado temporalmente y se reintenta más tarde. Incidentes reales por
    # encima del umbral adicional siguen requiriendo intervención manual.
    recoverable_quarantine_minutes: float = 60.0
    # Margen adicional (sumado al hard_risk_tolerance) hasta el cual un
    # breach post-fill se auto-recupera sin revision manual.
    recoverable_quarantine_extra_tolerance: float = 0.015
    # Exigimos que el volumen realmente ejecutable se acerque al riesgo objetivo.
    # Si el máximo de lotes del broker impide llegar al umbral, rechazamos la operación
    # en lugar de abrirla con un tamaño arbitrariamente grande o con un riesgo muy distinto.
    min_actual_risk_ratio: float = 0.99
    # Límite defensivo de margen requerido sobre la base de riesgo (equity/balance).
    max_margin_fraction: float | None = 0.15

    # Gestión activa de posiciones DEMO.
    break_even_enabled: bool = True
    break_even_trigger_rr: float = 1.0
    # BE protector: desplaza el SL hacia beneficio para cubrir spread/costes.
    break_even_offset_points: int = 2
    # v105: el BE clásico (entrada + spread/offset) solo evita pérdida, pero no
    # asegura ninguna ganancia real. Los 8 cierres BREAKEVEN observados en la
    # cuenta real cerraron con ~0.03R en promedio pese a haber alcanzado 1R de
    # favor. Bloqueamos una fracción del riesgo inicial como ganancia mínima
    # al activar el BE, para que "asegurar operación" también capture parte de
    # la ganancia ya alcanzada, no solo cubra costes.
    break_even_profit_lock_rr_fraction: float = 0.3
    break_even_confirmation_retries: int = 3
    break_even_confirmation_delay_seconds: float = 0.20
    orb_correlated_entry_min_break_even_offset_points: int = 2
    # El monitor pesado se ejecuta en un hilo independiente del scanner de
    # señales. Así una sincronización lenta de SQLite/MT5 no envejece M5/M1.
    background_position_monitor_enabled: bool = True
    position_monitor_audit_interval_seconds: float = 30.0
    strategy_evaluation_audit_interval_seconds: float = 300.0
    # v104: mitigación del arranque en frío. El primer ciclo tras iniciar el
    # worker no tiene ninguna etapa H1/M15/M5 en caché, así que analiza todos
    # los símbolos desde cero y es estructuralmente más lento que el resto.
    # Escalonar ese ciclo evita saturar al broker con ráfagas simultáneas de
    # peticiones, y excluirlo del aviso de overrun refleja que su duración es
    # esperada, no una degradación del intervalo objetivo.
    cold_start_batch_size: int = 5
    cold_start_batch_delay_seconds: float = 0.5
    cold_start_exclude_from_overrun: bool = True
    # La gestión de SL/BE conserva su frecuencia rápida, pero los cuatro marcos
    # visuales se reconstruyen con menor cadencia en el hilo del monitor.
    visual_audit_refresh_seconds: float = 30.0

    min_rr: float = 1.5
    stop_safety_points: int = 2
    validate_order_in_dry_run: bool = True

    # Límites de riesgo para ejecución real/demo.
    # Se mantiene max_open_positions por compatibilidad con configuraciones anteriores.
    # Cada setup se ejecuta en dos piernas (TP1 + RUNNER). Por eso 6 posiciones
    # equivalen a un máximo de 3 operaciones lógicas simultáneas.
    max_open_positions: int = 6
    max_total_open_positions: int | None = None
    max_open_positions_per_symbol: int = 2

    # Gestión 50/50 del riesgo de una operación lógica.
    split_entries_enabled: bool = True
    split_entry_risk_fraction: float = 0.50
    first_target_rr: float = 1.0
    second_target_rr: float = 2.0
    # Si el broker no permite dividir el 1% en dos piernas seguras, intentamos
    # una sola entrada de hasta 1% con TP 2R y BE+2 puntos al alcanzar 1R.
    single_entry_fallback_enabled: bool = True
    single_entry_target_rr: float = 2.0

    # Los perfiles SMC sintéticos cierran el runner en TP2. Las extensiones
    # siguientes se reservan para estrategias que las habiliten explícitamente.
    runner_extension_enabled: bool = False
    runner_extension_first_trigger_rr: float = 2.0
    runner_extension_first_lock_rr: float = 1.0
    runner_extension_second_trigger_rr: float = 3.0
    runner_extension_second_lock_rr: float = 2.0
    runner_extension_max_target_rr: float = 2.0
    smc_runner_max_target_rr: float = 2.0
    # Protección intermedia mientras busca TP3.
    smc_runner_tp3_guard_trigger_rr: float = 2.5
    smc_runner_tp3_guard_lock_rr: float = 2.0
    # Protección intermedia mientras busca TP4.
    smc_runner_tp4_guard_trigger_rr: float = 3.5
    smc_runner_tp4_guard_lock_rr: float = 3.0

    # v73: Forex usa objetivos lógicos progresivos aunque el broker conserve
    # un TP4 máximo como fail-safe. El runner nace buscando TP2.
    forex_runner_initial_target_rr: float = 2.0
    forex_runner_tp3_lock_rr: float = 1.0
    forex_runner_tp4_pre_eval_lock_rr: float = 2.0
    forex_runner_tp4_lock_rr: float = 2.5
    forex_runner_max_target_rr: float = 2.0
    forex_runner_broker_safety_target_rr: float = 2.0

    runner_extension_timeframe: str = "M5"
    runner_extension_candle_count: int = 80
    excursion_persist_step_rr: float = 0.05
    # v67: reevaluación MTF de posiciones SMC abiertas para "Entrada vs. ahora".
    current_strategy_refresh_seconds: float = 10.0
    # v95: salida defensiva únicamente cuando la reevaluación vigente invalida
    # la tesis en velas M5 cerradas distintas y consecutivas. No sustituye el
    # SL estructural ni cierra por una lectura aislada.
    # v105: el criterio de cierre ya NO exige alcanzar un RR de pérdida
    # mínimo (antes -0.35R): basta con que la invalidación estructural quede
    # confirmada (`analysis_invalidation_confirmations` velas consecutivas)
    # para salir de inmediato, sin esperar a que la pérdida crezca. El campo
    # `analysis_invalidation_exit_rr` se conserva solo por compatibilidad de
    # configuraciones/metadata antiguas; ya no gatea el cierre.
    # v106: `analysis_invalidation_confirmations` ahora cuenta velas M15
    # cerradas (más contexto), no M5. El comportamiento del precio que
    # determina si la tesis se invalidó sigue analizándose en M5.
    analysis_invalidation_exit_enabled: bool = True
    analysis_invalidation_exit_rr: float = -0.35
    analysis_invalidation_confirmations: int = 2
    analysis_invalidation_min_open_minutes: float = 10.0
    # Si una operación dañada recupera al menos +0.20R, no permitimos que vuelva
    # hasta el SL completo mientras la tesis actual siga inválida.
    analysis_recovery_mfe_rr: float = 0.20
    analysis_recovery_exit_rr: float = -0.10
    # FLIP: protege el capital después de una extensión moderada sólo cuando
    # el análisis M1 confirma la reversión.
    flip_reversal_protection_enabled: bool = True
    flip_reversal_protection_trigger_rr: float = 0.50

    # v101: meta-etiquetado con IA. Cada worker entrena y puntúa por separado.
    # SHADOW puntúa sin bloquear; FILTER exige probabilidad y expectativa neta.
    meta_labeling_enabled: bool = True
    # Se mantiene SHADOW por seguridad. RANKING/FILTER sólo se activan de
    # forma explícita por entorno, sin editar el código de cada worker.
    meta_labeling_mode: str = os.getenv(
        "DAEMONBLACKFX_META_LABELING_MODE", "SHADOW"
    ).upper()
    meta_labeling_min_probability: float = 0.55
    meta_labeling_min_net_expectancy_r: float = 0.10
    meta_labeling_ranking_enabled: bool = True
    meta_labeling_max_signals_per_cycle: int = 1
    meta_labeling_model_directory: str = "storage/ai_models"
    meta_labeling_min_training_samples: int = 30

    # v69: scheduler Forex por nueva vela cerrada M5.
    forex_event_scheduler_enabled: bool = True
    orb_event_scheduler_enabled: bool = True
    forex_event_timeframe: str = "M5"
    forex_event_poll_seconds: float = 10.0
    # v110: después de comprobar la vela vigente, no se vuelve a consultar
    # cada símbolo hasta la próxima frontera M5 (+ gracia de publicación).
    # El monitor de posiciones conserva intacta su cadencia de 2 segundos.
    event_scheduler_boundary_guard_enabled: bool = True
    event_scheduler_boundary_grace_seconds: float = 2.0
    # v93: todos los perfiles SMC analizan una sola vez cada vela M5 cerrada.
    # ORB mantiene su scheduler de sesión independiente.
    smc_event_scheduler_enabled: bool = True
    # v111: detector adicional de reversión por agotamiento. SHADOW significa
    # que registra candidatos pero jamás los convierte en órdenes.
    exhaustion_reversal_enabled: bool = True
    exhaustion_reversal_mode: str = "SHADOW"
    exhaustion_dealing_range_lookback: int = 50
    exhaustion_liquidity_lookback: int = 20
    exhaustion_premium_threshold: float = 0.75
    exhaustion_discount_threshold: float = 0.25
    exhaustion_minimum_wick_ratio: float = 0.45
    exhaustion_maximum_body_ratio: float = 0.35
    exhaustion_volume_climax_multiplier: float = 1.20
    # Sin posiciones SQLite del perfil, el monitor evita consultar MT5 cada 2s.
    idle_position_recovery_seconds: float = 30.0

    # v87: Oro con estrategia SMC/Forex desde apertura de Asia (Tokio 09:00)
    # hasta apertura cash de Nueva York (09:30), ambas con DST real por zona.
    gold_smc_session_enabled: bool = True
    gold_asia_timezone: str = "Asia/Tokyo"
    gold_asia_open_hour: int = 9
    gold_asia_open_minute: int = 0
    gold_london_timezone: str = "Europe/London"
    gold_london_open_hour: int = 8
    gold_london_close_hour: int = 12
    gold_new_york_timezone: str = "America/New_York"
    gold_new_york_open_hour: int = 9
    gold_new_york_open_minute: int = 30
    gold_take_profit_at_new_york_rr: float = 1.0
    gold_break_even_positive_at_new_york: bool = True
    # v107: modelo "Asian Range + sweep" para GOLD (ver PipelineConfig en
    # trade_pipeline.py). Solo se activa cuando bot_profile == GOLD.
    # v109: desactivado por defecto. Analisis de logs de produccion mostro
    # que GOLD perdia el 28.4% de sus ciclos activos en `NO_M15_SETUP` (vs.
    # solo 5.6% en Forex, que no tiene este filtro), es decir, este filtro
    # exigia que el barrido de liquidez coincidiera casi exacto ($2 de
    # tolerancia) con el low/high de la sesion asiatica (22:00-06:00 UTC)
    # para validar el setup, descartando barridos legitimos sobre otros
    # pivotes. Se conserva el campo (y toda su logica en trade_pipeline.py)
    # por si se quiere reactivar para pruebas futuras.
    gold_asian_range_sweep_enabled: bool = False
    gold_asian_range_tolerance_price: float = 2.0

    # Riesgo agregado Forex compartido vía SQLAlchemy.
    # Una divisa no puede acumular más de 1% de riesgo lógico abierto.
    # Las dos piernas de una operación (0.50% + 0.50%) se cuentan como una
    # sola operación lógica para no penalizar la división TP1 + Runner.
    forex_max_currency_exposure_percent: float = 1.0
    forex_max_total_risk_percent: float = 4.0
    forex_high_impact_news_guard_enabled: bool = True
    forex_high_impact_news_before_minutes: int = 15
    forex_high_impact_news_after_minutes: int = 15
    forex_high_impact_news_calendar_path: str = "storage/dashboard/financial_news.json"
    # v85: ORB ya no usa un techo global de 1%. Sólo evita duplicar exposición
    # entre S&P 500 y Nasdaq 100 hasta que la primera operación tenga BE real.
    orb_equity_correlation_guard_enabled: bool = True
    orb_correlated_entry_requires_break_even: bool = True

    # v41: Jump queda habilitado, pero bajo un filtro de calidad más estricto.
    jump_strict_filter_enabled: bool = False
    jump_min_confirmation_ratio: float = 0.90
    jump_min_trade_score: float = 90.0
    jump_require_rejection: bool = True
    jump_require_micro_structure: bool = True
    jump_require_displacement: bool = True
    jump_require_strong_close: bool = True
    jump_allow_single_fallback: bool = False

    magic: int = 26082026
    bot_profile: str = "SYNTHETICS"
    deviation: int = 20
    # Confluencia armónica + SMC usada por el daemon. El patrón armónico no
    # genera entradas por sí solo: debe confirmar la dirección y la PRZ del setup SMC.
    harmonic_enabled: bool = True
    harmonic_tolerance: float = 0.10
    harmonic_minimum_score: float = 75.0
    harmonic_bonus_points: float = 10.0
    require_harmonic: bool = False
    adaptive_confirmation_enabled: bool = True
    minimum_confirmation_ratio: float = 0.80
    minimum_viable_trade_score: float = 75.0
    divergence_enabled: bool = True
    divergence_rsi_period: int = 14
    divergence_lookback_candles: int = 80
    divergence_bonus_points: float = 5.0

    # Patrones chartistas: una tesis alineada y sin conflicto es obligatoria.
    chart_patterns_enabled: bool = True
    chart_patterns_lookback: int = 80
    chart_patterns_pivot_window: int = 2
    chart_patterns_price_tolerance: float = 0.006
    chart_patterns_volatility_adjusted_tolerance: bool = True
    chart_patterns_price_tolerance_range_multiplier: float = 1.50
    chart_patterns_minimum_price_tolerance: float = 0.00010
    chart_patterns_minimum_strength: float = 0.72
    chart_patterns_bonus_points: float = 8.0
    require_chart_pattern: bool = False
    chart_pattern_secondary_conflict_penalty: float = 10.0
    block_material_chart_pattern_conflict: bool = True
    # v108: margen mínimo (fracción 0-1) que el patrón chartista alineado con
    # la dirección deseada debe superar al contrario para no bloquear la
    # entrada. Ver detalle en confirmation_engine.M5ConfirmationConfig.
    # v109 Fase 2: bajado de 0.25 a 0.18 (relajación de gate estructural,
    # ver comentario completo en confirmation_engine.M5ConfirmationConfig).
    chart_pattern_conflict_min_margin: float = 0.18
    chart_pattern_contrary_min_strength: float = 0.80
    chart_pattern_contrary_min_advantage: float = 0.10
    # v109 Fase 1: bajado de 0.30 a 0.25. Configurable por perfil de bot;
    # ver comentario completo en confirmation_engine.M5ConfirmationConfig.
    minimum_rejection_wick_ratio: float = 0.25
    # v109 Fase 3: bajado de 1.35 a 1.20. Configurable por perfil de bot;
    # ver comentario completo en confirmation_engine.M5ConfirmationConfig.
    displacement_range_multiplier: float = 1.20
    block_similar_chart_pattern_forces: bool = True
    fvg_enabled: bool = True
    fvg_lookback: int = 30
    fvg_max_age_candles: int = 10
    fvg_require_alignment_with_zone: bool = False
    fvg_bonus_points: float = 6.0
    require_fvg: bool = False

    # v107: confirmación de convicción por volumen de la vela M5 de
    # confirmación (ver `strategy.smc.volume_confirmation`). Compara el
    # volumen de esa vela contra el promedio de `volume_confirmation_lookback`
    # velas previas; se exige alcanzar al menos
    # `volume_confirmation_spike_multiplier` veces ese promedio.
    #
    # OBLIGATORIA (`require_volume_confirmation=True`) en las 4 estrategias
    # por defecto: sin participación de volumen medible, la entrada se
    # rechaza igual que le pasaría a un FVG o patrón chartista ausente
    # cuando esos son obligatorios.
    #
    # CÓMO DESACTIVARLA (por perfil, sin tocar código de motor):
    # - `volume_confirmation_enabled=False`: apaga la confluencia por
    #   completo (no aporta bonus ni bloquea).
    # - `require_volume_confirmation=False`: la deja activa solo como bonus
    #   de score opcional, sin bloquear la entrada si falta.
    # - `volume_confirmation_skip_gate_without_reliable_volume=True`
    #   (default): si el símbolo/broker no publica ninguna columna de
    #   volumen real (`real_volume`/`tick_volume`/`volume` con suma > 0,
    #   común en algunos sintéticos), el gate NO rechaza por esa ausencia de
    #   dato; solo se pierde el bonus de score.
    volume_confirmation_enabled: bool = True
    volume_confirmation_lookback: int = 20
    volume_confirmation_spike_multiplier: float = 1.0
    volume_confirmation_bonus_points: float = 5.0
    require_volume_confirmation: bool = True
    volume_confirmation_skip_gate_without_reliable_volume: bool = True

    # Confirmación adicional H1: Doji reciente en extremos relevantes.
    h1_doji_enabled: bool = True
    h1_doji_lookback_candles: int = 100
    h1_doji_max_age_candles: int = 2
    h1_doji_max_body_ratio: float = 0.10
    h1_doji_extreme_fraction: float = 0.15
    h1_doji_min_rejection_wick_ratio: float = 0.35
    h1_doji_bonus_points: float = 5.0

    # v107: retest limpio validado con overshoot real (no fijo en True), patrón
    # chartista y FVG obligatorios en las 4 estrategias, sin killzones/filtro
    # horario forzado en Sintéticos/Forex, niveles de cuartos en Gold/ORB solo
    # para XAUUSD/microXAUUSD. Nueva frontera PRE/POST (ver
    # `tools/winrate_pre_post_report.py` y `POST_IMPROVEMENT_MIN_VERSION`).
    # v109 (11-09-2026): relajación medida de 3 gates estructurales que
    # concentraban el 47%-77% de los rechazos en Sintéticos/Forex (análisis
    # de 27.816 evaluaciones reales en storage/logs/bots/*.log):
    #   Fase 1: minimum_rejection_wick_ratio        0.30 -> 0.25
    #   Fase 2: chart_pattern_conflict_min_margin    0.25 -> 0.18
    #   Fase 3: displacement_range_multiplier        1.35 -> 1.20
    # minimum_body_ratio (0.65) y clean_retest_max_overshoot_ratio (0.50) NO
    # se tocaron. Ademas, mismo dia: ORB relaja VWAP+POC (basta con que uno
    # de los dos este alineado, ver `ORBConfig.vwap_poc_require_both`) y GOLD
    # desactiva el filtro "Asian Range + sweep" (`gold_asian_range_sweep_enabled`
    # False), que bloqueaba el 28.4% de sus ciclos activos en NO_M15_SETUP
    # (vs. 5.6% en Forex, que no lo usa). Nueva frontera PRE/POST para medir
    # el efecto real con `tools/winrate_pre_post_report.py` una vez se
    # acumulen operaciones.
    strategy_version: str = "smc-v109-relaxed-gates-orb-vwap-poc-gold-asian-sweep-off"


    # Segunda estrategia: Opening Range Breakout exclusivo para mercados NY autorizados.
    orb_enabled: bool = True
    orb_timeframe: str = "M5"
    # v76: contexto superior para evitar ORB contra tendencia mayor.
    orb_htf_context_enabled: bool = True
    orb_require_h1_alignment: bool = True
    orb_use_m15_context: bool = True
    orb_require_known_htf_context: bool = True
    orb_opening_range_minutes: int = 15
    orb_require_vwap_alignment: bool = True
    orb_require_poc_alignment: bool = True
    # v109: cuando VWAP y POC estan ambos activos, basta con que UNO este
    # alineado con el retest (no se exigen los dos simultaneamente). Ver
    # `ORBConfig.vwap_poc_require_both` para el detalle y el analisis de logs
    # que motivo el cambio.
    orb_vwap_poc_require_both: bool = False
    orb_poc_bins: int = 24
    orb_target_rr: float = 2.0
    # v61 ORB usa siempre 1% por operación lógica, dividido 0.5% + 0.5%.
    orb_risk_percent: float = 1.0
    orb_stop_mode: str = "MIDPOINT"
    orb_stop_buffer_fraction: float = 0.0
    orb_candle_count: int = 350
    orb_breakout_atr_buffer_fraction: float = 0.05
    orb_retest_max_candles: int = 3
    orb_strategy_version: str = "orb-ny-v2-m5-breakout-retest-midpoint"

    # Tercera estrategia: Apertura Indices Bursatiles (Wall Street 30, US
    # Tech 100, US SP 500) en la apertura de Nueva York (09:30 NY). Sesgo H1
    # 07h/08h + confirmacion M5 + doble entrada 0.5%+0.5% (TP1 1:1, TP2 1:2).
    # v109: desactivado por defecto a pedido del usuario (worker retirado de
    # la operativa activa). El código permanece intacto para poder
    # reactivarlo simplemente pasando idx_open_enabled=True de nuevo.
    idx_open_enabled: bool = False
    idx_open_confirmation_window_minutes: int = 20
    idx_open_tp1_rr: float = 1.0
    idx_open_target_rr: float = 2.0
    idx_open_strategy_version: str = "ny-index-open-v1-h1-bias-m5-confirmation"

    # v43: protección específica para Forex alrededor del rollover diario de NY.
    # Spot FX opera 24/5, pero alrededor de 17:00 New York suele disminuir la
    # liquidez y ampliarse el spread. DaemonBlackFx queda flat antes del rollover.
    forex_rollover_guard_enabled: bool = True
    forex_rollover_timezone: str = "America/New_York"
    forex_new_entry_cutoff_hour: int = 16
    forex_new_entry_cutoff_minute: int = 30
    forex_force_flat_hour: int = 16
    forex_force_flat_minute: int = 45
    # v89: Forex vuelve a habilitar entradas en la apertura de Tokio, igual que
    # GOLD. Los campos London se conservan sólo para configuraciones antiguas.
    forex_tokyo_timezone: str = "Asia/Tokyo"
    forex_tokyo_session_start_hour: int = 9
    forex_tokyo_session_start_minute: int = 0
    forex_london_timezone: str = "Europe/London"
    forex_london_session_start_hour: int = 8
    forex_london_session_start_minute: int = 0
    forex_force_flat_daily: bool = True
    forex_force_flat_friday: bool = True

    # GOLD: niveles de cuarto ($25/$50/$75/$100...) como confluencia de precio.
    gold_quarter_level_increment: float = 25.0
    gold_quarter_level_tolerance_price: float = 2.0
    gold_quarter_level_bonus_points: float = 4.0
    require_gold_quarter_level: bool = False

    # False = solo analiza y calcula la operación; no envía órdenes.
    execution_enabled: bool = False

    # En DRY_RUN normalmente queremos analizar señales aunque existan operaciones OPEN antiguas
    # en SQLite. Si se desea probar también el bloqueo, cambiar a True.
    enforce_position_limits_in_dry_run: bool = False

    diagnostic_mode: bool = True
    max_m5_signal_age_candles: int = 2
    # None = solo límite por velas. Si se define, añade un límite temporal absoluto.
    max_m5_signal_age_minutes: float | None = None

    # Máxima desviación del precio actual respecto a la entrada original, expresada en R.
    # 0.50 = no perseguir una entrada que ya se movió más de medio riesgo estructural.
    max_entry_drift_r: float | None = 0.50
    require_latest_m15_setup: bool = True


class LiveTradingEngine:
    """Motor DEMO: H1 contexto -> M15 setup -> M5 entrada -> MT5 -> SQLite.

    execution_enabled=False es un DRY RUN seguro: nunca abre una orden y, por defecto,
    tampoco bloquea el análisis por operaciones OPEN históricas guardadas en SQLite.
    """

    def __init__(
        self,
        provider,
        repository,
        config=None,
        pipeline_config=None,
        executor=None,
        lifecycle_manager=None,
        reporting_service=None,
        console_reporter=None,
        dashboard_service=None,
    ):
        """Ensambla el motor con sus dependencias e inicializa el estado interno.

        Todas las colaboraciones se inyectan, lo que permite sustituir el
        ejecutor real por uno simulado sin tocar la logica del motor.

        Args:
            provider: fuente de datos de mercado (velas, precios, cuenta).
            repository: capa de persistencia de senales y operaciones.
            config: `LiveTradingConfig`; si falta, se usan los valores por
                defecto de produccion.
            pipeline_config: `PipelineConfig` para el analisis SMC; si falta,
                se deriva de `config`.
            executor: implementacion de `TradeExecutor` que envia las ordenes.
            lifecycle_manager: `TradeLifecycleManager` que registra los
                estados de cada operacion.
            reporting_service: exportacion de informes.
            console_reporter: salida legible por consola.
            dashboard_service: publicacion de estado hacia el panel.

        Efectos: carga la cuarentena persistida desde disco, prepara los
        analizadores por temporalidad, crea el motor de meta-etiquetado de IA
        y deja listos los bloqueos que protegen el estado compartido entre
        el hilo del scanner y el del monitor de posiciones.
        """
        self.provider = provider
        self.repository = repository
        self.config = config or LiveTradingConfig()
        self.pipeline_config = pipeline_config or PipelineConfig(
            minimum_rejection_wick_ratio=float(
                getattr(self.config, "minimum_rejection_wick_ratio", 0.25)
            ),
            displacement_range_multiplier=float(
                getattr(self.config, "displacement_range_multiplier", 1.20)
            ),
            harmonic_enabled=bool(self.config.harmonic_enabled),
            harmonic_tolerance=float(self.config.harmonic_tolerance),
            harmonic_minimum_score=float(self.config.harmonic_minimum_score),
            harmonic_bonus_points=float(self.config.harmonic_bonus_points),
            require_harmonic=bool(self.config.require_harmonic),
            adaptive_confirmation_enabled=bool(self.config.adaptive_confirmation_enabled),
            minimum_confirmation_ratio=float(self.config.minimum_confirmation_ratio),
            minimum_viable_trade_score=float(self.config.minimum_viable_trade_score),
            divergence_enabled=bool(self.config.divergence_enabled),
            divergence_rsi_period=int(self.config.divergence_rsi_period),
            divergence_lookback_candles=int(self.config.divergence_lookback_candles),
            divergence_bonus_points=float(self.config.divergence_bonus_points),
            chart_patterns_enabled=bool(self.config.chart_patterns_enabled),
            chart_patterns_lookback=int(self.config.chart_patterns_lookback),
            chart_patterns_pivot_window=int(self.config.chart_patterns_pivot_window),
            chart_patterns_price_tolerance=float(self.config.chart_patterns_price_tolerance),
            chart_patterns_volatility_adjusted_tolerance=bool(self.config.chart_patterns_volatility_adjusted_tolerance),
            chart_patterns_price_tolerance_range_multiplier=float(self.config.chart_patterns_price_tolerance_range_multiplier),
            chart_patterns_minimum_price_tolerance=float(self.config.chart_patterns_minimum_price_tolerance),
            chart_patterns_minimum_strength=float(self.config.chart_patterns_minimum_strength),
            chart_patterns_bonus_points=float(self.config.chart_patterns_bonus_points),
            require_chart_pattern=bool(self.config.require_chart_pattern),
            chart_pattern_secondary_conflict_penalty=float(self.config.chart_pattern_secondary_conflict_penalty),
            block_material_chart_pattern_conflict=bool(self.config.block_material_chart_pattern_conflict),
            chart_pattern_conflict_min_margin=float(
                getattr(self.config, "chart_pattern_conflict_min_margin", 0.25)
            ),
            chart_pattern_contrary_min_strength=float(
                getattr(self.config, "chart_pattern_contrary_min_strength", 0.80)
            ),
            chart_pattern_contrary_min_advantage=float(
                getattr(self.config, "chart_pattern_contrary_min_advantage", 0.10)
            ),
            block_similar_chart_pattern_forces=bool(self.config.block_similar_chart_pattern_forces),
            h1_doji_enabled=bool(self.config.h1_doji_enabled),
            h1_doji_lookback_candles=int(self.config.h1_doji_lookback_candles),
            h1_doji_max_age_candles=int(self.config.h1_doji_max_age_candles),
            h1_doji_max_body_ratio=float(self.config.h1_doji_max_body_ratio),
            h1_doji_extreme_fraction=float(self.config.h1_doji_extreme_fraction),
            h1_doji_min_rejection_wick_ratio=float(self.config.h1_doji_min_rejection_wick_ratio),
            h1_doji_bonus_points=float(self.config.h1_doji_bonus_points),
            fvg_enabled=bool(getattr(self.config, "fvg_enabled", True)),
            fvg_lookback=int(getattr(self.config, "fvg_lookback", 30)),
            fvg_max_age_candles=int(getattr(self.config, "fvg_max_age_candles", 10)),
            fvg_require_alignment_with_zone=bool(getattr(self.config, "fvg_require_alignment_with_zone", False)),
            fvg_bonus_points=float(getattr(self.config, "fvg_bonus_points", 6.0)),
            require_fvg=bool(getattr(self.config, "require_fvg", True)),
            # Solo se activa para GOLD: múltiplos de $25 cubren 25/50/75/100.
            round_number_enabled=str(self.config.bot_profile or "").upper() == "GOLD",
            round_number_increment=float(self.config.gold_quarter_level_increment),
            round_number_tolerance_price=float(self.config.gold_quarter_level_tolerance_price),
            round_number_bonus_points=float(self.config.gold_quarter_level_bonus_points),
            require_round_number=bool(self.config.require_gold_quarter_level),
            volume_confirmation_enabled=bool(getattr(self.config, "volume_confirmation_enabled", True)),
            volume_confirmation_lookback=int(getattr(self.config, "volume_confirmation_lookback", 20)),
            volume_confirmation_spike_multiplier=float(getattr(self.config, "volume_confirmation_spike_multiplier", 1.0)),
            volume_confirmation_bonus_points=float(getattr(self.config, "volume_confirmation_bonus_points", 5.0)),
            require_volume_confirmation=bool(getattr(self.config, "require_volume_confirmation", True)),
            volume_confirmation_skip_gate_without_reliable_volume=bool(
                getattr(self.config, "volume_confirmation_skip_gate_without_reliable_volume", True)
            ),
            asian_range_sweep_enabled=(
                str(self.config.bot_profile or "").upper() == "GOLD"
                and bool(getattr(self.config, "gold_asian_range_sweep_enabled", False))
            ),
            asian_range_tolerance_price=float(getattr(self.config, "gold_asian_range_tolerance_price", 2.0)),
        )
        self.lifecycle_manager = lifecycle_manager
        self.reporting_service = reporting_service
        self.console_reporter = console_reporter
        self.dashboard_service = dashboard_service
        # v99: protege la ventana crítica broker fill -> persistencia SQLite.
        # El monitor puede seguir gestionando BE, pero no debe auto-importar una
        # posición recién llenada antes de que su callback la haya persistido.
        self._execution_persistence_lock = threading.Lock()
        # Permite inyectar un executor de prueba sin MetaTrader5. En producción,
        # si no se inyecta uno, se construye el proveedor real de MT5.
        if executor is None:
            from brokers.mt5_execution import MT5ExecutionProvider
            executor = MT5ExecutionProvider(provider.connector)
        self.executor = executor
        self.orb_strategy = NewYorkORBStrategy(
            data_provider=provider,
            config=ORBConfig(
                enabled=bool(self.config.orb_enabled),
                timeframe=str(self.config.orb_timeframe),
                opening_range_minutes=int(self.config.orb_opening_range_minutes),
                require_vwap_alignment=bool(self.config.orb_require_vwap_alignment),
                require_poc_alignment=bool(self.config.orb_require_poc_alignment),
                vwap_poc_require_both=bool(
                    getattr(self.config, "orb_vwap_poc_require_both", False)
                ),
                poc_bins=int(self.config.orb_poc_bins),
                target_rr=float(self.config.orb_target_rr),
                stop_mode=str(self.config.orb_stop_mode),
                stop_buffer_fraction=float(self.config.orb_stop_buffer_fraction),
                candle_count=int(self.config.orb_candle_count),
                breakout_atr_buffer_fraction=float(self.config.orb_breakout_atr_buffer_fraction),
                retest_max_candles=int(self.config.orb_retest_max_candles),
                gold_quarter_level_enabled=True,
                gold_quarter_level_increment=float(self.config.gold_quarter_level_increment),
                gold_quarter_level_tolerance_price=float(self.config.gold_quarter_level_tolerance_price),
            ),
        )
        # Selección efímera por ciclo entre XAUUSD y microXAUUSD.
        # Nunca se persiste como preferencia fija: cada oportunidad vuelve a comparar
        # sizing, spread y margen reales del broker.
        self._orb_gold_cycle_selection = None
        self._orb_gold_cycle_diagnostics = {}
        self.ny_index_open_strategy = NYIndexOpenStrategy(
            data_provider=provider,
            config=NYIndexOpenConfig(
                enabled=bool(self.config.idx_open_enabled),
                m5_confirmation_window_minutes=int(self.config.idx_open_confirmation_window_minutes),
                tp1_rr=float(self.config.idx_open_tp1_rr),
                target_rr=float(self.config.idx_open_target_rr),
                risk_percent_total=float(self.config.orb_risk_percent),
                split_entry_risk_fraction=float(self.config.split_entry_risk_fraction),
            ),
        )

        self.multi_timeframe = MultiTimeframeAnalyzer(
            data_provider=provider,
            config=MultiTimeframeConfig(
                higher_timeframe=self.config.higher_timeframe,
                structure_timeframe=self.config.structure_timeframe,
                confirmation_timeframe=self.config.confirmation_timeframe,
                entry_timeframe=self.config.entry_timeframe,
                higher_timeframe_candles=self.config.higher_timeframe_candle_count,
                require_h4_h1_convergence=self.config.require_h4_h1_convergence,
                structure_candles=self.config.structure_candle_count,
                confirmation_candles=self.config.confirmation_candle_count,
                entry_candles=self.config.entry_candle_count,
                max_m5_signal_age_candles=self.config.max_m5_signal_age_candles,
                max_m5_signal_age_minutes=self.config.max_m5_signal_age_minutes,
                require_latest_m15_setup=self.config.require_latest_m15_setup,
            ),
            pipeline_config=self.pipeline_config,
        )

        # v101: meta-etiquetado independiente por worker. El modelo de un perfil
        # nunca contamina a otro: se entrena y persiste con su propio historial.
        self.meta_labeling = MetaLabelingEngine(
            MetaLabelingConfig(
                enabled=bool(self.config.meta_labeling_enabled),
                mode=str(self.config.meta_labeling_mode),
                min_probability=float(self.config.meta_labeling_min_probability),
                min_net_expectancy_r=float(self.config.meta_labeling_min_net_expectancy_r),
                ranking_enabled=bool(self.config.meta_labeling_ranking_enabled),
                max_signals_per_cycle=int(self.config.meta_labeling_max_signals_per_cycle),
                model_directory=str(self.config.meta_labeling_model_directory),
                min_training_samples=int(self.config.meta_labeling_min_training_samples),
            ),
            worker=str(self.config.bot_profile or "DEFAULT"),
        )
        self._meta_label_cycle_decisions = []

    def _quarantine_file(self) -> Path:
        """Resuelve la ruta absoluta del fichero de cuarentena y crea su carpeta.

        Una ruta relativa se ancla al directorio de trabajo actual. El
        directorio padre se crea si no existe, de modo que el primer guardado
        nunca falle por falta de carpeta.
        """
        path = Path(self.config.quarantine_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @contextmanager
    def _quarantine_storage_lock(self):
        """Serializa el read/modify/write entre engines, hilos y procesos.

        El coordinador unificado comparte el archivo entre perfiles. Además se
        conserva compatibilidad con workers antiguos que aún puedan arrancar en
        otro proceso durante una migración.
        """
        lock_path = self._quarantine_file().with_suffix(".lock")
        with _QUARANTINE_PROCESS_LOCK:
            with lock_path.open("a+b") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    handle.seek(0)
                    if os.name == "nt":
                        import msvcrt
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _load_quarantine_unlocked(self) -> dict:
        """Lee el fichero de cuarentena SIN tomar el bloqueo.

        Uso interno: solo debe llamarse desde dentro de
        `_quarantine_storage_lock`. Ante fichero inexistente, JSON corrupto o
        contenido que no sea un dict devuelve `{}`: una cuarentena ilegible
        no debe impedir que el bot arranque.
        """
        path = self._quarantine_file()
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except Exception:
            return {}

    def _save_quarantine_unlocked(self, payload: dict) -> None:
        """Escribe la cuarentena de forma atómica SIN tomar el bloqueo.

        Escribe primero en un temporal cuyo nombre incluye PID e identificador
        de hilo, y luego lo renombra sobre el destino. Asi un corte a mitad de
        escritura nunca deja el fichero real truncado, y dos escritores
        simultaneos no se pisan el temporal.

        Uso interno: solo desde dentro de `_quarantine_storage_lock`.
        """
        path = self._quarantine_file()
        tmp = path.with_name(
            f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
        )
        try:
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            tmp.replace(path)
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass

    def _recoverable_quarantine_details(self, details: dict) -> dict:
        """Decide si un incidente de cuarentena puede expirar solo o exige revisión.

        Distingue dos naturalezas muy distintas:
        - RECUPERABLE: la unica causa fue superar el tope duro de riesgo tras
          el fill (`POST_FILL_RISK_HARD_CAP_BREACH`) por un exceso pequeno,
          compatible con la granularidad de lotes y el slippage normal. Se
          reintentara pasados unos minutos.
        - NO RECUPERABLE: cualquier otro motivo, o un exceso de riesgo por
          encima del limite. Queda bloqueado hasta intervencion manual.

        Args:
            details: datos del incidente, con `reason`, `target_risk_amount` y
                `actual_risk_amount`.

        Returns:
            Dict con `recoverable`, el `risk_excess_ratio` calculado y el
            limite aplicado. Si el exceso no puede calcularse, el incidente se
            trata como NO recuperable por prudencia.
        """
        reason = str(details.get("reason") or "").upper()
        target = details.get("target_risk_amount")
        actual = details.get("actual_risk_amount")
        try:
            excess_ratio = (float(actual) / float(target)) - 1.0 if float(target) > 0 else None
        except (TypeError, ValueError, ZeroDivisionError):
            excess_ratio = None
        recoverable_limit = (
            max(0.0, float(self.config.hard_risk_tolerance))
            + max(0.0, float(self.config.recoverable_quarantine_extra_tolerance))
        )
        recoverable = bool(
            reason == "POST_FILL_RISK_HARD_CAP_BREACH"
            and excess_ratio is not None
            and excess_ratio <= recoverable_limit + 1e-9
        )
        return {
            "recoverable": recoverable,
            "risk_excess_ratio": excess_ratio,
            "recoverable_risk_limit_ratio": recoverable_limit,
        }

    @staticmethod
    def _parse_quarantine_time(value):
        """Convierte una marca temporal guardada en `datetime` UTC, o `None`.

        Devolver `None` ante un valor ilegible permite a quien llama aplicar
        su propio criterio de respaldo en lugar de propagar el error.
        """
        try:
            stamp = pd.to_datetime(value, utc=True, errors="raise")
            return stamp.to_pydatetime()
        except Exception:
            return None

    def _load_quarantine(self) -> dict:
        """Lee la cuarentena completa tomando el bloqueo compartido.

        Returns:
            Dict `simbolo -> registro`, o `{}` si la cuarentena esta desactivada.
        """
        if not bool(self.config.quarantine_enabled):
            return {}
        with self._quarantine_storage_lock():
            return self._load_quarantine_unlocked()

    def _save_quarantine(self, payload: dict) -> None:
        """Persiste la cuarentena completa tomando el bloqueo compartido.

        No hace nada si la cuarentena esta desactivada en configuracion.
        """
        if not bool(self.config.quarantine_enabled):
            return
        with self._quarantine_storage_lock():
            self._save_quarantine_unlocked(payload)

    def _quarantine_symbol(self, symbol: str, details: dict) -> None:
        """Aparta un símbolo de la operativa registrando el motivo del incidente.

        Clasifica el incidente con `_recoverable_quarantine_details` y fija la
        politica resultante:
        - Recuperable: `expires_at` a unos minutos vista y politica
          `TEMPORARY_EXECUTION_GRANULARITY_GUARD`. Volvera solo.
        - No recuperable: sin caducidad y politica `MANUAL_REVIEW_REQUIRED`.
          Permanecera bloqueado hasta que alguien lo revise.

        La secuencia leer-modificar-escribir se hace dentro del bloqueo para
        que dos workers simultaneos no se sobrescriban mutuamente el registro.

        Args:
            symbol: instrumento a apartar.
            details: contexto del incidente que se conserva integro en el
                registro para poder auditarlo despues.
        """
        if not bool(self.config.quarantine_enabled):
            return
        now = datetime.now(timezone.utc)
        detail_payload = dict(details)
        recovery = self._recoverable_quarantine_details(detail_payload)
        record = {
            "symbol": str(symbol),
            "quarantined_at": now.isoformat(),
            **detail_payload,
            **recovery,
        }
        if recovery["recoverable"]:
            minutes = max(1.0, float(self.config.recoverable_quarantine_minutes))
            record["expires_at"] = (now + timedelta(minutes=minutes)).isoformat()
            record["quarantine_policy"] = "TEMPORARY_EXECUTION_GRANULARITY_GUARD"
        else:
            record["expires_at"] = None
            record["quarantine_policy"] = "MANUAL_REVIEW_REQUIRED"
        with self._quarantine_storage_lock():
            payload = self._load_quarantine_unlocked()
            payload[str(symbol)] = record
            self._save_quarantine_unlocked(payload)

    def _quarantine_result(self, symbol: str):
        """Consulta si un símbolo está en cuarentena, purgando la ya caducada.

        Ademas de consultar, LIMPIA: si el registro era recuperable y su
        caducidad ya paso, lo borra del fichero y devuelve `None`, con lo que
        el simbolo vuelve a estar operable sin intervencion.

        Incluye compatibilidad hacia atras con registros de versiones que no
        guardaban `recoverable` ni `expires_at`: en ese caso reclasifica el
        incidente y deriva la caducidad desde `quarantined_at`.

        Args:
            symbol: instrumento a consultar.

        Returns:
            El registro de cuarentena si sigue vigente, o `None` si el simbolo
            esta operable o la cuarentena esta desactivada.
        """
        if not bool(self.config.quarantine_enabled):
            return None
        key = str(symbol)
        with self._quarantine_storage_lock():
            payload = self._load_quarantine_unlocked()
            record = payload.get(key)
            if not isinstance(record, dict):
                return record

            # Compatibilidad: v98/v99 no guardaban recoverable/expires_at.
            recovery = self._recoverable_quarantine_details(record)
            recoverable = bool(record.get("recoverable", recovery["recoverable"]))
            expires_at = self._parse_quarantine_time(record.get("expires_at"))
            if recoverable and expires_at is None:
                quarantined_at = self._parse_quarantine_time(record.get("quarantined_at"))
                if quarantined_at is not None:
                    expires_at = quarantined_at + timedelta(
                        minutes=max(1.0, float(self.config.recoverable_quarantine_minutes))
                    )
            if recoverable and expires_at is not None and datetime.now(timezone.utc) >= expires_at:
                payload.pop(key, None)
                self._save_quarantine_unlocked(payload)
                return None
            return {
                **record,
                **{k: v for k, v in recovery.items() if k not in record},
                "expires_at": expires_at.isoformat() if expires_at is not None else record.get("expires_at"),
            }

    def _validate_post_fill_risk(
        self,
        *,
        symbol: str,
        direction: str,
        position_ticket,
        target_risk_amount: float,
        risk_base_value: float,
    ) -> dict:
        """Lee la posición real y recalcula el riesgo con volumen/precio/SL reales."""
        position = self.executor.get_position(int(position_ticket))
        if position is None:
            return {"valid": False, "reason": "POST_FILL_POSITION_NOT_FOUND"}

        volume = float(getattr(position, "volume", 0.0) or 0.0)
        entry_price = float(getattr(position, "price_open", 0.0) or 0.0)
        stop_loss = float(getattr(position, "sl", 0.0) or 0.0)
        if volume <= 0 or entry_price <= 0 or stop_loss <= 0:
            return {
                "valid": False,
                "reason": "POST_FILL_INVALID_POSITION_DATA",
                "volume": volume,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
            }

        broker_risk = self.executor.calculate_risk_amount(
            symbol=symbol,
            direction=direction,
            volume=volume,
            entry_price=entry_price,
            stop_loss=stop_loss,
        )
        actual_risk = float(broker_risk["actual_risk_amount"])
        hard_cap = float(target_risk_amount) * (
            1.0 + max(0.0, float(self.config.hard_risk_tolerance))
        )
        excess_ratio = (
            (actual_risk / float(target_risk_amount)) - 1.0
            if float(target_risk_amount) > 0
            else None
        )
        recoverable_limit = (
            max(0.0, float(self.config.hard_risk_tolerance))
            + max(0.0, float(self.config.recoverable_quarantine_extra_tolerance))
        )
        return {
            "valid": actual_risk <= hard_cap + 1e-9,
            "reason": "POST_FILL_RISK_OK" if actual_risk <= hard_cap + 1e-9 else "POST_FILL_RISK_HARD_CAP_BREACH",
            "actual_risk_amount": actual_risk,
            "actual_risk_percent": actual_risk / float(risk_base_value) * 100.0 if risk_base_value > 0 else None,
            "target_risk_amount": float(target_risk_amount),
            "hard_risk_cap": hard_cap,
            "risk_excess_ratio": excess_ratio,
            "recoverable_execution_granularity_breach": bool(
                actual_risk > hard_cap + 1e-9
                and excess_ratio is not None
                and excess_ratio <= recoverable_limit + 1e-9
            ),
            "position_ticket": str(position_ticket),
            "real_volume": volume,
            "real_entry_price": entry_price,
            "real_stop_loss": stop_loss,
            "risk_engine": broker_risk.get("risk_engine"),
        }

    def _execution_key(self, symbol, confirmation_time, direction, strategy_name="SMC"):
        """Construye la clave única e idempotente de una ejecución.

        Sirve para que la MISMA senal no se ejecute dos veces aunque el ciclo
        la vuelva a detectar. La clave combina fuente, simbolo, cadena de
        marcos temporales, instante de confirmacion y direccion, de modo que
        dos senales distintas nunca colisionan y una repetida siempre coincide.

        El formato depende de la estrategia porque ORB Nueva York confirma en
        M1 y no usa la cadena H1/M15/M5.

        Args:
            symbol: instrumento.
            confirmation_time: instante de la confirmacion, normalizado a UTC.
            direction: `BUY` o `SELL`.
            strategy_name: `SMC` por defecto, o `ORB_NEW_YORK`.

        Returns:
            La clave de ejecucion como cadena.
        """
        stamp = pd.to_datetime(confirmation_time, utc=True).isoformat()
        strategy = str(strategy_name or "SMC").upper()
        if strategy == "ORB_NEW_YORK":
            return f"{self.config.source}:{symbol}:ORB:NY:M1:{stamp}:{direction}"
        return f"{self.config.source}:{symbol}:H1:M15:M5:{stamp}:{direction}"

    def _persist_audit_event(
        self,
        event_type,
        *,
        instrument=None,
        action=None,
        reason=None,
        execution_key=None,
        broker_position_ticket=None,
        cycle_number=None,
        payload=None,
    ):
        """Telemetría runtime + auditoría persistente, ambas defensivas.

        v53: el estado del worker se persiste ANTES del Audit Log. Así una falla
        secundaria al serializar/escribir auditoría no deja al dashboard sin
        heartbeat ni progreso.
        """
        audit_payload = (
            dict(payload)
            if isinstance(payload, dict)
            else {"value": payload} if payload is not None else {}
        )
        audit_payload.setdefault("bot_profile", str(self.config.bot_profile).upper())
        audit_payload.setdefault("daemon_magic", int(self.config.magic))

        event_name = str(event_type or "").upper()
        runtime_error = None

        updater = getattr(self.repository, "upsert_worker_runtime_state", None)
        if callable(updater):
            state_kwargs = {
                "source": self.config.source,
                "status": "RUNNING",
                "cycle_number": cycle_number,
                "current_symbol": instrument,
                "last_action": action or event_name,
                "last_reason": reason,
            }
            if event_name == "DAEMON_CYCLE_START":
                state_kwargs["symbols_total"] = audit_payload.get("symbols_count")
                state_kwargs["symbols_processed"] = 0
                state_kwargs["current_symbol"] = None
                runtime_state = str(audit_payload.get("runtime_state") or "")
                if runtime_state in {"WAITING_NEW_M5_BAR", "WAITING_NEW_M1_BAR"}:
                    timeframe = "M1" if runtime_state == "WAITING_NEW_M1_BAR" else "M5"
                    # No es un worker sin símbolos: es un ciclo sin una vela
                    # nueva. Mostrar 0/N evita que 0/0 se interprete como que
                    # GOLD/FOREX nunca fueron descubiertos ni analizados.
                    selected_count = int(audit_payload.get("selected_symbols_count") or 0)
                    state_kwargs["symbols_total"] = selected_count
                    state_kwargs["symbols_processed"] = 0
                    state_kwargs["status"] = runtime_state
                    state_kwargs["last_action"] = "EVENT_SCHEDULER_WAIT"
                    state_kwargs["last_reason"] = (
                        f"Instrumentos disponibles; esperando nueva vela {timeframe} cerrada"
                    )
                elif runtime_state == "WAITING_FOREX_DATA":
                    state_kwargs["status"] = "WAITING_FOREX_DATA"
                    state_kwargs["last_action"] = "FOREX_DATA_WAIT"
                    state_kwargs["last_reason"] = (
                        "Sin velas Forex disponibles; posible mercado cerrado o datos MT5 pendientes"
                    )
                elif int(audit_payload.get("selected_symbols_count") or 0) == 0:
                    state_kwargs["status"] = "DEGRADED_NO_SYMBOLS"
                    state_kwargs["last_action"] = "EMPTY_CYCLE"
                    state_kwargs["last_reason"] = (
                        "El worker no tiene instrumentos seleccionados/configurados"
                    )
            elif event_name == "SYMBOL_PROCESS_START":
                index = audit_payload.get("index")
                state_kwargs["symbols_processed"] = max(0, int(index or 1) - 1)
                state_kwargs["symbols_total"] = audit_payload.get("total")
                state_kwargs["last_action"] = "ANALYZANDO"
            elif event_name == "SYMBOL_PROCESS_RESULT":
                state_kwargs["symbols_processed"] = audit_payload.get("index")
                state_kwargs["symbols_total"] = audit_payload.get("total")
                state_kwargs["last_elapsed_seconds"] = audit_payload.get("elapsed_seconds")
                # Sólo un resultado terminado reemplaza el último candidato auditado.
                state_kwargs["details"] = audit_payload
            elif event_name == "POSITION_MONITOR":
                state_kwargs["last_action"] = "MONITOR_POSICIONES"

            try:
                updater(
                    str(self.config.bot_profile).upper(),
                    int(self.config.magic),
                    **state_kwargs,
                )
            except Exception as exc:
                runtime_error = str(exc)
                # ASCII-safe para Windows aunque sys.stdout no haya sido reconfigurado.
                try:
                    print(
                        f"[RUNTIME DB ERROR] {self.config.bot_profile}: {runtime_error}",
                        file=sys.stderr,
                    )
                except Exception:
                    pass

        saver = getattr(self.repository, "save_audit_event", None)
        if not callable(saver):
            return {"runtime_error": runtime_error} if runtime_error else None

        # El inicio de símbolo ya queda representado por worker_runtime_states;
        # duplicarlo en una tabla append-only aportaba poco y duplicaba escrituras.
        if event_name == "SYMBOL_PROCESS_START":
            return {
                "runtime_only": True,
                "runtime_error": runtime_error,
            } if runtime_error else {"runtime_only": True}

        if event_name == "SYMBOL_PROCESS_RESULT":
            compact_result = audit_payload.get("result") if isinstance(audit_payload.get("result"), dict) else {}
            compact_action = str(compact_result.get("action") or action or "").upper()
            always_persist = bool(
                compact_result.get("valid")
                or compact_action in {"ORDER_OPENED", "SPLIT_ORDER_OPENED", "DRY_RUN_VALIDATED"}
                or any(token in compact_action for token in (
                    "ERROR", "REJECTED", "RISK", "MARGIN", "QUARANTINE",
                    "EXECUTION", "INVALIDATED", "ALREADY_EXECUTED",
                ))
            )
            signature = (
                str(instrument or compact_result.get("symbol") or ""),
                compact_action,
                str(compact_result.get("reason") or reason or ""),
                tuple(compact_result.get("missing_confirmations") or ()),
            )
            now_mono = time.monotonic()
            cache = dict(getattr(self, "_strategy_evaluation_audit_cache", {}) or {})
            previous = cache.get(signature)
            sample_interval = max(
                30.0,
                float(self.config.strategy_evaluation_audit_interval_seconds),
            )
            if not always_persist and previous is not None and (now_mono - float(previous)) < sample_interval:
                return {
                    "sampled_out": True,
                    "runtime_error": runtime_error,
                } if runtime_error else {"sampled_out": True}
            cache[signature] = now_mono
            # Elimina firmas inactivas para que la caché permanezca acotada.
            cutoff_mono = now_mono - max(sample_interval * 3.0, 900.0)
            self._strategy_evaluation_audit_cache = {
                key: value for key, value in cache.items() if float(value) >= cutoff_mono
            }

        if event_name == "POSITION_MONITOR":
            break_even = audit_payload.get("break_even") if isinstance(audit_payload.get("break_even"), dict) else {}
            forex_rollover = break_even.get("forex_rollover") if isinstance(break_even.get("forex_rollover"), dict) else {}
            meaningful = bool(
                audit_payload.get("sync")
                or break_even.get("activated")
                or break_even.get("runner_updates")
                or break_even.get("errors")
                or forex_rollover.get("closed")
            )
            now_mono = time.monotonic()
            last_mono = float(getattr(self, "_last_position_monitor_audit_monotonic", 0.0) or 0.0)
            sample_interval = max(1.0, float(self.config.position_monitor_audit_interval_seconds))
            if not meaningful and (now_mono - last_mono) < sample_interval:
                return {
                    "sampled_out": True,
                    "runtime_error": runtime_error,
                } if runtime_error else {"sampled_out": True}
            self._last_position_monitor_audit_monotonic = now_mono

        try:
            event_id = saver(
                event_type,
                source=self.config.source,
                instrument=instrument,
                action=action,
                reason=reason,
                execution_key=execution_key,
                broker_position_ticket=broker_position_ticket,
                cycle_number=cycle_number,
                payload=audit_payload,
            )
            return {
                "event_id": event_id,
                "runtime_error": runtime_error,
            } if runtime_error else event_id
        except Exception as exc:
            return {
                "persisted": False,
                "error": str(exc),
                "runtime_error": runtime_error,
            }

    @staticmethod
    def _compact_symbol_result(result: dict | None) -> dict:
        """Reduce telemetría por símbolo sin perder métricas de decisión.

        Las auditorías completas de una operación confirmada continúan en
        trades/trade_visual_audits/trade_audit_snapshots. Este resumen evita
        guardar cientos de veces el árbol H1/M15/M5 completo cuando NO hay trade.
        """
        row = dict(result or {})
        analysis = row.get("analysis") if isinstance(row.get("analysis"), dict) else {}
        signal = (
            analysis.get("signal") or analysis.get("entry") or row.get("signal") or row.get("entry") or {}
        )
        if not isinstance(signal, dict):
            signal = {}
        diagnostics = analysis.get("diagnostics") if isinstance(analysis.get("diagnostics"), dict) else {}
        strategy_name = str(
            row.get("strategy_name") or signal.get("strategy_name")
            or analysis.get("strategy_name") or "SMC"
        )

        def limited(value, limit=24):
            """Convierte una colección en lista de cadenas acotada en tamaño.

            Evita que una lista de diagnostico enorme infle el registro de
            auditoria. Lo que no sea coleccion devuelve lista vacia.
            """
            if isinstance(value, (list, tuple, set)):
                return [str(item) for item in list(value)[:limit]]
            return []

        confirmations = signal.get("confirmations")
        if not isinstance(confirmations, dict):
            confirmations = diagnostics.get("confirmations") if isinstance(diagnostics.get("confirmations"), dict) else {}
        confirmation_flags = {
            str(key): bool(value)
            for key, value in list(confirmations.items())[:32]
        }
        missing = limited(
            signal.get("missing_confirmations")
            or analysis.get("missing_confirmations")
            or [key for key, value in confirmation_flags.items() if not value]
        )

        signal_age = diagnostics.get("signal_age") if isinstance(diagnostics.get("signal_age"), dict) else {}
        risk_metrics = {
            key: row.get(key)
            for key in (
                "risk_percent", "risk_amount", "actual_risk_percent",
                "actual_risk_amount", "min_required_risk", "required_margin",
                "max_allowed_margin", "leg",
            )
            if row.get(key) is not None
        }
        for failure_name in ("split_failure", "single_failure", "risk_failure"):
            failure = row.get(failure_name)
            if not isinstance(failure, dict):
                continue
            risk_metrics[failure_name] = {
                key: failure.get(key)
                for key in (
                    "code", "leg", "risk_amount", "actual_risk_amount",
                    "actual_risk_percent", "min_required_risk", "max_allowed_risk",
                )
                if failure.get(key) is not None
            }

        compact = {
            "symbol": row.get("symbol") or analysis.get("symbol"),
            "action": row.get("action") or row.get("state") or analysis.get("action"),
            "reason": row.get("reason") or row.get("error") or analysis.get("reason"),
            "valid": bool(row.get("valid", analysis.get("valid", False))),
            "direction": row.get("direction") or signal.get("direction") or analysis.get("direction"),
            "strategy_name": strategy_name,
            "strategy_version": (
                row.get("strategy_version") or signal.get("strategy_version")
                or analysis.get("strategy_version")
            ),
            "trade_score": signal.get("trade_score", analysis.get("trade_score")),
            "confirmation_percentage": signal.get(
                "confirmation_percentage", analysis.get("confirmation_percentage")
            ),
            "missing_confirmations": missing,
            "confirmation_flags": confirmation_flags,
            "signal_age": {
                key: signal_age.get(key)
                for key in (
                    "signal_time", "age_candles", "age_minutes",
                    "max_age_candles", "max_age_minutes", "is_stale",
                )
                if signal_age.get(key) is not None
            },
            "risk_metrics": risk_metrics,
        }

        meta_label = row.get("meta_label")
        if not isinstance(meta_label, dict):
            meta_label = signal.get("meta_label") if isinstance(signal.get("meta_label"), dict) else {}
        if meta_label:
            compact["meta_label"] = {
                key: meta_label.get(key)
                for key in (
                    "mode", "probability", "net_expectancy_r",
                    "allowed", "shadow", "reason", "trained",
                )
                if meta_label.get(key) is not None
            }
        exhaustion = analysis.get("exhaustion_reversal_shadow")
        if isinstance(exhaustion, dict):
            compact["exhaustion_reversal_shadow"] = {
                key: exhaustion.get(key)
                for key in (
                    "mode", "valid", "action", "reason", "direction",
                    "direction_allowed", "exhaustion_time", "confirmation_time",
                    "entry_price", "stop_loss", "equilibrium_target",
                    "risk_distance", "volume_applicable", "volume_ratio",
                    "dealing_range", "checks",
                )
                if exhaustion.get(key) is not None
            }
        return {key: value for key, value in compact.items() if value not in (None, {}, [])}

    def _recover_unpersisted_open_positions(self):
        """Auto-repara posiciones MT5 del daemon que aún no estén en SQLite."""
        if not bool(self.config.execution_enabled):
            return {"seen": 0, "imported_daemon": 0, "skipped": True}
        lock = getattr(self, "_execution_persistence_lock", None)
        acquired = False
        if lock is not None:
            acquired = lock.acquire(blocking=False)
            if not acquired:
                return {
                    "seen": 0,
                    "imported_daemon": 0,
                    "skipped": True,
                    "reason": "EXECUTION_PERSISTENCE_IN_PROGRESS",
                }
        importer = getattr(self.repository, "import_open_mt5_positions", None)
        if not callable(importer):
            if acquired:
                lock.release()
            return {"seen": 0, "imported_daemon": 0, "skipped": True, "reason": "IMPORTER_UNAVAILABLE"}
        try:
            result = importer(
                self.executor,
                source=self.config.source,
                magic=int(self.config.magic),
                include_external=False,
                timeframe=str(self.config.entry_timeframe),
            )
            if (result or {}).get("imported_daemon"):
                self._persist_audit_event(
                    "PERSISTENCE_SELF_HEAL",
                    action="MT5_OPEN_POSITION_RECOVERED",
                    payload={"bot_profile": str(self.config.bot_profile).upper(), **dict(result or {})},
                )
            return result or {}
        except Exception as exc:
            self._persist_audit_event(
                "PERSISTENCE_SELF_HEAL_ERROR",
                action="MT5_RECOVERY_FAILED",
                reason=str(exc),
            )
            return {"error": str(exc), "imported_daemon": 0}
        finally:
            if acquired:
                lock.release()

    @staticmethod
    def _canonical_bot_profile(profile: str) -> str:
        """Devuelve la familia estratégica de un worker físicamente dividido."""
        value = str(profile or "").upper()
        if value.startswith("VOLATILITY_") and value.rsplit("_", 1)[-1].isdigit():
            return "VOLATILITY"
        return value

    @classmethod
    def _symbol_matches_split_profile(cls, symbol: str, profile: str) -> bool:
        """Comprueba si un símbolo pertenece al perfil de este worker.

        Base del reparto MULTI-WORKER: cada instancia opera solo su familia de
        instrumentos, de modo que varios bots corren en paralelo sin pisarse
        los mismos simbolos.

        Las comparaciones son por nombre y excluyentes entre si: `BOOM` exige
        que aparezca "boom" y NO "crash", y viceversa, porque los indices
        sinteticos comparten convenciones de nombre facilmente confundibles.

        Args:
            symbol: nombre del instrumento.
            profile: perfil del worker, normalizado antes con
                `_canonical_bot_profile` para agrupar workers divididos como
                `VOLATILITY_1` y `VOLATILITY_2` bajo la misma familia.

        Returns:
            `True` si el simbolo corresponde a este worker.
        """
        name = str(symbol or "").lower()
        profile = cls._canonical_bot_profile(profile)
        if profile == "BOOM":
            return "boom" in name and "crash" not in name
        if profile == "CRASH":
            return "crash" in name and "boom" not in name
        if profile == "VOLATILITY":
            return "volatility" in name or name.startswith("vol ")
        if profile == "STEP":
            return "step" in name
        if profile == "JUMP":
            return "jump" in name
        if profile == "FLIP":
            return ("flip" in name) or ("boom" in name and "crash" in name)
        return False

    @staticmethod
    def _is_synthetics_profile_name(bot_profile: str) -> bool:
        """True si `bot_profile` es un perfil de Sintéticos (Boom/Crash/Volatility/Step/Jump/Flip).

        v107: se usa para omitir metadata de runner TP3/TP4
        (`runner_max_target_rr`, `runner_tp3_guard_*`, `runner_tp4_guard_*`)
        que nunca se usa en Sintéticos, porque `_manage_runner_extension`
        siempre corta con `SYNTHETICS_FIXED_TP2_TARGET` antes de llegar a esa
        lógica (ver esa función más abajo). Antes esos campos se calculaban
        igual para todos los perfiles no-ORB, generando ruido en la
        metadata/auditoría de trades de Sintéticos.
        """
        profile = LiveTradingEngine._canonical_bot_profile(bot_profile)
        return profile.startswith("VOLATILITY") or profile in {
            "SYNTHETICS", "BOOM", "CRASH", "STEP", "JUMP", "FLIP",
        }

    @staticmethod
    def _uses_forex_style_smc_management(bot_profile: str) -> bool:
        """Perfiles SMC con la misma gestión progresiva de Forex.

        Esto no habilita el scheduler, el rollover ni los límites por divisa:
        esas protecciones continúan siendo exclusivas de perfiles FOREX.
        """
        profile = LiveTradingEngine._canonical_bot_profile(bot_profile)
        return profile.startswith("FOREX") or profile in {
            "GOLD",
            "SYNTHETICS", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"
        }

    def _gold_smc_session_state(self, now_utc=None) -> dict:
        """Ventanas DST-safe: Tokio->NY 09:30 y Londres 08:00->12:00."""
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        if now.tzinfo is None:
            now = now.tz_localize("UTC")
        else:
            now = now.tz_convert("UTC")
        asia_tz = ZoneInfo(str(self.config.gold_asia_timezone))
        ny_tz = ZoneInfo(str(self.config.gold_new_york_timezone))
        london_tz = ZoneInfo(str(self.config.gold_london_timezone))
        asia_now = now.tz_convert(asia_tz)
        london_now = now.tz_convert(london_tz)

        latest_asia_open = None
        for days_back in range(0, 8):
            day = (asia_now - pd.Timedelta(days=days_back)).date()
            if day.weekday() >= 5:
                continue
            candidate = pd.Timestamp(datetime(
                day.year, day.month, day.day,
                int(self.config.gold_asia_open_hour),
                int(self.config.gold_asia_open_minute),
                tzinfo=asia_tz,
            ))
            if candidate <= asia_now:
                latest_asia_open = candidate
                break

        next_ny_open = None
        if latest_asia_open is not None:
            start_ny_date = latest_asia_open.tz_convert(ny_tz).date()
            for days_forward in range(0, 8):
                day = start_ny_date + timedelta(days=days_forward)
                if day.weekday() >= 5:
                    continue
                candidate = pd.Timestamp(datetime(
                    day.year, day.month, day.day,
                    int(self.config.gold_new_york_open_hour),
                    int(self.config.gold_new_york_open_minute),
                    tzinfo=ny_tz,
                ))
                if candidate > latest_asia_open:
                    next_ny_open = candidate
                    break

        asia_active = bool(
            latest_asia_open is not None
            and next_ny_open is not None
            and latest_asia_open.tz_convert("UTC") <= now < next_ny_open.tz_convert("UTC")
        )
        london_open = london_now.replace(
            hour=int(self.config.gold_london_open_hour),
            minute=0,
            second=0,
            microsecond=0,
        )
        london_close = london_now.replace(
            hour=int(self.config.gold_london_close_hour),
            minute=0,
            second=0,
            microsecond=0,
        )
        london_active = bool(
            london_now.weekday() < 5 and london_open <= london_now < london_close
        )
        active = bool(asia_active or london_active)
        return {
            "active": active,
            "now_utc": now.isoformat(),
            "asia_open": latest_asia_open.isoformat() if latest_asia_open is not None else None,
            "new_york_open": next_ny_open.isoformat() if next_ny_open is not None else None,
            "asia_active": asia_active,
            "london_active": london_active,
            "entry_window": "ASIA_09_TOKYO_TO_NY_0930_OR_LONDON_08_TO_12",
        }

    def _gold_smc_entry_gate(self, symbol: str, now_utc=None):
        """PUERTA DE ENTRADA: restringe el oro a sus ventanas de sesión válidas.

        XAUUSD solo admite entradas SMC en Asia hasta la apertura de Nueva York
        (09:30) o durante Londres de 08:00 a 12:00. Fuera de esas franjas el
        comportamiento del oro no encaja con la logica del sistema.

        Solo aplica al worker con perfil `GOLD` y si la restriccion esta
        activada en configuracion.

        Args:
            symbol: instrumento evaluado.
            now_utc: instante de referencia; util para pruebas.

        Returns:
            `None` si la entrada esta PERMITIDA (convencion de todas las
            puertas), o un dict de bloqueo con `action`, `reason` y el estado
            de sesion cuando debe rechazarse.
        """
        if str(self.config.bot_profile or "").upper() != "GOLD":
            return None
        if not bool(self.config.gold_smc_session_enabled):
            return None
        state = self._gold_smc_session_state(now_utc)
        if state["active"]:
            return None
        return {
            "symbol": symbol,
            "action": "GOLD_SMC_SESSION_CLOSED",
            "reason": "XAUUSD_ENTRADAS_SOLO_ASIA_HASTA_NY_0930_O_LONDRES_08_A_12",
            "gold_session": state,
        }

    def _trade_owned_by_current_bot(self, trade: dict) -> bool:
        """Evita que un proceso administre posiciones de otro bot.

        v49 permite que los nuevos sub-bots sintéticos adopten posiciones legacy
        del magic histórico 26082026 únicamente cuando el símbolo pertenece de
        forma inequívoca a su propia familia.
        """
        metadata = self._trade_metadata(trade)
        recorded_magic = metadata.get("daemon_magic")
        if recorded_magic in (None, ""):
            recorded_magic = metadata.get("mt5_magic")

        current_magic = int(self.config.magic)
        profile = str(self.config.bot_profile).upper()
        family_profile = self._canonical_bot_profile(profile)

        if recorded_magic not in (None, ""):
            try:
                recorded_magic = int(recorded_magic)
            except Exception:
                return False

            if recorded_magic == current_magic:
                return True

            # El primer shard de Volatility es el único autorizado a adoptar
            # posiciones creadas por los magics legacy. Evita que cuatro
            # workers administren simultáneamente el mismo ticket antiguo.
            legacy_volatility_owner = profile in {"VOLATILITY", "VOLATILITY_1"}
            legacy_magic_allowed = (
                recorded_magic == 26082026
                or (recorded_magic == 26082103 and family_profile == "VOLATILITY")
            )
            if legacy_magic_allowed and family_profile in {
                "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"
            }:
                if family_profile == "VOLATILITY" and not legacy_volatility_owner:
                    return False
                return self._symbol_matches_split_profile(
                    trade.get("instrument"),
                    family_profile,
                )
            return False

        # Legacy sin magic persistido.
        if profile == "SYNTHETICS" and current_magic == 26082026:
            return True
        if family_profile in {"BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"}:
            if family_profile == "VOLATILITY" and profile not in {"VOLATILITY", "VOLATILITY_1"}:
                return False
            return self._symbol_matches_split_profile(
                trade.get("instrument"),
                family_profile,
            )
        return False

    def _account_and_guard(self):
        """Obtiene la cuenta y CORTA si no es una cuenta demo.

        Salvaguarda de seguridad: el motor esta configurado exclusivamente
        para DEMO. Verifica la fuente configurada y ademas exige al ejecutor
        que confirme contra el broker que la cuenta real es de demostracion,
        de modo que un error de configuracion no pueda operar dinero real.

        Returns:
            El snapshot de cuenta, ya persistido.

        Raises:
            RuntimeError: si la fuente configurada no es DEMO.
        """
        if self.config.source.upper() != "DEMO":
            raise RuntimeError("Este motor está configurado únicamente para DEMO.")
        account = self.executor.assert_demo_account()
        self.repository.save_account_snapshot(account)
        return account

    def _save_signal(self, symbol, signal):
        """Persiste una señal aplanando sus criterios SMC en columnas propias.

        Cada condicion estructural (tendencia, swing, liquidez, barrido,
        ruptura, order block, retest, premium/discount y confirmacion) se
        guarda como campo booleano consultable, y el analisis integro queda en
        `details`. Esa doble forma permite filtrar por criterio en SQL sin
        perder el contexto completo, que es justo lo que consume despues el
        entrenamiento del modelo de IA.

        Args:
            symbol: instrumento.
            signal: dict del analisis multi-temporal.

        Returns:
            Lo que devuelva `save_signal_once`, que es idempotente y no
            duplica una senal ya registrada.

        Vinculaciones:
        - `database.repository.save_signal_once` realiza la escritura.
        - Las filas resultantes alimentan `strategy.ai.training`.
        """
        payload = {
            "instrument": symbol,
            "timeframe": str(signal.get("timeframe") or self.config.entry_timeframe),
            "signal_time": signal["entry_time"],
            "direction": signal.get("direction"),
            "valid": bool(signal.get("valid", False)),
            "trend_ok": bool(signal.get("trend_ok", False)),
            "swing_ok": bool(signal.get("swing_ok", False)),
            "liquidity_ok": bool(signal.get("liquidity_ok", False)),
            "sweep_ok": bool(signal.get("sweep_ok", False)),
            "structure_break_ok": bool(signal.get("structure_break_ok", False)),
            "order_block_ok": bool(signal.get("order_block_ok", False)),
            "retest_ok": bool(signal.get("retest_ok", False)),
            "premium_discount_ok": bool(signal.get("premium_discount_ok", False)),
            "confirmation_ok": bool(signal.get("confirmation_ok", False)),
            "details": signal,
        }
        return self.repository.save_signal_once(payload)

    def _total_position_limit(self) -> int:
        """Devuelve el número máximo de posiciones abiertas simultáneas.

        Prefiere `max_total_open_positions` y recurre a `max_open_positions`
        si el primero no esta definido. El resultado nunca baja de 1, para que
        una configuracion a cero no deje el bot incapaz de operar.
        """
        value = self.config.max_total_open_positions
        if value is None:
            value = self.config.max_open_positions
        return max(1, int(value))

    def _open_trade_diagnostics(self, symbol: str) -> dict:
        """Obtiene únicamente operaciones OPEN del propio bot registradas en SQLite."""
        source = str(self.config.source).upper()
        open_trades = self.repository.open_trades(source=source)
        same_symbol = [
            trade for trade in open_trades
            if str(trade.get("instrument", "")) == str(symbol)
        ]

        def compact(trade):
            """Reduce una operación a los campos esenciales para diagnóstico."""
            return {
                "trade_id": trade.get("id"),
                "instrument": trade.get("instrument"),
                "direction": trade.get("direction"),
                "status": trade.get("status"),
                "entry_time": str(trade.get("entry_time")),
                "broker_position_ticket": trade.get("broker_position_ticket"),
                "external_ticket": trade.get("external_ticket"),
                "risk_amount": trade.get("risk_amount"),
            }

        return {
            "source": source,
            "total_open": len(open_trades),
            "symbol_open": len(same_symbol),
            "max_total": self._total_position_limit(),
            "max_per_symbol": max(1, int(self.config.max_open_positions_per_symbol)),
            "open_trades": [compact(trade) for trade in open_trades],
            "symbol_open_trades": [compact(trade) for trade in same_symbol],
        }

    def _sync_open_trades_before_execution(self):
        """Evita que SQLite mantenga OPEN una operación ya cerrada en MT5."""
        if not self.config.execution_enabled:
            return {"synced": 0, "skipped": True, "reason": "DRY_RUN"}
        try:
            owned = [
                trade
                for trade in (self.repository.open_trades(source=self.config.source) or [])
                if isinstance(trade, dict) and self._trade_owned_by_current_bot(trade)
            ]
            if not owned:
                return {
                    "synced": 0,
                    "skipped": True,
                    "reason": "NO_OWNED_OPEN_POSITIONS",
                }
        except Exception:
            # Ante un fallo de lectura SQLite conservamos la reconciliación MT5.
            pass
        try:
            updated = self.repository.sync_closed_mt5_trades(
                self.executor,
                source=self.config.source,
            )
            return {"synced": int(updated or 0), "skipped": False}
        except Exception as exc:
            # No ocultamos el error: se devuelve en diagnóstico y el flujo continúa.
            return {"synced": 0, "skipped": False, "error": str(exc)}


    @staticmethod
    def _signal_entry_price(signal):
        """Extrae el precio de entrada de una señal, tolerando ambos nombres de campo.

        Acepta `entry_price` o `entry` segun de que estrategia provenga la
        senal. Devuelve `None` si falta o no es numerico, nunca 0.0.
        """
        value = signal.get("entry_price", signal.get("entry")) if signal else None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _market_signal_diagnostics(self, symbol, direction, signal, tick, market_entry, structural_stop_loss):
        """Comprueba si el mercado actual invalida o degrada la señal original."""
        signal_entry = self._signal_entry_price(signal)
        structural_sl = float(structural_stop_loss)
        market_entry = float(market_entry)
        direction = str(direction).upper()

        risk_distance = abs(signal_entry - structural_sl) if signal_entry is not None else None
        signed_move = market_entry - signal_entry if signal_entry is not None else None
        abs_move = abs(signed_move) if signed_move is not None else None
        drift_r = (abs_move / risk_distance) if risk_distance and risk_distance > 0 else None

        if direction == "BUY":
            invalidated = market_entry <= structural_sl
            invalidation_reason = "BUY_MARKET_AT_OR_BELOW_STRUCTURAL_SL"
        elif direction == "SELL":
            invalidated = market_entry >= structural_sl
            invalidation_reason = "SELL_MARKET_AT_OR_ABOVE_STRUCTURAL_SL"
        else:
            invalidated = True
            invalidation_reason = "INVALID_DIRECTION"

        max_drift = self.config.max_entry_drift_r
        drift_exceeded = (
            not invalidated
            and max_drift is not None
            and drift_r is not None
            and drift_r > float(max_drift)
        )

        return {
            "symbol": symbol,
            "direction": direction,
            "signal_entry_price": signal_entry,
            "market_entry_price": market_entry,
            "structural_stop_loss": structural_sl,
            "market_bid": tick.get("bid"),
            "market_ask": tick.get("ask"),
            "spread": (float(tick.get("ask")) - float(tick.get("bid")))
                if tick.get("ask") is not None and tick.get("bid") is not None else None,
            "signal_to_market_move": signed_move,
            "absolute_move": abs_move,
            "structural_risk_distance": risk_distance,
            "entry_drift_r": drift_r,
            "max_entry_drift_r": max_drift,
            "market_invalidated_signal": bool(invalidated),
            "entry_drift_exceeded": bool(drift_exceeded),
            "reason": (
                invalidation_reason if invalidated
                else "ENTRY_PRICE_DRIFT_TOO_LARGE" if drift_exceeded
                else "MARKET_SIGNAL_VALID"
            ),
        }

    @staticmethod
    def _forex_pair_currencies(symbol: str):
        """Descompone un símbolo Forex en sus divisas base y cotizada.

        Filtra los caracteres no alfabeticos (sufijos del broker como `.m` o
        `_raw`) y busca un bloque de seis letras formado por dos divisas
        conocidas. Asi tolera nombres como `EURUSD.pro` o `fxEURUSD`.

        Args:
            symbol: nombre del instrumento.

        Returns:
            Tupla `(base, cotizada)`, o `(None, None)` si no es un par Forex
            reconocible, lo que permite a quien llama omitir el control.

        Vinculaciones:
        - La usan `_forex_exposure_guard` para agregar riesgo por divisa y
          `_forex_high_impact_news_entry_gate` para cruzar con el calendario.
        """
        letters = "".join(ch for ch in str(symbol or "").upper() if ch.isalpha())
        known = ("USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD","SEK","NOK","DKK","SGD","HKD","ZAR","MXN","TRY","PLN")
        for i in range(max(1, len(letters) - 5)):
            block = letters[i:i+6]
            if len(block) == 6 and block[:3] in known and block[3:] in known:
                return block[:3], block[3:]
        return (None, None)

    def _forex_exposure_guard(self, symbol: str, execution_key: str):
        """Bloqueo DB-global por exposición Forex, independiente del shard."""
        if not str(self.config.bot_profile or "").upper().startswith("FOREX"):
            return None
        base, quote = self._forex_pair_currencies(symbol)
        if not base or not quote:
            return None
        try:
            trades = self.repository.open_trades(source=self.config.source) or []
        except Exception:
            trades = []

        logical = {}
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            tb, tq = self._forex_pair_currencies(trade.get("instrument"))
            if not tb or not tq:
                continue
            details = trade.get("details") if isinstance(trade.get("details"), dict) else {}
            meta = details.get("metadata") if isinstance(details.get("metadata"), dict) else {}
            key = str(meta.get("parent_execution_key") or trade.get("execution_key") or trade.get("id"))
            try:
                operation_risk = float(meta.get("operation_risk_percent") or trade.get("risk_percent") or 0.0)
            except Exception:
                operation_risk = 0.0
            item = logical.setdefault(key, {"risk": 0.0, "currencies": {tb, tq}})
            item["risk"] = max(float(item["risk"]), operation_risk)
            item["currencies"].update({tb, tq})

        total = sum(float(v["risk"]) for v in logical.values())
        currency = {}
        for item in logical.values():
            for cur in item["currencies"]:
                currency[cur] = currency.get(cur, 0.0) + float(item["risk"])

        prospective = float(self.config.risk_percent)
        max_total = float(self.config.forex_max_total_risk_percent)
        max_cur = float(self.config.forex_max_currency_exposure_percent)

        if total + prospective > max_total + 1e-9:
            return {
                "symbol": symbol,
                "action": "FOREX_TOTAL_RISK_LIMIT",
                "reason": "FOREX_GLOBAL_RISK_EXPOSURE_LIMIT",
                "execution_key": execution_key,
                "forex_exposure": {
                    "current_total_risk_percent": round(total, 4),
                    "prospective_risk_percent": prospective,
                    "max_total_risk_percent": max_total,
                    "currency_exposure_percent": currency,
                },
            }

        violations = {
            cur: round(currency.get(cur, 0.0) + prospective, 4)
            for cur in (base, quote)
            if currency.get(cur, 0.0) + prospective > max_cur + 1e-9
        }
        if violations:
            return {
                "symbol": symbol,
                "action": "FOREX_CURRENCY_EXPOSURE_LIMIT",
                "reason": "FOREX_CURRENCY_RISK_EXPOSURE_LIMIT",
                "execution_key": execution_key,
                "forex_exposure": {
                    "pair": [base, quote],
                    "violations": violations,
                    "current_currency_exposure_percent": currency,
                    "prospective_risk_percent": prospective,
                    "max_currency_exposure_percent": max_cur,
                },
            }
        return None

    def _forex_high_impact_news_entry_gate(self, symbol: str) -> dict | None:
        """PUERTA DE ENTRADA: bloquea la operativa en torno a noticias de alto impacto.

        Durante una publicacion macroeconomica relevante el precio se mueve de
        forma erratica, el spread se dispara y la estructura tecnica deja de
        ser fiable. La puerta abre una ventana de exclusion que empieza unos
        minutos ANTES del evento y termina unos minutos DESPUES.

        Determina que divisas afectan al instrumento segun el perfil:
        - `FOREX*`: las dos divisas del par.
        - `GOLD` sobre simbolo ORB de oro: USD.
        - `ORB` sobre indices estadounidenses: USD.
        - Cualquier otro caso queda fuera del control.

        Args:
            symbol: instrumento evaluado.

        Returns:
            `None` si se puede entrar, o un dict de bloqueo con el evento
            responsable y la ventana aplicada.

        Vinculaciones:
        - `services.financial_news_service.load_economic_calendar_state`
          aporta el calendario economico.
        """
        profile = str(self.config.bot_profile or "").upper()
        if not bool(self.config.forex_high_impact_news_guard_enabled):
            return None
        if profile.startswith("FOREX"):
            base, quote = self._forex_pair_currencies(symbol)
            affected_currencies = {base, quote} if base and quote else set()
        elif profile == "GOLD" and is_orb_eligible_symbol(symbol):
            affected_currencies = {"USD"}
        elif profile == "ORB" and is_orb_eligible_symbol(symbol):
            affected_currencies = {"USD"}
        elif profile == "IDX_OPEN" and is_ny_index_open_symbol(symbol):
            affected_currencies = {"USD"}
        else:
            return None
        now = datetime.now(timezone.utc)
        before = timedelta(minutes=max(0, int(self.config.forex_high_impact_news_before_minutes)))
        after = timedelta(minutes=max(0, int(self.config.forex_high_impact_news_after_minutes)))
        calendar = load_economic_calendar_state(self.config.forex_high_impact_news_calendar_path)
        for event in calendar["events"]:
            if not isinstance(event, dict) or str(event.get("impact") or "").upper() != "ALTO":
                continue
            if str(event.get("country") or "").upper() not in affected_currencies:
                continue
            try:
                event_at = datetime.fromisoformat(
                    str(event.get("event_at") or "").replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except ValueError:
                continue
            if event_at - before <= now <= event_at + after:
                return {
                    "symbol": str(symbol),
                    "action": (
                        "FOREX_HIGH_IMPACT_NEWS_ENTRY_BLOCKED"
                        if profile.startswith("FOREX")
                        else "MARKET_HIGH_IMPACT_NEWS_ENTRY_BLOCKED"
                    ),
                    "reason": "HIGH_IMPACT_USD_NEWS_WINDOW",
                    "news_window": {
                        "event": event,
                        "event_at": event_at.isoformat(),
                        "window_start": (event_at - before).isoformat(),
                        "window_end": (event_at + after).isoformat(),
                        "phase": "PRE_EVENT" if now < event_at else "POST_EVENT",
                        "calendar_status": calendar["status"],
                    },
                }
        return None

    def _protect_forex_position_for_high_impact_news(
        self, *, trade, metadata, position, entry_price, current_sl, direction, move_stop
    ) -> dict | None:
        """Protege una posición Forex antes de una noticia con BE neto de spread."""
        gate = self._forex_high_impact_news_entry_gate(trade.get("instrument"))
        window = (gate or {}).get("news_window") or {}
        if not gate or window.get("phase") != "PRE_EVENT":
            return None
        get_tick = getattr(self.provider, "get_current_tick", None)
        if not callable(get_tick):
            return {"action": "FOREX_NEWS_BREAK_EVEN_UNAVAILABLE", "error": "LIVE_TICK_UNAVAILABLE"}
        try:
            tick = get_tick(trade["instrument"]) or {}
            bid, ask = float(tick["bid"]), float(tick["ask"])
            constraints = self.executor.get_symbol_constraints(trade["instrument"]) or {}
            point = max(0.0, float(constraints.get("point") or 0.0))
            digits = int(constraints.get("digits") or 5)
        except (KeyError, TypeError, ValueError, RuntimeError):
            return {"action": "FOREX_NEWS_BREAK_EVEN_UNAVAILABLE", "error": "LIVE_TICK_OR_CONSTRAINTS_UNAVAILABLE"}
        spread = ask - bid
        extra = point * 2
        if direction == "BUY":
            target, executable = max(float(current_sl), float(entry_price) + spread + extra), bid > float(entry_price) + spread + extra
        elif direction == "SELL":
            target, executable = min(float(current_sl), float(entry_price) - spread - extra), ask < float(entry_price) - spread - extra
        else:
            return {"action": "FOREX_NEWS_BREAK_EVEN_UNAVAILABLE", "error": f"INVALID_DIRECTION:{direction}"}
        target = round(target, digits)
        if not executable:
            return {"action": "FOREX_NEWS_BREAK_EVEN_DEFERRED", "reason": "PRICE_HAS_NOT_REACHED_NET_BREAK_EVEN"}
        modification = move_stop(
            position_ticket=str(trade["broker_position_ticket"]),
            stop_loss=target,
            take_profit=float(getattr(position, "tp", 0.0) or 0.0),
            reason="forex_high_impact_news_break_even",
        )
        if not modification.get("modified", False):
            return {"action": "FOREX_NEWS_BREAK_EVEN_REJECTED", "diagnostic": modification}
        confirmed = self.executor.get_position(int(trade["broker_position_ticket"]))
        if confirmed is None or abs(float(getattr(confirmed, "sl", 0.0)) - target) > self._break_even_price_tolerance(trade["instrument"], entry_price):
            return {"action": "FOREX_NEWS_BREAK_EVEN_NOT_CONFIRMED", "expected_stop_loss": target}
        metadata["break_even_activated"] = True
        metadata["break_even_confirmed"] = True
        metadata["break_even_price"] = target
        metadata["break_even_activation_reason"] = "FOREX_HIGH_IMPACT_NEWS_NET_SPREAD"
        details = dict(trade.get("details") or {})
        details["metadata"] = metadata
        self.repository.update_trade(int(trade["id"]), {"stop_loss": target, "details": details})
        return {"action": "FOREX_NEWS_BREAK_EVEN_CONFIRMED", "break_even_price": target, "spread": spread}

    def _forex_due_symbols(self, base_symbols):
        """Analiza perfiles SMC una sola vez por cada vela M5 cerrada.

        El nombre se conserva por compatibilidad. Desde v93 el scheduler se
        aplica a Forex, GOLD y familias sintéticas; ORB conserva el suyo.
        """
        symbols = list(base_symbols or [])
        profile = str(self.config.bot_profile or "").upper()
        family_profile = self._canonical_bot_profile(profile)
        smc_event_profiles = {
            "SYNTHETICS", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP",
        }
        uses_scheduler = (
            profile == "GOLD"
            or profile == "ORB"
            or profile.startswith("FOREX")
            or family_profile in smc_event_profiles
        )
        scheduler_enabled = bool(self.config.forex_event_scheduler_enabled)
        if profile == "ORB":
            scheduler_enabled = scheduler_enabled and bool(
                getattr(self.config, "orb_event_scheduler_enabled", True)
            )
        if family_profile in smc_event_profiles:
            scheduler_enabled = scheduler_enabled and bool(
                getattr(self.config, "smc_event_scheduler_enabled", True)
            )
        if not uses_scheduler or not scheduler_enabled:
            return symbols

        now_utc = datetime.now(timezone.utc)
        next_poll_at = getattr(self, "_event_scheduler_next_poll_at", None)
        if (
            bool(getattr(self.config, "event_scheduler_boundary_guard_enabled", True))
            and isinstance(next_poll_at, datetime)
            and now_utc < next_poll_at
        ):
            self._forex_pending_closed_bar = {}
            self._forex_scheduler_diagnostics = {
                "selected_symbols": len(symbols),
                "due_symbols": 0,
                "candles_available": len(symbols),
                "unchanged_m5_bars": len(symbols),
                "unavailable_symbols": 0,
                "errors": 0,
                "boundary_poll_skipped": True,
                "next_poll_at": next_poll_at.isoformat(),
            }
            return []

        seen = dict(getattr(self, "_forex_last_closed_bar", {}) or {})
        pending = {}
        due = []
        candles_available = unchanged = unavailable = errors = 0
        observed_closed_times = []
        for symbol in symbols:
            try:
                frame = self.provider.get_candles(
                    symbol=symbol,
                    timeframe=str(self.config.forex_event_timeframe),
                    count=3,
                )
                if frame is None or getattr(frame, "empty", True):
                    unavailable += 1
                    continue
                candles_available += 1
                frame = frame.sort_values("time")
                closed = frame.iloc[-2] if len(frame) > 1 else frame.iloc[-1]
                ts = str(closed["time"])
                try:
                    observed_closed_times.append(
                        pd.to_datetime(closed["time"], utc=True).to_pydatetime()
                    )
                except (TypeError, ValueError):
                    pass
                if symbol not in seen or seen.get(symbol) != ts:
                    due.append(symbol)
                    pending[symbol] = ts
                else:
                    unchanged += 1
            except Exception:
                errors += 1
                continue
        self._forex_pending_closed_bar = pending
        next_boundary = None
        if (
            bool(getattr(self.config, "event_scheduler_boundary_guard_enabled", True))
            and symbols
            and candles_available == len(symbols)
            and errors == 0
            and unavailable == 0
        ):
            timeframe = str(self.config.forex_event_timeframe or "M5").upper()
            seconds = int(MultiTimeframeAnalyzer._TIMEFRAME_SECONDS.get(timeframe, 0))
            freshest_closed = max(observed_closed_times) if observed_closed_times else None
            # No aplicar el reloj de pared a proveedores históricos/de prueba:
            # sólo es válido cuando MT5 está entregando la barra vigente.
            recent_market_clock = (
                freshest_closed is not None
                and abs((now_utc - freshest_closed).total_seconds())
                <= (seconds * 2 + 5)
            )
            if seconds > 0 and recent_market_clock:
                next_epoch = (int(now_utc.timestamp() // seconds) + 1) * seconds
                next_boundary = datetime.fromtimestamp(next_epoch, tz=timezone.utc) + timedelta(
                    seconds=max(
                        0.0,
                        float(getattr(self.config, "event_scheduler_boundary_grace_seconds", 2.0)),
                    )
                )
        self._event_scheduler_next_poll_at = next_boundary
        self._forex_scheduler_diagnostics = {
            "selected_symbols": len(symbols),
            "due_symbols": len(due),
            "candles_available": candles_available,
            "unchanged_m5_bars": unchanged,
            "unavailable_symbols": unavailable,
            "errors": errors,
            "boundary_poll_skipped": False,
            "next_poll_at": next_boundary.isoformat() if next_boundary else None,
        }
        return due

    def _commit_forex_processed_symbols(self, results):
        """Marca la vela M5 como procesada sólo tras terminar su análisis."""
        profile = str(self.config.bot_profile or "").upper()
        family_profile = self._canonical_bot_profile(profile)
        if not (
            profile.startswith("FOREX")
            or profile == "GOLD"
            or profile == "ORB"
            or family_profile in {"SYNTHETICS", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"}
        ):
            return
        pending = dict(getattr(self, "_forex_pending_closed_bar", {}) or {})
        if not pending:
            return
        seen = dict(getattr(self, "_forex_last_closed_bar", {}) or {})
        for row in (results or []):
            if not isinstance(row, dict):
                continue
            symbol = str(row.get("symbol") or "")
            action = str(row.get("action") or row.get("state") or "").upper()
            # Un error técnico conserva la vela pendiente para reintento.
            if symbol in pending and "ERROR" not in action:
                seen[symbol] = pending[symbol]
            elif symbol in pending:
                # Un fallo técnico debe poder reintentarse en el próximo ciclo,
                # incluso si aún no llega la siguiente frontera M5.
                self._event_scheduler_next_poll_at = None
        self._forex_last_closed_bar = seen
        self._forex_pending_closed_bar = {}

    def _position_limit_result(self, symbol: str, execution_key: str):
        """Devuelve None si se puede continuar o un resultado de bloqueo detallado."""
        enforce_limits = bool(self.config.execution_enabled or self.config.enforce_position_limits_in_dry_run)
        diagnostics = self._open_trade_diagnostics(symbol)
        diagnostics["limits_enforced"] = enforce_limits

        if not enforce_limits:
            return None

        forex_guard = self._forex_exposure_guard(symbol, execution_key)
        if forex_guard is not None:
            forex_guard["position_diagnostics"] = diagnostics
            return forex_guard

        required_slots = 2 if bool(self.config.split_entries_enabled) else 1
        diagnostics["required_slots"] = required_slots

        if diagnostics["total_open"] + required_slots > diagnostics["max_total"]:
            return {
                "symbol": symbol,
                "action": "MAX_TOTAL_OPEN_POSITIONS",
                "reason": "MAX_TOTAL_OPEN_POSITIONS_REACHED",
                "execution_key": execution_key,
                "position_diagnostics": diagnostics,
            }

        if diagnostics["symbol_open"] + required_slots > diagnostics["max_per_symbol"]:
            return {
                "symbol": symbol,
                "action": "POSITION_ALREADY_OPEN_FOR_SYMBOL",
                "reason": "MAX_OPEN_POSITIONS_PER_SYMBOL_REACHED",
                "execution_key": execution_key,
                "position_diagnostics": diagnostics,
            }

        return None

    @staticmethod
    def _trade_metadata(trade: dict) -> dict:
        """Extrae con seguridad el diccionario `metadata` de una operación.

        Navega `trade["details"]["metadata"]` devolviendo `{}` ante cualquier
        eslabon ausente o con tipo inesperado, de modo que quien llama pueda
        usar `.get()` sin comprobaciones previas.
        """
        details = trade.get("details") or {}
        if isinstance(details, dict):
            metadata = details.get("metadata") or {}
            return dict(metadata) if isinstance(metadata, dict) else {}
        return {}

    def _break_even_initial_stop(self, trade: dict, metadata: dict) -> float | None:
        """Recupera el stop ORIGINAL de la operación para medir el avance en R.

        Es imprescindible usar el stop inicial y no el actual: una vez movido
        el stop a break-even, calcular R contra el stop vigente daria una
        distancia de riesgo casi nula y falsearia por completo la medida.

        Prueba por orden de fiabilidad: el valor explicito persistido al abrir,
        el registrado en la validacion de stop, y por ultimo el stop actual de
        la operacion como respaldo.

        Returns:
            El stop inicial positivo, o `None` si ningun candidato sirve.
        """
        # Prioridad: valor explícito persistido al abrir la operación.
        candidates = [
            metadata.get("initial_stop_loss"),
            (metadata.get("stop_validation") or {}).get("stop_loss")
                if isinstance(metadata.get("stop_validation"), dict) else None,
            trade.get("stop_loss"),
        ]
        for value in candidates:
            try:
                value = float(value)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                continue
        return None

    def _break_even_target_stop(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        profit_lock_amount: float = 0.0,
    ) -> tuple[float, float]:
        """Calcula BE neto de spread más offset, hacia el lado favorable del trade.

        ``profit_lock_amount`` (en precio, no en R) suma una distancia extra al
        offset para que el BE asegure una fracción de la ganancia ya alcanzada,
        en lugar de limitarse a cubrir spread/costes de la operación.
        """
        offset_points = max(0, int(self.config.break_even_offset_points))
        point = 0.0
        digits = None
        get_constraints = getattr(self.executor, "get_symbol_constraints", None)
        if callable(get_constraints):
            try:
                constraints = get_constraints(symbol) or {}
                point = float(constraints.get("point", 0.0) or 0.0)
                digits = constraints.get("digits")
            except Exception:
                point = 0.0
                digits = None

        offset = point * offset_points
        get_tick = getattr(self.provider, "get_current_tick", None)
        if callable(get_tick):
            try:
                tick = get_tick(symbol) or {}
                spread = max(
                    0.0,
                    float(tick.get("ask") or 0.0) - float(tick.get("bid") or 0.0),
                )
                offset += spread
            except (TypeError, ValueError, RuntimeError):
                # Conserva el offset mínimo protector si el tick puntual no está disponible.
                pass
        offset += max(0.0, float(profit_lock_amount or 0.0))
        target = float(entry_price) + offset if str(direction).upper() == "BUY" else float(entry_price) - offset
        if digits is not None:
            target = round(target, max(0, int(digits)))
        return float(target), float(offset)

    def _break_even_tp1_completion(self, trade: dict, metadata: dict) -> dict:
        """
        Detecta si la pierna TP1 hermana ya cerró con beneficio.

        Esto hace persistente el evento 1R: aunque el precio toque TP1 y retroceda
        antes de la siguiente lectura del monitor, el RUNNER sigue quedando elegible
        para BE+offset.
        """
        if not bool(self.config.split_entries_enabled):
            return {"completed": False, "reason": "SPLIT_DISABLED"}

        if str(metadata.get("trade_leg") or "").upper() != "RUNNER":
            return {"completed": False, "reason": "NOT_RUNNER"}

        parent_key = str(metadata.get("parent_execution_key") or "").strip()
        if not parent_key:
            return {"completed": False, "reason": "PARENT_EXECUTION_KEY_MISSING"}

        getter = getattr(self.repository, "get_trade_by_execution_key", None)
        if not callable(getter):
            return {"completed": False, "reason": "REPOSITORY_LOOKUP_UNAVAILABLE"}

        tp1 = getter(f"{parent_key}:TP1")
        if not tp1:
            return {"completed": False, "reason": "TP1_NOT_FOUND"}

        status = str(tp1.get("status") or "").upper()
        result = str(tp1.get("result") or "").upper()
        realized_rr = tp1.get("realized_rr")
        try:
            realized_rr = float(realized_rr) if realized_rr is not None else None
        except (TypeError, ValueError):
            realized_rr = None

        # WIN es la evidencia principal después del sync de MT5. Como respaldo,
        # aceptamos un RR claramente positivo cercano al objetivo de 1R.
        profitable_tp1 = result == "WIN" or (realized_rr is not None and realized_rr >= 0.75)
        completed = status == "CLOSED" and profitable_tp1
        return {
            "completed": bool(completed),
            "reason": "TP1_CLOSED_IN_PROFIT" if completed else "TP1_NOT_COMPLETED_IN_PROFIT",
            "tp1_trade_id": tp1.get("id"),
            "tp1_status": status,
            "tp1_result": result,
            "tp1_realized_rr": realized_rr,
            "tp1_exit_price": tp1.get("exit_price"),
        }

    def _break_even_price_tolerance(self, symbol: str, entry_price: float) -> float:
        """Tolerancia de confirmación alineada al tick/point real del broker."""
        tolerance = max(abs(float(entry_price)) * 1e-10, 1e-8)
        get_constraints = getattr(self.executor, "get_symbol_constraints", None)
        if callable(get_constraints):
            try:
                constraints = get_constraints(symbol) or {}
                point = abs(float(constraints.get("point", 0.0) or 0.0))
                tick_size = abs(float(constraints.get("tick_size", 0.0) or 0.0))
                broker_step = max(point, tick_size)
                if broker_step > 0:
                    tolerance = max(tolerance, broker_step * 0.51)
            except Exception:
                pass
        return float(tolerance)

    def _update_excursion_metrics(
        self,
        trade: dict,
        metadata: dict,
        current_rr: float | None,
        current_price: float,
    ) -> tuple[dict, bool]:
        """Actualiza MFE/MAE muestreados por el monitor de posiciones.

        MFE = máximo recorrido favorable en R.
        MAE = máximo recorrido adverso en R (valor positivo).
        """
        if current_rr is None:
            return metadata, False

        rr_value = float(current_rr)
        previous_mfe = float(metadata.get("max_favorable_excursion_rr", 0.0) or 0.0)
        previous_mae = float(metadata.get("max_adverse_excursion_rr", 0.0) or 0.0)
        new_mfe = max(previous_mfe, rr_value, 0.0)
        new_mae = max(previous_mae, -rr_value, 0.0)

        step = max(0.0, float(self.config.excursion_persist_step_rr))
        changed = (
            new_mfe >= previous_mfe + step - 1e-9
            or new_mae >= previous_mae + step - 1e-9
        )
        if not changed:
            return metadata, False

        metadata["max_favorable_excursion_rr"] = round(new_mfe, 4)
        metadata["max_adverse_excursion_rr"] = round(new_mae, 4)
        metadata["excursion_last_sample_rr"] = round(rr_value, 4)
        metadata["excursion_last_sample_price"] = float(current_price)
        metadata["excursion_last_sample_time"] = datetime.now(timezone.utc).isoformat()

        if new_mfe > previous_mfe + 1e-9:
            metadata["mfe_price"] = float(current_price)
            metadata["mfe_time"] = metadata["excursion_last_sample_time"]
        if new_mae > previous_mae + 1e-9:
            metadata["mae_price"] = float(current_price)
            metadata["mae_time"] = metadata["excursion_last_sample_time"]

        details = dict(trade.get("details") or {})
        details["metadata"] = metadata
        self.repository.update_trade(
            int(trade["id"]),
            {"details": details},
        )
        return metadata, True

    def _analysis_invalidation_exit(
        self,
        *,
        trade: dict,
        metadata: dict,
        current_rr: float | None,
        close_position,
    ) -> dict:
        """Cierra una pérdida controlada cuando la tesis ACTUAL ya no es válida.

        Cuenta sólo velas M15 cerradas distintas (más contexto que M5), no
        las lecturas del monitor ni las reevaluaciones del mismo candle. El
        comportamiento del precio que determina la invalidación (dirección,
        ruptura de estructura, etc.) se sigue analizando en M5 vía
        `current_view`. La antigüedad de una señal bloquea entradas nuevas,
        pero no invalida una posición abierta.
        """
        result = {"managed": False, "closed": False, "reason": None}
        if not bool(getattr(self.config, "analysis_invalidation_exit_enabled", True)):
            return result
        if current_rr is None or not callable(close_position):
            return result

        # NY_INDEX_OPEN: el cierre defensivo por invalidación de análisis
        # sólo debe operar dentro de la ventana propia de la estrategia
        # (apertura NY + `m5_confirmation_window_minutes`, 20 min por
        # defecto). Si la entrada quedó abierta y se sigue gestionando horas
        # después (fuera de esa ventana), no se cierra anticipadamente por
        # este mecanismo: se deja que el SL/TP/break-even estructural
        # gestionen la salida con normalidad.
        if str(metadata.get("strategy_name") or "").upper() == "NY_INDEX_OPEN":
            ny_strategy = getattr(self, "ny_index_open_strategy", None)
            if ny_strategy is not None:
                try:
                    now_ny, _bias_start, _confirm_start, open_ny, confirmation_deadline_ny = (
                        ny_strategy._session_bounds(datetime.now(timezone.utc))
                    )
                    if not (open_ny <= now_ny < confirmation_deadline_ny):
                        return result
                except Exception:
                    # Si no se puede determinar la ventana, no bloqueamos el
                    # mecanismo de protección por prudencia.
                    pass

        symbol = str(trade.get("instrument") or "")
        direction = str(trade.get("direction") or "").upper()
        current_view = dict(
            (getattr(self, "_current_strategy_view_cache", {}) or {}).get(symbol) or {}
        )
        evaluated_at = str(current_view.get("evaluated_at") or "")
        if not current_view or not evaluated_at:
            return result

        view_direction = str(current_view.get("direction") or "").upper()
        state = str(current_view.get("state") or current_view.get("decision") or "").upper()
        reason = str(current_view.get("reason") or "").upper()
        freshness_only = state in {
            "STALE_M5_SIGNAL",
            "WAITING_NEW_M5_BAR",
        } or reason in {
            "M5_CONFIRMATION_TOO_OLD_FOR_LIVE_ENTRY",
            "WAITING_NEW_M5_BAR",
        }
        opposite_direction = bool(
            direction in {"BUY", "SELL"}
            and view_direction in {"BUY", "SELL"}
            and view_direction != direction
        )
        structure_break = str(
            current_view.get("structure_break")
            or current_view.get("bos_choch")
            or ""
        ).upper()
        opposite_structure = (
            direction == "BUY"
            and any(token in structure_break for token in ("BEARISH", "SELL", "DOWN"))
        ) or (
            direction == "SELL"
            and any(token in structure_break for token in ("BULLISH", "BUY", "UP"))
        )
        structural_state = state in {
            "NO_H1_CONTEXT",
            "DIRECTION_POLICY_BLOCKED",
            "INVALID_DIRECTION",
        }
        invalid_now = not freshness_only and bool(
            opposite_direction
            or opposite_structure
            or bool(current_view.get("htf_blocked", False))
            or bool(current_view.get("critical_failures") or [])
            or structural_state
        )

        diagnostics = current_view.get("diagnostics")
        diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
        signal_age = diagnostics.get("signal_age")
        signal_age = signal_age if isinstance(signal_age, dict) else {}
        # v106: el streak de confirmación avanza por vela M15 cerrada (más
        # contexto que M5), aunque `invalid_now` sigue evaluando el
        # comportamiento del precio en M5 vía `current_view`/diagnostics. Si
        # el análisis todavía no expone la vela M15 (paths de test/legacy),
        # se cae de nuevo a la clave M5 anterior para no romper el flujo.
        m15_diag = diagnostics.get("m15")
        m15_diag = m15_diag if isinstance(m15_diag, dict) else {}
        candle_key = str(
            current_view.get("latest_closed_m15_candle_time")
            or m15_diag.get("last_candle_time")
            or current_view.get("latest_closed_candle_time")
            or signal_age.get("latest_closed_candle_time")
            or current_view.get("signal_time")
            or signal_age.get("signal_time")
            or ""
        )
        evaluation_key = candle_key or evaluated_at
        previous_evaluation = str(metadata.get("analysis_exit_last_candle_key") or "")
        if evaluation_key != previous_evaluation:
            previous_streak = int(metadata.get("analysis_exit_invalid_streak", 0) or 0)
            streak = previous_streak + 1 if invalid_now else 0
            if freshness_only:
                streak = 0
            metadata["analysis_exit_invalid_streak"] = streak
            metadata["analysis_exit_last_candle_key"] = evaluation_key
            metadata["analysis_exit_last_evaluated_at"] = evaluated_at
            metadata["analysis_exit_last_state"] = state or None
            metadata["analysis_exit_last_reason"] = current_view.get("reason")
            metadata["analysis_exit_last_valid"] = bool(current_view.get("valid", False))
            details = dict(trade.get("details") or {})
            details["metadata"] = metadata
            self.repository.update_trade(int(trade["id"]), {"details": details})
        else:
            streak = int(metadata.get("analysis_exit_invalid_streak", 0) or 0)

        if not invalid_now:
            return result

        entry_time = trade.get("entry_time")
        try:
            opened_at = pd.to_datetime(entry_time, utc=True, errors="raise").to_pydatetime()
            open_minutes = max(
                0.0,
                (datetime.now(timezone.utc) - opened_at).total_seconds() / 60.0,
            )
        except Exception:
            # Si falta la hora no forzamos un cierre anticipado a ciegas.
            return result
        min_minutes = max(
            0.0,
            float(getattr(self.config, "analysis_invalidation_min_open_minutes", 10.0)),
        )
        required = max(
            2,
            int(getattr(self.config, "analysis_invalidation_confirmations", 2)),
        )
        if open_minutes + 1e-9 < min_minutes or streak < required:
            return result

        rr_now = float(current_rr)
        mfe = float(metadata.get("max_favorable_excursion_rr", 0.0) or 0.0)
        # v105: el criterio de cierre es la invalidación estructural en sí
        # misma (dirección/estructura del análisis cambió respecto a la
        # entrada, ya confirmada arriba por `streak >= required` velas M5
        # consecutivas), no un umbral de pérdida a tolerar. Esperar a un RR
        # negativo específico (-0.35R, valor antiguo) permitía que la posición
        # siguiera cayendo hasta el Stop Loss pleno en sintéticos, donde el
        # precio suele saltar de "levemente en contra" a SL en una sola vela.
        recovery_mfe = float(getattr(self.config, "analysis_recovery_mfe_rr", 0.20))
        recovery_threshold = float(
            getattr(self.config, "analysis_recovery_exit_rr", -0.10)
        )
        recovery_exit = mfe + 1e-9 >= recovery_mfe and rr_now <= recovery_threshold + 1e-9

        exit_reason = (
            "analysis_invalid_recovery_protection"
            if recovery_exit
            else "analysis_invalid_loss_cap"
        )
        ticket = str(trade.get("broker_position_ticket") or "")
        if not ticket:
            return result
        close_result = close_position(
            position_ticket=ticket,
            reason=exit_reason,
        )
        close_payload = close_result if isinstance(close_result, dict) else {}
        closed = bool(
            close_payload.get("closed", False)
            or str(close_payload.get("status") or "").upper() == "CLOSED"
        )
        metadata["analysis_exit_triggered"] = closed
        metadata["analysis_exit_reason"] = exit_reason
        metadata["analysis_exit_rr"] = round(rr_now, 4)
        metadata["analysis_exit_mfe_rr"] = round(mfe, 4)
        metadata["analysis_exit_state"] = state or None
        metadata["analysis_exit_evaluated_at"] = evaluated_at
        metadata["analysis_exit_requested_at"] = datetime.now(timezone.utc).isoformat()
        details = dict(trade.get("details") or {})
        details["metadata"] = metadata
        self.repository.update_trade(int(trade["id"]), {"details": details})
        self._persist_audit_event(
            "ANALYSIS_INVALIDATION_EXIT",
            instrument=symbol,
            action="POSITION_CLOSED_EARLY" if closed else "POSITION_CLOSE_REJECTED",
            reason=exit_reason,
            broker_position_ticket=ticket,
            payload={
                "trade_id": trade.get("id"),
                "current_rr": rr_now,
                "mfe_rr": mfe,
                "invalid_streak": streak,
                "current_strategy_view": current_view,
                "close_result": close_result,
            },
        )
        result.update({
            "managed": True,
            "closed": closed,
            "reason": exit_reason,
            "trade_id": trade.get("id"),
            "ticket": ticket,
            "symbol": symbol,
            "current_rr": rr_now,
            "mfe_rr": mfe,
            "invalid_streak": streak,
            "state": state,
            "close_result": close_result,
        })
        return result

    def _manage_runner_extension(
        self,
        *,
        trade: dict,
        position,
        metadata: dict,
        initial_stop_loss: float,
        current_rr: float | None,
        move_stop,
    ) -> dict:
        """Gestiona extensión dinámica del RUNNER con profit-lock estructural.

        SMC: 2R -> evaluar -> 3R -> evaluar -> 4R máximo.
        ORB: conserva 2R -> 3R -> 4R.

        Regla defensiva: al alcanzar un trigger primero se asegura el profit lock
        en MT5. Sólo después se evalúa si vale la pena continuar. Así, un error
        de datos/análisis nunca devuelve un RUNNER de 2R hasta Break Even.
        """
        result = {
            "managed": False,
            "closed": False,
            "extended": False,
            "stage": None,
            "error": None,
        }
        synthetic_profile = str(
            metadata.get("bot_profile") or self.config.bot_profile or ""
        ).upper()
        if self._is_synthetics_profile_name(synthetic_profile):
            result["reason"] = "SYNTHETICS_FIXED_TP2_TARGET"
            return result
        if str(metadata.get("bot_profile") or self.config.bot_profile or "").upper().startswith("FOREX"):
            result["reason"] = "FOREX_FIXED_TP2_TARGET"
            return result
        if not bool(self.config.runner_extension_enabled):
            return result
        if str(metadata.get("trade_leg") or "").upper() != "RUNNER":
            return result
        if current_rr is None:
            return result

        current_rr = float(current_rr)
        ticket = str(trade.get("broker_position_ticket") or "")
        symbol = str(trade.get("instrument") or "")
        direction = str(trade.get("direction") or "").upper()
        entry_price = float(getattr(position, "price_open", 0.0) or 0.0)
        if not ticket or entry_price <= 0 or direction not in {"BUY", "SELL"}:
            return result

        trade_executor = getattr(self.lifecycle_manager, "trade_executor", None)
        close_position = getattr(trade_executor, "close_position", None)
        if not callable(close_position):
            result["error"] = "TRADE_EXECUTOR_DOES_NOT_SUPPORT_RUNNER_CLOSE"
            return result

        strategy_name = str(metadata.get("strategy_name") or "SMC").upper()
        bot_profile = str(metadata.get("bot_profile") or self.config.bot_profile or "").upper()
        is_orb_runner = strategy_name == "ORB_NEW_YORK"
        is_forex_runner = self._uses_forex_style_smc_management(bot_profile)

        if is_forex_runner:
            max_target_rr = float(self.config.forex_runner_max_target_rr)
            stages = [
                (
                    "2R_TO_3R",
                    float(self.config.forex_runner_initial_target_rr),
                    float(self.config.forex_runner_tp3_lock_rr),
                    3.0,
                ),
                (
                    "3R_TO_4R",
                    3.0,
                    float(self.config.forex_runner_tp4_pre_eval_lock_rr),
                    max_target_rr,
                ),
            ]
        else:
            max_target_rr = (
                float(self.config.runner_extension_max_target_rr)
                if is_orb_runner
                else float(self.config.smc_runner_max_target_rr)
            )
            stages = [
                (
                    "2R_TO_3R",
                    float(self.config.runner_extension_first_trigger_rr),
                    float(self.config.runner_extension_first_lock_rr),
                    3.0,
                ),
            ]
            if max_target_rr > 3.0:
                stages.append(
                    (
                        "3R_TO_4R",
                        float(self.config.runner_extension_second_trigger_rr),
                        float(self.config.runner_extension_second_lock_rr),
                        max_target_rr,
                    )
                )
        completed_stages = set(metadata.get("runner_extension_completed_stages") or [])

        # v65: si SMC ya fue extendido a TP3, al alcanzar ~2.5R se protege
        # automáticamente +2R sin esperar a que llegue al TP3.
        guard_stage = "SMC_TP3_GUARD_2R"
        if (
            not is_orb_runner
            and not is_forex_runner
            and "2R_TO_3R" in completed_stages
            and guard_stage not in completed_stages
            and current_rr + 1e-9 >= float(self.config.smc_runner_tp3_guard_trigger_rr)
        ):
            guard_lock_rr = float(self.config.smc_runner_tp3_guard_lock_rr)
            guard_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                guard_lock_rr,
            )
            current_sl = float(getattr(position, "sl", 0.0) or 0.0)
            if direction == "BUY":
                guard_sl = max(current_sl, guard_price)
            else:
                guard_sl = guard_price if current_sl <= 0 else min(current_sl, guard_price)
            target_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                max_target_rr,
            )
            guard_modification = move_stop(
                position_ticket=ticket,
                stop_loss=float(guard_sl),
                take_profit=float(target_price),
                reason="smc_runner_tp3_guard_lock_2r",
            )
            if guard_modification.get("modified", False):
                completed_stages.add(guard_stage)
                metadata["runner_extension_completed_stages"] = sorted(completed_stages)
                metadata["runner_profit_lock_rr"] = guard_lock_rr
                metadata["runner_profit_lock_price"] = float(guard_sl)
                metadata["runner_extension_stage"] = "PROTECTED_FOR_TP3"
                metadata["runner_next_evaluation_rr"] = max_target_rr
                metadata["runner_extension_updated_at"] = datetime.now(timezone.utc).isoformat()
                details = dict(trade.get("details") or {})
                details["metadata"] = metadata
                self.repository.update_trade(
                    int(trade["id"]),
                    {
                        "stop_loss": float(guard_sl),
                        "take_profit": float(target_price),
                        "planned_rr": current_logical_target_rr,
                        "details": details,
                    },
                )
                result.update({
                    "managed": True,
                    "extended": True,
                    "stage": guard_stage,
                    "profit_lock_rr": guard_lock_rr,
                    "profit_lock_price": float(guard_sl),
                    "target_rr": max_target_rr,
                    "target_price": float(target_price),
                })
                return result

        # v66: si SMC fue extendido de TP3 hacia TP4, al alcanzar ~3.5R
        # se asegura +3R antes de intentar completar TP4.
        tp4_guard_stage = "SMC_TP4_GUARD_3R"
        if (
            not is_orb_runner
            and not is_forex_runner
            and "3R_TO_4R" in completed_stages
            and tp4_guard_stage not in completed_stages
            and current_rr + 1e-9 >= float(self.config.smc_runner_tp4_guard_trigger_rr)
        ):
            guard_lock_rr = float(self.config.smc_runner_tp4_guard_lock_rr)
            guard_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                guard_lock_rr,
            )
            current_sl = float(getattr(position, "sl", 0.0) or 0.0)
            if direction == "BUY":
                guard_sl = max(current_sl, guard_price)
            else:
                guard_sl = guard_price if current_sl <= 0 else min(current_sl, guard_price)
            target_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                max_target_rr,
            )
            guard_modification = move_stop(
                position_ticket=ticket,
                stop_loss=float(guard_sl),
                take_profit=float(target_price),
                reason="smc_runner_tp4_guard_lock_3r",
            )
            if guard_modification.get("modified", False):
                completed_stages.add(tp4_guard_stage)
                metadata["runner_extension_completed_stages"] = sorted(completed_stages)
                metadata["runner_profit_lock_rr"] = guard_lock_rr
                metadata["runner_profit_lock_price"] = float(guard_sl)
                metadata["runner_extension_stage"] = "PROTECTED_FOR_TP4"
                metadata["runner_next_evaluation_rr"] = max_target_rr
                metadata["runner_extension_updated_at"] = datetime.now(timezone.utc).isoformat()
                details = dict(trade.get("details") or {})
                details["metadata"] = metadata
                self.repository.update_trade(
                    int(trade["id"]),
                    {
                        "stop_loss": float(guard_sl),
                        "take_profit": float(target_price),
                        "planned_rr": max_target_rr,
                        "details": details,
                    },
                )
                result.update({
                    "managed": True,
                    "extended": True,
                    "stage": tp4_guard_stage,
                    "profit_lock_rr": guard_lock_rr,
                    "profit_lock_price": float(guard_sl),
                    "target_rr": max_target_rr,
                    "target_price": float(target_price),
                })
                return result

        for stage_name, trigger_rr, lock_rr, next_target_rr in stages:
            if stage_name in completed_stages or current_rr + 1e-9 < trigger_rr:
                continue

            # ------------------------------------------------------------
            # 1) PROTEGER GANANCIA ANTES DE CUALQUIER EVALUACIÓN
            # ------------------------------------------------------------
            lock_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                lock_rr,
            )
            target_price = rr_price(
                entry_price,
                float(initial_stop_loss),
                direction,
                max_target_rr,
            )

            current_sl = float(getattr(position, "sl", 0.0) or 0.0)
            if direction == "BUY":
                protected_sl = max(current_sl, lock_price)
            else:
                protected_sl = lock_price if current_sl <= 0 else min(current_sl, lock_price)

            modification = move_stop(
                position_ticket=ticket,
                stop_loss=float(protected_sl),
                take_profit=float(target_price),
                reason=f"runner_profit_lock_{stage_name.lower()}",
            )
            if not modification.get("modified", False):
                result.update({
                    "managed": True,
                    "stage": stage_name,
                    "error": modification.get("error") or "RUNNER_PROFIT_LOCK_REJECTED",
                    "diagnostic": modification,
                })
                return result

            tolerance = self._break_even_price_tolerance(symbol, entry_price)
            confirmed_position = self.executor.get_position(int(ticket))
            if confirmed_position is None:
                result.update({
                    "managed": True,
                    "stage": stage_name,
                    "error": "RUNNER_PROFIT_LOCK_POSITION_NOT_FOUND",
                })
                return result

            broker_sl = float(getattr(confirmed_position, "sl", 0.0) or 0.0)
            if abs(broker_sl - float(protected_sl)) > tolerance:
                result.update({
                    "managed": True,
                    "stage": stage_name,
                    "error": "RUNNER_PROFIT_LOCK_NOT_CONFIRMED_BY_BROKER",
                    "expected_stop_loss": float(protected_sl),
                    "broker_stop_loss": broker_sl,
                })
                return result

            current_logical_target_rr = float(
                metadata.get("runner_logical_target_rr")
                or metadata.get("runner_initial_target_rr")
                or (self.config.forex_runner_initial_target_rr if is_forex_runner else max_target_rr)
            )
            metadata["runner_profit_lock_rr"] = float(lock_rr)
            metadata["runner_profit_lock_price"] = float(protected_sl)
            metadata["runner_max_target_rr"] = max_target_rr
            metadata["runner_candidate_target_rr"] = float(next_target_rr)
            metadata["runner_broker_safety_target_rr"] = max_target_rr if is_forex_runner else current_logical_target_rr
            metadata["runner_target_price"] = float(target_price)
            metadata["runner_extension_updated_at"] = datetime.now(timezone.utc).isoformat()

            details = dict(trade.get("details") or {})
            details["metadata"] = metadata
            self.repository.update_trade(
                int(trade["id"]),
                {
                    "stop_loss": float(protected_sl),
                    "take_profit": float(target_price),
                    "planned_rr": max_target_rr,
                    "details": details,
                },
            )

            # ------------------------------------------------------------
            # 2) EVALUAR SI EXISTE CONTINUACIÓN
            # ------------------------------------------------------------
            try:
                candles = self.provider.get_candles(
                    symbol,
                    str(self.config.runner_extension_timeframe),
                    count=int(self.config.runner_extension_candle_count),
                )
                decision = evaluate_runner_continuation(
                    candles,
                    direction=direction,
                    stage_rr=trigger_rr,
                )
            except Exception as exc:
                # El profit lock ya quedó confirmado en broker. Ante error de
                # análisis no forzamos cierre a ciegas, pero tampoco devolvemos
                # la ganancia protegida.
                metadata.setdefault("runner_extension_decisions", []).append({
                    "stage": stage_name,
                    "trigger_rr": trigger_rr,
                    "current_rr": round(current_rr, 4),
                    "continue_runner": None,
                    "reason": "ANALYSIS_ERROR_AFTER_PROFIT_LOCK",
                    "error": str(exc),
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                })
                details = dict(trade.get("details") or {})
                details["metadata"] = metadata
                self.repository.update_trade(int(trade["id"]), {"details": details})
                result.update({
                    "managed": True,
                    "stage": stage_name,
                    "profit_lock_rr": lock_rr,
                    "profit_lock_price": float(protected_sl),
                    "error": f"RUNNER_EXTENSION_ANALYSIS_ERROR_PROFIT_ALREADY_LOCKED:{exc}",
                })
                return result

            metadata.setdefault("runner_extension_decisions", []).append({
                "stage": stage_name,
                "trigger_rr": trigger_rr,
                "current_rr": round(current_rr, 4),
                "continue_runner": bool(decision.continue_runner),
                "reason": decision.reason,
                "diagnostics": decision.diagnostics,
                "evaluated_at": datetime.now(timezone.utc).isoformat(),
            })

            # ------------------------------------------------------------
            # 3a) SIN CONTINUACIÓN: cerrar con beneficio ya protegido
            # ------------------------------------------------------------
            if not decision.continue_runner:
                metadata["runner_exit_reason"] = f"{stage_name}:{decision.reason}"
                metadata["runner_exit_requested_rr"] = round(current_rr, 4)
                details = dict(trade.get("details") or {})
                details["metadata"] = metadata
                self.repository.update_trade(int(trade["id"]), {"details": details})

                close_result = close_position(
                    position_ticket=ticket,
                    reason=f"runner_extension_{stage_name.lower()}_no_continuation",
                )
                result.update({
                    "managed": True,
                    "closed": bool((close_result or {}).get("closed", False)),
                    "stage": stage_name,
                    "decision": decision.reason,
                    "profit_lock_rr": lock_rr,
                    "profit_lock_price": float(protected_sl),
                    "close_result": close_result,
                })
                return result

            # ------------------------------------------------------------
            # 3b) CONTINUACIÓN: habilitar siguiente objetivo
            # ------------------------------------------------------------
            if is_forex_runner and stage_name == "3R_TO_4R":
                # El mercado ganó el derecho a TP4: elevar protección a +2.5R.
                tp4_lock_rr = float(self.config.forex_runner_tp4_lock_rr)
                tp4_lock_price = rr_price(
                    entry_price,
                    float(initial_stop_loss),
                    direction,
                    tp4_lock_rr,
                )
                current_sl = float(getattr(confirmed_position, "sl", 0.0) or 0.0)
                if direction == "BUY":
                    tp4_protected_sl = max(current_sl, tp4_lock_price)
                else:
                    tp4_protected_sl = (
                        tp4_lock_price if current_sl <= 0 else min(current_sl, tp4_lock_price)
                    )
                post_eval_lock = move_stop(
                    position_ticket=ticket,
                    stop_loss=float(tp4_protected_sl),
                    take_profit=float(target_price),
                    reason="forex_runner_tp4_lock_2_5r",
                )
                if post_eval_lock.get("modified", False):
                    protected_sl = float(tp4_protected_sl)
                    lock_rr = tp4_lock_rr
                    metadata["runner_profit_lock_rr"] = tp4_lock_rr
                    metadata["runner_profit_lock_price"] = float(tp4_protected_sl)
                    self.repository.update_trade(
                        int(trade["id"]),
                        {
                            "stop_loss": float(tp4_protected_sl),
                            "planned_rr": 4.0,
                        },
                    )

            completed_stages.add(stage_name)
            metadata["runner_extension_completed_stages"] = sorted(completed_stages)
            if is_forex_runner:
                metadata["runner_logical_target_rr"] = float(next_target_rr)
                metadata["runner_candidate_target_rr"] = None
                self.repository.update_trade(
                    int(trade["id"]),
                    {"planned_rr": float(next_target_rr)},
                )
            metadata["runner_extension_stage"] = (
                "EXTENDED_TO_3R" if stage_name == "2R_TO_3R" else "EXTENDED_TO_4R"
            )
            if stage_name == "2R_TO_3R":
                metadata["runner_next_evaluation_rr"] = (
                    3.0
                    if is_forex_runner
                    else (
                        max_target_rr
                        if not is_orb_runner
                        else float(self.config.runner_extension_second_trigger_rr)
                    )
                )
            else:
                metadata["runner_next_evaluation_rr"] = max_target_rr
            details = dict(trade.get("details") or {})
            details["metadata"] = metadata
            self.repository.update_trade(int(trade["id"]), {"details": details})

            result.update({
                "managed": True,
                "extended": True,
                "stage": stage_name,
                "decision": decision.reason,
                "profit_lock_rr": lock_rr,
                "profit_lock_price": float(protected_sl),
                "target_rr": float(next_target_rr if is_forex_runner else max_target_rr),
                "broker_safety_target_rr": float(max_target_rr) if is_forex_runner else None,
                "target_price": float(target_price),
                "next_target_rr": next_target_rr,
            })

            position = confirmed_position

        return result

    def _persist_live_position_market_snapshots(self, snapshots) -> dict:
        """Persiste telemetría ligera de posiciones abiertas en cada monitor.

        Es deliberadamente independiente de SMC / Forex / ORB. No genera gráficos
        ni reanaliza la estrategia; sólo hace durable el estado MT5 actual para que
        el dashboard central pueda leerlo desde SQLAlchemy.
        """
        writer = getattr(self.repository, "upsert_trade_visual_audit", None)
        if not callable(writer):
            return {"updated": 0, "errors": []}

        updated = 0
        errors = []
        strategy_cache = dict(getattr(self, "_current_strategy_view_cache", {}) or {})
        now_iso = datetime.now(timezone.utc).isoformat()

        for snapshot in (snapshots or []):
            if not isinstance(snapshot, dict):
                continue
            trade_id = snapshot.get("trade_id")
            symbol = str(snapshot.get("symbol") or "")
            if not trade_id or not symbol:
                continue

            latest_market = dict(snapshot)
            current_view = strategy_cache.get(symbol)
            if isinstance(current_view, dict):
                latest_market["current_strategy_view"] = current_view
                latest_market["strategy_evaluated_at"] = current_view.get("evaluated_at")
            latest_market["market_evaluated_at"] = now_iso
            latest_market["telemetry_mode"] = "LIVE_POSITION_MONITOR"
            latest_market["bot_profile"] = str(self.config.bot_profile).upper()
            latest_market["daemon_magic"] = int(self.config.magic)

            try:
                writer(
                    int(trade_id),
                    instrument=symbol,
                    bot_profile=str(self.config.bot_profile).upper(),
                    daemon_magic=int(self.config.magic),
                    broker_position_ticket=snapshot.get("ticket"),
                    latest_market=latest_market,
                    source=self.config.source,
                    updated_at=now_iso,
                )
                updated += 1
            except Exception as exc:
                errors.append({
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "error": str(exc),
                })

        return {"updated": updated, "errors": errors, "updated_at": now_iso}

    def _persist_entry_audit_immediately(self, trade, signal, analysis, ticket=None):
        """Congela tesis y snapshot inicial apenas MT5 confirma la entrada."""
        writer = getattr(self.repository, "upsert_trade_visual_audit", None)
        if not callable(writer) or not isinstance(trade, dict) or not trade.get("id"):
            return False
        signal = signal if isinstance(signal, dict) else {}
        analysis = analysis if isinstance(analysis, dict) else {}
        htf = signal.get("higher_timeframe_context") or analysis.get("higher_timeframe_context") or {}
        entry_chart = self._entry_chart_snapshot_from_cache(
            str(trade.get("instrument") or ""),
            analysis=analysis,
        )
        entry = {
            "bot_profile": str(self.config.bot_profile).upper(),
            "daemon_magic": int(self.config.magic),
            "strategy_name": str(
                signal.get("strategy_name") or analysis.get("strategy_name") or "SMC"
            ).upper(),
            "strategy_version": str(
                signal.get("strategy_version")
                or analysis.get("strategy_version")
                or trade.get("strategy_version")
                or self.config.strategy_version
            ),
            "trade_id": int(trade["id"]),
            "instrument": trade.get("instrument"),
            "direction": trade.get("direction"),
            "entry_time": trade.get("entry_time"),
            "entry_price": trade.get("entry_price"),
            "stop_loss": trade.get("stop_loss"),
            "take_profit": trade.get("take_profit"),
            "planned_rr": trade.get("planned_rr"),
            "risk_percent": trade.get("risk_percent"),
            "decision": signal.get("confirmation_decision") or signal.get("decision") or analysis.get("action"),
            "score": signal.get("trade_score"),
            "grade": signal.get("trade_grade"),
            "confirmation_percentage": signal.get("confirmation_percentage"),
            "passed": signal.get("passed_confirmations") or [],
            "missing": signal.get("missing_confirmations") or [],
            "critical_failures": signal.get("critical_confirmation_failures") or [],
            "confirmation_details": signal.get("confirmations") or {},
            "harmonic_confirmed": bool(signal.get("harmonic_confirmed")),
            "harmonic_pattern": signal.get("harmonic_pattern"),
            "harmonic_score": signal.get("harmonic_score"),
            "chart_pattern_confirmed": bool(signal.get("chart_pattern_confirmed")),
            "chart_pattern_name": signal.get("chart_pattern_name"),
            "chart_pattern_direction": signal.get("chart_pattern_direction"),
            "chart_pattern_strength": signal.get("chart_pattern_strength"),
            "chart_pattern_conflict": bool(signal.get("chart_pattern_conflict")),
            "chart_pattern_conflict_level": signal.get("chart_pattern_conflict_level"),
            "chart_pattern_conflict_reason": signal.get("chart_pattern_conflict_reason"),
            "h1_trend": analysis.get("h1_trend") or htf.get("h1_trend"),
            "h4_trend": analysis.get("h4_trend"),
            "h4_h1_convergence": analysis.get("h4_h1_convergence"),
            "h4_timeframe": analysis.get("h4_timeframe") or "H4",
            "structure_break": analysis.get("m15_structure_break_type") or htf.get("m15_structure"),
            "zone": analysis.get("m15_zone"),
            "higher_timeframe_context": htf,
            "htf_alignment": None if not htf else not bool(htf.get("blocked")),
            "htf_blocked": bool(htf.get("blocked")) if htf else None,
            "htf_reason": htf.get("reason") if htf else None,
            "captured_immediately_after_fill": True,
            "market_data_source": "DERIV_CHARTS",
            "evidence_mode": "ENTRY_DECISION_CACHE",
        }
        writer(
            int(trade["id"]), instrument=str(trade.get("instrument") or ""),
            bot_profile=str(self.config.bot_profile).upper(), daemon_magic=int(self.config.magic),
            broker_position_ticket=ticket or trade.get("broker_position_ticket"),
            entry_chart=entry_chart or None,
            entry_context=entry, source=self.config.source,
        )

        # v86: la página /account/trade/<id>/audit y su Excel consumen la serie
        # append-only. Crear el primer punto aquí evita perder trades que abren y
        # cierran antes del siguiente refresco periódico de estrategia/gráficos.
        snapshot_writer = getattr(self.repository, "save_trade_audit_snapshot", None)
        snapshot_reader = getattr(self.repository, "trade_audit_snapshots", None)
        if callable(snapshot_writer):
            already_snapshotted = False
            if callable(snapshot_reader):
                try:
                    already_snapshotted = bool(snapshot_reader(
                        trade_id=int(trade["id"]), source=self.config.source, limit=1,
                    ))
                except Exception:
                    already_snapshotted = False
            if not already_snapshotted:
                try:
                    current_view = self._current_strategy_view_from_analysis(analysis)
                except Exception:
                    current_view = {
                        "decision": entry.get("decision"),
                        "direction": entry.get("direction"),
                        "score": entry.get("score"),
                        "confirmation_percentage": entry.get("confirmation_percentage"),
                    }
                snapshot_writer(
                    int(trade["id"]),
                    instrument=str(trade.get("instrument") or ""),
                    entry_view=entry,
                    current_view=current_view,
                    market={
                        "current_price": trade.get("entry_price"),
                        "entry_price": trade.get("entry_price"),
                        "current_stop_loss": trade.get("stop_loss"),
                        "initial_stop_loss": trade.get("stop_loss"),
                        "take_profit": trade.get("take_profit"),
                        "current_rr": 0.0,
                        "telemetry_mode": "ENTRY_FILL_CONFIRMED",
                    },
                    visual_context={
                        "capture_mode": "IMMEDIATE_POST_FILL",
                        "entry_chart_pending": True,
                    },
                    bot_profile=str(self.config.bot_profile).upper(),
                    daemon_magic=int(self.config.magic),
                    broker_position_ticket=ticket or trade.get("broker_position_ticket"),
                    source=self.config.source,
                    snapshot_at=trade.get("entry_time"),
                )
        return True

    def _entry_chart_snapshot_from_cache(
        self, symbol: str, candle_count: int = 120, analysis: dict | None = None
    ) -> dict:
        """Congela las velas exactas ya usadas por el pipeline al decidir.

        No consulta nuevamente al proveedor. Así la evidencia de entrada no
        puede incorporar una vela cerrada después del fill. Si una ruta no usa
        la caché SMC, la auditoría declara el gráfico de entrada como ausente.
        """
        if not symbol:
            return {}
        cache_reader = getattr(getattr(self, "multi_timeframe", None), "cached_stage", None)
        if not callable(cache_reader):
            cache_reader = lambda *args, **kwargs: {}

        tf_snapshots = {}
        counts = {"H4": 120, "H1": 120, "M15": 120, "M5": 140}
        for label in ("H4", "H1", "M15", "M5"):
            cached = cache_reader(symbol, label) or {}
            cached_result = cached.get("result") if isinstance(cached, dict) else None
            raw = cached_result.get("data") if isinstance(cached_result, dict) else None
            if raw is None and isinstance(cached, dict):
                raw = cached.get("data")
            if raw is None or not hasattr(raw, "empty") or raw.empty:
                continue
            try:
                data = raw.copy()
                data["time"] = pd.to_datetime(data["time"], utc=True)
                data = (
                    data.sort_values("time")
                    .drop_duplicates("time")
                    .tail(max(counts[label], int(candle_count)))
                    .reset_index(drop=True)
                )
                close = data["close"].astype(float)
                delta = close.diff()
                gain = delta.clip(lower=0.0)
                loss = -delta.clip(upper=0.0)
                avg_gain = gain.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
                avg_loss = loss.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
                rs = avg_gain / avg_loss.replace(0.0, float("nan"))
                rsi = (100.0 - (100.0 / (1.0 + rs))).clip(0.0, 100.0)
                candles = []
                for idx, row in data.iterrows():
                    rv = rsi.iloc[idx] if idx < len(rsi) else None
                    rv = float(rv) if pd.notna(rv) else None
                    raw_volume = row.get("tick_volume")
                    volume = float(raw_volume) if pd.notna(raw_volume) else None
                    candles.append({
                        "time": row["time"].isoformat(),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": volume,
                        "rsi14": rv,
                    })
                visual = build_smc_visual_context(data, candle_count=len(data))
                tf_snapshots[label] = {
                    "symbol": symbol,
                    "timeframe": label,
                    "broker_timeframe": label,
                    "candles": candles,
                    "events": visual.get("events", []),
                    "zones": visual.get("zones", []),
                    "levels": visual.get("levels", []),
                    "smc_context": visual.get("context", {}),
                    "smc_legend": visual.get("legend", {}),
                    "context_mode": "ESTRATEGIA",
                    "evidence_mode": "ENTRY_DECISION_CACHE",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            except Exception:
                continue

        seed = (analysis or {}).get("audit_chart_seed") if isinstance(analysis, dict) else None
        if isinstance(seed, dict):
            for label, payload in (seed.get("timeframes") or {}).items():
                if label not in tf_snapshots and isinstance(payload, dict):
                    tf_snapshots[str(label).upper()] = dict(payload)

        if not tf_snapshots:
            return {}
        default = tf_snapshots.get("M5") or next(iter(tf_snapshots.values()))
        return {
            **default,
            "symbol": symbol,
            "data_source": "DERIV_CHARTS",
            "evidence_mode": "ENTRY_DECISION_CACHE",
            "timeframes": tf_snapshots,
            "available_timeframes": [
                tf for tf in ("H4", "H1", "M15", "M5") if tf in tf_snapshots
            ],
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

    def _monitor_break_even_positions(self) -> dict:
        """
        Monitorea posiciones OPEN del daemon y mueve el SL real en MT5 a Break Even
        cuando el precio alcanza el RR configurado.

        Se basa en SQLite + posición real MT5, por lo que sigue funcionando después
        de reiniciar el proceso del daemon.
        """
        if not self.config.execution_enabled:
            return {"checked": 0, "activated": 0, "errors": [], "skipped": "DRY_RUN"}

        if not self.config.break_even_enabled:
            return {"checked": 0, "activated": 0, "errors": [], "skipped": "DISABLED"}

        trigger_rr = float(self.config.break_even_trigger_rr)
        if trigger_rr <= 0:
            return {"checked": 0, "activated": 0, "errors": ["INVALID_BREAK_EVEN_TRIGGER"], "skipped": False}

        trade_executor = getattr(self.lifecycle_manager, "trade_executor", None)
        move_stop = getattr(trade_executor, "move_stop_loss", None)
        close_position = getattr(trade_executor, "close_position", None)
        if not callable(move_stop):
            return {
                "checked": 0,
                "activated": 0,
                "errors": ["TRADE_EXECUTOR_DOES_NOT_SUPPORT_STOP_MODIFICATION"],
                "skipped": False,
            }

        checked = 0
        activated = 0
        errors = []
        updates = []
        runner_updates = []
        gold_transition_updates = []
        analysis_exit_updates = []
        position_snapshots = []
        seen_position_tickets = set()
        duplicate_position_rows = []

        for trade in self.repository.open_trades(source=self.config.source):
            if not self._trade_owned_by_current_bot(trade):
                continue
            ticket = trade.get("broker_position_ticket")
            if not ticket:
                continue
            ticket_key = str(ticket)
            if ticket_key in seen_position_tickets:
                duplicate_position_rows.append({
                    "trade_id": trade.get("id"),
                    "ticket": ticket_key,
                    "symbol": trade.get("instrument"),
                })
                continue
            seen_position_tickets.add(ticket_key)

            try:
                position = self.executor.get_position(int(ticket))
                if position is None:
                    continue

                checked += 1
                metadata = self._trade_metadata(trade)
                trade_trigger_rr = float(
                    metadata.get("break_even_trigger_rr", trigger_rr) or trigger_rr
                )
                if trade_trigger_rr <= 0:
                    trade_trigger_rr = trigger_rr

                # En una operación dividida, TP1 se cierra mecánicamente en 1R.
                # El Break Even protector corresponde al RUNNER, que busca 2R.
                # Aun así TP1 también se publica en el monitor de salud.
                trade_leg = str(metadata.get("trade_leg") or "").upper()

                entry_price = float(getattr(position, "price_open", 0.0) or 0.0)
                current_price = float(getattr(position, "price_current", 0.0) or 0.0)
                current_sl = float(getattr(position, "sl", 0.0) or 0.0)
                direction = str(trade.get("direction", "")).upper()
                initial_sl = self._break_even_initial_stop(trade, metadata)

                if entry_price <= 0 or current_price <= 0 or initial_sl is None:
                    errors.append({
                        "trade_id": trade.get("id"),
                        "ticket": str(ticket),
                        "error": "BREAK_EVEN_INSUFFICIENT_POSITION_DATA",
                    })
                    continue

                if direction == "BUY":
                    initial_risk_snapshot = entry_price - float(initial_sl)
                    current_rr_snapshot = (current_price - entry_price) / initial_risk_snapshot if initial_risk_snapshot > 0 else None
                    distance_to_sl_r = (current_price - float(initial_sl)) / initial_risk_snapshot if initial_risk_snapshot > 0 else None
                    tp_value = float(getattr(position, "tp", trade.get("take_profit") or 0.0) or 0.0)
                    distance_to_tp_r = (tp_value - current_price) / initial_risk_snapshot if initial_risk_snapshot > 0 and tp_value > 0 else None
                elif direction == "SELL":
                    initial_risk_snapshot = float(initial_sl) - entry_price
                    current_rr_snapshot = (entry_price - current_price) / initial_risk_snapshot if initial_risk_snapshot > 0 else None
                    distance_to_sl_r = (float(initial_sl) - current_price) / initial_risk_snapshot if initial_risk_snapshot > 0 else None
                    tp_value = float(getattr(position, "tp", trade.get("take_profit") or 0.0) or 0.0)
                    distance_to_tp_r = (current_price - tp_value) / initial_risk_snapshot if initial_risk_snapshot > 0 and tp_value > 0 else None
                else:
                    initial_risk_snapshot = None
                    current_rr_snapshot = None
                    distance_to_sl_r = None
                    distance_to_tp_r = None
                    tp_value = float(getattr(position, "tp", trade.get("take_profit") or 0.0) or 0.0)

                metadata, excursion_changed = self._update_excursion_metrics(
                    trade,
                    metadata,
                    current_rr_snapshot,
                    current_price,
                )

                position_snapshots.append({
                    "trade_id": trade.get("id"),
                    "ticket": str(ticket),
                    "symbol": trade.get("instrument"),
                    "direction": direction,
                    "trade_leg": trade_leg,
                    "entry_price": entry_price,
                    "current_price": current_price,
                    "current_stop_loss": current_sl,
                    "initial_stop_loss": initial_sl,
                    "take_profit": tp_value,
                    "current_rr": current_rr_snapshot,
                    "distance_to_sl_r": distance_to_sl_r,
                    "distance_to_tp_r": distance_to_tp_r,
                    "break_even_confirmed": bool(metadata.get("break_even_confirmed", False)),
                    "max_favorable_excursion_rr": metadata.get("max_favorable_excursion_rr", 0.0),
                    "max_adverse_excursion_rr": metadata.get("max_adverse_excursion_rr", 0.0),
                    "runner_extension_stage": metadata.get("runner_extension_stage"),
                    "runner_profit_lock_rr": metadata.get("runner_profit_lock_rr"),
                })

                forex_news_protection = self._protect_forex_position_for_high_impact_news(
                    trade=trade,
                    metadata=metadata,
                    position=position,
                    entry_price=entry_price,
                    current_sl=current_sl,
                    direction=direction,
                    move_stop=move_stop,
                )
                if forex_news_protection is not None:
                    if forex_news_protection["action"] == "FOREX_NEWS_BREAK_EVEN_CONFIRMED":
                        activated += 1
                    updates.append({
                        "trade_id": trade.get("id"),
                        "ticket": str(ticket),
                        "symbol": trade.get("instrument"),
                        **forex_news_protection,
                    })
                    continue

                analysis_exit = self._analysis_invalidation_exit(
                    trade=trade,
                    metadata=metadata,
                    current_rr=current_rr_snapshot,
                    close_position=close_position,
                )
                if analysis_exit.get("managed"):
                    analysis_exit_updates.append(analysis_exit)
                if analysis_exit.get("closed"):
                    # El sync de MT5 se realizará en la siguiente pasada; no se
                    # debe intentar BE/runner sobre una posición ya cerrada.
                    continue

                # v87: al abrir Nueva York no se conserva riesgo nuevo de la
                # sesión Asia/Londres. >=1R toma ganancias; 0R..1R intenta BE.
                gold_after_ny = (
                    str(self.config.bot_profile or "").upper() == "GOLD"
                    and not self._gold_smc_session_state()["active"]
                )
                if gold_after_ny and current_rr_snapshot is not None:
                    rr_now = float(current_rr_snapshot)
                    if (
                        rr_now > 0.0
                        and bool(self.config.gold_break_even_positive_at_new_york)
                        and not bool(metadata.get("gold_ny_transition_protected", False))
                    ):
                        # BE exacto (sin offset) para maximizar probabilidad de
                        # aceptación cuando la ganancia aún es menor que 1R.
                        transition_be = float(entry_price)
                        modification = move_stop(
                            position_ticket=str(ticket),
                            stop_loss=transition_be,
                            take_profit=float(tp_value),
                            reason="gold_new_york_open_break_even",
                        )
                        confirmed = False
                        confirmed_position = None
                        if modification.get("modified", False):
                            for attempt in range(max(1, int(self.config.break_even_confirmation_retries))):
                                confirmed_position = self.executor.get_position(int(ticket))
                                broker_sl = float(getattr(confirmed_position, "sl", 0.0) or 0.0) if confirmed_position is not None else 0.0
                                if abs(broker_sl - transition_be) <= self._break_even_price_tolerance(str(trade.get("instrument") or ""), entry_price):
                                    confirmed = True
                                    break
                                if attempt < int(self.config.break_even_confirmation_retries) - 1:
                                    time.sleep(max(0.0, float(self.config.break_even_confirmation_delay_seconds)))
                        if confirmed:
                            metadata["break_even_activated"] = True
                            metadata["break_even_confirmed"] = True
                            metadata["break_even_price"] = transition_be
                            metadata["break_even_activation_reason"] = "GOLD_NEW_YORK_OPEN_POSITIVE"
                            metadata["gold_ny_transition_protected"] = True
                            metadata["gold_ny_transition_at"] = datetime.now(timezone.utc).isoformat()
                            details = dict(trade.get("details") or {})
                            details["metadata"] = metadata
                            self.repository.update_trade(int(trade["id"]), {
                                "stop_loss": transition_be,
                                "details": details,
                            })
                            activated += 1
                            gold_transition_updates.append({
                                "trade_id": trade.get("id"),
                                "ticket": str(ticket),
                                "symbol": trade.get("instrument"),
                                "action": "GOLD_NY_BREAK_EVEN_CONFIRMED",
                                "current_rr": rr_now,
                                "break_even_price": transition_be,
                            })
                            continue
                        errors.append({
                            "trade_id": trade.get("id"),
                            "ticket": str(ticket),
                            "error": "GOLD_NY_BREAK_EVEN_NOT_CONFIRMED",
                            "diagnostic": modification,
                        })

                if bool(self.config.split_entries_enabled) and trade_leg == "TP1":
                    continue

                # FLIP: una reversión M1 confirmada después de +0.50R protege
                # entrada/costes antes de que actúe el BE estándar de +1R.
                flip_view = (
                    (getattr(self, "_current_strategy_view_cache", {}) or {}).get(
                        str(trade.get("instrument") or "")
                    ) or {}
                )
                flip_protection = (
                    str(self.config.bot_profile or "").upper() == "FLIP"
                    and bool(getattr(self.config, "flip_reversal_protection_enabled", True))
                    and current_rr_snapshot is not None
                    and float(current_rr_snapshot) >= float(
                        getattr(self.config, "flip_reversal_protection_trigger_rr", 0.50)
                    )
                    and bool(flip_view.get("m1_reversal_confirmed", False))
                    and not bool(metadata.get("flip_reversal_protected", False))
                )
                if flip_protection:
                    flip_be_price, flip_offset = self._break_even_target_stop(
                        str(trade.get("instrument") or ""), direction, entry_price
                    )
                    modification = move_stop(
                        position_ticket=str(ticket),
                        stop_loss=flip_be_price,
                        take_profit=float(tp_value),
                        reason="flip_m1_reversal_protection",
                    )
                    if modification.get("modified", False):
                        metadata["flip_reversal_protected"] = True
                        metadata["flip_reversal_protection_rr"] = round(
                            float(current_rr_snapshot), 4
                        )
                        metadata["flip_reversal_protection_at"] = datetime.now(
                            timezone.utc
                        ).isoformat()
                        metadata["break_even_price"] = flip_be_price
                        metadata["break_even_offset"] = flip_offset
                        metadata["break_even_activation_reason"] = (
                            "FLIP_M1_REVERSAL_CONFIRMED"
                        )
                        details = dict(trade.get("details") or {})
                        details["metadata"] = metadata
                        self.repository.update_trade(
                            int(trade["id"]),
                            {
                                "stop_loss": flip_be_price,
                                "details": details,
                            },
                        )
                        continue

                # Idempotencia: si el broker ya tiene SL en BE+offset, solo persistimos
                # el estado local y no enviamos otra modificación. La tolerancia usa
                # el point/tick real para evitar falsos negativos por redondeo de MT5.
                tolerance = self._break_even_price_tolerance(
                    str(trade.get("instrument") or ""), entry_price
                )
                profit_lock_fraction = max(
                    0.0, float(self.config.break_even_profit_lock_rr_fraction or 0.0)
                )
                profit_lock_amount = (
                    float(initial_risk_snapshot) * profit_lock_fraction
                    if initial_risk_snapshot and initial_risk_snapshot > 0
                    else 0.0
                )
                already_active = bool(metadata.get("break_even_activated", False))
                break_even_price, break_even_offset = self._break_even_target_stop(
                    str(trade.get("instrument") or ""),
                    direction,
                    entry_price,
                    profit_lock_amount=profit_lock_amount,
                )
                broker_at_entry = abs(current_sl - break_even_price) <= tolerance
                if already_active or broker_at_entry:
                    if not already_active:
                        metadata["break_even_activated"] = True
                        metadata["break_even_price"] = break_even_price
                        metadata["break_even_offset"] = break_even_offset
                        metadata["break_even_offset_points"] = int(self.config.break_even_offset_points)
                        metadata["break_even_trigger_rr"] = trade_trigger_rr
                        self.repository.update_trade(
                            int(trade["id"]),
                            {
                                "stop_loss": break_even_price,
                                "details": {
                                    **(trade.get("details") or {}),
                                    "metadata": metadata,
                                },
                            },
                        )

                    extension = self._manage_runner_extension(
                        trade=trade,
                        position=position,
                        metadata=metadata,
                        initial_stop_loss=float(initial_sl),
                        current_rr=current_rr_snapshot,
                        move_stop=move_stop,
                    )
                    if extension.get("managed"):
                        runner_updates.append({
                            "trade_id": trade.get("id"),
                            "ticket": str(ticket),
                            "symbol": trade.get("instrument"),
                            **extension,
                        })
                    continue

                tp1_completion = self._break_even_tp1_completion(trade, metadata)

                if direction == "BUY":
                    initial_risk = entry_price - initial_sl
                    trigger_price = entry_price + initial_risk * trade_trigger_rr
                    price_reached_trigger = initial_risk > 0 and current_price >= trigger_price
                elif direction == "SELL":
                    initial_risk = initial_sl - entry_price
                    trigger_price = entry_price - initial_risk * trade_trigger_rr
                    price_reached_trigger = initial_risk > 0 and current_price <= trigger_price
                else:
                    errors.append({
                        "trade_id": trade.get("id"),
                        "ticket": str(ticket),
                        "error": f"INVALID_DIRECTION:{direction}",
                    })
                    continue

                # Dos caminos válidos de activación:
                # 1) el precio observado sigue en >=1R; o
                # 2) TP1 ya cerró en beneficio, lo cual demuestra que 1R fue alcanzado
                #    aunque el precio haya retrocedido antes de esta lectura.
                eligible = bool(price_reached_trigger or tp1_completion.get("completed", False))
                if not eligible:
                    continue
                activation_reason = (
                    "TP1_CLOSED_IN_PROFIT"
                    if tp1_completion.get("completed", False)
                    else "PRICE_REACHED_TRIGGER_RR"
                )

                modification = move_stop(
                    position_ticket=str(ticket),
                    stop_loss=break_even_price,
                    take_profit=float(getattr(position, "tp", trade.get("take_profit") or 0.0) or 0.0),
                    reason="break_even_1R_plus_offset",
                )
                if not modification.get("modified", False):
                    errors.append({
                        "trade_id": trade.get("id"),
                        "ticket": str(ticket),
                        "error": modification.get("error") or "BREAK_EVEN_MODIFICATION_REJECTED",
                        "diagnostic": modification,
                    })
                    continue

                # La respuesta de order_send no es suficiente: confirmamos leyendo
                # nuevamente la posición real desde MT5. Así evitamos marcar BE en
                # SQLite si el broker no aplicó realmente el nuevo SL.
                confirmed_position = None
                confirmed = False
                retries = max(1, int(self.config.break_even_confirmation_retries))
                for attempt in range(retries):
                    confirmed_position = self.executor.get_position(int(ticket))
                    if confirmed_position is not None:
                        broker_sl = float(getattr(confirmed_position, "sl", 0.0) or 0.0)
                        if abs(broker_sl - break_even_price) <= tolerance:
                            confirmed = True
                            break
                    if attempt < retries - 1:
                        time.sleep(max(0.0, float(self.config.break_even_confirmation_delay_seconds)))

                if not confirmed:
                    errors.append({
                        "trade_id": trade.get("id"),
                        "ticket": str(ticket),
                        "error": "BREAK_EVEN_NOT_CONFIRMED_BY_BROKER",
                        "diagnostic": modification,
                        "expected_stop_loss": break_even_price,
                        "broker_stop_loss": (
                            float(getattr(confirmed_position, "sl", 0.0) or 0.0)
                            if confirmed_position is not None else None
                        ),
                    })
                    continue

                metadata["break_even_activated"] = True
                metadata["break_even_confirmed"] = True
                metadata["break_even_price"] = break_even_price
                metadata["break_even_offset"] = break_even_offset
                metadata["break_even_offset_points"] = int(self.config.break_even_offset_points)
                metadata["break_even_trigger_rr"] = trade_trigger_rr
                metadata["break_even_trigger_price"] = trigger_price
                metadata["break_even_activated_at_price"] = current_price
                metadata["break_even_activation_reason"] = activation_reason
                metadata["break_even_tp1_completion"] = tp1_completion
                metadata["break_even_modified_at"] = datetime.now(timezone.utc).isoformat()
                metadata["break_even_broker_result"] = modification

                details = dict(trade.get("details") or {})
                details["metadata"] = metadata
                self.repository.update_trade(
                    int(trade["id"]),
                    {
                        "stop_loss": break_even_price,
                        "details": details,
                    },
                )
                activated += 1
                updates.append({
                    "trade_id": trade.get("id"),
                    "ticket": str(ticket),
                    "symbol": trade.get("instrument"),
                    "direction": direction,
                    "entry_price": entry_price,
                    "trigger_price": trigger_price,
                    "current_price": current_price,
                    "break_even_price": break_even_price,
                    "activation_reason": activation_reason,
                    "tp1_completion": tp1_completion,
                })

                if current_rr_snapshot is not None and float(current_rr_snapshot) >= float(self.config.runner_extension_first_trigger_rr):
                    refreshed_position = self.executor.get_position(int(ticket)) or position
                    extension = self._manage_runner_extension(
                        trade=trade,
                        position=refreshed_position,
                        metadata=metadata,
                        initial_stop_loss=float(initial_sl),
                        current_rr=current_rr_snapshot,
                        move_stop=move_stop,
                    )
                    if extension.get("managed"):
                        runner_updates.append({
                            "trade_id": trade.get("id"),
                            "ticket": str(ticket),
                            "symbol": trade.get("instrument"),
                            **extension,
                        })

            except Exception as exc:
                errors.append({
                    "trade_id": trade.get("id"),
                    "ticket": str(ticket),
                    "error": str(exc),
                })

        # v79: la telemetría de salud se persiste en CADA pasada del monitor,
        # independientemente de la estrategia que abrió el trade.
        live_persistence = self._persist_live_position_market_snapshots(position_snapshots)
        if live_persistence.get("errors"):
            errors.extend({
                "error": "LIVE_POSITION_TELEMETRY_PERSIST_FAILED",
                **row,
            } for row in live_persistence.get("errors") or [])

        reporting_config = getattr(self.reporting_service, "config", None)
        auto_export = (
            True
            if reporting_config is None
            else bool(getattr(reporting_config, "auto_export", True))
        )
        if (
            (activated > 0 or errors)
            and self.reporting_service is not None
            and auto_export
        ):
            try:
                self.reporting_service.export_now()
            except Exception as exc:
                errors.append({"error": f"BREAK_EVEN_EXPORT_FAILED:{exc}"})

        return {
            "checked": checked,
            "activated": activated,
            "updates": updates,
            "positions": position_snapshots,
            "runner_updates": runner_updates,
            "gold_transition_updates": gold_transition_updates,
            "analysis_exit_updates": analysis_exit_updates,
            "duplicate_position_rows_skipped": duplicate_position_rows,
            "live_persistence": live_persistence,
            "errors": errors,
            "skipped": False,
        }

    def _orb_gold_counterpart_open(self, symbol: str) -> dict | None:
        """Evita duplicar la misma tesis de Oro entre XAUUSD y microXAUUSD."""
        if not is_orb_gold_symbol(symbol):
            return None
        for trade in self.repository.open_trades(source=self.config.source):
            instrument = str(trade.get("instrument") or "")
            if instrument != str(symbol) and is_orb_gold_symbol(instrument):
                return {
                    "trade_id": trade.get("id"),
                    "instrument": instrument,
                    "broker_position_ticket": trade.get("broker_position_ticket"),
                }
        return None

    def _gold_smc_exposure_open(self) -> dict | None:
        """Detecta Oro SMC aún abierto para impedir una segunda tesis ORB."""
        try:
            trades = self.repository.open_trades(source=self.config.source) or []
        except Exception:
            trades = []
        for trade in trades:
            if not is_orb_gold_symbol(str(trade.get("instrument") or "")):
                continue
            metadata = self._trade_metadata(trade)
            if str(metadata.get("bot_profile") or "").upper() != "GOLD":
                continue
            return {
                "trade_id": trade.get("id"),
                "instrument": trade.get("instrument"),
                "broker_position_ticket": trade.get("broker_position_ticket"),
                "break_even_confirmed": self._trade_has_confirmed_break_even(trade),
            }
        return None

    def _evaluate_orb_gold_contract(self, symbol: str, account: dict) -> dict:
        """Evalúa si un contrato de Oro puede ejecutar correctamente una señal ORB."""
        result = {"symbol": str(symbol), "eligible": True, "viable": False}
        try:
            analysis = self.orb_strategy.analyze_symbol(symbol)
            result["analysis_action"] = analysis.get("action")
            result["analysis_reason"] = analysis.get("reason")
            if not analysis.get("valid"):
                result["reason"] = analysis.get("reason") or "ORB_SIGNAL_NOT_VALID"
                return result

            signal = analysis.get("signal") or analysis.get("entry") or {}
            direction = str(signal.get("direction") or "").upper()
            if direction not in {"BUY", "SELL"}:
                result["reason"] = "INVALID_DIRECTION"
                return result

            tick = self.provider.get_current_tick(symbol)
            entry = float(tick["ask"] if direction == "BUY" else tick["bid"])
            rr = float(signal.get("risk_reward_ratio", self.config.orb_target_rr) or self.config.orb_target_rr)
            stop_validation = self.executor.normalize_market_stops(
                symbol,
                direction,
                entry,
                float(signal["stop_loss"]),
                rr,
                safety_points=self.config.stop_safety_points,
            )
            if not stop_validation.get("valid"):
                result["reason"] = stop_validation.get("reason") or "INVALID_MARKET_STOP"
                return result

            entry = float(stop_validation["entry_price"])
            sl = float(stop_validation["stop_loss"])
            risk_base_name = str(self.config.risk_base).upper()
            risk_base_value = float(
                account["equity"] if risk_base_name == "EQUITY" else account["balance"]
            )
            total_risk_amount = risk_base_value * float(self.config.orb_risk_percent) / 100.0
            leg_fraction = (
                float(self.config.split_entry_risk_fraction)
                if bool(self.config.split_entries_enabled)
                else 1.0
            )
            target_leg_risk = total_risk_amount * leg_fraction
            sizing = self.executor.calculate_volume(
                symbol, direction, entry, sl, target_leg_risk
            )
            actual_leg_risk = float(sizing["actual_risk_amount"])

            min_required = target_leg_risk * max(0.0, float(self.config.min_actual_risk_ratio))
            max_allowed = target_leg_risk * (
                1.0 + max(0.0, float(self.config.max_actual_risk_tolerance))
            )
            if actual_leg_risk > max_allowed + 1e-9:
                result.update({
                    "reason": "RISK_ABOVE_ALLOWED",
                    "actual_leg_risk": actual_leg_risk,
                    "target_leg_risk": target_leg_risk,
                })
                return result
            if "raw_volume" in sizing and actual_leg_risk + 1e-9 < min_required:
                result.update({
                    "reason": "RISK_TARGET_UNREACHABLE",
                    "actual_leg_risk": actual_leg_risk,
                    "target_leg_risk": target_leg_risk,
                })
                return result

            bid = float(tick["bid"])
            ask = float(tick["ask"])
            spread_entry = ask if direction == "BUY" else bid
            spread_exit = bid if direction == "BUY" else ask
            spread_cost = float(
                self.executor.calculate_risk_amount(
                    symbol=symbol,
                    direction=direction,
                    volume=float(sizing["volume"]),
                    entry_price=spread_entry,
                    stop_loss=spread_exit,
                )["actual_risk_amount"]
            )

            margin_required = 0.0
            calc_margin = getattr(self.executor, "calculate_margin_amount", None)
            if callable(calc_margin):
                margin_required = float(
                    calc_margin(
                        symbol=symbol,
                        direction=direction,
                        volume=float(sizing["volume"]),
                        entry_price=entry,
                    ).get("margin_required", 0.0)
                )

            quality = score_orb_gold_contract_candidate(
                target_leg_risk=target_leg_risk,
                actual_leg_risk=actual_leg_risk,
                spread_cost=spread_cost,
                margin_required=margin_required,
                free_margin=float(account.get("free_margin", 0.0) or 0.0),
            )
            result.update({
                "viable": True,
                "direction": direction,
                "entry_price": entry,
                "stop_loss": sl,
                "volume_per_leg": float(sizing["volume"]),
                "target_leg_risk": target_leg_risk,
                "actual_leg_risk": actual_leg_risk,
                "actual_leg_risk_percent": (
                    actual_leg_risk / risk_base_value * 100.0 if risk_base_value > 0 else None
                ),
                "spread_points_price": abs(ask - bid),
                "spread_cost_per_leg": spread_cost,
                "margin_required_per_leg": margin_required,
                "quality": quality,
            })
            return result
        except Exception as exc:
            result["reason"] = f"ORB_GOLD_SELECTION_ERROR:{exc}"
            return result

    def _orb_session_is_active(self, symbol: str | None = None, now_utc=None) -> bool:
        """True sólo mientras la sesión ORB NY está activa (09:30 <= NY < 16:00).

        Se usa para evitar cálculos costosos del selector XAUUSD/XAUUSDmicro
        fuera de la sesión. SMC/sintéticos NO dependen de este filtro.
        """
        if now_utc is None:
            if not symbol:
                return False
            try:
                tick = self.provider.get_current_tick(symbol)
                now_utc = pd.Timestamp(tick["time"]).to_pydatetime()
            except Exception:
                return False

        now_ny, open_ny, _range_end_ny, close_ny = self.orb_strategy._session_bounds(now_utc)
        return bool(now_ny.weekday() < 5 and open_ny <= now_ny < close_ny)

    def _prepare_orb_gold_selection(self, symbols) -> dict:
        """Selecciona un solo contrato de Oro para la oportunidad ORB del ciclo."""
        candidates = []
        for symbol in symbols:
            if is_orb_gold_symbol(symbol) and str(symbol) not in candidates:
                candidates.append(str(symbol))

        self._orb_gold_cycle_selection = None
        self._orb_gold_cycle_diagnostics = {
            "candidate_symbols": candidates,
            "selected_symbol": None,
            "reason": "NO_GOLD_CANDIDATES",
            "evaluations": [],
        }
        if not candidates:
            return self._orb_gold_cycle_diagnostics

        # ORB es independiente: fuera de Nueva York no evaluamos sizing,
        # spread ni margen de los dos contratos de Oro.
        if not self._orb_session_is_active(candidates[0]):
            self._orb_gold_cycle_diagnostics["reason"] = "OUTSIDE_ORB_NEW_YORK_SESSION"
            return self._orb_gold_cycle_diagnostics

        if len(candidates) == 1:
            self._orb_gold_cycle_selection = candidates[0]
            self._orb_gold_cycle_diagnostics.update({
                "selected_symbol": candidates[0],
                "reason": "ONLY_ONE_GOLD_CONTRACT_IN_CYCLE",
            })
            return self._orb_gold_cycle_diagnostics

        # Si ambas variantes están disponibles, la elección se recalcula en cada ciclo.
        try:
            account = self._account_and_guard()
        except Exception as exc:
            self._orb_gold_cycle_diagnostics["reason"] = f"ACCOUNT_UNAVAILABLE:{exc}"
            return self._orb_gold_cycle_diagnostics

        evaluations = [
            self._evaluate_orb_gold_contract(symbol, account)
            for symbol in candidates
        ]
        viable = [
            item for item in evaluations
            if item.get("viable") and isinstance((item.get("quality") or {}).get("score"), (int, float))
        ]
        if viable:
            viable.sort(
                key=lambda item: (
                    float(item["quality"]["score"]),
                    float(item["quality"].get("spread_risk_ratio", 0.0)),
                    float(item["quality"].get("margin_free_ratio", 0.0)),
                    str(item["symbol"]).lower(),
                )
            )
            selected = str(viable[0]["symbol"])
            self._orb_gold_cycle_selection = selected
            reason = "BEST_RISK_SPREAD_MARGIN_EXECUTION"
        else:
            selected = None
            reason = "NO_VIABLE_GOLD_ORB_SIGNAL"

        self._orb_gold_cycle_diagnostics = {
            "candidate_symbols": candidates,
            "selected_symbol": selected,
            "reason": reason,
            "evaluations": evaluations,
        }
        return self._orb_gold_cycle_diagnostics

    @staticmethod
    def _is_forex_symbol(symbol: str) -> bool:
        """Reconoce pares FX estándar aun cuando el broker agregue un sufijo."""
        letters = "".join(ch for ch in str(symbol or "").upper() if ch.isalpha())
        currencies = {
            "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
            "SEK", "NOK", "DKK", "SGD", "HKD", "MXN", "ZAR", "TRY", "PLN",
            "CNH",
        }
        if len(letters) < 6:
            return False
        base, quote = letters[:3], letters[3:6]
        return base in currencies and quote in currencies and base != quote

    def _forex_rollover_status(self, now_utc=None) -> dict:
        """Ventana Forex: Tokio 09:00 hasta cutoff NY 16:30, DST-safe."""
        ny_tz = ZoneInfo(str(self.config.forex_rollover_timezone))
        tokyo_tz = ZoneInfo(str(self.config.forex_tokyo_timezone))
        current = now_utc or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)

        now_ny = current.astimezone(ny_tz)
        now_tokyo = current.astimezone(tokyo_tz)
        ny_minute = now_ny.hour * 60 + now_ny.minute

        cutoff = int(self.config.forex_new_entry_cutoff_hour) * 60 + int(self.config.forex_new_entry_cutoff_minute)
        force_flat = int(self.config.forex_force_flat_hour) * 60 + int(self.config.forex_force_flat_minute)

        latest_tokyo_open = None
        for days_back in range(0, 8):
            day = (now_tokyo - timedelta(days=days_back)).date()
            if day.weekday() >= 5:
                continue
            candidate = datetime(
                day.year, day.month, day.day,
                int(self.config.forex_tokyo_session_start_hour),
                int(self.config.forex_tokyo_session_start_minute),
                tzinfo=tokyo_tz,
            )
            if candidate <= now_tokyo:
                latest_tokyo_open = candidate
                break

        session_cutoff_ny = None
        if latest_tokyo_open is not None:
            start_ny_date = latest_tokyo_open.astimezone(ny_tz).date()
            for days_forward in range(0, 8):
                day = start_ny_date + timedelta(days=days_forward)
                if day.weekday() >= 5:
                    continue
                candidate = datetime(
                    day.year, day.month, day.day,
                    int(self.config.forex_new_entry_cutoff_hour),
                    int(self.config.forex_new_entry_cutoff_minute),
                    tzinfo=ny_tz,
                )
                if candidate > latest_tokyo_open:
                    session_cutoff_ny = candidate
                    break

        session_active = bool(
            latest_tokyo_open is not None
            and session_cutoff_ny is not None
            and latest_tokyo_open.astimezone(timezone.utc)
            <= current.astimezone(timezone.utc)
            < session_cutoff_ny.astimezone(timezone.utc)
        )
        block_new_entries = not session_active
        # Nunca aplicar force-flat a posiciones recién abiertas en Tokio aunque
        # Nueva York todavía marque la tarde del día calendario anterior.
        force_flat_now = bool(
            not session_active
            and now_ny.weekday() < 5
            and ny_minute >= force_flat
        )
        weekend = bool(now_tokyo.weekday() >= 5 and now_ny.weekday() >= 5)

        return {
            "now_ny": now_ny.isoformat(),
            "now_tokyo": now_tokyo.isoformat(),
            "weekday_ny": now_ny.strftime("%A"),
            "weekday_tokyo": now_tokyo.strftime("%A"),
            "block_new_entries": bool(block_new_entries),
            "force_flat_now": bool(force_flat_now and self.config.forex_force_flat_daily),
            "weekend": bool(weekend),
            "new_entry_cutoff": f"{int(self.config.forex_new_entry_cutoff_hour):02d}:{int(self.config.forex_new_entry_cutoff_minute):02d}",
            "force_flat_time": f"{int(self.config.forex_force_flat_hour):02d}:{int(self.config.forex_force_flat_minute):02d}",
            "tokyo_session_start": f"{int(self.config.forex_tokyo_session_start_hour):02d}:{int(self.config.forex_tokyo_session_start_minute):02d}",
            "tokyo_session_open": latest_tokyo_open.isoformat() if latest_tokyo_open else None,
            "session_cutoff_ny": session_cutoff_ny.isoformat() if session_cutoff_ny else None,
            "new_york_timezone": str(self.config.forex_rollover_timezone),
            "tokyo_timezone": str(self.config.forex_tokyo_timezone),
        }

    def _forex_rollover_entry_gate(self, symbol: str) -> dict | None:
        """PUERTA DE ENTRADA: impide abrir Forex en la ventana del rollover diario.

        En el cambio de dia del broker la liquidez se hunde, el spread se
        ensancha y se aplican los intereses de financiacion. Abrir ahi supone
        pagar un coste evitable con una ejecucion de mala calidad.

        IMPORTANTE: solo bloquea ENTRADAS NUEVAS. Las posiciones ya abiertas no
        se cierran por rollover, coherentemente con la regla de que los cierres
        deben responder a invalidacion estructural. Ver
        `_close_forex_positions_for_rollover`, que lo deja explicito.

        Args:
            symbol: instrumento evaluado.

        Returns:
            `None` si se puede entrar, o un dict de bloqueo con el estado del
            rollover.
        """
        if not bool(self.config.forex_rollover_guard_enabled) or not self._is_forex_symbol(symbol):
            return None
        status = self._forex_rollover_status()
        if not status["block_new_entries"]:
            return None
        return {
            "symbol": str(symbol),
            "action": "FOREX_ROLLOVER_ENTRY_BLOCKED",
            "reason": "FOREX_NO_NUEVAS_ENTRADAS_CERCA_DEL_ROLLOVER",
            "rollover": status,
        }

    def _close_forex_positions_for_rollover(self) -> dict:
        """Cierra posiciones Forex administradas por el daemon antes del rollover."""
        result = {"checked": 0, "closed": 0, "errors": [], "positions": []}
        if not bool(self.config.execution_enabled) or not bool(self.config.forex_rollover_guard_enabled):
            return result

        status = self._forex_rollover_status()
        if not status.get("force_flat_now"):
            return result

        close_position = getattr(self.executor, "close_position", None)
        if not callable(close_position):
            result["errors"].append("TRADE_EXECUTOR_DOES_NOT_SUPPORT_POSITION_CLOSE")
            return result

        seen_tickets = set()
        for trade in self.repository.open_trades(source=self.config.source) or []:
            if not self._trade_owned_by_current_bot(trade):
                continue
            if not self._is_forex_symbol(str(trade.get("instrument") or "")):
                continue
            ticket = str(trade.get("broker_position_ticket") or "")
            if not ticket or ticket in seen_tickets:
                continue
            seen_tickets.add(ticket)
            result["checked"] += 1
            close_result = close_position(
                position_ticket=ticket,
                reason="forex_pre_new_york_close",
            )
            closed = bool(
                (close_result or {}).get("closed", False)
                or str((close_result or {}).get("status") or "").upper() == "CLOSED"
            )
            result["positions"].append({
                "trade_id": trade.get("id"),
                "ticket": ticket,
                "symbol": trade.get("instrument"),
                "closed": closed,
                "close_result": close_result,
            })
            if closed:
                result["closed"] += 1
        return result

    @staticmethod
    def _is_jump_symbol(symbol: str) -> bool:
        """Indica si el símbolo es un índice sintético de la familia Jump.

        Estos instrumentos saltan a intervalos regulares y reciben tratamiento
        propio en varias decisiones de gestion.
        """
        return "jump" in str(symbol or "").lower()

    def _meta_label_gate(
        self,
        *,
        symbol: str,
        signal: dict,
        analysis: dict,
        strategy_name: str,
    ) -> dict:
        """Puntúa la señal con el meta-etiquetado del worker.

        En SHADOW registra la probabilidad sin bloquear. En FILTER exige que
        probabilidad y expectativa neta superen los umbrales configurados.
        """
        engine = getattr(self, "meta_labeling", None)
        if engine is None:
            return {"allowed": True, "reason": "META_LABELING_NOT_AVAILABLE"}

        try:
            decision = engine.score_signal(
                symbol=str(symbol),
                signal=signal,
                analysis=analysis,
                market={
                    "planned_rr": signal.get("risk_reward_ratio"),
                    "risk_percent": float(self.config.risk_percent),
                    "entry_price": signal.get("entry_price"),
                },
                strategy_name=strategy_name,
            ).to_dict()
        except Exception as exc:
            # Un fallo del modelo nunca debe impedir operar una señal válida.
            return {"allowed": True, "reason": f"META_LABEL_ERROR:{exc}"}

        self._meta_label_cycle_decisions.append(decision)
        self._persist_audit_event(
            "META_LABEL_SIGNAL_SCORED",
            instrument=str(symbol),
            action="SHADOW_SCORED" if decision.get("shadow") else (
                "FILTER_ALLOWED" if decision.get("allowed") else "FILTER_REJECTED"
            ),
            reason=decision.get("reason"),
            payload={"meta_label": decision},
        )
        return decision

    def meta_label_cycle_ranking(self, *, reset: bool = True) -> list[dict]:
        """Ordena las señales puntuadas del ciclo por expectativa y probabilidad."""
        decisions = list(getattr(self, "_meta_label_cycle_decisions", []) or [])
        if reset:
            self._meta_label_cycle_decisions = []
        if not decisions or not bool(self.config.meta_labeling_ranking_enabled):
            return []
        ranked = rank_signals(
            decisions,
            max_signals=int(self.config.meta_labeling_max_signals_per_cycle),
        )
        self._persist_audit_event(
            "META_LABEL_CYCLE_RANKING",
            action="SIGNALS_RANKED",
            reason="RANKED_BY_NET_EXPECTANCY_AND_PROBABILITY",
            payload={"ranking": ranked},
        )
        return ranked

    def train_meta_labeling(self, *, strategy_name: str = "ALL") -> dict:
        """Entrena el modelo del worker con su historial persistido."""
        engine = getattr(self, "meta_labeling", None)
        if engine is None:
            return {"trained": False, "reason": "META_LABELING_NOT_AVAILABLE"}

        reader = getattr(self.repository, "trade_history_dataframe", None)
        if not callable(reader):
            reader = getattr(self.repository, "trades_dataframe", None)
        if not callable(reader):
            return {"trained": False, "reason": "REPOSITORY_HAS_NO_TRADE_HISTORY"}

        trades = reader(source=self.config.source)
        report = engine.train(trades, strategy_name=strategy_name)
        self._persist_audit_event(
            "META_LABEL_MODEL_TRAINED",
            action="MODEL_TRAINED" if report.get("trained") else "MODEL_NOT_TRAINED",
            reason="TEMPORAL_VALIDATION_COMPLETED",
            payload=report,
        )
        return report

    def _jump_quality_gate(self, symbol: str, signal: dict) -> dict | None:
        """Filtro extra para Jump basado en la muestra DEMO observada.

        Jump no se elimina: simplemente exige que las confirmaciones que más
        reducen falsos positivos estén presentes antes de permitir ejecución.
        """
        if not bool(self.config.jump_strict_filter_enabled) or not self._is_jump_symbol(symbol):
            return None

        confirmations = signal.get("confirmations") or {}
        percentage = float(signal.get("confirmation_percentage") or 0.0)
        score = float(signal.get("trade_score") or 0.0)

        failures = []
        checks = {
            "rejection": bool(confirmations.get("rejection", False)),
            "micro_structure": bool(confirmations.get("micro_structure", False)),
            "displacement": bool(confirmations.get("displacement", False)),
            "strong_close": bool(confirmations.get("strong_close", False)),
        }

        if bool(self.config.jump_require_rejection) and not checks["rejection"]:
            failures.append("JUMP_REJECTION_REQUIRED")
        if bool(self.config.jump_require_micro_structure) and not checks["micro_structure"]:
            failures.append("JUMP_MICRO_STRUCTURE_REQUIRED")
        if bool(self.config.jump_require_displacement) and not checks["displacement"]:
            failures.append("JUMP_DISPLACEMENT_REQUIRED")
        if bool(self.config.jump_require_strong_close) and not checks["strong_close"]:
            failures.append("JUMP_STRONG_CLOSE_REQUIRED")
        if percentage + 1e-9 < float(self.config.jump_min_confirmation_ratio) * 100.0:
            failures.append("JUMP_CONFIRMATION_PERCENTAGE_TOO_LOW")
        if score + 1e-9 < float(self.config.jump_min_trade_score):
            failures.append("JUMP_TRADE_SCORE_TOO_LOW")

        if not failures:
            signal["jump_strict_gate"] = {
                "passed": True,
                "checks": checks,
                "confirmation_percentage": percentage,
                "trade_score": score,
            }
            return None

        return {
            "symbol": str(symbol),
            "action": "JUMP_STRICT_FILTER_REJECTED",
            "reason": "JUMP_REQUIERE_CONFIRMACIONES_ESTRUCTURALES_REFORZADAS",
            "failures": failures,
            "checks": checks,
            "confirmation_percentage": percentage,
            "minimum_confirmation_percentage": float(self.config.jump_min_confirmation_ratio) * 100.0,
            "trade_score": score,
            "minimum_trade_score": float(self.config.jump_min_trade_score),
        }

    def _orb_higher_timeframe_context(self, symbol: str, direction: str) -> dict:
        """Obtiene contexto H1/M15 sin convertir ORB en una estrategia SMC."""
        result = {
            "enabled": bool(getattr(self.config, "orb_htf_context_enabled", True)),
            "direction": str(direction or "").upper(),
            "h1_trend": None,
            "h1_alignment": None,
            "m15_structure": None,
            "m15_alignment": None,
            "blocked": False,
            "reason": None,
            "raw_action": None,
        }
        if not result["enabled"] or result["direction"] not in {"BUY", "SELL"}:
            return result
        try:
            mtf = self.multi_timeframe.analyze_symbol(symbol)
        except Exception as exc:
            result["reason"] = f"ORB_HTF_CONTEXT_ERROR:{exc}"
            return result

        result["raw_action"] = mtf.get("action")
        h1 = mtf.get("h1") if isinstance(mtf.get("h1"), dict) else {}
        h1_ctx = h1.get("context") if isinstance(h1.get("context"), dict) else {}
        h1_trend = mtf.get("h1_trend") or h1_ctx.get("trend")
        result["h1_trend"] = h1_trend

        trend = str(h1_trend or "").upper()
        if trend in {"BULLISH", "ALCISTA", "UP", "UPTREND"}:
            h1_dir = "BUY"
        elif trend in {"BEARISH", "BAJISTA", "DOWN", "DOWNTREND"}:
            h1_dir = "SELL"
        else:
            h1_dir = None
        result["h1_alignment"] = None if h1_dir is None else (h1_dir == result["direction"])

        m15 = mtf.get("m15") if isinstance(mtf.get("m15"), dict) else {}
        setup = m15.get("setup") if isinstance(m15.get("setup"), dict) else {}
        structure = mtf.get("m15_structure_break_type") or setup.get("structure_break_type")
        result["m15_structure"] = structure
        s = str(structure or "").upper()
        if "BULL" in s or "ALCIST" in s:
            m15_dir = "BUY"
        elif "BEAR" in s or "BAJIST" in s:
            m15_dir = "SELL"
        else:
            m15_dir = None
        result["m15_alignment"] = None if m15_dir is None else (m15_dir == result["direction"])

        if bool(getattr(self.config, "orb_require_known_htf_context", True)):
            if result["h1_alignment"] is None or (
                bool(getattr(self.config, "orb_use_m15_context", True))
                and result["m15_alignment"] is None
            ):
                result["blocked"] = True
                result["reason"] = "ORB_HTF_CONTEXT_UNAVAILABLE"
                return result

        if bool(getattr(self.config, "orb_require_h1_alignment", True)) and result["h1_alignment"] is False:
            result["blocked"] = True
            result["reason"] = "ORB_BREAKOUT_CONTRA_TENDENCIA_H1"
            if bool(getattr(self.config, "orb_use_m15_context", True)) and result["m15_alignment"] is False:
                result["reason"] = "ORB_BREAKOUT_CONTRA_H1_Y_M15"
        return result

    @staticmethod
    def _trade_has_confirmed_break_even(
        trade: dict,
        minimum_offset_points: int = 0,
    ) -> bool:
        """Confirma BE y, opcionalmente, un margen protector mínimo."""
        details = trade.get("details") if isinstance(trade.get("details"), dict) else {}
        meta = details.get("metadata") if isinstance(details.get("metadata"), dict) else {}
        minimum_offset_points = max(0, int(minimum_offset_points))
        recorded_offset = meta.get("break_even_offset_points")
        if bool(meta.get("break_even_confirmed", False)):
            try:
                return float(recorded_offset or 0) >= minimum_offset_points
            except (TypeError, ValueError):
                return minimum_offset_points == 0
        if minimum_offset_points > 0:
            return False
        try:
            entry = float(trade.get("entry_price") or 0.0)
            stop = float(trade.get("stop_loss") or 0.0)
        except (TypeError, ValueError):
            return False
        direction = str(trade.get("direction") or "").upper()
        if entry <= 0 or stop <= 0:
            return False
        tolerance = max(abs(entry) * 1e-9, 1e-9)
        return (
            direction == "BUY" and stop >= entry - tolerance
        ) or (
            direction == "SELL" and stop <= entry + tolerance
        )

    def _orb_exposure_guard(self, symbol: str, execution_key: str, strategy_name: str):
        """Evita S&P 500 + Nasdaq simultáneos hasta confirmar Break Even."""
        if str(strategy_name or "").upper() != "ORB_NEW_YORK":
            return None
        if not bool(getattr(self.config, "orb_equity_correlation_guard_enabled", True)):
            return None
        candidate_market = classify_orb_market(symbol)
        correlated_markets = {"US_500", "US_TECH_100"}
        if candidate_market not in correlated_markets:
            return None
        counterpart_market = (correlated_markets - {candidate_market}).pop()
        try:
            trades = self.repository.open_trades(source=self.config.source) or []
        except Exception:
            trades = []
        counterpart_setups = {}
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            if classify_orb_market(trade.get("instrument")) != counterpart_market:
                continue
            details = trade.get("details") if isinstance(trade.get("details"), dict) else {}
            meta = details.get("metadata") if isinstance(details.get("metadata"), dict) else {}
            if str(meta.get("strategy_name") or "").upper() != "ORB_NEW_YORK":
                continue
            key = str(meta.get("parent_execution_key") or trade.get("execution_key") or trade.get("id"))
            item = counterpart_setups.setdefault(key, {"trades": [], "all_at_break_even": True})
            protected = self._trade_has_confirmed_break_even(
                trade,
                minimum_offset_points=int(
                    getattr(self.config, "orb_correlated_entry_min_break_even_offset_points", 2)
                ),
            )
            item["all_at_break_even"] = bool(item["all_at_break_even"] and protected)
            item["trades"].append({
                "trade_id": trade.get("id"),
                "ticket": trade.get("broker_position_ticket"),
                "instrument": trade.get("instrument"),
                "leg": meta.get("trade_leg"),
                "break_even_confirmed": protected,
                "stop_loss": trade.get("stop_loss"),
                "entry_price": trade.get("entry_price"),
            })
        if not counterpart_setups:
            return None
        all_protected = all(item["all_at_break_even"] for item in counterpart_setups.values())
        if all_protected or not bool(getattr(self.config, "orb_correlated_entry_requires_break_even", True)):
            return None
        return {
            "symbol": symbol,
            "action": "ORB_CORRELATED_MARKET_BLOCKED",
            "reason": "ORB_SP500_NASDAQ_REQUIRES_CONFIRMED_BREAK_EVEN",
            "execution_key": execution_key,
            "orb_correlation": {
                "candidate_market": candidate_market,
                "open_counterpart_market": counterpart_market,
                "entry_allowed_after_break_even": True,
                "counterpart_setups": counterpart_setups,
            },
        }

    def _exhaustion_reversal_shadow(self, symbol: str) -> dict | None:
        """Busca una reversión adicional sin alterar la decisión principal.

        Reutiliza H1/M5 de la caché cuando el flujo normal ya los calculó. Si
        M5 no fue necesario para la señal de continuación, descarga sólo las
        velas cerradas requeridas por este detector y evita ejecutar todo el
        pipeline SMC una segunda vez.
        """
        if not bool(getattr(self.config, "exhaustion_reversal_enabled", True)):
            return None
        if str(getattr(self.config, "exhaustion_reversal_mode", "SHADOW")).upper() != "SHADOW":
            return None

        profile = str(self.config.bot_profile or "").upper()
        family = self._canonical_bot_profile(profile)
        supported = (
            profile == "GOLD"
            or profile.startswith("FOREX")
            or family in {"SYNTHETICS", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"}
        )
        if not supported:
            return None

        h1_cached = self.multi_timeframe.cached_stage(
            symbol, self.config.structure_timeframe
        )
        m5_cached = self.multi_timeframe.cached_stage(
            symbol, self.config.entry_timeframe
        )
        h1_data = h1_cached.get("data")
        m5_data = m5_cached.get("data")
        if h1_data is None or getattr(h1_data, "empty", True):
            h1_data = self.multi_timeframe._get_closed_candles(
                symbol,
                self.config.structure_timeframe,
                max(60, int(self.config.exhaustion_dealing_range_lookback) + 1),
            )
        if m5_data is None or getattr(m5_data, "empty", True):
            m5_data = self.multi_timeframe._get_closed_candles(
                symbol,
                self.config.entry_timeframe,
                max(40, int(self.config.exhaustion_liquidity_lookback) + 3),
            )

        policy = get_symbol_direction_policy(symbol)
        result = detect_exhaustion_reversal(
            h1_data,
            m5_data,
            symbol=symbol,
            allowed_direction=policy.allowed_direction,
            config=ExhaustionReversalConfig(
                dealing_range_lookback=int(self.config.exhaustion_dealing_range_lookback),
                liquidity_lookback=int(self.config.exhaustion_liquidity_lookback),
                premium_threshold=float(self.config.exhaustion_premium_threshold),
                discount_threshold=float(self.config.exhaustion_discount_threshold),
                minimum_rejection_wick_ratio=float(self.config.exhaustion_minimum_wick_ratio),
                maximum_exhaustion_body_ratio=float(self.config.exhaustion_maximum_body_ratio),
                displacement_range_multiplier=float(self.config.displacement_range_multiplier),
                volume_climax_multiplier=float(self.config.exhaustion_volume_climax_multiplier),
            ),
        )
        result["bot_profile"] = profile
        result["direction_policy"] = direction_policy_diagnostics(
            symbol, result.get("direction")
        )
        return result

    def _orb_session_trade_exists(self, symbol: str, session_date: str) -> dict | None:
        """Busca en el historial una ejecución ORB de la misma sesión NY.

        Es la defensa persistente de `one_signal_per_session`: sobrevive a
        reinicios y sólo considera operaciones realmente guardadas, nunca una
        candidata que fue rechazada antes del fill.
        """
        reader = getattr(self.repository, "trade_history_dataframe", None)
        if not callable(reader) or not session_date:
            return None
        try:
            history = reader(source=self.config.source)
        except Exception:
            return None
        if history is None or getattr(history, "empty", True):
            return None
        for row in reversed(history.to_dict("records")):
            if str(row.get("instrument") or "") != str(symbol):
                continue
            details = row.get("details")
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except Exception:
                    details = {}
            details = details if isinstance(details, dict) else {}
            metadata = details.get("metadata") if isinstance(details.get("metadata"), dict) else {}
            strategy = str(
                metadata.get("strategy_name")
                or row.get("strategy_name")
                or ""
            ).upper()
            if strategy != "ORB_NEW_YORK":
                continue
            recorded_session = str(metadata.get("orb_session_date") or "")
            if not recorded_session:
                try:
                    recorded_session = str(
                        pd.to_datetime(row.get("entry_time"), utc=True)
                        .tz_convert("America/New_York")
                        .date()
                    )
                except Exception:
                    continue
            if recorded_session == str(session_date):
                return {
                    "trade_id": row.get("id"),
                    "entry_time": row.get("entry_time"),
                    "breakout_candle_time": metadata.get("breakout_candle_time"),
                }
        return None

    def _mark_orb_session_after_fill(self, symbol: str, signal: dict) -> None:
        if str(signal.get("strategy_name") or "").upper() != "ORB_NEW_YORK":
            return
        self.orb_strategy.mark_signal_used(
            symbol,
            str(signal.get("orb_session_date") or ""),
            str(signal.get("breakout_candle_time") or ""),
        )

    def _attach_exhaustion_reversal_shadow(self, symbol: str, analysis: dict) -> dict:
        """Adjunta y audita el candidato SHADOW; nunca cambia `valid`/`signal`."""
        try:
            shadow = self._exhaustion_reversal_shadow(symbol)
        except Exception as exc:
            shadow = {
                "strategy_name": "SMC_EXHAUSTION_REVERSAL",
                "mode": "SHADOW",
                "valid": False,
                "action": "EXHAUSTION_REVERSAL_DATA_ERROR",
                "reason": str(exc),
            }
        if not isinstance(shadow, dict):
            return analysis

        analysis = dict(analysis or {})
        analysis["exhaustion_reversal_shadow"] = shadow
        if shadow.get("valid"):
            self._persist_audit_event(
                "EXHAUSTION_REVERSAL_SHADOW",
                instrument=symbol,
                action=shadow.get("action"),
                reason=shadow.get("reason"),
                payload={"exhaustion_reversal": shadow},
            )
        return analysis

    def _risk_percent_for_strategy(self, strategy_name: str) -> float:
        """Devuelve el riesgo lógico sin mezclar contratos de estrategia.

        ORB conserva siempre su campo dedicado. El resto de estrategias usa
        el riesgo general del worker. Centralizar esta selección permite una
        prueba de comportamiento y evita depender sólo de inspección textual.
        """
        if str(strategy_name or "").upper() == "ORB_NEW_YORK":
            return float(self.config.orb_risk_percent)
        return float(self.config.risk_percent)

    def process_symbol(self, symbol: str, sync_before_execution: bool = True):
        """Procesa un símbolo de extremo a extremo: análisis, filtros y ejecución.

        METODO CENTRAL del motor. Recorre en orden todas las etapas y se
        detiene en la PRIMERA que rechace, devolviendo siempre un dict con
        `action` y `reason` que explica el desenlace:

        1. Resolucion del simbolo exacto en el broker.
        2. Puertas de entrada, en este orden: sesion del oro, rollover Forex,
           noticias de alto impacto y cuarentena del simbolo.
        3. Analisis multi-temporal H1/M15/M5 (o ORB segun el perfil).
        4. Persistencia de la senal para auditoria y entrenamiento del modelo.
        5. Puerta de meta-etiquetado de IA: en modo sombra solo registra la
           probabilidad, en modo filtro exige superar los umbrales de
           probabilidad y expectativa neta.
        6. Comprobacion de que el mercado actual no invalida la senal y de que
           el precio no se ha desplazado demasiado respecto al de la senal.
        7. Limites de posiciones y exposicion.
        8. Dimensionado por riesgo y envio de la orden.
        9. Validacion POST-fill del riesgo real: si excede el tope duro, la
           posicion se cierra de inmediato y el simbolo pasa a cuarentena.

        Args:
            symbol: instrumento a procesar, admite alias sin resolver.
            sync_before_execution: si se reconcilian primero las operaciones
                cerradas con el broker, para partir de un estado fiable.

        Returns:
            Dict con el resultado. No lanza ante un rechazo normal: que una
            senal no llegue a ejecutarse es un desenlace esperado.

        Vinculaciones:
        - Lo invoca `run_once` para cada simbolo del ciclo.
        - Se apoya en `MultiTimeframeAnalyzer`, `strategy.ai.meta_labeling`,
          el `TradeExecutor` configurado y `trade_lifecycle_manager`.
        """
        exact_symbol = self.provider.resolve_symbol(symbol)
        self.provider.ensure_symbol(exact_symbol)

        gold_session_gate = self._gold_smc_entry_gate(exact_symbol)
        if gold_session_gate is not None:
            return gold_session_gate

        forex_rollover_gate = self._forex_rollover_entry_gate(exact_symbol)
        if forex_rollover_gate is not None:
            return forex_rollover_gate
        forex_news_gate = self._forex_high_impact_news_entry_gate(exact_symbol)
        if forex_news_gate is not None:
            return forex_news_gate

        quarantined = self._quarantine_result(exact_symbol)
        if quarantined is not None:
            return {
                "symbol": exact_symbol,
                "action": "SYMBOL_QUARANTINED",
                "reason": (
                    "RISK_INCIDENT_TEMPORARY_COOLDOWN"
                    if quarantined.get("recoverable")
                    else "RISK_INCIDENT_REQUIRES_MANUAL_REVIEW"
                ),
                "quarantine": quarantined,
            }

        # En ejecución real sincronizamos SQLite con MT5 antes del ciclo.
        # La llamada directa a process_symbol conserva la sincronización por compatibilidad.
        sync_info = (
            self._sync_open_trades_before_execution()
            if sync_before_execution else {"synced": 0, "skipped": True, "reason": "CYCLE_SYNC"}
        )

        # Router de estrategias. ORB New York tiene prioridad EXCLUSIVAMENTE en
        # XAUUSD / microXAUUSD / Wall Street 30 / US Tech 100 / US500. Para cualquier otro
        # instrumento se conserva intacto el pipeline SMC H1 -> M15 -> M5.
        if (
            bool(self.config.orb_enabled)
            and is_orb_gold_symbol(exact_symbol)
            and self._orb_gold_cycle_selection
            and str(exact_symbol) != str(self._orb_gold_cycle_selection)
        ):
            return {
                "symbol": exact_symbol,
                "action": "ORB_GOLD_ALTERNATIVE_SELECTED",
                "reason": "OTRO_CONTRATO_DE_ORO_OFRECE_MEJOR_EJECUCION",
                "selected_symbol": self._orb_gold_cycle_selection,
                "gold_contract_selection": self._orb_gold_cycle_diagnostics,
            }

        if (
            str(self.config.bot_profile or "").upper() == "IDX_OPEN"
            and bool(self.config.idx_open_enabled)
            and is_ny_index_open_symbol(exact_symbol)
        ):
            analysis = self.ny_index_open_strategy.analyze_symbol(exact_symbol)
        elif bool(self.config.orb_enabled) and is_orb_eligible_symbol(exact_symbol):
            analysis = self.orb_strategy.analyze_symbol(exact_symbol)
            orb_signal = analysis.get("signal") or analysis.get("entry") or {}
            orb_direction = str(orb_signal.get("direction") or analysis.get("direction") or "").upper()
            if analysis.get("valid") and orb_direction in {"BUY", "SELL"}:
                htf_context = self._orb_higher_timeframe_context(exact_symbol, orb_direction)
                analysis["higher_timeframe_context"] = htf_context
                analysis["h1_trend"] = htf_context.get("h1_trend")
                analysis["m15_structure_break_type"] = htf_context.get("m15_structure")
                if isinstance(orb_signal, dict):
                    confirmations = dict(orb_signal.get("confirmations") or {})
                    h1_align = htf_context.get("h1_alignment")
                    m15_align = htf_context.get("m15_alignment")
                    confirmations["h1_context_alignment"] = True if h1_align is None else bool(h1_align)
                    if bool(getattr(self.config, "orb_use_m15_context", True)):
                        confirmations["m15_context_alignment"] = True if m15_align is None else bool(m15_align)
                    orb_signal["confirmations"] = confirmations
                    passed = [k for k, v in confirmations.items() if bool(v)]
                    missing = [k for k, v in confirmations.items() if not bool(v)]
                    orb_signal["passed_confirmations"] = passed
                    orb_signal["missing_confirmations"] = missing
                    orb_signal["confirmation_percentage"] = round(len(passed) / max(1, len(confirmations)) * 100.0, 2)
                    orb_signal["trade_score"] = orb_signal["confirmation_percentage"]
                    orb_signal["higher_timeframe_context"] = htf_context
                    analysis["signal"] = orb_signal
                    analysis["entry"] = orb_signal
                if htf_context.get("blocked"):
                    analysis["valid"] = False
                    analysis["action"] = "ORB_HTF_CONTEXT_BLOCKED"
                    analysis["reason"] = htf_context.get("reason")
                    analysis["rejection_reasons"] = [htf_context.get("reason")]
        else:
            analysis = self.multi_timeframe.analyze_symbol(exact_symbol)
            analysis = self._attach_exhaustion_reversal_shadow(
                exact_symbol, analysis
            )
        if not analysis.get("valid"):
            result = {
                "symbol": exact_symbol,
                "action": analysis.get("action", "NO_SIGNAL"),
                "reason": analysis.get("reason"),
                "analysis": analysis,
            }
            if self.config.diagnostic_mode:
                result["diagnostics"] = analysis.get("diagnostics", {})
                result["sync"] = sync_info
            return result

        signal = analysis.get("signal") or analysis.get("entry")
        if not signal:
            return {"symbol": exact_symbol, "action": "NO_SIGNAL", "analysis": analysis}

        if is_orb_gold_symbol(exact_symbol):
            candidate_strategy_name = str(
                signal.get("strategy_name") or analysis.get("strategy_name") or "SMC"
            ).upper()
            if candidate_strategy_name == "ORB_NEW_YORK":
                gold_smc = self._gold_smc_exposure_open()
                if gold_smc is not None:
                    return {
                        "symbol": exact_symbol,
                        "action": "ORB_GOLD_BLOCKED_BY_SMC_EXPOSURE",
                        "reason": "XAUUSD_SMC_ASIA_LONDON_AUN_ESTA_ABIERTO",
                        "gold_smc_position": gold_smc,
                        "analysis": analysis if self.config.diagnostic_mode else None,
                    }
            counterpart = self._orb_gold_counterpart_open(exact_symbol)
            if counterpart is not None:
                return {
                    "symbol": exact_symbol,
                    "action": "ORB_GOLD_EXPOSURE_ALREADY_OPEN",
                    "reason": "YA_EXISTE_EXPOSICION_ORB_EN_EL_OTRO_CONTRATO_DE_ORO",
                    "counterpart_position": counterpart,
                    "gold_contract_selection": self._orb_gold_cycle_diagnostics,
                    "analysis": analysis if self.config.diagnostic_mode else None,
                }

        direction = str(signal.get("direction") or signal.get("setup_type", "")).upper()
        direction = "BUY" if direction == "LONG" else "SELL" if direction == "SHORT" else direction
        if direction not in {"BUY", "SELL"}:
            return {"symbol": exact_symbol, "action": "INVALID_DIRECTION", "analysis": analysis}

        policy = direction_policy_diagnostics(exact_symbol, direction)
        if not is_direction_allowed(exact_symbol, direction):
            return {
                "symbol": exact_symbol,
                "action": "DIRECTION_POLICY_BLOCKED",
                "reason": f"{policy['policy_reason']}_REJECTED_{direction}",
                "direction": direction,
                "direction_policy": policy,
                "analysis": analysis,
            }

        signal["direction"] = direction
        signal["valid"] = True

        jump_gate = self._jump_quality_gate(exact_symbol, signal)
        if jump_gate is not None:
            if self.config.diagnostic_mode:
                jump_gate["analysis"] = analysis
            return jump_gate

        rr = float(signal.get("risk_reward_ratio", signal.get("risk_reward", 0.0)) or 0.0)
        if rr < self.config.min_rr:
            return {
                "symbol": exact_symbol,
                "action": "RR_TOO_LOW",
                "risk_reward_ratio": rr,
                "analysis": analysis,
            }

        signal_id, _ = self._save_signal(exact_symbol, signal)
        strategy_name = str(signal.get("strategy_name") or analysis.get("strategy_name") or "SMC").upper()
        strategy_version = str(signal.get("strategy_version") or analysis.get("strategy_version") or self.config.strategy_version)
        key = self._execution_key(exact_symbol, signal["entry_time"], direction, strategy_name=strategy_name)

        meta_label = self._meta_label_gate(
            symbol=exact_symbol,
            signal=signal,
            analysis=analysis,
            strategy_name=strategy_name,
        )
        signal["meta_label"] = meta_label
        if not meta_label.get("allowed", True):
            return {
                "symbol": exact_symbol,
                "action": "META_LABEL_FILTER_REJECTED",
                "reason": meta_label.get("reason"),
                "execution_key": key,
                "direction": direction,
                "meta_label": meta_label,
                "analysis": analysis if self.config.diagnostic_mode else None,
            }

        if strategy_name == "ORB_NEW_YORK" and bool(
            getattr(self.orb_strategy.config, "one_signal_per_session", True)
        ):
            prior_orb_trade = self._orb_session_trade_exists(
                exact_symbol, str(signal.get("orb_session_date") or "")
            )
            if prior_orb_trade is not None:
                return {
                    "symbol": exact_symbol,
                    "action": "ORB_SESSION_SIGNAL_LIMIT_REACHED",
                    "reason": "YA_EXISTE_TRADE_ORB_PERSISTIDO_ESTA_SESION",
                    "execution_key": key,
                    "orb_session_trade": prior_orb_trade,
                    "analysis": analysis if self.config.diagnostic_mode else None,
                }

        # v109: la señal de NY_INDEX_OPEN se marca "usada para esta sesión"
        # recién aquí, tras superar dirección, jump gate, R:R y meta-label.
        # Antes se marcaba dentro de `analyze_symbol` en cuanto se armaba la
        # señal candidata, bloqueando el resto de la sesión aunque luego
        # fuera descartada sin abrir ninguna operación.
        if strategy_name == "NY_INDEX_OPEN" and signal.get("ny_index_session_date"):
            self.ny_index_open_strategy.mark_signal_used(
                exact_symbol, signal["ny_index_session_date"]
            )

        orb_exposure = self._orb_exposure_guard(exact_symbol, key, strategy_name)
        if orb_exposure is not None:
            if self.config.diagnostic_mode:
                orb_exposure["analysis"] = analysis
            return orb_exposure

        execution_keys = (
            [f"{key}:TP1", f"{key}:RUNNER"]
            if bool(self.config.split_entries_enabled)
            else [key]
        )
        if any(self.repository.get_trade_by_execution_key(item) is not None for item in execution_keys):
            return {
                "symbol": exact_symbol,
                "action": "ALREADY_EXECUTED",
                "execution_key": key,
                "execution_keys": execution_keys,
            }

        limit_result = self._position_limit_result(exact_symbol, key)
        if limit_result is not None:
            if self.config.diagnostic_mode:
                limit_result["sync"] = sync_info
                limit_result["analysis"] = analysis
            return limit_result

        account = self._account_and_guard()
        tick = self.provider.get_current_tick(exact_symbol)
        entry = float(tick["ask"] if direction == "BUY" else tick["bid"])
        original_sl = float(signal["stop_loss"])

        # 1) Antes de normalizar stops, comprobar si el mercado ya invalidó
        # la estructura original o si la entrada se alejó demasiado del precio de señal.
        market_signal_diagnostics = self._market_signal_diagnostics(
            exact_symbol, direction, signal, tick, entry, original_sl
        )
        if market_signal_diagnostics.get("market_invalidated_signal"):
            return {
                "symbol": exact_symbol,
                "action": "MARKET_INVALIDATED_SIGNAL",
                "reason": market_signal_diagnostics.get("reason"),
                "execution_key": key,
                "direction": direction,
                "signal_entry_price": market_signal_diagnostics.get("signal_entry_price"),
                "market_entry_price": entry,
                "structural_stop_loss": original_sl,
                "market_signal_diagnostics": market_signal_diagnostics,
                "direction_policy": policy,
                "analysis": analysis if self.config.diagnostic_mode else None,
            }
        if market_signal_diagnostics.get("entry_drift_exceeded"):
            return {
                "symbol": exact_symbol,
                "action": "ENTRY_PRICE_DRIFT_TOO_LARGE",
                "reason": market_signal_diagnostics.get("reason"),
                "execution_key": key,
                "direction": direction,
                "signal_entry_price": market_signal_diagnostics.get("signal_entry_price"),
                "market_entry_price": entry,
                "structural_stop_loss": original_sl,
                "market_signal_diagnostics": market_signal_diagnostics,
                "direction_policy": policy,
                "analysis": analysis if self.config.diagnostic_mode else None,
            }

        # 2) Adaptar SL/TP a las reglas reales del símbolo y al precio actual.
        stop_validation = self.executor.normalize_market_stops(
            exact_symbol, direction, entry, original_sl, rr,
            safety_points=self.config.stop_safety_points,
        )
        if not stop_validation.get("valid"):
            return {
                "symbol": exact_symbol,
                "action": "REJECTED_INVALID_MARKET_STOP",
                "reason": stop_validation.get("reason"),
                "execution_key": key,
                "direction": direction,
                "signal_entry_price": float(signal.get("entry_price")) if signal.get("entry_price") is not None else None,
                "market_entry_price": entry,
                "original_stop_loss": original_sl,
                "signal_entry_time": signal.get("entry_time"),
                "stop_validation": stop_validation,
                "market_stop_diagnostics": {
                    **stop_validation,
                    **market_signal_diagnostics,
                    "direction_policy": policy,
                },
                "market_signal_diagnostics": market_signal_diagnostics,
                "direction_policy": policy,
                "analysis": analysis if self.config.diagnostic_mode else None,
            }

        entry = float(stop_validation["entry_price"])
        sl = float(stop_validation["stop_loss"])
        tp = float(stop_validation["take_profit"])

        # 3) Riesgo explícito y auditable. Primero intentamos dividir el riesgo
        # total en TP1 + RUNNER. Si las restricciones del broker impiden hacerlo
        # sin superar el 1%, se intenta una única entrada segura (fallback).
        risk_base_name = str(self.config.risk_base).upper()
        if risk_base_name not in {"EQUITY", "BALANCE"}:
            return {"symbol": exact_symbol, "action": "INVALID_RISK_BASE", "reason": risk_base_name}
        risk_base_value = float(account["equity"] if risk_base_name == "EQUITY" else account["balance"])
        total_risk_percent = self._risk_percent_for_strategy(strategy_name)
        # Contrato operativo v61: esta comprobación explícita evita que una
        # refactorización vuelva a heredar silenciosamente el riesgo SMC.
        if strategy_name == "ORB_NEW_YORK":
            total_risk_percent = float(self.config.orb_risk_percent)
        if risk_base_value <= 0 or not (0 < total_risk_percent <= 100):
            return {"symbol": exact_symbol, "action": "INVALID_RISK_CONFIGURATION", "risk_base": risk_base_value, "risk_percent": total_risk_percent}

        total_risk_amount = risk_base_value * total_risk_percent / 100.0
        risk_fraction = float(self.config.split_entry_risk_fraction)
        if bool(self.config.split_entries_enabled) and (not (0 < risk_fraction < 1) or abs((risk_fraction * 2.0) - 1.0) > 1e-9):
            return {
                "symbol": exact_symbol,
                "action": "INVALID_SPLIT_RISK_CONFIGURATION",
                "reason": "LAS_DOS_ENTRADAS_DEBEN_SUMAR_EL_100_POR_CIENTO_DEL_RIESGO",
                "split_entry_risk_fraction": risk_fraction,
            }

        risk_distance = abs(entry - sl)
        if risk_distance <= 0:
            return {"symbol": exact_symbol, "action": "INVALID_RISK_DISTANCE", "execution_key": key}

        min_ratio = max(0.0, float(self.config.min_actual_risk_ratio))

        def build_plan(specs, execution_mode):
            """Construye el plan de tramos (legs) repartiendo riesgo y objetivos.

            Una operacion puede dividirse en varios tramos con objetivos R
            crecientes, de modo que se asegura beneficio por partes mientras
            el resto sigue corriendo. Para cada tramo calcula su porcion de
            riesgo, el volumen ejecutable y el precio del objetivo.

            El riesgo se dimensiona con una reserva previa al fill que absorbe
            el desplazamiento entre el precio calculado y el de ejecucion real.

            Args:
                specs: tuplas `(nombre, fraccion, objetivo_rr)` u
                    `(nombre, fraccion, objetivo_rr, objetivo_rr_broker)`
                    cuando el objetivo enviado al broker difiere del interno.
                execution_mode: modo de ejecucion aplicado a los tramos.

            Returns:
                Tupla `(plan, error)`. Ante cualquier problema devuelve el plan
                a `None` y un dict de error con su codigo, en lugar de lanzar.
            """
            planned_legs = []
            for spec in specs:
                if len(spec) == 4:
                    leg_name, fraction, target_rr, broker_target_rr = spec
                else:
                    leg_name, fraction, target_rr = spec
                    broker_target_rr = target_rr
                if target_rr <= 0 or broker_target_rr <= 0:
                    return None, {
                        "code": "OBJETIVO_RR_INVALIDO",
                        "leg": leg_name,
                        "target_rr": target_rr,
                        "broker_target_rr": broker_target_rr,
                    }
                leg_risk_amount = total_risk_amount * fraction
                leg_risk_percent = total_risk_percent * fraction
                pre_fill_buffer = min(
                    0.25,
                    max(0.0, float(self.config.pre_fill_risk_buffer)),
                )
                sizing_risk_amount = leg_risk_amount * (1.0 - pre_fill_buffer)
                leg_tp = (
                    entry + risk_distance * broker_target_rr
                    if direction == "BUY"
                    else entry - risk_distance * broker_target_rr
                )
                constraints = stop_validation.get("constraints") or {}
                digits = constraints.get("digits")
                if digits is not None:
                    leg_tp = round(float(leg_tp), max(0, int(digits)))

                try:
                    sizing = self.executor.calculate_volume(
                        exact_symbol,
                        direction,
                        entry,
                        sl,
                        sizing_risk_amount,
                    )
                except Exception as exc:
                    message = str(exc)
                    normalized = message.casefold()
                    minimum_volume = any(
                        token in normalized
                        for token in (
                            "minimum volume", "volumen mínimo", "volumen minimo",
                            "minimum lot", "lote mínimo", "lote minimo",
                        )
                    )
                    return None, {
                        "code": (
                            "VOLUMEN_MINIMO_SUPERA_RIESGO_DE_LA_PIERNA"
                            if minimum_volume
                            else "CALCULO_DE_VOLUMEN_NO_DISPONIBLE"
                        ),
                        "leg": leg_name,
                        "risk_amount": leg_risk_amount,
                        "sizing_risk_amount": sizing_risk_amount,
                        "pre_fill_risk_buffer": pre_fill_buffer,
                        "error": message,
                    }
                actual_risk_amount = float(sizing["actual_risk_amount"])
                actual_risk_ratio = actual_risk_amount / leg_risk_amount if leg_risk_amount > 0 else 0.0
                actual_risk_percent = actual_risk_amount / risk_base_value * 100.0 if risk_base_value > 0 else 0.0
                max_allowed_risk = leg_risk_amount * (1.0 + max(0.0, float(self.config.max_actual_risk_tolerance)))
                min_required_risk = leg_risk_amount * min_ratio

                if actual_risk_amount > max_allowed_risk + 1e-9:
                    return None, {
                        "code": "RIESGO_REAL_SUPERA_LIMITE_DE_LA_ENTRADA",
                        "leg": leg_name, "risk_amount": leg_risk_amount,
                        "actual_risk_amount": actual_risk_amount,
                        "actual_risk_percent": actual_risk_percent,
                        "max_allowed_risk": max_allowed_risk,
                        "sizing": sizing,
                    }

                sizing_is_broker_aware = "raw_volume" in sizing and "volume_max" in sizing
                if sizing_is_broker_aware and actual_risk_amount + 1e-9 < min_required_risk:
                    return None, {
                        "code": "LOTE_DEL_BROKER_NO_PERMITE_ALCANZAR_RIESGO_OBJETIVO",
                        "leg": leg_name, "risk_amount": leg_risk_amount,
                        "actual_risk_amount": actual_risk_amount,
                        "actual_risk_percent": actual_risk_percent,
                        "min_required_risk": min_required_risk,
                        "sizing": sizing,
                    }

                leg_key = f"{key}:{leg_name}" if execution_mode == "SPLIT" else f"{key}:SINGLE"
                comment_prefix = "ORB" if strategy_name == "ORB_NEW_YORK" else "SMC"
                comment = f"{comment_prefix}-{signal_id}-{leg_name}"[:31]
                order_check = None
                if self.config.execution_enabled or self.config.validate_order_in_dry_run:
                    order_check = self.executor.check_market_order(
                        exact_symbol, direction, sizing["volume"], sl, leg_tp, self.config.magic,
                        comment, self.config.deviation,
                    )
                    if not order_check.get("valid"):
                        return None, {
                            "code": "ORDEN_RECHAZADA_EN_VALIDACION_MT5",
                            "leg": leg_name, "order_check": order_check,
                        }

                planned_legs.append({
                    "name": leg_name,
                    "execution_key": leg_key,
                    "risk_fraction": fraction,
                    "risk_percent": leg_risk_percent,
                    "risk_amount": leg_risk_amount,
                    "sizing_risk_amount": sizing_risk_amount,
                    "pre_fill_risk_buffer": pre_fill_buffer,
                    "target_rr": target_rr,
                    "logical_target_rr": target_rr,
                    "broker_target_rr": broker_target_rr,
                    "take_profit": float(leg_tp),
                    "sizing": sizing,
                    "actual_risk_amount": actual_risk_amount,
                    "actual_risk_ratio": actual_risk_ratio,
                    "actual_risk_percent": actual_risk_percent,
                    "min_required_risk": min_required_risk,
                    "comment": comment,
                    "order_check": order_check,
                })

            total_actual = sum(float(leg["actual_risk_amount"]) for leg in planned_legs)
            max_total = total_risk_amount * (1.0 + max(0.0, float(self.config.max_actual_risk_tolerance)))
            if total_actual > max_total + 1e-9:
                return None, {
                    "code": "RIESGO_TOTAL_REAL_SUPERA_EL_MAXIMO_PERMITIDO",
                    "actual_risk_amount": total_actual,
                    "max_allowed_risk": max_total,
                    "legs": planned_legs,
                }
            return planned_legs, None

        split_failure = None
        execution_mode = "SINGLE"
        if bool(self.config.split_entries_enabled):
            is_forex_profile = self._uses_forex_style_smc_management(self.config.bot_profile)
            if is_forex_profile:
                # Forex toma siempre ganancias con el runner en TP2.
                split_specs = [
                    ("TP1", risk_fraction, float(self.config.first_target_rr), float(self.config.first_target_rr)),
                    (
                        "RUNNER",
                        risk_fraction,
                        float(self.config.second_target_rr),
                        float(self.config.second_target_rr),
                    ),
                ]
            else:
                if bool(self.config.runner_extension_enabled):
                    strategy_runner_max_rr = (
                        float(self.config.runner_extension_max_target_rr)
                        if strategy_name == "ORB_NEW_YORK"
                        else float(self.config.smc_runner_max_target_rr)
                    )
                    runner_target_rr = max(float(self.config.second_target_rr), strategy_runner_max_rr)
                else:
                    runner_target_rr = float(self.config.second_target_rr)
                split_specs = [
                    ("TP1", risk_fraction, float(self.config.first_target_rr)),
                    ("RUNNER", risk_fraction, runner_target_rr),
                ]
            legs, split_failure = build_plan(split_specs, "SPLIT")
            execution_mode = "SPLIT"
        else:
            legs, split_failure = build_plan([("FULL", 1.0, rr)], "SINGLE")

        # Fallback: si dividir el riesgo no es viable por restricciones de lote/riesgo,
        # se intenta una sola entrada con riesgo total <= 1%, TP 2R y BE+2 en 1R.
        jump_single_fallback_blocked = (
            self._is_jump_symbol(exact_symbol)
            and bool(self.config.jump_strict_filter_enabled)
            and not bool(self.config.jump_allow_single_fallback)
        )
        if (
            legs is None
            and bool(self.config.split_entries_enabled)
            and bool(self.config.single_entry_fallback_enabled)
            and not jump_single_fallback_blocked
        ):
            single_specs = [("SINGLE", 1.0, float(self.config.single_entry_target_rr))]
            single_legs, single_failure = build_plan(single_specs, "SINGLE_FALLBACK")
            if single_legs is not None:
                legs = single_legs
                execution_mode = "SINGLE_FALLBACK"
            else:
                # Si el problema es que el volumen máximo del broker ni siquiera permite
                # alcanzar el riesgo objetivo, conservamos el código histórico porque no
                # se trata de sobre-riesgo y el fallback tampoco puede solucionarlo.
                if (split_failure or {}).get("code") == "LOTE_DEL_BROKER_NO_PERMITE_ALCANZAR_RIESGO_OBJETIVO" and (single_failure or {}).get("code") == "LOTE_DEL_BROKER_NO_PERMITE_ALCANZAR_RIESGO_OBJETIVO":
                    sf = split_failure or {}
                    return {
                        "symbol": exact_symbol,
                        "action": "REJECTED_RISK_TARGET_UNREACHABLE",
                        "reason": "BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK",
                        "leg": sf.get("leg"),
                        "risk_amount": sf.get("risk_amount"),
                        "actual_risk_amount": sf.get("actual_risk_amount"),
                        "min_required_risk": sf.get("min_required_risk"),
                        "actual_risk_percent": sf.get("actual_risk_percent"),
                        "execution_key": key,
                        "split_failure": split_failure,
                        "single_failure": single_failure,
                    }
                return {
                    "symbol": exact_symbol,
                    "action": "OPERACION_RECHAZADA_POR_RIESGO",
                    "reason": "NI_LA_DIVISION_NI_LA_ENTRADA_UNICA_RESPETAN_EL_RIESGO_MAXIMO",
                    "risk_amount": total_risk_amount,
                    "risk_percent": total_risk_percent,
                    "split_failure": split_failure,
                    "single_failure": single_failure,
                    "execution_key": key,
                }
        elif legs is None:
            if jump_single_fallback_blocked:
                return {
                    "symbol": exact_symbol,
                    "action": "JUMP_SINGLE_FALLBACK_BLOCKED",
                    "reason": "JUMP_REQUIERE_EJECUCION_DIVIDIDA_TP1_RUNNER",
                    "split_failure": split_failure,
                    "execution_key": key,
                }
            return {
                "symbol": exact_symbol,
                "action": "OPERACION_RECHAZADA_POR_RIESGO",
                "reason": (split_failure or {}).get("code", "PLAN_DE_RIESGO_NO_VIABLE"),
                "risk_amount": total_risk_amount,
                "risk_percent": total_risk_percent,
                "risk_failure": split_failure,
                "execution_key": key,
            }

        total_actual_risk_amount = sum(float(leg["actual_risk_amount"]) for leg in legs)
        total_actual_risk_percent = total_actual_risk_amount / risk_base_value * 100.0 if risk_base_value > 0 else 0.0

        max_margin_fraction = self.config.max_margin_fraction
        if max_margin_fraction is not None:
            margins = []
            for leg in legs:
                result = (leg.get("order_check") or {}).get("result") or {}
                if result.get("margin") is not None:
                    margins.append(float(result["margin"]))
            if margins:
                required_margin = sum(margins)
                max_margin = risk_base_value * float(max_margin_fraction)
                if required_margin > max_margin + 1e-9:
                    return {
                        "symbol": exact_symbol,
                        "action": "REJECTED_MARGIN_EXCEEDED",
                        "reason": "SPLIT_ORDERS_MARGIN_EXCEEDS_LIMIT",
                        "required_margin": required_margin,
                        "max_allowed_margin": max_margin,
                        "execution_key": key,
                        "legs": legs,
                    }

        base = {
            "symbol": exact_symbol,
            "strategy_name": strategy_name,
            "strategy_version": strategy_version,
            "signal_id": signal_id,
            "execution_key": key,
            "direction": direction,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": legs[-1]["take_profit"],
            "original_stop_loss": original_sl,
            "planned_rr": legs[-1]["target_rr"],
            "risk_base": risk_base_name,
            "risk_base_value": risk_base_value,
            "risk_percent": total_risk_percent,
            "risk_amount": total_risk_amount,
            "actual_risk_amount": total_actual_risk_amount,
            "actual_risk_percent": total_actual_risk_percent,
            "split_entries_enabled": bool(self.config.split_entries_enabled),
            "execution_mode": execution_mode,
            "execution_mode_es": {
                "SPLIT": "DOS ENTRADAS: 0,5% + 0,5%",
                "SINGLE_FALLBACK": "ENTRADA ÚNICA ALTERNATIVA: HASTA 1%",
                "SINGLE": "ENTRADA ÚNICA",
            }.get(execution_mode, execution_mode),
            "split_failure": split_failure if execution_mode == "SINGLE_FALLBACK" else None,
            "break_even_offset_points": int(self.config.break_even_offset_points),
            "legs": legs,
            "stop_validation": stop_validation,
            "market_signal_diagnostics": market_signal_diagnostics,
            "analysis": analysis,
            "direction_policy": policy,
            "gold_contract_selection": (
                self._orb_gold_cycle_diagnostics
                if strategy_name == "ORB_NEW_YORK" and is_orb_gold_symbol(exact_symbol)
                else None
            ),
        }

        if self.config.diagnostic_mode:
            base["position_diagnostics"] = self._open_trade_diagnostics(exact_symbol)
            base["sync"] = sync_info

        if not self.config.execution_enabled:
            return {"action": "DRY_RUN_VALIDATED", **base}

        # Ejecución DEMO: abre las dos piernas como posiciones independientes,
        # pero auditadas como una sola operación lógica de riesgo total <= 1%.
        if self.lifecycle_manager is not None:
            opened = []
            for leg in legs:
                execution_signal = {
                    "symbol": exact_symbol,
                    "timeframe": str(signal.get("timeframe") or (self.config.orb_timeframe if strategy_name == "ORB_NEW_YORK" else self.config.entry_timeframe)),
                    "direction": direction,
                    "entry_time": signal["entry_time"],
                    "entry_price": entry,
                    "stop_loss": sl,
                    "take_profit": leg["take_profit"],
                    "risk_reward_ratio": leg["target_rr"],
                    "action": "ORB_NY_CONFIRMED" if strategy_name == "ORB_NEW_YORK" else "SMC_HARMONIC_CONFIRMED",
                }
                lifecycle = self.lifecycle_manager.create_from_signal(execution_signal)
                lifecycle.metadata.update({
                    "execution_key": leg["execution_key"],
                    "parent_execution_key": key,
                    "trade_leg": leg["name"],
                    "execution_mode": execution_mode,
                    "signal_id": signal_id,
                    "risk_base": risk_base_name,
                    "risk_base_value": risk_base_value,
                    "operation_risk_percent": total_risk_percent,
                    "risk_percent": leg["risk_percent"],
                    "risk_amount": leg["risk_amount"],
                    "actual_risk_amount": leg["actual_risk_amount"],
                    "initial_stop_loss": sl,
                    "break_even_enabled": bool(self.config.break_even_enabled),
                    "break_even_trigger_rr": float(self.config.break_even_trigger_rr),
                    "break_even_offset_points": int(self.config.break_even_offset_points),
                    "strategy_version": strategy_version,
                    "strategy_name": strategy_name,
                    "confirmation_decision": signal.get("confirmation_decision"),
                    "confirmation_percentage": signal.get("confirmation_percentage"),
                    "trade_score": signal.get("trade_score"),
                    "passed_confirmations": signal.get("passed_confirmations") or [],
                    "missing_confirmations": signal.get("missing_confirmations") or [],
                    "confirmations_passed": len(signal.get("passed_confirmations") or []),
                    "confirmations_total": len(signal.get("confirmations") or {}),
                    "runner_initial_target_rr": float(leg.get("logical_target_rr", self.config.second_target_rr)),
                    "runner_logical_target_rr": float(leg.get("logical_target_rr", leg["target_rr"])),
                    "runner_broker_safety_target_rr": float(leg.get("broker_target_rr", leg["target_rr"])),
                    "runner_max_target_rr": (
                        None if self._is_synthetics_profile_name(self.config.bot_profile)
                        else float(self.config.runner_extension_max_target_rr)
                        if strategy_name == "ORB_NEW_YORK"
                        else float(self.config.smc_runner_max_target_rr)
                    ),
                    "runner_tp3_guard_trigger_rr": (
                        None if strategy_name == "ORB_NEW_YORK"
                        or self._is_synthetics_profile_name(self.config.bot_profile)
                        else float(self.config.smc_runner_tp3_guard_trigger_rr)
                    ),
                    "runner_tp3_guard_lock_rr": (
                        None if strategy_name == "ORB_NEW_YORK"
                        or self._is_synthetics_profile_name(self.config.bot_profile)
                        else float(self.config.smc_runner_tp3_guard_lock_rr)
                    ),
                    "runner_tp4_guard_trigger_rr": (
                        None if strategy_name == "ORB_NEW_YORK"
                        or self._is_synthetics_profile_name(self.config.bot_profile)
                        else float(self.config.smc_runner_tp4_guard_trigger_rr)
                    ),
                    "runner_tp4_guard_lock_rr": (
                        None if strategy_name == "ORB_NEW_YORK"
                        or self._is_synthetics_profile_name(self.config.bot_profile)
                        else float(self.config.smc_runner_tp4_guard_lock_rr)
                    ),
                    "bot_profile": str(self.config.bot_profile).upper(),
                    "daemon_magic": int(self.config.magic),
                    "orb_market": signal.get("orb_market"),
                    "orb_session_date": signal.get("orb_session_date"),
                    "opening_range_high": signal.get("opening_range_high"),
                    "opening_range_low": signal.get("opening_range_low"),
                    "opening_range_midpoint": signal.get("opening_range_midpoint"),
                    "breakout_candle_time_ny": signal.get("breakout_candle_time_ny"),
                    "breakout_candle_time": signal.get("breakout_candle_time"),
                    "retest_candle_time_ny": signal.get("retest_candle_time_ny"),
                    "orb_risk_model": signal.get("orb_risk_model"),
                    "orb_runner_plan": signal.get("orb_runner_plan"),
                    "session_vwap": signal.get("session_vwap"),
                    "session_poc": signal.get("session_poc"),
                    "higher_timeframe_context": signal.get("higher_timeframe_context") or analysis.get("higher_timeframe_context"),
                    "htf_alignment": not bool((signal.get("higher_timeframe_context") or analysis.get("higher_timeframe_context") or {}).get("blocked")),
                    "htf_blocked": bool((signal.get("higher_timeframe_context") or analysis.get("higher_timeframe_context") or {}).get("blocked")),
                    "htf_reason": (signal.get("higher_timeframe_context") or analysis.get("higher_timeframe_context") or {}).get("reason"),
                    "gold_contract_selection": (
                        self._orb_gold_cycle_diagnostics
                        if strategy_name == "ORB_NEW_YORK" and is_orb_gold_symbol(exact_symbol)
                        else None
                    ),
                    "harmonic_confirmed": bool(signal.get("harmonic_confirmed", False)),
                    "harmonic_pattern": signal.get("harmonic_pattern"),
                    "harmonic_score": signal.get("harmonic_score"),
                    "divergence_confirmation": bool(signal.get("divergence_confirmation", False)),
                    "divergence_type": signal.get("divergence_type"),
                    "h1_doji_confirmation": bool(signal.get("h1_doji_confirmation", False)),
                    "h1_doji_type": signal.get("h1_doji_type"),
                    "h1_doji_time": signal.get("h1_doji_time"),
                    "h1_doji_zone": signal.get("h1_doji_zone"),
                    "h1_doji_reason": signal.get("h1_doji_reason"),
                    "h1_doji_body_ratio": signal.get("h1_doji_body_ratio"),
                    "h1_doji_upper_wick_ratio": signal.get("h1_doji_upper_wick_ratio"),
                    "h1_doji_lower_wick_ratio": signal.get("h1_doji_lower_wick_ratio"),
                    # Evidencia explicable de la decisión de entrada. Se persiste en
                    # SQLite para que el XLSX pueda reconstruir exactamente por qué
                    # el daemon autorizó el trade, incluso después de reiniciar.
                    "trade_score": signal.get("trade_score"),
                    "trade_grade": signal.get("trade_grade"),
                    "confirmation_decision": signal.get("confirmation_decision"),
                    "confirmation_percentage": signal.get("confirmation_percentage"),
                    "confirmations_passed": signal.get("confirmations_passed"),
                    "confirmations_total": signal.get("confirmations_total"),
                    "passed_confirmations": signal.get("passed_confirmations", []),
                    "missing_confirmations": signal.get("missing_confirmations", []),
                    "critical_confirmations_ok": signal.get("critical_confirmations_ok"),
                    "critical_confirmation_failures": signal.get("critical_confirmation_failures", []),
                    "rejection_reasons": signal.get("rejection_reasons", []),
                    "confirmation_details": signal.get("confirmations", {}),
                    "h1_trend": analysis.get("h1_trend"),
                    "m15_setup_type": analysis.get("m15_setup_type"),
                    "m15_structure_break_type": analysis.get("m15_structure_break_type"),
                    "m15_zone": analysis.get("m15_zone"),
                    "stop_validation": stop_validation,
                    "order_check": leg["order_check"],
                })
                # La notificación EXECUTION_FILLED persiste el trade dentro de
                # execute_with_executor. El lock impide que el monitor importe
                # el ticket MT5 durante la pequeña ventana entre fill y commit.
                with self._execution_persistence_lock:
                    lifecycle = self.lifecycle_manager.execute_with_executor(
                        lifecycle=lifecycle,
                        volume=float(leg["sizing"]["volume"]),
                    )

                if lifecycle.execution_status != "FILLED":
                    rollback = []
                    for previous in opened:
                        try:
                            rollback.append(self.lifecycle_manager.close_execution(
                                previous["lifecycle"], reason="split_entry_rollback"
                            ))
                        except Exception as exc:
                            rollback.append({"closed": False, "error": str(exc)})
                    return {
                        "symbol": exact_symbol,
                        "action": "EXECUTION_REJECTED",
                        "execution_key": leg["execution_key"],
                        "failed_leg": leg["name"],
                        "reason": lifecycle.metadata.get("execution_reason"),
                        "rollback": rollback,
                        "lifecycle": lifecycle.to_dict(),
                        **base,
                    }

                post_fill_risk = self._validate_post_fill_risk(
                    symbol=exact_symbol,
                    direction=direction,
                    position_ticket=lifecycle.position_ticket,
                    target_risk_amount=leg["risk_amount"],
                    risk_base_value=risk_base_value,
                )
                lifecycle.metadata["post_fill_risk"] = post_fill_risk
                if not post_fill_risk.get("valid", False):
                    incident = {
                        "reason": post_fill_risk.get("reason"),
                        "trade_leg": leg["name"],
                        "target_risk_amount": leg["risk_amount"],
                        "hard_risk_cap": post_fill_risk.get("hard_risk_cap"),
                        "actual_risk_amount": post_fill_risk.get("actual_risk_amount"),
                        "risk_excess_ratio": post_fill_risk.get("risk_excess_ratio"),
                        "recoverable_execution_granularity_breach": post_fill_risk.get(
                            "recoverable_execution_granularity_breach"
                        ),
                        "position_ticket": lifecycle.position_ticket,
                        "direction": direction,
                    }
                    self._quarantine_symbol(exact_symbol, incident)
                    all_lifecycles = [item["lifecycle"] for item in opened] + [lifecycle]
                    rollback = []
                    if bool(self.config.emergency_risk_exit_enabled):
                        for active in all_lifecycles:
                            try:
                                rollback.append(self.lifecycle_manager.close_execution(
                                    active, reason="emergency_split_risk_hard_cap_breach"
                                ))
                            except Exception as exc:
                                rollback.append({"closed": False, "error": str(exc)})
                    return {
                        "symbol": exact_symbol,
                        "action": "EMERGENCY_RISK_EXIT",
                        "reason": "POST_FILL_RISK_HARD_CAP_BREACH",
                        "failed_leg": leg["name"],
                        "post_fill_risk": post_fill_risk,
                        "quarantine": self._quarantine_result(exact_symbol),
                        "emergency_close": rollback,
                        **base,
                    }

                # El callback habitual ya corrió dentro de execute_with_executor.
                # Si falló, serializamos también la verificación y la defensa
                # final frente al importador MT5 del monitor de posiciones.
                with self._execution_persistence_lock:
                    row = self.repository.get_trade_by_execution_key(leg["execution_key"])
                    persistence_recovery = None
                    if row is None and self.reporting_service is not None:
                        try:
                            persistence_recovery = self.reporting_service.on_lifecycle_event(
                                event="EXECUTION_FILLED",
                                lifecycle=lifecycle,
                                volume=float(leg["sizing"]["volume"]),
                            )
                        except Exception as exc:
                            persistence_recovery = {"error": str(exc)}
                        row = self.repository.get_trade_by_execution_key(leg["execution_key"])

                    if row is None:
                        # Última defensa: si el broker confirmó FILLED pero el callback
                        # de reporting no creó la fila, persistimos directamente.
                        trade_id, _ = self.repository.create_trade_once({
                            "external_ticket": lifecycle.execution_id or lifecycle.position_ticket,
                            "execution_key": leg["execution_key"],
                            "broker_position_ticket": lifecycle.position_ticket,
                            "source": self.config.source,
                            "broker": lifecycle.metadata.get("execution_broker") or account.get("server") or "MT5",
                            "instrument": exact_symbol,
                            "timeframe": lifecycle.timeframe,
                            "direction": direction,
                            "status": "OPEN",
                            "entry_time": lifecycle.execution_time or lifecycle.entry_time,
                            "entry_price": lifecycle.entry_price,
                            "stop_loss": lifecycle.stop_loss,
                            "take_profit": lifecycle.take_profit,
                            "volume": float(leg["sizing"]["volume"]),
                            "planned_rr": leg["target_rr"],
                            "balance_before": account.get("balance"),
                            "equity": account.get("equity"),
                            "risk_percent": leg["risk_percent"],
                            "risk_amount": leg["actual_risk_amount"],
                            "setup_reason": "Persistencia defensiva posterior a fill MT5",
                            "details": {
                                "metadata": {
                                    **dict(lifecycle.metadata or {}),
                                    "bot_profile": str(self.config.bot_profile).upper(),
                                    "daemon_magic": int(self.config.magic),
                                },
                                "persistence_recovery": persistence_recovery,
                                "signal": signal,
                                "analysis": analysis,
                            },
                            "strategy_version": strategy_version,
                        })
                        row = self.repository.get_trade(trade_id)
                        self._persist_audit_event(
                            "TRADE_PERSISTENCE_RECOVERY",
                            instrument=exact_symbol,
                            action="FILLED_TRADE_RECOVERED",
                            execution_key=leg["execution_key"],
                            broker_position_ticket=lifecycle.position_ticket,
                            payload={"trade_id": trade_id, "recovery": persistence_recovery},
                        )

                if row is not None:
                    try:
                        self._persist_entry_audit_immediately(
                            row, signal, analysis, ticket=lifecycle.position_ticket
                        )
                    except Exception as exc:
                        self._persist_audit_event(
                            "TRADE_ENTRY_AUDIT_ERROR",
                            instrument=exact_symbol,
                            action="ENTRY_AUDIT_PERSIST_FAILED",
                            reason=str(exc),
                            broker_position_ticket=lifecycle.position_ticket,
                        )

                opened.append({
                    "leg": leg["name"],
                    "trade_id": None if row is None else int(row["id"]),
                    "sqlite_trade_found": row is not None,
                    "position_ticket": lifecycle.position_ticket,
                    "execution_id": lifecycle.execution_id,
                    "post_fill_risk": post_fill_risk,
                    "lifecycle": lifecycle,
                })

            self._mark_orb_session_after_fill(exact_symbol, signal)
            return {
                "action": "SPLIT_ORDER_OPENED" if execution_mode == "SPLIT" else "ORDER_OPENED",
                "opened_legs": [
                    {**item, "lifecycle": item["lifecycle"].to_dict()} for item in opened
                ],
                **base,
            }

        # Compatibilidad sin lifecycle_manager. También respeta las dos piernas.
        opened = []
        for leg in legs:
            placed = self.executor.place_market_order(
                exact_symbol, direction, leg["sizing"]["volume"], sl, leg["take_profit"],
                self.config.magic, leg["comment"], self.config.deviation,
            )
            position_ticket = (
                self.executor.find_position_ticket(exact_symbol, self.config.magic, leg["comment"])
                or self.executor.position_ticket_from_deal(placed.get("deal_ticket"))
            )
            external_ticket = str(placed.get("order_ticket") or placed.get("deal_ticket") or leg["execution_key"])
            trade_id, created = self.repository.create_trade_once({
                "external_ticket": external_ticket,
                "execution_key": leg["execution_key"],
                "broker_order_ticket": placed.get("order_ticket"),
                "broker_deal_ticket": placed.get("deal_ticket"),
                "broker_position_ticket": position_ticket,
                "source": self.config.source,
                "broker": account["server"],
                "instrument": exact_symbol,
                "timeframe": str(signal.get("timeframe") or (self.config.orb_timeframe if strategy_name == "ORB_NEW_YORK" else self.config.entry_timeframe)),
                "direction": direction,
                "status": "OPEN",
                "entry_time": datetime.now(timezone.utc),
                "entry_price": float(placed["entry_price"]),
                "stop_loss": sl,
                "take_profit": leg["take_profit"],
                "volume": leg["sizing"]["volume"],
                "planned_rr": leg["target_rr"],
                "balance_before": account["balance"],
                "equity": account["equity"],
                "risk_percent": leg["risk_percent"],
                "risk_amount": leg["actual_risk_amount"],
                "setup_reason": (
                    "ORB NY M5 breakout + retest ORB + VWAP + POC + SL 50% ORB"
                    if strategy_name == "ORB_NEW_YORK"
                    else "H1 trend,M15 SMC setup,M5 OB retest + harmonic confluence"
                ),
                "details": {
                    "signal": signal,
                    "analysis": analysis,
                    "sizing": leg["sizing"],
                    "metadata": {
                        "parent_execution_key": key,
                        "trade_leg": leg["name"],
                        "execution_mode": execution_mode,
                        "bot_profile": str(self.config.bot_profile).upper(),
                        "daemon_magic": int(self.config.magic),
                        "operation_risk_percent": total_risk_percent,
                        "runner_initial_target_rr": float(leg.get("logical_target_rr", self.config.second_target_rr)),
                        "runner_logical_target_rr": float(leg.get("logical_target_rr", leg["target_rr"])),
                        "runner_broker_safety_target_rr": float(leg.get("broker_target_rr", leg["target_rr"])),
                        "runner_max_target_rr": (
                            None if self._is_synthetics_profile_name(self.config.bot_profile)
                            else float(self.config.forex_runner_max_target_rr)
                            if self._uses_forex_style_smc_management(self.config.bot_profile)
                            else (
                                float(self.config.runner_extension_max_target_rr)
                                if strategy_name == "ORB_NEW_YORK"
                                else float(self.config.smc_runner_max_target_rr)
                            )
                        ),
                        "runner_tp3_guard_trigger_rr": (
                            None if strategy_name == "ORB_NEW_YORK"
                            or self._is_synthetics_profile_name(self.config.bot_profile)
                            else float(self.config.smc_runner_tp3_guard_trigger_rr)
                        ),
                        "runner_tp3_guard_lock_rr": (
                            None if strategy_name == "ORB_NEW_YORK"
                            or self._is_synthetics_profile_name(self.config.bot_profile)
                            else float(self.config.smc_runner_tp3_guard_lock_rr)
                        ),
                        "runner_tp4_guard_trigger_rr": (
                            None if strategy_name == "ORB_NEW_YORK"
                            or self._is_synthetics_profile_name(self.config.bot_profile)
                            else float(self.config.smc_runner_tp4_guard_trigger_rr)
                        ),
                        "runner_tp4_guard_lock_rr": (
                            None if strategy_name == "ORB_NEW_YORK"
                            or self._is_synthetics_profile_name(self.config.bot_profile)
                            else float(self.config.smc_runner_tp4_guard_lock_rr)
                        ),
                        "break_even_offset_points": int(self.config.break_even_offset_points),
                        "break_even_trigger_rr": float(self.config.break_even_trigger_rr),
                        "strategy_name": strategy_name,
                        "strategy_version": strategy_version,
                        "orb_session_date": signal.get("orb_session_date"),
                        "breakout_candle_time": signal.get("breakout_candle_time"),
                        "confirmation_decision": signal.get("confirmation_decision"),
                        "confirmation_percentage": signal.get("confirmation_percentage"),
                        "trade_score": signal.get("trade_score"),
                        "passed_confirmations": signal.get("passed_confirmations") or [],
                        "missing_confirmations": signal.get("missing_confirmations") or [],
                        "confirmations_passed": len(signal.get("passed_confirmations") or []),
                        "confirmations_total": len(signal.get("confirmations") or {}),
                        "risk_base": risk_base_name,
                        "risk_base_value": risk_base_value,
                        "original_stop_loss": original_sl,
                        "stop_validation": stop_validation,
                        "order_check": leg["order_check"],
                    },
                },
                "strategy_version": strategy_version,
            })
            try:
                persisted_trade = self.repository.get_trade(trade_id)
                self._persist_entry_audit_immediately(
                    persisted_trade, signal, analysis, ticket=position_ticket
                )
            except Exception as exc:
                self._persist_audit_event(
                    "TRADE_ENTRY_AUDIT_ERROR",
                    instrument=exact_symbol,
                    action="ENTRY_AUDIT_PERSIST_FAILED",
                    reason=str(exc),
                    broker_position_ticket=position_ticket,
                )
            opened.append({
                "leg": leg["name"], "trade_id": trade_id, "created": created,
                "position_ticket": position_ticket, "execution_key": leg["execution_key"],
            })
        self._mark_orb_session_after_fill(exact_symbol, signal)
        return {
            "action": "SPLIT_ORDER_OPENED" if execution_mode == "SPLIT" else "ORDER_OPENED",
            "opened_legs": opened,
            **base,
        }

    def _pre_execution_ranking_enabled(self) -> bool:
        """Activa selección real sólo en modo RANKING explícito."""
        return bool(
            self.config.execution_enabled
            and self.config.meta_labeling_enabled
            and self.config.meta_labeling_ranking_enabled
            and str(self.config.meta_labeling_mode or "").upper() == RANKING_MODE
        )

    @staticmethod
    def _meta_label_from_result(result: dict) -> dict:
        analysis = result.get("analysis") if isinstance(result, dict) else {}
        analysis = analysis if isinstance(analysis, dict) else {}
        signal = analysis.get("signal") or analysis.get("entry") or {}
        return signal.get("meta_label") if isinstance(signal, dict) and isinstance(signal.get("meta_label"), dict) else {}

    def _process_symbols_with_pre_execution_ranking(
        self,
        symbols,
        *,
        sync_before_execution,
        progress_callback,
        before_symbol,
        after_symbol,
        batch_size,
        batch_delay_seconds,
    ):
        """Valida el ciclo sin fills, rankea y recién entonces ejecuta.

        Si algún modelo aún no está entrenado, no descarta ninguna candidata:
        conserva el contrato seguro de no bloquear por falta de historial.
        """
        symbols = list(symbols)
        if sync_before_execution:
            self._sync_open_trades_before_execution()

        execution_enabled = bool(self.config.execution_enabled)
        try:
            self.config.execution_enabled = False
            preliminary = self.process_symbols(
                symbols,
                sync_before_execution=False,
                progress_callback=None,
                before_symbol=before_symbol,
                after_symbol=after_symbol,
                batch_size=batch_size,
                batch_delay_seconds=batch_delay_seconds,
                _ranking_preflight=True,
            )
        finally:
            self.config.execution_enabled = execution_enabled

        candidates = []
        for index, result in enumerate(preliminary):
            if not isinstance(result, dict) or result.get("action") != "DRY_RUN_VALIDATED":
                continue
            decision = self._meta_label_from_result(result)
            candidates.append({"index": index, "symbol": symbols[index], "decision": decision})

        trained_cycle = bool(candidates) and all(
            bool(item["decision"].get("trained")) for item in candidates
        )
        selected_indexes = {item["index"] for item in candidates}
        ranking = []
        if trained_cycle:
            decisions = []
            for item in candidates:
                payload = dict(item["decision"])
                payload["candidate_index"] = item["index"]
                decisions.append(payload)
            ranking = rank_signals(
                decisions,
                max_signals=int(self.config.meta_labeling_max_signals_per_cycle),
            )
            selected_indexes = {
                int(row["candidate_index"])
                for row in ranking
                if row.get("selected") and row.get("candidate_index") is not None
            }
            self._persist_audit_event(
                "META_LABEL_PRE_EXECUTION_RANKING",
                action="TRAINED_SIGNALS_SELECTED_BEFORE_FILL",
                reason="RANKED_BY_NET_EXPECTANCY_AND_PROBABILITY",
                payload={"ranking": ranking},
            )

        self._meta_label_cycle_decisions = []
        results = list(preliminary)
        for item in candidates:
            index = item["index"]
            if index in selected_indexes:
                results[index] = self.process_symbol(item["symbol"], sync_before_execution=False)
            else:
                results[index] = {
                    "symbol": item["symbol"],
                    "action": "META_LABEL_RANKING_NOT_SELECTED",
                    "reason": "LOWER_EXPECTANCY_THAN_SELECTED_SIGNAL",
                    "meta_label": item["decision"],
                    "ranking": ranking,
                }

        self.meta_label_cycle_ranking()
        if progress_callback is not None:
            total = len(results)
            for index, result in enumerate(results, start=1):
                progress_callback(
                    result=result,
                    index=index,
                    total=total,
                    elapsed_seconds=0.0,
                )
        return results

    def process_symbols(
        self,
        symbols,
        sync_before_execution: bool = True,
        progress_callback=None,
        before_symbol=None,
        after_symbol=None,
        batch_size=None,
        batch_delay_seconds: float = 0.0,
        _ranking_preflight: bool = False,
    ):
        """Procesa símbolos uno a uno con puntos de control cooperativos.

        ``progress_callback`` permite informar progreso inmediatamente, sin esperar
        a que termine todo el ciclo. ``before_symbol`` y ``after_symbol`` permiten
        que el daemon ejecute tareas urgentes (por ejemplo Break Even) entre
        símbolos, evitando que un ciclo largo deje las posiciones sin supervisión.

        ``batch_size``/``batch_delay_seconds`` escalonan el procesamiento: tras
        cada lote de ese tamaño se espera la pausa indicada antes de continuar.
        Pensado para el ciclo de arranque en frío, donde ninguna etapa H1/M15/M5
        tiene caché todavía y una ráfaga de N símbolos simultáneos golpearía al
        broker de una sola vez. En operación normal (``batch_size=None``) no
        cambia el comportamiento.
        """
        symbols = list(symbols)
        if self._pre_execution_ranking_enabled() and not _ranking_preflight:
            return self._process_symbols_with_pre_execution_ranking(
                symbols,
                sync_before_execution=sync_before_execution,
                progress_callback=progress_callback,
                before_symbol=before_symbol,
                after_symbol=after_symbol,
                batch_size=batch_size,
                batch_delay_seconds=batch_delay_seconds,
            )

        # Para Oro ORB, XAUUSD y XAUUSDmicro son alternativas de ejecución de la
        # misma tesis. Elegimos una sola antes de procesar el ciclo.
        if bool(self.config.orb_enabled):
            self._prepare_orb_gold_selection(symbols)

        # Sincronizar una sola vez por ciclo evita consultar MT5 hasta N veces para N símbolos.
        if sync_before_execution:
            self._sync_open_trades_before_execution()

        results = []
        total = len(symbols)
        self._meta_label_cycle_decisions = []
        for index, symbol in enumerate(symbols, start=1):
            symbol_started = time.monotonic()
            if before_symbol is not None:
                before_symbol(index=index, total=total, symbol=symbol)

            try:
                result = self.process_symbol(symbol, sync_before_execution=False)
            except Exception as exc:
                result = {"symbol": symbol, "action": "ERROR", "error": str(exc)}

            elapsed_seconds = time.monotonic() - symbol_started
            results.append(result)

            self._persist_audit_event(
                "SYMBOL_PROCESS_RESULT",
                instrument=str(symbol),
                action=result.get("action") if isinstance(result, dict) else None,
                reason=(
                    result.get("reason") or result.get("error")
                    if isinstance(result, dict) else None
                ),
                execution_key=(
                    result.get("execution_key")
                    if isinstance(result, dict) else None
                ),
                payload={
                    "schema_version": "strategy-evaluation-v1",
                    "result": self._compact_symbol_result(result),
                    "elapsed_seconds": elapsed_seconds,
                    "index": index,
                    "total": total,
                },
            )

            if progress_callback is not None:
                progress_callback(
                    result=result,
                    index=index,
                    total=total,
                    elapsed_seconds=elapsed_seconds,
                )

            if after_symbol is not None:
                after_symbol(
                    index=index,
                    total=total,
                    symbol=symbol,
                    result=result,
                    elapsed_seconds=elapsed_seconds,
                )

            if (
                batch_size
                and int(batch_size) > 0
                and index < total
                and index % int(batch_size) == 0
                and batch_delay_seconds > 0
            ):
                time.sleep(float(batch_delay_seconds))

        # El ranking se publica al cerrar el ciclo, cuando ya se conocen todas
        # las señales simultáneas y sus probabilidades.
        self.meta_label_cycle_ranking()

        return results

    def run_once(self, symbols):
        """Ejecuta un ciclo completo: sincroniza, gestiona break-even y analiza.

        Secuencia: reconciliar cierres con el broker, revisar break-even,
        procesar todos los simbolos y revisar break-even de nuevo.

        El break-even se evalua ANTES y DESPUES a proposito: el analisis de
        todos los simbolos lleva su tiempo, y una posicion podria alcanzar su
        umbral justo durante esa ventana. La segunda pasada evita dejarla sin
        proteger hasta el ciclo siguiente.

        Args:
            symbols: instrumentos candidatos del ciclo.

        Returns:
            Dict con los resultados por simbolo, el resultado de la
            sincronizacion y el estado de break-even antes y despues.
        """
        # Revisamos Break Even antes y después del análisis. Esto permite que el
        # modo --once también gestione posiciones ya abiertas y reduce una ventana
        # de tiempo en la que una posición podría alcanzar 1R durante el ciclo.
        # Sincronizamos antes de evaluar BE para recuperar un TP1 que haya cerrado
        # entre ciclos. En --once mantenemos una sola sincronización por compatibilidad;
        # el daemon continuo sincroniza en cada pasada del monitor.
        sync = self.sync_closed_trades()
        break_even_before = self._monitor_break_even_positions()
        results = self.process_symbols(symbols)
        break_even_after = self._monitor_break_even_positions()
        return {
            "results": results,
            "sync": sync,
            "break_even": {
                "before": break_even_before,
                "after": break_even_after,
            },
        }


    def _dashboard_chart_snapshots(self, candle_count=120):
        """Construye snapshots multi-timeframe para auditar posiciones abiertas.

        El visor puede navegar M1/M5/M15/H1/H4 sin que el navegador consulte MT5.
        Las lecturas al broker ocurren en el hilo desacoplado del monitor.
        M5/M15/H1 reutilizan el DataFrame SMC cacheado cuando existe; M1 se
        publica como contexto visual adicional y no altera la estrategia.
        """
        try:
            open_trades = self.repository.open_trades(source=self.config.source) or []
        except Exception:
            return {}

        owned_trades = [
            t for t in open_trades
            if isinstance(t, dict) and self._trade_owned_by_current_bot(t)
        ]
        symbols = sorted({
            str(t.get("instrument") or "").strip()
            for t in owned_trades
            if t.get("instrument")
        })
        snapshots = {}
        # El visor ofrece estas cuatro temporalidades exactas independientemente
        # de cambios futuros en la configuración del pipeline.
        # v109: mínimos reducidos (180/140/120/120 -> 120/100/90/90) como parte
        # de la optimización de memoria del coordinador: menos velas por
        # símbolo/timeframe implica JSON más chico persistido y servido.
        tf_map = {"M1": "M1", "M5": "M5", "M15": "M15", "H1": "H1", "H4": "H4"}
        counts = {"M1": max(120, int(candle_count)), "M5": max(100, int(candle_count)), "M15": max(90, int(candle_count)), "H1": max(90, int(candle_count)), "H4": max(90, int(candle_count))}

        def _serialize_frame(raw):
            """Convierte un DataFrame de velas a listas JSON con RSI(14) incluido.

            Normaliza los tiempos a UTC, ordena, elimina duplicados y calcula
            el RSI de 14 periodos por media exponencial. Los valores no
            calculables (las primeras velas, o divisiones por cero) quedan
            como `None` en lugar de NaN, que no es serializable a JSON.

            Returns:
                Tupla `(velas, ultimo_rsi)`, o `([], None)` si no hay datos.
            """
            if raw is None or raw.empty:
                return [], None
            df = raw.copy()
            df["time"] = pd.to_datetime(df["time"], utc=True)
            df = df.sort_values("time").drop_duplicates("time").reset_index(drop=True)
            close_series = df["close"].astype(float)
            delta = close_series.diff()
            gain = delta.clip(lower=0.0)
            loss = (-delta.clip(upper=0.0))
            avg_gain = gain.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
            avg_loss = loss.ewm(alpha=1.0 / 14.0, adjust=False, min_periods=14).mean()
            rs = avg_gain / avg_loss.replace(0.0, float("nan"))
            rsi14 = (100.0 - (100.0 / (1.0 + rs))).clip(lower=0.0, upper=100.0)
            candles = []
            for idx, row in df.iterrows():
                rv = rsi14.iloc[idx] if idx < len(rsi14) else None
                try:
                    rv = float(rv)
                    if not pd.notna(rv):
                        rv = None
                except Exception:
                    rv = None
                candles.append({
                    "time": row["time"].isoformat(),
                    "open": float(row["open"]), "high": float(row["high"]),
                    "low": float(row["low"]), "close": float(row["close"]),
                    "volume": (
                        float(row.get("tick_volume"))
                        if pd.notna(row.get("tick_volume"))
                        else None
                    ),
                    "rsi14": rv,
                })
            return candles, df

        for symbol in symbols:
            tf_snapshots = {}
            errors = []
            for label, timeframe in tf_map.items():
                try:
                    count = counts[label]
                    cache_reader = getattr(
                        getattr(self, "multi_timeframe", None), "cached_stage", None
                    )
                    cached = (
                        cache_reader(symbol, timeframe)
                        if callable(cache_reader) and label != "M1"
                        else {}
                    )
                    cached_result = cached.get("result") if isinstance(cached, dict) else None
                    analyzed = cached_result.get("data") if isinstance(cached_result, dict) else None
                    raw = analyzed
                    if raw is None and isinstance(cached, dict):
                        raw = cached.get("data")
                    # M1 es auxiliar; las temporalidades SMC sólo consultan al
                    # proveedor cuando todavía no existe una etapa cacheada.
                    if raw is None or not hasattr(raw, "empty") or raw.empty:
                        raw = self.provider.get_candles(
                            symbol=symbol, timeframe=timeframe, count=count
                        )
                    candles, raw_df = _serialize_frame(raw)
                    if not candles:
                        tf_snapshots[label] = {
                            "symbol": symbol, "timeframe": label, "candles": [],
                            "events": [], "zones": [], "levels": [], "smc_context": {},
                            "context_mode": "AUXILIAR" if label == "M1" else "ESTRATEGIA",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                        continue

                    if analyzed is None:
                        candidate = cached.get("data") if isinstance(cached, dict) else None
                        if candidate is not None and hasattr(candidate, "columns") and any(
                            col in candidate.columns for col in ("choch_bullish", "swing_high", "ob_type")
                        ):
                            analyzed = candidate
                    # M1 no forma parte del gate actual de entrada; usa OHLC para FVG
                    # y otras capas auxiliares que build_smc_visual_context pueda derivar.
                    visual_source = analyzed if analyzed is not None else raw_df
                    smc_visual = build_smc_visual_context(visual_source, candle_count=count)
                    tf_snapshots[label] = {
                        "symbol": symbol,
                        "timeframe": label,
                        "broker_timeframe": str(timeframe).upper(),
                        "candles": candles[-count:],
                        "events": smc_visual.get("events", []),
                        "zones": smc_visual.get("zones", []),
                        "levels": smc_visual.get("levels", []),
                        "smc_context": smc_visual.get("context", {}),
                        "smc_legend": smc_visual.get("legend", {}),
                        "context_mode": "AUXILIAR" if label == "M1" else "ESTRATEGIA",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                except Exception as exc:
                    errors.append(f"{label}: {exc}")
                    tf_snapshots[label] = {
                        "symbol": symbol, "timeframe": label, "candles": [],
                        "events": [], "zones": [], "levels": [], "smc_context": {},
                        "context_mode": "AUXILIAR" if label == "M1" else "ESTRATEGIA",
                        "error": str(exc), "updated_at": datetime.now(timezone.utc).isoformat(),
                    }

            # Conserva el contrato previo usando M5 como vista por defecto.
            default = tf_snapshots.get("M5") or next(iter(tf_snapshots.values()), {})
            mtf_context = {}
            for label in ("H4", "H1", "M15", "M5", "M1"):
                q = tf_snapshots.get(label, {})
                mtf_context[label] = {
                    "timeframe": label,
                    "context": q.get("smc_context", {}),
                    "recent_events": (q.get("events") or [])[-12:],
                    "recent_zones": (q.get("zones") or [])[-8:],
                    "context_mode": q.get("context_mode"),
                }
            snapshots[symbol] = {
                **default,
                "symbol": symbol,
                "timeframe": "M5",
                "timeframes": tf_snapshots,
                "available_timeframes": [tf for tf in ("M1", "M5", "M15", "H1", "H4") if tf in tf_snapshots],
                "multi_timeframe": mtf_context,
                "data_source": "DERIV_CHARTS",
                "evidence_mode": "CURRENT_MARKET_REFRESH",
                "error": " | ".join(errors) if errors else None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        return snapshots

    @staticmethod
    def _selection_profile_for_bot(bot_profile: str) -> str:
        """Traduce el perfil del worker al perfil de selección de instrumentos.

        Varios workers comparten la misma lista de instrumentos: todos los
        `FOREX*` usan `FOREX`, `GOLD` usa `ORB`, y el resto recae en
        `SYNTHETICS`. `IDX_OPEN` (Apertura Índices Bursátiles) tiene su propia
        selección independiente en /instruments, así que se mapea a sí mismo.
        """
        profile=str(bot_profile or "").upper()
        if profile.startswith("FOREX"): return "FOREX"
        if profile == "IDX_OPEN": return "IDX_OPEN"
        if profile in {"ORB", "GOLD"}: return "ORB"
        return "SYNTHETICS"

    def _selected_cycle_symbols(self, base_symbols):
        """Filtra los símbolos del ciclo según la selección vigente del usuario.

        El operador puede elegir desde el panel que instrumentos quedan
        activos. Este metodo busca esa seleccion en cascada:

        1. Seleccion por perfil guardada en el repositorio.
        2. Seleccion antigua sin perfil, solo para `SYNTHETICS`.
        3. Seleccion publicada por el servicio de dashboard.
        4. Si nada esta disponible, la lista base completa.

        Se conserva SIEMPRE el orden de `base_symbols`, y solo se filtra: una
        seleccion no puede introducir simbolos que el worker no gestiona.

        Args:
            base_symbols: instrumentos candidatos del worker.

        Returns:
            Lista filtrada de simbolos a analizar en este ciclo. Cualquier
            fallo de lectura degrada al siguiente origen en lugar de detener
            el ciclo.
        """
        base=[str(s) for s in (base_symbols or [])]
        profile=self._selection_profile_for_bot(getattr(self.config,"bot_profile",None))
        pref=None
        reader=getattr(self.repository,"latest_instrument_selection_profile",None)
        if callable(reader):
            try: pref=reader(profile,source=self.config.source)
            except Exception: pref=None
        if pref is None and profile == "SYNTHETICS":
            legacy=getattr(self.repository,"latest_instrument_selection",None)
            if callable(legacy):
                try: pref=legacy(source=self.config.source)
                except Exception: pref=None
        if pref is not None:
            selected={str(s) for s in (pref.get("selected_symbols") or [])}
            return [s for s in base if s in selected]
        if self.dashboard_service is not None:
            try:
                selected=self.dashboard_service.get_selected_symbols(default=base,selection_profile=profile)
                selected_set={str(s) for s in selected}
                return [s for s in base if s in selected_set]
            except Exception:
                pass
        return base

    @staticmethod
    def _current_strategy_view_from_analysis(analysis: dict) -> dict:
        """Normaliza cualquier resultado MTF a una vista auditable del estado actual.

        Incluso los estados WAITING/NO_SETUP se publican para evitar "Sin registro".
        """
        analysis = analysis if isinstance(analysis, dict) else {}
        m5 = analysis.get("m5") if isinstance(analysis.get("m5"), dict) else {}
        signal = analysis.get("signal") if isinstance(analysis.get("signal"), dict) else {}
        if not signal and isinstance(m5.get("signal"), dict):
            signal = m5.get("signal") or {}

        h1 = analysis.get("h1") if isinstance(analysis.get("h1"), dict) else {}
        h1_ctx = h1.get("context") if isinstance(h1.get("context"), dict) else {}
        m15 = analysis.get("m15") if isinstance(analysis.get("m15"), dict) else {}
        m15_setup = m15.get("setup") if isinstance(m15.get("setup"), dict) else {}

        def pick(*keys, default=None):
            """Devuelve el primer valor no nulo buscando en la señal y el análisis.

            Los distintos productores usan nombres de campo diferentes para el
            mismo dato; probar varias claves en orden evita depender de cual
            de ellos genero el resultado.
            """
            for source in (signal, analysis):
                if not isinstance(source, dict):
                    continue
                for key in keys:
                    value = source.get(key)
                    if value is not None:
                        return value
            return default

        confirmations = signal.get("confirmations") if isinstance(signal.get("confirmations"), dict) else {}
        passed = pick("passed_confirmations", "passed", default=[]) or []
        missing = pick("missing_confirmations", "missing", default=[]) or []
        critical = pick("critical_confirmation_failures", "critical_failures", default=[]) or []

        # Si el engine no expone listas explícitas, derivarlas del mapa booleano.
        if confirmations and not passed:
            passed = [k for k, v in confirmations.items() if bool(v)]
        if confirmations and not missing:
            missing = [k for k, v in confirmations.items() if not bool(v)]

        decision = (
            pick("confirmation_decision", "decision")
            or analysis.get("action")
            or analysis.get("state")
            or "ANALISIS_ACTUAL"
        )
        direction = pick("direction") or analysis.get("direction")
        return {
            "decision": decision,
            "state": analysis.get("state") or analysis.get("action"),
            "reason": analysis.get("reason"),
            "valid": bool(analysis.get("valid", False)),
            "direction": direction,
            "score": pick("trade_score", "score", "quality_score"),
            "grade": pick("trade_grade", "grade"),
            "confirmation_percentage": pick("confirmation_percentage"),
            "passed": list(passed),
            "missing": list(missing),
            "critical_failures": list(critical),
            "divergence_confirmed": bool(pick("divergence_confirmation", "divergence_confirmed", default=False)),
            "divergence_type": pick("divergence_type"),
            "harmonic_confirmed": bool(pick("harmonic_confirmed", default=False)),
            "harmonic_pattern": pick("harmonic_pattern"),
            "harmonic_score": pick("harmonic_score"),
            "chart_pattern_confirmed": bool(pick("chart_pattern_confirmed", default=False)),
            "chart_pattern_name": pick("chart_pattern_name"),
            "chart_pattern_strength": pick("chart_pattern_strength"),
            "chart_pattern_conflict": bool(pick("chart_pattern_conflict", default=False)),
            "chart_pattern_supporting_pattern": pick("chart_pattern_supporting_pattern"),
            "chart_pattern_supporting_direction": pick("chart_pattern_supporting_direction"),
            "chart_pattern_supporting_strength": pick("chart_pattern_supporting_strength"),
            "chart_pattern_conflicting_pattern": pick("chart_pattern_conflicting_pattern"),
            "chart_pattern_conflicting_direction": pick("chart_pattern_conflicting_direction"),
            "chart_pattern_conflicting_strength": pick("chart_pattern_conflicting_strength"),
            "chart_pattern_conflict_level": pick("chart_pattern_conflict_level"),
            "chart_pattern_conflict_reason": pick("chart_pattern_conflict_reason"),
            "chart_pattern_conflict_strength_delta": pick("chart_pattern_conflict_strength_delta"),
            "m1_reversal_confirmed": bool(
                pick("m1_reversal_confirmed", "reversal_m1_confirmed", default=False)
            ),
            "h1_doji_confirmed": bool(pick("h1_doji_confirmation", "h1_doji_confirmed", default=False)),
            "h1_doji_type": pick("h1_doji_type"),
            "h1_doji_zone": pick("h1_doji_zone"),
            "h1_trend": pick("h1_trend") or h1_ctx.get("trend"),
            "structure_break": (
                pick("m15_structure_break_type", "structure_break")
                or m15_setup.get("structure_break_type")
            ),
            "zone": pick("m15_zone", "zone") or m15_setup.get("zone"),
            "signal_time": pick("signal_time", "m5_confirmation_time"),
            "latest_closed_candle_time": (
                pick("latest_closed_candle_time")
                or (
                    (analysis.get("diagnostics") or {}).get("signal_age", {}).get(
                        "latest_closed_candle_time"
                    )
                    if isinstance(analysis.get("diagnostics"), dict)
                    and isinstance((analysis.get("diagnostics") or {}).get("signal_age"), dict)
                    else None
                )
            ),
            # v106: la salida por invalidación de análisis cuenta velas M15
            # cerradas (más contexto que M5) para el streak de confirmación,
            # aunque el comportamiento invalidante en sí se evalúa con M5.
            "latest_closed_m15_candle_time": (
                (analysis.get("diagnostics") or {}).get("m15", {}).get("last_candle_time")
                if isinstance(analysis.get("diagnostics"), dict)
                and isinstance((analysis.get("diagnostics") or {}).get("m15"), dict)
                else None
            ),
            "diagnostics": analysis.get("diagnostics") or {},
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _refresh_current_strategy_views(self):
        """Reanaliza posiciones abiertas y persiste el bloque 'ahora'.

        SMC usa el analizador MTF y ORB usa NewYorkORBStrategy. No ejecuta órdenes:
        nunca llama a process_symbol(), por lo que esta auditoría es sólo lectura.
        """
        now_mono = time.monotonic()
        last = float(getattr(self, "_last_current_strategy_refresh_monotonic", 0.0) or 0.0)
        interval = max(2.0, float(getattr(self.config, "current_strategy_refresh_seconds", 10.0)))
        if (now_mono - last) < interval:
            return {"updated": 0, "skipped": True}

        try:
            trades = [
                t for t in (self.repository.open_trades(source=self.config.source) or [])
                if isinstance(t, dict) and self._trade_owned_by_current_bot(t)
            ]
        except Exception as exc:
            return {"updated": 0, "error": str(exc)}

        auditable_trades = []
        for trade in trades:
            details = trade.get("details") if isinstance(trade.get("details"), dict) else {}
            metadata = details.get("metadata") if isinstance(details.get("metadata"), dict) else {}
            strategy_name = str(metadata.get("strategy_name") or "SMC").upper()
            trade["_audit_strategy_name"] = strategy_name
            auditable_trades.append(trade)

        if not auditable_trades:
            self._last_current_strategy_refresh_monotonic = now_mono
            return {"updated": 0, "symbols": 0}

        cache = dict(getattr(self, "_current_strategy_view_cache", {}) or {})
        by_symbol = {}
        errors = []
        strategy_by_symbol = {
            str(t.get("instrument") or ""): str(t.get("_audit_strategy_name") or "SMC").upper()
            for t in auditable_trades if t.get("instrument")
        }
        direction_by_symbol = {
            str(t.get("instrument") or ""): str(t.get("direction") or "").upper()
            for t in auditable_trades if t.get("instrument")
        }
        for symbol in sorted(strategy_by_symbol):
            try:
                strategy_name = strategy_by_symbol.get(symbol, "SMC")
                if strategy_name == "ORB_NEW_YORK":
                    analysis = self.orb_strategy.analyze_symbol(symbol)
                else:
                    analysis = self.multi_timeframe.analyze_symbol(symbol)
                view = self._current_strategy_view_from_analysis(analysis)
                view["strategy_name"] = strategy_name
                if strategy_name == "ORB_NEW_YORK":
                    htf_context = self._orb_higher_timeframe_context(
                        symbol,
                        direction_by_symbol.get(symbol),
                    )
                    view["higher_timeframe_context"] = htf_context
                    view["h1_trend"] = htf_context.get("h1_trend")
                    view["structure_break"] = htf_context.get("m15_structure")
                    view["htf_alignment"] = htf_context.get("h1_alignment")
                    view["htf_blocked"] = htf_context.get("blocked")
                    view["htf_reason"] = htf_context.get("reason")
                    view["orb_market"] = analysis.get("orb_market")
                    view["opening_range_high"] = analysis.get("opening_range_high")
                    view["opening_range_low"] = analysis.get("opening_range_low")
                    view["opening_range_midpoint"] = analysis.get("opening_range_midpoint")
                    view["session_vwap"] = analysis.get("session_vwap")
                    view["session_poc"] = analysis.get("session_poc")
                    view["breakout_up"] = analysis.get("breakout_up")
                    view["breakout_down"] = analysis.get("breakout_down")
                    view["retest_buy_ok"] = analysis.get("retest_buy_ok")
                    view["retest_sell_ok"] = analysis.get("retest_sell_ok")
                by_symbol[symbol] = view
                cache[symbol] = view
                self._persist_audit_event(
                    "OPEN_POSITION_STRATEGY_REFRESH",
                    instrument=symbol,
                    action="CURRENT_STRATEGY_VIEW_UPDATED",
                    reason=view.get("reason"),
                    payload={"current_strategy_view": view},
                )
            except Exception as exc:
                errors.append({"symbol": symbol, "error": str(exc)})

        self._current_strategy_view_cache = cache
        writer = getattr(self.repository, "upsert_trade_visual_audit", None)
        snapshot_writer = getattr(self.repository, "save_trade_audit_snapshot", None)
        existing = {}
        if callable(writer) and hasattr(self.repository, "trade_visual_audits"):
            try:
                existing = {
                    str(r.get("trade_id")): r
                    for r in (self.repository.trade_visual_audits(source=self.config.source) or [])
                    if isinstance(r, dict)
                }
            except Exception:
                existing = {}

        updated = 0
        if callable(writer):
            for trade in auditable_trades:
                symbol = str(trade.get("instrument") or "")
                view = by_symbol.get(symbol)
                trade_id = trade.get("id")
                if not view or not trade_id:
                    continue
                previous = existing.get(str(trade_id), {})
                latest_market = dict(previous.get("latest_market") or {})
                latest_market["current_strategy_view"] = view
                latest_market["strategy_evaluated_at"] = view.get("evaluated_at")
                try:
                    writer(
                        int(trade_id),
                        instrument=symbol,
                        bot_profile=str(self.config.bot_profile).upper(),
                        daemon_magic=int(self.config.magic),
                        broker_position_ticket=trade.get("broker_position_ticket"),
                        latest_market=latest_market,
                        source=self.config.source,
                    )
                    # v68: además del estado latest, guardar una serie histórica
                    # append-only para investigación Entrada vs. Ahora.
                    if callable(snapshot_writer):
                        entry_view = previous.get("entry_context") or {}
                        latest_chart = previous.get("latest_chart") or {}
                        visual_context = {
                            "entry_chart_captured_at": previous.get("entry_captured_at"),
                            "latest_visual_updated_at": previous.get("latest_updated_at"),
                            "available_timeframes": sorted(list((latest_chart.get("timeframes") or {}).keys())) if isinstance(latest_chart, dict) else [],
                            "strategy_evaluated_at": view.get("evaluated_at"),
                        }
                        snapshot_writer(
                            int(trade_id),
                            instrument=symbol,
                            entry_view=entry_view,
                            current_view=view,
                            market=latest_market,
                            visual_context=visual_context,
                            bot_profile=str(self.config.bot_profile).upper(),
                            daemon_magic=int(self.config.magic),
                            broker_position_ticket=trade.get("broker_position_ticket"),
                            source=self.config.source,
                            snapshot_at=view.get("evaluated_at"),
                        )
                    updated += 1
                except Exception as exc:
                    errors.append({"trade_id": trade_id, "symbol": symbol, "error": str(exc)})

        self._last_current_strategy_refresh_monotonic = now_mono
        return {"updated": updated, "symbols": len(by_symbol), "errors": errors}

    def run_daemon(
        self,
        symbols,
        interval_seconds=30,
        position_monitor_interval=2,
        console_reporter=None,
        max_cycles=None,
    ):
        """Ejecuta scanner de señales y monitor de posiciones desacoplados.

        En producción el monitor pesado corre en un hilo daemon independiente.
        Una sincronización lenta de MT5/SQLite deja de bloquear el scheduler de
        velas. ``max_cycles`` conserva modo cooperativo determinista para pruebas.
        """
        symbols = list(symbols)
        signal_interval = max(1, int(interval_seconds))
        monitor_interval = max(1, int(position_monitor_interval))
        reporter = console_reporter or self.console_reporter

        if reporter is not None:
            reporter.print_daemon_started(
                interval=signal_interval,
                symbols_count=len(symbols),
                position_monitor_interval=monitor_interval,
            )
        print({
            "action": "POSITION_MONITOR_STARTED",
            "signal_interval_seconds": signal_interval,
            "position_monitor_interval_seconds": monitor_interval,
            "monitor_mode": (
                "BACKGROUND_DECOUPLED"
                if bool(self.config.background_position_monitor_enabled) and max_cycles is None
                else "COOPERATIVE_TEST_MODE"
            ),
        })

        cycle_number = 0
        next_signal_at = time.monotonic()
        next_monitor_at = time.monotonic()
        last_idle_recovery_at = 0.0

        def load_owned_open_trades():
            """Carga las operaciones abiertas que pertenecen a este worker.

            Returns:
                Lista de operaciones propias, `[]` si no hay ninguna, o `None`
                si la lectura fallo. La distincion importa: `[]` autoriza la
                via rapida de reposo, mientras que `None` significa "no se
                sabe" y obliga a hacer el monitoreo completo.
            """
            try:
                return [
                    trade
                    for trade in (self.repository.open_trades(source=self.config.source) or [])
                    if isinstance(trade, dict) and self._trade_owned_by_current_bot(trade)
                ]
            except Exception:
                return None

        def run_position_monitor_if_due(*, force=False, phase=""):
            """Ejecuta el monitor de posiciones si toca por cadencia.

            El monitor es la parte cara del daemon: consulta el broker,
            reconcilia cierres, evalua break-even y trailing, regenera
            graficos y reconstruye informes. Por eso se limita su frecuencia.

            VIA RAPIDA DE REPOSO: sin posiciones propias abiertas, no tiene
            sentido pagar todo ese trabajo cada pocos segundos. En ese caso
            solo se ejecuta una recuperacion ligera de posiciones no
            persistidas, y con un intervalo mucho mas amplio.

            El orden importa: primero se sincronizan los cierres, para que un
            tramo TP1 recien cerrado permita activar break-even en esta misma
            pasada aunque el precio ya haya retrocedido.

            Args:
                force: ejecuta ahora, ignorando la cadencia y la via rapida.
                phase: etiqueta del momento del ciclo, para diagnostico.

            Returns:
                Dict con el resultado del monitoreo, o `None` si aun no tocaba.
            """
            nonlocal next_monitor_at, last_idle_recovery_at
            now = time.monotonic()
            if not force and now < next_monitor_at:
                return None
            monitor_started = time.monotonic()
            try:
                open_owned = load_owned_open_trades()
                idle_recovery_interval = max(
                    float(monitor_interval),
                    float(getattr(self.config, "idle_position_recovery_seconds", 30.0)),
                )
                # v93: once monitores sin posiciones no deben consultar MT5,
                # crear gráficos y reconstruir XLSX cada dos segundos.
                if open_owned == [] and not force:
                    if (now - last_idle_recovery_at) < idle_recovery_interval:
                        return {
                            "break_even": {
                                "checked": 0, "activated": 0, "errors": [],
                                "skipped": "NO_OWNED_OPEN_POSITIONS",
                            },
                            "sync": 0,
                            "elapsed_seconds": time.monotonic() - monitor_started,
                            "phase": phase,
                            "idle_fast_path": True,
                        }
                    last_idle_recovery_at = now
                    persistence_recovery = self._recover_unpersisted_open_positions()
                    if not int((persistence_recovery or {}).get("imported_daemon") or 0):
                        return {
                            "break_even": {
                                "checked": 0, "activated": 0, "errors": [],
                                "skipped": "IDLE_RECOVERY_NO_POSITIONS",
                            },
                            "persistence_recovery": persistence_recovery,
                            "sync": 0,
                            "elapsed_seconds": time.monotonic() - monitor_started,
                            "phase": phase,
                            "idle_fast_path": True,
                        }

                # Primero sincronizamos cierres. Si TP1 acaba de tocar 1R y cerró,
                # el RUNNER puede activar BE+2 en esta misma pasada aunque el precio
                # ya haya retrocedido por debajo de 1R.
                persistence_recovery = self._recover_unpersisted_open_positions()
                sync = self.sync_closed_trades()
                forex_rollover = self._close_forex_positions_for_rollover()
                # Si se cerraron posiciones por rollover, sincronizamos inmediatamente
                # antes de que Break Even intente administrarlas de nuevo.
                if forex_rollover.get("closed"):
                    sync += self.sync_closed_trades()
                break_even = self._monitor_break_even_positions()
                break_even["forex_rollover"] = forex_rollover
                elapsed = time.monotonic() - monitor_started
                self._persist_audit_event(
                    "POSITION_MONITOR",
                    action="POSITION_MONITOR",
                    reason=phase or None,
                    payload={
                        "persistence_recovery": persistence_recovery,
                        "sync": sync,
                        "break_even": break_even,
                        "elapsed_seconds": elapsed,
                        "phase": phase,
                    },
                )
                if reporter is not None:
                    reporter.print_position_monitor(
                        checked=break_even.get("checked", 0),
                        activated=break_even.get("activated", 0),
                        errors=break_even.get("errors") or [],
                        sync=sync,
                        elapsed_seconds=elapsed,
                        phase=phase,
                        runner_updates=break_even.get("runner_updates") or [],
                    )
                elif break_even.get("activated") or break_even.get("runner_updates") or (break_even.get("forex_rollover") or {}).get("closed") or break_even.get("errors") or sync:
                    print({
                        "action": "POSITION_MONITOR",
                        "phase": phase,
                        "checked": break_even.get("checked"),
                        "activated": break_even.get("activated"),
                        "runner_updates": break_even.get("runner_updates") or [],
                        "forex_rollover": break_even.get("forex_rollover") or {},
                        "sync": sync,
                        "errors": break_even.get("errors"),
                        "elapsed_seconds": round(elapsed, 3),
                    })
                monitor_result = {"break_even": break_even, "sync": sync, "elapsed_seconds": elapsed, "phase": phase}

                current_strategy = self._refresh_current_strategy_views()
                monitor_result["current_strategy"] = current_strategy

                now_monotonic = time.monotonic()
                last_visual = float(getattr(self, "_last_visual_audit_persist_monotonic", 0.0) or 0.0)
                visual_interval = max(
                    10.0,
                    float(getattr(self.config, "visual_audit_refresh_seconds", 30.0)),
                )
                persist_visual = (now_monotonic - last_visual) >= visual_interval
                charts = {}
                # El dashboard reconstruye su vista desde el último snapshot DB
                # mientras esta tarea no está vencida. Evita cuatro lecturas de
                # velas por símbolo cada dos segundos.
                if persist_visual:
                    charts = self._dashboard_chart_snapshots()
                    monitor_result["charts"] = charts

                if persist_visual and charts:
                    symbol_writer = getattr(self.repository, "upsert_position_visual_audit", None)
                    trade_writer = getattr(self.repository, "upsert_trade_visual_audit", None)

                    try:
                        owned_open_trades = [
                            trade for trade in (self.repository.open_trades(source=self.config.source) or [])
                            if isinstance(trade, dict) and self._trade_owned_by_current_bot(trade)
                        ]
                    except Exception:
                        owned_open_trades = []

                    market_by_trade_id = {
                        str(row.get("trade_id")): row
                        for row in (break_even.get("positions") or [])
                        if isinstance(row, dict) and row.get("trade_id") is not None
                    }

                    if callable(symbol_writer):
                        for chart_symbol, chart_payload in charts.items():
                            try:
                                symbol_writer(
                                    chart_symbol,
                                    chart_payload,
                                    bot_profile=str(self.config.bot_profile).upper(),
                                    daemon_magic=int(self.config.magic),
                                    source=self.config.source,
                                )
                            except Exception as exc:
                                self._persist_audit_event(
                                    "VISUAL_AUDIT_PERSIST_ERROR",
                                    instrument=chart_symbol,
                                    action="VISUAL_AUDIT_DB_FAILED",
                                    reason=str(exc),
                                )

                    if callable(trade_writer):
                        for trade in owned_open_trades:
                            trade_id = trade.get("id")
                            symbol = str(trade.get("instrument") or "")
                            chart_payload = charts.get(symbol) or {}
                            if not trade_id or not chart_payload:
                                continue

                            details = trade.get("details") if isinstance(trade.get("details"), dict) else {}
                            metadata = details.get("metadata") if isinstance(details.get("metadata"), dict) else {}
                            signal = details.get("signal") if isinstance(details.get("signal"), dict) else {}
                            analysis = details.get("analysis") if isinstance(details.get("analysis"), dict) else {}

                            def _pick(*keys):
                                """Primer valor no nulo entre metadata, señal y análisis."""
                                for source in (metadata, signal, analysis):
                                    if not isinstance(source, dict):
                                        continue
                                    for key in keys:
                                        value = source.get(key)
                                        if value is not None:
                                            return value
                                return None

                            entry_context = {
                                "bot_profile": str(self.config.bot_profile).upper(),
                                "daemon_magic": int(self.config.magic),
                                "trade_id": int(trade_id),
                                "instrument": symbol,
                                "direction": trade.get("direction"),
                                "entry_time": trade.get("entry_time"),
                                "entry_price": trade.get("entry_price"),
                                "stop_loss": trade.get("stop_loss"),
                                "take_profit": trade.get("take_profit"),
                                "planned_rr": trade.get("planned_rr"),
                                "risk_percent": trade.get("risk_percent"),
                                "trade_leg": metadata.get("trade_leg"),
                                "execution_mode": metadata.get("execution_mode"),
                                "strategy_version": trade.get("strategy_version"),
                                "setup_reason": trade.get("setup_reason"),
                                "decision": _pick("confirmation_decision", "decision"),
                                "score": _pick("trade_score", "score", "quality_score"),
                                "grade": _pick("trade_grade", "grade"),
                                "confirmation_percentage": _pick("confirmation_percentage"),
                                "passed": _pick("passed_confirmations", "passed") or [],
                                "missing": _pick("missing_confirmations", "missing") or [],
                                "critical_failures": _pick(
                                    "critical_confirmation_failures",
                                    "critical_failures",
                                ) or [],
                                "divergence_confirmed": bool(_pick(
                                    "divergence_confirmation",
                                    "divergence_confirmed",
                                )),
                                "divergence_type": _pick("divergence_type"),
                                "harmonic_confirmed": bool(_pick("harmonic_confirmed")),
                                "harmonic_pattern": _pick("harmonic_pattern"),
                                "harmonic_score": _pick("harmonic_score"),
                                "chart_pattern_confirmed": bool(_pick("chart_pattern_confirmed")),
                                "chart_pattern_name": _pick("chart_pattern_name"),
                                "chart_pattern_direction": _pick("chart_pattern_direction"),
                                "chart_pattern_strength": _pick("chart_pattern_strength"),
                                "chart_pattern_bonus": _pick("chart_pattern_bonus"),
                                "chart_pattern_conflict": bool(_pick("chart_pattern_conflict")),
                                "chart_pattern_evidence": _pick("chart_pattern_evidence") or {},
                                "chart_pattern_candidates": _pick("chart_pattern_candidates") or [],
                                "chart_pattern_supporting_pattern": _pick("chart_pattern_supporting_pattern"),
                                "chart_pattern_supporting_direction": _pick("chart_pattern_supporting_direction"),
                                "chart_pattern_supporting_strength": _pick("chart_pattern_supporting_strength"),
                                "chart_pattern_supporting_evidence": _pick("chart_pattern_supporting_evidence") or {},
                                "chart_pattern_conflicting_pattern": _pick("chart_pattern_conflicting_pattern"),
                                "chart_pattern_conflicting_direction": _pick("chart_pattern_conflicting_direction"),
                                "chart_pattern_conflicting_strength": _pick("chart_pattern_conflicting_strength"),
                                "chart_pattern_conflicting_evidence": _pick("chart_pattern_conflicting_evidence") or {},
                                "chart_pattern_conflict_level": _pick("chart_pattern_conflict_level"),
                                "chart_pattern_conflict_reason": _pick("chart_pattern_conflict_reason"),
                                "chart_pattern_conflict_strength_delta": _pick("chart_pattern_conflict_strength_delta"),
                                # Snapshot completo e inmutable de todas las confirmaciones
                                # que justificaron la entrada.
                                "confirmation_details": _pick("confirmations") or {},
                                "h1_doji_confirmed": bool(_pick(
                                    "h1_doji_confirmation",
                                    "h1_doji_confirmed",
                                )),
                                "h1_doji_type": _pick("h1_doji_type"),
                                "h1_doji_zone": _pick("h1_doji_zone"),
                                "h1_doji_time": _pick("h1_doji_time"),
                                "h1_trend": _pick("h1_trend"),
                                "structure_break": _pick(
                                    "m15_structure_break_type",
                                    "structure_break",
                                ),
                                "zone": _pick("m15_zone", "zone"),
                            }
                            try:
                                trade_writer(
                                    int(trade_id),
                                    instrument=symbol,
                                    bot_profile=str(self.config.bot_profile).upper(),
                                    daemon_magic=int(self.config.magic),
                                    broker_position_ticket=trade.get("broker_position_ticket"),
                                    entry_chart=chart_payload,
                                    entry_context=entry_context,
                                    latest_chart=chart_payload,
                                    latest_market={
                                        **(market_by_trade_id.get(str(trade_id), {}) or {}),
                                        **({
                                            "current_strategy_view": (getattr(self, "_current_strategy_view_cache", {}) or {}).get(symbol),
                                            "strategy_evaluated_at": ((getattr(self, "_current_strategy_view_cache", {}) or {}).get(symbol) or {}).get("evaluated_at"),
                                        } if (getattr(self, "_current_strategy_view_cache", {}) or {}).get(symbol) else {}),
                                    },
                                    source=self.config.source,
                                )
                            except Exception as exc:
                                self._persist_audit_event(
                                    "TRADE_VISUAL_AUDIT_PERSIST_ERROR",
                                    instrument=symbol,
                                    action="TRADE_VISUAL_AUDIT_DB_FAILED",
                                    reason=str(exc),
                                    payload={"trade_id": trade_id},
                                )

                    self._last_visual_audit_persist_monotonic = now_monotonic

                if self.dashboard_service is not None:
                    self.dashboard_service.monitor_result(monitor_result)
                return monitor_result
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                print({
                    "action": "POSITION_MONITOR_ERROR",
                    "phase": phase,
                    "error": str(exc),
                    "cycle_time": datetime.now(timezone.utc).isoformat(),
                })
                return None
            finally:
                # Avanza desde el instante actual: evita acumulación de llamadas
                # atrasadas cuando el análisis tarda más que el intervalo.
                next_monitor_at = time.monotonic() + monitor_interval

        background_monitor_enabled = bool(
            self.config.background_position_monitor_enabled and max_cycles is None
        )
        monitor_stop = threading.Event()
        monitor_thread = None
        if background_monitor_enabled:
            def background_monitor_loop():
                """Bucle del hilo dedicado a monitorizar posiciones.

                Corre en un hilo aparte para que una lectura lenta de MT5 o de
                SQLite no retrase el escaneo de senales y envejezca las velas
                M5/M1 que dependen de llegar a tiempo.

                Descuenta del intervalo el tiempo ya consumido, de modo que la
                cadencia se mantiene estable, y espera sobre un evento para
                poder detenerse de inmediato al cerrar el daemon.
                """
                while not monitor_stop.is_set():
                    started = time.monotonic()
                    run_position_monitor_if_due(phase="BACKGROUND_MONITOR")
                    remaining = max(0.05, monitor_interval - (time.monotonic() - started))
                    monitor_stop.wait(remaining)

            monitor_thread = threading.Thread(
                target=background_monitor_loop,
                name=f"DaemonBlackFx-Monitor-{str(self.config.bot_profile).upper()}",
                daemon=True,
            )
            monitor_thread.start()

        while max_cycles is None or cycle_number < int(max_cycles):
            if not background_monitor_enabled:
                run_position_monitor_if_due(phase="LOOP_IDLE")

            now = time.monotonic()
            if now >= next_signal_at:
                cycle_number += 1
                cycle_started = datetime.now(timezone.utc)
                started_monotonic = time.monotonic()
                results = []

                try:
                    selected_symbols = self._selected_cycle_symbols(symbols)
                    cycle_symbols = self._forex_due_symbols(selected_symbols)
                    scheduler = dict(getattr(self, "_forex_scheduler_diagnostics", {}) or {})
                    runtime_state = "RUNNING"
                    event_profiles = {
                        "SYNTHETICS", "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP", "GOLD",
                    }
                    profile = str(self.config.bot_profile or "").upper()
                    family_profile = self._canonical_bot_profile(profile)
                    if (
                        (profile.startswith("FOREX") or family_profile in event_profiles)
                        and selected_symbols
                        and not cycle_symbols
                    ):
                        event_timeframe = str(self.config.forex_event_timeframe or "M5").upper()
                        runtime_state = (
                            f"WAITING_NEW_{event_timeframe}_BAR"
                            if int(scheduler.get("candles_available") or 0) > 0
                            else "WAITING_FOREX_DATA"
                        )
                    elif not selected_symbols:
                        runtime_state = "DEGRADED_NO_SYMBOLS"
                    self._persist_audit_event(
                        "DAEMON_CYCLE_START",
                        action="CYCLE_START",
                        cycle_number=cycle_number,
                        payload={
                            "symbols_count": len(cycle_symbols),
                            "configured_symbols_count": len(symbols),
                            "selected_symbols_count": len(selected_symbols),
                            "runtime_state": runtime_state,
                            "forex_scheduler": scheduler,
                        },
                    )
                    if reporter is not None:
                        reporter.print_cycle_start(cycle_number, cycle_started, total_symbols=len(cycle_symbols))
                    if self.dashboard_service is not None:
                        self.dashboard_service.cycle_start(cycle_number, len(cycle_symbols))

                    def before_symbol(**kwargs):
                        """Gancho previo al análisis de cada símbolo.

                        Registra el evento de auditoria y avisa a la consola y
                        al panel. Si el monitor de posiciones NO corre en su
                        propio hilo, aprovecha este punto para ejecutarlo y
                        que las posiciones no queden desatendidas durante un
                        ciclo largo.
                        """
                        if not background_monitor_enabled:
                            run_position_monitor_if_due(phase="BEFORE_SYMBOL")
                        self._persist_audit_event(
                            "SYMBOL_PROCESS_START",
                            instrument=kwargs["symbol"],
                            action="ANALYZING",
                            cycle_number=cycle_number,
                            payload={
                                "index": kwargs["index"],
                                "total": kwargs["total"],
                            },
                        )
                        if reporter is not None:
                            reporter.print_symbol_start(
                                index=kwargs["index"],
                                total=kwargs["total"],
                                symbol=kwargs["symbol"],
                            )
                        if self.dashboard_service is not None:
                            self.dashboard_service.symbol_start(
                                kwargs["symbol"], kwargs["index"], kwargs["total"]
                            )

                    def progress_callback(**kwargs):
                        """Publica el resultado de un símbolo en consola y panel."""
                        if reporter is not None:
                            reporter.print_symbol_result(
                                row=kwargs["result"],
                                index=kwargs["index"],
                                total=kwargs["total"],
                                elapsed_seconds=kwargs["elapsed_seconds"],
                            )
                        if self.dashboard_service is not None:
                            self.dashboard_service.symbol_result(
                                kwargs["result"], kwargs["index"], kwargs["total"], kwargs["elapsed_seconds"]
                            )

                    def after_symbol(**kwargs):
                        """Gancho posterior a cada símbolo.

                        Ejecuta el monitor de posiciones cuando no hay hilo
                        dedicado, intercalando la gestion entre simbolos.
                        """
                        if not background_monitor_enabled:
                            run_position_monitor_if_due(phase="AFTER_SYMBOL")

                    is_cold_start_cycle = cycle_number == 1
                    process_kwargs = {}
                    if is_cold_start_cycle and int(self.config.cold_start_batch_size or 0) > 0:
                        process_kwargs["batch_size"] = int(self.config.cold_start_batch_size)
                        process_kwargs["batch_delay_seconds"] = float(
                            self.config.cold_start_batch_delay_seconds or 0.0
                        )

                    results = self.process_symbols(
                        cycle_symbols,
                        progress_callback=progress_callback,
                        before_symbol=before_symbol,
                        after_symbol=after_symbol,
                        **process_kwargs,
                    )
                    self._commit_forex_processed_symbols(results)

                    cycle_elapsed = time.monotonic() - started_monotonic
                    cold_start_excluded = (
                        is_cold_start_cycle and bool(self.config.cold_start_exclude_from_overrun)
                    )
                    if cold_start_excluded:
                        # El arranque en frío no tiene caché de etapas H1/M15/M5:
                        # su duración es estructuralmente mayor y no representa
                        # una degradación del intervalo. El reloj del siguiente
                        # ciclo arranca al terminar este, no se descuenta de él,
                        # y no se reporta como overrun.
                        next_signal_at = time.monotonic() + signal_interval
                        next_delay = signal_interval
                        overrun = 0.0
                    else:
                        next_signal_at = started_monotonic + signal_interval
                        next_delay = max(0.0, next_signal_at - time.monotonic())
                        overrun = max(0.0, cycle_elapsed - signal_interval)

                    if reporter is not None:
                        reporter.summarize(
                            results,
                            sync=0,
                            cycle_number=cycle_number,
                            elapsed_seconds=cycle_elapsed,
                            interval=signal_interval,
                            next_delay_seconds=next_delay,
                            overrun_seconds=overrun,
                        )
                    else:
                        for row in results:
                            print(row)

                    if self.dashboard_service is not None:
                        self.dashboard_service.cycle_end(cycle_elapsed)

                    # Si el ciclo superó el intervalo, el siguiente ciclo comienza
                    # inmediatamente; nunca se añade una espera extra de 30 segundos.
                    if next_delay <= 0:
                        next_signal_at = time.monotonic()

                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    self._persist_audit_event(
                        "DAEMON_CYCLE_ERROR",
                        action="ERROR",
                        reason=str(exc),
                        cycle_number=cycle_number,
                        payload={"cycle_started": cycle_started.isoformat()},
                    )
                    if reporter is not None:
                        reporter.print_cycle_error(exc, cycle_started)
                    else:
                        print({
                            "action": "DAEMON_CYCLE_ERROR",
                            "error": str(exc),
                            "cycle_time": cycle_started.isoformat(),
                        })
                    next_signal_at = time.monotonic() + signal_interval

                if max_cycles is not None and cycle_number >= int(max_cycles):
                    break

            now = time.monotonic()
            sleep_until = (
                next_signal_at
                if background_monitor_enabled
                else min(next_signal_at, next_monitor_at)
            )
            sleep_seconds = max(0.05, sleep_until - now)
            time.sleep(sleep_seconds)

        monitor_stop.set()
        if monitor_thread is not None:
            monitor_thread.join(timeout=max(1.0, float(monitor_interval)))

    def run_loop(self, symbols, interval_seconds=30):
        """Alias histórico de `run_daemon`, conservado por compatibilidad."""
        return self.run_daemon(symbols, interval_seconds=interval_seconds)

    def sync_closed_trades(self):
        """Reconcilia con el broker las operaciones que ya se cerraron.

        El broker puede cerrar una posicion por stop loss o take profit sin
        que el bot intervenga. Esta sincronizacion detecta esos cierres y
        actualiza el registro local con el resultado real.

        Tras actualizar, exporta el informe SOLO si le corresponde: en modo
        coordinado los workers llevan `auto_export=False` y el coordinador es
        el unico escritor del XLSX, evitando que dos procesos colisionen sobre
        el mismo fichero.

        Returns:
            El numero de operaciones actualizadas, junto con el diagnostico de
            la exportacion.

        Vinculaciones:
        - `database.repository.sync_closed_mt5_trades` hace la reconciliacion.
        - Los resultados cerrados alimentan el entrenamiento de la IA.
        """
        updated = self.repository.sync_closed_mt5_trades(
            self.executor,
            source=self.config.source,
        )
        # v93: workers coordinados tienen auto_export=False; el coordinador es
        # el único escritor XLSX. Respetar la bandera evita colisión openpyxl.
        reporting_config = getattr(self.reporting_service, "config", None)
        auto_export = (
            True
            if reporting_config is None
            else bool(getattr(reporting_config, "auto_export", True))
        )
        if self.reporting_service is not None and auto_export:
            try:
                self.reporting_service.export_now()
            except Exception as exc:
                self._persist_audit_event(
                    "REPORT_EXPORT_ERROR",
                    action="XLSX_EXPORT_FAILED_AFTER_SYNC",
                    reason=str(exc),
                )
        return int(updated or 0)
