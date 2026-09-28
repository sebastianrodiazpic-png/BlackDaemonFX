"""Estrategia Opening Range Breakout (ORB) de la sesión cash de Nueva York.

Estrategia INDEPENDIENTE del pipeline SMC: no usa order blocks ni confirmacion
M5 de `strategy.smc`. Se apoya en un concepto distinto — el rango de apertura
de Nueva York — y produce su propio dict de senal.

Idea: el rango que el precio marca en los primeros 15 minutos de la sesion
cash (09:30-09:45 NY) delimita el equilibrio inicial del dia. Romperlo con
cierre M5 confirmado, y volver a superarlo tras un retesteo, indica
continuacion direccional.

Alcance restringido a proposito: solo opera contratos concretos y conocidos
(Oro, Plata, Petroleo, indices US), porque el concepto de sesion cash de
Nueva York carece de sentido en sinteticos que cotizan 24/7.

Vinculaciones:
- La orquesta `strategy.execution.live_trading_engine`, que la invoca para
  los simbolos elegibles.
- Depende de un `data_provider` con `get_candles` y `get_current_tick`,
  normalmente el proveedor MT5 de `brokers/`.
- El motor pasa sus senales por `strategy.ai.meta_labeling` igual que las
  demas estrategias, con su propio modelo por worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
import math
import re

import pandas as pd

from strategy.smc.volume_utils import select_volume_column
from strategy.orb.asset_rules import (
    ORB_STRATEGY_VERSION, default_asset_profiles, check_range_amplitude,
    audit_volume_confirmation, evaluate_retest_quality,
)


NEW_YORK = ZoneInfo("America/New_York")


def _norm_symbol(symbol: str) -> str:
    """Reduce el símbolo a minúsculas y sólo caracteres alfanuméricos.

    Neutraliza las variantes de nomenclatura entre brokers (`US-30`, `US 30`,
    `us30`) para poder compararlas con los alias conocidos.
    """
    return re.sub(r"[^a-z0-9]", "", str(symbol or "").lower())


def classify_orb_market(symbol: str) -> str | None:
    """Clasifica únicamente los contratos ORB autorizados.

    Importante: no usamos el término genérico ``gold`` porque Deriv publica
    productos distintos (Gold BB, Gold MACO, etc.) que no son XAUUSD y algunos
    tienen trading deshabilitado.

    El ORDEN importa: `xauusdmicro` se evalua antes que `xauusd`, porque la
    coincidencia por subcadena haria que el micro fuese absorbido por la
    familia estandar.

    Args:
        symbol: nombre del simbolo tal y como lo publica el broker.

    Returns:
        `XAUUSD`, `MICRO_XAUUSD`, `XAGUSD`, `MICRO_XAGUSD`, `US_OIL`,
        `WALL_STREET_30`, `US_TECH_100`, `US_500`, o `None` si el simbolo no
        es apto para ORB.
    """
    name = _norm_symbol(symbol)

    # Oro: nombres concretos observados/soportados. Evaluar micro primero evita
    # que XAUUSDmicro sea absorbido por la familia XAUUSD estándar.
    if name in {"xauusdmicro", "microxauusd"}:
        return "MICRO_XAUUSD"
    if name in {"xauusd", "gold"}:
        return "XAUUSD"

    # Plata: mismo patron que el Oro, micro evaluado primero.
    if name in {"xagusdmicro", "microxagusd"}:
        return "MICRO_XAGUSD"
    if name in {"xagusd", "silver"}:
        return "XAGUSD"

    if name == "btcusd":
        return "BTCUSD"

    if name == "cl":
        return "US_OIL"

    aliases = {
        "WALL_STREET_30": ("wallstreet30", "us30", "dj30", "dow30", "dowjones30", "ws30"),
        "US_TECH_100": ("ustech100", "ustec100", "ustec", "nasdaq100", "nas100", "ndx100"),
        "US_500": ("usa500", "us500", "sp500", "spx500", "sandp500"),
        "US_OIL": ("usoil", "uso", "wti", "wtioil", "crudeoil", "brent", "brentoil"),
    }
    for market, tokens in aliases.items():
        if any(token == name or token in name for token in tokens):
            return market
    return None


def is_orb_eligible_symbol(symbol: str) -> bool:
    """Indica si el símbolo puede operarse con ORB.

    Es el filtro que aplica el motor antes de invocar la estrategia.
    """
    return classify_orb_market(symbol) is not None


def is_orb_gold_symbol(symbol: str) -> bool:
    """True únicamente para las dos variantes de Oro autorizadas por ORB."""
    return classify_orb_market(symbol) in {"XAUUSD", "MICRO_XAUUSD"}


def is_orb_silver_symbol(symbol: str) -> bool:
    """True únicamente para las dos variantes de Plata autorizadas por ORB."""
    return classify_orb_market(symbol) in {"XAGUSD", "MICRO_XAGUSD"}


def orb_session_asset(symbol: str) -> str:
    """Silver contracts share an ORB session; other instruments keep their identity."""
    return "XAGUSD" if is_orb_silver_symbol(symbol) else str(symbol)


def is_orb_oil_symbol(symbol: str) -> bool:
    """True únicamente para el contrato de Petróleo autorizado por ORB."""
    return classify_orb_market(symbol) == "US_OIL"


def is_orb_commodity_symbol(symbol: str) -> bool:
    """True para cualquier materia prima autorizada por ORB (oro/plata/petróleo)."""
    return (
        is_orb_gold_symbol(symbol)
        or is_orb_silver_symbol(symbol)
        or is_orb_oil_symbol(symbol)
    )


def is_orb_index_symbol(symbol: str) -> bool:
    """True para cualquiera de los tres índices US autorizados por ORB."""
    return classify_orb_market(symbol) in {"WALL_STREET_30", "US_TECH_100", "US_500"}


def score_orb_gold_contract_candidate(
    *,
    target_leg_risk: float,
    actual_leg_risk: float,
    spread_cost: float,
    margin_required: float,
    free_margin: float,
) -> dict:
    """Puntúa la calidad de ejecución del contrato de Oro.

    Menor score = mejor contrato para representar la MISMA oportunidad ORB.
    Priorizamos:
      1) precisión del riesgo de 0.5% después del volume_step;
      2) coste de spread respecto del riesgo de esa pierna;
      3) margen consumido respecto del margen libre.

    La señal técnica no gana puntos por ser XAUUSD o microXAUUSD: la elección es
    puramente de calidad de ejecución/riesgo para no duplicar exposición.
    """
    target = max(0.0, float(target_leg_risk))
    actual = max(0.0, float(actual_leg_risk))
    spread = max(0.0, float(spread_cost))
    margin = max(0.0, float(margin_required))
    free = max(0.0, float(free_margin))

    risk_error_ratio = abs(actual - target) / target if target > 0 else math.inf
    spread_risk_ratio = spread / target if target > 0 else math.inf
    margin_free_ratio = margin / free if free > 0 else math.inf

    # El error de sizing domina. Spread y margen actúan como desempate económico.
    score = (
        risk_error_ratio * 1000.0
        + spread_risk_ratio * 100.0
        + margin_free_ratio * 10.0
    )
    return {
        "score": float(score),
        "risk_error_ratio": float(risk_error_ratio),
        "spread_risk_ratio": float(spread_risk_ratio),
        "margin_free_ratio": float(margin_free_ratio),
        "target_leg_risk": target,
        "actual_leg_risk": actual,
        "spread_cost": spread,
        "margin_required": margin,
        "free_margin": free,
    }


def discover_orb_symbols(data_provider) -> list[str]:
    """Descubre únicamente contratos ORB operables en la cuenta MT5 actual.

    Los símbolos con ``trade_mode == 0`` se excluyen antes del preflight para
    que productos Deriv no utilizados (por ejemplo Gold BB/MACO) no bloqueen
    todo el arranque del daemon.
    """
    terms = (
        "XAUUSD",
        "BTCUSD",
        "US30",
        "NAS100",
        "XAGUSD",
        "Silver",
        "US Oil",
        "USOIL",
        "WTI",
        "Crude Oil",
        "Brent",
        "Wall Street",
        "US Tech",
        "USTEC",
        "NASDAQ",
        "US500",
        "US 500",
        "SP500",
        "SPX500",
        "S&P 500",
        "SandP500",
        "US SP 500",
    )
    found = set()
    get_info = getattr(data_provider, "get_symbol_info", None)

    for term in terms:
        try:
            candidates = data_provider.search_symbols(term)
        except Exception:
            continue

        for symbol in candidates:
            if not is_orb_eligible_symbol(symbol):
                continue

            # Cuando el proveedor expone trade_mode, 0 corresponde a
            # SYMBOL_TRADE_MODE_DISABLED en MetaTrader5.
            if callable(get_info):
                try:
                    info = get_info(symbol) or {}
                    trade_mode = info.get("trade_mode")
                    if trade_mode is not None and int(trade_mode) == 0:
                        continue
                except Exception:
                    # Si no podemos validar el contrato, no lo incorporamos
                    # automáticamente al universo de ejecución.
                    continue

            found.add(str(symbol))

    return sorted(found)


@dataclass
class ORBConfig:
    """Parámetros de la sesión, los filtros y la gestión de riesgo del ORB.

    Los valores por defecto describen la sesion cash estandar de Nueva York:
    rango 09:30-09:45, operativa hasta las 16:00, analisis en M5.

    Filtros de contexto activables: retesteo obligatorio, alineacion con el
    VWAP de sesion y con el POC del perfil de volumen. Los tres suman
    exigencia y reducen el numero de senales.

    `stop_mode` en `MIDPOINT` (v61) coloca el stop en el 50% del rango de
    apertura en lugar de en el borde opuesto, acortando el riesgo.

    `one_signal_per_session` evita reentrar el mismo dia tras una ruptura ya
    aprovechada. Ahora SI se aplica: la estrategia recuerda, por simbolo y
    fecha NY, la vela de ruptura de la primera señal confirmada del dia y
    bloquea cualquier señal posterior basada en OTRA ruptura ese mismo dia.

    `require_breakout_volume_confirmation` exige que la vela de ruptura
    tenga volumen por encima del promedio reciente, evitando operar rupturas
    "débiles" sin participación real (causa habitual de falsos breakouts).

    Los perfiles controlan modos, buffer ATR y volumen. El rango amplio
    restringe Momentum; el umbral critico cancela la sesion.
    """

    asset_profiles: dict = field(default_factory=default_asset_profiles)
    enabled: bool = True
    timezone_name: str = "America/New_York"
    opening_hour: int = 9
    opening_minute: int = 30
    opening_range_minutes: int = 15
    session_close_hour: int = 16
    session_close_minute: int = 0
    timeframe: str = "M5"
    # La estrategia sólo necesita contexto previo para ATR/volumen y las velas
    # de la sesión vigente. 350 M5 cubren holgadamente ese contrato y evitan
    # descargar 1000 barras en cada evaluación del worker ORB.
    candle_count: int = 350
    breakout_buffer_fraction: float = 0.0
    # Buffer mínimo adaptativo para no considerar ruptura un cierre de apenas
    # un tick fuera del rango. Se expresa como fracción del ATR M5 previo.
    breakout_atr_buffer_fraction: float = 0.05
    # Una ruptura puede retestear el borde durante las siguientes N velas M5.
    # La ventana sigue siendo corta y cerrada para no perseguir señales viejas.
    retest_max_candles: int = 3
    require_retest: bool = True
    momentum_enabled: bool = True
    momentum_min_body_ratio: float = 0.65
    momentum_min_displacement_atr: float = 0.15
    momentum_max_extension_atr: float = 0.50
    require_vwap_alignment: bool = True
    require_poc_alignment: bool = True
    # v109: cuando VWAP y POC estan ambos activos, si esto es False basta con
    # que UNO de los dos este alineado con el retest (no se exigen ambos a la
    # vez). Ver el uso en la evaluacion de retest para el detalle.
    vwap_poc_require_both: bool = False
    poc_bins: int = 24
    target_rr: float = 2.0
    stop_mode: str = "MIDPOINT"  # v61: protección estructural al 50% del ORB
    stop_buffer_fraction: float = 0.0
    one_signal_per_session: bool = True
    require_breakout_volume_confirmation: bool = True
    breakout_volume_lookback: int = 20
    breakout_volume_multiplier: float = 1.2
    require_max_opening_range_atr: bool = True
    opening_range_atr_period: int = 14
    max_opening_range_atr_multiple: float = 1.5
    # v107: confluencia de niveles de cuarto ($25/$50/$75/$100), aplicada
    # SOLO a XAUUSD/microXAUUSD (ver `is_orb_gold_symbol`). Para el resto de
    # mercados ORB (US30/US_TECH_100/US_500) esta confluencia no aplica.
    gold_quarter_level_enabled: bool = False
    gold_quarter_level_increment: float = 25.0
    gold_quarter_level_tolerance_price: float = 2.0
    require_gold_quarter_level: bool = False


class NewYorkORBStrategy:
    """Opening Range Breakout para la sesión cash de Nueva York.

    - Rango: 09:30 <= NY < 09:45.
    - Rupturas: desde 09:45 hasta antes de 16:00 NY.
    - Ruptura M5 con retesteo o alternativa de momentum controlada.
    - El retesteo admite max(2 * spread, 0.10 * ATR M5) y cierre fuera del rango.
    - VWAP de sesión y POC aproximado por perfil de volumen se usan como filtros de contexto.
    """

    def __init__(self, data_provider, config: ORBConfig | None = None):
        """Enlaza la estrategia con su proveedor de datos y su configuración.

        Args:
            data_provider: objeto con `get_candles` y `get_current_tick`.
            config: parametros de sesion y filtros; usa los de fabrica si se
                omite.
        """
        self.data_provider = data_provider
        self.config = config or ORBConfig()
        self.tz = ZoneInfo(self.config.timezone_name)
        # Memoria de "una señal por sesión": sólo se actualiza mediante
        # `mark_signal_used`, después de un fill confirmado. El analizador no
        # consume la sesión por construir una candidata que luego puede ser
        # rechazada por HTF, exposición, riesgo o MT5.
        self._session_signal_memory: dict[str, tuple[str, str]] = {}
        self._frozen_atr_sessions = {}

    def mark_signal_used(self, symbol: str, session_date: str, breakout_key: str) -> None:
        """Marca una tesis ORB como utilizada únicamente tras ejecución real."""
        if not (is_orb_silver_symbol(symbol) or bool(getattr(self.config, "one_signal_per_session", True))):
            return
        if session_date and breakout_key:
            self._session_signal_memory[orb_session_asset(symbol)] = (
                str(session_date), str(breakout_key)
            )

    def _session_bounds(self, now_utc: datetime):
        """Calcula los hitos horarios de la sesión para el día en curso.

        Todo el calculo se hace en hora de Nueva York para que los cambios de
        horario de verano no desplacen la sesion.

        Args:
            now_utc: instante actual, con o sin zona horaria; se asume UTC si
                viene desnudo.

        Returns:
            Tupla `(ahora_ny, apertura, fin_del_rango, cierre)` como
            `pd.Timestamp` con zona.
        """
        now_utc = pd.Timestamp(now_utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.tz_localize("UTC")
        else:
            now_utc = now_utc.tz_convert("UTC")
        now_ny = now_utc.tz_convert(self.tz)
        d = now_ny.date()
        open_ny = pd.Timestamp(datetime.combine(d, time(self.config.opening_hour, self.config.opening_minute)), tz=self.tz)
        range_end_ny = open_ny + pd.Timedelta(minutes=int(self.config.opening_range_minutes))
        close_ny = pd.Timestamp(datetime.combine(d, time(self.config.session_close_hour, self.config.session_close_minute)), tz=self.tz)
        return now_ny, open_ny, range_end_ny, close_ny

    @staticmethod
    def _volume_column(df: pd.DataFrame) -> pd.Series:
        """Elige la mejor columna de volumen disponible en las velas.

        Delegado a `strategy.smc.volume_utils.select_volume_column` (extraído
        para que `strategy.smc.volume_confirmation` reutilice la misma
        lógica sin duplicar código). Se conserva este método como alias por
        compatibilidad con el resto de esta clase.
        """
        return select_volume_column(df)

    @staticmethod
    def _session_vwap(df: pd.DataFrame) -> float | None:
        """Precio medio ponderado por volumen de la sesión.

        Usa el precio tipico `(high + low + close) / 3` de cada vela. Sirve
        de filtro direccional: se compra por encima del VWAP y se vende por
        debajo.

        Si el volumen total es cero recurre a la media aritmetica del precio
        tipico, para devolver algo utilizable en vez de `None`.

        Returns:
            El VWAP, o `None` si no hay velas o el resultado no es finito.
        """
        if df.empty:
            return None
        volume = NewYorkORBStrategy._volume_column(df)
        typical = (
            pd.to_numeric(df["high"], errors="coerce")
            + pd.to_numeric(df["low"], errors="coerce")
            + pd.to_numeric(df["close"], errors="coerce")
        ) / 3.0
        denom = float(volume.sum())
        if denom <= 0:
            return float(typical.mean()) if typical.notna().any() else None
        value = float((typical * volume).sum() / denom)
        return value if math.isfinite(value) else None

    @staticmethod
    def _session_poc(df: pd.DataFrame, bins: int = 24) -> float | None:
        """Point of Control: precio donde se concentró más volumen.

        Aproxima el perfil de volumen dividiendo el recorrido de la sesion en
        `bins` franjas y asignando a cada vela su volumen completo en la
        franja de su precio tipico. Es una simplificacion: un perfil exacto
        repartiria el volumen entre todas las franjas que la vela atraviesa.

        Devuelve el CENTRO de la franja mas negociada, no un precio real
        operado. Se usa como zona de referencia, no como nivel exacto.

        Args:
            df: velas de la sesion.
            bins: numero de franjas; se fuerza un minimo de 4.

        Returns:
            El precio del POC, o `None` si no hay datos utilizables.
        """
        if df.empty:
            return None
        low = float(pd.to_numeric(df["low"], errors="coerce").min())
        high = float(pd.to_numeric(df["high"], errors="coerce").max())
        if not (math.isfinite(low) and math.isfinite(high)):
            return None
        if high <= low:
            return float(pd.to_numeric(df["close"], errors="coerce").iloc[-1])

        bins = max(4, int(bins))
        width = (high - low) / bins
        volume = NewYorkORBStrategy._volume_column(df)
        typical = (
            pd.to_numeric(df["high"], errors="coerce")
            + pd.to_numeric(df["low"], errors="coerce")
            + pd.to_numeric(df["close"], errors="coerce")
        ) / 3.0
        bucket_volume = [0.0] * bins
        for price, vol in zip(typical.tolist(), volume.tolist()):
            if not (math.isfinite(float(price)) and math.isfinite(float(vol))):
                continue
            idx = min(bins - 1, max(0, int((float(price) - low) / width)))
            bucket_volume[idx] += max(0.0, float(vol))
        idx = max(range(bins), key=lambda i: bucket_volume[i])
        return low + (idx + 0.5) * width

    @staticmethod
    def _average_true_range(df: pd.DataFrame, period: int = 14) -> float | None:
        """ATR simple sobre las velas recibidas (sin suavizado de Wilder).

        Se usa solo como referencia de amplitud típica reciente para filtrar
        rangos de apertura anormalmente anchos, no como stop.

        Returns:
            El ATR, o `None` si no hay suficientes velas.
        """
        if df.empty or len(df) < 2:
            return None
        high = pd.to_numeric(df["high"], errors="coerce")
        low = pd.to_numeric(df["low"], errors="coerce")
        close = pd.to_numeric(df["close"], errors="coerce")
        prev_close = close.shift(1)
        true_range = pd.concat([
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        window = true_range.dropna().tail(max(1, int(period)))
        if window.empty:
            return None
        value = float(window.mean())
        return value if math.isfinite(value) and value > 0 else None

    @staticmethod
    def _breakout_volume_confirmed(
        df: pd.DataFrame,
        breakout_time,
        lookback: int = 20,
        multiplier: float = 1.2,
    ) -> tuple[bool | None, float | None, float | None]:
        """Compara el volumen de la vela de ruptura contra el promedio reciente.

        Evita operar rupturas "de baja convicción": sin participación real,
        el breakout es más propenso a ser una trampa de liquidez que
        continuación genuina.

        Args:
            df: velas de la sesión ya ordenadas por tiempo.
            breakout_time: timestamp de la vela de ruptura.
            lookback: cuántas velas previas usar de referencia.
            multiplier: umbral mínimo (volumen_ruptura >= promedio * multiplier).

        Returns:
            Tupla `(confirmado, volumen_ruptura, promedio_referencia)`.
            `confirmado` es `None` cuando no hay volumen fiable disponible
            (no penaliza al desconocer el dato).
        """
        # Unit weights used by VWAP/POC are not evidence of breakout volume.
        from strategy.smc.volume_utils import has_reliable_volume
        df = df[df["time"] <= breakout_time]
        if not has_reliable_volume(df):
            return None, None, None
        source = NewYorkORBStrategy._volume_source(df)
        if source is None:
            return None, None, None
        volume = pd.to_numeric(df[source], errors="coerce")
        if float(volume.sum()) <= 0:
            return None, None, None
        prior = df[df["time"] < breakout_time]
        reference = volume.loc[prior.index].tail(max(1, int(lookback)))
        if reference.empty:
            return None, None, None
        breakout_rows = df[df["time"] == breakout_time]
        if breakout_rows.empty:
            return None, None, None
        breakout_volume = float(volume.loc[breakout_rows.index[-1]])
        avg_volume = float(reference.mean())
        if not math.isfinite(breakout_volume) or not math.isfinite(avg_volume) or breakout_volume < 0 or reference.isna().any() or (reference < 0).any():
            return None, None, None
        if avg_volume <= 0:
            return None, breakout_volume, avg_volume
        confirmed = breakout_volume >= avg_volume * max(0.0, float(multiplier))
        return bool(confirmed), breakout_volume, avg_volume

    @staticmethod
    def _volume_source(df):
        for name in ("real_volume", "tick_volume", "volume"):
            if name in df and pd.to_numeric(df[name], errors="coerce").fillna(0).sum() > 0:
                return name
        return None

    def _prepare_candles(self, symbol: str, now_utc: datetime) -> pd.DataFrame:
        """Descarga las velas y descarta las que aún no han cerrado.

        FILTRO ANTI-REPINTADO, el punto mas delicado del metodo: solo
        conserva velas cuyo instante de cierre (`time` + duracion) ya ha
        pasado. Sin el, la estrategia decidiria sobre la vela en formacion y
        el backtest arrojaria resultados imposibles de reproducir en vivo.

        Anade la columna `time_ny` con la hora local de Nueva York.

        Returns:
            DataFrame ordenado por tiempo, con indice reiniciado.

        Raises:
            ValueError: si las velas no traen columna `time`.
        """
        df = self.data_provider.get_candles(symbol, self.config.timeframe, count=int(self.config.candle_count)).copy()
        if "time" not in df.columns:
            raise ValueError(f"ORB requiere columna time en las velas {self.config.timeframe}")
        df["time"] = pd.to_datetime(df["time"], utc=True)
        # Sólo velas cerradas. v61 usa M5 para breakout/retest.
        tf = str(self.config.timeframe or "M5").upper()
        timeframe_minutes = 5 if tf == "M5" else 1
        now_ts = pd.Timestamp(now_utc)
        if now_ts.tzinfo is None:
            now_ts = now_ts.tz_localize("UTC")
        else:
            now_ts = now_ts.tz_convert("UTC")
        df = df[(df["time"] + pd.Timedelta(minutes=timeframe_minutes)) <= now_ts].copy()
        df["time_ny"] = df["time"].dt.tz_convert(self.tz)
        return df.sort_values("time").reset_index(drop=True)

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        """Evalúa un símbolo y devuelve la señal ORB, válida o no.

        Es el PUNTO DE ENTRADA de la estrategia. Secuencia:

        1. Comprueba que el simbolo sea apto y la estrategia este activa.
        2. Calcula los hitos de la sesion y descarga velas cerradas.
        3. Delimita el rango de apertura (maximo y minimo de 09:30-09:45).
        4. Busca una ruptura con cierre M5 fuera del rango.
        5. Exige el retesteo del borde roto si la configuracion lo pide.
        6. Aplica los filtros de VWAP y POC.
        7. Calcula stop y objetivo segun `stop_mode` y `target_rr`.

        SIEMPRE devuelve un dict, nunca lanza por falta de senal: cuando no
        hay entrada, `valid` es `False` y `action`/`reason` explican en que
        paso se detuvo. Eso hace que el motor pueda registrar el motivo.

        Args:
            symbol: instrumento a evaluar.
            now_utc: instante de referencia; si se omite se toma del tick
                actual. Pasarlo explicitamente es lo que permite reproducir
                el analisis en backtest.

        Returns:
            Dict de senal con `valid`, `strategy_name`, `action`, `reason` y,
            si es valida, direccion, entrada, stop y objetivo.

        Vinculaciones:
        - Lo llama `strategy.execution.live_trading_engine`.
        - El dict resultante se pasa a `strategy.ai.feature_extraction` para
          el meta-etiquetado.
        """
        market = classify_orb_market(symbol)
        if not bool(self.config.enabled) or market is None:
            return {
                "valid": False,
                "strategy_name": "ORB_NEW_YORK",
                "action": "SYMBOL_NOT_ORB_ELIGIBLE",
                "reason": (
                    "ORB_SOLO_XAUUSD_MICROXAUUSD_XAGUSD_MICROXAGUSD_USOIL_"
                    "WALL_STREET_30_US_TECH_100_US500"
                ),
                "symbol": symbol,
            }

        if now_utc is None:
            tick = self.data_provider.get_current_tick(symbol)
            now_utc = pd.Timestamp(tick["time"]).to_pydatetime()
        now_ny, open_ny, range_end_ny, close_ny = self._session_bounds(now_utc)

        base = {
            "valid": False,
            "strategy_name": "ORB_NEW_YORK",
            "strategy_version": ORB_STRATEGY_VERSION,
            "symbol": symbol,
            "orb_market": market,
            "timezone": self.config.timezone_name,
            "session_date_ny": str(now_ny.date()),
            "session_open_ny": open_ny.isoformat(),
            "opening_range_end_ny": range_end_ny.isoformat(),
            "session_close_ny": close_ny.isoformat(),
        }

        if now_ny.weekday() >= 5:
            return {**base, "action": "NO_ORB_SESSION", "reason": "FIN_DE_SEMANA_NEW_YORK"}
        if now_ny < open_ny:
            return {**base, "action": "WAITING_NEW_YORK_OPEN", "reason": "ANTES_DE_09_30_NEW_YORK"}
        if now_ny >= close_ny:
            return {**base, "action": "NO_ORB_SESSION", "reason": "SESION_NEW_YORK_FINALIZADA"}

        df = self._prepare_candles(symbol, now_utc)
        session = df[(df["time_ny"] >= open_ny) & (df["time_ny"] < close_ny)].copy()
        opening = session[(session["time_ny"] >= open_ny) & (session["time_ny"] < range_end_ny)].copy()

        # v61: con M5 el ORB 09:30-09:45 queda formado por 3 velas cerradas.
        tf_minutes = 5 if str(self.config.timeframe or "M5").upper() == "M5" else 1
        needed = max(1, int(math.ceil(float(self.config.opening_range_minutes) / tf_minutes)))
        if now_ny < range_end_ny or len(opening) < needed:
            partial_high = float(opening["high"].max()) if not opening.empty else None
            partial_low = float(opening["low"].min()) if not opening.empty else None
            return {
                **base,
                "action": "BUILDING_OPENING_RANGE",
                "reason": "FORMANDO_RANGO_PRIMEROS_15_MINUTOS",
                "opening_range_candles": int(len(opening)),
                "opening_range_required_candles": needed,
                "opening_range_high": partial_high,
                "opening_range_low": partial_low,
            }

        range_high = float(opening["high"].max())
        range_low = float(opening["low"].min())
        range_size = range_high - range_low
        midpoint = (range_high + range_low) / 2.0
        if not math.isfinite(range_size) or range_size <= 0:
            return {**base, "action": "INVALID_OPENING_RANGE", "reason": "RANGO_ORB_SIN_AMPLITUD"}

        profile_key = {"MICRO_XAUUSD": "XAUUSD", "WALL_STREET_30": "US30",
                       "US_TECH_100": "NAS100", "MICRO_XAGUSD": "XAGUSD",
                       "US_OIL": "USOIL", "US_500": "US500"}.get(market, market)
        cfg = self.config.asset_profiles.get(profile_key, {
            "allowed_modes": ["MOMENTUM", "RETEST"],
            "atr_buffer": self.config.breakout_atr_buffer_fraction,
            "max_range_atr_ratio": self.config.max_opening_range_atr_multiple,
            "require_volume": self.config.require_breakout_volume_confirmation,
        })
        period = self.config.opening_range_atr_period
        # Anchor to candles CLOSED by range completion (09:40 bar closes 09:45).
        # Reconstructible after restart; later candles never enter this estimate.
        session_key = (symbol, str(now_ny.date()))
        atr_reference = self._frozen_atr_sessions.get(session_key)
        if atr_reference is None:
            opening_history = df[df["time_ny"] < range_end_ny]
            atr_reference = self._average_true_range(opening_history, period) if len(opening_history) >= period + 1 else None
            if atr_reference is not None:
                self._frozen_atr_sessions[session_key] = atr_reference
        base.update(atr_frozen_m5=atr_reference, orb_atr_frozen_at=range_end_ny.isoformat())
        max_atr_multiple = float(cfg["max_range_atr_ratio"])
        amplitude = check_range_amplitude(range_high, range_low, atr_reference, max_atr_multiple)
        range_atr_ratio = amplitude["ratio"]
        opening_range_atr_within_limit = amplitude["allow_momentum"]
        allowed_modes = list(cfg["allowed_modes"])
        if not amplitude["allow_momentum"] or not self.config.momentum_enabled:
            allowed_modes = [mode for mode in allowed_modes if mode != "MOMENTUM"]
        base.update(asset_profile=profile_key, allowed_modes=allowed_modes,
                    range_amplitude=amplitude, opening_range_atr_ratio=range_atr_ratio)
        base["orb_audit"] = {
            "schema": "orb-audit-v2", "evaluated_at": pd.Timestamp(now_utc).isoformat(),
            "symbol": symbol, "source": getattr(self.data_provider, "source_name", "UNSPECIFIED_PROVIDER"),
            "range_start": open_ny.isoformat(), "range_end": range_end_ny.isoformat(),
            "orh": range_high, "orl": range_low, "range_amplitude": amplitude,
            "allowed_modes": allowed_modes, "asset_profile": profile_key,
        }
        base["orb_audit"].update(atr_frozen_m5=atr_reference,
                                  atr_frozen_at=range_end_ny.isoformat())
        if atr_reference is not None and not amplitude["isValid"]:
            trigger = {"ratio": range_atr_ratio, "critical_ratio": max_atr_multiple * 1.3,
                       "candle_time": range_end_ny.isoformat()}
            base["orb_audit"]["session_cancellation"] = trigger
            base["session_cancellation"] = trigger
            return {**base, "action": "ORB_SESSION_CANCELLED", "reason": "RANGO_ORB_SUPERA_UMBRAL_CRITICO"}
        if atr_reference is None:
            return {**base, "action": "WAITING_ORB_ATR", "reason": "ATR_M5_SIN_HISTORIAL_SUFICIENTE"}

        post_range = session[session["time_ny"] >= range_end_ny].copy()
        if post_range.empty:
            return {
                **base,
                "action": "WAITING_BREAKOUT",
                "reason": "RANGO_COMPLETO_ESPERANDO_PRIMERA_VELA_CERRADA_POST_09_45",
                "opening_range_high": range_high,
                "opening_range_low": range_low,
                "opening_range_midpoint": midpoint,
                "opening_range_size": range_size,
            }

        # ORB: BREAKOUT -> RETEST -> ENTRADA. El retest puede aparecer durante
        # las siguientes 1..N velas cerradas, sin perseguir rupturas antiguas.
        if len(post_range) < 2 and not self.config.momentum_enabled:
            return {
                **base,
                "action": "WAITING_M5_BREAKOUT_RETEST",
                "reason": "ESPERANDO_SECUENCIA_M5_BREAKOUT_MAS_RETEST",
                "opening_range_high": range_high,
                "opening_range_low": range_low,
                "opening_range_midpoint": midpoint,
                "opening_range_size": range_size,
            }

        retest = post_range.iloc[-1]
        retest_close = float(retest["close"])
        retest_high = float(retest["high"])
        retest_low = float(retest["low"])
        buffer = max(
            range_size * max(0.0, float(self.config.breakout_buffer_fraction)),
            (atr_reference or 0.0)
            * max(0.0, float(cfg["atr_buffer"])),
        )

        max_retest = max(1, int(getattr(self.config, "retest_max_candles", 3)))
        candidates = []
        first_candidate = max(0, len(post_range) - max_retest - 1)
        for breakout_index in range(len(post_range) - 2, first_candidate - 1, -1):
            candidate = post_range.iloc[breakout_index]
            before_breakout = session[session["time"] < candidate["time"]]
            prev = (
                float(before_breakout.iloc[-1]["close"])
                if not before_breakout.empty
                else float(opening.iloc[-1]["close"])
            )
            close = float(candidate["close"])
            breakout_up_candidate = prev <= range_high + buffer and close > range_high + buffer
            breakout_down_candidate = prev >= range_low - buffer and close < range_low - buffer
            bars_after = len(post_range) - 1 - breakout_index
            if not (breakout_up_candidate or breakout_down_candidate):
                continue

            intermediate = post_range.iloc[breakout_index + 1:-1]
            invalidated = False
            if breakout_up_candidate and not intermediate.empty:
                invalidated = bool((pd.to_numeric(intermediate["close"]) <= midpoint).any())
            elif breakout_down_candidate and not intermediate.empty:
                invalidated = bool((pd.to_numeric(intermediate["close"]) >= midpoint).any())
            if invalidated:
                continue
            candidates.append((candidate, prev, close, breakout_up_candidate, breakout_down_candidate, bars_after))
            break

        if candidates:
            breakout, prev_close, breakout_close, breakout_up, breakout_down, bars_after_breakout = candidates[0]
        else:
            breakout = post_range.iloc[-2] if len(post_range) >= 2 else post_range.iloc[-1]
            before_breakout = session[session["time"] < breakout["time"]]
            prev_close = float(before_breakout.iloc[-1]["close"]) if not before_breakout.empty else float(opening.iloc[-1]["close"])
            breakout_close = float(breakout["close"])
            breakout_up = breakout_down = False
            bars_after_breakout = 1

        # Retest BUY/SELL: toca el borde y vuelve a cerrar fuera del rango.
        signal_atr = atr_reference
        try:
            quote = self.data_provider.get_current_tick(symbol)
            spread = float(quote["ask"]) - float(quote["bid"])
            spread = spread if math.isfinite(spread) and spread >= 0 else 0.0
        except (KeyError, TypeError, ValueError, AttributeError):
            spread = 0.0
        tolerance = max(2 * spread, 0.10 * (signal_atr or 0.0))
        retest_buy_ok = bool(breakout_up and midpoint < retest_low <= range_high + tolerance and retest_close > range_high + buffer)
        retest_sell_ok = bool(breakout_down and midpoint > retest_high >= range_low - tolerance and retest_close < range_low - buffer)
        retest_buy_ok = retest_buy_ok and "RETEST" in allowed_modes
        retest_sell_ok = retest_sell_ok and "RETEST" in allowed_modes
        direction = "BUY" if retest_buy_ok else "SELL" if retest_sell_ok else None

        entry_mode = "ORB_BREAKOUT_RETEST"
        momentum_failures = []
        momentum_audit = {"evaluated":False, "variants":{}, "entry_authorized":False}
        if direction is None and "MOMENTUM" in allowed_modes:
            previous = float(session[session["time"] < retest["time"]].iloc[-1]["close"])
            up = previous <= range_high + buffer and retest_close > range_high + buffer
            down = previous >= range_low - buffer and retest_close < range_low - buffer
            if up or down:
                sign, edge = (1, range_high) if up else (-1, range_low)
                body = sign * (retest_close - float(retest["open"]))
                body_ratio = body / (retest_high - retest_low) if retest_high > retest_low else 0
                displacement = sign * (retest_close - edge)
                momentum_volume = audit_volume_confirmation(df, retest["time"], "MOMENTUM", cfg["require_volume"])
                vol, avg = momentum_volume["volume"], momentum_volume["average_volume"]
                if body_ratio < self.config.momentum_min_body_ratio:
                    momentum_failures.append("MOMENTUM_BODY_TOO_SMALL")
                if not signal_atr or displacement < self.config.momentum_min_displacement_atr * signal_atr:
                    momentum_failures.append("MOMENTUM_DISPLACEMENT_INSUFFICIENT")
                if not signal_atr or displacement > self.config.momentum_max_extension_atr * signal_atr:
                    momentum_failures.append("MOMENTUM_OVEREXTENDED")
                if not momentum_volume["confirmed"]:
                    momentum_failures.append("MOMENTUM_VOLUME_UNCONFIRMED")
                volume_available = vol is not None and avg is not None and vol > 0 and avg > 0
                momentum_audit = {
                    "evaluated":True, "direction":"BUY" if up else "SELL",
                    "confirmation_time":pd.Timestamp(retest["time"]).isoformat(),
                    "body_ratio":body_ratio, "minimum_body_ratio":self.config.momentum_min_body_ratio,
                    "atr":signal_atr, "extension_atr":displacement/signal_atr if signal_atr else None,
                    "maximum_extension_atr":self.config.momentum_max_extension_atr,
                    "minimum_displacement_atr":self.config.momentum_min_displacement_atr,
                    "volume":vol, "average_volume":avg,
                    "volume_status":"AVAILABLE" if volume_available else "UNAVAILABLE_OR_ZERO",
                    "volume_source":self._volume_source(df[df.time <= retest.time]),
                    "volume_ratio":vol / avg if vol is not None and avg and avg > 0 else None,
                    "volume_threshold":1.0,
                    "volume_evidence":momentum_volume,
                    "live_rejections":list(momentum_failures), "variants":{}, "entry_authorized":False,
                }
                # Sensitivity comparisons only: no alternative can set direction.
                for extension_limit in (.50, .75, 1.0, 1.5, 2.0):
                    for allow_missing_volume in (False, True):
                        failures = [f for f in momentum_failures if f != "MOMENTUM_OVEREXTENDED"]
                        if not signal_atr or displacement > extension_limit * signal_atr:
                            failures.append("MOMENTUM_OVEREXTENDED")
                        if allow_missing_volume and not volume_available:
                            failures = [f for f in failures if f != "MOMENTUM_VOLUME_UNCONFIRMED"]
                        name = f"EXT_{extension_limit:.2f}_" + ("MISSING_VOLUME_SHADOW" if allow_missing_volume else "VOLUME_REQUIRED")
                        momentum_audit["variants"][name] = {"maximum_extension_atr":extension_limit,
                            "missing_volume_exception":allow_missing_volume and not volume_available,
                            "remaining_failures":failures, "momentum_checks_pass":not failures,
                            "other_execution_checks":"NOT_EVALUATED", "entry_authorized":False}
                if not momentum_failures:
                    direction = "BUY" if up else "SELL"
                    entry_mode = "ORB_BREAKOUT_MOMENTUM"
                    breakout, breakout_close, prev_close = retest, retest_close, previous
                    breakout_up, breakout_down, bars_after_breakout = up, down, 0

        through_candidate = session[session["time"] <= retest["time"]].copy()
        vwap = self._session_vwap(through_candidate)
        poc = self._session_poc(through_candidate, bins=int(self.config.poc_bins))
        vwap_buy_ok = vwap is not None and retest_close > float(vwap)
        vwap_sell_ok = vwap is not None and retest_close < float(vwap)
        poc_buy_ok = poc is not None and retest_close > float(poc)
        poc_sell_ok = poc is not None and retest_close < float(poc)

        diagnostics = {
            "orb_entry_mode": entry_mode,
            "orb_audit": {
                **base["orb_audit"],
                "evaluated_at":pd.Timestamp(now_utc).isoformat(),
                "symbol":symbol, "source":getattr(self.data_provider,"source_name", "UNSPECIFIED_PROVIDER"),
                "session_timezone":self.config.timezone_name,
                "range_start":pd.Timestamp(open_ny).isoformat(), "range_end":pd.Timestamp(range_end_ny).isoformat(),
                "orh":range_high, "orl":range_low, "buffer":buffer, "retest_tolerance":tolerance,
                "opening_candles":[{"time":pd.Timestamp(r["time"]).isoformat(),
                    **{k:float(r[k]) for k in ("open","high","low","close")}} for _,r in opening.iterrows()],
                "momentum":momentum_audit,
                "retest":{"buy_ok":retest_buy_ok,"sell_ok":retest_sell_ok,
                    "bars_after_breakout":int(bars_after_breakout), "maximum_bars":max_retest},
            },
            "orb_signal_atr": signal_atr,
            "retest_tolerance": tolerance,
            "momentum_rejection_reasons": momentum_failures,
            "opening_range_high": range_high,
            "opening_range_low": range_low,
            "opening_range_midpoint": midpoint,
            "opening_range_size": range_size,
            "breakout_candle_time": pd.Timestamp(breakout["time"]).isoformat(),
            "breakout_candle_time_ny": pd.Timestamp(breakout["time_ny"]).isoformat(),
            "breakout_close": breakout_close,
            "retest_candle_time": pd.Timestamp(retest["time"]).isoformat() if entry_mode == "ORB_BREAKOUT_RETEST" else None,
            "retest_candle_time_ny": pd.Timestamp(retest["time_ny"]).isoformat() if entry_mode == "ORB_BREAKOUT_RETEST" else None,
            "retest_close": retest_close,
            "retest_high": retest_high,
            "retest_low": retest_low,
            "previous_close": prev_close,
            "session_vwap": vwap,
            "session_poc": poc,
            "vwap_buy_ok": bool(vwap_buy_ok),
            "vwap_sell_ok": bool(vwap_sell_ok),
            "poc_buy_ok": bool(poc_buy_ok),
            "poc_sell_ok": bool(poc_sell_ok),
            "breakout_up": bool(breakout_up),
            "breakout_down": bool(breakout_down),
            "breakout_buffer": float(buffer),
            "bars_after_breakout": int(bars_after_breakout),
            "retest_max_candles": int(max_retest),
            "retest_buy_ok": bool(retest_buy_ok),
            "retest_sell_ok": bool(retest_sell_ok),
            "volume_source": (
                "real_volume" if "real_volume" in through_candidate and float(pd.to_numeric(through_candidate["real_volume"], errors="coerce").fillna(0).sum()) > 0
                else "tick_volume" if "tick_volume" in through_candidate
                else "fallback"
            ),
            "opening_range_atr_reference": atr_reference,
            "opening_range_atr_ratio": range_atr_ratio,
            "opening_range_atr_max_multiple": max_atr_multiple,
        }

        if direction is None:
            reason = (
                "ULTIMA_SECUENCIA_M5_NO_TIENE_BREAKOUT_VALIDO"
                if not (breakout_up or breakout_down)
                else "BREAKOUT_M5_SIN_RETEST_CONFIRMADO_AL_ORB"
            )
            if momentum_audit["evaluated"] and momentum_failures:
                reason = "ORB_MOMENTUM_REJECTED:" + ",".join(momentum_failures)
            return {**base, **diagnostics, "action": "WAITING_M5_BREAKOUT_RETEST", "reason": reason}

        # one_signal_per_session: si ya se aprovechó una ruptura distinta ese
        # mismo día NY para este símbolo, no se generan señales adicionales
        # basadas en otra vela de ruptura (evita sobre-operar el mismo día).
        session_date_str = str(now_ny.date())
        breakout_key = str(pd.Timestamp(breakout["time"]).isoformat())
        if is_orb_silver_symbol(symbol) or bool(getattr(self.config, "one_signal_per_session", True)):
            remembered = self._session_signal_memory.get(orb_session_asset(symbol))
            if remembered is not None and remembered[0] == session_date_str and (is_orb_silver_symbol(symbol) or remembered[1] != breakout_key):
                return {
                    **base, **diagnostics, "direction": direction,
                    "action": "ORB_SESSION_SIGNAL_LIMIT_REACHED",
                    "reason": "ORB_SILVER_SESSION_ALREADY_USED" if is_orb_silver_symbol(symbol) else "YA_SE_UTILIZO_UNA_RUPTURA_DISTINTA_ESTA_SESION",
                    "session_previous_breakout_time": remembered[1],
                }

        mode = "MOMENTUM" if entry_mode == "ORB_BREAKOUT_MOMENTUM" else "RETEST"
        volume_evidence = audit_volume_confirmation(df, breakout["time"], mode, cfg["require_volume"])
        breakout_volume_confirmed = volume_evidence["confirmed"]
        breakout_volume = volume_evidence["volume"]
        breakout_volume_reference = volume_evidence["average_volume"]
        diagnostics.update(breakout_volume=breakout_volume,
                           breakout_volume_reference_avg=breakout_volume_reference,
                           breakout_volume_confirmed=breakout_volume_confirmed)
        body = abs(retest_close - float(retest["open"]))
        tail = (min(float(retest["open"]), retest_close) - retest_low if direction == "BUY"
                else retest_high - max(float(retest["open"]), retest_close))
        tail_ratio = max(0.0, tail) / max(body, 1e-12)
        quality = evaluate_retest_quality(bars_after_breakout, tail_ratio) if mode == "RETEST" else None
        quality_weight = {"HIGH_QUALITY": 1.0, "STANDARD_QUALITY": 0.75, "LOW_QUALITY": 0.5}.get(quality)
        diagnostics.update(retest_quality=quality, rejection_tail_ratio=tail_ratio if quality else None)
        diagnostics["orb_audit"]["retest"].update(quality=quality, quality_weight=quality_weight,
                                                 rejection_tail_ratio=tail_ratio if quality else None)
        diagnostics["orb_audit"]["volume_evidence"] = volume_evidence
        diagnostics["volume_status"] = volume_evidence["status"]

        vwap_ok = vwap_buy_ok if direction == "BUY" else vwap_sell_ok
        poc_ok = poc_buy_ok if direction == "BUY" else poc_sell_ok
        failed = []
        require_vwap = bool(self.config.require_vwap_alignment)
        require_poc = bool(self.config.require_poc_alignment)
        require_both = bool(getattr(self.config, "vwap_poc_require_both", False))
        if require_vwap and require_poc and not require_both:
            # v109: basta con que UNO de los dos (VWAP o POC) este alineado con
            # el retest, en vez de exigir ambos simultaneamente. El analisis de
            # logs mostro que el 100% de los rechazos de retest en produccion
            # ya venian acompanados de "RUPTURA_SIN_VOLUMEN_SUFICIENTE" (el
            # verdadero cuello de botella); VWAP/POC casi nunca bloqueaban solos.
            if not vwap_ok and not poc_ok:
                failed.append("VWAP_Y_POC_NO_ALINEADOS_CON_RETEST")
        else:
            if require_vwap and not vwap_ok:
                failed.append("VWAP_NO_ALINEADO_CON_RETEST")
            if require_poc and not poc_ok:
                failed.append("POC_NO_ALINEADO_CON_RETEST")
        if (
            entry_mode == "ORB_BREAKOUT_RETEST"
            and cfg["require_volume"]
            and breakout_volume_confirmed is False
        ):
            failed.append("RUPTURA_SIN_VOLUMEN_SUFICIENTE")

        # v107: niveles de cuarto ($25/$50/$75/$100) SOLO para XAUUSD/microXAUUSD.
        # El resto de mercados ORB no aplica esta confluencia (ver docstring de
        # `ORBConfig.gold_quarter_level_enabled`).
        quarter_level_applicable = bool(
            self.config.gold_quarter_level_enabled and is_orb_gold_symbol(symbol)
        )
        quarter_level_ok = True
        nearest_quarter_level = None
        if quarter_level_applicable:
            increment = max(1e-6, float(self.config.gold_quarter_level_increment))
            tolerance = max(0.0, float(self.config.gold_quarter_level_tolerance_price))
            nearest_quarter_level = round(retest_close / increment) * increment
            quarter_level_ok = abs(retest_close - nearest_quarter_level) <= tolerance
            if bool(self.config.require_gold_quarter_level) and not quarter_level_ok:
                failed.append("SIN_CONFLUENCIA_NIVEL_DE_CUARTO_GOLD")
        if failed:
            return {
                **base, **diagnostics, "direction": direction,
                "action": "ORB_RETEST_FILTERED" if entry_mode == "ORB_BREAKOUT_RETEST" else "ORB_MOMENTUM_FILTERED", "reason": ",".join(failed),
                "rejection_reasons": failed,
            }


        # v61: protección exacta en el 50% del Opening Range.
        # Sin buffer adicional: el midpoint es el nivel estructural de invalidación.
        stop_loss = midpoint
        entry_price = retest_close
        risk_distance = abs(entry_price - stop_loss)
        if risk_distance <= 0:
            return {**base, **diagnostics, "action": "INVALID_ORB_STOP", "reason": "DISTANCIA_DE_RIESGO_ORB_INVALIDA"}
        target_rr = max(0.1, float(self.config.target_rr))
        take_profit = entry_price + risk_distance * target_rr if direction == "BUY" else entry_price - risk_distance * target_rr

        confirmations = {
            "opening_range_complete": True,
            "m5_fresh_breakout": True,
            ("orb_retest_confirmed" if entry_mode == "ORB_BREAKOUT_RETEST" else "orb_momentum_confirmed"): True,
            "vwap_alignment": bool(vwap_ok),
            "poc_alignment": bool(poc_ok),
            "new_york_session": True,
            "eligible_market": True,
            "stop_at_orb_50_percent": True,
            "opening_range_atr_within_limit": opening_range_atr_within_limit,
            "breakout_volume_confirmed": entry_mode == "ORB_BREAKOUT_MOMENTUM" or breakout_volume_confirmed is not False,
        }
        if quarter_level_applicable:
            confirmations["gold_quarter_level_alignment"] = bool(quarter_level_ok)
        passed = [name for name, ok in confirmations.items() if ok]
        missing = [name for name, ok in confirmations.items() if not ok]
        percentage = round(len(passed) / len(confirmations) * 100.0, 2)

        signal = {
            "strategy_name": "ORB_NEW_YORK",
            "strategy_version": ORB_STRATEGY_VERSION,
            "orb_entry_mode": entry_mode,
            "orb_metrics_strategy": "ORB_NY_" + mode,
            "retest_quality": quality,
            "retest_quality_weight": quality_weight,
            "rejection_tail_ratio": tail_ratio if quality else None,
            "retest_candle_index": bars_after_breakout if quality else None,
            "asset_profile": profile_key,
            "range_amplitude": amplitude,
            "orb_signal_atr": signal_atr,
            "orb_momentum_max_extension_atr": self.config.momentum_max_extension_atr,
            "timeframe": "M5",
            "valid": True,
            "direction": direction,
            "entry_time": pd.Timestamp(retest["time"]).to_pydatetime(),
            "entry_price": entry_price,
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "risk_reward_ratio": target_rr,
            "confirmation_ok": True,
            "confirmation_decision": entry_mode + "_CONFIRMED",
            "confirmation_percentage": percentage,
            "confirmations_passed": len(passed),
            "confirmations_total": len(confirmations),
            "passed_confirmations": passed,
            "missing_confirmations": missing,
            "critical_confirmations_ok": True,
            "critical_confirmation_failures": [],
            "rejection_reasons": [],
            "confirmations": confirmations,
            "trade_score": percentage,
            "trade_grade": "A" if percentage >= 90 else "B",
            "orb_market": market,
            "opening_range_high": range_high,
            "opening_range_low": range_low,
            "opening_range_midpoint": midpoint,
            "session_vwap": vwap,
            "session_poc": poc,
            "breakout_candle_time_ny": pd.Timestamp(breakout["time_ny"]).isoformat(),
            "breakout_candle_time": breakout_key,
            "retest_candle_time_ny": pd.Timestamp(retest["time_ny"]).isoformat() if entry_mode == "ORB_BREAKOUT_RETEST" else None,
            "orb_session_date": session_date_str,
            "volume_evidence": volume_evidence,
            "volume_status": volume_evidence["status"],
            "atr_frozen_m5": atr_reference,
            "orb_atr_frozen_at": range_end_ny.isoformat(),
            "opening_range_atr_ratio": range_atr_ratio,
            "breakout_volume_ratio": (
                breakout_volume / breakout_volume_reference
                if breakout_volume is not None and breakout_volume_reference not in (None, 0)
                else None
            ),
            "orb_risk_model": "1_PERCENT_TOTAL_SPLIT_0_5_TP1_0_5_RUNNER",
            "orb_runner_plan": "FIXED_TP_BE_AFTER_TP1_SPREAD_PROTECTED",
        }

        from strategy.orb.signal_payload import build_signal_payload
        signal.update(build_signal_payload(direction, entry_price, stop_loss,
            entry_price + (1 if direction == "BUY" else -1) * risk_distance, take_profit,
            {"HIGH_QUALITY": "ALTA", "STANDARD_QUALITY": "ESTÁNDAR", "LOW_QUALITY": "BAJA"}.get(quality, "NO_CLASIFICADA"),
            atr_frozen_m5=atr_reference, volume_status=volume_evidence["status"],
            range_amplitude_ratio=range_atr_ratio))

        # Evidencia exacta de la decisión ORB. Se entrega al motor únicamente
        # para congelar la auditoría visual; no participa en el score ni en la
        # ejecución. Incluye sólo velas ya cerradas para evitar repintado.
        audit_candles = []
        volume_column = next(
            (name for name in ("tick_volume", "real_volume", "volume") if name in df.columns),
            None,
        )
        for _, candle in df.tail(140).iterrows():
            raw_volume = candle.get(volume_column) if volume_column else None
            audit_candles.append({
                "time": pd.Timestamp(candle["time"]).isoformat(),
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
                "volume": float(raw_volume) if raw_volume is not None and pd.notna(raw_volume) else None,
            })
        audit_chart_seed = {
            "data_source": "DERIV_CHARTS",
            "evidence_mode": "ENTRY_DECISION_CACHE",
            "timeframes": {
                "M5": {
                    "symbol": symbol,
                    "timeframe": "M5",
                    "candles": audit_candles,
                    "events": [
                        {
                            "time": pd.Timestamp(breakout["time"]).isoformat(),
                            "type": "orb_breakout",
                            "label": "Breakout ORB",
                            "direction": direction,
                            "price": breakout_close,
                            "layer": "structure",
                        },
                        {
                            "time": pd.Timestamp(retest["time"]).isoformat(),
                            "type": "orb_retest" if entry_mode == "ORB_BREAKOUT_RETEST" else "orb_momentum",
                            "label": "Retest ORB confirmado" if entry_mode == "ORB_BREAKOUT_RETEST" else "Momentum ORB confirmado",
                            "direction": direction,
                            "price": retest_close,
                            "layer": "structure",
                        },
                    ],
                    "zones": [{
                        "time": open_ny.isoformat(),
                        "type": "orb_opening_range",
                        "label": "Rango apertura NY 09:30–09:45",
                        "low": range_low,
                        "high": range_high,
                        "direction": direction,
                        "status": "CONFIRMADO",
                        "layer": "orb",
                    }],
                    "levels": [
                        {"type": "orb_high", "label": "ORB High", "price": range_high},
                        {"type": "orb_low", "label": "ORB Low", "price": range_low},
                        {"type": "orb_mid", "label": "ORB 50%", "price": midpoint},
                        {"type": "vwap", "label": "VWAP sesión", "price": vwap},
                        {"type": "poc", "label": "POC sesión", "price": poc},
                    ],
                    "smc_context": {
                        "range_high": range_high,
                        "range_low": range_low,
                        "equilibrium": midpoint,
                        "zone": "ORB",
                    },
                    "context_mode": "ESTRATEGIA_ORB",
                    "evidence_mode": "ENTRY_DECISION_CACHE",
                    "updated_at": pd.Timestamp(retest["time"]).isoformat(),
                }
            },
            "available_timeframes": ["M5"],
            "captured_at": pd.Timestamp(retest["time"]).isoformat(),
        }

        return {
            **base,
            **diagnostics,
            "valid": True,
            "action": "ORB_SIGNAL_CONFIRMED",
            "reason": entry_mode + "_CONFIRMADO_CON_VWAP_Y_POC",
            "direction": direction,
            "signal": signal,
            "entry": signal,
            "h1_trend": None,
            "m15_setup_type": None,
            "m15_structure_break_type": None,
            "m15_zone": None,
            "diagnostics": diagnostics,
            "audit_chart_seed": audit_chart_seed,
        }
