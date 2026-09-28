"""Adaptador de MT5 al contrato generico `TradeExecutor`.

Permite que el motor trabaje siempre contra la misma interfaz, tanto si opera
en MT5 real como en papel. Aqui no hay logica de estrategia: solo traduccion
entre `TradeExecutionRequest`/`TradeExecutionResult` y las llamadas nativas.

El import de `MetaTrader5` es tolerante a fallo para poder importar el proyecto
y ejecutar los tests fuera de Windows; los metodos que lo necesitan comprueban
`mt5 is None` y lanzan un error claro.

Vinculaciones:
    - `strategy.execution.trade_executor`: contrato y constantes de estado.
    - `execution_provider`: instancia de `brokers.mt5_execution`, que hace el
      trabajo de bajo nivel.
    - Consumidores: `app.main` y `services.live_demo_smoke_test_service`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

try:
    import MetaTrader5 as mt5
except ModuleNotFoundError:  # permite importar el proyecto fuera de Windows/MT5
    mt5 = None

from strategy.execution.trade_executor import (
    EXECUTION_STATUS_CLOSED,
    EXECUTION_STATUS_FILLED,
    TradeExecutionRequest,
    TradeExecutionResult,
    TradeExecutor,
)


class MT5TradeExecutor(TradeExecutor):
    """Adaptador del proveedor MT5 al contrato TradeExecutor.

    Esta clase no contiene lógica de estrategia. Su única responsabilidad es
    traducir TradeExecutionRequest/Result hacia operaciones reales de MT5.
    """

    BROKER_NAME = "MT5"

    def __init__(self, execution_provider, magic: int, deviation: int = 20):
        """Configura el adaptador.

        Args:
            execution_provider: capa de bajo nivel (`brokers.mt5_execution`).
            magic: identificador del bot en las ordenes; permite que varios
                workers convivan en la misma cuenta sin tocar posiciones ajenas.
            deviation: desviacion maxima de precio tolerada, en puntos.
        """
        self.execution_provider = execution_provider
        self.magic = int(magic)
        self.deviation = int(deviation)

    def execute_trade(self, request: TradeExecutionRequest) -> TradeExecutionResult:
        """Envia una orden a mercado y devuelve el resultado normalizado.

        Antes de nada llama a `assert_demo_account()`: es la salvaguarda que
        impide enviar ordenes a una cuenta real por error.

        Tras el envio localiza el ticket de posicion por comentario y, si no
        aparece, lo deriva del ticket del deal. El comentario que genera
        `_comment_for` incorpora la `execution_key`, lo que hace la operacion
        rastreable e idempotente extremo a extremo.

        Raises:
            RuntimeError: si `MetaTrader5` no esta disponible en el entorno.
        """
        if mt5 is None:
            raise RuntimeError("MetaTrader5 no está disponible en este entorno")
        self.execution_provider.assert_demo_account()

        comment = self._comment_for(request)
        placed = self.execution_provider.place_market_order(
            symbol=request.symbol,
            direction=request.direction,
            volume=float(request.volume),
            stop_loss=float(request.stop_loss),
            take_profit=float(request.take_profit),
            magic=self.magic,
            comment=comment,
            deviation=self.deviation,
            **({"max_risk_amount": request.metadata["pre_send_risk_cap"]}
               if request.metadata and "pre_send_risk_cap" in request.metadata else {}),
            **({"minimum_executable_rr": request.metadata["minimum_executable_rr"]}
               if request.metadata.get("minimum_executable_rr") is not None else {}),
        )

        position_ticket = (
            self.execution_provider.find_position_ticket(
                request.symbol,
                self.magic,
                comment,
            )
            or self.execution_provider.position_ticket_from_deal(
                placed.get("deal_ticket")
            )
        )

        if position_ticket is None:
            raise RuntimeError(
                "MT5 confirmó la ejecución, pero no se pudo resolver el ticket de posición"
            )

        execution_id = str(
            placed.get("deal_ticket")
            or placed.get("order_ticket")
            or position_ticket
        )

        return TradeExecutionResult(
            accepted=True,
            status=EXECUTION_STATUS_FILLED,
            execution_id=execution_id,
            broker=self.BROKER_NAME,
            symbol=request.symbol,
            timeframe=request.timeframe,
            direction=request.direction,
            volume=float(placed.get("filled_volume") or (placed.get("request") or {}).get("volume") or request.volume),
            requested_entry_price=float(request.entry_price),
            filled_price=float(placed.get("entry_price") or request.entry_price),
            stop_loss=float(request.stop_loss),
            take_profit=float(request.take_profit),
            execution_time=datetime.now(timezone.utc),
            position_ticket=str(position_ticket),
            reason="mt5_filled",
            metadata={
                "order_ticket": placed.get("order_ticket"),
                "deal_ticket": placed.get("deal_ticket"),
                "selected_filling": placed.get("selected_filling"),
                "selected_filling_name": placed.get("selected_filling_name"),
                "risk_resize": placed.get("risk_resize"),
                "executable_rr_audit": placed.get("executable_rr_audit"),
            },
        )

    def move_stop_loss(
        self,
        position_ticket: str,
        stop_loss: float,
        take_profit: float | None = None,
        reason: str = "break_even",
    ) -> dict:
        """
        Modifica el Stop Loss de una posición real sin cerrarla.

        El método se usa por el daemon para llevar el SL a Break Even cuando
        la posición alcanza el RR configurado.
        """
        if mt5 is None:
            raise RuntimeError("MetaTrader5 no está disponible en este entorno")

        result = self.execution_provider.modify_position_stops(
            position_ticket=int(position_ticket),
            stop_loss=float(stop_loss),
            take_profit=take_profit,
        )
        result["reason"] = str(reason)
        return result

    def get_position(self, position_ticket: str) -> Optional[dict]:
        """Estado actual de una posicion, normalizado a dict.

        Returns:
            dict con direccion, volumen, precios de entrada y actual, SL, TP y
            PnL flotante; o `None` si la posicion ya no existe (normalmente
            porque se cerro).
        """
        row = self.execution_provider.get_position(int(position_ticket))
        if row is None:
            return None

        return {
            "position_ticket": str(getattr(row, "ticket", position_ticket)),
            "symbol": str(getattr(row, "symbol", "")),
            "direction": (
                "BUY"
                if int(getattr(row, "type", -1)) == int(mt5.POSITION_TYPE_BUY)
                else "SELL"
            ),
            "volume": float(getattr(row, "volume", 0.0)),
            "entry_price": float(getattr(row, "price_open", 0.0)),
            "current_price": float(getattr(row, "price_current", 0.0)),
            "stop_loss": float(getattr(row, "sl", 0.0)),
            "take_profit": float(getattr(row, "tp", 0.0)),
            "floating_pnl_money": float(getattr(row, "profit", 0.0)),
            "status": EXECUTION_STATUS_FILLED,
        }

    def close_position(
        self,
        position_ticket: str,
        exit_price: Optional[float] = None,
        reason: str = "manual_close",
    ) -> dict:
        """Cierra una posicion abierta enviando la orden opuesta.

        Si la posicion ya no existe devuelve `closed: True` con motivo
        `already_closed`, comportamiento idempotente que evita errores cuando
        el broker cerro por SL/TP entre la decision y la ejecucion.

        Prueba secuencialmente los modos de llenado que admite el simbolo,
        porque no todos los brokers aceptan el mismo, y acumula cada intento en
        `attempts` para poder diagnosticar el rechazo.

        Args:
            position_ticket: ticket de la posicion.
            exit_price: precio deseado; si es `None` toma bid o ask segun la
                direccion del cierre.
            reason: motivo, que viaja en el comentario de la orden (truncado a
                20 caracteres por el limite de MT5).

        Returns:
            dict con `closed`, precio de salida, motivo y los tickets.

        Raises:
            RuntimeError: si MT5 no esta disponible, si no hay tick, o si todos
                los modos de llenado fueron rechazados.
        """
        if mt5 is None:
            raise RuntimeError("MetaTrader5 no está disponible en este entorno")
        self.execution_provider._ensure()
        position = self.execution_provider.get_position(int(position_ticket))
        if position is None:
            return {
                "closed": True,
                "position_ticket": str(position_ticket),
                "reason": "already_closed",
            }

        symbol = str(position.symbol)
        volume = float(position.volume)
        direction = (
            "SELL"
            if int(position.type) == int(mt5.POSITION_TYPE_BUY)
            else "BUY"
        )
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"No hay tick para cerrar '{symbol}': {mt5.last_error()}")

        price = float(exit_price) if exit_price is not None else (
            float(tick.bid) if direction == "SELL" else float(tick.ask)
        )
        info = self.execution_provider.symbol_spec(symbol)
        candidates = self.execution_provider._symbol_filling_candidates(symbol)
        attempts = []

        for filling in candidates:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL if direction == "SELL" else mt5.ORDER_TYPE_BUY,
                "position": int(position.ticket),
                "price": self.execution_provider._normalize_price(price, int(info.digits)),
                "deviation": self.deviation,
                "magic": self.magic,
                "comment": f"close:{str(reason)[:20]}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": int(filling),
            }
            result = mt5.order_send(request)
            attempts.append({
                "filling": int(filling),
                "retcode": None if result is None else int(getattr(result, "retcode", -1)),
                "comment": None if result is None else str(getattr(result, "comment", "")),
            })
            if self.execution_provider._is_order_send_success(result):
                return {
                    "closed": True,
                    "position_ticket": str(position_ticket),
                    "exit_price": float(getattr(result, "price", 0.0) or price),
                    "reason": str(reason),
                    "deal_ticket": int(getattr(result, "deal", 0) or 0) or None,
                    "order_ticket": int(getattr(result, "order", 0) or 0) or None,
                    "attempts": attempts,
                }

        raise RuntimeError(f"MT5 rechazó el cierre: {attempts}; last_error={mt5.last_error()}")

    @staticmethod
    def _comment_for(request: TradeExecutionRequest) -> str:
        """Comentario de la orden, truncado a los 31 caracteres que admite MT5.

        Prefiere la `execution_key` de los metadatos: asi el comentario sirve
        despues para reencontrar la posicion y garantizar idempotencia. Como
        alternativa compone `smc:simbolo:direccion`.
        """
        raw = request.metadata.get("execution_key") if request.metadata else None
        if raw:
            return str(raw)[:31]
        return f"smc:{request.symbol}:{request.direction}"[:31]
