"""Prueba de humo de extremo a extremo sobre una cuenta MT5 DEMO.

Envia UNA orden real minima y recorre todo el circuito de produccion
(ejecucion -> ciclo de vida -> persistencia -> Excel) para confirmar que la
cadena completa funciona antes de dejar el bot operando solo.

No genera senales ni decide entradas: el instrumento, la direccion y las
distancias los fija la configuracion. El llamador debe haber pasado el
preflight y dado su confirmacion explicita.

Vinculaciones:
    - `brokers.mt5_trade_executor.MT5TradeExecutor`: envio de la orden.
    - `trade_lifecycle_manager.TradeLifecycleManager`: maquina de estados.
    - `reporting.trade_reporting_service`: persistencia y exportacion.
    - `app.main`: unico consumidor.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService
from brokers.mt5_trade_executor import MT5TradeExecutor
from trade_lifecycle_manager import TradeLifecycleManager


@dataclass
class LiveDemoSmokeTestConfig:
    """Parametros de la prueba.

    Attributes:
        symbol: instrumento a operar.
        direction: BUY o SELL.
        volume: lotes; si es 0 se usa el minimo del simbolo.
        timeframe: marco declarado en el registro de la operacion.
        rr: relacion riesgo/beneficio con la que se situa el TP.
        stop_distance_points: distancia del SL respecto a la entrada.
        stop_safety_points: margen extra sobre la distancia minima que exige el
            broker, para que la orden no sea rechazada por stop invalido.
        auto_close: cierra la posicion al terminar; conviene dejarlo en `True`
            para que la prueba no deje riesgo vivo.
        output_path: destino del XLSX generado.
    """

    symbol: str
    direction: str = "BUY"
    volume: float = 0.0
    timeframe: str = "M5"
    rr: float = 2.0
    stop_distance_points: int = 50
    stop_safety_points: int = 1000
    auto_close: bool = True
    output_path: str | Path | None = None


class LiveDemoSmokeTestService:
    """Prueba controlada de una única orden real en una cuenta MT5 DEMO.

    Requiere que el llamador haya ejecutado el preflight y haya dado una
    confirmación explícita. No genera señales ni decide entradas de estrategia.
    """

    def __init__(self, execution_provider, repository, config: LiveDemoSmokeTestConfig, magic=26082026, deviation=20):
        """Monta la misma cadena de componentes que usa el bot en produccion.

        Ejecutor MT5, servicio de reporting con origen DEMO y gestor de ciclo
        de vida: si la prueba pasa, esa cadena esta verificada de punta a punta.
        """
        self.execution_provider = execution_provider
        self.repository = repository
        self.config = config
        self.executor = MT5TradeExecutor(
            execution_provider=execution_provider,
            magic=magic,
            deviation=deviation,
        )
        self.reporting_service = TradeReportingService(
            repository=repository,
            config=TradeReportingConfig(
                source="DEMO",
                broker="MT5-DEMO",
                output_path=config.output_path,
                auto_export=True,
            ),
        )
        self.lifecycle_manager = TradeLifecycleManager(
            trade_executor=self.executor,
            reporting_service=self.reporting_service,
        )

    def run(self) -> dict:
        """Ejecuta la prueba completa y devuelve su resultado.

        Vuelve a exigir cuenta DEMO como ultima barrera, calcula SL y TP a
        partir de `point` y las distancias configuradas, normaliza el volumen
        al minimo operable, abre la posicion y, si `auto_close` esta activo, la
        cierra.

        Returns:
            dict con los datos de la operacion y la ruta del informe generado.

        Raises:
            ValueError / RuntimeError: si la direccion es invalida o el simbolo
                no informa un `point` utilizable.
        """
        self.execution_provider.assert_demo_account()
        symbol = str(self.config.symbol)
        direction = str(self.config.direction).upper()
        if direction not in {"BUY", "SELL"}:
            raise ValueError("direction debe ser BUY o SELL")

        # ensure_symbol() garantiza disponibilidad/selección. El proveedor de
        # ejecución devuelve allí un diccionario de metadatos, mientras que
        # normalize_volume() trabaja con el objeto SymbolInfo de MT5.
        self.execution_provider.ensure_symbol(symbol)
        info = self.execution_provider.symbol_spec(symbol)
        constraints = self.execution_provider.get_symbol_constraints(symbol)
        point = float(constraints.get("point") or 0.0)
        if point <= 0:
            raise RuntimeError("El símbolo no informa un point válido")

        volume = float(self.config.volume or constraints.get("volume_min") or 0.0)
        if volume <= 0:
            raise RuntimeError("No se pudo determinar un volumen válido")
        volume = self.executor.execution_provider.normalize_volume(volume, info)

        tick = self._tick(symbol)
        entry = float(tick["ask"] if direction == "BUY" else tick["bid"])

        # El smoke test no usa un SL estructural real. Generamos un SL inicial y
        # delegamos en el proveedor MT5 la normalización contra las restricciones
        # reales del broker (trade_stops_level, point y digits). Esto evita que
        # una configuración fija de puntos genere INVALID_STOPS en símbolos como
        # Boom 100 Index, cuyo mínimo de SL/TP puede ser muy superior a 50 puntos.
        requested_distance = max(
            int(self.config.stop_distance_points),
            1,
        ) * point
        requested_stop_loss = (
            entry - requested_distance
            if direction == "BUY"
            else entry + requested_distance
        )

        stops = self.execution_provider.normalize_market_stops(
            symbol=symbol,
            direction=direction,
            entry_price=entry,
            stop_loss=requested_stop_loss,
            risk_reward=float(self.config.rr),
            safety_points=max(0, int(self.config.stop_safety_points)),
        )
        if not stops.get("valid"):
            raise RuntimeError(
                "LIVE_DEMO_SMOKE_STOPS_INVALID: "
                f"reason={stops.get('reason')}; diagnostics={stops}"
            )

        stop_loss = float(stops["stop_loss"])
        take_profit = float(stops["take_profit"])

        signal = {
            "symbol": symbol,
            "timeframe": self.config.timeframe,
            "direction": direction,
            "entry_time": tick.get("time"),
            "entry_price": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward_ratio": float(self.config.rr),
            "action": "LIVE_DEMO_SMOKE_TEST",
        }

        lifecycle = self.lifecycle_manager.process_signal_with_executor(
            signal=signal,
            volume=volume,
        )
        broker_position = self.executor.get_position(lifecycle.position_ticket)
        report_path = self.reporting_service.exporter.output_path
        row = self.repository.get_trade_by_execution_key(lifecycle.execution_id)

        result = {
            "opened": True,
            "symbol": symbol,
            "direction": direction,
            "volume": volume,
            "execution_id": lifecycle.execution_id,
            "position_ticket": lifecycle.position_ticket,
            "broker_position_found": broker_position is not None,
            "sqlite_trade_found": row is not None,
            "xlsx": str(report_path),
            "stops": stops,
            "lifecycle": lifecycle,
        }

        if self.config.auto_close:
            close_result = self.lifecycle_manager.close_execution(
                lifecycle=lifecycle,
                reason="manual_close",
            )
            result["closed"] = True
            result["close_result"] = close_result
        else:
            result["closed"] = False

        return result

    @staticmethod
    def _tick(symbol: str) -> dict:
        """Precio actual del simbolo (bid/ask/last).

        Importa `MetaTrader5` de forma diferida para que el modulo se pueda
        importar en entornos sin el terminal.

        Raises:
            RuntimeError: si la libreria falta o no hay tick disponible.
        """
        try:
            import MetaTrader5 as mt5
        except ModuleNotFoundError as exc:
            raise RuntimeError("MetaTrader5 no está disponible en este entorno") from exc
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No hay tick para '{symbol}': {mt5.last_error()}")
        return {
            "bid": float(tick.bid),
            "ask": float(tick.ask),
            "time": getattr(tick, "time", None),
        }
