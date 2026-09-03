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
        self.execution_provider = execution_provider
        self.magic = int(magic)
        self.deviation = int(deviation)

    def execute_trade(self, request: TradeExecutionRequest) -> TradeExecutionResult:
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
            volume=float(request.volume),
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
        raw = request.metadata.get("execution_key") if request.metadata else None
        if raw:
            return str(raw)[:31]
        return f"smc:{request.symbol}:{request.direction}"[:31]
