"""Capa de ejecucion de bajo nivel contra MetaTrader 5.

Es el unico punto del proyecto que envia ordenes reales. Concentra todas las
salvaguardas previas al `order_send`:

- **Cuenta DEMO obligatoria**: `assert_demo_account` bloquea la ejecucion
  automatica si la cuenta conectada no es de practicas.
- **Restricciones del simbolo**: distancias minimas de stop, pasos de precio y
  limites de volumen del broker.
- **Normalizacion**: precios y volumenes se ajustan a los digitos y al paso
  admitidos, porque un valor mal redondeado provoca rechazo.
- **Modo de llenado**: se detectan y prueban FOK / IOC / RETURN, ya que cada
  broker admite unos distintos.
- **`order_check` antes de `order_send`**: se valida la orden antes de enviarla
  y se guarda el diagnostico de cada intento.

Requiere el terminal MT5 abierto y conectado.

Vinculaciones:
    - `brokers.mt5_trade_executor.MT5TradeExecutor` lo envuelve y lo adapta al
      contrato generico del motor.
    - Consumidores: `app.main` y `strategy.execution.live_trading_engine`.
    - `brokers/mt5_execution.back.py` es una copia obsoleta de este fichero.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math

import MetaTrader5 as mt5


class MT5ExecutionError(RuntimeError):
    """Fallo en la ejecucion o validacion contra MT5.

    Cubre desde la ausencia de un simbolo hasta el rechazo de una orden. Se usa
    un tipo propio para poder distinguir estos errores de los de la estrategia.
    """

    pass


class MT5ExecutionProvider:
    """Capa de ejecución para una cuenta MT5 ya conectada.

    MetaTrader 5 debe estar abierto y conectado.
    La clase conserva las validaciones de:
    - cuenta Demo
    - restricciones del símbolo
    - normalización de SL/TP
    - cálculo de volumen por riesgo
    - order_check antes de order_send

    Además añade:
    - detección automática de filling modes por símbolo
    - fallback entre FOK / IOC / RETURN
    - diagnóstico detallado de cada intento de order_check
    - selección del filling mode realmente aceptado por MT5
    """

    def __init__(self, connector):
        """Guarda el conector; la conexion se asegura en cada operacion."""
        self.connector = connector

    # ==========================================================
    # CONEXIÓN Y CUENTA
    # ==========================================================

    def _ensure(self):
        """Reconecta si hace falta antes de cualquier llamada a MT5."""
        if not self.connector.is_connected():
            self.connector.connect()

    def account_info(self) -> dict:
        """Estado de la cuenta normalizado a dict.

        Returns:
            dict con login, servidor, divisa, balance, equity, margen, margen
            libre, beneficio flotante, apalancamiento, `trade_mode` y el
            instante UTC de la lectura.

        Raises:
            MT5ExecutionError: si el terminal no devuelve la cuenta.
        """
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
        """SALVAGUARDA CRITICA: aborta si la cuenta conectada no es DEMO.

        Se invoca antes de cada envio de orden. Si `ACCOUNT_TRADE_MODE_DEMO` no
        existe en la version instalada de la libreria, la comprobacion se omite
        en lugar de fallar.

        Returns:
            El dict de cuenta, para reaprovecharlo sin releerlo.

        Raises:
            MT5ExecutionError: si la cuenta es real.
        """
        account = self.account_info()

        demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", None)

        if (
            demo_mode is not None
            and account["trade_mode"] != int(demo_mode)
        ):
            raise MT5ExecutionError(
                "La cuenta conectada no es DEMO. "
                "La ejecución automática está bloqueada para proteger una cuenta real."
            )

        return account

    # ==========================================================
    # SÍMBOLO
    # ==========================================================

    def ensure_symbol(self, symbol: str):
        """Asegura que el símbolo exista y esté seleccionado en Market Watch."""
        self._ensure()

        info = mt5.symbol_info(symbol)

        if info is None:
            raise MT5ExecutionError(
                f"No existe el símbolo '{symbol}': {mt5.last_error()}"
            )

        if not bool(getattr(info, "visible", False)):
            if not mt5.symbol_select(symbol, True):
                raise MT5ExecutionError(
                    f"No se pudo seleccionar '{symbol}' en Market Watch: "
                    f"{mt5.last_error()}"
                )

            info = mt5.symbol_info(symbol)

            if info is None:
                raise MT5ExecutionError(
                    f"No se pudo recargar la información de '{symbol}': "
                    f"{mt5.last_error()}"
                )

        return info

    def symbol_spec(self, symbol: str):
        """Especificacion del simbolo, garantizando que este seleccionado.

        Alias de `ensure_symbol` con nombre orientado a su uso: obtener
        digitos, paso de volumen y distancia minima de stop.
        """
        self._ensure()
        return self.ensure_symbol(symbol)

    # ==========================================================
    # RESTRICCIONES DEL SÍMBOLO
    # ==========================================================

    def get_symbol_constraints(self, symbol: str) -> dict:
        """Devuelve restricciones reales informadas por MT5."""
        info = self.symbol_spec(symbol)

        point = float(getattr(info, "point", 0.0) or 0.0)
        digits = int(getattr(info, "digits", 0) or 0)
        stops_level = int(getattr(info, "trade_stops_level", 0) or 0)
        freeze_level = int(getattr(info, "trade_freeze_level", 0) or 0)

        return {
            "symbol": symbol,
            "digits": digits,
            "point": point,
            "stops_level_points": stops_level,
            "freeze_level_points": freeze_level,
            "min_stop_distance": stops_level * point,
            "volume_min": float(getattr(info, "volume_min", 0.0) or 0.0),
            "volume_max": float(getattr(info, "volume_max", 0.0) or 0.0),
            "volume_step": float(getattr(info, "volume_step", 0.0) or 0.0),
            "tick_size": float(
                getattr(info, "trade_tick_size", 0.0) or 0.0
            ),
            "tick_value": float(
                getattr(info, "trade_tick_value", 0.0) or 0.0
            ),
            "tick_value_loss": float(
                getattr(info, "trade_tick_value_loss", 0.0) or 0.0
            ),
            "filling_mode_raw": int(
                getattr(info, "filling_mode", 0) or 0
            ),
            "trade_exemode": int(
                getattr(info, "trade_exemode", 0) or 0
            ),
        }

    @staticmethod
    def _normalize_price(price: float, digits: int) -> float:
        """Redondea el precio a los decimales que admite el simbolo.

        Imprescindible: un precio con mas decimales de los permitidos provoca
        el rechazo de la orden por parte del broker.
        """
        return round(float(price), max(0, int(digits)))

    # ==========================================================
    # STOPS
    # ==========================================================

    def normalize_market_stops(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float,
        safety_points: int = 2,
    ) -> dict:
        """Valida/adapta SL y TP y devuelve diagnóstico completo.

        Regla importante:
        - BUY: el precio de entrada de mercado debe estar estrictamente sobre el SL estructural.
        - SELL: el precio de entrada de mercado debe estar estrictamente bajo el SL estructural.

        Si el mercado ya cruzó el SL estructural, la señal se considera invalidada
        y NO se mueve el SL para "salvar" una operación que ya perdió su estructura.
        """
        self._ensure()

        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            raise ValueError("direction debe ser BUY o SELL")

        rr = float(risk_reward_ratio)
        if rr <= 0:
            raise ValueError("risk_reward_ratio debe ser mayor que cero")

        constraints = self.get_symbol_constraints(symbol)
        point = float(constraints["point"])
        digits = int(constraints["digits"])

        entry = self._normalize_price(float(entry_price), digits)
        original_sl = self._normalize_price(float(stop_loss), digits)

        # Distancia firmada: positiva = la entrada está en el lado correcto del SL.
        signed_distance = (
            entry - original_sl
            if direction == "BUY"
            else original_sl - entry
        )

        base_diagnostics = {
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry,
            "original_stop_loss": original_sl,
            "risk_reward_ratio": rr,
            "entry_vs_structural_sl": signed_distance,
            "absolute_distance_to_structural_sl": abs(entry - original_sl),
            "entry_equals_structural_sl": abs(entry - original_sl) <= 1e-12,
            "constraints": constraints,
        }

        if direction == "BUY" and entry <= original_sl:
            return {
                "valid": False,
                "reason": "MARKET_ALREADY_BELOW_OR_AT_STRUCTURAL_SL",
                "invalidation_rule": "BUY_REQUIRES_MARKET_ENTRY_ABOVE_STRUCTURAL_SL",
                "market_relation": (
                    "AT_STRUCTURAL_SL"
                    if abs(entry - original_sl) <= 1e-12
                    else "BELOW_STRUCTURAL_SL"
                ),
                **base_diagnostics,
            }

        if direction == "SELL" and entry >= original_sl:
            return {
                "valid": False,
                "reason": "MARKET_ALREADY_ABOVE_OR_AT_STRUCTURAL_SL",
                "invalidation_rule": "SELL_REQUIRES_MARKET_ENTRY_BELOW_STRUCTURAL_SL",
                "market_relation": (
                    "AT_STRUCTURAL_SL"
                    if abs(entry - original_sl) <= 1e-12
                    else "ABOVE_STRUCTURAL_SL"
                ),
                **base_diagnostics,
            }

        min_distance = max(
            float(constraints["min_stop_distance"]),
            (
                (
                    int(constraints["stops_level_points"])
                    + max(0, int(safety_points))
                )
                * point
                if point > 0
                else 0.0
            ),
            point if point > 0 else 0.0,
        )

        structural_distance = abs(entry - original_sl)
        used_distance = max(structural_distance, min_distance)
        adjusted = used_distance > structural_distance + 1e-12

        if direction == "BUY":
            sl = entry - used_distance
            tp = entry + used_distance * rr
        else:
            sl = entry + used_distance
            tp = entry - used_distance * rr

        sl = self._normalize_price(sl, digits)
        tp = self._normalize_price(tp, digits)

        sl_distance = abs(entry - sl)
        tp_distance = abs(tp - entry)

        if direction == "BUY" and not (sl < entry < tp):
            return {
                "valid": False,
                "reason": "INVALID_STOP_DIRECTION_AFTER_NORMALIZATION",
                **base_diagnostics,
                "stop_loss": sl,
                "take_profit": tp,
                "minimum_stop_distance": min_distance,
            }

        if direction == "SELL" and not (tp < entry < sl):
            return {
                "valid": False,
                "reason": "INVALID_STOP_DIRECTION_AFTER_NORMALIZATION",
                **base_diagnostics,
                "stop_loss": sl,
                "take_profit": tp,
                "minimum_stop_distance": min_distance,
            }

        if sl_distance + 1e-12 < min_distance:
            return {
                "valid": False,
                "reason": "STOP_DISTANCE_STILL_BELOW_MINIMUM",
                **base_diagnostics,
                "stop_loss": sl,
                "take_profit": tp,
                "minimum_stop_distance": min_distance,
                "used_stop_distance": sl_distance,
            }

        return {
            "valid": True,
            "reason": "STOPS_NORMALIZED" if adjusted else "STOPS_VALID",
            **base_diagnostics,
            "market_relation": "VALID_SIDE_OF_STRUCTURAL_SL",
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "structural_stop_distance": structural_distance,
            "minimum_stop_distance": min_distance,
            "used_stop_distance": sl_distance,
            "take_profit_distance": tp_distance,
            "adjusted": adjusted,
            "safety_points": int(safety_points),
        }

    # ==========================================================
    # FILLING MODES
    # ==========================================================

    @staticmethod
    def _filling_name(filling: int) -> str:
        """Nombre legible del modo de llenado, para los diagnosticos.

        Devuelve `UNKNOWN_<n>` si el valor no es ninguno de los tres conocidos,
        en vez de ocultarlo.
        """
        names = {
            getattr(mt5, "ORDER_FILLING_FOK", 0): "FOK",
            getattr(mt5, "ORDER_FILLING_IOC", 1): "IOC",
            getattr(mt5, "ORDER_FILLING_RETURN", 2): "RETURN",
        }
        return names.get(int(filling), f"UNKNOWN_{filling}")

    def _symbol_filling_candidates(self, symbol: str) -> list[int]:
        """Construye candidatos según las flags del símbolo.

        MetaTrader expone info.filling_mode como máscara de modos permitidos.
        Las constantes SYMBOL_FILLING_* son flags y no deben confundirse
        con ORDER_FILLING_* usados dentro de una orden.
        """
        info = self.symbol_spec(symbol)

        raw_mode = int(
            getattr(info, "filling_mode", 0) or 0
        )

        candidates: list[int] = []

        order_fok = getattr(mt5, "ORDER_FILLING_FOK", 0)
        order_ioc = getattr(mt5, "ORDER_FILLING_IOC", 1)
        order_return = getattr(mt5, "ORDER_FILLING_RETURN", 2)

        symbol_fok = getattr(
            mt5,
            "SYMBOL_FILLING_FOK",
            1,
        )
        symbol_ioc = getattr(
            mt5,
            "SYMBOL_FILLING_IOC",
            2,
        )

        if raw_mode & int(symbol_fok):
            candidates.append(order_fok)

        if raw_mode & int(symbol_ioc):
            candidates.append(order_ioc)

        # RETURN no siempre aparece como flag en symbol_info.
        # Se deja como fallback y será aceptado/rechazado por order_check.
        if order_return not in candidates:
            candidates.append(order_return)

        # Fallback defensivo: algunos brokers/terminales reportan
        # filling_mode de forma no concluyente.
        for candidate in (
            order_ioc,
            order_fok,
            order_return,
        ):
            if candidate not in candidates:
                candidates.append(candidate)

        unique: list[int] = []

        for candidate in candidates:
            if candidate not in unique:
                unique.append(candidate)

        return unique

    def get_filling_diagnostics(self, symbol: str) -> dict:
        """Expone cómo MT5 informa los filling modes del símbolo."""
        info = self.symbol_spec(symbol)
        candidates = self._symbol_filling_candidates(symbol)

        return {
            "symbol": symbol,
            "filling_mode_raw": int(
                getattr(info, "filling_mode", 0) or 0
            ),
            "trade_exemode": int(
                getattr(info, "trade_exemode", 0) or 0
            ),
            "candidates": [
                {
                    "value": int(item),
                    "name": self._filling_name(item),
                }
                for item in candidates
            ],
        }

    # ==========================================================
    # REQUEST
    # ==========================================================

    def _current_market_price(
        self,
        symbol: str,
        direction: str,
    ) -> float:
        """Precio de mercado del lado correcto: ask para BUY, bid para SELL.

        Usar el lado equivocado introduciria un error del tamano del spread en
        el calculo de riesgo.

        Raises:
            MT5ExecutionError: si no hay tick o el precio no es positivo.
        """
        tick = mt5.symbol_info_tick(symbol)

        if tick is None:
            raise MT5ExecutionError(
                f"No hay tick para '{symbol}': {mt5.last_error()}"
            )

        if direction == "BUY":
            price = float(tick.ask)
        else:
            price = float(tick.bid)

        if price <= 0:
            raise MT5ExecutionError(
                f"Precio inválido para '{symbol}': {price}"
            )

        return price

    @staticmethod
    def _sanitize_comment(comment: str | None, max_bytes: int = 30) -> str:
        """Normaliza el comentario para el binding de MetaTrader5.

        Algunos terminales/bindings devuelven last_error=(-2, 'Invalid "comment"
        argument') antes de llegar al servidor. Por seguridad usamos solo ASCII
        imprimible y un límite conservador de 30 bytes (no 31 caracteres Unicode).
        """
        text = "" if comment is None else str(comment)
        text = " ".join(text.split())
        text = "".join(ch for ch in text if 32 <= ord(ch) <= 126)
        if not text:
            text = "BOT"
        encoded = text.encode("ascii", errors="ignore")[:max(1, int(max_bytes))]
        text = encoded.decode("ascii", errors="ignore").strip()
        return text or "BOT"

    @staticmethod
    def _last_error_is_invalid_comment(last_error) -> bool:
        """Detecta el error `-2 Invalid "comment" argument` del binding.

        Ese fallo lo produce la libreria de Python ANTES de llegar al servidor,
        de modo que reintentar con un comentario minimo si tiene sentido: no
        hay riesgo de haber enviado ya la orden.
        """
        try:
            code = int(last_error[0]) if last_error else None
            message = str(last_error[1]) if last_error and len(last_error) > 1 else ""
        except Exception:
            return False
        return code == -2 and "comment" in message.lower()

    def _order_check_safe(self, request: dict) -> tuple[object, dict, dict]:
        """Ejecuta order_check y, si el binding rechaza el comentario,
        reintenta automáticamente con un comentario mínimo y seguro.
        """
        first_request = dict(request)
        first_request["comment"] = self._sanitize_comment(
            first_request.get("comment")
        )
        check = mt5.order_check(first_request)
        last_error = mt5.last_error()
        diagnostic = {
            "comment_used": first_request.get("comment"),
            "comment_fallback_used": False,
            "mt5_last_error": last_error,
        }

        if check is None and self._last_error_is_invalid_comment(last_error):
            retry_request = dict(first_request)
            retry_request["comment"] = "BOT"
            check = mt5.order_check(retry_request)
            retry_error = mt5.last_error()
            diagnostic.update({
                "comment_fallback_used": True,
                "comment_fallback_value": "BOT",
                "mt5_last_error_first": last_error,
                "mt5_last_error": retry_error,
            })
            return check, retry_request, diagnostic

        return check, first_request, diagnostic

    def _order_send_safe(self, request: dict) -> tuple[object, dict, dict]:
        """Envía la orden y aplica el mismo fallback defensivo de comentario."""
        first_request = dict(request)
        first_request["comment"] = self._sanitize_comment(
            first_request.get("comment")
        )
        result = mt5.order_send(first_request)
        last_error = mt5.last_error()
        diagnostic = {
            "comment_used": first_request.get("comment"),
            "comment_fallback_used": False,
            "mt5_last_error": last_error,
        }

        if result is None and self._last_error_is_invalid_comment(last_error):
            retry_request = dict(first_request)
            retry_request["comment"] = "BOT"
            result = mt5.order_send(retry_request)
            retry_error = mt5.last_error()
            diagnostic.update({
                "comment_fallback_used": True,
                "comment_fallback_value": "BOT",
                "mt5_last_error_first": last_error,
                "mt5_last_error": retry_error,
            })
            return result, retry_request, diagnostic

        return result, first_request, diagnostic

    def _build_market_request_base(
        self,
        symbol: str,
        direction: str,
        volume: float,
        stop_loss: float,
        take_profit: float,
        magic: int,
        comment: str,
        deviation: int,
    ) -> dict:
        """Arma el diccionario base de una orden a mercado.

        Normaliza precio, SL y TP a los decimales del simbolo y sanea el
        comentario. No incluye `type_filling`: ese campo lo anaden los
        reintentos que prueban FOK / IOC / RETURN.

        Raises:
            ValueError: si la direccion no es BUY ni SELL.
        """
        direction = str(direction).upper()

        if direction not in {"BUY", "SELL"}:
            raise ValueError("direction debe ser BUY o SELL")

        info = self.symbol_spec(symbol)

        order_type = (
            mt5.ORDER_TYPE_BUY
            if direction == "BUY"
            else mt5.ORDER_TYPE_SELL
        )

        price = self._current_market_price(
            symbol,
            direction,
        )

        return {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": self._normalize_price(
                price,
                int(getattr(info, "digits", 0) or 0),
            ),
            "sl": self._normalize_price(
                float(stop_loss),
                int(getattr(info, "digits", 0) or 0),
            ),
            "tp": self._normalize_price(
                float(take_profit),
                int(getattr(info, "digits", 0) or 0),
            ),
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": self._sanitize_comment(comment),
            "type_time": mt5.ORDER_TIME_GTC,
        }

    # ==========================================================
    # DIAGNÓSTICO DE ORDER_CHECK
    # ==========================================================

    @staticmethod
    def _result_fields(result) -> dict:
        """Convierte a dict el objeto que devuelve MT5 (namedtuple opaco).

        Intenta `_asdict()` y, si no esta disponible, extrae los campos
        conocidos uno a uno. Asi el diagnostico se puede serializar a JSON y
        guardar en la auditoria.
        """
        if result is None:
            return {}

        data = {}

        if hasattr(result, "_asdict"):
            try:
                data = dict(result._asdict())
            except Exception:
                data = {}

        if not data:
            for field in (
                "retcode",
                "comment",
                "balance",
                "equity",
                "profit",
                "margin",
                "margin_free",
                "margin_level",
                "request_id",
                "retcode_external",
            ):
                if hasattr(result, field):
                    data[field] = getattr(result, field)

        normalized = {}

        for key, value in data.items():
            try:
                if isinstance(value, (int, float, str, bool)) or value is None:
                    normalized[key] = value
                else:
                    normalized[key] = str(value)
            except Exception:
                normalized[key] = repr(value)

        return normalized

    @staticmethod
    def _is_order_check_success(check) -> bool:
        """
        order_check() y order_send() no usan el mismo criterio de éxito.

        En MetaTrader 5, un order_check() válido normalmente devuelve:
            retcode == 0
            comment == "Done"

        TRADE_RETCODE_DONE (por ejemplo 10009) corresponde al resultado
        de ejecución de order_send(), por lo que NO debe usarse para decidir
        si order_check() aceptó la solicitud.
        """
        if check is None:
            return False

        try:
            return int(getattr(check, "retcode", -1)) == 0
        except Exception:
            return False

    @staticmethod
    def _is_order_send_success(result) -> bool:
        """Determina éxito después de order_send()."""
        if result is None:
            return False

        values = {
            getattr(mt5, "TRADE_RETCODE_DONE", None),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", None),
            getattr(mt5, "TRADE_RETCODE_PLACED", None),
        }

        valid = {
            int(value)
            for value in values
            if value is not None
        }

        try:
            return int(getattr(result, "retcode", -1)) in valid
        except Exception:
            return False

    def _run_order_check_with_fallback(
        self,
        symbol: str,
        request_base: dict,
    ) -> dict:
        """Prueba cada filling mode y conserva el diagnóstico completo."""
        attempts = []

        candidates = self._symbol_filling_candidates(symbol)

        for filling in candidates:
            request = dict(request_base)
            request["type_filling"] = int(filling)

            check, request, check_diagnostic = self._order_check_safe(request)

            attempt = {
                "filling": int(filling),
                "filling_name": self._filling_name(filling),
                "request": dict(request),
                "mt5_last_error": check_diagnostic.get("mt5_last_error"),
                "comment_used": check_diagnostic.get("comment_used"),
                "comment_fallback_used": check_diagnostic.get(
                    "comment_fallback_used", False
                ),
            }

            if check_diagnostic.get("comment_fallback_used"):
                attempt["comment_fallback_value"] = check_diagnostic.get(
                    "comment_fallback_value"
                )
                attempt["mt5_last_error_first"] = check_diagnostic.get(
                    "mt5_last_error_first"
                )

            if check is None:
                attempt.update({
                    "valid": False,
                    "retcode": None,
                    "comment": "ORDER_CHECK_NONE",
                    "result": None,
                })

                attempts.append(attempt)
                continue

            retcode = int(
                getattr(check, "retcode", -1)
            )

            comment = str(
                getattr(check, "comment", "")
            )

            valid = self._is_order_check_success(check)

            attempt.update({
                "valid": bool(valid),
                "retcode": retcode,
                "comment": comment,
                "result": self._result_fields(check),
                "diagnostic": (
                    "ORDER_CHECK_OK" if valid
                    else "ORDER_CHECK_REJECTED"
                ),
            })

            attempts.append(attempt)

            if valid:
                return {
                    "valid": True,
                    "selected_filling": int(filling),
                    "selected_filling_name": self._filling_name(
                        filling
                    ),
                    "request": request,
                    "retcode": retcode,
                    "comment": comment,
                    "attempts": attempts,
                    "filling_diagnostics": self.get_filling_diagnostics(
                        symbol
                    ),
                }

        last = attempts[-1] if attempts else {}

        return {
            "valid": False,
            "reason": (
                last.get("comment")
                or "NO_COMPATIBLE_FILLING_MODE"
            ),
            "retcode": last.get("retcode"),
            "comment": last.get("comment"),
            "request": last.get("request"),
            "attempts": attempts,
            "filling_diagnostics": self.get_filling_diagnostics(
                symbol
            ),
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
        """Ejecuta order_check sin abrir una operación.

        Prueba automáticamente los filling modes compatibles del símbolo.
        """
        self._ensure()

        request_base = self._build_market_request_base(
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            magic=magic,
            comment=comment,
            deviation=deviation,
        )

        return self._run_order_check_with_fallback(
            symbol,
            request_base,
        )

    def calculate_margin_amount(
        self,
        symbol: str,
        direction: str,
        volume: float,
        entry_price: float,
    ) -> dict:
        """Calcula margen requerido con el motor nativo de MT5."""
        self._ensure()
        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            raise ValueError("direction debe ser BUY o SELL")
        action = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        margin = mt5.order_calc_margin(
            action,
            str(symbol),
            float(volume),
            float(entry_price),
        )
        if margin is None:
            raise MT5ExecutionError(
                "MT5 no pudo calcular el margen requerido: "
                f"{mt5.last_error()}"
            )
        return {
            "symbol": str(symbol),
            "direction": direction,
            "volume": float(volume),
            "entry_price": float(entry_price),
            "margin_required": abs(float(margin)),
            "margin_engine": "MT5_ORDER_CALC_MARGIN",
        }

    # ==========================================================
    # VOLUMEN
    # ==========================================================

    @staticmethod
    def normalize_volume(
        volume: float,
        info,
        round_down: bool = True,
    ) -> float:
        """Ajusta el volumen al paso, minimo y maximo que admite el simbolo.

        Args:
            volume: lotes deseados.
            info: especificacion del simbolo.
            round_down: `True` por defecto y ese es el criterio prudente,
                porque redondear al alza superaria el riesgo objetivo.

        El epsilon `1e-12` del `floor` evita que un error de coma flotante haga
        perder un paso entero (p. ej. 2.9999999 -> 2 en vez de 3).

        Returns:
            El volumen normalizado y acotado a `[volume_min, volume_max]`.

        Raises:
            MT5ExecutionError: si el simbolo no informa limites validos; se
                prefiere fallar antes que enviar un volumen arbitrario.
        """
        step = float(
            getattr(info, "volume_step", 0.0) or 0.0
        )
        vmin = float(
            getattr(info, "volume_min", 0.0) or 0.0
        )
        vmax = float(
            getattr(info, "volume_max", 0.0) or 0.0
        )

        if step <= 0 or vmin <= 0 or vmax <= 0:
            raise MT5ExecutionError(
                "El símbolo no informa límites de volumen válidos."
            )

        raw_steps = (
            (float(volume) - vmin) / step
        )

        steps = (
            math.floor(raw_steps + 1e-12)
            if round_down
            else round(raw_steps)
        )

        normalized = (
            vmin + max(0, steps) * step
        )

        normalized = min(
            max(normalized, vmin),
            vmax,
        )

        decimals = (
            max(
                0,
                int(round(-math.log10(step))),
            )
            if step < 1
            else 0
        )

        return round(
            normalized,
            decimals + 2,
        )

    def calculate_risk_amount(
        self,
        symbol: str,
        direction: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
    ) -> dict:
        """Calcula la pérdida monetaria teórica usando el propio motor del broker.

        Esta función es la fuente de verdad para el riesgo. No utiliza una fórmula
        basada en tick_value/tick_size porque algunos sintéticos pueden reportar
        metadatos que no reproducen el PnL monetario real del contrato.
        """
        self._ensure()
        direction = str(direction).upper()
        if direction not in {"BUY", "SELL"}:
            raise ValueError("direction debe ser BUY o SELL")

        action = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        profit = mt5.order_calc_profit(
            action,
            str(symbol),
            float(volume),
            float(entry_price),
            float(stop_loss),
        )
        if profit is None:
            raise MT5ExecutionError(
                "MT5 no pudo calcular el riesgo monetario: "
                f"{mt5.last_error()}"
            )

        return {
            "symbol": str(symbol),
            "direction": direction,
            "volume": float(volume),
            "entry_price": float(entry_price),
            "stop_loss": float(stop_loss),
            "broker_profit_at_stop": float(profit),
            "actual_risk_amount": abs(float(profit)),
            "risk_engine": "MT5_ORDER_CALC_PROFIT",
        }

    def calculate_volume(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        risk_amount: float,
    ) -> dict:
        """Calcula volumen con MT5 como fuente de verdad del riesgo.

        IMPORTANTE: se elimina la prioridad histórica de tick_value/tick_size.
        Primero se pregunta a MT5 cuánto perdería exactamente 1 lote al llegar al
        SL y se vuelve a validar el volumen normalizado con una segunda llamada.
        """
        self._ensure()
        info = self.symbol_spec(symbol)
        direction = str(direction).upper()

        if direction not in {"BUY", "SELL"}:
            raise ValueError("direction debe ser BUY o SELL")

        entry_price = float(entry_price)
        stop_loss = float(stop_loss)
        risk_amount = float(risk_amount)

        if risk_amount <= 0:
            raise MT5ExecutionError("risk_amount debe ser mayor que cero.")
        if entry_price == stop_loss:
            raise MT5ExecutionError("entry_price y stop_loss no pueden ser iguales.")

        one_lot = self.calculate_risk_amount(
            symbol=symbol,
            direction=direction,
            volume=1.0,
            entry_price=entry_price,
            stop_loss=stop_loss,
        )
        risk_per_lot = float(one_lot["actual_risk_amount"])
        if risk_per_lot <= 0:
            raise MT5ExecutionError("MT5 devolvió riesgo por lote inválido.")

        raw_volume = risk_amount / risk_per_lot
        min_volume = float(getattr(info, "volume_min", 0.0) or 0.0)
        max_volume = float(getattr(info, "volume_max", 0.0) or 0.0)
        step = float(getattr(info, "volume_step", 0.0) or 0.0)

        if min_volume <= 0 or max_volume <= 0 or step <= 0:
            raise MT5ExecutionError("El símbolo no informa límites de volumen válidos.")

        min_risk = self.calculate_risk_amount(
            symbol=symbol,
            direction=direction,
            volume=min_volume,
            entry_price=entry_price,
            stop_loss=stop_loss,
        )["actual_risk_amount"]

        if float(min_risk) > risk_amount + 1e-9:
            raise MT5ExecutionError(
                f"El volumen mínimo {min_volume} arriesga {float(min_risk):.2f}, "
                f"superior al riesgo permitido {risk_amount:.2f}."
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

        # Segunda validación después del floor al volume_step.
        normalized = self.calculate_risk_amount(
            symbol=symbol,
            direction=direction,
            volume=volume,
            entry_price=entry_price,
            stop_loss=stop_loss,
        )
        actual_risk = float(normalized["actual_risk_amount"])

        return {
            "volume": float(volume),
            "raw_volume": float(raw_volume),
            "risk_per_lot": float(risk_per_lot),
            "actual_risk_amount": actual_risk,
            "risk_engine": "MT5_ORDER_CALC_PROFIT",
            "broker_profit_at_stop": normalized["broker_profit_at_stop"],
            "volume_min": min_volume,
            "volume_max": max_volume,
            "volume_step": step,
        }

    # ==========================================================
    # EJECUCIÓN REAL
    # ==========================================================

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
        """Abre una orden de mercado.

        Antes de order_send ejecuta order_check con fallback de filling modes.
        Si un modo es aceptado por order_check, ese mismo modo se usa para
        la ejecución real.
        """
        self._ensure()

        request_base = self._build_market_request_base(
            symbol=symbol,
            direction=direction,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            magic=magic,
            comment=comment,
            deviation=deviation,
        )

        validation = self._run_order_check_with_fallback(
            symbol,
            request_base,
        )

        if not validation.get("valid"):
            raise MT5ExecutionError(
                "MT5 order_check rechazó la orden. "
                f"reason={validation.get('reason')}; "
                f"retcode={validation.get('retcode')}; "
                f"comment={validation.get('comment')}; "
                f"attempts={validation.get('attempts')}"
            )

        request = dict(validation["request"])

        # Se refresca el precio inmediatamente antes de enviar.
        request["price"] = self._current_market_price(
            symbol,
            str(direction).upper(),
        )

        # Segundo check final con el filling ya seleccionado.
        final_check, request, final_check_diagnostic = self._order_check_safe(
            request
        )

        if final_check is None:
            raise MT5ExecutionError(
                "ORDER_CHECK_FINAL_NONE: "
                f"last_error={final_check_diagnostic.get('mt5_last_error')}; "
                f"comment={request.get('comment')}; "
                f"fallback={final_check_diagnostic.get('comment_fallback_used', False)}"
            )

        final_retcode = int(
            getattr(final_check, "retcode", -1)
        )

        if not self._is_order_check_success(final_check):
            raise MT5ExecutionError(
                "ORDER_CHECK_FINAL_REJECTED: "
                f"retcode={final_retcode}, "
                f"comment={getattr(final_check, 'comment', '')}, "
                f"filling={self._filling_name(request['type_filling'])}"
            )

        result, request, send_diagnostic = self._order_send_safe(request)

        if result is None:
            raise MT5ExecutionError(
                "MT5 order_send devolvió None: "
                f"last_error={send_diagnostic.get('mt5_last_error')}; "
                f"comment={request.get('comment')}; "
                f"fallback={send_diagnostic.get('comment_fallback_used', False)}"
            )

        retcode = int(
            getattr(result, "retcode", -1)
        )

        if not self._is_order_send_success(result):
            raise MT5ExecutionError(
                "MT5 rechazó la orden: "
                f"retcode={retcode}, "
                f"comment={getattr(result, 'comment', '')}, "
                f"filling={self._filling_name(request['type_filling'])}, "
                f"last_error={mt5.last_error()}"
            )

        return {
            "result": result,
            "request": request,
            "entry_price": float(
                getattr(result, "price", 0.0)
                or request["price"]
            ),
            "order_ticket": (
                int(getattr(result, "order", 0) or 0)
                or None
            ),
            "deal_ticket": (
                int(getattr(result, "deal", 0) or 0)
                or None
            ),
            "selected_filling": int(
                request["type_filling"]
            ),
            "selected_filling_name": self._filling_name(
                request["type_filling"]
            ),
            "order_check": validation,
            "final_check": self._result_fields(
                final_check
            ),
            "final_check_diagnostic": final_check_diagnostic,
            "order_send_diagnostic": send_diagnostic,
        }

    # ==========================================================
    # POSICIONES E HISTORIAL
    # ==========================================================

    def modify_position_stops(
        self,
        position_ticket: int,
        stop_loss: float,
        take_profit: float | None = None,
    ) -> dict:
        """
        Modifica SL/TP de una posición abierta mediante TRADE_ACTION_SLTP.

        Se utiliza, entre otros casos, para mover el Stop Loss a Break Even.
        La actualización se confirma por el retcode de MT5 y devuelve un
        diagnóstico serializable para auditoría.
        """
        self._ensure()

        position = self.get_position(int(position_ticket))
        if position is None:
            return {
                "modified": False,
                "reason": "POSITION_NOT_FOUND",
                "position_ticket": str(position_ticket),
            }

        symbol = str(getattr(position, "symbol", ""))
        if not symbol:
            return {
                "modified": False,
                "reason": "POSITION_SYMBOL_MISSING",
                "position_ticket": str(position_ticket),
            }

        info = self.symbol_spec(symbol)
        digits = int(getattr(info, "digits", 5) or 5)
        current_tp = float(getattr(position, "tp", 0.0) or 0.0)
        requested_tp = current_tp if take_profit is None else float(take_profit)

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position_ticket),
            "symbol": symbol,
            "sl": self._normalize_price(float(stop_loss), digits),
            "tp": self._normalize_price(float(requested_tp), digits) if requested_tp > 0 else 0.0,
        }

        result = mt5.order_send(request)
        last_error = mt5.last_error()
        retcode = None if result is None else int(getattr(result, "retcode", -1))
        comment = None if result is None else str(getattr(result, "comment", ""))

        success_codes = {
            int(getattr(mt5, "TRADE_RETCODE_DONE", 10009)),
            int(getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010)),
            int(getattr(mt5, "TRADE_RETCODE_NO_CHANGES", 10025)),
        }
        modified = retcode in success_codes

        return {
            "modified": bool(modified),
            "position_ticket": str(position_ticket),
            "symbol": symbol,
            "requested_stop_loss": float(request["sl"]),
            "requested_take_profit": float(request["tp"]),
            "retcode": retcode,
            "comment": comment,
            "last_error": last_error,
            "request": request,
        }

    def list_open_positions(self, magic: int | None = None) -> list[dict]:
        """Devuelve un snapshot serializable de las posiciones abiertas de MT5.

        Si ``magic`` se informa, filtra exclusivamente por ese identificador.
        El método no modifica ninguna posición y está pensado para reconciliación
        MT5 -> SQLAlchemy al arrancar el daemon.
        """
        self._ensure()

        rows = mt5.positions_get() or []
        result = []
        for position in rows:
            position_magic = int(getattr(position, "magic", 0) or 0)
            if magic is not None and position_magic != int(magic):
                continue

            position_type = int(getattr(position, "type", -1))
            buy_type = int(getattr(mt5, "POSITION_TYPE_BUY", 0))
            sell_type = int(getattr(mt5, "POSITION_TYPE_SELL", 1))
            if position_type == buy_type:
                direction = "BUY"
            elif position_type == sell_type:
                direction = "SELL"
            else:
                direction = "UNKNOWN"

            opened_epoch = int(getattr(position, "time", 0) or 0)
            opened_at = (
                datetime.fromtimestamp(opened_epoch, tz=timezone.utc)
                if opened_epoch > 0
                else datetime.now(timezone.utc)
            )

            result.append({
                "position_ticket": int(getattr(position, "ticket", 0) or 0),
                "identifier": int(getattr(position, "identifier", 0) or 0),
                "symbol": str(getattr(position, "symbol", "") or ""),
                "direction": direction,
                "type": position_type,
                "magic": position_magic,
                "comment": str(getattr(position, "comment", "") or ""),
                "entry_time": opened_at,
                "entry_price": float(getattr(position, "price_open", 0.0) or 0.0),
                "current_price": float(getattr(position, "price_current", 0.0) or 0.0),
                "stop_loss": float(getattr(position, "sl", 0.0) or 0.0),
                "take_profit": float(getattr(position, "tp", 0.0) or 0.0),
                "volume": float(getattr(position, "volume", 0.0) or 0.0),
                "floating_profit": float(getattr(position, "profit", 0.0) or 0.0),
                "swap": float(getattr(position, "swap", 0.0) or 0.0),
            })

        return result

    def list_history_deals(
        self,
        from_time=None,
        to_time=None,
        magic: int | None = None,
    ) -> list[dict]:
        """Devuelve el historial de deals disponible en MT5 en formato serializable.

        Se usa exclusivamente para reconstruir el journal histórico de Cuenta
        activa. No envía órdenes ni modifica posiciones. Si ``magic`` se
        informa, filtra por el identificador del daemon.
        """
        self._ensure()

        if from_time is None:
            from_time = datetime(2000, 1, 1, tzinfo=timezone.utc)
        if to_time is None:
            to_time = datetime.now(timezone.utc)

        rows = mt5.history_deals_get(from_time, to_time) or []
        result = []

        entry_names = {
            int(getattr(mt5, "DEAL_ENTRY_IN", 0)): "IN",
            int(getattr(mt5, "DEAL_ENTRY_OUT", 1)): "OUT",
            int(getattr(mt5, "DEAL_ENTRY_INOUT", 2)): "INOUT",
            int(getattr(mt5, "DEAL_ENTRY_OUT_BY", 3)): "OUT_BY",
        }
        reason_names = {}
        for attr, label in (
            ("DEAL_REASON_CLIENT", "CLIENT"),
            ("DEAL_REASON_MOBILE", "MOBILE"),
            ("DEAL_REASON_WEB", "WEB"),
            ("DEAL_REASON_EXPERT", "EXPERT"),
            ("DEAL_REASON_SL", "SL"),
            ("DEAL_REASON_TP", "TP"),
            ("DEAL_REASON_SO", "STOP_OUT"),
        ):
            value = getattr(mt5, attr, None)
            if value is not None:
                reason_names[int(value)] = label

        buy_type = int(getattr(mt5, "DEAL_TYPE_BUY", 0))
        sell_type = int(getattr(mt5, "DEAL_TYPE_SELL", 1))

        for deal in rows:
            deal_magic = int(getattr(deal, "magic", 0) or 0)
            if magic is not None and deal_magic != int(magic):
                continue
            deal_type = int(getattr(deal, "type", -1))
            if deal_type == buy_type:
                direction = "BUY"
            elif deal_type == sell_type:
                direction = "SELL"
            else:
                # Balance, credit, commission-only and other account records are
                # not position deals and must not become trades in Cuenta activa.
                continue

            epoch = int(getattr(deal, "time", 0) or 0)
            deal_time = (
                datetime.fromtimestamp(epoch, tz=timezone.utc)
                if epoch > 0 else datetime.now(timezone.utc)
            )
            entry = int(getattr(deal, "entry", -1))
            reason = int(getattr(deal, "reason", -1))
            result.append({
                "deal_ticket": int(getattr(deal, "ticket", 0) or 0),
                "order_ticket": int(getattr(deal, "order", 0) or 0),
                "position_ticket": int(getattr(deal, "position_id", 0) or 0),
                "symbol": str(getattr(deal, "symbol", "") or ""),
                "magic": deal_magic,
                "comment": str(getattr(deal, "comment", "") or ""),
                "time": deal_time,
                "entry": entry,
                "entry_kind": entry_names.get(entry, str(entry)),
                "type": deal_type,
                "direction": direction,
                "reason": reason,
                "reason_kind": reason_names.get(reason, str(reason)),
                "price": float(getattr(deal, "price", 0.0) or 0.0),
                "volume": float(getattr(deal, "volume", 0.0) or 0.0),
                "profit": float(getattr(deal, "profit", 0.0) or 0.0),
                "commission": float(getattr(deal, "commission", 0.0) or 0.0),
                "swap": float(getattr(deal, "swap", 0.0) or 0.0),
                "fee": float(getattr(deal, "fee", 0.0) or 0.0),
            })

        result.sort(key=lambda row: (row["time"], row["deal_ticket"]))
        return result

    def find_position_ticket(
        self,
        symbol: str,
        magic: int,
        comment: str,
    ):
        """Localiza el ticket de la posicion recien abierta.

        `order_send` no siempre devuelve el ticket de POSICION (devuelve el del
        deal), asi que se busca entre las posiciones del simbolo por `magic` o
        por comentario, y se toma la mas reciente.

        Returns:
            El ticket como entero, o `None` si no hay candidatos.
        """
        self._ensure()

        positions = mt5.positions_get(
            symbol=symbol
        ) or []

        candidates = [
            position
            for position in positions
            if (
                int(getattr(position, "magic", 0))
                == int(magic)
                or str(
                    getattr(position, "comment", "")
                )
                == str(comment)[:31]
            )
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda position: getattr(
                position,
                "time",
                0,
            ),
            reverse=True,
        )

        return int(candidates[0].ticket)

    def position_ticket_from_deal(
        self,
        deal_ticket: int | None,
    ):
        """Deriva el ticket de posicion a partir del ticket de un deal.

        Via alternativa cuando `find_position_ticket` no encuentra nada: el
        historial de deals guarda el `position_id` al que pertenecen.

        Returns:
            El ticket de posicion, o `None` si no se puede determinar.
        """
        if not deal_ticket:
            return None

        self._ensure()

        rows = mt5.history_deals_get(
            ticket=int(deal_ticket)
        ) or []

        if not rows:
            return None

        value = getattr(
            rows[0],
            "position_id",
            0,
        )

        return int(value) if value else None

    def get_position(
        self,
        ticket: int | None,
    ):
        """Objeto nativo de la posicion abierta, o `None` si ya no existe.

        Devolver `None` es la senal de que la posicion se cerro; no es un
        error.
        """
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
        """Deals historicos de una posicion, o de un rango temporal.

        Con `position_ticket` consulta directamente por posicion (preciso);
        sin el, recurre a la ventana `from_time`/`to_time`. Es la base para
        reconstruir precio de salida y PnL real de una operacion cerrada.

        Returns:
            Lista de deals, vacia si no hay nada.
        """
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
