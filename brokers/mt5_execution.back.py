from __future__ import annotations

from datetime import datetime, timezone
import math

import MetaTrader5 as mt5


class MT5ExecutionError(RuntimeError):
    pass


class MT5ExecutionProvider:
    """Capa de ejecución para una cuenta MT5 ya conectada.

    Esta clase no contiene credenciales. MetaTrader 5 debe estar abierto y la
    cuenta Demo debe estar iniciada en el terminal.
    """

    def __init__(self, connector):
        self.connector = connector

    def _ensure(self):
        if not self.connector.is_connected():
            self.connector.connect()

    def account_info(self) -> dict:
        self._ensure()
        info = mt5.account_info()
        if info is None:
            raise MT5ExecutionError(
                f"No se pudo obtener la cuenta: {mt5.last_error()}"
            )

        return {
            "login": int(info.login),
            "server": str(info.server),
            "currency": str(info.currency),
            "balance": float(info.balance),
            "equity": float(info.equity),
            "margin": float(info.margin),
            "free_margin": float(info.margin_free),
            "profit": float(info.profit),
            "leverage": int(info.leverage),
            "trade_mode": int(info.trade_mode),
            "snapshot_time": datetime.now(timezone.utc),
            "broker": "MT5",
        }

    def assert_demo_account(self):
        account = self.account_info()
        demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", None)

        if demo_mode is not None and account["trade_mode"] != int(demo_mode):
            raise MT5ExecutionError(
                "La cuenta conectada no es DEMO. La ejecución automática de este "
                "modo está bloqueada para proteger una cuenta real."
            )

        return account

    def symbol_spec(self, symbol: str):
        self._ensure()
        info = mt5.symbol_info(symbol)

        if info is None:
            raise MT5ExecutionError(
                f"No existe el símbolo '{symbol}': {mt5.last_error()}"
            )

        return info

    @staticmethod
    def normalize_volume(volume: float, info, round_down: bool = True) -> float:
        step = float(info.volume_step or 0.0)
        vmin = float(info.volume_min or 0.0)
        vmax = float(info.volume_max or 0.0)

        if step <= 0 or vmin <= 0 or vmax <= 0:
            raise MT5ExecutionError(
                "El símbolo no informa límites de volumen válidos."
            )

        raw_steps = (float(volume) - vmin) / step
        steps = (
            math.floor(raw_steps + 1e-12)
            if round_down
            else round(raw_steps)
        )

        normalized = vmin + max(0, steps) * step
        normalized = min(max(normalized, vmin), vmax)

        decimals = max(
            0,
            int(round(-math.log10(step))) if step < 1 else 0,
        )

        return round(normalized, decimals + 2)

    def calculate_volume(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        risk_amount: float,
    ):
        self._ensure()
        info = self.symbol_spec(symbol)

        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            raise MT5ExecutionError("direction debe ser BUY o SELL")

        action = (
            mt5.ORDER_TYPE_BUY
            if direction == "BUY"
            else mt5.ORDER_TYPE_SELL
        )

        entry_price = float(entry_price)
        stop_loss = float(stop_loss)
        risk_amount = float(risk_amount)

        if risk_amount <= 0:
            raise MT5ExecutionError(
                "risk_amount debe ser mayor que cero."
            )

        risk_per_lot = None

        tick_size = float(
            getattr(info, "trade_tick_size", 0.0) or 0.0
        )
        tick_value = float(
            getattr(info, "trade_tick_value_loss", 0.0)
            or getattr(info, "trade_tick_value", 0.0)
            or 0.0
        )

        if tick_size > 0 and tick_value > 0:
            risk_per_lot = (
                abs(entry_price - stop_loss)
                / tick_size
                * tick_value
            )

        if not risk_per_lot or risk_per_lot <= 0:
            profit = mt5.order_calc_profit(
                action,
                symbol,
                1.0,
                entry_price,
                stop_loss,
            )

            if profit is None:
                raise MT5ExecutionError(
                    "No se pudo calcular el riesgo por lote: "
                    f"{mt5.last_error()}"
                )

            risk_per_lot = abs(float(profit))

        if risk_per_lot <= 0:
            raise MT5ExecutionError(
                "No se pudo calcular el riesgo por lote."
            )

        raw_volume = risk_amount / risk_per_lot

        min_volume = float(info.volume_min)
        max_volume = float(info.volume_max)
        step = float(info.volume_step)

        # No forzamos el volumen mínimo si excede el riesgo objetivo.
        min_risk = min_volume * risk_per_lot

        if min_risk > risk_amount + 1e-9:
            raise MT5ExecutionError(
                f"El volumen mínimo {min_volume} arriesga "
                f"{min_risk:.2f}, superior al riesgo permitido "
                f"{risk_amount:.2f}."
            )

        volume = self.normalize_volume(
            min(raw_volume, max_volume),
            info,
            round_down=True,
        )

        if volume < min_volume:
            raise MT5ExecutionError(
                "El volumen calculado quedó por debajo del mínimo permitido."
            )

        actual_risk = volume * risk_per_lot

        return {
            "volume": float(volume),
            "raw_volume": float(raw_volume),
            "risk_per_lot": float(risk_per_lot),
            "actual_risk_amount": float(actual_risk),
            "tick_size": tick_size,
            "tick_value": tick_value,
            "volume_min": min_volume,
            "volume_max": max_volume,
            "volume_step": step,
        }

    @staticmethod
    def _price_decimals(info) -> int:
        digits = int(getattr(info, "digits", 0) or 0)

        if digits > 0:
            return digits

        point = float(getattr(info, "point", 0.0) or 0.0)
        if point > 0:
            return max(
                0,
                int(round(-math.log10(point)))
                if point < 1
                else 0,
            )

        return 8

    @classmethod
    def _normalize_price(cls, price: float, info) -> float:
        return round(float(price), cls._price_decimals(info))

    @staticmethod
    def _minimum_stop_distance(info) -> float:
        point = float(getattr(info, "point", 0.0) or 0.0)
        stops_level = int(
            getattr(info, "trade_stops_level", 0) or 0
        )

        # Añadimos un punto de seguridad para evitar errores por redondeo.
        return (stops_level + 1) * point if point > 0 else 0.0

    def _normalize_stops(
        self,
        info,
        direction: str,
        tick,
        stop_loss: float | None,
        take_profit: float | None,
    ) -> tuple[float, float]:
        direction = str(direction).upper()

        if direction not in {"BUY", "SELL"}:
            raise MT5ExecutionError(
                "direction debe ser BUY o SELL"
            )

        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)

        if bid <= 0 or ask <= 0:
            raise MT5ExecutionError(
                "El tick recibido no contiene bid/ask válidos."
            )

        sl = float(stop_loss or 0.0)
        tp = float(take_profit or 0.0)

        if sl <= 0 or tp <= 0:
            raise MT5ExecutionError(
                "La orden requiere stop_loss y take_profit mayores que cero."
            )

        min_distance = self._minimum_stop_distance(info)

        if direction == "BUY":
            # Para BUY, el SL debe quedar suficientemente por debajo del BID
            # y el TP suficientemente por encima del ASK.
            max_valid_sl = bid - min_distance
            min_valid_tp = ask + min_distance

            if sl >= bid or sl > max_valid_sl:
                sl = max_valid_sl

            if tp <= ask or tp < min_valid_tp:
                tp = min_valid_tp

        else:
            # Para SELL, el SL debe quedar suficientemente por encima del ASK
            # y el TP suficientemente por debajo del BID.
            min_valid_sl = ask + min_distance
            max_valid_tp = bid - min_distance

            if sl <= ask or sl < min_valid_sl:
                sl = min_valid_sl

            if tp >= bid or tp > max_valid_tp:
                tp = max_valid_tp

        sl = self._normalize_price(sl, info)
        tp = self._normalize_price(tp, info)

        if direction == "BUY":
            if sl <= 0 or sl >= bid:
                raise MT5ExecutionError(
                    "No fue posible construir un SL válido para BUY."
                )
            if tp <= ask:
                raise MT5ExecutionError(
                    "No fue posible construir un TP válido para BUY."
                )
        else:
            if sl <= ask:
                raise MT5ExecutionError(
                    "No fue posible construir un SL válido para SELL."
                )
            if tp <= 0 or tp >= bid:
                raise MT5ExecutionError(
                    "No fue posible construir un TP válido para SELL."
                )

        return sl, tp

    def _allowed_fillings(self, info) -> list[int]:
        """Convierte el bitmask SYMBOL_FILLING_* a ORDER_FILLING_*.

        IMPORTANTE:
        info.filling_mode es una máscara de capacidades del símbolo.
        No debe enviarse directamente como type_filling.
        """

        mode = int(getattr(info, "filling_mode", 0) or 0)

        symbol_fok = int(
            getattr(mt5, "SYMBOL_FILLING_FOK", 1)
        )
        symbol_ioc = int(
            getattr(mt5, "SYMBOL_FILLING_IOC", 2)
        )

        fillings: list[int] = []

        if mode & symbol_ioc:
            fillings.append(mt5.ORDER_FILLING_IOC)

        if mode & symbol_fok:
            fillings.append(mt5.ORDER_FILLING_FOK)

        # RETURN no está representado como capability bit en filling_mode.
        # Se deja como último fallback porque algunos brokers lo aceptan
        # dependiendo del modo de ejecución.
        return_mode = getattr(mt5, "ORDER_FILLING_RETURN", None)
        if return_mode is not None:
            fillings.append(int(return_mode))

        # Eliminar duplicados preservando el orden.
        unique: list[int] = []
        for filling in fillings:
            if filling not in unique:
                unique.append(filling)

        if not unique:
            unique = [
                mt5.ORDER_FILLING_IOC,
                mt5.ORDER_FILLING_FOK,
            ]
            if return_mode is not None:
                unique.append(int(return_mode))

        return unique

    @staticmethod
    def _check_result_dict(check_result):
        if check_result is None:
            return {
                "valid": False,
                "retcode": None,
                "comment": "order_check devolvió None",
                "result": None,
            }

        retcode = int(getattr(check_result, "retcode", -1))
        comment = str(getattr(check_result, "comment", ""))

        return {
            "valid": retcode == 0,
            "retcode": retcode,
            "comment": comment,
            "result": check_result,
        }


    def get_symbol_constraints(self, symbol: str) -> dict:
        """Devuelve las restricciones reales informadas por MT5 para el símbolo."""
        self._ensure()
        info = self.symbol_spec(symbol)
        point = float(getattr(info, "point", 0.0) or 0.0)
        stops_level = int(getattr(info, "trade_stops_level", 0) or 0)
        return {
            "symbol": symbol,
            "digits": int(getattr(info, "digits", 0) or 0),
            "point": point,
            "stops_level_points": stops_level,
            "freeze_level_points": int(getattr(info, "trade_freeze_level", 0) or 0),
            "min_stop_distance": self._minimum_stop_distance(info),
            "volume_min": float(getattr(info, "volume_min", 0.0) or 0.0),
            "volume_max": float(getattr(info, "volume_max", 0.0) or 0.0),
            "volume_step": float(getattr(info, "volume_step", 0.0) or 0.0),
            "tick_size": float(getattr(info, "trade_tick_size", 0.0) or 0.0),
            "tick_value": float(getattr(info, "trade_tick_value", 0.0) or 0.0),
            "tick_value_loss": float(getattr(info, "trade_tick_value_loss", 0.0) or 0.0),
            "filling_mode_raw": int(getattr(info, "filling_mode", 0) or 0),
            "trade_exemode": int(getattr(info, "trade_exemode", 0) or 0),
        }

    def normalize_market_stops(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        risk_reward: float,
        safety_points: int = 2,
    ) -> dict:
        """
        Adapta SL/TP al precio actual y a la distancia mínima exigida por el broker.
        El TP se recalcula manteniendo el RR solicitado.
        """
        self._ensure()
        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            return {"valid": False, "reason": "INVALID_DIRECTION"}

        info = self.symbol_spec(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {
                "valid": False,
                "reason": "NO_MARKET_TICK",
                "last_error": mt5.last_error(),
            }

        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)
        if bid <= 0 or ask <= 0:
            return {"valid": False, "reason": "INVALID_MARKET_TICK", "bid": bid, "ask": ask}

        entry = float(entry_price)
        if entry <= 0:
            entry = ask if direction == "BUY" else bid

        point = float(getattr(info, "point", 0.0) or 0.0)
        min_distance = self._minimum_stop_distance(info)
        safety_distance = max(0, int(safety_points)) * point
        required_distance = min_distance + safety_distance

        requested_sl = float(stop_loss)
        rr = float(risk_reward)
        if rr <= 0:
            return {"valid": False, "reason": "INVALID_RISK_REWARD"}

        if direction == "BUY":
            max_sl = min(entry - required_distance, bid - required_distance)
            normalized_sl = min(requested_sl, max_sl)
            if normalized_sl <= 0 or normalized_sl >= entry:
                return {
                    "valid": False,
                    "reason": "INVALID_BUY_STOP",
                    "entry_price": entry,
                    "requested_stop_loss": requested_sl,
                    "required_distance": required_distance,
                }
            risk_distance = entry - normalized_sl
            normalized_tp = entry + risk_distance * rr
            min_tp = ask + required_distance
            normalized_tp = max(normalized_tp, min_tp)
        else:
            min_sl = max(entry + required_distance, ask + required_distance)
            normalized_sl = max(requested_sl, min_sl)
            if normalized_sl <= entry:
                return {
                    "valid": False,
                    "reason": "INVALID_SELL_STOP",
                    "entry_price": entry,
                    "requested_stop_loss": requested_sl,
                    "required_distance": required_distance,
                }
            risk_distance = normalized_sl - entry
            normalized_tp = entry - risk_distance * rr
            max_tp = bid - required_distance
            normalized_tp = min(normalized_tp, max_tp)
            if normalized_tp <= 0:
                return {"valid": False, "reason": "INVALID_SELL_TAKE_PROFIT"}

        normalized_sl = self._normalize_price(normalized_sl, info)
        normalized_tp = self._normalize_price(normalized_tp, info)

        return {
            "valid": True,
            "symbol": symbol,
            "direction": direction,
            "entry_price": self._normalize_price(entry, info),
            "stop_loss": normalized_sl,
            "take_profit": normalized_tp,
            "requested_stop_loss": requested_sl,
            "risk_distance": abs(entry - normalized_sl),
            "risk_reward": rr,
            "min_stop_distance": min_distance,
            "required_distance": required_distance,
            "bid": bid,
            "ask": ask,
        }

    def check_market_order(
        self,
        symbol: str,
        direction: str,
        volume: float,
        stop_loss: float,
        take_profit: float,
        magic: int,
        comment: str,
        deviation: int = 20,
    ) -> dict:
        """Ejecuta order_check sin enviar la orden y prueba los filling compatibles."""
        self._ensure()
        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            return {"valid": False, "reason": "INVALID_DIRECTION"}

        info = self.symbol_spec(symbol)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"valid": False, "reason": "NO_MARKET_TICK", "last_error": mt5.last_error()}

        price = float(tick.ask if direction == "BUY" else tick.bid)
        order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        normalized_volume = self.normalize_volume(float(volume), info, round_down=True)
        sl, tp = self._normalize_stops(info, direction, tick, stop_loss, take_profit)

        base = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": normalized_volume,
            "type": order_type,
            "price": self._normalize_price(price, info),
            "sl": sl,
            "tp": tp,
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": str(comment)[:31],
            "type_time": mt5.ORDER_TIME_GTC,
        }
        attempts = []
        for filling in self._allowed_fillings(info):
            request = {**base, "type_filling": int(filling)}
            check = mt5.order_check(request)
            check_info = self._check_result_dict(check)
            attempts.append({
                "filling": int(filling),
                "filling_name": self._filling_name(filling),
                "retcode": check_info["retcode"],
                "comment": check_info["comment"],
                "request": request,
            })
            if check_info["valid"]:
                return {
                    "valid": True,
                    "selected_filling": int(filling),
                    "selected_filling_name": self._filling_name(filling),
                    "request": request,
                    "result": check_info["result"],
                    "attempts": attempts,
                }
        return {
            "valid": False,
            "reason": attempts[-1]["comment"] if attempts else "NO_FILLING_MODE_AVAILABLE",
            "attempts": attempts,
        }

    def _symbol_filling_candidates(self, symbol: str) -> list[int]:
        return self._allowed_fillings(self.symbol_spec(symbol))

    @staticmethod
    def _is_order_send_success(result) -> bool:
        if result is None:
            return False
        success_codes = {
            int(getattr(mt5, "TRADE_RETCODE_DONE", -1)),
            int(getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", -2)),
            int(getattr(mt5, "TRADE_RETCODE_PLACED", -3)),
        }
        return int(getattr(result, "retcode", -999999)) in success_codes

    def place_market_order(
        self,
        symbol: str,
        direction: str,
        volume: float,
        stop_loss: float,
        take_profit: float,
        magic: int,
        comment: str,
        deviation: int = 20,
    ):
        self._ensure()

        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            raise ValueError(
                "direction debe ser BUY o SELL"
            )

        info = self.symbol_spec(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5ExecutionError(
                f"No hay tick para '{symbol}': {mt5.last_error()}"
            )

        bid = float(getattr(tick, "bid", 0.0) or 0.0)
        ask = float(getattr(tick, "ask", 0.0) or 0.0)

        if bid <= 0 or ask <= 0:
            raise MT5ExecutionError(
                f"Tick inválido para '{symbol}': bid={bid}, ask={ask}"
            )

        order_type = (
            mt5.ORDER_TYPE_BUY
            if direction == "BUY"
            else mt5.ORDER_TYPE_SELL
        )

        price = ask if direction == "BUY" else bid
        price = self._normalize_price(price, info)

        normalized_volume = self.normalize_volume(
            float(volume),
            info,
            round_down=True,
        )

        normalized_sl, normalized_tp = self._normalize_stops(
            info=info,
            direction=direction,
            tick=tick,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        request_base = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(normalized_volume),
            "type": order_type,
            "price": price,
            "sl": normalized_sl,
            "tp": normalized_tp,
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": str(comment)[:31],
            "type_time": mt5.ORDER_TIME_GTC,
        }

        attempts = []

        for filling in self._allowed_fillings(info):
            request = dict(request_base)
            request["type_filling"] = int(filling)

            check = mt5.order_check(request)
            check_info = self._check_result_dict(check)

            attempts.append(
                {
                    "filling": int(filling),
                    "filling_name": self._filling_name(filling),
                    "request": request,
                    "check_retcode": check_info["retcode"],
                    "check_comment": check_info["comment"],
                }
            )

            if not check_info["valid"]:
                continue

            result = mt5.order_send(request)

            if result is None:
                attempts[-1]["send_retcode"] = None
                attempts[-1]["send_comment"] = (
                    f"order_send devolvió None; "
                    f"last_error={mt5.last_error()}"
                )
                continue

            attempts[-1]["send_retcode"] = int(
                getattr(result, "retcode", -1)
            )
            attempts[-1]["send_comment"] = str(
                getattr(result, "comment", "")
            )

            success_codes = {
                int(mt5.TRADE_RETCODE_DONE),
                int(getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", -999)),
                int(getattr(mt5, "TRADE_RETCODE_PLACED", -998)),
            }

            if int(getattr(result, "retcode", -1)) in success_codes:
                return {
                    "result": result,
                    "request": request,
                    "entry_price": float(
                        getattr(result, "price", 0.0) or price
                    ),
                    "order_ticket": (
                        int(getattr(result, "order", 0) or 0) or None
                    ),
                    "deal_ticket": (
                        int(getattr(result, "deal", 0) or 0) or None
                    ),
                    "stop_loss": normalized_sl,
                    "take_profit": normalized_tp,
                    "attempts": attempts,
                    "selected_filling": int(filling),
                    "selected_filling_name": self._filling_name(filling),
                }

        raise MT5ExecutionError(
            "MT5 rechazó la orden después de probar los modos de filling "
            f"permitidos. attempts={attempts}; "
            f"last_error={mt5.last_error()}"
        )

    @staticmethod
    def _filling_name(filling: int) -> str:
        names = {
            int(getattr(mt5, "ORDER_FILLING_FOK", -100)): "FOK",
            int(getattr(mt5, "ORDER_FILLING_IOC", -101)): "IOC",
            int(getattr(mt5, "ORDER_FILLING_RETURN", -102)): "RETURN",
        }
        return names.get(int(filling), f"UNKNOWN_{filling}")

    def find_position_ticket(
        self,
        symbol: str,
        magic: int,
        comment: str,
    ):
        self._ensure()

        positions = mt5.positions_get(symbol=symbol) or []

        candidates = [
            p
            for p in positions
            if int(getattr(p, "magic", 0)) == int(magic)
            or str(getattr(p, "comment", "")) == str(comment)[:31]
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda p: getattr(p, "time", 0),
            reverse=True,
        )

        return int(candidates[0].ticket)

    def position_ticket_from_deal(
        self,
        deal_ticket: int | None,
    ):
        if not deal_ticket:
            return None

        self._ensure()

        rows = mt5.history_deals_get(
            ticket=int(deal_ticket)
        ) or []

        if not rows:
            return None

        value = getattr(rows[0], "position_id", 0)
        return int(value) if value else None

    def get_position(self, ticket: int | None):
        if not ticket:
            return None

        self._ensure()

        rows = mt5.positions_get(
            ticket=int(ticket)
        ) or []

        return rows[0] if rows else None

    def history_for_position(
        self,
        position_ticket: int | None,
        from_time,
        to_time,
    ):
        self._ensure()

        if position_ticket:
            rows = mt5.history_deals_get(
                position=int(position_ticket)
            )
        else:
            rows = mt5.history_deals_get(
                from_time,
                to_time,
            )

        return list(rows or [])

    def ensure_symbol(self, symbol: str) -> dict:
        self._ensure()
        """
        Verifica que el símbolo exista en MetaTrader 5 y quede seleccionado
        para recibir precios y permitir operaciones.
        """

        symbol_info = mt5.symbol_info(symbol)

        if symbol_info is None:
            raise MT5ExecutionError(
                f"El símbolo '{symbol}' no existe o no está disponible en MT5."
            )

        if not symbol_info.visible:
            selected = mt5.symbol_select(symbol, True)

            if not selected:
                raise MT5ExecutionError(
                    f"No fue posible habilitar el símbolo '{symbol}' en MT5."
                )

            symbol_info = mt5.symbol_info(symbol)

            if symbol_info is None:
                raise MT5ExecutionError(
                    f"No fue posible obtener información del símbolo '{symbol}'."
                )

        return {
            "symbol": symbol,
            "visible": bool(symbol_info.visible),
            "trade_mode": symbol_info.trade_mode,
            "volume_min": symbol_info.volume_min,
            "volume_max": symbol_info.volume_max,
            "volume_step": symbol_info.volume_step,
            "point": symbol_info.point,
            "digits": symbol_info.digits,
            "trade_stops_level": symbol_info.trade_stops_level,
        }
