"""Comprobaciones previas al arranque de la ejecucion en DEMO.

Verifica de una sola pasada que estan dadas todas las condiciones para operar:
terminal conectado, AutoTrading habilitado, cuenta de practicas, margen libre
suficiente, base de datos escribible y cada simbolo activo y operable.

Se ejecuta UNA vez al arrancar. No forma parte del ciclo ni puede cerrar
posiciones: su unico efecto es permitir o impedir que el bot empiece.

Vinculaciones:
    - `execution_provider`: `brokers.mt5_execution.MT5ExecutionProvider`.
    - `repository`: opcional; si esta, se prueba escribiendo un snapshot de
      cuenta real, que ademas deja constancia del estado inicial.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

try:
    import MetaTrader5 as mt5
except ModuleNotFoundError:  # permite ejecutar tests unitarios sin el terminal MT5
    mt5 = None


@dataclass
class ExecutionPreflightConfig:
    """Umbrales del preflight.

    Attributes:
        require_demo_account: si `True`, una cuenta real hace fallar la
            comprobacion. Es la proteccion principal del servicio.
        min_free_margin: margen libre minimo exigido.
    """

    require_demo_account: bool = True
    min_free_margin: float = 0.0


class ExecutionPreflightService:
    """Valida que el entorno MT5 esté listo antes de permitir ejecución DEMO."""

    def __init__(self, execution_provider, repository=None, config=None):
        """Guarda proveedor, repositorio opcional y umbrales."""
        self.execution_provider = execution_provider
        self.repository = repository
        self.config = config or ExecutionPreflightConfig()

    def run(self, symbols: Iterable[str]) -> dict:
        """Ejecuta todas las comprobaciones y devuelve el veredicto.

        Args:
            symbols: instrumentos que se van a operar; cada uno se activa y se
                verifica que no tenga el trading deshabilitado.

        Returns:
            dict con `ready` (booleano global), `checks` (todas) y `failed`
            (solo las fallidas).

        No lanza excepciones: cada fallo se convierte en un check negativo, de
        modo que el llamador vea el diagnostico COMPLETO en vez de detenerse en
        el primer problema. La unica excepcion es un fallo al leer la cuenta,
        que corta de inmediato porque el resto de comprobaciones dependen de
        ella.
        """
        if mt5 is None:
            return {
                "ready": False,
                "checks": [{"name": "MT5_MODULE", "ok": False, "details": {"error": "MetaTrader5 no está instalado"}}],
                "failed": [{"name": "MT5_MODULE", "ok": False, "details": {"error": "MetaTrader5 no está instalado"}}],
            }
        checks = []

        def check(name, ok, details=None):
            """Acumula un resultado de comprobacion en la lista."""
            checks.append({"name": name, "ok": bool(ok), "details": details or {}})

        try:
            account = self.execution_provider.account_info()
            check("MT5_ACCOUNT_INFO", True, account)
        except Exception as exc:
            check("MT5_ACCOUNT_INFO", False, {"error": str(exc)})
            return self._result(checks)

        try:
            terminal = mt5.terminal_info()
            terminal_ok = terminal is not None and bool(getattr(terminal, "connected", False))
            trade_allowed = terminal is not None and bool(getattr(terminal, "trade_allowed", False))
            api_disabled = bool(getattr(terminal, "tradeapi_disabled", False)) if terminal is not None else True
            check("MT5_TERMINAL_CONNECTED", terminal_ok, {
                "trade_allowed": trade_allowed,
                "tradeapi_disabled": api_disabled,
            })
            check("MT5_AUTOTRADING_ALLOWED", trade_allowed and not api_disabled, {
                "trade_allowed": trade_allowed,
                "tradeapi_disabled": api_disabled,
            })
        except Exception as exc:
            check("MT5_TERMINAL_CONNECTED", False, {"error": str(exc)})
            check("MT5_AUTOTRADING_ALLOWED", False, {"error": str(exc)})

        if self.config.require_demo_account:
            demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", None)
            demo_ok = demo_mode is None or int(account["trade_mode"]) == int(demo_mode)
            check("DEMO_ACCOUNT", demo_ok, {
                "trade_mode": account["trade_mode"],
                "server": account["server"],
            })

        check(
            "FREE_MARGIN",
            float(account["free_margin"]) >= float(self.config.min_free_margin),
            {"free_margin": account["free_margin"], "required": self.config.min_free_margin},
        )

        if self.repository is not None:
            try:
                self.repository.save_account_snapshot(account)
                check("DATABASE_READY", True)
            except Exception as exc:
                check("DATABASE_READY", False, {"error": str(exc)})

        for symbol in symbols:
            try:
                info = self.execution_provider.ensure_symbol(str(symbol))
                constraints = self.execution_provider.get_symbol_constraints(str(symbol))

                # MT5ExecutionProvider.ensure_symbol() devuelve actualmente un
                # diccionario. Algunos dobles de prueba/devuelven objetos tipo
                # SimpleNamespace. El preflight debe aceptar ambos contratos.
                def field(name, default=None):
                    """Lee un atributo tanto si `info` es dict como si es objeto.

                    `ensure_symbol` devuelve un diccionario, pero los dobles de
                    prueba usan `SimpleNamespace`; el preflight acepta ambos.
                    """
                    if isinstance(info, dict):
                        return info.get(name, default)
                    return getattr(info, name, default)

                trade_mode = field("trade_mode")
                disabled = getattr(mt5, "SYMBOL_TRADE_MODE_DISABLED", None)

                if trade_mode is None:
                    raise RuntimeError(
                        "El símbolo no informa trade_mode después de ensure_symbol()."
                    )

                trade_ok = (
                    disabled is None
                    or int(trade_mode) != int(disabled)
                )

                volume_min = float(constraints.get("volume_min") or 0.0)
                volume_step = float(constraints.get("volume_step") or 0.0)
                point = float(constraints.get("point") or 0.0)
                constraints_ok = (
                    volume_min > 0.0
                    and volume_step > 0.0
                    and point > 0.0
                )

                symbol_ok = trade_ok and constraints_ok
                details = {
                    "visible": bool(field("visible", False)),
                    "trade_mode": trade_mode,
                    "volume_min": volume_min,
                    "volume_step": volume_step,
                    "point": point,
                    "stops_level_points": constraints.get("stops_level_points"),
                }

                if not trade_ok:
                    details["reason"] = "SYMBOL_TRADING_DISABLED"
                elif not constraints_ok:
                    details["reason"] = "INVALID_SYMBOL_CONSTRAINTS"

                check(f"SYMBOL:{symbol}", symbol_ok, details)
            except Exception as exc:
                check(f"SYMBOL:{symbol}", False, {"error": str(exc)})

        return self._result(checks)

    @staticmethod
    def _result(checks):
        """Empaqueta el veredicto: `ready` solo si NINGUNA comprobacion fallo."""
        failed = [item for item in checks if not item["ok"]]
        return {
            "ready": not failed,
            "checks": checks,
            "failed": failed,
        }
