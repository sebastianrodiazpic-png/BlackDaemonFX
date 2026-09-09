"""Pipeline SMC completo: de las velas OHLC a los setups confirmados.

Encadena en orden los diez pasos del analisis Smart Money Concepts. Cada paso
ANOTA columnas nuevas sobre el mismo DataFrame, de modo que al final cada
vela lleva todo su contexto estructural.

Orden real del encadenamiento:

    validacion OHLC -> swings -> estructura de mercado -> liquidez ->
    barridos -> CHOCH/BOS -> order blocks -> premium/discount ->
    construccion de setups -> confirmacion M5 -> riesgo/beneficio

`build_setups` es el embudo: exige que SIETE condiciones se cumplan a la vez
y descarta el resto. Lo que sobrevive pasa por el motor de confirmacion M5,
que es quien puntua la calidad de la entrada.

Vinculaciones:
- Consume casi todo `strategy.smc`.
- `config.symbol_policy` restringe la direccion en simbolos como Boom y
  Crash, donde solo tiene sentido operar hacia un lado.
- Lo invoca `strategy.execution.multi_timeframe`, y a traves de el el motor
  en vivo.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import pandas as pd

from config.symbol_policy import get_symbol_direction_policy, normalize_direction
from strategy.orb.new_york_orb import is_orb_gold_symbol
from strategy.smc.swings import detect_swings
from strategy.smc.market_structure import classify_market_structure, get_current_trend
from strategy.smc.liquidity import detect_liquidity_levels
from strategy.smc.liquidity_sweeps import detect_liquidity_sweeps
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.order_blocks import detect_order_blocks
from strategy.smc.premium_discount import calculate_premium_discount
from strategy.smc.entry_confirmation import detect_entry_confirmations
from strategy.smc.confirmation_engine import M5ConfirmationConfig
from strategy.smc.risk_reward import calculate_risk_reward


@dataclass
class PipelineConfig:
    """Todos los parámetros del pipeline SMC en un único objeto reproducible.

    Los valores son EXPLICITOS a proposito: guardando esta configuracion se
    puede reproducir exactamente por que una entrada fue aceptada o
    rechazada, tanto en backtest como en vivo.

    Bloques:
    - Deteccion estructural: `swing_*`, `liquidity_tolerance`,
      `order_block_lookback`, `premium_discount_lookback`, `sweep_lookback`.
    - Confirmacion M5: umbral de score, requisitos obligatorios
      (`require_*`), proporciones minimas de cuerpo y mecha.
    - Confluencias que SUMAN puntos pero no son obligatorias: armonicos,
      patrones chartistas, divergencias RSI, doji H1 en extremos.

    Distincion clave: los `require_*` son VETOS, mientras que los
    `*_bonus_points` solo suman al score. Los patrones chartistas son la
    excepcion, porque ademas pueden RESTAR mediante
    `chart_pattern_secondary_conflict_penalty` cuando existe un patron
    contrario, o bloquear del todo con
    `block_material_chart_pattern_conflict`.

    Vinculaciones:
    - Sus campos de confirmacion se trasladan a
      `strategy.smc.confirmation_engine.M5ConfirmationConfig` dentro de
      `run_trade_pipeline`.
    """

    swing_left: int = 3
    swing_right: int = 3
    liquidity_tolerance: float = 0.0015
    order_block_lookback: int = 20
    premium_discount_lookback: int = 100
    sweep_lookback: int = 100
    max_retest_candles: int = 50
    min_retest_wait_candles: int = 1
    risk_reward_ratio: float = 2.0

    # M5 confirmation engine. These values are deliberately explicit so every
    # backtest/live run can reproduce exactly why an entry was accepted.
    minimum_trade_score: float = 85.0
    require_rejection: bool = True
    require_displacement: bool = True
    require_micro_confirmation: bool = True
    require_momentum: bool = False
    minimum_body_ratio: float = 0.65
    minimum_rejection_wick_ratio: float = 0.30
    displacement_range_multiplier: float = 1.35
    momentum_range_multiplier: float = 1.00
    confirmation_range_lookback: int = 20
    max_ob_touches: int = 1
    confirmation_mode: str = "midpoint"
    max_m5_confirmation_age_candles: int = 2
    require_strong_close: bool = True
    strong_close_fraction: float = 0.30
    harmonic_enabled: bool = True
    harmonic_tolerance: float = 0.10
    harmonic_minimum_score: float = 75.0
    harmonic_bonus_points: float = 10.0
    require_harmonic: bool = False
    adaptive_confirmation_enabled: bool = True
    minimum_confirmation_ratio: float = 0.80
    minimum_viable_trade_score: float = 75.0
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
    # v108: margen mínimo (fracción 0-1) que el patrón alineado debe superar
    # al contrario para no bloquear la entrada por conflicto chartista.
    chart_pattern_conflict_min_margin: float = 0.25
    block_similar_chart_pattern_forces: bool = False
    divergence_enabled: bool = True
    divergence_rsi_period: int = 14
    divergence_lookback_candles: int = 80
    divergence_bonus_points: float = 5.0
    fvg_enabled: bool = True
    fvg_lookback: int = 30
    fvg_max_age_candles: int = 10
    fvg_require_alignment_with_zone: bool = False
    fvg_bonus_points: float = 6.0
    require_fvg: bool = False
    synthetics_killzone_enabled: bool = False
    synthetics_favorable_hour_ranges: tuple = ((13, 15), (17, 18), (22, 24))
    synthetics_killzone_bonus_points: float = 5.0
    require_synthetics_killzone: bool = False
    round_number_enabled: bool = False
    round_number_increment: float = 50.0
    round_number_tolerance_price: float = 2.0
    round_number_bonus_points: float = 4.0
    require_round_number: bool = False
    # v107: modelo "Asian Range + sweep" (solo GOLD). Cuando está activo, el
    # sweep de `build_setups` solo cuenta si el nivel barrido pertenece al
    # rango de consolidación asiático más reciente (no a cualquier pivote
    # genérico). Es un gate MAS ESTRICTO sobre `sweep_ok`, no una confluencia
    # adicional: por eso está desactivado por defecto para no afectar a
    # Forex/Sintéticos/ORB.
    asian_range_sweep_enabled: bool = False
    asian_range_start_hour_utc: int = 22
    asian_range_end_hour_utc: int = 6
    asian_range_lookback_candles: int = 200
    asian_range_tolerance_price: float = 0.0

    # Doji H1 en extremos: confluencia opcional, nunca requisito obligatorio.
    h1_doji_enabled: bool = True
    h1_doji_lookback_candles: int = 100
    h1_doji_max_age_candles: int = 2
    h1_doji_max_body_ratio: float = 0.10
    h1_doji_extreme_fraction: float = 0.15
    h1_doji_min_rejection_wick_ratio: float = 0.35
    h1_doji_bonus_points: float = 5.0


CHECKLIST_COLUMNS = [
    'trend_ok', 'swing_ok', 'liquidity_ok', 'sweep_ok', 'asian_range_ok',
    'structure_break_ok', 'order_block_ok', 'retest_ok',
    'premium_discount_ok', 'confirmation_ok',
]


def _empty_setups() -> pd.DataFrame:
    """DataFrame vacío con el esquema completo de setups.

    Devolverlo en lugar de `None` permite que los consumidores encadenen
    operaciones de pandas sin comprobar nulos.
    """
    columns = [
        'time', 'setup_time', 'break_time', 'setup_type', 'ob_high', 'ob_low',
        'ob_type', 'zone', 'equilibrium', 'trend', 'sweep_time', 'sweep_level',
        'structure_break_type', *CHECKLIST_COLUMNS,
    ]
    return pd.DataFrame(columns=columns)


def _validate_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza y valida las velas antes de analizarlas.

    Trabaja sobre una COPIA. Convierte `time` a UTC, ordena
    cronologicamente, elimina marcas duplicadas y reinicia el indice.

    Ese saneamiento es imprescindible: todos los pasos posteriores usan
    indices posicionales, y un DataFrame desordenado o con duplicados
    produciria estructuras de mercado falsas.

    Raises:
        ValueError: si faltan columnas OHLC o no queda ninguna vela.
    """
    required = ['time', 'open', 'high', 'low', 'close']
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f'Faltan columnas OHLC: {missing}')
    result = df.copy()
    result['time'] = pd.to_datetime(result['time'], utc=True)
    result = result.sort_values('time').drop_duplicates('time').reset_index(drop=True)
    if result.empty:
        raise ValueError('No hay velas para analizar.')
    return result


def _latest_sweep(data: pd.DataFrame, direction: str, break_index: int, lookback: int):
    """Busca el último barrido de liquidez ANTERIOR a la ruptura estructural.

    El orden temporal es lo esencial: la secuencia SMC valida exige que
    primero se barra liquidez y despues se rompa la estructura. Por eso la
    ventana termina en `break_index`, sin incluirlo.

    Args:
        data: velas ya anotadas con las columnas de barrido.
        direction: `long` busca `bullish_sweep`; cualquier otro valor,
            `bearish_sweep`.
        break_index: posicion de la ruptura.
        lookback: cuantas velas mirar hacia atras.

    Returns:
        La fila del barrido mas reciente, o `None` si no hay ninguno.
    """
    column = 'bullish_sweep' if direction == 'long' else 'bearish_sweep'
    start = max(0, break_index - lookback)
    candidates = data.iloc[start:break_index]
    candidates = candidates[candidates[column].fillna(False).astype(bool)]
    if candidates.empty:
        return None
    return candidates.iloc[-1]


def _trend_at(data: pd.DataFrame, break_index: int) -> str:
    """Tendencia vigente en el momento de la ruptura, sin mirar el futuro.

    Recorta el DataFrame hasta `break_index` inclusive antes de clasificar.
    Ese recorte es lo que evita el sesgo de anticipacion: la tendencia se
    evalua con la informacion que existia entonces, no con la posterior.
    """
    return get_current_trend(data.iloc[: break_index + 1])


def _asian_range_at(data: pd.DataFrame, reference_index: int, asian_start_hour: int, asian_end_hour: int, lookback_candles: int) -> tuple[float | None, float | None]:
    """Rango (high, low) de la sesión asiática vigente hasta `reference_index`.

    v107: soporte del modelo "Asian Range + sweep" para GOLD. Busca hacia
    atrás, desde `reference_index`, el bloque continuo de velas más reciente
    cuya hora UTC cae en `[asian_start_hour, asian_end_hour)` (con soporte de
    rango que cruza medianoche, ej. 22-06h). Ese bloque define el rango cuya
    liquidez debe ser barrida para que el sweep cuente como válido.

    Args:
        data: velas con columna `time` (UTC, tz-aware).
        reference_index: posición de referencia (típicamente el índice del
            barrido a validar); no mira hacia el futuro respecto de él.
        asian_start_hour: hora UTC de inicio de la sesión asiática.
        asian_end_hour: hora UTC de fin (puede ser menor que el inicio si
            cruza medianoche, ej. 22 -> 6).
        lookback_candles: cuántas velas hacia atrás se exploran como máximo.

    Returns:
        `(asian_high, asian_low)`, o `(None, None)` si no se encontró un
        bloque asiático completo en la ventana de búsqueda.
    """
    if reference_index <= 0:
        return None, None
    start = max(0, reference_index - max(1, int(lookback_candles)))
    window = data.iloc[start:reference_index]
    if window.empty:
        return None, None

    def _in_asian_hours(hour: int) -> bool:
        if asian_start_hour <= asian_end_hour:
            return asian_start_hour <= hour < asian_end_hour
        return hour >= asian_start_hour or hour < asian_end_hour

    hours = window['time'].dt.hour
    mask = hours.apply(_in_asian_hours)
    asian_candles = window[mask]
    if asian_candles.empty:
        return None, None
    # Se queda solo con el bloque contiguo mas reciente (evita mezclar dos
    # sesiones asiaticas distintas si el lookback abarca varios dias).
    contiguous_index = asian_candles.index[-1]
    block_indices = [contiguous_index]
    for idx in reversed(asian_candles.index[:-1]):
        if idx == block_indices[-1] - 1:
            block_indices.append(idx)
        else:
            break
    block = data.loc[block_indices]
    return float(block['high'].max()), float(block['low'].min())


def build_setups(data: pd.DataFrame, config: PipelineConfig) -> pd.DataFrame:
    """Construye los setups válidos a partir de los order blocks detectados.

    Es el EMBUDO del pipeline. Para cada order block comprueba SIETE
    condiciones y descarta el setup si falla una sola:

    1. `trend_ok`: la tendencia acompana a la direccion.
    2. `swing_ok`: existen swings altos y bajos previos.
    3. `liquidity_ok`: el barrido tiene nivel de liquidez conocido.
    4. `sweep_ok`: hubo barrido antes de la ruptura.
    5. `structure_break_ok`: el BOS/CHOCH va en la direccion correcta.
    6. `order_block_ok`: el order block tiene limites definidos.
    7. `premium_discount_ok`: las compras nacen en descuento y las ventas en
       premium.

    `retest_ok` y `confirmation_ok` salen SIEMPRE en `False`: son etapas
    posteriores que rellena el motor de confirmacion.

    Returns:
        DataFrame de setups ordenado por tiempo y sin duplicados, o el
        esquema vacio de `_empty_setups` si no sobrevive ninguno.
    """
    rows = []
    ob_rows = data[data['ob_type'].notna()].copy()

    for _, ob in ob_rows.iterrows():
        direction = 'long' if ob['ob_type'] == 'bullish' else 'short'
        break_index = int(ob['ob_break_index'])
        if break_index <= 0 or break_index >= len(data):
            continue

        sweep = _latest_sweep(data, direction, break_index, config.sweep_lookback)
        sweep_ok = sweep is not None
        liquidity_ok = bool(sweep_ok and pd.notna(sweep.get('sweep_level')))

        # v107: modelo "Asian Range + sweep" (solo GOLD, desactivado por
        # defecto). Si está activo, el barrido solo es válido cuando el nivel
        # barrido pertenece al rango asiático más reciente respecto a la
        # ruptura, no a cualquier pivote genérico.
        asian_range_ok = True
        if sweep_ok and bool(getattr(config, 'asian_range_sweep_enabled', False)):
            sweep_index = data.index.get_indexer([sweep.name])[0] if sweep.name in data.index else break_index
            asian_high, asian_low = _asian_range_at(
                data, sweep_index,
                int(getattr(config, 'asian_range_start_hour_utc', 22)),
                int(getattr(config, 'asian_range_end_hour_utc', 6)),
                int(getattr(config, 'asian_range_lookback_candles', 200)),
            )
            tolerance = float(getattr(config, 'asian_range_tolerance_price', 0.0))
            sweep_level = float(sweep['sweep_level']) if pd.notna(sweep.get('sweep_level')) else None
            if asian_high is None or asian_low is None or sweep_level is None:
                asian_range_ok = False
            elif direction == 'long':
                # Bullish sweep: barre sell-side liquidity, debe estar cerca del low asiatico.
                asian_range_ok = sweep_level <= asian_low + tolerance
            else:
                # Bearish sweep: barre buy-side liquidity, debe estar cerca del high asiatico.
                asian_range_ok = sweep_level >= asian_high - tolerance
        trend = _trend_at(data, break_index)
        trend_ok = trend == ('BULLISH' if direction == 'long' else 'BEARISH')
        swing_ok = bool(
            data['swing_high'].iloc[: break_index + 1].any()
            and data['swing_low'].iloc[: break_index + 1].any()
        )
        premium_discount_ok = ob['zone'] == ('discount' if direction == 'long' else 'premium')
        structure_break_type = ob.get('ob_break_type')
        allowed_breaks = {'choch_bullish', 'bos_bullish'} if direction == 'long' else {'choch_bearish', 'bos_bearish'}
        structure_break_ok = structure_break_type in allowed_breaks
        order_block_ok = pd.notna(ob.get('ob_high')) and pd.notna(ob.get('ob_low'))

        if not all((trend_ok, swing_ok, liquidity_ok, sweep_ok, asian_range_ok, structure_break_ok, order_block_ok, premium_discount_ok)):
            continue

        rows.append({
            'time': ob['ob_break_time'], 'setup_time': ob['ob_break_time'],
            'break_time': ob['ob_break_time'], 'setup_type': direction,
            'ob_high': float(ob['ob_high']), 'ob_low': float(ob['ob_low']),
            'ob_type': ob['ob_type'], 'zone': ob['zone'],
            'equilibrium': ob.get('equilibrium'), 'trend': trend,
            'sweep_time': sweep['time'] if sweep_ok else pd.NaT,
            'sweep_level': float(sweep['sweep_level']) if sweep_ok and pd.notna(sweep['sweep_level']) else None,
            'structure_break_type': structure_break_type,
            'trend_ok': bool(trend_ok), 'swing_ok': bool(swing_ok),
            'liquidity_ok': bool(liquidity_ok), 'sweep_ok': bool(sweep_ok),
            'asian_range_ok': bool(asian_range_ok),
            'structure_break_ok': bool(structure_break_ok),
            'order_block_ok': bool(order_block_ok), 'retest_ok': False,
            'premium_discount_ok': bool(premium_discount_ok), 'confirmation_ok': False,
        })

    if not rows:
        return _empty_setups()
    return pd.DataFrame(rows).sort_values('setup_time').drop_duplicates(
        ['setup_time', 'ob_high', 'ob_low', 'setup_type']
    ).reset_index(drop=True)


def _filter_by_policy(frame: pd.DataFrame, column: str, allowed_direction: str | None) -> pd.DataFrame:
    """Filtra una columna de dirección respetando la política del símbolo.

    La misma función se usa para ``setup_type`` (long/short) y ``direction``
    (BUY/SELL). Comparar texto directamente contra ``long``/``short`` vaciaba
    las confirmaciones después de convertirlas a BUY/SELL. Normalizamos ambos
    formatos antes de comparar para que la política sea consistente en todas
    las etapas del pipeline.

    Args:
        frame: setups o confirmaciones a filtrar.
        column: `setup_type` o `direction`.
        allowed_direction: unica direccion permitida, o `None` para no
            filtrar.

    Returns:
        El DataFrame filtrado; el original si no hay politica que aplicar.
    """
    if frame is None or frame.empty or not allowed_direction or column not in frame.columns:
        return frame

    expected = normalize_direction(allowed_direction)
    if expected is None:
        return frame.iloc[0:0].copy()

    normalized = frame[column].map(normalize_direction)
    return frame[normalized == expected].copy()


def _is_xauusd_contract(symbol: str) -> bool:
    """True solo para XAUUSD/microXAUUSD; usado para aislar la confluencia
    de niveles de cuarto del resto de instrumentos compartidos por GOLD/ORB."""
    return is_orb_gold_symbol(symbol)


def run_trade_pipeline(
    df: pd.DataFrame,
    config: PipelineConfig | None = None,
    symbol: str | None = None,
) -> dict:
    """Ejecuta la cadena SMC completa. Si symbol es Boom/Crash, aplica la política de dirección del activo.

    Punto de entrada del pipeline. Encadena los diez pasos del analisis y
    devuelve tanto el resultado final como los productos intermedios, lo que
    permite auditar en que etapa se perdio una oportunidad.

    La politica de simbolo se aplica DOS VECES: sobre los setups y de nuevo
    sobre las confirmaciones, porque en el camino la direccion cambia de
    vocabulario (`long`/`short` a `BUY`/`SELL`).

    Args:
        df: velas OHLC con columna `time`.
        config: parametros del pipeline; usa los de fabrica si se omite.
        symbol: instrumento, necesario para aplicar la politica de direccion.

    Returns:
        Dict con las velas anotadas, los setups antes y despues de la
        politica, las confirmaciones y las operaciones con su riesgo
        calculado.

    Raises:
        ValueError: si las velas no superan `_validate_price_data`.
    """
    config = config or PipelineConfig()
    # Los niveles de cuarto (25/50/75/100) son una confluencia especifica del
    # Oro: aunque el worker GOLD comparte universo con ORB (Plata, Petroleo,
    # indices), solo deben evaluarse cuando el simbolo actual es XAUUSD o
    # microXAUUSD. Para el resto de instrumentos se desactivan aqui, sin
    # importar lo que traiga la config del perfil.
    if config.round_number_enabled and symbol and not is_orb_gold_symbol(symbol):
        config = replace(config, round_number_enabled=False, require_round_number=False)
    policy = get_symbol_direction_policy(symbol or '') if symbol else None
    allowed_direction = policy.allowed_direction if policy else None

    data = _validate_price_data(df)
    data = detect_swings(data, left=config.swing_left, right=config.swing_right)
    data = classify_market_structure(data)
    data = detect_liquidity_levels(data, tolerance=config.liquidity_tolerance)
    data = detect_liquidity_sweeps(data)
    data = detect_choch_bos(data)
    data = detect_order_blocks(data, lookback=config.order_block_lookback)
    data = calculate_premium_discount(data, lookback=config.premium_discount_lookback)

    setups_before_policy = build_setups(data, config)
    setups = _filter_by_policy(setups_before_policy, 'setup_type', allowed_direction)

    m5_confirmation_config = M5ConfirmationConfig(
        minimum_trade_score=config.minimum_trade_score,
        require_rejection=config.require_rejection,
        require_displacement=config.require_displacement,
        require_micro_confirmation=config.require_micro_confirmation,
        require_momentum=config.require_momentum,
        minimum_body_ratio=config.minimum_body_ratio,
        minimum_rejection_wick_ratio=config.minimum_rejection_wick_ratio,
        displacement_range_multiplier=config.displacement_range_multiplier,
        momentum_range_multiplier=config.momentum_range_multiplier,
        range_lookback=config.confirmation_range_lookback,
        max_ob_touches=config.max_ob_touches,
        confirmation_mode=config.confirmation_mode,
        max_confirmation_age_candles=config.max_m5_confirmation_age_candles,
        harmonic_enabled=getattr(config, "harmonic_enabled", True),
        harmonic_tolerance=getattr(config, "harmonic_tolerance", 0.10),
        harmonic_minimum_score=getattr(config, "harmonic_minimum_score", 75.0),
        harmonic_bonus_points=getattr(config, "harmonic_bonus_points", 10.0),
        require_harmonic=getattr(config, "require_harmonic", False),
        adaptive_confirmation_enabled=getattr(config, "adaptive_confirmation_enabled", True),
        minimum_confirmation_ratio=getattr(config, "minimum_confirmation_ratio", 0.80),
        minimum_viable_trade_score=getattr(config, "minimum_viable_trade_score", 75.0),
        chart_patterns_enabled=getattr(config, "chart_patterns_enabled", True),
        chart_patterns_lookback=getattr(config, "chart_patterns_lookback", 80),
        chart_patterns_pivot_window=getattr(config, "chart_patterns_pivot_window", 2),
        chart_patterns_price_tolerance=getattr(config, "chart_patterns_price_tolerance", 0.006),
        chart_patterns_volatility_adjusted_tolerance=getattr(config, "chart_patterns_volatility_adjusted_tolerance", True),
        chart_patterns_price_tolerance_range_multiplier=getattr(config, "chart_patterns_price_tolerance_range_multiplier", 1.50),
        chart_patterns_minimum_price_tolerance=getattr(config, "chart_patterns_minimum_price_tolerance", 0.00010),
        chart_patterns_minimum_strength=getattr(config, "chart_patterns_minimum_strength", 0.72),
        chart_patterns_bonus_points=getattr(config, "chart_patterns_bonus_points", 8.0),
        require_chart_pattern=getattr(config, "require_chart_pattern", False),
        chart_pattern_secondary_conflict_penalty=getattr(config, "chart_pattern_secondary_conflict_penalty", 10.0),
        block_material_chart_pattern_conflict=getattr(config, "block_material_chart_pattern_conflict", True),
        chart_pattern_conflict_min_margin=getattr(config, "chart_pattern_conflict_min_margin", 0.25),
        block_similar_chart_pattern_forces=getattr(config, "block_similar_chart_pattern_forces", False),
        divergence_enabled=getattr(config, "divergence_enabled", True),
        divergence_rsi_period=getattr(config, "divergence_rsi_period", 14),
        divergence_lookback_candles=getattr(config, "divergence_lookback_candles", 80),
        divergence_bonus_points=getattr(config, "divergence_bonus_points", 5.0),
        fvg_enabled=getattr(config, "fvg_enabled", True),
        fvg_lookback=getattr(config, "fvg_lookback", 30),
        fvg_max_age_candles=getattr(config, "fvg_max_age_candles", 10),
        fvg_require_alignment_with_zone=getattr(config, "fvg_require_alignment_with_zone", False),
        fvg_bonus_points=getattr(config, "fvg_bonus_points", 6.0),
        require_fvg=getattr(config, "require_fvg", False),
        synthetics_killzone_enabled=getattr(config, "synthetics_killzone_enabled", False),
        synthetics_favorable_hour_ranges=getattr(config, "synthetics_favorable_hour_ranges", ((13, 15), (17, 18), (22, 24))),
        synthetics_killzone_bonus_points=getattr(config, "synthetics_killzone_bonus_points", 5.0),
        require_synthetics_killzone=getattr(config, "require_synthetics_killzone", False),
        round_number_enabled=getattr(config, "round_number_enabled", False),
        round_number_increment=getattr(config, "round_number_increment", 50.0),
        round_number_tolerance_price=getattr(config, "round_number_tolerance_price", 2.0),
        round_number_bonus_points=getattr(config, "round_number_bonus_points", 4.0),
        require_round_number=getattr(config, "require_round_number", False),
    )

    confirmations = detect_entry_confirmations(
        data, setups,
        max_wait_candles=config.max_retest_candles,
        min_wait_candles=config.min_retest_wait_candles,
        confirmation_config=m5_confirmation_config,
    )
    rejected_candidates = list(confirmations.attrs.get("rejected_candidates", []))

    if not confirmations.empty:
        confirmations = calculate_risk_reward(confirmations, risk_reward_ratio=config.risk_reward_ratio)
        confirmations['direction'] = confirmations['setup_type'].str.upper().replace({'LONG': 'BUY', 'SHORT': 'SELL'})
        confirmations = _filter_by_policy(confirmations, 'direction', allowed_direction)
        confirmations['valid'] = confirmations.get('trade_valid', True).astype(bool) & confirmations.get('confirmation_valid', True).astype(bool)
        for column in CHECKLIST_COLUMNS:
            if column not in confirmations.columns:
                confirmations[column] = True
        confirmations['confirmation_ok'] = confirmations.get('confirmation_valid', True).astype(bool)
    else:
        confirmations = pd.DataFrame(columns=['entry_time', 'setup_type', 'direction', 'valid', *CHECKLIST_COLUMNS])

    latest_rejected = rejected_candidates[-1] if rejected_candidates else None
    rejection_reason_counts = {}
    for candidate in rejected_candidates:
        for reason in candidate.get("rejection_reasons", []) or []:
            rejection_reason_counts[reason] = rejection_reason_counts.get(reason, 0) + 1

    policy_diag = None
    if policy:
        policy_diag = {
            'symbol': symbol, 'category': policy.category,
            'allowed_direction': policy.allowed_direction,
            'reason': policy.reason,
            'setups_before_policy': int(len(setups_before_policy)),
            'setups_after_policy': int(len(setups)),
            'confirmations_after_policy': int(len(confirmations)),
        }

    return {
        'data': data, 'setups': setups, 'confirmations': confirmations,
        'config': asdict(config),
        'summary': {
            'candles': int(len(data)),
            'swing_highs': int(data['swing_high'].sum()),
            'swing_lows': int(data['swing_low'].sum()),
            'bullish_sweeps': int(data['bullish_sweep'].sum()),
            'bearish_sweeps': int(data['bearish_sweep'].sum()),
            'bullish_choch': int(data['choch_bullish'].sum()),
            'bearish_choch': int(data['choch_bearish'].sum()),
            'bullish_bos': int(data['bos_bullish'].sum()),
            'bearish_bos': int(data['bos_bearish'].sum()),
            'order_blocks': int(data['ob_type'].notna().sum()),
            'setups': int(len(setups)), 'confirmed_entries': int(len(confirmations)),
            'average_trade_score': None if confirmations.empty or 'trade_score' not in confirmations.columns else round(float(confirmations['trade_score'].mean()), 2),
            'a_or_better_entries': 0 if confirmations.empty or 'trade_grade' not in confirmations.columns else int(confirmations['trade_grade'].isin(['A', 'A+']).sum()),
        },
        'diagnostics': {
            'first_candle_time': data['time'].iloc[0].isoformat(),
            'rejected_m5_candidates': int(len(rejected_candidates)),
            'rejection_reason_counts': rejection_reason_counts,
            'latest_rejected_candidate': latest_rejected,
            'last_candle_time': data['time'].iloc[-1].isoformat(),
            'latest_trend': get_current_trend(data),
            'latest_setup_time': None if setups.empty else pd.to_datetime(setups['setup_time'].iloc[-1], utc=True).isoformat(),
            'latest_setup_type': None if setups.empty else str(setups['setup_type'].iloc[-1]),
            'latest_confirmation_time': None if confirmations.empty else pd.to_datetime(confirmations['entry_time'].iloc[-1], utc=True).isoformat(),
            'latest_confirmation_direction': None if confirmations.empty else str(confirmations['direction'].iloc[-1]),
            'direction_policy': policy_diag,
        },
    }
