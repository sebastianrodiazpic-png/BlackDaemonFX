"""Puente entre el ciclo de vida de una operacion y su persistencia/exportacion.

Este modulo NO decide nada de trading: solo escucha los eventos que emite el
`TradeLifecycleManager` y los traduce a escrituras en SQLite y a una
regeneracion del Excel.

Flujo de un evento:
    executor -> TradeLifecycleManager -> TradeReportingService.on_lifecycle_event
        -> TradingRepository (create_trade_once / update_trade / close_trade)
        -> TradeReportExporter.export (XLSX)

Principio de resiliencia: la base de datos es la fuente de verdad. Si el Excel
esta abierto o bloqueado por el usuario, el fallo se registra como evento de
auditoria pero NUNCA invalida ni revierte una operacion ya persistida.

Vinculaciones:
    - `reporting.trade_report_exporter.TradeReportExporter`: genera el XLSX.
    - `database.repository.TradingRepository`: destino de toda escritura.
    - `strategy.execution.*`: productores de los objetos `lifecycle`.
"""

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
        """Prepara el servicio y su exportador XLSX asociado.

        Args:
            repository: `TradingRepository` obligatorio; sin el no hay donde
                persistir y se lanza `ValueError` de inmediato para no fallar
                mas tarde, en mitad de un fill.
            config: `TradeReportingConfig`; si es `None` se usa el perfil PAPER.

        Mantiene ademas una cache `position_ticket/execution_id -> trade_id`
        que evita releer SQLite en cada actualizacion de una posicion abierta.
        """
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
        """Punto de entrada unico: traduce un evento del lifecycle a persistencia.

        Args:
            event: `EXECUTION_FILLED`, `EXECUTION_REJECTED`, `POSITION_UPDATED`
                o `LIFECYCLE_FINALIZED`. Cualquier otro valor es un error de
                programacion y lanza `ValueError`.
            lifecycle: objeto con el estado completo de la operacion.
            volume: volumen real confirmado por el broker; si es `None` se toma
                el de `lifecycle.metadata`.

        Returns:
            dict con `event`, `trade_id` y, en las altas, `created`.

        Nota: `EXECUTION_REJECTED` no escribe nada en `trades` porque no llego a
        existir una operacion; solo queda en la bitacora de auditoria.
        """
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
        """Da de alta la operacion de forma idempotente.

        Usa `create_trade_once`, que se apoya en `execution_key` para no
        duplicar filas si el mismo fill se notifica dos veces (reintentos,
        reconexiones del broker). Si la fila ya existia, refresca los campos
        dinamicos en lugar de insertar.

        Returns:
            Tupla `(trade_id, created)`.
        """
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
        """Refresca en SQLite una posicion que sigue abierta (SL/TP/volumen).

        Si no encuentra la fila (por ejemplo el arranque perdio la cache), la
        crea antes de actualizar, de modo que nunca se pierde una posicion viva.
        """
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
        """Cierra la operacion en SQLite con resultado, salida y PnL.

        Guarda `exit_reason` tal cual lo entrego el motor, para que motivos
        estructurales concretos no se degraden a un generico en el Excel.

        En lifecycles simulados puede no existir ticket previo; en ese caso se
        registra primero el alta y despues el cierre, para que la fila quede
        completa.
        """
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
        """Construye el diccionario completo del INSERT de una operacion nueva.

        Incluye las claves de idempotencia (`execution_key`, tickets), los datos
        del plan (entrada, SL, TP, RR) y el contexto de riesgo tomado de
        `lifecycle.metadata`. `equity` solo se rellena si la base de riesgo
        declarada fue EQUITY, para no mezclar balance con equity.
        """
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
        strategy_version = self._strategy_version(lifecycle)
        if strategy_version:
            data["strategy_version"] = strategy_version
        return data

    def _build_open_update(self, lifecycle, volume: float | None):
        """Igual que `_build_open_data` pero sin `execution_key`.

        La clave de ejecucion es inmutable: identifica la fila y jamas debe
        reescribirse en un UPDATE. El resto de campos si se refresca porque el
        SL puede moverse a break-even, el TP escalarse o el volumen reducirse
        con cierres parciales.
        """
        data = {
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
        strategy_version = self._strategy_version(lifecycle)
        if strategy_version:
            data["strategy_version"] = strategy_version
        return data

    def _build_details(self, lifecycle):
        """Empaqueta el contexto no consultable en el JSON `details`.

        Sigue el criterio general del proyecto: columnas para lo que se filtra
        o agrega, y un JSON para conservar el resto integro sin migrar el
        esquema cada vez que aparece un metadato nuevo.
        """
        return {
            "lifecycle_state": lifecycle.state,
            "execution_status": lifecycle.execution_status,
            "execution_id": lifecycle.execution_id,
            "position_ticket": lifecycle.position_ticket,
            "execution_time": self._safe_value(lifecycle.execution_time),
            "metadata": self._safe_value(dict(lifecycle.metadata or {})),
        }

    @staticmethod
    def _strategy_version(lifecycle):
        """Recupera la versión de estrategia guardada en `lifecycle.metadata`.

        El motor (`live_trading_engine.py`) siempre fija
        `metadata["strategy_version"]` al crear el lifecycle, con la versión
        vigente en el momento de la señal. Sin esta lectura, la columna
        dedicada `Trade.strategy_version` nunca se rellenaba y quedaba en su
        valor por defecto (`smc-v1`), lo que rompía la comparativa PRE/POST
        del dashboard (`dashboard.winrate_pre_post`), que depende de esta
        columna para clasificar cada señal.

        Devuelve `None` si no está presente, de modo que la persistencia siga
        aplicando su propio valor por defecto en vez de sobrescribir con un
        `None` explícito.
        """
        value = (lifecycle.metadata or {}).get("strategy_version")
        return str(value) if value else None

    def _broker(self, lifecycle) -> str:
        """Resuelve el broker por prioridad: configuracion, metadatos, defecto.

        El ultimo recurso deduce PAPER cuando la fuente es PAPER y MT5 en
        cualquier otro caso, de modo que la columna nunca queda vacia.
        """
        configured = self.config.broker
        if configured:
            return str(configured)

        broker = (lifecycle.metadata or {}).get("execution_broker")
        if broker:
            return str(broker)

        return "PAPER" if self.source == "PAPER" else "MT5"

    @staticmethod
    def _volume(lifecycle, volume):
        """Prioriza el volumen confirmado por el broker sobre el planificado.

        El parametro `volume` viene del fill real; solo si falta se recurre al
        valor guardado en metadatos, que es la intencion previa y puede diferir
        por normalizacion de lotes del broker.
        """
        if volume is not None:
            return float(volume)

        metadata = lifecycle.metadata or {}
        value = metadata.get("volume")
        return None if value is None else float(value)

    # ============================================================
    # BÚSQUEDA / IDEMPOTENCIA
    # ============================================================

    def _find_trade_id(self, lifecycle):
        """Localiza el `trade_id` en tres niveles, del mas barato al mas caro.

        1. Cache en memoria por ticket / execution_id.
        2. SQLite por `execution_key` (clave de idempotencia).
        3. SQLite por `broker_position_ticket`.

        Returns:
            El id encontrado, o `None` si la operacion aun no existe.
        """
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
        """Indexa el id bajo todas las claves conocidas del lifecycle."""
        for key in self._lookup_keys(lifecycle):
            self._trade_ids[key] = int(trade_id)

    @staticmethod
    def _lookup_keys(lifecycle):
        """Claves de cache utilizables: ticket de posicion e id de ejecucion.

        Se indexan ambas porque el ticket definitivo puede llegar despues del
        id de ejecucion, y asi la operacion se encuentra con cualquiera de los
        dos identificadores.
        """
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
        """Calcula la clave de idempotencia de la operacion.

        Prioridad: `metadata['execution_key']` explicito, id de ejecucion,
        ticket de posicion y, como ultimo recurso, una clave sintetica
        `LIFECYCLE|simbolo|tf|direccion|entrada` para los lifecycles simulados
        que no tienen identificadores de broker.
        """
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
        """Fuerza la regeneracion del XLSX ignorando `auto_export`."""
        return self.exporter.export(source=self.source)

    def _export_if_enabled(self):
        """Exporta el XLSX si esta habilitado, absorbiendo cualquier fallo.

        Un Excel abierto por el usuario provoca `PermissionError`. Ese error se
        registra como evento `REPORT_EXPORT_ERROR` y se devuelve un dict con
        `exported: False`, pero jamas se propaga: la operacion ya esta
        persistida en SQLite y eso es lo que cuenta.
        """
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
        """Deja constancia append-only de la transicion en la bitacora (v46).

        Se ejecuta ANTES de tocar `trades`, para que quede rastro incluso si la
        persistencia posterior falla. Es totalmente tolerante a fallos: si el
        repositorio no expone `save_audit_event`, o si la escritura revienta,
        devuelve `None` en silencio para no bloquear un fill ni un cierre.
        """
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
        """Convierte recursivamente cualquier valor en algo serializable a JSON.

        Escalares se dejan igual, las fechas pasan a ISO-8601, diccionarios y
        secuencias se recorren en profundidad y todo lo demas cae a `str`. Asi
        un metadato exotico nunca rompe el guardado de `details`.
        """
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
