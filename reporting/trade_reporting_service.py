from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reporting.trade_report_exporter import TradeReportExporter


@dataclass
class TradeReportingConfig:
    """
    Configuración del servicio de reporting del ciclo de vida.

    source:
        Origen que se guardará en SQLite y que se utilizará al exportar el XLSX.
        Ejemplos: PAPER, DEMO, LIVE.

    auto_export:
        Si es True, cada cambio relevante del lifecycle actualiza el XLSX.
    """

    source: str = "PAPER"
    output_path: str | Path | None = None
    auto_export: bool = True
    broker: str | None = None


class TradeReportingService:
    """
    Adaptador entre TradeLifecycleManager, TradingRepository y TradeReportExporter.

    Responsabilidades:
    - registrar una operación OPEN cuando el executor la llena;
    - sincronizar cambios relevantes mientras la posición sigue abierta;
    - cerrar la operación en SQLite cuando el lifecycle llega a un estado final;
    - regenerar el XLSX cuando corresponde.

    El servicio no ejecuta órdenes ni decide la lógica de trading.
    """

    def __init__(self, repository, config: TradeReportingConfig | None = None):
        if repository is None:
            raise ValueError("repository no puede ser None")

        self.repository = repository
        self.config = config or TradeReportingConfig()
        self.source = str(self.config.source).upper()

        self.exporter = TradeReportExporter(
            repository=self.repository,
            output_path=self.config.output_path,
        )

        # position_ticket/execution_id -> trade_id SQLite
        self._trade_ids: dict[str, int] = {}

    # ============================================================
    # API DE EVENTOS PARA TRADE LIFECYCLE MANAGER
    # ============================================================

    def on_lifecycle_event(
        self,
        event: str,
        lifecycle,
        volume: float | None = None,
    ) -> dict[str, Any]:
        event = str(event).upper()

        # v46: cada transición del lifecycle queda en una bitácora append-only,
        # independientemente de que el XLSX pueda escribirse en ese instante.
        self._audit_lifecycle_event(event, lifecycle, volume)

        if event == "EXECUTION_FILLED":
            trade_id, created = self._ensure_open_trade(
                lifecycle=lifecycle,
                volume=volume,
            )
            self._export_if_enabled()
            return {
                "event": event,
                "trade_id": trade_id,
                "created": created,
            }

        if event == "EXECUTION_REJECTED":
            return {
                "event": event,
                "trade_id": None,
                "created": False,
            }

        if event == "POSITION_UPDATED":
            trade_id = self._sync_open_trade(
                lifecycle=lifecycle,
                volume=volume,
            )
            self._export_if_enabled()
            return {
                "event": event,
                "trade_id": trade_id,
            }

        if event == "LIFECYCLE_FINALIZED":
            trade_id = self._close_trade(
                lifecycle=lifecycle,
                volume=volume,
            )
            self._export_if_enabled()
            return {
                "event": event,
                "trade_id": trade_id,
            }

        raise ValueError(f"Evento de reporting desconocido: {event}")

    # ============================================================
    # OPERACIÓN ABIERTA
    # ============================================================

    def _ensure_open_trade(self, lifecycle, volume: float | None):
        data = self._build_open_data(lifecycle, volume)

        trade_id, created = self.repository.create_trade_once(data)
        self._remember_trade(lifecycle, trade_id)

        # Si ya existía por idempotencia, actualizamos los datos dinámicos.
        if not created:
            self.repository.update_trade(
                trade_id,
                self._build_open_update(lifecycle, volume),
            )

        return trade_id, created

    def _sync_open_trade(self, lifecycle, volume: float | None):
        trade_id = self._find_trade_id(lifecycle)

        if trade_id is None:
            trade_id, _ = self._ensure_open_trade(
                lifecycle=lifecycle,
                volume=volume,
            )

        self.repository.update_trade(
            trade_id,
            self._build_open_update(lifecycle, volume),
        )
        self._remember_trade(lifecycle, trade_id)
        return trade_id

    # ============================================================
    # OPERACIÓN FINALIZADA
    # ============================================================

    def _close_trade(self, lifecycle, volume: float | None):
        trade_id = self._find_trade_id(lifecycle)

        # En un lifecycle simulado puede no existir ticket. En ese caso
        # registramos primero la operación y después la cerramos.
        if trade_id is None:
            trade_id, _ = self._ensure_open_trade(
                lifecycle=lifecycle,
                volume=volume,
            )

        close_data = {
            **self._build_open_update(lifecycle, volume),
            "result": lifecycle.result,
            "exit_time": lifecycle.exit_time,
            "exit_price": lifecycle.exit_price,
            "exit_reason": lifecycle.exit_reason,
            "bars_held": lifecycle.bars_held,
            "gross_pnl": lifecycle.pnl_price,
            "net_pnl": lifecycle.pnl_price,
            "details": self._build_details(lifecycle),
        }

        self.repository.close_trade(
            trade_id=trade_id,
            data=close_data,
        )
        self._remember_trade(lifecycle, trade_id)
        return trade_id

    # ============================================================
    # CONSTRUCCIÓN DE DATOS
    # ============================================================

    def _build_open_data(self, lifecycle, volume: float | None):
        execution_key = self._execution_key(lifecycle)
        broker = self._broker(lifecycle)

        return {
            "execution_key": execution_key,
            "external_ticket": lifecycle.execution_id or lifecycle.position_ticket,
            "broker_position_ticket": lifecycle.position_ticket,
            "source": self.source,
            "broker": broker,
            "instrument": lifecycle.symbol,
            "timeframe": lifecycle.timeframe,
            "direction": lifecycle.direction,
            "status": "OPEN",
            "entry_time": lifecycle.execution_time or lifecycle.entry_time,
            "entry_price": lifecycle.entry_price,
            "stop_loss": lifecycle.stop_loss,
            "take_profit": lifecycle.take_profit,
            "volume": self._volume(lifecycle, volume),
            "planned_rr": lifecycle.risk_reward_ratio,
            "risk_percent": (lifecycle.metadata or {}).get("risk_percent"),
            "risk_amount": (lifecycle.metadata or {}).get("actual_risk_amount")
                or (lifecycle.metadata or {}).get("risk_amount"),
            "balance_before": (lifecycle.metadata or {}).get("risk_base_value"),
            "equity": (lifecycle.metadata or {}).get("risk_base_value")
                if str((lifecycle.metadata or {}).get("risk_base", "")).upper() == "EQUITY"
                else None,
            "details": self._build_details(lifecycle),
        }

    def _build_open_update(self, lifecycle, volume: float | None):
        return {
            "external_ticket": lifecycle.execution_id or lifecycle.position_ticket,
            "broker_position_ticket": lifecycle.position_ticket,
            "source": self.source,
            "broker": self._broker(lifecycle),
            "instrument": lifecycle.symbol,
            "timeframe": lifecycle.timeframe,
            "direction": lifecycle.direction,
            "status": "OPEN",
            "entry_time": lifecycle.execution_time or lifecycle.entry_time,
            "entry_price": lifecycle.entry_price,
            "stop_loss": lifecycle.stop_loss,
            "take_profit": lifecycle.take_profit,
            "volume": self._volume(lifecycle, volume),
            "planned_rr": lifecycle.risk_reward_ratio,
            "risk_percent": (lifecycle.metadata or {}).get("risk_percent"),
            "risk_amount": (lifecycle.metadata or {}).get("actual_risk_amount")
                or (lifecycle.metadata or {}).get("risk_amount"),
            "balance_before": (lifecycle.metadata or {}).get("risk_base_value"),
            "equity": (lifecycle.metadata or {}).get("risk_base_value")
                if str((lifecycle.metadata or {}).get("risk_base", "")).upper() == "EQUITY"
                else None,
            "details": self._build_details(lifecycle),
        }

    def _build_details(self, lifecycle):
        return {
            "lifecycle_state": lifecycle.state,
            "execution_status": lifecycle.execution_status,
            "execution_id": lifecycle.execution_id,
            "position_ticket": lifecycle.position_ticket,
            "execution_time": self._safe_value(lifecycle.execution_time),
            "metadata": self._safe_value(dict(lifecycle.metadata or {})),
        }

    def _broker(self, lifecycle) -> str:
        configured = self.config.broker
        if configured:
            return str(configured)

        broker = (lifecycle.metadata or {}).get("execution_broker")
        if broker:
            return str(broker)

        return "PAPER" if self.source == "PAPER" else "MT5"

    @staticmethod
    def _volume(lifecycle, volume):
        if volume is not None:
            return float(volume)

        metadata = lifecycle.metadata or {}
        value = metadata.get("volume")
        return None if value is None else float(value)

    # ============================================================
    # BÚSQUEDA / IDEMPOTENCIA
    # ============================================================

    def _find_trade_id(self, lifecycle):
        for key in self._lookup_keys(lifecycle):
            if key in self._trade_ids:
                return self._trade_ids[key]

        execution_key = self._execution_key(lifecycle)
        row = self.repository.get_trade_by_execution_key(execution_key)
        if row is not None:
            trade_id = int(row["id"])
            self._remember_trade(lifecycle, trade_id)
            return trade_id

        if lifecycle.position_ticket:
            row = self.repository.get_trade_by_position_ticket(
                lifecycle.position_ticket
            )
            if row is not None:
                trade_id = int(row["id"])
                self._remember_trade(lifecycle, trade_id)
                return trade_id

        return None

    def _remember_trade(self, lifecycle, trade_id: int):
        for key in self._lookup_keys(lifecycle):
            self._trade_ids[key] = int(trade_id)

    @staticmethod
    def _lookup_keys(lifecycle):
        values = [
            lifecycle.position_ticket,
            lifecycle.execution_id,
        ]
        return [
            str(value)
            for value in values
            if value not in (None, "")
        ]

    @staticmethod
    def _execution_key(lifecycle) -> str:
        metadata = lifecycle.metadata or {}
        explicit_key = metadata.get("execution_key")
        if explicit_key not in (None, ""):
            return str(explicit_key)

        if lifecycle.execution_id not in (None, ""):
            return str(lifecycle.execution_id)

        if lifecycle.position_ticket not in (None, ""):
            return str(lifecycle.position_ticket)

        return "|".join(
            [
                "LIFECYCLE",
                str(lifecycle.symbol),
                str(lifecycle.timeframe),
                str(lifecycle.direction),
                str(lifecycle.entry_time),
            ]
        )

    # ============================================================
    # XLSX
    # ============================================================

    def export_now(self):
        return self.exporter.export(source=self.source)

    def _export_if_enabled(self):
        if not self.config.auto_export:
            return None
        try:
            return self.export_now()
        except Exception as exc:
            # La base de datos es la fuente de verdad. Un Excel abierto/bloqueado
            # no puede invalidar una operación ya persistida.
            saver = getattr(self.repository, "save_audit_event", None)
            if callable(saver):
                try:
                    saver(
                        "REPORT_EXPORT_ERROR",
                        source=self.source,
                        action="XLSX_EXPORT_FAILED",
                        reason=str(exc),
                        payload={"output_path": str(self.exporter.output_path)},
                    )
                except Exception:
                    pass
            return {"exported": False, "error": str(exc), "path": str(self.exporter.output_path)}

    def _audit_lifecycle_event(self, event, lifecycle, volume):
        saver = getattr(self.repository, "save_audit_event", None)
        if not callable(saver):
            return None
        metadata = dict(getattr(lifecycle, "metadata", {}) or {})
        try:
            return saver(
                f"LIFECYCLE_{str(event).upper()}",
                source=self.source,
                instrument=getattr(lifecycle, "symbol", None),
                action=str(event).upper(),
                reason=metadata.get("execution_reason") or getattr(lifecycle, "exit_reason", None),
                execution_key=metadata.get("execution_key"),
                broker_position_ticket=getattr(lifecycle, "position_ticket", None),
                payload={
                    "lifecycle": lifecycle.to_dict() if hasattr(lifecycle, "to_dict") else str(lifecycle),
                    "volume": volume,
                },
            )
        except Exception:
            # La bitácora complementa, pero no debe bloquear el fill ni el cierre.
            return None

    # ============================================================
    # SERIALIZACIÓN SEGURA
    # ============================================================

    @classmethod
    def _safe_value(cls, value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if hasattr(value, "isoformat"):
            return value.isoformat()

        if isinstance(value, dict):
            return {
                str(key): cls._safe_value(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                cls._safe_value(item)
                for item in value
            ]

        return str(value)
