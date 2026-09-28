"""Analizador multi-temporal H4 → H1 → M15 → M5.

Aplica el principio SMC de que cada temporalidad cumple un papel distinto:

- H4 da la TENDENCIA MAYOR.
- H1 confirma el CONTEXTO y debe converger con H4.
- M15 da el SETUP: donde esta la zona operable.
- M5 da la CONFIRMACION: cuando entrar exactamente.

Recorre una maquina de estados que solo avanza si cada etapa valida la
anterior. Si algo falla, la senal se detiene en un estado terminal y se
registra el motivo, de modo que siempre se puede explicar por que NO se
opero.

CACHE POR ETAPA: recalcular H1 en cada ciclo seria absurdo, porque su
resultado no cambia hasta que cierra una vela nueva. La cache guarda cada
etapa hasta el cierre siguiente, protegida por un `RLock` porque el monitor
de posiciones puede leerla mientras el escaner la renueva.

ANTIGUEDAD DE SENAL: `max_m5_signal_age_candles` limita la vejez de la
confirmacion M5 para ABRIR una entrada nueva. Un `STALE_M5_SIGNAL` significa
"demasiado tarde para entrar", NO "la tesis se ha invalidado", y por tanto no
debe usarse como criterio para cerrar una posicion ya abierta.

Vinculaciones:
- Ejecuta `strategy.execution.trade_pipeline.run_trade_pipeline` en cada
  temporalidad.
- Usa `strategy.smc.market_structure.get_current_trend` para el contexto H1 y
  `strategy.smc.h1_doji_extremes` como confluencia.
- `config.symbol_policy` puede bloquear direcciones por instrumento.
- Lo consumen `strategy.execution.live_trading_engine` y
  `strategy.execution.live_paper_trading_engine`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import threading
import time

import pandas as pd

from config.symbol_policy import get_symbol_direction_policy
from strategy.execution.trade_pipeline import PipelineConfig, run_trade_pipeline
from strategy.smc.structural_validation import get_h1_structural_range_flexible
from strategy.smc.m15_setup import build_m15_setups
from strategy.smc.market_structure import get_current_trend
from strategy.smc.h1_adaptive_context import evaluate_h1_adaptive_context, h1_ob_location_valid
from strategy.smc.entry_location import closed_range, evaluate_entry_location
from strategy.smc.h1_doji_extremes import H1ExtremeDojiConfig, detect_h1_extreme_doji


@dataclass
class MultiTimeframeConfig:
    """
    Configuración del flujo:

        H4  -> tendencia mayor
        H1  -> contexto / convergencia
        M15 -> setup
        M5  -> confirmación / entrada

    Los `require_*` permiten relajar etapas en pruebas, pero en operativa
    deben quedarse en `True`: desactivarlos elimina precisamente las
    validaciones que dan sentido al analisis multi-temporal.

    `require_m5_after_m15` exige que la confirmacion sea POSTERIOR al setup,
    evitando dar por buena una confirmacion que ocurrio antes.

    `max_m5_signal_age_candles` limita la antiguedad de la confirmacion para
    ABRIR una entrada. No es un criterio de invalidacion de posiciones ya
    abiertas.
    """

    higher_timeframe: str = "H4"
    structure_timeframe: str = "H1"
    confirmation_timeframe: str = "M15"
    entry_timeframe: str = "M5"

    higher_timeframe_candles: int = 500
    structure_candles: int = 500
    confirmation_candles: int = 500
    entry_candles: int = 350

    # El analizador aislado conserva compatibilidad con consumidores que
    # construyen una secuencia H1/M15/M5. El motor live lo activa de forma
    # sólo para el perfil ORB; SMC usa H1 como contexto principal.
    require_h4_h1_convergence: bool = False
    smc_entry_location_enabled: bool = False
    h1_location_only: bool = False
    smc_entry_location_policy: str = "ALL_TIMEFRAMES"
    volatility_entry_location_enabled: bool = False  # Legacy standalone configuration
    require_h1_trend: bool = True
    require_m15_setup: bool = True
    require_m5_confirmation: bool = True

    require_m5_after_m15: bool = True
    require_latest_m15_setup: bool = True

    max_m5_signal_age_candles: int = 2
    max_m5_signal_age_minutes: float | None = None

    # Optimización del demonio: H1/M15/M5 se recalculan solamente cuando puede
    # existir una nueva vela cerrada. La entrada sigue consultando el tick actual
    # cuando aparece una señal válida.
    stage_cache_enabled: bool = True
    cache_grace_seconds: float = 2.0


class MultiTimeframeAnalyzer:
    """
    Analizador multi-temporal H1 -> M15 -> M5.

    Estados principales:

        START
          |
          +--> H1_CONTEXT_READY
                  |
                  +--> DIRECTION_VALIDATED
                          |
                          +--> M15_SETUP_READY
                                  |
                                  +--> WAITING_M5_CONFIRMATION
                                          |
                                          +--> M5_CONFIRMATION_READY
                                                  |
                                                  +--> M5_SIGNAL_FRESH
                                                          |
                                                          +--> READY_TO_ENTER

    Estados terminales posibles:

        NO_H1_CONTEXT
        DIRECTION_POLICY_BLOCKED
        NO_M15_SETUP
        WAITING_M5_AFTER_M15
        NO_M5_CONFIRMATION
        STALE_M5_SIGNAL
        INVALID_DIRECTION
        READY_TO_ENTER

    Solo `READY_TO_ENTER` habilita una entrada. Los demas estados terminales
    describen en que punto exacto se detuvo el analisis, informacion que se
    registra y se usa despues para auditar oportunidades perdidas.
    """

    def __init__(
        self,
        data_provider,
        config: MultiTimeframeConfig | None = None,
        pipeline_config: PipelineConfig | None = None,
    ):
        """Enlaza proveedor de datos y configuración, y prepara la caché.

        Args:
            data_provider: objeto con `get_candles` y `get_current_tick`.
            config: parametros del flujo multi-temporal.
            pipeline_config: parametros del pipeline SMC que se ejecutara en
                cada temporalidad.
        """
        self.data_provider = data_provider
        self.config = config or MultiTimeframeConfig()
        self.pipeline_config = pipeline_config or PipelineConfig()

        # (symbol, timeframe) -> datos y resultado del pipeline de la última
        # vela cerrada analizada.
        self._stage_cache = {}
        # El monitor de posiciones puede leer la caché mientras el scanner M5
        # la renueva. El lock protege únicamente el mapa; las lecturas de MT5 y
        # el pipeline siguen fuera de la sección crítica para no frenar señales.
        self._stage_cache_lock = threading.RLock()
        # Un lock por (símbolo, timeframe) evita el efecto "cache stampede":
        # si el scanner y el monitor piden la misma etapa justo al cerrar una
        # vela, sólo uno descarga/procesa y el otro reutiliza ese resultado.
        # Los símbolos distintos continúan ejecutándose de forma independiente.
        self._stage_inflight_locks = {}

    _TIMEFRAME_SECONDS = {
        "M1": 60,
        "M2": 120,
        "M3": 180,
        "M4": 240,
        "M5": 300,
        "M6": 360,
        "M10": 600,
        "M12": 720,
        "M15": 900,
        "M20": 1200,
        "M30": 1800,
        "H1": 3600,
        "H2": 7200,
        "H3": 10800,
        "H4": 14400,
        "H6": 21600,
        "H8": 28800,
        "H12": 43200,
        "D1": 86400,
    }

    def clear_stage_cache(self, symbol=None, timeframe=None):
        """Invalida la caché completa o una etapa concreta.

        Sin argumentos borra todo. Con `symbol` o `timeframe` filtra
        selectivamente, y ambos pueden combinarse.

        Vinculaciones:
        - Lo llama `strategy.execution.live_trading_engine` cuando necesita
          forzar un recalculo, por ejemplo tras reconectar con el broker.
        """
        with self._stage_cache_lock:
            if symbol is None and timeframe is None:
                self._stage_cache.clear()
                return

            keys = list(self._stage_cache.keys())
            for key in keys:
                key_symbol, key_timeframe = key
                if symbol is not None and key_symbol != symbol:
                    continue
                if timeframe is not None and key_timeframe != str(timeframe).upper():
                    continue
                self._stage_cache.pop(key, None)

    def cached_stage(self, symbol, timeframe):
        """Devuelve un snapshot seguro de una etapa para auditoría visual.

        Copia superficial bajo el lock: el llamante puede inspeccionarla sin
        riesgo de corromper la cache ni de leerla a medio actualizar.

        Returns:
            Dict con `data`, `result` y `refresh_at`, o vacio si no hay nada
            cacheado.
        """
        key = (str(symbol), str(timeframe).upper())
        with self._stage_cache_lock:
            cached = self._stage_cache.get(key)
            return dict(cached) if isinstance(cached, dict) else {}

    def _next_refresh_at(self, timeframe, now):
        """Calcula cuándo caduca la caché de una temporalidad.

        Alinea el vencimiento con el cierre real de la siguiente vela —no con
        un intervalo fijo desde ahora— y le suma `cache_grace_seconds` para
        dar margen a que el broker publique el dato definitivo.

        Returns:
            Instante de caducidad. Si la temporalidad es desconocida devuelve
            `now`, lo que desactiva la cache en la practica.
        """
        seconds = self._TIMEFRAME_SECONDS.get(str(timeframe).upper(), 0)
        if seconds <= 0:
            return now
        epoch = now.timestamp()
        next_epoch = (int(epoch // seconds) + 1) * seconds
        return (
            pd.Timestamp(next_epoch, unit="s", tz="UTC")
            + pd.Timedelta(seconds=float(self.config.cache_grace_seconds))
        ).to_pydatetime()

    def _get_stage_result(self, symbol, timeframe, count):
        """Obtiene una etapa H1/M15/M5 usando caché hasta la próxima vela cerrada.

        Con acierto de cache devuelve al instante lo guardado. Si no, descarga
        velas cerradas, ejecuta el pipeline y guarda el resultado.

        Descarga y pipeline se ejecutan FUERA del lock, y solo se toma para
        leer y escribir el mapa. Asi el trabajo lento no bloquea al monitor
        de posiciones.

        Returns:
            Tupla `(datos, resultado, telemetria)`, donde la telemetria trae
            `cache_hit` y los tiempos de descarga y pipeline.
        """
        key = (str(symbol), str(timeframe).upper())
        now = datetime.now(timezone.utc)
        with self._stage_cache_lock:
            cached = self._stage_cache.get(key)

        if (
            bool(self.config.stage_cache_enabled)
            and cached is not None
            and now < cached["refresh_at"]
        ):
            return (
                cached["data"],
                cached["result"],
                {
                    "cache_hit": True,
                    "data_fetch_seconds": 0.0,
                    "pipeline_seconds": 0.0,
                    "refresh_at": cached["refresh_at"].isoformat(),
                },
            )

        # Crear/obtener el candado bajo el lock del mapa; el trabajo pesado se
        # serializa únicamente para esta clave, nunca entre símbolos distintos.
        with self._stage_cache_lock:
            stage_lock = self._stage_inflight_locks.setdefault(
                key, threading.Lock()
            )

        with stage_lock:
            # Otra hebra pudo completar esta etapa mientras esperábamos.
            now = datetime.now(timezone.utc)
            with self._stage_cache_lock:
                cached = self._stage_cache.get(key)
            if (
                bool(self.config.stage_cache_enabled)
                and cached is not None
                and now < cached["refresh_at"]
            ):
                return (
                    cached["data"],
                    cached["result"],
                    {
                        "cache_hit": True,
                        "single_flight_reuse": True,
                        "data_fetch_seconds": 0.0,
                        "pipeline_seconds": 0.0,
                        "refresh_at": cached["refresh_at"].isoformat(),
                    },
                )

            fetch_started = time.monotonic()
            data = self._get_closed_candles(symbol, timeframe, count)
            fetch_seconds = time.monotonic() - fetch_started

            pipeline_started = time.monotonic()
            result = self._run_pipeline(data, symbol)
            if str(timeframe).upper() == 'M15' and self.config.h1_location_only:
                setups, block_audit = build_m15_setups(result.get('data'), replace(self.pipeline_config, adaptive_smc_score_enabled=True))
                result = dict(result, setups=setups,
                              diagnostics={**result.get('diagnostics', {}),
                                           'm15_block_audit': block_audit,
                                           'setup_role': 'OB_STRUCTURAL_BREAK'})
            pipeline_seconds = time.monotonic() - pipeline_started

            refresh_at = self._next_refresh_at(timeframe, now)
            if bool(self.config.stage_cache_enabled):
                with self._stage_cache_lock:
                    self._stage_cache[key] = {
                        "data": data,
                        "result": result,
                        "refresh_at": refresh_at,
                    }

        return (
            data,
            result,
            {
                "cache_hit": False,
                "data_fetch_seconds": fetch_seconds,
                "pipeline_seconds": pipeline_seconds,
                "refresh_at": refresh_at.isoformat(),
            },
        )

    # ============================================================
    # TRANSICIONES
    # ============================================================

    @staticmethod
    def _new_transitions():
        """Inicia el registro de transiciones con el estado `START`.

        La lista de transiciones es la TRAZA del analisis: cada etapa anade
        su paso, y al final explica por completo el recorrido seguido.
        """
        return [
            {
                "state": "START",
                "reason": "MULTI_TIMEFRAME_ANALYSIS_STARTED",
            }
        ]

    @staticmethod
    def _add_transition(transitions, state, reason=None, **details):
        """Añade un paso a la traza del análisis.

        Los `details` son opcionales y solo se incluyen si se pasan, para no
        llenar la traza de claves vacias.

        Args:
            transitions: lista que se MUTA en el sitio.
            state: nombre del estado alcanzado.
            reason: codigo del motivo.
            **details: datos de contexto de ese paso.
        """
        transition = {
            "state": state,
            "reason": reason,
        }

        if details:
            transition["details"] = details

        transitions.append(transition)

    # ============================================================
    # DATOS
    # ============================================================

    def _get_closed_candles(self, symbol, timeframe, count):
        """Descarga velas y descarta la última, que puede estar en formación.

        SALVAGUARDA ANTI-REPINTADO: la ultima vela devuelta por el broker
        suele ser la actual, todavia abierta. Analizarla haria que los
        resultados cambiasen a cada tick y que el backtest no reprodujera lo
        vivido en vivo.

        Ademas normaliza `time` a UTC, ordena y elimina duplicados.

        Returns:
            DataFrame de velas cerradas, o uno vacio si el proveedor no
            devuelve nada.
        """
        df = self.data_provider.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        df["time"] = pd.to_datetime(
            df["time"],
            utc=True,
        )

        df = (
            df.sort_values("time")
            .drop_duplicates("time")
            .reset_index(drop=True)
        )

        # Eliminar la vela posiblemente abierta.
        if len(df) > 1:
            df = df.iloc[:-1].copy()

        return df.reset_index(drop=True)

    def _run_pipeline(self, df, symbol):
        """Ejecuta el pipeline SMC, tolerando la ausencia de velas.

        Sin datos devuelve una estructura VACIA con las mismas claves en vez
        de lanzar, de modo que las etapas siguientes puedan seguir su curso y
        terminar en un estado terminal explicito.
        """
        if df is None or df.empty:
            return {
                "data": pd.DataFrame(),
                "setups": pd.DataFrame(),
                "confirmations": pd.DataFrame(),
                "summary": {},
                "diagnostics": {},
            }

        return run_trade_pipeline(
            df=df,
            config=self.pipeline_config,
            symbol=symbol,
        )

    # ============================================================
    # UTILIDADES
    # ============================================================

    @staticmethod
    def _as_time(value):
        """Convierte un valor a Timestamp UTC, o `None` si no es una fecha.

        Envuelve `pd.isna` en try/except porque lanza `TypeError` con ciertos
        tipos, como listas.
        """
        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        return pd.to_datetime(
            value,
            utc=True,
        )

    def _pipeline_diagnostics(self, result, stage_timing=None):
        """Resume el resultado del pipeline en contadores para la traza.

        Reduce DataFrames enteros a numeros (velas, setups, confirmaciones) e
        incorpora la telemetria de cache. Sin esta reduccion, la traza del
        analisis seria impracticable de persistir.

        Returns:
            Dict de diagnostico, ampliando el que ya trajera el pipeline.
        """
        data = result.get("data")
        setups = result.get("setups")
        confirmations = result.get("confirmations")

        diagnostics = dict(
            result.get("diagnostics") or {}
        )

        if stage_timing:
            diagnostics["cache"] = dict(stage_timing)

        diagnostics.update(
            {
                "candles": (
                    int(len(data))
                    if data is not None
                    else 0
                ),
                "setups": (
                    int(len(setups))
                    if setups is not None
                    else 0
                ),
                "confirmations": (
                    int(len(confirmations))
                    if confirmations is not None
                    else 0
                ),
                "first_candle_time": (
                    self._as_time(
                        data["time"].iloc[0]
                    ).isoformat()
                    if data is not None
                    and not data.empty
                    else None
                ),
                "last_candle_time": (
                    self._as_time(
                        data["time"].iloc[-1]
                    ).isoformat()
                    if data is not None
                    and not data.empty
                    else None
                ),
            }
        )

        return diagnostics

    @staticmethod
    def _trend_direction(trend):
        """Traduce la tendencia a dirección operable.

        `BULLISH` a `BUY`, `BEARISH` a `SELL` y cualquier otro valor a
        `None`, que detiene el analisis. Un mercado sin direccion clara no
        genera senal.
        """
        if trend == "BULLISH":
            return "BUY"

        if trend == "BEARISH":
            return "SELL"

        return None

    # ============================================================
    # H1 CONTEXT
    # ============================================================

    def _get_h1_context(self, result, timeframe="H1"):
        """Obtiene un contexto HTF direccional sin exigir que el proveedor
        controlado haya pasado previamente por classify_market_structure().

        El pipeline real puede traer ``structure`` (HH/HL/LH/LL). Las pruebas
        controladas pueden traer solamente eventos BOS/CHOCH. Esta función
        soporta ambos contratos y nunca delega a ``get_current_trend`` con una
        columna ``structure`` inexistente.

        Aplica TRES estrategias en cascada, deteniendose en la primera que
        arroje direccion:
        1. `get_current_trend` sobre la estructura HH/HL/LH/LL.
        2. El ultimo evento BOS/CHOCH: gana el mas reciente.
        3. La tendencia que el propio pipeline resumio en `summary`.

        `timeframe` sólo adapta los motivos de auditoría. El valor por defecto
        conserva el contrato histórico H1 usado por las pruebas y consumidores.

        Returns:
            Dict con `trend`, `valid`, `reason` y `context_time`. Sin
            direccion clara, `valid` es `False` con motivo
            `NO_DIRECTIONAL_H1_TREND` y el analisis termina en
            `NO_H1_CONTEXT`.
        """
        label = str(timeframe or "H1").upper()
        data = result.get("data")
        if data is None or data.empty:
            return {
                "trend": "UNKNOWN",
                "valid": False,
                "reason": f"NO_{label}_DATA",
                "context_time": None,
            }

        data = data.copy()

        # get_current_trend() exige esta columna. No se debe asumir que todos
        # los proveedores de datos ya ejecutaron classify_market_structure().
        if "structure" not in data.columns:
            data["structure"] = None

        trend = get_current_trend(data)

        # Fallback: inferir dirección a partir del último evento BOS/CHOCH.
        if trend == "UNKNOWN":
            bullish = pd.Series(False, index=data.index)
            bearish = pd.Series(False, index=data.index)

            for column in ("bos_bullish", "choch_bullish"):
                if column in data.columns:
                    bullish = bullish | data[column].fillna(False).astype(bool)

            for column in ("bos_bearish", "choch_bearish"):
                if column in data.columns:
                    bearish = bearish | data[column].fillna(False).astype(bool)

            bull_positions = [
                pos for pos, value in enumerate(bullish.to_numpy()) if value
            ]
            bear_positions = [
                pos for pos, value in enumerate(bearish.to_numpy()) if value
            ]

            last_bull = bull_positions[-1] if bull_positions else -1
            last_bear = bear_positions[-1] if bear_positions else -1

            if last_bull > last_bear:
                trend = "BULLISH"
            elif last_bear > last_bull:
                trend = "BEARISH"

        # Último fallback: el pipeline puede haber resumido explícitamente la
        # tendencia aunque su DataFrame de diagnóstico no contenga estructura.
        if trend == "UNKNOWN":
            summary_trend = (result.get("summary") or {}).get("trend")
            if summary_trend in {"BULLISH", "BEARISH"}:
                trend = summary_trend

        valid = trend in {"BULLISH", "BEARISH"}
        context_time = self._as_time(data["time"].iloc[-1])

        return {
            "trend": trend,
            "valid": valid,
            "reason": "VALID_TREND" if valid else f"NO_DIRECTIONAL_{label}_TREND",
            "context_time": context_time.isoformat() if context_time is not None else None,
            "recent_swings": [
                {"time": str(row.get("time")), "structure": str(row.get("structure"))}
                for _, row in data[data["structure"].notna()].tail(6).iterrows()
            ],
            "fallback_allowed": trend == "UNKNOWN",
        }

    def _m15_setups(self, result, expected_direction):
        """Filtra los setups M15 que coinciden con la dirección del contexto H1.

        Traduce `BUY`/`SELL` al vocabulario `long`/`short` que usan los
        setups. Devuelve un DataFrame vacio ante cualquier dato ausente, en
        vez de fallar.

        Args:
            result: salida del pipeline en M15.
            expected_direction: `BUY` o `SELL` que impone H1.

        Returns:
            Setups alineados, ordenados por `setup_time`.
        """
        setups = result.get("setups")

        if (
            setups is None
            or setups.empty
            or expected_direction not in {"BUY", "SELL"}
        ):
            return pd.DataFrame()

        if "setup_type" not in setups.columns:
            return pd.DataFrame()

        if "setup_time" not in setups.columns:
            return pd.DataFrame()

        expected_type = (
            "long"
            if expected_direction == "BUY"
            else "short"
        )

        setups = setups.copy()

        setups = setups[
            setups["setup_type"]
            .astype(str)
            .str.lower()
            == expected_type
        ]

        if setups.empty:
            return setups.reset_index(drop=True)

        setups["setup_time"] = pd.to_datetime(
            setups["setup_time"],
            utc=True,
        )

        return (
            setups.sort_values("setup_time")
            .reset_index(drop=True)
        )

    # ============================================================
    # M5 CONFIRMATIONS
    # ============================================================

    def _m5_confirmations(self, result, expected_direction):
        """Filtra las confirmaciones M5 válidas y alineadas con la dirección.

        Aplica dos filtros: descarta las que el motor de confirmacion marco
        como invalidas, y las que apuntan al lado contrario.

        Returns:
            Confirmaciones utilizables, ordenadas por `entry_time`.
        """
        confirmations = result.get("confirmations")

        if confirmations is None or confirmations.empty:
            return pd.DataFrame()

        confirmations = confirmations.copy()

        if "entry_time" not in confirmations.columns:
            return pd.DataFrame()

        if "valid" in confirmations.columns:
            confirmations = confirmations[
                confirmations["valid"]
                .fillna(False)
                .astype(bool)
            ]

        if (
            expected_direction in {"BUY", "SELL"}
            and "direction" in confirmations.columns
        ):
            confirmations = confirmations[
                confirmations["direction"]
                .astype(str)
                .str.upper()
                == expected_direction
            ]

        if confirmations.empty:
            return confirmations.reset_index(drop=True)

        confirmations["entry_time"] = pd.to_datetime(
            confirmations["entry_time"],
            utc=True,
        )

        return (
            confirmations.sort_values("entry_time")
            .reset_index(drop=True)
        )

    # ============================================================
    # SECUENCIA M15 -> M5
    # ============================================================

    def _select_ordered_pair(
        self,
        m15_setups,
        m5_confirmations,
    ):
        """Empareja un setup M15 con la confirmación M5 que le corresponde.

        Aqui se impone el ORDEN TEMPORAL de la metodologia: primero aparece
        la zona operable en M15 y despues llega la confirmacion en M5. Una
        confirmacion anterior al setup no lo confirma, aunque coincida en
        direccion.

        Dos ajustes gobiernan la seleccion:
        - `require_latest_m15_setup`: solo se considera el setup mas
          reciente. Desactivarlo permite recuperar setups anteriores todavia
          vigentes.
        - `require_m5_after_m15`: exige la posterioridad estricta.

        Entre las confirmaciones elegibles se elige la MAS RECIENTE, por ser
        la que refleja el estado actual del mercado.

        Returns:
            Tupla `(setup, confirmacion, motivo, diagnostico)`. El motivo es
            `None` si el emparejamiento tiene exito, o un codigo terminal
            (`NO_M15_SETUP`, `NO_M5_CONFIRMATION`, `WAITING_M5_AFTER_M15`).
        """
        sequence_diag = {
            "m15_setups_total": (
                0
                if m15_setups is None
                else int(len(m15_setups))
            ),
            "m5_confirmations_total": (
                0
                if m5_confirmations is None
                else int(len(m5_confirmations))
            ),
            "require_latest_m15_setup": bool(
                self.config.require_latest_m15_setup
            ),
            "require_m5_after_m15": bool(
                self.config.require_m5_after_m15
            ),
            "selected_setup_time": None,
            "selected_confirmation_time": None,
            "latest_available_confirmation_time": (
                str(m5_confirmations["entry_time"].max())
                if m5_confirmations is not None and not m5_confirmations.empty else None
            ),
            "eligible_confirmations": 0,
        }

        if m15_setups is None or m15_setups.empty:
            return (
                None,
                None,
                "NO_M15_SETUP",
                sequence_diag,
            )

        ordered_setups = (
            m15_setups.sort_values("setup_time")
            .reset_index(drop=True)
        )

        latest_setup = ordered_setups.iloc[-1]

        latest_setup_time = self._as_time(
            latest_setup["setup_time"]
        )

        sequence_diag["selected_setup_time"] = (
            latest_setup_time.isoformat()
            if latest_setup_time is not None
            else None
        )

        if (
            m5_confirmations is None
            or m5_confirmations.empty
        ):
            return (
                latest_setup.to_dict(),
                None,
                "NO_M5_CONFIRMATION",
                sequence_diag,
            )

        confirmations = (
            m5_confirmations.sort_values("entry_time")
            .reset_index(drop=True)
        )
        sequence_diag["confirmations_before_latest_setup"] = int(
            (confirmations["entry_time"] < latest_setup_time).sum()
        )
        sequence_diag["oldest_setup_time"] = str(ordered_setups.iloc[0]["setup_time"])
        # Diagnostic only: an earlier timestamp is not proof that an OB is
        # still valid. Do not reactivate old setups without invalidation checks.


        if self.config.require_latest_m15_setup:
            candidate_setups = [
                ordered_setups.iloc[-1]
            ]
        else:
            candidate_setups = [
                ordered_setups.iloc[index]
                for index in range(
                    len(ordered_setups) - 1,
                    -1,
                    -1,
                )
            ]

        for setup in candidate_setups:
            setup_time = self._as_time(
                setup["setup_time"]
            )

            if self.config.require_m5_after_m15:
                eligible = confirmations[
                    confirmations["entry_time"] >= setup_time
                ]
            else:
                eligible = confirmations

            if eligible.empty:
                continue

            signal = eligible.iloc[-1]

            signal_time = self._as_time(
                signal["entry_time"]
            )

            sequence_diag.update(
                {
                    "selected_setup_time": (
                        setup_time.isoformat()
                        if setup_time is not None
                        else None
                    ),
                    "selected_confirmation_time": (
                        signal_time.isoformat()
                        if signal_time is not None
                        else None
                    ),
                    "eligible_confirmations": int(
                        len(eligible)
                    ),
                }
            )

            return (
                setup.to_dict(),
                signal.to_dict(),
                "VALID_SEQUENCE",
                sequence_diag,
            )

        return (
            latest_setup.to_dict(),
            None,
            "STALE_M5_CONFIRMATIONS",
            sequence_diag,
        )

    # ============================================================
    # ANTIGÜEDAD M5
    # ============================================================

    def _signal_age_diagnostics(
        self,
        m5_data,
        signal,
    ):
        """Mide la antigüedad de la confirmación M5 y decide si está caducada.

        Una confirmacion valida deja de servir para ABRIR si el mercado ha
        avanzado demasiadas velas desde entonces: el precio ya no esta donde
        estaba y la entrada perderia su ventaja.

        Mide por dos vias independientes, y basta que UNA se supere para
        marcar `is_stale`:
        - `age_candles`: velas transcurridas desde la senal.
        - `age_minutes`: minutos transcurridos, solo si
          `max_m5_signal_age_minutes` esta configurado.

        LIMITE CONCEPTUAL IMPORTANTE: la caducidad significa "ya no procede
        abrir aqui", NO "la tesis se ha invalidado". Aplicarla como criterio
        de cierre sobre una posicion ya abierta confunde dos conceptos
        distintos y provoca salidas prematuras.

        Returns:
            Dict con la posicion de la senal, ambas medidas de antiguedad,
            sus umbrales y los indicadores `is_stale`, `stale_by_candles` y
            `stale_by_minutes`.
        """
        base = {
            "valid": False,
            "reason": "NO_M5_DATA_OR_SIGNAL",
            "signal_time": None,
            "latest_closed_candle_time": None,
            "signal_found_in_m5": False,
            "signal_bar_index": None,
            "latest_bar_index": None,
            "age_candles": None,
            "age_minutes": None,
            "max_age_candles": int(
                self.config.max_m5_signal_age_candles
            ),
            "max_age_minutes": (
                self.config.max_m5_signal_age_minutes
            ),
            "is_stale": False,
            "stale_by_candles": False,
            "stale_by_minutes": False,
        }

        if (
            m5_data is None
            or m5_data.empty
            or signal is None
        ):
            return base

        signal_time = self._as_time(
            signal.get("entry_time")
        )

        if signal_time is None:
            base["reason"] = "M5_SIGNAL_TIME_INVALID"
            return base

        data = m5_data.copy()

        data["time"] = pd.to_datetime(
            data["time"],
            utc=True,
        )

        data = (
            data.sort_values("time")
            .drop_duplicates("time")
            .reset_index(drop=True)
        )

        latest_time = self._as_time(
            data["time"].iloc[-1]
        )

        latest_index = len(data) - 1

        exact_indexes = data.index[
            data["time"] == signal_time
        ]

        signal_found = len(exact_indexes) > 0

        signal_index = (
            int(exact_indexes[-1])
            if signal_found
            else None
        )

        if signal_found:
            age_candles = max(
                0,
                latest_index - signal_index,
            )
        else:
            age_candles = int(
                (data["time"] > signal_time).sum()
            )

        age_minutes = max(
            0.0,
            (
                latest_time - signal_time
            ).total_seconds() / 60.0,
        )

        stale_by_candles = (
            age_candles
            > int(
                self.config.max_m5_signal_age_candles
            )
        )

        max_minutes = (
            self.config.max_m5_signal_age_minutes
        )

        stale_by_minutes = (
            max_minutes is not None
            and age_minutes > float(max_minutes)
        )

        is_stale = bool(
            stale_by_candles
            or stale_by_minutes
        )

        return {
            **base,
            "valid": not is_stale,
            "reason": (
                "M5_SIGNAL_TOO_OLD"
                if is_stale
                else "M5_SIGNAL_FRESH"
            ),
            "signal_time": signal_time.isoformat(),
            "latest_closed_candle_time": (
                latest_time.isoformat()
                if latest_time is not None
                else None
            ),
            "signal_found_in_m5": signal_found,
            "signal_bar_index": signal_index,
            "latest_bar_index": latest_index,
            "age_candles": age_candles,
            "age_minutes": age_minutes,
            "is_stale": is_stale,
            "stale_by_candles": stale_by_candles,
            "stale_by_minutes": stale_by_minutes,
        }

    # ============================================================
    # RESPUESTA BASE
    # ============================================================

    def _build_result(
        self,
        *,
        symbol,
        valid,
        action,
        state,
        direction,
        reason,
        transitions,
        policy_diag,
        h4=None,
        h1=None,
        m15=None,
        m5=None,
        diagnostics=None,
        extra=None,
    ):
        """Compone el dict de respuesta uniforme del analizador.

        TODAS las salidas pasan por aqui, tanto las senales validas como los
        estados terminales. Esa uniformidad permite a los consumidores tratar
        cualquier resultado con la misma forma.

        `extra` se fusiona al final y es lo que anade los campos de operativa
        (entrada, stop, objetivo) cuando la senal es valida.

        Args:
            symbol: instrumento analizado.
            valid: si hay senal operable.
            action: accion para el resto del sistema, p. ej.
                `MULTI_TIMEFRAME_SIGNAL`.
            state: estado de la maquina de estados alcanzado.
            direction: `BUY`, `SELL` o `None`.
            reason: codigo del motivo del desenlace.
            transitions: traza completa del analisis.
            policy_diag: politica de direccion aplicada al simbolo.
            h1, m15, m5: bloques de diagnostico por temporalidad.
            diagnostics: diagnostico general.
            extra: campos adicionales que se fusionan al final.

        Returns:
            El dict de analisis completo.
        """
        result = {
            "symbol": symbol,
            "valid": valid,

            # Compatibilidad con el resto del proyecto.
            "action": action,

            # Nuevo estado explícito.
            "state": state,

            "direction": direction,
            "reason": reason,

            "transitions": transitions,
            "direction_policy": policy_diag,

            "h4": h4,
            "h1": h1,
            "m15": m15,
            "m5": m5,

            "diagnostics": diagnostics or {},
        }

        if extra:
            result.update(extra)

        if self.pipeline_config.telemetry_bot_name:
            try:
                from strategy.smc.telemetry_logger import get_telemetry_tracker
                get_telemetry_tracker(self.pipeline_config.telemetry_bot_name).log_pipeline_result(result)
            except Exception:
                import logging
                logging.getLogger('SMC_Telemetry').exception('SMC funnel recording failed')

        return result

    # ============================================================
    # ANALIZADOR PRINCIPAL
    # ============================================================

    def analyze_symbol(self, symbol):
        """Analiza un símbolo de principio a fin y devuelve la señal o el bloqueo.

        METODO PRINCIPAL de la clase. Recorre la maquina de estados completa:

        1. Politica de direccion del instrumento.
        2. H4: tendencia mayor -> `NO_H4_CONTEXT` si no hay direccion.
        3. H1: contexto y convergencia -> `HTF_TREND_DIVERGENCE` si difiere.
        4. Validacion de la direccion contra la politica ->
           `DIRECTION_POLICY_BLOCKED`.
        5. M15: setups alineados -> `NO_M15_SETUP`.
        6. M5: confirmaciones validas -> `NO_M5_CONFIRMATION`.
        7. Emparejamiento ordenado -> `WAITING_M5_AFTER_M15`.
        8. Antiguedad de la senal -> `STALE_M5_SIGNAL`.
        9. `READY_TO_ENTER` con entrada, stop y objetivo.

        SIEMPRE devuelve un dict y no lanza por falta de senal: la ausencia
        de oportunidad es un resultado normal, y su motivo queda registrado.

        Args:
            symbol: instrumento a analizar.

        Returns:
            Dict de analisis con `valid`, `state`, `action`, `reason`, la
            traza de `transitions` y los diagnosticos por temporalidad.

        Vinculaciones:
        - Lo llaman `strategy.execution.live_trading_engine` y
          `strategy.execution.live_paper_trading_engine` en cada ciclo.
        - Cuando `valid` es `True`, el motor pasa el dict por
          `strategy.ai.meta_labeling` antes de decidir si ejecuta.
        """
        transitions = self._new_transitions()

        # --------------------------------------------------------
        # POLÍTICA DEL INSTRUMENTO
        # --------------------------------------------------------

        policy = get_symbol_direction_policy(symbol)

        policy_diag = {
            "category": policy.category,
            "allowed_direction": policy.allowed_direction,
            "reason": policy.reason,
        }

        # --------------------------------------------------------
        # H4 · TENDENCIA MAYOR OBLIGATORIA
        # --------------------------------------------------------

        h4_diag = {}
        h4_payload = None
        h4_trend = "UNKNOWN"
        h4_direction = None

        if self.config.require_h4_h1_convergence:
            h4_data, h4_result, h4_timing = self._get_stage_result(
                symbol,
                self.config.higher_timeframe,
                self.config.higher_timeframe_candles,
            )
            h4_context = self._get_h1_context(
                h4_result,
                timeframe=self.config.higher_timeframe,
            )
            h4_diag = self._pipeline_diagnostics(h4_result)
            h4_payload = {
                "timeframe": self.config.higher_timeframe,
                "context": h4_context,
                "summary": h4_result.get("summary", {}),
                "timing": h4_timing,
            }
            h4_trend = h4_context["trend"]
            h4_direction = self._trend_direction(h4_trend)

        if self.config.require_h4_h1_convergence and not h4_context["valid"]:
            self._add_transition(
                transitions,
                "NO_H4_CONTEXT",
                h4_context["reason"],
            )
            diagnostics = {
                "failed_stage": "H4",
                "h4": h4_diag,
                "direction_policy": policy_diag,
                "transitions": transitions,
            }
            return self._build_result(
                symbol=symbol,
                valid=False,
                action="NO_H4_CONTEXT",
                state="NO_H4_CONTEXT",
                direction=None,
                reason=h4_context["reason"],
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=None,
                m15=None,
                m5=None,
                diagnostics=diagnostics,
            )

        if self.config.require_h4_h1_convergence:
            self._add_transition(
                transitions,
                "H4_CONTEXT_READY",
                h4_context["reason"],
                trend=h4_trend,
                direction=h4_direction,
                context_time=h4_context.get("context_time"),
            )

        # --------------------------------------------------------
        # H1
        # --------------------------------------------------------

        h1_data, h1_result, h1_timing = self._get_stage_result(
            symbol,
            self.config.structure_timeframe,
            self.config.structure_candles,
        )

        h1_context = self._get_h1_context(
            h1_result
        )

        location_direction = None
        if self.config.h1_location_only:
            zone_data, _, _ = self._get_stage_result(symbol, self.config.entry_timeframe, self.config.entry_candles)
            bounds = get_h1_structural_range_flexible(h1_data, self.pipeline_config.h1_fractal_left,
                    self.pipeline_config.h1_fractal_right, self.pipeline_config.h1_fallback_bars)
            macro_context = evaluate_h1_adaptive_context(h1_data,
                float(zone_data.iloc[-1]['close']) if not zone_data.empty else float('nan'), bounds)
            location_direction = macro_context.get('direction')
            location_detail = macro_context['reason']
            if bounds:
                bounds = dict(bounds, adaptive_context_enabled=True,
                              active_context_type=macro_context['context_type'],
                              source=macro_context.get('source'), expansion_retest_tolerance=0.002)
            h1_context['adaptive_context'] = macro_context
            h1_context.update(valid=location_direction is not None, location_detail=location_detail,
                              role="LOCATION_ONLY", location_direction=location_direction, structural_range=bounds,
                              reason="H1_LOCATION_READY" if location_direction else "H1_LOCATION_UNAVAILABLE_OR_EQUILIBRIUM")

        h1_diag = self._pipeline_diagnostics(
            h1_result, h1_timing
        )

        h1_payload = {
            "timeframe": self.config.structure_timeframe,
            "context": h1_context,
            "summary": h1_result.get("summary", {}),
        }

        if (
            self.config.require_h1_trend
            and not h1_context["valid"]
        ):
            self._add_transition(
                transitions,
                "NO_H1_CONTEXT",
                h1_context["reason"],
            )

            diagnostics = {
                "failed_stage": "H1",
                "h4": h4_diag,
                "h1": h1_diag,
                "direction_policy": policy_diag,
                "transitions": transitions,
            }

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="NO_H1_CONTEXT",
                state="NO_H1_CONTEXT",
                direction=None,
                reason=h1_context["reason"],
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=None,
                m5=None,
                diagnostics=diagnostics,
            )

        h1_trend = h1_context["trend"]

        h1_direction = location_direction if self.config.h1_location_only else self._trend_direction(h1_trend)

        self._add_transition(
            transitions,
            "H1_CONTEXT_READY",
            h1_context["reason"],
            trend=h1_trend,
            direction=h1_direction,
            context_time=h1_context.get(
                "context_time"
            ),
        )

        if (
            self.config.require_h4_h1_convergence
            and h4_direction != h1_direction
        ):
            reason = "H4_H1_TREND_DIVERGENCE"
            self._add_transition(
                transitions,
                "HTF_TREND_DIVERGENCE",
                reason,
                h4_trend=h4_trend,
                h4_direction=h4_direction,
                h1_trend=h1_trend,
                h1_direction=h1_direction,
            )
            diagnostics = {
                "failed_stage": "H4_H1_CONVERGENCE",
                "h4": h4_diag,
                "h1": h1_diag,
                "direction_policy": policy_diag,
                "transitions": transitions,
            }
            return self._build_result(
                symbol=symbol,
                valid=False,
                action="HTF_TREND_DIVERGENCE",
                state="HTF_TREND_DIVERGENCE",
                direction=None,
                reason=reason,
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=None,
                m5=None,
                diagnostics=diagnostics,
            )

        if self.config.require_h4_h1_convergence:
            self._add_transition(
                transitions,
                "H4_H1_CONVERGENCE_CONFIRMED",
                "H4_H1_SAME_DIRECTION",
                h4_direction=h4_direction,
                h1_direction=h1_direction,
            )

        # --------------------------------------------------------
        # DIRECCIÓN
        # --------------------------------------------------------

        expected_direction = (
            policy.allowed_direction
            or h1_direction
        )

        # Confluencia opcional: Doji H1 reciente en un extremo compatible con
        # la dirección. No bloquea ninguna entrada si está ausente.
        h1_doji = detect_h1_extreme_doji(
            h1_result.get("data"),
            direction=expected_direction,
            config=H1ExtremeDojiConfig(
                enabled=bool(getattr(self.pipeline_config, "h1_doji_enabled", True)),
                lookback_candles=int(getattr(self.pipeline_config, "h1_doji_lookback_candles", 100)),
                max_age_candles=int(getattr(self.pipeline_config, "h1_doji_max_age_candles", 2)),
                max_body_ratio=float(getattr(self.pipeline_config, "h1_doji_max_body_ratio", 0.10)),
                extreme_fraction=float(getattr(self.pipeline_config, "h1_doji_extreme_fraction", 0.15)),
                min_rejection_wick_ratio=float(getattr(self.pipeline_config, "h1_doji_min_rejection_wick_ratio", 0.35)),
                bonus_points=float(getattr(self.pipeline_config, "h1_doji_bonus_points", 5.0)),
            ),
        )
        h1_payload["doji_extreme"] = h1_doji
        if h1_doji.get("h1_doji_confirmation"):
            self._add_transition(
                transitions,
                "H1_EXTREME_DOJI_CONFIRMED",
                h1_doji.get("h1_doji_reason") or "DOJI_H1_EXTREMO_CONFIRMADO",
                doji_type=h1_doji.get("h1_doji_type"),
                doji_time=h1_doji.get("h1_doji_time"),
                zone=h1_doji.get("h1_doji_zone"),
                direction=expected_direction,
            )

        if (
            policy.allowed_direction
            and h1_direction != policy.allowed_direction
        ):
            reason = (
                f"{policy.reason}_REQUIRES_"
                f"{policy.allowed_direction}_H1_CONTEXT"
            )

            self._add_transition(
                transitions,
                "DIRECTION_POLICY_BLOCKED",
                reason,
                h1_direction=h1_direction,
                required_direction=(
                    policy.allowed_direction
                ),
            )

            diagnostics = {
                "failed_stage": "DIRECTION_POLICY",
                "h4": h4_diag,
                "h1": h1_diag,
                "direction_policy": policy_diag,
                "transitions": transitions,
            }

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="DIRECTION_POLICY_BLOCKED",
                state="DIRECTION_POLICY_BLOCKED",
                direction=h1_direction,
                reason=reason,
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=None,
                m5=None,
                diagnostics=diagnostics,
            )

        self._add_transition(
            transitions,
            "DIRECTION_VALIDATED",
            "DIRECTION_POLICY_ACCEPTED",
            h1_direction=h1_direction,
            expected_direction=expected_direction,
            allowed_direction=(
                policy.allowed_direction
            ),
        )

        # --------------------------------------------------------
        # M15
        # --------------------------------------------------------

        m15_data, m15_result, m15_timing = self._get_stage_result(
            symbol,
            self.config.confirmation_timeframe,
            self.config.confirmation_candles,
        )

        m15_setups = self._m15_setups(
            m15_result,
            expected_direction,
        )

        if self.config.h1_location_only:
            if bounds and not m15_setups.empty:
                midpoint = (m15_setups.ob_low + m15_setups.ob_high) / 2
                located = midpoint.map(lambda price: h1_ob_location_valid(price, h1_direction, bounds))
                m15_setups = m15_setups.loc[located].copy()
                m15_setups['zone'] = 'discount' if h1_direction == 'BUY' else 'premium'
                m15_setups['premium_discount_ok'] = True
                m15_setups['equilibrium'] = bounds['equilibrium']
            elif not bounds:
                m15_setups = m15_setups.iloc[:0].copy()
        m15_diag = self._pipeline_diagnostics(
            m15_result, m15_timing
        )

        m15_diag['m15_block_audit'] = [
            {**item, 'accepted': False,
             'reasons': list(item['reasons']) + ['M15_DIRECTION_DIFFERS_FROM_H1_LOCATION']}
            if item.get('direction') != expected_direction else dict(item)
            for item in m15_diag.get('m15_block_audit', [])
        ]
        if self.config.h1_location_only:
            for item in m15_diag.get('m15_block_audit', []):
                mid = (item['ob_low'] + item['ob_high']) / 2
                valid_location = bool(bounds and h1_ob_location_valid(mid, item['direction'], bounds))
                if not valid_location:
                    item['accepted'] = False
                    item['reasons'] = list(item['reasons']) + ['M15_OB_H1_LOCATION_MISMATCH']
        m15_payload = {
            "timeframe": (
                self.config.confirmation_timeframe
            ),
            "setup": None,
            "summary": (
                m15_result.get("summary", {})
            ),
        }

        if (
            self.config.require_m15_setup
            and m15_setups.empty
        ):
            self._add_transition(
                transitions,
                "NO_M15_SETUP",
                "NO_DIRECTIONAL_M15_SETUP",
                expected_direction=expected_direction,
            )

            diagnostics = {
                "failed_stage": "M15",
                "h4": h4_diag,
                "h1": h1_diag,
                "m15": m15_diag,
                "direction_policy": policy_diag,
                "transitions": transitions,
            }

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="NO_M15_SETUP",
                state="NO_M15_SETUP",
                direction=expected_direction,
                reason="NO_DIRECTIONAL_M15_SETUP",
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=m15_payload,
                m5=None,
                diagnostics=diagnostics,
            )

        latest_m15_setup = (
            m15_setups.iloc[-1].to_dict()
            if not m15_setups.empty
            else None
        )

        m15_payload["setup"] = latest_m15_setup

        latest_setup_time = None

        if latest_m15_setup is not None:
            parsed_setup_time = self._as_time(
                latest_m15_setup.get("setup_time")
            )

            if parsed_setup_time is not None:
                latest_setup_time = (
                    parsed_setup_time.isoformat()
                )

        self._add_transition(
            transitions,
            "M15_SETUP_READY",
            "DIRECTIONAL_M15_SETUP_FOUND",
            expected_direction=expected_direction,
            total_setups=int(len(m15_setups)),
            latest_setup_time=latest_setup_time,
        )

        # --------------------------------------------------------
        # ESPERA DE M5
        # --------------------------------------------------------

        self._add_transition(
            transitions,
            "WAITING_M5_CONFIRMATION",
            "M15_SETUP_READY_WAITING_FOR_M5_CONFIRMATION",
            expected_direction=expected_direction,
        )

        # --------------------------------------------------------
        # M5
        # --------------------------------------------------------

        m5_data, m5_result, m5_timing = self._get_stage_result(
            symbol,
            self.config.entry_timeframe,
            self.config.entry_candles,
        )

        if self.config.h1_location_only:
            # Confirm the selected M15 zone, not an unrelated setup rebuilt on M5.
            selected = m15_setups.tail(1) if self.config.require_latest_m15_setup else m15_setups
            selected = selected.copy()
            selected['h1_location_direction'] = h1_direction
            selected['h1_range_source'] = 'FALLBACK_24H' if bounds.get('fallback_used') else 'PIVOT'
            selected['h1_adaptive_bounds'] = [dict(bounds) for _ in range(len(selected))]
            selected['h1_context_type'] = macro_context['context_type']
            selected['h1_range_low'] = bounds['low']
            selected['h1_range_high'] = bounds['high']
            m5_result = run_trade_pipeline(
                df=m5_data, symbol=symbol, confirmation_setups=selected,
                config=replace(self.pipeline_config, require_m5_structure_event=True,
                               require_favorable_confirmation=False, require_choch_fvg=False,
                               adaptive_smc_score_enabled=True,
                               m5_evaluation_time=pd.Timestamp.now(tz="UTC").isoformat(),
                               require_fvg=False, fvg_enabled=True, require_chart_pattern=False,
                               block_material_chart_pattern_conflict=False,
                               block_similar_chart_pattern_forces=False),
            )

        m5_confirmations = self._m5_confirmations(
            m5_result,
            expected_direction,
        )

        m5_diag = self._pipeline_diagnostics(
            m5_result, m5_timing
        )

        (
            m15_setup,
            m5_signal,
            sequence_status,
            sequence_diag,
        ) = self._select_ordered_pair(
            m15_setups,
            m5_confirmations,
        )

        # El Doji H1 suma calidad solamente cuando existe una señal M5 ya
        # confirmada. No entra en el denominador del 80% y su ausencia nunca
        # invalida la operación.
        if m5_signal is not None:
            m5_signal = dict(m5_signal)
            m5_signal.update(h1_doji)
            confirmations = dict(m5_signal.get("confirmations") or {})
            confirmations["h1_extreme_doji_confirmation"] = bool(h1_doji.get("h1_doji_confirmation"))
            m5_signal["confirmations"] = confirmations
            if h1_doji.get("h1_doji_confirmation"):
                bonus = float(getattr(self.pipeline_config, "h1_doji_bonus_points", 5.0))
                score = self._safe_float(m5_signal.get("trade_score")) or 0.0
                score = min(100.0, score + bonus)
                m5_signal["trade_score"] = round(score, 2)
                m5_signal["trade_grade"] = "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "REJECT"

        age_diag = self._signal_age_diagnostics(
            m5_data,
            m5_signal,
        )

        m15_payload["setup"] = m15_setup

        m5_payload = {
            "timeframe": self.config.entry_timeframe,
            "signal": m5_signal,
            "summary": m5_result.get("summary", {}),
        }

        common_diagnostics = {
            "h4": h4_diag,
            "h1": h1_diag,
            "m15": m15_diag,
            "m5": m5_diag,
            "sequence_status": sequence_status,
            "sequence": sequence_diag,
            "signal_age": age_diag,
            "stage_timing": {"H1": h1_timing, "M15": m15_timing, "M5": m5_timing},
            "direction_policy": policy_diag,
            "h1_extreme_doji": h1_doji,
            "transitions": transitions,
        }

        # --------------------------------------------------------
        # M5 EXISTE, PERO ES ANTERIOR AL SETUP M15
        # --------------------------------------------------------

        if sequence_status == "STALE_M5_CONFIRMATIONS":
            reason = (
                "M5_CONFIRMATIONS_EXIST_BUT_ALL_"
                "PRECEDE_LATEST_M15_SETUP"
            )

            self._add_transition(
                transitions,
                "WAITING_M5_AFTER_M15",
                reason,
                selected_setup_time=(
                    sequence_diag.get(
                        "selected_setup_time"
                    )
                ),
                total_m5_confirmations=(
                    sequence_diag.get(
                        "m5_confirmations_total"
                    )
                ),
            )

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="WAITING_M5_AFTER_M15",
                state="WAITING_M5_AFTER_M15",
                direction=expected_direction,
                reason=reason,
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=m15_payload,
                m5=m5_payload,
                diagnostics=common_diagnostics,
            )

        # --------------------------------------------------------
        # NO HAY CONFIRMACIÓN M5
        # --------------------------------------------------------

        if (
            self.config.require_m5_confirmation
            and m5_signal is None
        ):
            self._add_transition(
                transitions,
                "NO_M5_CONFIRMATION",
                "NO_DIRECTIONAL_M5_CONFIRMATION",
                expected_direction=expected_direction,
                sequence_status=sequence_status,
            )

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="NO_M5_CONFIRMATION",
                state="NO_M5_CONFIRMATION",
                direction=expected_direction,
                reason="NO_DIRECTIONAL_M5_CONFIRMATION",
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=m15_payload,
                m5=m5_payload,
                diagnostics=common_diagnostics,
            )

        # --------------------------------------------------------
        # CONFIRMACIÓN M5 ENCONTRADA
        # --------------------------------------------------------

        self._add_transition(
            transitions,
            "M5_CONFIRMATION_READY",
            "VALID_M5_CONFIRMATION_FOUND",
            selected_setup_time=(
                sequence_diag.get(
                    "selected_setup_time"
                )
            ),
            confirmation_time=(
                sequence_diag.get(
                    "selected_confirmation_time"
                )
            ),
            eligible_confirmations=(
                sequence_diag.get(
                    "eligible_confirmations"
                )
            ),
        )

        # --------------------------------------------------------
        # SEÑAL M5 ANTIGUA
        # --------------------------------------------------------

        if age_diag.get("is_stale"):
            self._add_transition(
                transitions,
                "STALE_M5_SIGNAL",
                "M5_CONFIRMATION_TOO_OLD_FOR_LIVE_ENTRY",
                signal_time=age_diag.get(
                    "signal_time"
                ),
                age_candles=age_diag.get(
                    "age_candles"
                ),
                age_minutes=age_diag.get(
                    "age_minutes"
                ),
                max_age_candles=age_diag.get(
                    "max_age_candles"
                ),
                max_age_minutes=age_diag.get(
                    "max_age_minutes"
                ),
            )

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="STALE_M5_SIGNAL",
                state="STALE_M5_SIGNAL",
                direction=expected_direction,
                reason=(
                    "M5_CONFIRMATION_TOO_OLD_FOR_LIVE_ENTRY"
                ),
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=m15_payload,
                m5=m5_payload,
                diagnostics=common_diagnostics,
            )

        # --------------------------------------------------------
        # SEÑAL M5 FRESCA
        # --------------------------------------------------------

        self._add_transition(
            transitions,
            "M5_SIGNAL_FRESH",
            "M5_CONFIRMATION_IS_FRESH",
            signal_time=age_diag.get(
                "signal_time"
            ),
            age_candles=age_diag.get(
                "age_candles"
            ),
            age_minutes=age_diag.get(
                "age_minutes"
            ),
        )

        # --------------------------------------------------------
        # VALIDACIÓN FINAL DE DIRECCIÓN
        # --------------------------------------------------------

        direction = str(
            m5_signal.get("direction", "")
        ).upper()

        if direction not in {"BUY", "SELL"}:
            self._add_transition(
                transitions,
                "INVALID_DIRECTION",
                "M5_DIRECTION_NOT_BUY_OR_SELL",
                signal_direction=direction,
            )

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="INVALID_DIRECTION",
                state="INVALID_DIRECTION",
                direction=direction,
                reason="M5_DIRECTION_NOT_BUY_OR_SELL",
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=m15_payload,
                m5=m5_payload,
                diagnostics=common_diagnostics,
            )

        if (
            policy.allowed_direction
            and direction != policy.allowed_direction
        ):
            reason = (
                f"{policy.reason}_REJECTED_SIGNAL_DIRECTION"
            )

            self._add_transition(
                transitions,
                "DIRECTION_POLICY_BLOCKED",
                reason,
                signal_direction=direction,
                required_direction=(
                    policy.allowed_direction
                ),
            )

            return self._build_result(
                symbol=symbol,
                valid=False,
                action="DIRECTION_POLICY_BLOCKED",
                state="DIRECTION_POLICY_BLOCKED",
                direction=direction,
                reason=reason,
                transitions=transitions,
                policy_diag=policy_diag,
                h4=h4_payload,
                h1=h1_payload,
                m15=m15_payload,
                m5=m5_payload,
                diagnostics=common_diagnostics,
            )

        if self.config.smc_entry_location_enabled or (
            self.config.volatility_entry_location_enabled and "volatility" in symbol.lower()
        ):
            ranges = {
                "H1": get_h1_structural_range_flexible(h1_data, self.pipeline_config.h1_fractal_left,
                    self.pipeline_config.h1_fractal_right, self.pipeline_config.h1_fallback_bars),
                "M15": closed_range(m15_data, self.pipeline_config.premium_discount_lookback),
                "M5": closed_range(m5_data, self.pipeline_config.premium_discount_lookback),
            }
            if self.config.h1_location_only:
                ranges['H1'] = bounds
            location = evaluate_entry_location(direction, m5_data.iloc[-1]["close"], ranges, self.config.smc_entry_location_policy)
            common_diagnostics["entry_location_comparison"] = {
                policy: evaluate_entry_location(direction, m5_data.iloc[-1]["close"], ranges, policy)
                for policy in ("ALL_TIMEFRAMES", "H1_PRIMARY")
            }
            common_diagnostics["entry_location"] = location
            m5_signal["entry_location_ranges"] = ranges
            m5_signal["entry_location"] = location
            if not location["valid"]:
                reason = ",".join(location["rejection_reasons"])
                self._add_transition(transitions, "ENTRY_LOCATION_BLOCKED", reason)
                return self._build_result(
                    symbol=symbol, valid=False, action="ENTRY_LOCATION_BLOCKED",
                    state="ENTRY_LOCATION_BLOCKED", direction=direction, reason=reason,
                    transitions=transitions, policy_diag=policy_diag, h4=h4_payload,
                    h1=h1_payload, m15=m15_payload, m5=m5_payload,
                    diagnostics=common_diagnostics,
                )

        # --------------------------------------------------------
        # READY TO ENTER
        # --------------------------------------------------------

        self._add_transition(
            transitions,
            "READY_TO_ENTER",
            "MULTI_TIMEFRAME_SIGNAL_VALIDATED",
            direction=direction,
            entry_time=m5_signal.get(
                "entry_time"
            ),
            entry_price=m5_signal.get(
                "entry_price"
            ),
        )

        from strategy.smc.target_obstacles import collect_obstacles
        m5_signal["m15_obstacles"] = collect_obstacles(m15_result.get("data"), direction)
        # Capture native indicator values at the confirmed candle, not later prices.
        m5_signal["m15_structure_break_type"] = m15_setup.get("structure_break_type")
        indicator_data = m5_result.get("data")
        if indicator_data is not None and not indicator_data.empty:
            at_signal = indicator_data[pd.to_datetime(indicator_data["time"], utc=True) == pd.to_datetime(m5_signal.get("entry_time"), utc=True)]
            if not at_signal.empty:
                for indicator in ("atr", "adx"):
                    value = self._safe_float(at_signal.iloc[-1].get(indicator))
                    if value is not None:
                        m5_signal[indicator] = value

        m5_signal["indicator_provenance"] = {"timeframe": "M5", "period": 14,
            "method": "WILDER_SMA_SEED", "candle_open": str(m5_signal.get("entry_time")),
            "closed_candles_only": True}

        common_diagnostics["transitions"] = transitions

        extra = {
            "h4_timeframe": self.config.higher_timeframe,
            "h4_trend": h4_trend,
            "h4_h1_convergence": (h4_direction == h1_direction) if self.config.require_h4_h1_convergence else None,
            "entry_time": m5_signal["entry_time"],
            "entry_price": float(
                m5_signal["entry_price"]
            ),
            "stop_loss": float(
                m5_signal["stop_loss"]
            ),
            "take_profit": float(
                m5_signal["take_profit"]
            ),
            "risk_reward_ratio": float(
                m5_signal["risk_reward_ratio"]
            ),
            "signal": m5_signal,

            "h1_timeframe": (
                self.config.structure_timeframe
            ),
            "h1_trend": h1_trend,

            "m15_timeframe": (
                self.config.confirmation_timeframe
            ),
            "m15_setup_time": (
                m15_setup.get("setup_time")
            ),
            "m15_setup_type": (
                m15_setup.get("setup_type")
            ),
            "m15_ob_high": self._safe_float(
                m15_setup.get("ob_high")
            ),
            "m15_ob_low": self._safe_float(
                m15_setup.get("ob_low")
            ),
            "m15_zone": m15_setup.get(
                "zone"
            ),
            "m15_sweep_time": m15_setup.get(
                "sweep_time"
            ),
            "m15_structure_break_type": (
                m15_setup.get(
                    "structure_break_type"
                )
            ),

            "m5_timeframe": (
                self.config.entry_timeframe
            ),
            "m5_confirmation_time": (
                m5_signal.get("entry_time")
            ),
            "m5_confirmation_type": (
                m5_signal.get(
                    "confirmation_type"
                )
            ),
            "m5_trade_score": self._safe_float(m5_signal.get("trade_score")),
            "m5_trade_grade": m5_signal.get("trade_grade"),
            "m5_confirmation_decision": m5_signal.get("confirmation_decision"),
            "m5_confirmation_percentage": self._safe_float(m5_signal.get("confirmation_percentage")),
            "m5_confirmations_passed": m5_signal.get("confirmations_passed"),
            "m5_confirmations_total": m5_signal.get("confirmations_total"),
            "m5_missing_confirmations": m5_signal.get("missing_confirmations", []),
            "m5_critical_confirmations_ok": m5_signal.get("critical_confirmations_ok"),
            "m5_critical_confirmation_failures": m5_signal.get("critical_confirmation_failures", []),
            "m5_confirmation_reasons": m5_signal.get("rejection_reasons", []),
            "m5_ob_touches": m5_signal.get("ob_touches"),
            "m5_confirmation_details": m5_signal.get("confirmations", {}),
            "m5_divergence_confirmation": m5_signal.get("divergence_confirmation", False),
            "m5_divergence_type": m5_signal.get("divergence_type"),
            "m5_divergence_reason": m5_signal.get("divergence_reason"),
            "h1_doji_confirmation": m5_signal.get("h1_doji_confirmation", False),
            "h1_doji_type": m5_signal.get("h1_doji_type"),
            "h1_doji_time": m5_signal.get("h1_doji_time"),
            "h1_doji_zone": m5_signal.get("h1_doji_zone"),
            "h1_doji_reason": m5_signal.get("h1_doji_reason"),

            "config": asdict(self.config),
        }

        return self._build_result(
            symbol=symbol,
            valid=True,

            # Mantener para compatibilidad.
            action="MULTI_TIMEFRAME_SIGNAL",

            # Nuevo estado explícito.
            state="READY_TO_ENTER",

            direction=direction,
            reason="MULTI_TIMEFRAME_SIGNAL_VALIDATED",

            transitions=transitions,
            policy_diag=policy_diag,

            h4=h4_payload,
            h1=h1_payload,
            m15=m15_payload,
            m5=m5_payload,

            diagnostics=common_diagnostics,
            extra=extra,
        )

    # ============================================================
    # CONVERSIÓN SEGURA
    # ============================================================

    @staticmethod
    def _safe_float(value):
        """Convierte a float devolviendo `None` ante nulos, NaN o basura.

        Devuelve `None` en lugar de 0.0 a proposito: un precio ausente no es
        un precio de cero, y confundirlos produciria stops absurdos.
        """
        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
