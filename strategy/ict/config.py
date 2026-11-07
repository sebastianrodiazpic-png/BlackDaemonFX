"""Configuración para la estrategia institucional ICT (Sabri Malle - AMD & FVG Rejection v2)."""
import os
from dataclasses import dataclass, field

from config.ict_instrument_policy import (
    ICT_5Y_RESCUED_SYNTHETICS,
    ICT_5Y_SYNTH_PRUNED,
    ICT_PHASE1_EXCLUDED,
)
from config.strategy_config import ICT_WR45_PRUNED


@dataclass
class ICTSabriMalleConfig:
    strategy_name: str = "ICT_SABRI_MALLE"
    strategy_version: str = "ict-sabri-malle-v2-fase1"  # v2: sin ventana NY 07-12:30 (no sintéticos) + exclusiones
    macro_timeframe: str = "H4"
    # Velas H4 que se piden para el sesgo macro (EMA 50/100/200). Con 300 la EMA200 (adjust=False) converge con peso
    # residual < 5%; DAEMONBLACKFX_ICT_H4_CANDLES permite medir/ajustar (ver registro, 26-oct-2026).
    macro_h4_candles: int = int(os.getenv("DAEMONBLACKFX_ICT_H4_CANDLES", "300"))
    structure_timeframe: str = "H1"
    entry_timeframe: str = "M15"
    
    # Filtro Horario y Killzones Institucionales (New York Time)
    killzone_filter_enabled: bool = True
    asian_range_start_ny: int = 20  # 20:00 NY
    asian_range_end_ny: int = 0     # 00:00 NY
    # Mejora 3 (26-oct-2026): se retira la hora 02:00 NY (-67,7 R en 5 años, Judas Swing aún en formación) y se opera 03:00-05:00 NY.
    london_kz_start_ny: int = int(os.getenv("DAEMONBLACKFX_ICT_LONDON_START_NY", "3"))  # 03:00 NY
    london_kz_end_ny: int = int(os.getenv("DAEMONBLACKFX_ICT_LONDON_END_NY", "5"))      # 05:00 NY
    ny_kz_start_ny: int = 7         # 07:00 NY
    ny_kz_end_ny: int = 11          # 11:00 NY
    # Replay fiel (365d, sin lookahead): Londres +0.18R/trade (n=238), NY 07-11 -0.16R/trade (n=434).
    # Fase 1 (18-oct-2026): replay fiel 365d, mercados reales NY 07-12 = -0.158R/trade (n=434, negativo
    # en ambas mitades) vs resto +0.179R/trade (n=238, positivo en ambas). Sintéticos no se ven afectados (24/7).
    ny_killzone_enabled: bool = False
    forex_ny_killzone_enabled: bool = False  # NY Killzone desactivada también para Forex
    london_close_reversal_enabled: bool = False  # Ventana 11:00-12:30 NY (horas 11-12 negativas en replay fiel)
    silver_bullet_enabled: bool = True  # Ventanas Silver Bullet restringidas a silver_bullet_hours_ny
    # Ventanas Silver Bullet oficiales de Michael Huddleston: London (03:00 NY) y New York AM (10:00 NY).
    # Configurable por DAEMONBLACKFX_ICT_SB_HOURS_NY (por defecto "3,10").
    silver_bullet_hours_ny: tuple = tuple(
        int(h.strip()) for h in os.getenv("DAEMONBLACKFX_ICT_SB_HOURS_NY", "3,10").split(",") if h.strip()
    )

    # Activos con expectativa negativa en el replay fiel multianual (excluidos solo para ICT)
    excluded_symbols: tuple = ICT_PHASE1_EXCLUDED
    # Poda por acierto <= 45% en el replay fiel (config/strategy_config.py:ICT_WR45_PRUNED) descontando rescatados
    wr_pruned_symbols: tuple = tuple(s for s in ICT_WR45_PRUNED if s not in set(ICT_5Y_RESCUED_SYNTHETICS))
    # Poda multianual 5 años (26-oct-2026)
    synth_5y_pruned_symbols: tuple = ICT_5Y_SYNTH_PRUNED
    
    # Cierre de Mercado y Guardias de Rollover (Forex, Metales, Índices)
    market_closure_filter_enabled: bool = True
    friday_close_cutoff_ny: int = 14  # No abrir órdenes viernes después de 14:00 NY
    weekend_filter_enabled: bool = True
    rollover_guard_enabled: bool = True
    rollover_start_ny_hour: int = 16
    rollover_start_ny_minute: int = 45
    rollover_end_ny_hour: int = 17
    rollover_end_ny_minute: int = 45

    # Detección Estructural y Manipulación (AMD / Judas Swing / OB 5 Estrellas)
    range_lookback: int = 24
    min_atr_factor: float = 0.5
    max_atr_factor: float = 5.0
    min_rejection_wick_ratio: float = 0.35
    synthetics_min_rejection_wick_ratio: float = 0.25
    synthetics_rolling_lookback_bars: int = 8  # Rango fractal dinámico para sintéticos 24/7
    
    # Order Block 5 Estrellas (Sabri Malle Video 9)
    ob_five_star_enabled: bool = True
    ob_lookback_bars: int = 30
    
    # Macro Bias H4 Flexible (Sabri Malle Video 8 EMA 100 / EMA 50-200)
    macro_ema_period: int = 100
    macro_bias_flexible: bool = True
    
    # Ruptura Estructural Estricta (MSS) y FVG Consequent Encroachment
    strict_mss_body_ratio: float = 0.45
    fvg_consequent_encroachment_ratio: float = 0.50
    fvg_consequent_encroachment_entry: bool = True
    fvg_lookback_bars: int = 40
    fibo_discount_premium_filter: bool = True
    # Mejora 1 (26-oct-2026): piso estructural de SL en sintéticos (sl_atr_h1 >= 1.0 evita -244,8 R de stops por ruido M15)
    # y ventana H1 para extremo de barrido en sintéticos.
    synthetics_sweep_lookback_h1_bars: int = int(os.getenv("DAEMONBLACKFX_ICT_SYNTH_SWEEP_H1_BARS", "1"))
    min_sl_atr_h1: float = float(os.getenv("DAEMONBLACKFX_ICT_MIN_SL_ATR_H1", "1.0"))
    # Mejora 2 (26-oct / 28-oct-2026): validación de FVG real de 3 velas y tope de retroceso <= 0.45 R (+363 trades, +37.7 R netos en 5y).
    require_real_fvg_ce: bool = os.getenv("DAEMONBLACKFX_ICT_REQUIRE_REAL_FVG_CE", "0").strip().lower() in ("1", "true", "on")
    max_signed_pullback_r: float = float(os.getenv("DAEMONBLACKFX_ICT_MAX_PULLBACK_R", "0.45"))
    # Mejora 4 (26-oct / 28-oct-2026): especialización direccional en Jump 50/75 (solo BUY) y Step Index / Step Index 500 (solo SELL: +8.2 R salvados).
    directional_asymmetry_filter_enabled: bool = os.getenv("DAEMONBLACKFX_ICT_DIRECTIONAL_ASYMMETRY", "1").strip().lower() not in ("0", "false", "off")
    jump_buy_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_ICT_JUMP_BUY_ONLY", "Jump 50 Index,Jump 75 Index").split(",") if s.strip()
    )
    step_sell_only_symbols: tuple = tuple(
        s.strip() for s in os.getenv("DAEMONBLACKFX_ICT_STEP_SELL_ONLY", "Step Index,Step Index 500").split(",") if s.strip()
    )
    # Mejora 5 (26-oct-2026): filtro de régimen H1 (ADX >= 20 evita -114,2 R en mercados muertos/laterales).
    min_adx_h1: float = float(os.getenv("DAEMONBLACKFX_ICT_MIN_ADX_H1", "20.0"))
    
    # Mejora 9 (30-oct-2026): Lógica Adaptativa Bidireccional para Workers STEP y JUMP
    # Permite compras y ventas en Step Index, Step 500, Jump 50 y Jump 75 garantizando WR > 51.5%
    # - Ventas en Jump: Escudo Anti-Salto (SL >= 1.45 ATR H1, signed_pb <= 0.40) -> WR 55.8% (+14.6 R)
    # - Compras en Step: Ancla de Expansión (ADX H1 >= 28.0, signed_pb <= 0.25) -> WR 52.4% (+6.5 R)
    adaptive_bidirectional_jump_step_enabled: bool = (
        os.getenv("DAEMONBLACKFX_ICT_ADAPTIVE_BIDIRECTIONAL", "1").strip().lower() not in ("0", "false", "off")
    )
    jump_sell_min_sl_atr_h1: float = float(os.getenv("DAEMONBLACKFX_ICT_JUMP_SELL_MIN_SL_ATR", "1.45"))
    jump_sell_max_signed_pb_r: float = float(os.getenv("DAEMONBLACKFX_ICT_JUMP_SELL_MAX_PB", "0.40"))
    step_buy_min_adx_h1: float = float(os.getenv("DAEMONBLACKFX_ICT_STEP_BUY_MIN_ADX", "28.0"))
    step_buy_max_signed_pb_r: float = float(os.getenv("DAEMONBLACKFX_ICT_STEP_BUY_MAX_PB", "0.25"))
    
    # Mejora 7 (27-oct-2026): Entrada Dual Escalonada (Mitigación al 25% y Consequent Encroachment al 50%)
    dual_entry_mitigation_enabled: bool = os.getenv("DAEMONBLACKFX_ICT_DUAL_ENTRY_MITIGATION", "1").strip().lower() not in ("0", "false", "off")
    mitigation_fvg_ratio: float = float(os.getenv("DAEMONBLACKFX_ICT_MITIGATION_FVG_RATIO", "0.25"))
    # Mitigación de Order Blocks (Sabri Malle Video 9): entrada en extremo/borde de OB 5 estrellas y FVG
    ob_mitigation_entry_enabled: bool = os.getenv("DAEMONBLACKFX_ICT_OB_MITIGATION", "1").strip().lower() not in ("0", "false", "off")
    # Mejora 8 (27-oct-2026): Apertura Killzone Tokio-Londres (00:00 - 02:00 NY) para pares Forex con JPY
    tokyo_london_kz_enabled: bool = os.getenv("DAEMONBLACKFX_ICT_TOKYO_LONDON_KZ", "1").strip().lower() not in ("0", "false", "off")
    # Sesión Asiática oficial (Tokyo / Sydney) para pares JPY y AUD (19:00 - 02:00 NY)
    asian_session_jpy_aud_enabled: bool = field(default_factory=lambda: os.getenv("DAEMONBLACKFX_ICT_ASIAN_SESSION_JPY_AUD", "1").strip().lower() not in ("0", "false", "off", "no"))
    asian_kz_hours_ny: tuple = field(default_factory=lambda: tuple(int(h.strip()) for h in os.getenv("DAEMONBLACKFX_ICT_ASIAN_KZ_HOURS_NY", "19,20,21,22,23,0,1,2").split(",") if h.strip()))
    # Manipulación Institucional por barrido de Asian Range y Previous Day High / Low (PDH / PDL)
    asian_range_sweep_enabled: bool = field(default_factory=lambda: os.getenv("DAEMONBLACKFX_ICT_ASIAN_RANGE_SWEEP", "1").strip().lower() not in ("0", "false", "off", "no"))
    pdh_pdl_sweep_enabled: bool = field(default_factory=lambda: os.getenv("DAEMONBLACKFX_ICT_PDH_PDL_SWEEP", "1").strip().lower() not in ("0", "false", "off", "no"))
    # Micro-Stops por Mecha de Rechazo en M15 para Sintéticos (02-nov-2026)
    enable_m15_micro_stop: bool = field(default_factory=lambda: os.getenv("DAEMONBLACKFX_ICT_MICRO_STOP", "1").strip().lower() in ("1", "true", "on"))
    m15_micro_stop_buffer_atr: float = field(default_factory=lambda: float(os.getenv("DAEMONBLACKFX_ICT_MICRO_STOP_BUFFER_ATR", "0.10")))
    m15_micro_stop_min_risk_atr: float = field(default_factory=lambda: float(os.getenv("DAEMONBLACKFX_ICT_MICRO_STOP_MIN_RISK_ATR", "0.20")))
    
    # Gestión Asimétrica Dual y Salidas
    min_rr_planned: float = 1.0
    tp1_rr: float = 1.0
    runner_rr: float = 2.0
    be_trigger_rr: float = 1.0
    be_trigger_rr_fast: float = 1.0  # Break-Even opcional a 1.0R (Video 9)
    leg1_risk_ratio: float = 0.5
    leg2_risk_ratio: float = 0.5
    min_body_ratio: float = 0.40
    
    # Sintéticos (Operativa 24/7 sin Killzones bancarias)
    synthetics_24_7_enabled: bool = True
    synthetics_use_volatility_squeeze: bool = True
    synthetics_squeeze_lookback: int = 20

    # Opción A: SMT Divergence (Smart Money Technique)
    smt_divergence_enabled: bool = True
    smt_score_bonus: float = 15.0
    smt_lookback_bars: int = 16

    # Opción B: Cascada Fractal M5 Timing en Sintéticos
    m5_cascade_timing_enabled: bool = True
    m5_cascade_timeframe: str = "M5"

    # Opción C: Inversion FVG (iFVG) y Balanced Price Range (BPR)
    ifvg_bpr_enabled: bool = True
    ifvg_lookback_bars: int = 24
    ifvg_bpr_require_gbdt_filter: bool = True
    ifvg_bpr_atr_sl_buffer: float = field(default_factory=lambda: float(os.getenv("DAEMONBLACKFX_ICT_IFVG_ATR_SL_BUFFER", "0.25")))
    scan_displacement_leg_fvg: bool = field(default_factory=lambda: os.getenv("DAEMONBLACKFX_ICT_SCAN_DISPLACEMENT_FVG", "1").strip().lower() not in ("0", "false", "off"))

    # Paso 1.1: Umbral calibrado GBDT LightGBM y activos ACTIVE (26-oct-2026: actualizados con auditoría 5 años)
    gbdt_min_probability: float = 0.55
    active_22_symbols: tuple = (
        "Crash 900 Index", "Volatility 50 (1s) Index", "Boom 900 Index",
        "Volatility 25 Index", "Jump 25 Index", "Step Index 200",
        "US Oil", "Volatility 150 (1s) Index", "Volatility 75 Index",
        "Volatility 75 (1s) Index", "Volatility 15 Index", "Jump 75 Index",
        "Jump 10 Index", "Step Index 500", "Volatility 250 (1s) Index",
        "Volatility 90 Index", "Step Index 400", "Boom 500 Index",
        "Volatility 5 Index", "High Frequency Vol 100 Index", "Volatility 10 Index",
        "US Tech 100", "Volatility 100 Index", "CHFJPY", "GBPJPY", "XAUUSD",
    )

    def __post_init__(self):
        raw_sb = os.getenv("DAEMONBLACKFX_ICT_SB_HOURS_NY", "")
        if raw_sb:
            self.silver_bullet_hours_ny = tuple(int(h.strip()) for h in raw_sb.split(",") if h.strip())
        raw_dual = os.getenv("DAEMONBLACKFX_ICT_DUAL_ENTRY_MITIGATION", "")
        if raw_dual:
            self.dual_entry_mitigation_enabled = raw_dual.strip().lower() not in ("0", "false", "off")
        raw_ob_mit = os.getenv("DAEMONBLACKFX_ICT_OB_MITIGATION", "")
        if raw_ob_mit:
            self.ob_mitigation_entry_enabled = raw_ob_mit.strip().lower() not in ("0", "false", "off")
        raw_mit_ratio = os.getenv("DAEMONBLACKFX_ICT_MITIGATION_FVG_RATIO", "")
        if raw_mit_ratio:
            try:
                self.mitigation_fvg_ratio = float(raw_mit_ratio.strip())
            except ValueError:
                pass
        raw_mstop = os.getenv("DAEMONBLACKFX_ICT_MICRO_STOP", "")
        if raw_mstop:
            self.enable_m15_micro_stop = raw_mstop.strip().lower() in ("1", "true", "on")
        raw_mstop_buf = os.getenv("DAEMONBLACKFX_ICT_MICRO_STOP_BUFFER_ATR", "")
        if raw_mstop_buf:
            try:
                self.m15_micro_stop_buffer_atr = float(raw_mstop_buf.strip())
            except ValueError:
                pass
        raw_mstop_floor = os.getenv("DAEMONBLACKFX_ICT_MICRO_STOP_MIN_RISK_ATR", "")
        if raw_mstop_floor:
            try:
                self.m15_micro_stop_min_risk_atr = float(raw_mstop_floor.strip())
            except ValueError:
                pass
        raw_asian_jpy_aud = os.getenv("DAEMONBLACKFX_ICT_ASIAN_SESSION_JPY_AUD", "")
        if raw_asian_jpy_aud:
            self.asian_session_jpy_aud_enabled = raw_asian_jpy_aud.strip().lower() not in ("0", "false", "off", "no")
        raw_asian_kz_hours = os.getenv("DAEMONBLACKFX_ICT_ASIAN_KZ_HOURS_NY", "")
        if raw_asian_kz_hours:
            self.asian_kz_hours_ny = tuple(int(h.strip()) for h in raw_asian_kz_hours.split(",") if h.strip())
        raw_ar_sweep = os.getenv("DAEMONBLACKFX_ICT_ASIAN_RANGE_SWEEP", "")
        if raw_ar_sweep:
            self.asian_range_sweep_enabled = raw_ar_sweep.strip().lower() not in ("0", "false", "off", "no")
        raw_pdh_sweep = os.getenv("DAEMONBLACKFX_ICT_PDH_PDL_SWEEP", "")
        if raw_pdh_sweep:
            self.pdh_pdl_sweep_enabled = raw_pdh_sweep.strip().lower() not in ("0", "false", "off", "no")
