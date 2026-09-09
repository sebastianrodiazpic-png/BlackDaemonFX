"""Repositorio de datos: única API de acceso a la base de datos del proyecto.

Modulo mas extenso de la capa de datos. Concentra TODAS las lecturas y
escrituras, de modo que ningun otro modulo consulta las tablas directamente.

Responsabilidades:
- Persistir senales y operaciones, incluidas las que no se ejecutan.
- Reconciliar con MT5 las operaciones que el broker cerro por su cuenta.
- Mantener el historial permanente `trade_journal`, independiente de la tabla
  operativa `trades`, de modo que un reinicio de estadisticas no borre lo ya
  auditado.
- Registrar auditoria, estado de los workers y snapshots visuales.
- Construir los DataFrames y resumenes que consumen panel e informes.
- Guardar la seleccion de instrumentos del operador.

IDEMPOTENCIA: las escrituras clave (`save_signal_once`, `create_trade`) se
apoyan en claves de ejecucion y tickets para no duplicar registros cuando un
ciclo reprocesa la misma senal o varios workers coinciden.

Vinculaciones:
- Se apoya en `database.database` para sesiones y en `database.models` para
  las tablas.
- Clasifica desenlaces con `trade_outcome_policy` (el de la raiz).
- Lo consumen el motor de ejecucion, los servicios de reporting, el panel y
  el pipeline de backtesting.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import sqlite3

import pandas as pd
from sqlalchemy import delete, func, select, text

from database.database import (
    backup_sqlite_database,
    database_diagnostics,
    get_session_factory,
    init_database,
    resolve_db_path,
)
from database.models import Trade, Signal, AccountSnapshot, TradeJournal, AccountStatsReset, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, DaemonAuditEvent, WorkerRuntimeState, PositionVisualAudit, TradeVisualAudit, TradeAuditSnapshot
from trade_outcome_policy import BREAK_EVEN_RR_TOLERANCE, decisive_outcome, is_break_even_rr


class TradingRepository:
    """
    Capa única de persistencia para:

    - Señales SMC
    - Operaciones
    - Operaciones abiertas
    - Tickets MT5
    - Historial financiero
    - Snapshots de cuenta
    - Sincronización SQLite <-> MT5
    """

    def __init__(self, db_path: str | Path | None = None):
        """Resuelve la base, la inicializa y prepara la fábrica de sesiones.

        Construir el repositorio GARANTIZA que el esquema existe y esta
        migrado: `init_database` crea tablas, columnas e indices ausentes.

        Args:
            db_path: ruta explicita; si falta se usa la ubicacion estable.
        """
        self.db_path = resolve_db_path(db_path)
        init_database(self.db_path)
        self.Session = get_session_factory(self.db_path)

    def database_diagnostics(self):
        """Devuelve el diagnóstico de la base en uso por este repositorio.

        Util para confirmar desde el panel que se esta leyendo el fichero
        esperado tras una actualizacion de version.

        NOTA: el codigo posterior al `return` es inalcanzable y no se ejecuta.
        """
        return database_diagnostics(self.db_path)
        # Migración transparente para instalaciones previas: cualquier trade
        # que ya exista en la tabla operativa se incorpora al journal permanente.
        self.sync_trade_journal()

    # ============================================================
    # HELPERS / NORMALIZACIÓN
    # ============================================================

    @staticmethod
    def _dt(value):
        """
        Convierte distintos formatos de fecha a datetime UTC.
        """

        if value is None:
            return None

        if isinstance(value, float):
            if math.isnan(value):
                return None

        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)

            return value.astimezone(timezone.utc)

        try:
            dt = pd.to_datetime(value, utc=True)

            if pd.isna(dt):
                return None

            return dt.to_pydatetime()

        except Exception:
            return None

    @staticmethod
    def _float_or_none(value):
        """
        Convierte un valor a float o devuelve None.
        """

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return None

        try:
            value = float(value)

            if math.isnan(value):
                return None

            if math.isinf(value):
                return None

            return value

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int_or_none(value):
        """
        Convierte un valor a entero o devuelve None.
        """

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return None

        try:
            return int(float(value))

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _num(value, default=0.0):
        """
        Convierte a float.
        Si falla, devuelve default.
        """

        if value is None:
            return default

        try:
            value = float(value)

            if math.isnan(value):
                return default

            if math.isinf(value):
                return default

            return value

        except (TypeError, ValueError):
            return default

    @staticmethod
    def _none_or_upper(value):
        """
        Convierte texto a MAYÚSCULAS.
        """

        if value is None:
            return None

        value = str(value).strip()

        if value == "":
            return None

        return value.upper()

    @staticmethod
    def _clean_value(value):
        """
        Limpia valores provenientes de pandas / numpy.
        """

        if value is None:
            return None

        try:
            if pd.isna(value):
                return None
        except Exception:
            pass

        if isinstance(value, pd.Timestamp):
            return value.isoformat()

        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, (int, float)):

            try:
                if math.isnan(value):
                    return None
            except Exception:
                pass

            return value

        return str(value)

    @classmethod
    def _json_or_none(cls, value):
        """
        Convierte dict/list/etc. a JSON serializable.
        """

        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if value == "":
                return None

            return value

        try:
            return json.dumps(
                value,
                ensure_ascii=False,
                default=cls._clean_value,
            )

        except Exception:
            return json.dumps(
                {
                    "raw_value": str(value)
                },
                ensure_ascii=False,
            )

    @staticmethod
    def _backtest_ticket(
        instrument,
        timeframe,
        entry_time,
        direction,
        trade_number=None,
        confirmation_time=None,
        setup_time=None,
    ):
        """
        Genera una clave única para evitar duplicar
        operaciones importadas desde backtests.
        """

        parts = [
            "BACKTEST",
            str(instrument or "").strip(),
            str(timeframe or "").strip(),
            str(direction or "").upper().strip(),
        ]

        if entry_time is not None:
            if isinstance(entry_time, datetime):
                parts.append(entry_time.isoformat())
            else:
                parts.append(str(entry_time))

        if trade_number not in (None, "", float("nan")):
            try:
                if not pd.isna(trade_number):
                    parts.append(f"TRADE-{trade_number}")
            except Exception:
                parts.append(f"TRADE-{trade_number}")

        if confirmation_time is not None:
            parts.append(f"CONF-{confirmation_time}")

        if setup_time is not None:
            parts.append(f"SETUP-{setup_time}")

        return "|".join(parts)

    @staticmethod
    def _build_setup_reason(row: dict):
        """
        Construye una descripción del setup SMC.
        """

        parts = []

        setup_type = row.get("setup_type")
        confirmation_type = row.get("confirmation_type")
        zone = row.get("zone")

        if setup_type not in (None, ""):
            parts.append(str(setup_type))

        if confirmation_type not in (None, ""):
            parts.append(str(confirmation_type))

        if zone not in (None, ""):
            parts.append(f"zone={zone}")

        flags = {
            "trend": row.get("trend_ok"),
            "swing": row.get("swing_ok"),
            "liquidity": row.get("liquidity_ok"),
            "sweep": row.get("sweep_ok"),
            "structure_break": row.get("structure_break_ok"),
            "order_block": row.get("order_block_ok"),
            "retest": row.get("retest_ok"),
            "premium_discount": row.get("premium_discount_ok"),
            "confirmation": row.get("confirmation_ok"),
        }

        active_flags = []

        for name, value in flags.items():

            if value is True:
                active_flags.append(name)

            elif isinstance(value, str) and value.strip().lower() in {
                "true",
                "1",
                "yes",
                "si",
                "sí",
            }:
                active_flags.append(name)

        if active_flags:
            parts.append(
                "checks=" + ",".join(active_flags)
            )

        if not parts:
            return None

        return " | ".join(parts)

    # ============================================================
    # SERIALIZACIÓN DE TRADE
    # ============================================================

    def _trade_kwargs(self, data: dict):
        """
        Normaliza datos antes de crear un Trade.
        """

        numeric_fields = {
            "entry_price",
            "exit_price",
            "stop_loss",
            "take_profit",
            "volume",
            "planned_rr",
            "realized_rr",
            "balance_before",
            "balance_after",
            "equity",
            "peak_balance",
            "drawdown_amount",
            "drawdown_percent",
            "risk_percent",
            "risk_amount",
            "gross_pnl",
            "commission",
            "swap",
            "net_pnl",
        }

        datetime_fields = {
            "entry_time",
            "exit_time",
        }

        uppercase_fields = {
            "result",
            "source",
            "direction",
            "status",
        }

        ticket_fields = {
            "execution_key",
            "external_ticket",
            "broker_order_ticket",
            "broker_deal_ticket",
            "broker_position_ticket",
        }

        kwargs = {}

        for key, value in data.items():

            if key == "details":
                kwargs["details_json"] = self._json_or_none(value)
                continue

            if key == "details_json":
                kwargs["details_json"] = self._json_or_none(value)
                continue

            if key in datetime_fields:
                kwargs[key] = self._dt(value)
                continue

            if key in numeric_fields:
                kwargs[key] = self._float_or_none(value)
                continue

            if key == "bars_held":
                kwargs[key] = self._int_or_none(value)
                continue

            if key in uppercase_fields:
                kwargs[key] = self._none_or_upper(value)
                continue

            if key in ticket_fields:
                kwargs[key] = (
                    str(value)
                    if value not in (None, "")
                    else None
                )
                continue

            kwargs[key] = value

        return kwargs

    @staticmethod
    def _trade_dict(row):
        """
        Convierte un objeto Trade de SQLAlchemy a dict.
        """

        if row is None:
            return None

        result = {}

        for column in row.__table__.columns:
            key = column.name
            value = getattr(row, key)

            if key == "details_json" and value:

                if isinstance(value, str):
                    try:
                        result["details"] = json.loads(value)
                    except Exception:
                        result["details"] = value

                else:
                    result["details"] = value

            result[key] = value

        return result

    # ============================================================
    # BITÁCORA OPERATIVA APPEND-ONLY
    # ============================================================

    def save_audit_event(
        self,
        event_type: str,
        *,
        source: str = "DEMO",
        instrument: str | None = None,
        action: str | None = None,
        reason: str | None = None,
        execution_key: str | None = None,
        broker_position_ticket: str | None = None,
        cycle_number: int | None = None,
        payload=None,
        event_time=None,
    ) -> int:
        """Persiste un evento sin sobrescribir eventos anteriores."""
        with self.Session() as session:
            row = DaemonAuditEvent(
                event_time=self._dt(event_time) or datetime.now(timezone.utc),
                source=str(source or "DEMO").upper(),
                event_type=str(event_type or "EVENT").upper(),
                instrument=None if instrument in (None, "") else str(instrument),
                action=None if action in (None, "") else str(action),
                reason=None if reason in (None, "") else str(reason),
                execution_key=None if execution_key in (None, "") else str(execution_key),
                broker_position_ticket=(
                    None if broker_position_ticket in (None, "")
                    else str(broker_position_ticket)
                ),
                cycle_number=self._int_or_none(cycle_number),
                payload_json=self._json_or_none(payload),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

    def meta_label_decision_summary(
        self,
        *,
        source: str | None = None,
        limit: int = 500,
    ) -> dict:
        """Resume las decisiones del meta-etiquetado para la pantalla Cuenta.

        Lee los eventos META_LABEL_* de la bitácora. Estos eventos no están
        sujetos a la política de retención operacional, así que el conteo
        refleja el histórico completo de señales puntuadas por la IA.
        """
        summary = {
            "analyzed_total": 0,
            "shadow_scored": 0,
            "filter_allowed": 0,
            "filter_rejected": 0,
            "trained_decisions": 0,
            "untrained_decisions": 0,
            "average_probability": None,
            "average_net_expectancy_r": None,
            "by_worker": [],
            "rejection_reasons": [],
            "last_trained_at": None,
            "recent_decisions": [],
        }

        try:
            with self.Session() as session:
                rows = session.execute(
                    select(DaemonAuditEvent)
                    .where(DaemonAuditEvent.event_type == "META_LABEL_SIGNAL_SCORED")
                    .where(
                        DaemonAuditEvent.source == str(source).upper()
                        if source else text("1=1")
                    )
                    .order_by(DaemonAuditEvent.event_time.desc(), DaemonAuditEvent.id.desc())
                    .limit(max(1, int(limit)))
                ).scalars().all()

                trained_rows = session.execute(
                    select(DaemonAuditEvent)
                    .where(DaemonAuditEvent.event_type == "META_LABEL_MODEL_TRAINED")
                    .order_by(DaemonAuditEvent.event_time.desc(), DaemonAuditEvent.id.desc())
                    .limit(50)
                ).scalars().all()
        except Exception as exc:
            summary["error"] = str(exc)
            return summary

        workers: dict[str, dict] = {}
        reasons: dict[str, int] = {}
        probabilities: list[float] = []
        expectancies: list[float] = []

        for row in rows:
            try:
                payload = json.loads(row.payload_json) if row.payload_json else {}
            except Exception:
                payload = {}
            decision = payload.get("meta_label") if isinstance(payload, dict) else {}
            if not isinstance(decision, dict):
                decision = {}

            summary["analyzed_total"] += 1
            shadow = bool(decision.get("shadow"))
            allowed = bool(decision.get("allowed", True))
            trained = bool(decision.get("trained"))

            if shadow:
                summary["shadow_scored"] += 1
            elif allowed:
                summary["filter_allowed"] += 1
            else:
                summary["filter_rejected"] += 1

            if trained:
                summary["trained_decisions"] += 1
                # Sin modelo entrenado la probabilidad es 0.0 por convención y
                # promediarla distorsionaría la métrica mostrada.
                try:
                    probabilities.append(float(decision.get("probability") or 0.0))
                    expectancies.append(float(decision.get("net_expectancy_r") or 0.0))
                except (TypeError, ValueError):
                    pass
            else:
                summary["untrained_decisions"] += 1

            worker = str(decision.get("worker") or payload.get("bot_profile") or "DESCONOCIDO")
            entry = workers.setdefault(worker, {
                "worker": worker, "analyzed": 0, "allowed": 0,
                "rejected": 0, "shadow": 0, "trained": False,
            })
            entry["analyzed"] += 1
            entry["trained"] = bool(entry["trained"] or trained)
            if shadow:
                entry["shadow"] += 1
            elif allowed:
                entry["allowed"] += 1
            else:
                entry["rejected"] += 1

            if not allowed and not shadow:
                reason = str(decision.get("reason") or "SIN_MOTIVO")
                reasons[reason] = reasons.get(reason, 0) + 1

            if len(summary["recent_decisions"]) < 25:
                summary["recent_decisions"].append({
                    "event_time": row.event_time.isoformat() if row.event_time else None,
                    "instrument": row.instrument,
                    "worker": worker,
                    "strategy_name": decision.get("strategy_name"),
                    "mode": decision.get("mode"),
                    "probability": decision.get("probability"),
                    "net_expectancy_r": decision.get("net_expectancy_r"),
                    "allowed": allowed,
                    "shadow": shadow,
                    "trained": trained,
                    "reason": decision.get("reason"),
                })

        if probabilities:
            summary["average_probability"] = round(sum(probabilities) / len(probabilities), 4)
        if expectancies:
            summary["average_net_expectancy_r"] = round(sum(expectancies) / len(expectancies), 4)

        summary["by_worker"] = sorted(
            workers.values(), key=lambda item: (-item["analyzed"], item["worker"])
        )
        summary["rejection_reasons"] = sorted(
            ({"reason": key, "count": value} for key, value in reasons.items()),
            key=lambda item: -item["count"],
        )

        for row in trained_rows:
            try:
                payload = json.loads(row.payload_json) if row.payload_json else {}
            except Exception:
                payload = {}
            if isinstance(payload, dict) and payload.get("trained"):
                summary["last_trained_at"] = (
                    row.event_time.isoformat() if row.event_time else None
                )
                break

        return summary

    # Sólo estos eventos de alta frecuencia están sujetos a retención. Las
    # entradas, salidas, incidentes de riesgo, auditorías visuales y journal de
    # trades permanecen fuera de esta política y no se eliminan.
    OPERATIONAL_AUDIT_EVENT_TYPES = (
        "DAEMON_CYCLE_START",
        "SYMBOL_PROCESS_START",
        "SYMBOL_PROCESS_RESULT",
        "POSITION_MONITOR",
        "OPEN_POSITION_STRATEGY_REFRESH",
    )

    def prune_operational_audit_events(
        self,
        *,
        retention_days: int = 14,
        max_rows: int = 250_000,
        batch_size: int = 5_000,
    ) -> dict:
        """Retención incremental sin bloquear SQLite durante una eliminación masiva."""
        retention_days = max(1, int(retention_days))
        max_rows = max(10_000, int(max_rows))
        batch_size = max(100, min(10_000, int(batch_size)))
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted_by_age = 0
        deleted_by_cap = 0

        def delete_batch(where_clause) -> int:
            """Borra un lote acotado de eventos, confirmando en cada pasada.

            Se borra por lotes en transacciones cortas para no mantener SQLite
            bloqueado durante una eliminacion masiva, lo que dejaria a los
            demas workers esperando.

            Returns:
                Numero de filas borradas, o 0 cuando ya no queda nada.
            """
            with self.Session() as session:
                ids = list(session.execute(
                    select(DaemonAuditEvent.id)
                    .where(
                        DaemonAuditEvent.event_type.in_(self.OPERATIONAL_AUDIT_EVENT_TYPES),
                        where_clause,
                    )
                    .order_by(DaemonAuditEvent.id)
                    .limit(batch_size)
                ).scalars())
                if not ids:
                    return 0
                session.execute(delete(DaemonAuditEvent).where(DaemonAuditEvent.id.in_(ids)))
                session.commit()
                return len(ids)

        while True:
            removed = delete_batch(DaemonAuditEvent.event_time < cutoff)
            deleted_by_age += removed
            if removed < batch_size:
                break

        with self.Session() as session:
            operational_count = int(session.execute(
                select(func.count(DaemonAuditEvent.id)).where(
                    DaemonAuditEvent.event_type.in_(self.OPERATIONAL_AUDIT_EVENT_TYPES)
                )
            ).scalar_one())
            boundary_id = None
            if operational_count > max_rows:
                boundary_id = session.execute(
                    select(DaemonAuditEvent.id)
                    .where(DaemonAuditEvent.event_type.in_(self.OPERATIONAL_AUDIT_EVENT_TYPES))
                    .order_by(DaemonAuditEvent.id.desc())
                    .offset(max_rows - 1)
                    .limit(1)
                ).scalar_one_or_none()

        if boundary_id is not None:
            while True:
                removed = delete_batch(DaemonAuditEvent.id < int(boundary_id))
                deleted_by_cap += removed
                if removed < batch_size:
                    break

        return {
            "retention_days": retention_days,
            "max_operational_rows": max_rows,
            "cutoff": cutoff.isoformat(),
            "deleted_by_age": deleted_by_age,
            "deleted_by_cap": deleted_by_cap,
            "deleted_total": deleted_by_age + deleted_by_cap,
            "preserved_event_types": "ALL_EXCEPT_OPERATIONAL_ALLOWLIST",
        }

    def checkpoint_database(self, mode: str = "PASSIVE") -> dict:
        """Checkpoint WAL explícito; TRUNCATE se reserva para mantenimiento coordinado."""
        normalized = str(mode or "PASSIVE").upper()
        if normalized not in {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}:
            raise ValueError(f"Modo de checkpoint no soportado: {mode}")
        connection = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            connection.execute("PRAGMA busy_timeout=30000")
            row = connection.execute(f"PRAGMA wal_checkpoint({normalized})").fetchone()
            connection.execute("PRAGMA optimize")
            return {
                "mode": normalized,
                "busy": int(row[0]) if row else None,
                "wal_pages": int(row[1]) if row else None,
                "checkpointed_pages": int(row[2]) if row else None,
            }
        finally:
            connection.close()

    def create_consistent_backup(self, destination_path=None) -> dict:
        """Crea una copia de seguridad consistente, incluso con el bot operando.

        Usa el mecanismo de backup en caliente de SQLite, que produce una
        copia integra aunque haya escrituras en curso. Copiar el fichero a
        mano mientras el daemon opera si podria dar una copia corrupta.

        Args:
            destination_path: destino explicito; si falta se genera dentro de
                `backups/` con la marca temporal en el nombre.

        Returns:
            Dict con origen, destino y tamano del fichero creado.
        """
        destination = (
            Path(destination_path).expanduser().resolve()
            if destination_path
            else self.db_path.parent / "backups" / (
                "trading_bot_maintenance_"
                + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                + ".sqlite3"
            )
        )
        backup_sqlite_database(self.db_path, destination)
        return {
            "source": str(self.db_path),
            "destination": str(destination),
            "size_bytes": destination.stat().st_size,
        }

    def vacuum_database(self) -> dict:
        """Compactación explícita para ejecutar sólo con el daemon detenido."""
        before = self.db_path.stat().st_size if self.db_path.exists() else 0
        connection = sqlite3.connect(str(self.db_path), timeout=60)
        try:
            connection.execute("PRAGMA busy_timeout=60000")
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            connection.execute("VACUUM")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            connection.execute("PRAGMA optimize")
        finally:
            connection.close()
        after = self.db_path.stat().st_size if self.db_path.exists() else 0
        return {
            "before_bytes": before,
            "after_bytes": after,
            "reclaimed_bytes": max(0, before - after),
            "integrity_check": integrity[0] if integrity else None,
        }

    def maintain_operational_audits(
        self,
        *,
        retention_days: int = 14,
        max_rows: int = 250_000,
        checkpoint_mode: str = "PASSIVE",
    ) -> dict:
        """Ejecuta el mantenimiento periódico de la auditoría operativa.

        Combina en una sola llamada la poda de eventos antiguos, el
        checkpoint del WAL para que el fichero no crezca sin limite, y el
        diagnostico final del estado de la base.

        Args:
            retention_days: dias de eventos que se conservan.
            max_rows: tope de filas por encima del cual se poda aunque sean
                recientes.
            checkpoint_mode: modo del checkpoint WAL; `PASSIVE` no interrumpe
                a los escritores en curso.

        Returns:
            Dict con el resultado de la poda, del checkpoint y el diagnostico.
        """
        retention = self.prune_operational_audit_events(
            retention_days=retention_days,
            max_rows=max_rows,
        )
        return {
            "retention": retention,
            "checkpoint": self.checkpoint_database(checkpoint_mode),
            "database": self.database_diagnostics(),
        }

    def recent_symbol_evaluation_events(
        self,
        *,
        source: str = "DEMO",
        hours: float = 24.0,
    ) -> list[dict]:
        """Datos compactos para evaluar riesgo sin leer toda la auditoría."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max(0.25, float(hours)))
        with self.Session() as session:
            rows = session.execute(
                select(DaemonAuditEvent)
                .where(
                    DaemonAuditEvent.source == str(source or "DEMO").upper(),
                    DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT",
                    DaemonAuditEvent.event_time >= cutoff,
                )
                .order_by(DaemonAuditEvent.event_time, DaemonAuditEvent.id)
            ).scalars().all()
            result = []
            for row in rows:
                payload = {}
                if row.payload_json:
                    try:
                        payload = json.loads(row.payload_json)
                    except Exception:
                        payload = {}
                result.append({
                    "id": int(row.id),
                    "event_time": row.event_time,
                    "instrument": row.instrument,
                    "action": row.action,
                    "reason": row.reason,
                    "payload": payload,
                })
            return result

    def audit_events_dataframe(self, source: str | None = None) -> pd.DataFrame:
        """Devuelve todos los eventos de auditoría como DataFrame.

        Cada `payload_json` se decodifica en la columna `payload`; si no es
        JSON valido se conserva el texto original en lugar de descartarlo.

        Args:
            source: filtra por fuente, p. ej. `DEMO`. Sin valor devuelve todo.

        Returns:
            DataFrame ordenado cronologicamente, vacio si no hay eventos.
        """
        with self.Session() as session:
            stmt = select(DaemonAuditEvent).order_by(
                DaemonAuditEvent.event_time,
                DaemonAuditEvent.id,
            )
            if source:
                stmt = stmt.where(DaemonAuditEvent.source == str(source).upper())
            rows = session.execute(stmt).scalars().all()
            records = []
            for row in rows:
                record = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                if row.payload_json:
                    try:
                        record["payload"] = json.loads(row.payload_json)
                    except Exception:
                        record["payload"] = row.payload_json
                records.append(record)
            return pd.DataFrame(records)

    # ============================================================
    # ESTADO RUNTIME MULTI-BOT
    # ============================================================

    def upsert_worker_runtime_state(
        self,
        bot_profile: str,
        daemon_magic: int,
        *,
        source: str = "DEMO",
        status: str | None = None,
        pid: int | None = None,
        cycle_number: int | None = None,
        symbols_total: int | None = None,
        symbols_processed: int | None = None,
        current_symbol: str | None = None,
        last_action: str | None = None,
        last_reason: str | None = None,
        last_elapsed_seconds: float | None = None,
        details=None,
        event_time=None,
    ):
        """Crea o actualiza el estado en vivo de un worker.

        Es la fila que alimenta el panel: que esta haciendo cada worker, en
        que ciclo va, que simbolo analiza y cuantos lleva procesados.

        Solo se actualizan los campos recibidos con valor no nulo, por lo que
        una llamada parcial no borra la informacion previa. La clave del
        registro es la pareja fuente + perfil, de modo que cada worker
        mantiene exactamente una fila.

        Args:
            bot_profile: perfil del worker, p. ej. `FOREX_1` o `GOLD`.
            daemon_magic: identificador magico de sus operaciones.
            source: entorno, `DEMO` por defecto.
            status: estado actual, p. ej. `RUNNING` o `WAITING_NEW_M5_BAR`.
            pid: proceso del sistema operativo.
            cycle_number: numero de ciclo en curso.
            symbols_total, symbols_processed: progreso del ciclo.
            current_symbol: simbolo que se analiza ahora.
            last_action, last_reason: ultimo desenlace, legible en el panel.
            last_elapsed_seconds: duracion del ultimo paso.
            details: contexto adicional serializado.
            event_time: instante del evento; por defecto, ahora en UTC.
        """
        source = str(source or "DEMO").upper()
        profile = str(bot_profile or "UNKNOWN").upper()
        now = self._dt(event_time) or datetime.now(timezone.utc)
        with self.Session() as session:
            row = (
                session.execute(
                    select(WorkerRuntimeState)
                    .where(
                        WorkerRuntimeState.source == source,
                        WorkerRuntimeState.bot_profile == profile,
                    )
                    .limit(1)
                )
                .scalar_one_or_none()
            )
            if row is None:
                row = WorkerRuntimeState(
                    source=source,
                    bot_profile=profile,
                    daemon_magic=int(daemon_magic),
                    status=str(status or "STARTING").upper(),
                    last_event_time=now,
                )
                session.add(row)

            row.daemon_magic = int(daemon_magic)
            if status is not None:
                row.status = str(status).upper()
            if pid is not None:
                row.pid = int(pid)
            if cycle_number is not None:
                row.cycle_number = int(cycle_number)
            if symbols_total is not None:
                row.symbols_total = int(symbols_total)
            if symbols_processed is not None:
                row.symbols_processed = int(symbols_processed)
            if current_symbol is not None:
                row.current_symbol = str(current_symbol)
            if last_action is not None:
                row.last_action = str(last_action)
            if last_reason is not None:
                row.last_reason = str(last_reason)
            if last_elapsed_seconds is not None:
                row.last_elapsed_seconds = self._float_or_none(last_elapsed_seconds)
            if details is not None:
                row.details_json = self._json_or_none(details)
            row.last_event_time = now
            row.updated_at = now
            session.commit()
            session.refresh(row)
            return row.id

    def worker_runtime_states(self, source: str = "DEMO"):
        """Devuelve el estado en vivo de todos los workers de una fuente.

        Args:
            source: entorno, `DEMO` por defecto.

        Returns:
            Lista de dicts ordenada por perfil, con `details` ya decodificado.
            El panel la usa para mostrar la actividad de cada worker.
        """
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = (
                session.execute(
                    select(WorkerRuntimeState)
                    .where(WorkerRuntimeState.source == source)
                    .order_by(WorkerRuntimeState.bot_profile)
                )
                .scalars()
                .all()
            )
            result = []
            for row in rows:
                item = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                if row.details_json:
                    try:
                        item["details"] = json.loads(row.details_json)
                    except Exception:
                        item["details"] = row.details_json
                result.append(item)
            return result

    # ============================================================
    # AUDITORÍA VISUAL PERSISTENTE
    # ============================================================

    def upsert_position_visual_audit(
        self,
        instrument: str,
        chart,
        *,
        market=None,
        bot_profile: str,
        daemon_magic: int,
        source: str = "DEMO",
        updated_at=None,
    ):
        """Guarda o refresca el contexto gráfico de una posición abierta.

        Persiste los graficos multi-temporal que se generan en el hilo del
        monitor, de modo que el panel pueda mostrarlos sin consultar a MT5
        desde el navegador.

        Mantiene una unica fila por fuente, perfil e instrumento: cada
        refresco sobrescribe la anterior en lugar de acumular historico.

        Args:
            instrument: simbolo, obligatorio.
            chart: estructura con las velas y el contexto por temporalidad.
            market: datos de mercado adicionales.
            bot_profile: worker propietario de la posicion.
            daemon_magic: identificador magico del worker.
            source: entorno, `DEMO` por defecto.
            updated_at: instante del refresco; por defecto, ahora en UTC.

        Returns:
            El identificador de la fila guardada.

        Raises:
            ValueError: si el instrumento viene vacio.
        """
        source = str(source or "DEMO").upper()
        profile = str(bot_profile or "UNKNOWN").upper()
        instrument = str(instrument or "").strip()
        if not instrument:
            raise ValueError("instrument es obligatorio")
        now = self._dt(updated_at) or datetime.now(timezone.utc)
        with self.Session() as session:
            row = (
                session.execute(
                    select(PositionVisualAudit)
                    .where(
                        PositionVisualAudit.source == source,
                        PositionVisualAudit.bot_profile == profile,
                        PositionVisualAudit.instrument == instrument,
                    )
                    .limit(1)
                )
                .scalar_one_or_none()
            )
            if row is None:
                row = PositionVisualAudit(
                    source=source,
                    bot_profile=profile,
                    daemon_magic=int(daemon_magic),
                    instrument=instrument,
                )
                session.add(row)
            row.daemon_magic = int(daemon_magic)
            row.chart_json = self._json_or_none({
                "chart": chart or {},
                "market": market or {},
            })
            row.updated_at = now
            session.commit()
            session.refresh(row)
            return int(row.id)

    def position_visual_audits(self, source: str = "DEMO"):
        """Recupera el contexto gráfico guardado de las posiciones abiertas.

        Incluye compatibilidad hacia atras: las versiones antiguas guardaban
        solo el grafico, sin envolverlo junto a los datos de mercado. Si el
        JSON no trae las claves `chart` y `market`, se interpreta como el
        grafico completo y el mercado queda vacio.

        Args:
            source: entorno, `DEMO` por defecto.

        Returns:
            Lista de dicts, del refresco mas reciente al mas antiguo.
        """
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = (
                session.execute(
                    select(PositionVisualAudit)
                    .where(PositionVisualAudit.source == source)
                    .order_by(PositionVisualAudit.updated_at.desc())
                )
                .scalars()
                .all()
            )
            result = []
            for row in rows:
                try:
                    stored = json.loads(row.chart_json) if row.chart_json else {}
                except Exception:
                    stored = {}
                if isinstance(stored, dict) and ("chart" in stored or "market" in stored):
                    chart = stored.get("chart") or {}
                    market = stored.get("market") or {}
                else:
                    chart = stored if isinstance(stored, dict) else {}
                    market = {}
                result.append({
                    "id": row.id,
                    "source": row.source,
                    "bot_profile": row.bot_profile,
                    "daemon_magic": row.daemon_magic,
                    "instrument": row.instrument,
                    "chart": chart,
                    "market": market,
                    "updated_at": row.updated_at,
                })
            return result

    def upsert_trade_visual_audit(
        self,
        trade_id: int,
        *,
        instrument: str,
        bot_profile: str | None = None,
        daemon_magic: int | None = None,
        broker_position_ticket=None,
        entry_chart=None,
        entry_context=None,
        latest_chart=None,
        latest_market=None,
        source: str = "DEMO",
        updated_at=None,
    ):
        """Congela entry_* sólo una vez; latest_* puede actualizarse."""
        source = str(source or "DEMO").upper()
        now = self._dt(updated_at) or datetime.now(timezone.utc)
        with self.Session() as session:
            row = (
                session.execute(
                    select(TradeVisualAudit)
                    .where(TradeVisualAudit.trade_id == int(trade_id))
                    .limit(1)
                )
                .scalar_one_or_none()
            )
            if row is None:
                row = TradeVisualAudit(
                    trade_id=int(trade_id),
                    source=source,
                    instrument=str(instrument),
                )
                session.add(row)

            # v84: un reset puede reutilizar trade_id. Nunca conservar la tesis
            # congelada de otro instrumento/ticket bajo el nuevo trade.
            identity_changed = bool(
                str(row.instrument or "") != str(instrument)
                or (
                    row.broker_position_ticket
                    and broker_position_ticket not in (None, "")
                    and str(row.broker_position_ticket) != str(broker_position_ticket)
                )
            )
            if identity_changed:
                row.entry_chart_json = None
                row.entry_context_json = None
                row.entry_captured_at = None
                row.latest_chart_json = None
                row.latest_market_json = None
                row.latest_updated_at = None

            row.source = source
            row.instrument = str(instrument)
            if bot_profile:
                row.bot_profile = str(bot_profile).upper()
            if daemon_magic not in (None, ""):
                row.daemon_magic = int(daemon_magic)
            if broker_position_ticket not in (None, ""):
                row.broker_position_ticket = str(broker_position_ticket)

            if not row.entry_chart_json and entry_chart:
                row.entry_chart_json = self._json_or_none(entry_chart)
                row.entry_captured_at = now
            if not row.entry_context_json and entry_context:
                row.entry_context_json = self._json_or_none(entry_context)
                if row.entry_captured_at is None:
                    row.entry_captured_at = now

            if latest_chart is not None:
                row.latest_chart_json = self._json_or_none(latest_chart)
                row.latest_updated_at = now
            if latest_market is not None:
                row.latest_market_json = self._json_or_none(latest_market)
                row.latest_updated_at = now

            row.updated_at = now
            session.commit()
            session.refresh(row)
            return int(row.id)

    def trade_visual_audits(self, source: str = "DEMO"):
        """Recupera la auditoría visual asociada a operaciones concretas.

        A diferencia de `position_visual_audits`, aqui se conserva la imagen
        del momento de ENTRADA, que solo se escribe una vez y no se
        sobrescribe, junto al ultimo estado. Esa pareja permite comparar como
        se veia el mercado al entrar frente a como esta ahora.

        Args:
            source: entorno, `DEMO` por defecto.

        Returns:
            Lista de dicts con los graficos y contextos ya decodificados.
        """
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = (
                session.execute(
                    select(TradeVisualAudit)
                    .where(TradeVisualAudit.source == source)
                    .order_by(TradeVisualAudit.updated_at.desc())
                )
                .scalars()
                .all()
            )
            def decode(value):
                """Decodifica un campo JSON a dict, o `{}` si no es utilizable."""
                if not value:
                    return {}
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, dict) else {}
                except Exception:
                    return {}
            return [{
                "trade_id": row.trade_id,
                "source": row.source,
                "bot_profile": row.bot_profile,
                "daemon_magic": row.daemon_magic,
                "instrument": row.instrument,
                "broker_position_ticket": row.broker_position_ticket,
                "entry_chart": decode(row.entry_chart_json),
                "entry_context": decode(row.entry_context_json),
                "entry_captured_at": row.entry_captured_at,
                "latest_chart": decode(row.latest_chart_json),
                "latest_market": decode(row.latest_market_json),
                "latest_updated_at": row.latest_updated_at,
            } for row in rows]

    def save_trade_audit_snapshot(
        self,
        trade_id: int,
        *,
        instrument: str,
        entry_view=None,
        current_view=None,
        market=None,
        visual_context=None,
        bot_profile: str | None = None,
        daemon_magic: int | None = None,
        broker_position_ticket=None,
        source: str = "DEMO",
        snapshot_at=None,
    ):
        """Append-only: una fila por observación Entrada vs. Ahora."""
        now = self._dt(snapshot_at) or datetime.now(timezone.utc)
        with self.Session() as session:
            row = TradeAuditSnapshot(
                trade_id=int(trade_id),
                source=str(source or "DEMO").upper(),
                bot_profile=(str(bot_profile).upper() if bot_profile else None),
                daemon_magic=(int(daemon_magic) if daemon_magic not in (None, "") else None),
                instrument=str(instrument),
                broker_position_ticket=(str(broker_position_ticket) if broker_position_ticket not in (None, "") else None),
                snapshot_at=now,
                entry_view_json=self._json_or_none(entry_view or {}),
                current_view_json=self._json_or_none(current_view or {}),
                market_json=self._json_or_none(market or {}),
                visual_context_json=self._json_or_none(visual_context or {}),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return int(row.id)

    def trade_audit_snapshots(self, *, trade_id=None, source: str = "DEMO", limit=None):
        """Recupera el histórico de snapshots de auditoría de operaciones.

        A diferencia de las auditorias visuales, que mantienen una unica fila
        por operacion, aqui cada snapshot se ACUMULA. Eso permite reconstruir
        la evolucion de una operacion a lo largo de su vida.

        Args:
            trade_id: limita a una operacion concreta; sin valor, todas.
            source: entorno, `DEMO` por defecto.
            limit: numero maximo de snapshots devueltos.

        Returns:
            Lista de dicts, del mas reciente al mas antiguo, con las vistas
            de entrada y actual, el mercado y el contexto visual decodificados.
        """
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            stmt = select(TradeAuditSnapshot).where(TradeAuditSnapshot.source == source)
            if trade_id is not None:
                stmt = stmt.where(TradeAuditSnapshot.trade_id == int(trade_id))
            stmt = stmt.order_by(TradeAuditSnapshot.snapshot_at.desc(), TradeAuditSnapshot.id.desc())
            if limit is not None:
                stmt = stmt.limit(max(1, int(limit)))
            rows = session.execute(stmt).scalars().all()

            def decode(value):
                """Decodifica un campo JSON a dict, o `{}` si no es utilizable."""
                if not value:
                    return {}
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, dict) else {}
                except Exception:
                    return {}

            return [{
                "id": row.id,
                "trade_id": row.trade_id,
                "source": row.source,
                "bot_profile": row.bot_profile,
                "daemon_magic": row.daemon_magic,
                "instrument": row.instrument,
                "broker_position_ticket": row.broker_position_ticket,
                "snapshot_at": row.snapshot_at,
                "entry_view": decode(row.entry_view_json),
                "current_view": decode(row.current_view_json),
                "market": decode(row.market_json),
                "visual_context": decode(row.visual_context_json),
            } for row in rows]

    def trade_visual_audit_entry_contexts(self, *, source: str = "DEMO") -> dict[str, dict]:
        """Devuelve sólo el contexto inmutable de entrada para Cuenta activa."""
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = session.execute(
                select(TradeVisualAudit.trade_id, TradeVisualAudit.entry_context_json)
                .where(TradeVisualAudit.source == source)
            ).all()
        contexts = {}
        for trade_id, entry_context_json in rows:
            if trade_id is None or not entry_context_json:
                continue
            try:
                entry_context = json.loads(entry_context_json)
            except (TypeError, ValueError):
                continue
            if isinstance(entry_context, dict):
                contexts[str(trade_id)] = entry_context
        return contexts

    def trade_audit_snapshot_summaries(self, *, source: str = "DEMO") -> dict[str, dict]:
        """Cuenta y fecha más reciente por trade sin cargar snapshots JSON."""
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = session.execute(
                select(
                    TradeAuditSnapshot.trade_id,
                    func.count(TradeAuditSnapshot.id),
                    func.max(TradeAuditSnapshot.snapshot_at),
                )
                .where(TradeAuditSnapshot.source == source)
                .group_by(TradeAuditSnapshot.trade_id)
            ).all()
        return {
            str(trade_id): {
                "count": int(count),
                "latest_snapshot_at": latest_snapshot_at,
            }
            for trade_id, count, latest_snapshot_at in rows
            if trade_id is not None
        }

    def trade_audit_snapshots_dataframe(self, source: str = "DEMO"):
        """Aplana los snapshots de auditoría en un DataFrame comparable.

        Extrae de las estructuras anidadas los campos relevantes y los coloca
        en columnas planas con prefijo `entry_` o `current_`. Esa disposicion
        permite comparar de un vistazo como estaba el analisis al ENTRAR
        frente a como esta AHORA: si la direccion cambio, si el score cayo, si
        aparecio un patron contrario.

        Es la vista clave para investigar por que se cerro una operacion.

        Args:
            source: entorno, `DEMO` por defecto.

        Returns:
            DataFrame con una fila por snapshot.
        """
        rows = self.trade_audit_snapshots(source=source)
        flat = []
        for row in rows:
            entry = row.get("entry_view") or {}
            current = row.get("current_view") or {}
            market = row.get("market") or {}
            visual = row.get("visual_context") or {}
            flat.append({
                "snapshot_id": row.get("id"),
                "trade_id": row.get("trade_id"),
                "snapshot_at": row.get("snapshot_at"),
                "source": row.get("source"),
                "bot_profile": row.get("bot_profile"),
                "daemon_magic": row.get("daemon_magic"),
                "instrument": row.get("instrument"),
                "broker_position_ticket": row.get("broker_position_ticket"),
                "entry_decision": entry.get("decision"),
                "entry_direction": entry.get("direction"),
                "entry_score": entry.get("score"),
                "entry_confirmation_pct": entry.get("confirmation_percentage"),
                "entry_h1_trend": entry.get("h1_trend"),
                "entry_structure_break": entry.get("structure_break"),
                "entry_zone": entry.get("zone"),
                "entry_chart_pattern": entry.get("chart_pattern_name"),
                "current_decision": current.get("decision") or current.get("state"),
                "current_reason": current.get("reason"),
                "current_direction": current.get("direction"),
                "current_score": current.get("score"),
                "current_confirmation_pct": current.get("confirmation_percentage"),
                "current_h1_trend": current.get("h1_trend"),
                "current_structure_break": current.get("structure_break"),
                "current_zone": current.get("zone"),
                "current_chart_pattern": current.get("chart_pattern_name"),
                "current_chart_pattern_strength": current.get("chart_pattern_strength"),
                "current_chart_pattern_conflict": current.get("chart_pattern_conflict"),
                "current_price": market.get("current_price"),
                "current_rr": market.get("current_rr"),
                "current_stop_loss": market.get("current_stop_loss"),
                "take_profit": market.get("take_profit"),
                "recommendation": market.get("recommendation"),
                "entry_view_json": json.dumps(entry, ensure_ascii=False, separators=(",", ":")),
                "current_view_json": json.dumps(current, ensure_ascii=False, separators=(",", ":")),
                "market_json": json.dumps(market, ensure_ascii=False, separators=(",", ":")),
                "visual_context_json": json.dumps(visual, ensure_ascii=False, separators=(",", ":")),
            })
        return pd.DataFrame(flat)

    def latest_worker_process_results(self, source: str = "DEMO", limit: int = 500):
        """Último SYMBOL_PROCESS_RESULT por bot_profile desde auditoría append-only."""
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = (
                session.execute(
                    select(DaemonAuditEvent)
                    .where(
                        DaemonAuditEvent.source == source,
                        DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT",
                    )
                    .order_by(DaemonAuditEvent.event_time.desc(), DaemonAuditEvent.id.desc())
                    .limit(max(20, int(limit)))
                )
                .scalars()
                .all()
            )
            found = {}
            for row in rows:
                try:
                    payload = json.loads(row.payload_json) if row.payload_json else {}
                except Exception:
                    payload = {}
                if not isinstance(payload, dict):
                    continue
                profile = str(payload.get("bot_profile") or "").upper()
                if not profile or profile in found:
                    continue
                result = payload.get("result")
                if not isinstance(result, dict):
                    result = {}
                item = dict(result)
                item.setdefault("symbol", row.instrument)
                item["_bot_profile"] = profile
                item["_daemon_magic"] = payload.get("daemon_magic")
                item["_event_time"] = row.event_time
                item["_cycle_number"] = row.cycle_number
                item["_action"] = row.action
                found[profile] = item
            return found

    @staticmethod
    def _infer_audit_profile(payload: dict, result: dict, instrument: str | None = None):
        """Deduce a qué worker pertenece un evento de auditoría antiguo.

        Los eventos recientes ya traen `bot_profile`, pero los generados por
        versiones anteriores no. Para no perderlos, se infiere en cascada:

        1. El `bot_profile` explicito del evento.
        2. El numero magico, que identifica de forma unica a cada worker.
        3. Como ultimo recurso, la accion y el nombre del simbolo.

        Args:
            payload: contenido del evento auditado.
            result: resultado asociado al evento.
            instrument: simbolo, si no viene dentro del resultado.

        Returns:
            El perfil del worker deducido.
        """
        profile = str((payload or {}).get("bot_profile") or "").upper()
        if profile:
            return profile

        magic = (payload or {}).get("daemon_magic")
        magic_map = {
            26082028: "ORB",
            26082101: "BOOM",
            26082102: "CRASH",
            26082103: "VOLATILITY",
            26082401: "VOLATILITY_1",
            26082402: "VOLATILITY_2",
            26082403: "VOLATILITY_3",
            26082404: "VOLATILITY_4",
            26082104: "STEP",
            26082105: "JUMP",
            26082106: "FLIP",
            26082201: "FOREX_1",
            26082202: "FOREX_2",
            26082203: "FOREX_3",
            26082204: "FOREX_4",
        }
        try:
            if int(magic) in magic_map:
                return magic_map[int(magic)]
        except Exception:
            pass

        action = str((result or {}).get("action") or "").upper()
        symbol = str(instrument or (result or {}).get("symbol") or "").upper()
        if action.startswith("WAITING_NEW_YORK") or action.startswith("ORB_"):
            return "ORB"
        if "BOOM" in symbol and "CRASH" not in symbol:
            return "BOOM"
        if "CRASH" in symbol and "BOOM" not in symbol:
            return "CRASH"
        if "VOLATILITY" in symbol:
            return "VOLATILITY"
        if "STEP" in symbol:
            return "STEP"
        if "JUMP" in symbol:
            return "JUMP"
        if "FLIP" in symbol:
            return "FLIP"
        return "UNKNOWN"

    def recent_symbol_process_results(
        self,
        source: str = "DEMO",
        limit: int = 120,
        per_profile: int = 12,
        scan_limit: int = 2500,
    ):
        """Panel equilibrado de análisis recientes de todos los workers.

        Un ORB esperando apertura de NY puede generar cientos de eventos rápidos.
        Si sólo se toman las últimas N filas globales, desplaza de la pantalla a
        Forex y sintéticos. Esta versión:
        1. examina un pool amplio;
        2. conserva el resultado más reciente por profile+symbol+action;
        3. limita cada profile;
        4. mezcla cronológicamente los perfiles resultantes.
        """
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            rows = (
                session.execute(
                    select(DaemonAuditEvent)
                    .where(
                        DaemonAuditEvent.source == source,
                        DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT",
                    )
                    .order_by(DaemonAuditEvent.event_time.desc(), DaemonAuditEvent.id.desc())
                    .limit(max(int(limit), int(scan_limit)))
                )
                .scalars()
                .all()
            )

        grouped = {}
        dedupe = set()
        for row in rows:
            try:
                payload = json.loads(row.payload_json) if row.payload_json else {}
            except Exception:
                payload = {}
            if not isinstance(payload, dict):
                payload = {}

            result = payload.get("result")
            if not isinstance(result, dict):
                result = {}
            item = dict(result)
            item.setdefault("symbol", row.instrument)

            profile = self._infer_audit_profile(payload, item, row.instrument)
            action = str(item.get("action") or row.action or "")
            symbol = str(item.get("symbol") or row.instrument or "")
            signature = (profile, symbol.upper(), action.upper())
            if signature in dedupe:
                continue
            dedupe.add(signature)

            item["_bot_profile"] = profile
            item["_daemon_magic"] = payload.get("daemon_magic")
            item["_event_time"] = row.event_time
            item["_cycle_number"] = row.cycle_number
            item["_action"] = row.action

            bucket = grouped.setdefault(profile, [])
            if len(bucket) < max(1, int(per_profile)):
                bucket.append(item)

        # Orden cronológico global después de dar cupo a cada worker.
        combined = [item for bucket in grouped.values() for item in bucket]
        combined.sort(
            key=lambda item: item.get("_event_time") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return combined[:max(1, int(limit))]

    def latest_symbol_process_result(self, instrument: str, source: str = "DEMO"):
        """Último análisis persistido del símbolo, independiente del dashboard local."""
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            row = (
                session.execute(
                    select(DaemonAuditEvent)
                    .where(
                        DaemonAuditEvent.source == source,
                        DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT",
                        DaemonAuditEvent.instrument == str(instrument),
                    )
                    .order_by(DaemonAuditEvent.event_time.desc(), DaemonAuditEvent.id.desc())
                    .limit(1)
                )
                .scalar_one_or_none()
            )
            if row is None:
                return {}
            try:
                payload = json.loads(row.payload_json) if row.payload_json else {}
            except Exception:
                payload = {}
            result = payload.get("result") if isinstance(payload, dict) else {}
            if not isinstance(result, dict):
                result = {}
            result = dict(result)
            result.setdefault("symbol", row.instrument)
            result["_bot_profile"] = payload.get("bot_profile") if isinstance(payload, dict) else None
            result["_daemon_magic"] = payload.get("daemon_magic") if isinstance(payload, dict) else None
            result["_event_time"] = row.event_time
            return result

    # ============================================================
    # JOURNAL HISTÓRICO PERMANENTE
    # ============================================================

    @staticmethod
    def _journal_key(trade: dict) -> str:
        """Clave estable para que un mismo trade no se duplique al reiniciar."""
        source = str(trade.get("source") or "LIVE").upper()
        for name in ("broker_position_ticket", "execution_key", "external_ticket"):
            value = trade.get(name)
            if value not in (None, ""):
                return f"{source}:{name}:{value}"
        entry = trade.get("entry_time")
        if hasattr(entry, "isoformat"):
            entry = entry.isoformat()
        return "SEMANTIC:%s:%s:%s:%s:%s" % (
            source, trade.get("instrument") or "", trade.get("direction") or "",
            entry or "", trade.get("entry_price") if trade.get("entry_price") is not None else "",
        )

    def _upsert_trade_journal_session(self, session, trade_row):
        """Copia una operación al historial permanente dentro de una sesión abierta.

        `trade_journal` es INDEPENDIENTE de `trades` a proposito: un reinicio
        de estadisticas puede vaciar la tabla operativa sin perder el
        historial auditado.

        La identidad se establece mediante `journal_key`, derivada de la
        operacion, de modo que reprocesar la misma operacion la actualiza en
        lugar de duplicarla.

        No confirma la transaccion: eso corresponde a quien la abrio, lo que
        permite archivar muchas operaciones en un unico commit.

        Args:
            session: sesion ORM ya abierta.
            trade_row: fila ORM o dict de la operacion.

        Returns:
            La fila del journal creada o actualizada.
        """
        trade = self._trade_dict(trade_row) if not isinstance(trade_row, dict) else dict(trade_row)
        key = self._journal_key(trade)
        row = session.execute(select(TradeJournal).where(TradeJournal.journal_key == key)).scalar_one_or_none()
        values = {
            "source_trade_id": trade.get("id"), "source": str(trade.get("source") or "LIVE").upper(),
            "broker": str(trade.get("broker") or "MT5"), "instrument": str(trade.get("instrument") or ""),
            "direction": str(trade.get("direction") or "").upper(), "status": str(trade.get("status") or "OPEN").upper(),
            "result": self._none_or_upper(trade.get("result")), "entry_time": self._dt(trade.get("entry_time")),
            "exit_time": self._dt(trade.get("exit_time")), "entry_price": self._float_or_none(trade.get("entry_price")),
            "exit_price": self._float_or_none(trade.get("exit_price")), "stop_loss": self._float_or_none(trade.get("stop_loss")),
            "take_profit": self._float_or_none(trade.get("take_profit")), "volume": self._float_or_none(trade.get("volume")),
            "planned_rr": self._float_or_none(trade.get("planned_rr")), "realized_rr": self._float_or_none(trade.get("realized_rr")),
            "risk_percent": self._float_or_none(trade.get("risk_percent")), "risk_amount": self._float_or_none(trade.get("risk_amount")),
            "net_pnl": self._num(trade.get("net_pnl"), 0.0), "execution_key": trade.get("execution_key"),
            "external_ticket": trade.get("external_ticket"), "broker_position_ticket": trade.get("broker_position_ticket"),
            "strategy_version": str(trade.get("strategy_version") or "smc-v1"),
            "details_json": self._json_or_none(trade.get("details") if "details" in trade else trade.get("details_json")),
            "last_seen_at": datetime.now(timezone.utc),
        }
        if row is None:
            row = TradeJournal(journal_key=key, **values)
            session.add(row)
        else:
            for name, value in values.items():
                setattr(row, name, value)
        return row

    def sync_trade_journal(self):
        """Copia al journal cualquier trade operativo previo que aún no esté archivado."""
        with self.Session() as session:
            rows = session.execute(select(Trade)).scalars().all()
            for row in rows:
                self._upsert_trade_journal_session(session, row)
            session.commit()
            return len(rows)

    def trade_history_dataframe(self, source: str | None = None):
        """Devuelve el historial permanente de operaciones como DataFrame.

        Lee de `trade_journal`, no de `trades`, por lo que incluye tambien las
        operaciones anteriores a un reinicio de estadisticas. Es la fuente que
        alimenta la pantalla de Cuenta y el entrenamiento del modelo de IA.

        Args:
            source: filtra por entorno; sin valor devuelve todo.

        Returns:
            DataFrame ordenado por fecha de entrada.
        """
        with self.Session() as session:
            stmt = select(TradeJournal).order_by(TradeJournal.entry_time, TradeJournal.id)
            if source:
                stmt = stmt.where(TradeJournal.source == str(source).upper())
            rows = session.execute(stmt).scalars().all()
            records = []
            for row in rows:
                d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                d["id"] = row.id
                if row.details_json:
                    try: d["details"] = json.loads(row.details_json)
                    except Exception: d["details"] = row.details_json
                records.append(d)
            return pd.DataFrame(records)

    def latest_account_stats_reset(self, source: str = "DEMO"):
        """Devuelve la marca persistente más reciente para reiniciar estadísticas."""
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            row = (
                session.execute(
                    select(AccountStatsReset)
                    .where(AccountStatsReset.source == source)
                    .order_by(AccountStatsReset.reset_time.desc(), AccountStatsReset.id.desc())
                    .limit(1)
                )
                .scalar_one_or_none()
            )
        if row is None:
            return None
        return {
            "id": row.id,
            "source": row.source,
            "reset_time": row.reset_time,
            "reason": row.reason,
            "created_at": row.created_at,
        }

    def reset_account_statistics(self, source: str = "DEMO", reason: str = "MANUAL_RESET"):
        """Inicia una nueva ventana estadística sin borrar trades ni posiciones abiertas.

        Los cierres anteriores a ``reset_time`` dejan de participar en Cuenta activa.
        Una posición que ya estaba OPEN al reset se conserva y, si cierra después,
        su resultado sí será contabilizado en la nueva ventana.
        """
        source = str(source or "DEMO").upper()
        now = datetime.now(timezone.utc)
        previous = self.latest_account_stats_reset(source=source)
        with self.Session() as session:
            row = AccountStatsReset(
                reset_time=now,
                source=source,
                reason=str(reason or "MANUAL_RESET"),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            reset_id = row.id

        # Sólo informativo: no modificamos ni borramos filas del journal.
        frame = self.account_trade_history_dataframe(source=source, apply_stats_reset=False)
        before_total = 0 if frame is None or frame.empty else len(frame)
        before_open = 0
        before_closed = 0
        if frame is not None and not frame.empty:
            statuses = frame["status"].astype(str).str.upper()
            before_open = int((statuses == "OPEN").sum())
            before_closed = int((statuses != "OPEN").sum())

        return {
            "ok": True,
            "reset_id": reset_id,
            "source": source,
            "reset_time": now,
            "previous_reset_time": previous.get("reset_time") if previous else None,
            "historical_rows_preserved": before_total,
            "open_positions_preserved": before_open,
            "closed_rows_hidden_from_new_window": before_closed,
        }

    def account_trade_history_dataframe(
        self,
        source: str | None = None,
        apply_stats_reset: bool = True,
    ):
        """Historial DB-only usado por Cuenta activa.

        Conserva sólo filas originadas en la tabla operacional y, cuando existe
        un reset estadístico, muestra:
        - todas las posiciones actualmente OPEN;
        - cierres cuya ``exit_time`` ocurrió desde el último reset.

        Los cierres previos siguen físicamente en ``trade_journal`` para auditoría.
        """
        source_norm = str(source).upper() if source else None
        with self.Session() as session:
            stmt = (
                select(TradeJournal)
                .where(TradeJournal.source_trade_id.is_not(None))
                .order_by(TradeJournal.entry_time, TradeJournal.id)
            )
            if source_norm:
                stmt = stmt.where(TradeJournal.source == source_norm)
            rows = session.execute(stmt).scalars().all()

            reset_time = None
            if apply_stats_reset:
                reset_stmt = select(AccountStatsReset).order_by(
                    AccountStatsReset.reset_time.desc(), AccountStatsReset.id.desc()
                )
                if source_norm:
                    reset_stmt = reset_stmt.where(AccountStatsReset.source == source_norm)
                reset_row = session.execute(reset_stmt.limit(1)).scalar_one_or_none()
                reset_time = self._dt(reset_row.reset_time) if reset_row else None

            records = []
            for row in rows:
                status = str(row.status or "").upper()
                if reset_time is not None and status != "OPEN":
                    exit_time = self._dt(row.exit_time)
                    if exit_time is None or exit_time < reset_time:
                        continue

                d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
                d["id"] = row.id
                if row.details_json:
                    try:
                        d["details"] = json.loads(row.details_json)
                    except Exception:
                        d["details"] = row.details_json
                records.append(d)
            return pd.DataFrame(records)

    # ============================================================
    # INSTRUMENT SELECTION PREFERENCES
    # ============================================================

    def save_instrument_selection(self, selected_symbols, source: str = "DEMO"):
        """Persiste la selección completa de instrumentos como preferencia de usuario."""
        source = str(source or "DEMO").upper()
        normalized = []
        seen = set()
        for symbol in selected_symbols or []:
            value = str(symbol or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        if not normalized:
            raise ValueError("La selección persistente requiere al menos un instrumento.")

        with self.Session() as session:
            previous = (
                session.execute(
                    select(InstrumentSelectionPreference)
                    .where(InstrumentSelectionPreference.source == source)
                    .order_by(
                        InstrumentSelectionPreference.updated_at.desc(),
                        InstrumentSelectionPreference.id.desc(),
                    )
                    .limit(1)
                )
                .scalar_one_or_none()
            )
            version = int(previous.version or 0) + 1 if previous else 1
            row = InstrumentSelectionPreference(
                source=source,
                selected_symbols_json=json.dumps(normalized, ensure_ascii=False),
                version=version,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(row)
            session.commit()
            session.refresh(row)

        result = {
            "id": row.id,
            "source": row.source,
            "selected_symbols": normalized,
            "version": row.version,
            "updated_at": row.updated_at,
        }
        try:
            self.save_audit_event(
                "INSTRUMENT_SELECTION_CHANGED",
                source=source,
                action="SELECTION_PERSISTED",
                payload=result,
            )
        except Exception:
            pass
        return result

    @staticmethod
    def _normalize_selection_profile(profile: str | None) -> str:
        """Normaliza y valida un perfil de selección de instrumentos.

        Se admiten `SYNTHETICS`, `FOREX`, `ORB` e `IDX_OPEN` (Apertura de
        Índices Bursátiles, con selección persistente independiente de ORB).
        Rechazar cualquier otro valor evita guardar una seleccion bajo un
        perfil inexistente que despues nadie leeria.

        Args:
            profile: perfil recibido; sin valor se asume `SYNTHETICS`.

        Returns:
            El perfil en mayusculas.

        Raises:
            ValueError: si el perfil no es uno de los soportados.
        """
        value = str(profile or "SYNTHETICS").upper().strip()
        if value not in {"SYNTHETICS", "FOREX", "ORB", "IDX_OPEN"}:
            raise ValueError(f"Perfil de selección no soportado: {value}")
        return value

    def save_instrument_selection_profile(self, selected_symbols, *, selection_profile: str, source: str = "DEMO"):
        """Guarda una única selección autoritativa por perfil.

        v57 elimina ambigüedad entre varias versiones históricas. El historial del
        cambio sigue quedando en daemon_audit_events, mientras esta tabla conserva
        exactamente el estado vigente que debe sobrevivir a reinicios.
        """
        source = str(source or "DEMO").upper()
        profile = self._normalize_selection_profile(selection_profile)
        normalized, seen = [], set()
        for symbol in selected_symbols or []:
            value = str(symbol or "").strip()
            if value and value not in seen:
                seen.add(value); normalized.append(value)

        now = datetime.now(timezone.utc)
        with self.Session() as session:
            rows = list(session.execute(
                select(InstrumentSelectionProfilePreference)
                .where(InstrumentSelectionProfilePreference.source == source,
                       InstrumentSelectionProfilePreference.selection_profile == profile)
                .order_by(InstrumentSelectionProfilePreference.id.asc())
            ).scalars())

            if rows:
                row = rows[0]
                version = max(int(r.version or 0) for r in rows) + 1
                row.selected_symbols_json = json.dumps(normalized, ensure_ascii=False)
                row.version = version
                row.updated_at = now
                # Compactar instalaciones v56 que pudieran tener varias filas.
                for duplicate in rows[1:]:
                    session.delete(duplicate)
            else:
                row = InstrumentSelectionProfilePreference(
                    source=source,
                    selection_profile=profile,
                    selected_symbols_json=json.dumps(normalized, ensure_ascii=False),
                    version=1,
                    updated_at=now,
                )
                session.add(row)

            session.commit()
            session.refresh(row)
            row_id = row.id
            row_version = row.version
            row_updated_at = row.updated_at

        result={"id":row_id,"source":source,"selection_profile":profile,
                "selected_symbols":normalized,"version":row_version,"updated_at":row_updated_at}

        # Verificación read-after-write: si SQLAlchemy no devuelve exactamente lo
        # recién guardado, el dashboard debe considerarlo un error, no un éxito.
        verify = self.latest_instrument_selection_profile(profile, source=source)
        if verify is None or verify.get("selected_symbols") != normalized:
            raise RuntimeError(
                f"Persistencia no verificada para {profile}: "
                f"guardado={normalized!r}, leído={(verify or {}).get('selected_symbols')!r}"
            )

        try:
            self.save_audit_event("INSTRUMENT_SELECTION_PROFILE_CHANGED", source=source,
                                  action="PROFILE_SELECTION_PERSISTED_VERIFIED", reason=profile, payload=result)
        except Exception:
            pass
        return result

    def latest_instrument_selection_profile(self, selection_profile: str, *, source: str = "DEMO"):
        """Recupera la selección de instrumentos vigente para un perfil.

        Devuelve solo la fila mas reciente: la seleccion es un estado actual,
        no un historico. El registro del cambio queda en la auditoria.

        Args:
            selection_profile: `SYNTHETICS`, `FOREX` u `ORB`.
            source: entorno, `DEMO` por defecto.

        Returns:
            Dict con los simbolos seleccionados y la version, o `None` si
            nunca se guardo una seleccion para ese perfil, lo que indica al
            worker que debe operar su lista completa.
        """
        source=str(source or "DEMO").upper(); profile=self._normalize_selection_profile(selection_profile)
        with self.Session() as session:
            row=session.execute(
                select(InstrumentSelectionProfilePreference)
                .where(InstrumentSelectionProfilePreference.source == source,
                       InstrumentSelectionProfilePreference.selection_profile == profile)
                .order_by(InstrumentSelectionProfilePreference.updated_at.desc(),
                          InstrumentSelectionProfilePreference.id.desc()).limit(1)
            ).scalar_one_or_none()
        if row is None: return None
        try: selected=json.loads(row.selected_symbols_json or "[]")
        except Exception: selected=[]
        if not isinstance(selected,list): selected=[]
        selected=[str(v).strip() for v in selected if str(v).strip()]
        return {"id":row.id,"source":row.source,"selection_profile":profile,
                "selected_symbols":selected,"version":row.version,"updated_at":row.updated_at}

    def latest_instrument_selection_profiles(self, source: str = "DEMO"):
        """Devuelve la selección vigente de los tres perfiles a la vez.

        Los perfiles sin seleccion guardada se OMITEN del resultado, en lugar
        de aparecer vacios: ausencia significa "sin restriccion", mientras que
        una lista vacia significaria "ningun simbolo".

        Returns:
            Dict `perfil -> seleccion`, solo con los perfiles configurados.
        """
        result={}
        for profile in ("SYNTHETICS","FOREX","ORB","IDX_OPEN"):
            row=self.latest_instrument_selection_profile(profile,source=source)
            if row is not None: result[profile]=row
        return result

    def latest_instrument_selection(self, source: str = "DEMO"):
        """Recupera la última selección persistida; None si nunca se guardó."""
        source = str(source or "DEMO").upper()
        with self.Session() as session:
            row = (
                session.execute(
                    select(InstrumentSelectionPreference)
                    .where(InstrumentSelectionPreference.source == source)
                    .order_by(
                        InstrumentSelectionPreference.updated_at.desc(),
                        InstrumentSelectionPreference.id.desc(),
                    )
                    .limit(1)
                )
                .scalar_one_or_none()
            )
        if row is None:
            return None
        try:
            selected = json.loads(row.selected_symbols_json or "[]")
        except Exception:
            selected = []
        if not isinstance(selected, list):
            selected = []
        selected = [str(value).strip() for value in selected if str(value).strip()]
        return {
            "id": row.id,
            "source": row.source,
            "selected_symbols": selected,
            "version": row.version,
            "updated_at": row.updated_at,
        }

    # ============================================================
    # ACCOUNT SNAPSHOTS
    # ============================================================

    def save_account_snapshot(self, account: dict):
        """Guarda una foto del estado de la cuenta en el broker.

        Cada llamada AÑADE una fila; la serie resultante permite reconstruir
        la curva de capital y el drawdown sin depender del historico del
        broker. Los importes ausentes se guardan como 0.0.

        Args:
            account: dict con balance, equity, margen, margen libre y
                beneficio flotante.

        Returns:
            El identificador de la fila creada.
        """
        with self.Session() as session:

            row = AccountSnapshot(
                snapshot_time=(
                    self._dt(account.get("snapshot_time"))
                    or datetime.now(timezone.utc)
                ),
                broker=str(
                    account.get("broker", "MT5")
                ),
                balance=self._num(
                    account.get("balance"),
                    0.0,
                ),
                equity=self._num(
                    account.get("equity"),
                    0.0,
                ),
                margin=self._num(
                    account.get("margin"),
                    0.0,
                ),
                free_margin=self._num(
                    account.get("free_margin"),
                    0.0,
                ),
                profit=self._num(
                    account.get("profit"),
                    0.0,
                ),
            )

            session.add(row)
            session.commit()

            return row.id


    def latest_account_snapshot(self):
        """Devuelve el snapshot de cuenta más reciente como dict."""
        with self.Session() as session:
            row = (
                session.execute(
                    select(AccountSnapshot)
                    .order_by(AccountSnapshot.snapshot_time.desc(), AccountSnapshot.id.desc())
                    .limit(1)
                )
                .scalar_one_or_none()
            )
        if row is None:
            return None
        return {
            "id": row.id,
            "snapshot_time": row.snapshot_time,
            "broker": row.broker,
            "balance": row.balance,
            "equity": row.equity,
            "margin": row.margin,
            "free_margin": row.free_margin,
            "profit": row.profit,
        }

    def reset_database(self, allow_open_trades: bool = False):
        """Reinicia datos operativos conservando ``trade_journal``.

        Cuenta activa mantiene así el historial permanente de trades incluso
        después de un reset operativo. Por seguridad, los OPEN siguen bloqueando
        el reset salvo confirmación forzada explícita.
        """
        with self.Session() as session:
            open_count = len(
                session.execute(select(Trade.id).where(Trade.status == "OPEN")).scalars().all()
            )
            if open_count and not allow_open_trades:
                raise RuntimeError(
                    f"LIMPIEZA BLOQUEADA: existen {open_count} trades OPEN en SQLite. "
                    "Cierra/sincroniza las posiciones o usa la confirmación forzada explícita."
                )
            counts = {
                "trades": len(session.execute(select(Trade.id)).scalars().all()),
                "signals": len(session.execute(select(Signal.id)).scalars().all()),
                "account_snapshots": len(session.execute(select(AccountSnapshot.id)).scalars().all()),
                "open_trades": open_count,
                "trade_journal_preserved": len(session.execute(select(TradeJournal.id)).scalars().all()),
            }
            session.execute(delete(Trade))
            session.execute(delete(Signal))
            session.execute(delete(AccountSnapshot))
            # SQLite mantiene secuencias internas. Reiniciarlas facilita una base
            # realmente limpia, pero no es requisito funcional.
            try:
                session.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('trades','signals','account_snapshots')"))
            except Exception:
                pass
            session.commit()
        return {"ok": True, **counts}

    # ============================================================
    # SIGNALS
    # ============================================================

    def save_signal(self, data: dict):
        """Inserta una señal SIN comprobar duplicados.

        Cada criterio SMC se guarda en su columna booleana y el analisis
        integro en `details_json`.

        Para el uso habitual conviene `save_signal_once`, que evita duplicar
        la misma senal cuando un ciclo la reprocesa.

        Args:
            data: dict con instrumento, marco, instante, direccion y las
                banderas de cada criterio.

        Returns:
            El identificador de la senal creada.
        """
        details = data.get("details")

        with self.Session() as session:

            row = Signal(
                instrument=str(data["instrument"]),
                timeframe=str(
                    data.get("timeframe", "M5")
                ),
                signal_time=(
                    self._dt(data.get("signal_time"))
                    or datetime.now(timezone.utc)
                ),
                direction=self._none_or_upper(
                    data.get("direction")
                ),
                valid=bool(
                    data.get("valid", False)
                ),
                trend_ok=bool(
                    data.get("trend_ok", False)
                ),
                swing_ok=bool(
                    data.get("swing_ok", False)
                ),
                liquidity_ok=bool(
                    data.get("liquidity_ok", False)
                ),
                sweep_ok=bool(
                    data.get("sweep_ok", False)
                ),
                structure_break_ok=bool(
                    data.get("structure_break_ok", False)
                ),
                order_block_ok=bool(
                    data.get("order_block_ok", False)
                ),
                retest_ok=bool(
                    data.get("retest_ok", False)
                ),
                premium_discount_ok=bool(
                    data.get("premium_discount_ok", False)
                ),
                confirmation_ok=bool(
                    data.get("confirmation_ok", False)
                ),
                details_json=self._json_or_none(details),
            )

            session.add(row)
            session.commit()

            return row.id

    def save_signal_once(self, data: dict):
        """Inserta una señal solo si no existe ya una idéntica.

        La identidad la forman instrumento, marco temporal, instante de la
        senal y direccion. Un mismo ciclo puede reevaluar la misma vela
        varias veces, y sin esta comprobacion el historico se llenaria de
        duplicados que sesgarian el entrenamiento del modelo.

        Args:
            data: igual que en `save_signal`.

        Returns:
            Tupla `(id, creada)`, donde `creada` indica si se inserto ahora o
            ya existia.
        """
        signal_time = (
            self._dt(data.get("signal_time"))
            or datetime.now(timezone.utc)
        )

        direction = self._none_or_upper(
            data.get("direction")
        )

        with self.Session() as session:

            stmt = select(Signal).where(
                Signal.instrument == str(
                    data["instrument"]
                ),
                Signal.timeframe == str(
                    data.get("timeframe", "M5")
                ),
                Signal.signal_time == signal_time,
                Signal.direction == direction,
            )

            existing = (
                session.execute(stmt)
                .scalar_one_or_none()
            )

            if existing is not None:
                return existing.id, False

        signal_data = dict(data)
        signal_data["signal_time"] = signal_time

        signal_id = self.save_signal(signal_data)

        return signal_id, True

    # ============================================================
    # TRADES
    # ============================================================

    def create_trade(self, data: dict):
        """Crea una operación y la archiva de inmediato en el historial.

        Ambas escrituras ocurren en la MISMA transaccion, de modo que nunca
        queda una operacion en `trades` sin su copia en `trade_journal`.

        Para el uso habitual conviene `create_trade_once`, que evita duplicar
        la operacion cuando la recuperacion y el callback de ejecucion se
        solapan durante un fill.

        Args:
            data: campos de la operacion.

        Returns:
            El identificador de la operacion creada.
        """
        kwargs = self._trade_kwargs(data)

        with self.Session() as session:

            row = Trade(**kwargs)

            session.add(row)
            session.flush()
            self._upsert_trade_journal_session(session, row)
            session.commit()
            session.refresh(row)

            return row.id

    def create_trade_once(self, data: dict):
        """
        Crea una operación una sola vez usando:

        1. execution_key
        2. external_ticket
        3. broker_position_ticket

        El tercer identificador evita que la recuperación MT5 y el callback de
        ejecución creen dos filas para la misma posición durante un fill.
        """

        execution_key = data.get(
            "execution_key"
        )

        ticket = data.get(
            "external_ticket"
        )
        position_ticket = data.get("broker_position_ticket")

        with self.Session() as session:

            if execution_key not in (None, ""):

                existing = (
                    session.execute(
                        select(Trade).where(
                            Trade.execution_key
                            == str(execution_key)
                        )
                    )
                    .scalar_one_or_none()
                )

                if existing is not None:
                    return existing.id, False

            if ticket not in (None, ""):

                existing = (
                    session.execute(
                        select(Trade).where(
                            Trade.external_ticket
                            == str(ticket)
                        )
                    )
                    .scalar_one_or_none()
                )

                if existing is not None:
                    return existing.id, False

            if position_ticket not in (None, "", 0):
                stmt = select(Trade).where(
                    Trade.broker_position_ticket == str(position_ticket)
                )
                source = data.get("source")
                if source not in (None, ""):
                    stmt = stmt.where(Trade.source == str(source).upper())
                existing = (
                    session.execute(stmt.order_by(Trade.id.asc()).limit(1))
                    .scalar_one_or_none()
                )

                if existing is not None:
                    # Si el monitor alcanzó a importar la posición entre el fill
                    # y el callback, promovemos esa misma fila con la identidad y
                    # tesis completas de la ejecución, sin crear un duplicado.
                    recovered = (
                        str(existing.execution_key or "").startswith("mt5-open-position:")
                        or str(existing.external_ticket or "").startswith("MT5POS:")
                        or str(existing.strategy_version or "") == "smc-reconciled-mt5-open"
                    )
                    if recovered:
                        for name, value in self._trade_kwargs(data).items():
                            if value is not None and hasattr(existing, name):
                                setattr(existing, name, value)
                        session.flush()
                        self._upsert_trade_journal_session(session, existing)
                        session.commit()
                    return existing.id, False

        return self.create_trade(data), True

    def get_trade(self, trade_id: int):
        """Recupera una operación por su identificador interno.

        Returns:
            Dict de la operacion, o `None` si no existe.
        """
        with self.Session() as session:

            row = session.get(
                Trade,
                int(trade_id),
            )

            return self._trade_dict(row)

    def get_trade_by_execution_key(
        self,
        execution_key: str,
    ):
        """Recupera una operación por su clave de ejecución.

        Es la consulta que sostiene la idempotencia: antes de ejecutar una
        senal, el motor comprueba aqui si esa clave ya produjo una operacion.

        Returns:
            Dict de la operacion, o `None` si esa clave no se ejecuto.
        """
        with self.Session() as session:

            row = (
                session.execute(
                    select(Trade).where(
                        Trade.execution_key
                        == str(execution_key)
                    )
                )
                .scalar_one_or_none()
            )

            return self._trade_dict(row)

    def get_trade_by_position_ticket(
        self,
        position_ticket,
    ):
        """Recupera la operación asociada a un ticket de posición del broker.

        Si existen varias filas para el mismo ticket, PREFIERE la que no
        proviene de una recuperacion automatica (clave `mt5-open-position:`).
        La fila creada por el propio flujo de ejecucion conserva el analisis
        que origino la entrada, mientras que la recuperada solo tiene lo que
        el broker informa.

        Returns:
            Dict de la operacion, o `None` si el ticket falta o no existe.
        """
        if position_ticket in (None, ""):
            return None

        with self.Session() as session:

            rows = (
                session.execute(
                    select(Trade).where(
                        Trade.broker_position_ticket
                        == str(position_ticket)
                    ).order_by(Trade.id.asc())
                )
                .scalars()
                .all()
            )
            if not rows:
                return None
            row = next((
                candidate for candidate in rows
                if not str(candidate.execution_key or "").startswith("mt5-open-position:")
            ), rows[0])
            return self._trade_dict(row)

    def open_trades(
        self,
        source: str | None = None,
    ):
        """Devuelve las operaciones con estado OPEN.

        Consulta base del monitor de posiciones y de los limites de exposicion.
        NO filtra por worker: cada motor decide despues cuales le pertenecen
        mediante su comprobacion de propiedad.

        Args:
            source: filtra por entorno; sin valor devuelve todas.

        Returns:
            Lista de dicts de operaciones abiertas.
        """
        with self.Session() as session:

            stmt = (
                select(Trade)
                .where(
                    Trade.status == "OPEN"
                )
                .order_by(
                    Trade.entry_time,
                    Trade.id,
                )
            )

            if source:
                stmt = stmt.where(
                    Trade.source
                    == str(source).upper()
                )

            rows = (
                session.execute(stmt)
                .scalars()
                .all()
            )

            return [
                self._trade_dict(row)
                for row in rows
            ]

    def update_trade(
        self,
        trade_id: int,
        data: dict,
    ):
        """Actualiza los campos indicados de una operación existente.

        Actualizacion PARCIAL: solo se tocan las claves presentes en `data`,
        de modo que no hace falta reenviar la operacion completa.

        Cada campo se normaliza segun su tipo (numerico, fecha, texto en
        mayusculas o ticket) antes de escribirse, y el historial permanente se
        sincroniza en la misma transaccion.

        Args:
            trade_id: operacion a modificar.
            data: campos a actualizar.

        Returns:
            La operacion ya actualizada.
        """
        numeric_fields = {
            "entry_price",
            "exit_price",
            "stop_loss",
            "take_profit",
            "volume",
            "planned_rr",
            "realized_rr",
            "balance_before",
            "balance_after",
            "equity",
            "peak_balance",
            "drawdown_amount",
            "drawdown_percent",
            "risk_percent",
            "risk_amount",
            "gross_pnl",
            "commission",
            "swap",
            "net_pnl",
        }

        datetime_fields = {
            "entry_time",
            "exit_time",
        }

        uppercase_fields = {
            "result",
            "source",
            "direction",
            "status",
        }

        ticket_fields = {
            "execution_key",
            "external_ticket",
            "broker_order_ticket",
            "broker_deal_ticket",
            "broker_position_ticket",
        }

        with self.Session() as session:

            row = session.get(
                Trade,
                int(trade_id),
            )

            if row is None:
                raise ValueError(
                    f"No existe trade id={trade_id}"
                )

            for key, value in data.items():

                if key == "details":
                    row.details_json = (
                        self._json_or_none(value)
                    )
                    continue

                if key == "details_json":
                    row.details_json = (
                        self._json_or_none(value)
                    )
                    continue

                if not hasattr(row, key):
                    continue

                if key in datetime_fields:
                    value = self._dt(value)

                elif key in numeric_fields:
                    value = self._float_or_none(value)

                elif key == "bars_held":
                    value = self._int_or_none(value)

                elif key in uppercase_fields:
                    value = self._none_or_upper(value)

                elif key in ticket_fields:
                    value = (
                        str(value)
                        if value not in (None, "")
                        else None
                    )

                setattr(
                    row,
                    key,
                    value,
                )

            session.flush()
            self._upsert_trade_journal_session(session, row)
            session.commit()
            session.refresh(row)

            return row.id

    def close_trade(
        self,
        trade_id: int,
        data: dict,
    ):
        """Marca una operación como cerrada y registra su desenlace.

        Fija el estado en `CLOSED` y, si no se indica la hora de salida, usa
        el instante actual. El resto de campos (precio de salida, resultado en
        R, neto y motivo del cierre) se toman de `data`.

        Args:
            trade_id: operacion a cerrar.
            data: datos del cierre; conviene incluir `exit_reason` para poder
                distinguir despues un stop loss de un cierre defensivo.

        Returns:
            El identificador de la operacion cerrada.
        """
        close_data = dict(data)

        close_data["status"] = "CLOSED"

        if close_data.get("exit_time") is None:
            close_data["exit_time"] = (
                datetime.now(timezone.utc)
            )

        self.update_trade(
            trade_id,
            close_data,
        )

        return trade_id

    # ============================================================
    # IMPORTACIÓN BACKTEST
    # ============================================================

    def import_backtest_dataframe(
        self,
        trades: pd.DataFrame,
        instrument: str,
        timeframe: str = "M5",
        broker: str = "SIMULATOR",
        strategy_version: str = "smc-v1",
        source: str = "BACKTEST",
    ):
        """Importa a la base los resultados de un backtest.

        Permite que las operaciones simuladas convivan con las reales en las
        mismas tablas, distinguidas por `source`, de modo que los informes y
        el analisis funcionen igual para ambas.

        Args:
            trades: DataFrame con las operaciones simuladas.
            instrument: simbolo al que corresponden.
            timeframe: marco temporal, `M5` por defecto.
            broker: origen de la simulacion.
            strategy_version: version de la estrategia evaluada.
            source: entorno, `BACKTEST` por defecto, para no mezclarlas con
                la operativa real.

        Returns:
            Dict con cuantas se crearon, cuantas ya existian y sus ids.

        Raises:
            ValueError: si `trades` es `None`. Un DataFrame vacio si es valido
                y devuelve un resultado con contadores a cero.
        """
        if trades is None:
            raise ValueError(
                "trades no puede ser None"
            )

        if trades.empty:
            return {
                "created": 0,
                "existing": 0,
                "ids": [],
            }

        required = {
            "entry_time",
            "direction",
            "result",
        }

        missing = (
            required
            .difference(trades.columns)
        )

        if missing:
            raise ValueError(
                f"Faltan columnas para importar backtest: "
                f"{sorted(missing)}"
            )

        created = 0
        existing = 0
        ids = []

        for _, raw in trades.iterrows():

            row = raw.to_dict()

            entry_time = self._dt(
                row.get("entry_time")
            )

            direction = (
                self._none_or_upper(
                    row.get("direction")
                )
                or ""
            )

            key = self._backtest_ticket(
                instrument=instrument,
                timeframe=timeframe,
                entry_time=entry_time,
                direction=direction,
                trade_number=row.get(
                    "trade_number"
                ),
                confirmation_time=row.get(
                    "confirmation_time"
                ),
                setup_time=row.get(
                    "setup_time"
                ),
            )

            result = (
                self._none_or_upper(
                    row.get("result")
                )
                or "OPEN"
            )

            status = (
                "OPEN"
                if result == "OPEN"
                else "CLOSED"
            )

            net_pnl = self._num(
                row.get(
                    "pnl",
                    row.get(
                        "net_pnl",
                        0.0,
                    ),
                ),
                0.0,
            )

            setup_reason = (
                self._build_setup_reason(row)
            )

            details = {
                "trade_number": self._clean_value(
                    row.get("trade_number")
                ),
                "setup_time": self._clean_value(
                    row.get("setup_time")
                ),
                "retest_time": self._clean_value(
                    row.get("retest_time")
                ),
                "confirmation_time": self._clean_value(
                    row.get("confirmation_time")
                ),
                "setup_type": self._clean_value(
                    row.get("setup_type")
                ),
                "confirmation_type": self._clean_value(
                    row.get("confirmation_type")
                ),
                "zone": self._clean_value(
                    row.get("zone")
                ),
                "equilibrium": self._clean_value(
                    row.get("equilibrium")
                ),
                "trend_ok": self._clean_value(
                    row.get("trend_ok")
                ),
                "swing_ok": self._clean_value(
                    row.get("swing_ok")
                ),
                "liquidity_ok": self._clean_value(
                    row.get("liquidity_ok")
                ),
                "sweep_ok": self._clean_value(
                    row.get("sweep_ok")
                ),
                "structure_break_ok": self._clean_value(
                    row.get(
                        "structure_break_ok"
                    )
                ),
                "order_block_ok": self._clean_value(
                    row.get("order_block_ok")
                ),
                "retest_ok": self._clean_value(
                    row.get("retest_ok")
                ),
                "premium_discount_ok": self._clean_value(
                    row.get(
                        "premium_discount_ok"
                    )
                ),
                "confirmation_ok": self._clean_value(
                    row.get(
                        "confirmation_ok"
                    )
                ),
            }

            data = {
                "external_ticket": key,
                "source": source,
                "broker": broker,
                "instrument": instrument,
                "timeframe": timeframe,
                "direction": direction,
                "status": status,
                "result": result,
                "entry_time": row.get(
                    "entry_time"
                ),
                "exit_time": row.get(
                    "exit_time"
                ),
                "entry_price": row.get(
                    "entry_price"
                ),
                "exit_price": row.get(
                    "exit_price"
                ),
                "stop_loss": row.get(
                    "stop_loss"
                ),
                "take_profit": row.get(
                    "take_profit"
                ),
                "volume": row.get(
                    "volume"
                ),
                "planned_rr": row.get(
                    "planned_rr",
                    row.get(
                        "risk_reward_ratio"
                    ),
                ),
                "realized_rr": row.get(
                    "realized_rr"
                ),
                "bars_held": row.get(
                    "bars_held"
                ),
                "exit_reason": row.get(
                    "reason"
                ),
                "balance_before": row.get(
                    "balance_before"
                ),
                "balance_after": row.get(
                    "balance_after"
                ),
                "equity": row.get(
                    "equity"
                ),
                "peak_balance": row.get(
                    "peak_balance"
                ),
                "drawdown_amount": row.get(
                    "drawdown_amount"
                ),
                "drawdown_percent": row.get(
                    "drawdown_percent"
                ),
                "risk_percent": row.get(
                    "risk_percent"
                ),
                "risk_amount": row.get(
                    "risk_amount"
                ),
                "gross_pnl": net_pnl,
                "net_pnl": net_pnl,
                "setup_reason": setup_reason,
                "details": details,
                "strategy_version": (
                    strategy_version
                ),
            }

            trade_id, was_created = (
                self.create_trade_once(data)
            )

            ids.append(trade_id)

            if was_created:
                created += 1
            else:
                existing += 1

        return {
            "created": created,
            "existing": existing,
            "ids": ids,
        }

    # ============================================================
    # DATAFRAME / RESUMEN
    # ============================================================

    def trades_dataframe(
        self,
        source: str | None = None,
    ):
        """Devuelve las operaciones de la tabla operativa como DataFrame.

        Lee de `trades`, por lo que refleja el estado tras el ultimo reinicio
        de estadisticas. Para el historial completo, `trade_history_dataframe`.

        Args:
            source: filtra por entorno; sin valor devuelve todo.

        Returns:
            DataFrame ordenado por fecha de entrada.
        """
        with self.Session() as session:

            stmt = (
                select(Trade)
                .order_by(
                    Trade.entry_time,
                    Trade.id,
                )
            )

            if source:
                stmt = stmt.where(
                    Trade.source
                    == str(source).upper()
                )

            rows = (
                session.execute(stmt)
                .scalars()
                .all()
            )

            return pd.DataFrame(
                [
                    self._trade_dict(row)
                    for row in rows
                ]
            )

    def summary(
        self,
        source: str | None = None,
    ):
        """Calcula el resumen agregado de rendimiento de las operaciones.

        Cuenta operaciones totales, abiertas y cerradas, y clasifica los
        resultados en ganadoras, perdedoras y AMBIGUAS. Estas ultimas son los
        cierres tan proximos a 0R que no representan una ventaja real; se
        separan mediante `trade_outcome_policy` para que no inflen
        artificialmente la tasa de acierto.

        Args:
            source: filtra por entorno; sin valor agrega todo.

        Returns:
            Dict con los recuentos y las metricas de rendimiento. Con la base
            vacia devuelve la misma estructura con todo a cero, de modo que el
            panel no tenga que distinguir ese caso.
        """
        df = self.trades_dataframe(
            source=source
        )

        if df.empty:
            return {
                "total_trades": 0,
                "closed_trades": 0,
                "open_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "ambiguous_trades": 0,
                "breakeven_trades": 0,
                "win_rate": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "total_net_pnl": 0.0,
                "invested_amount": 0.0,
                "average_planned_rr": 0.0,
                "average_realized_rr": 0.0,
                "max_drawdown_amount": 0.0,
                "max_drawdown_percent": 0.0,
                "instruments": [],
            }

        closed = df[
            df["status"].eq("CLOSED")
        ].copy()

        # v48: Win Rate usa RR real cuando existe. La banda neutral ±0.25R
        # se considera Break Even y queda fuera del denominador.
        rr_series = (
            pd.to_numeric(closed["realized_rr"], errors="coerce")
            if "realized_rr" in closed.columns
            else pd.Series(float("nan"), index=closed.index, dtype=float)
        )
        has_rr = rr_series.notna()
        result_upper = (
            closed["result"].astype(str).str.upper()
            if "result" in closed.columns
            else pd.Series("", index=closed.index, dtype=str)
        )

        win_mask = (
            (has_rr & (rr_series > BREAK_EVEN_RR_TOLERANCE))
            | (~has_rr & result_upper.eq("WIN"))
        )
        loss_mask = (
            (has_rr & (rr_series < -BREAK_EVEN_RR_TOLERANCE))
            | (~has_rr & result_upper.eq("LOSS"))
        )
        be_mask = (
            (has_rr & (rr_series.abs() <= BREAK_EVEN_RR_TOLERANCE))
            | (~has_rr & result_upper.isin(["BREAKEVEN", "BREAK_EVEN"]))
        )

        wins = closed[win_mask]
        losses = closed[loss_mask]
        closed_decisive = closed[win_mask | loss_mask]

        def numeric(frame, column):
            """Columna como serie numérica, vacía si la columna no existe."""
            if column not in frame.columns:
                return pd.Series(
                    dtype=float
                )

            return (
                pd.to_numeric(
                    frame[column],
                    errors="coerce",
                )
                .fillna(0.0)
            )

        net = numeric(
            closed,
            "net_pnl",
        )

        planned = numeric(
            closed_decisive,
            "planned_rr",
        )

        realized = numeric(
            closed_decisive,
            "realized_rr",
        )

        dd_amount = numeric(
            df,
            "drawdown_amount",
        )

        dd_percent = numeric(
            df,
            "drawdown_percent",
        )

        risk_amount = numeric(
            df,
            "risk_amount",
        )

        return {
            "total_trades": int(
                len(df)
            ),

            "closed_trades": int(
                len(closed)
            ),

            "open_trades": int(
                df["status"]
                .eq("OPEN")
                .sum()
            ),

            "winning_trades": int(
                len(wins)
            ),

            "losing_trades": int(
                len(losses)
            ),

            "ambiguous_trades": int(
                closed["result"]
                .eq("AMBIGUOUS")
                .sum()
            ),

            "breakeven_trades": int(be_mask.sum()),

            "win_rate": round(
                (
                    len(wins)
                    / len(closed_decisive)
                    * 100
                )
                if len(closed_decisive)
                else 0.0,
                4,
            ),

            "gross_profit": float(
                net[net > 0].sum()
            ),

            "gross_loss": float(
                abs(
                    net[net < 0].sum()
                )
            ),

            "total_net_pnl": float(
                net.sum()
            ),

            "invested_amount": float(
                risk_amount.sum()
            ),

            "average_planned_rr": float(
                planned.mean()
            )
            if len(planned)
            else 0.0,

            "average_realized_rr": float(
                realized.mean()
            )
            if len(realized)
            else 0.0,

            "max_drawdown_amount": float(
                dd_amount.min()
            )
            if len(dd_amount)
            else 0.0,

            "max_drawdown_percent": float(
                dd_percent.min()
            )
            if len(dd_percent)
            else 0.0,

            "instruments": sorted(
                df["instrument"]
                .dropna()
                .unique()
                .tolist()
            ),
        }

    # ============================================================
    # SINCRONIZACIÓN MT5
    # ============================================================

    def sync_closed_mt5_trades(
        self,
        executor,
        source: str = "DEMO",
    ):
        """
        Sincroniza SQLite con MT5.

        Solo marca una operación como CLOSED cuando:

        1. Ya no existe la posición en MT5.
        2. Existe historial de deals para esa posición.
        """

        updated = 0

        now = datetime.now(
            timezone.utc
        )

        open_trades = self.open_trades(
            source=source
        )

        for trade in open_trades:

            position_ticket = trade.get(
                "broker_position_ticket"
            )

            if not position_ticket:
                continue

            try:
                position_ticket_int = int(
                    position_ticket
                )
            except (TypeError, ValueError):
                continue

            position = executor.get_position(
                position_ticket_int
            )

            if position is not None:
                continue

            try:
                deals = executor.history_for_position(
                    position_ticket_int,
                    now - timedelta(days=30),
                    now,
                )

            except Exception:
                deals = []

            if not deals:
                continue

            profit = sum(
                float(
                    getattr(
                        deal,
                        "profit",
                        0.0,
                    )
                    or 0.0
                )
                for deal in deals
            )

            commission = sum(
                float(
                    getattr(
                        deal,
                        "commission",
                        0.0,
                    )
                    or 0.0
                )
                for deal in deals
            )

            swap = sum(
                float(
                    getattr(
                        deal,
                        "swap",
                        0.0,
                    )
                    or 0.0
                )
                for deal in deals
            )

            net = (
                profit
                + commission
                + swap
            )

            exit_deal = deals[-1]

            exit_price = (
                float(
                    getattr(
                        exit_deal,
                        "price",
                        0.0,
                    )
                    or 0.0
                )
                or None
            )

            deal_time = getattr(
                exit_deal,
                "time",
                None,
            )

            if deal_time:

                exit_time = (
                    pd.to_datetime(
                        deal_time,
                        unit="s",
                        utc=True,
                    )
                    .to_pydatetime()
                )

            else:
                exit_time = now

            risk = float(
                trade.get("risk_amount")
                or 0.0
            )

            realized_rr = (
                net / risk
                if risk > 0
                else None
            )

            outcome = decisive_outcome(
                realized_rr=realized_rr,
                net_pnl=net,
                status="CLOSED",
            )
            result = (
                "WIN" if outcome == "WIN"
                else "LOSS" if outcome == "LOSS"
                else "BREAKEVEN"
            )

            self.update_trade(
                int(trade["id"]),
                {
                    "status": "CLOSED",
                    "result": result,
                    "exit_time": exit_time,
                    "exit_price": exit_price,
                    "gross_pnl": profit,
                    "commission": commission,
                    "swap": swap,
                    "net_pnl": net,
                    "realized_rr": realized_rr,
                    "exit_reason": (
                        "mt5_history_sync"
                    ),
                },
            )

            updated += 1

        return updated

    # ============================================================
    # IMPORTACIÓN DE POSICIONES ABIERTAS MT5
    # ============================================================

    def import_open_mt5_positions(
        self,
        executor,
        source: str = "DEMO",
        magic: int | None = None,
        include_external: bool = True,
        external_source: str = "MT5_EXTERNAL",
        timeframe: str = "M5",
    ):
        """Descubre posiciones abiertas en MT5 que todavía no existen en SQLite.

        Las posiciones con el ``magic`` del daemon se adoptan como operaciones del
        daemon (``source``). Las demás, si ``include_external`` es True, se
        persisten como ``MT5_EXTERNAL`` únicamente para visibilidad/auditoría; no
        deben ser gestionadas automáticamente por el motor de trading.
        """
        if not hasattr(executor, "list_open_positions"):
            return {
                "seen": 0, "imported_daemon": 0, "imported_external": 0,
                "existing": 0, "skipped": 0, "ids": [],
            }

        positions = list(executor.list_open_positions() or [])
        account = {}
        try:
            account = executor.account_info() if hasattr(executor, "account_info") else {}
        except Exception:
            account = {}

        equity = float(account.get("equity") or 0.0) if isinstance(account, dict) else 0.0
        imported_daemon = imported_external = existing = skipped = 0
        ids = []

        for position in positions:
            ticket = position.get("position_ticket")
            symbol = str(position.get("symbol") or "")
            direction = str(position.get("direction") or "").upper()
            if ticket in (None, "", 0) or not symbol or direction not in {"BUY", "SELL"}:
                skipped += 1
                continue

            found = self.get_trade_by_position_ticket(ticket)
            if found is not None:
                existing += 1
                ids.append(found.get("id"))
                continue

            position_magic = int(position.get("magic") or 0)
            daemon_owned = magic is not None and position_magic == int(magic)
            if not daemon_owned and not include_external:
                skipped += 1
                continue

            trade_source = str(source if daemon_owned else external_source).upper()
            entry = float(position.get("entry_price") or 0.0)
            sl = float(position.get("stop_loss") or 0.0)
            tp = float(position.get("take_profit") or 0.0)
            volume = float(position.get("volume") or 0.0)

            planned_rr = None
            risk_distance = abs(entry - sl) if entry > 0 and sl > 0 else 0.0
            if risk_distance > 0 and tp > 0:
                planned_rr = abs(tp - entry) / risk_distance

            risk_amount = None
            risk_percent = None
            if sl > 0 and entry > 0 and volume > 0 and hasattr(executor, "calculate_risk_amount"):
                try:
                    risk_info = executor.calculate_risk_amount(
                        symbol=symbol, direction=direction, volume=volume,
                        entry_price=entry, stop_loss=sl,
                    )
                    risk_amount = float(risk_info.get("actual_risk_amount") or 0.0)
                    if equity > 0 and risk_amount > 0:
                        risk_percent = risk_amount / equity * 100.0
                except Exception:
                    risk_amount = None
                    risk_percent = None

            comment_upper = str(position.get("comment") or "").upper()
            trade_leg = None
            if "RUNNER" in comment_upper:
                trade_leg = "RUNNER"
            elif "TP1" in comment_upper:
                trade_leg = "TP1"
            elif "SINGLE" in comment_upper:
                trade_leg = "SINGLE"
            execution_mode = (
                "SPLIT" if trade_leg in {"TP1", "RUNNER"}
                else "SINGLE_FALLBACK" if trade_leg == "SINGLE"
                else "RECOVERED_MT5"
            )

            metadata = {
                "adopted_from_mt5": True,
                "trade_leg": trade_leg,
                "execution_mode": execution_mode,
                "managed_by_daemon": bool(daemon_owned),
                "mt5_magic": position_magic,
                "mt5_comment": position.get("comment"),
                "mt5_identifier": position.get("identifier"),
                "last_known_price": position.get("current_price"),
                "floating_profit_at_import": position.get("floating_profit"),
                "swap_at_import": position.get("swap"),
                "import_reason": (
                    "POSICION_DEL_DAEMON_DESCUBIERTA_EN_MT5"
                    if daemon_owned else "POSICION_EXTERNA_MT5_SOLO_VISUALIZACION"
                ),
            }
            payload = {
                "external_ticket": f"MT5POS:{ticket}",
                "execution_key": f"mt5-open-position:{ticket}",
                "broker_position_ticket": str(ticket),
                "source": trade_source,
                "broker": "MT5",
                "instrument": symbol,
                "timeframe": timeframe,
                "direction": direction,
                "status": "OPEN",
                "result": "OPEN",
                "entry_time": position.get("entry_time"),
                "entry_price": entry or None,
                "stop_loss": sl or None,
                "take_profit": tp or None,
                "volume": volume or None,
                "planned_rr": planned_rr,
                "equity": equity or None,
                "risk_percent": risk_percent,
                "risk_amount": risk_amount,
                "setup_reason": (
                    "Posición del daemon recuperada desde MT5 al iniciar."
                    if daemon_owned
                    else "Posición existente en MT5 importada sólo para visualización; no gestionada por el daemon."
                ),
                "details": {"metadata": metadata},
                "strategy_version": (
                    "smc-reconciled-mt5-open" if daemon_owned else "mt5-external-position"
                ),
            }
            trade_id, created = self.create_trade_once(payload)
            ids.append(trade_id)
            if created:
                if daemon_owned:
                    imported_daemon += 1
                else:
                    imported_external += 1
            else:
                existing += 1

        return {
            "seen": len(positions),
            "imported_daemon": imported_daemon,
            "imported_external": imported_external,
            "existing": existing,
            "skipped": skipped,
            "ids": ids,
        }

    # ============================================================
    # IMPORTACIÓN DE HISTORIAL CERRADO MT5
    # ============================================================

    def import_mt5_trade_history(
        self,
        executor,
        source: str = "DEMO",
        magic: int | None = None,
        include_external: bool = False,
        external_source: str = "MT5_EXTERNAL",
        from_time=None,
        to_time=None,
    ):
        """Reconstruye el historial permanente usando los deals de MT5.

        Los deals se agrupan por ``position_id``. Las posiciones aún abiertas se
        dejan a ``import_open_mt5_positions``; aquí se importan posiciones
        cerradas para que Cuenta activa pueda recuperar operaciones anteriores a
        la instalación de la base local. La operación es idempotente gracias al
        ``broker_position_ticket``/``journal_key``.
        """
        if not hasattr(executor, "list_history_deals"):
            return {
                "deals_seen": 0, "positions_seen": 0, "imported": 0,
                "updated": 0, "skipped_open": 0, "skipped_external": 0,
                "skipped_incomplete": 0,
            }

        # Pedimos todo el historial disponible y filtramos por grupo. Esto
        # permite reconocer correctamente un position_id aunque alguno de sus
        # deals tenga metadatos incompletos.
        deals = list(executor.list_history_deals(from_time=from_time, to_time=to_time) or [])
        groups = {}
        for deal in deals:
            ticket = deal.get("position_ticket")
            if ticket in (None, "", 0, "0"):
                continue
            groups.setdefault(str(ticket), []).append(dict(deal))

        open_tickets = set()
        if hasattr(executor, "list_open_positions"):
            try:
                open_tickets = {
                    str(row.get("position_ticket"))
                    for row in (executor.list_open_positions() or [])
                    if row.get("position_ticket") not in (None, "", 0, "0")
                }
            except Exception:
                open_tickets = set()

        imported = updated = skipped_open = skipped_external = skipped_incomplete = 0
        now = datetime.now(timezone.utc)

        def weighted_price(rows):
            """Precio medio ponderado por volumen de un conjunto de deals.

            Una posicion puede llenarse o cerrarse en varios deals a precios
            distintos. Promediar sin ponderar daria un precio erroneo, porque
            un deal de 0.01 lotes pesaria igual que uno de 1.0.

            Returns:
                El precio ponderado, o `None` si el volumen total es cero.
            """
            total_volume = sum(max(0.0, self._num(r.get("volume"), 0.0)) for r in rows)
            if total_volume <= 0:
                return None
            return sum(
                self._num(r.get("price"), 0.0) * max(0.0, self._num(r.get("volume"), 0.0))
                for r in rows
            ) / total_volume

        with self.Session() as session:
            for position_ticket, rows in groups.items():
                if position_ticket in open_tickets:
                    skipped_open += 1
                    continue

                rows.sort(key=lambda r: (self._dt(r.get("time")) or now, int(r.get("deal_ticket") or 0)))
                entry_rows = [r for r in rows if str(r.get("entry_kind") or "").upper() in {"IN", "INOUT"}]
                exit_rows = [r for r in rows if str(r.get("entry_kind") or "").upper() in {"OUT", "OUT_BY", "INOUT"}]
                if not entry_rows or not exit_rows:
                    skipped_incomplete += 1
                    continue

                group_magics = {int(r.get("magic") or 0) for r in rows}
                group_comments_upper = " | ".join(
                    str(r.get("comment") or "").upper() for r in rows
                )
                # Compatibilidad histórica: algunas versiones anteriores pueden
                # haber usado otro magic, pero las órdenes del proyecto usan
                # comentarios SMC-<signal>-<leg>. Reconocer ambos evita perder
                # trades antiguos legítimos del daemon.
                daemon_owned = (
                    (magic is not None and int(magic) in group_magics)
                    or "SMC-" in group_comments_upper
                    or "DAEMONBLACKFX" in group_comments_upper
                    or "DBFX" in group_comments_upper
                )
                if not daemon_owned and not include_external:
                    skipped_external += 1
                    continue

                trade_source = str(source if daemon_owned else external_source).upper()
                opening = entry_rows[0]
                direction = str(opening.get("direction") or "").upper()
                if direction not in {"BUY", "SELL"}:
                    skipped_incomplete += 1
                    continue

                symbol = str(opening.get("symbol") or next((r.get("symbol") for r in rows if r.get("symbol")), ""))
                if not symbol:
                    skipped_incomplete += 1
                    continue

                entry_time = self._dt(entry_rows[0].get("time"))
                exit_time = self._dt(exit_rows[-1].get("time"))
                entry_price = weighted_price(entry_rows)
                exit_price = weighted_price(exit_rows)
                entry_volume = sum(max(0.0, self._num(r.get("volume"), 0.0)) for r in entry_rows)
                net_pnl = sum(
                    self._num(r.get("profit"), 0.0)
                    + self._num(r.get("commission"), 0.0)
                    + self._num(r.get("swap"), 0.0)
                    + self._num(r.get("fee"), 0.0)
                    for r in rows
                )

                comments = [str(r.get("comment") or "") for r in rows if r.get("comment")]
                comment_upper = " | ".join(comments).upper()
                trade_leg = (
                    "RUNNER" if "RUNNER" in comment_upper else
                    "TP1" if "TP1" in comment_upper else
                    "SINGLE" if "SINGLE" in comment_upper else None
                )
                execution_mode = (
                    "SPLIT" if trade_leg in {"TP1", "RUNNER"}
                    else "SINGLE_FALLBACK" if trade_leg == "SINGLE"
                    else "HISTORICAL_MT5"
                )
                close_reason = str(exit_rows[-1].get("reason_kind") or "UNKNOWN").upper()
                if close_reason == "SL":
                    result = "STOP_LOSS"
                elif close_reason == "TP":
                    result = "TAKE_PROFIT"
                elif net_pnl > 0:
                    result = "WIN"
                elif net_pnl < 0:
                    result = "LOSS"
                else:
                    result = "BREAK_EVEN"

                broker_deals = [str(r.get("deal_ticket")) for r in rows if r.get("deal_ticket")]
                metadata = {
                    "historical_mt5_import": True,
                    "managed_by_daemon": bool(daemon_owned),
                    "mt5_magic_values": sorted(group_magics),
                    "mt5_comments": comments,
                    "mt5_deal_tickets": broker_deals,
                    "mt5_close_reason": close_reason,
                    "trade_leg": trade_leg,
                    "execution_mode": execution_mode,
                    "history_recovered_at": now.isoformat(),
                }
                payload = {
                    "source": trade_source,
                    "broker": "MT5",
                    "instrument": symbol,
                    "direction": direction,
                    "status": "CLOSED",
                    "result": result,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "volume": entry_volume or None,
                    "net_pnl": net_pnl,
                    "execution_key": f"mt5-history-position:{position_ticket}",
                    "external_ticket": f"MT5HIST:{position_ticket}",
                    "broker_position_ticket": position_ticket,
                    "strategy_version": (
                        "smc-v23-mt5-history-recovered" if daemon_owned
                        else "mt5-external-history"
                    ),
                    "details": {"metadata": metadata},
                }

                key = self._journal_key(payload)
                journal = session.execute(
                    select(TradeJournal).where(TradeJournal.journal_key == key)
                ).scalar_one_or_none()

                # Compatibilidad con journals antiguos cuya clave pudo haberse
                # construido con execution_key/external_ticket antes de conocer
                # el broker_position_ticket.
                if journal is None:
                    journal = session.execute(
                        select(TradeJournal).where(
                            TradeJournal.source == trade_source,
                            TradeJournal.broker_position_ticket == position_ticket,
                        )
                    ).scalar_one_or_none()

                if journal is None:
                    self._upsert_trade_journal_session(session, payload)
                    imported += 1
                else:
                    existing_details = {}
                    if journal.details_json:
                        try:
                            existing_details = json.loads(journal.details_json)
                        except Exception:
                            existing_details = {}
                    if not isinstance(existing_details, dict):
                        existing_details = {}
                    existing_meta = existing_details.get("metadata")
                    if not isinstance(existing_meta, dict):
                        existing_meta = {}
                    existing_meta.update(metadata)
                    existing_details["metadata"] = existing_meta

                    journal.status = "CLOSED"
                    journal.result = result
                    journal.entry_time = journal.entry_time or entry_time
                    journal.exit_time = exit_time or journal.exit_time
                    journal.entry_price = journal.entry_price or entry_price
                    journal.exit_price = exit_price if exit_price is not None else journal.exit_price
                    journal.volume = journal.volume or (entry_volume or None)
                    journal.net_pnl = net_pnl
                    journal.broker_position_ticket = position_ticket
                    journal.execution_key = journal.execution_key or payload["execution_key"]
                    journal.external_ticket = journal.external_ticket or payload["external_ticket"]
                    journal.details_json = self._json_or_none(existing_details)
                    journal.last_seen_at = now
                    updated += 1

            session.commit()

        return {
            "deals_seen": len(deals),
            "positions_seen": len(groups),
            "imported": imported,
            "updated": updated,
            "skipped_open": skipped_open,
            "skipped_external": skipped_external,
            "skipped_incomplete": skipped_incomplete,
        }

    # ============================================================
    # RECONCILIACIÓN
    # ============================================================

    def reconcile_open_trades(
        self,
        executor,
        source: str = "DEMO",
    ):
        """
        Diagnóstico entre SQLite y MT5.
        """

        before = self.open_trades(
            source=source
        )

        synced = self.sync_closed_mt5_trades(
            executor,
            source=source,
        )

        after = self.open_trades(
            source=source
        )

        unresolved = [
            trade
            for trade in after
            if not trade.get(
                "broker_position_ticket"
            )
        ]

        return {
            "source": str(source).upper(),
            "open_before": len(before),
            "closed_synced": int(synced),
            "open_after": len(after),
            "unresolved_without_position_ticket": (
                unresolved
            ),
        }

    def account_snapshots_dataframe(self):
        """Devuelve la serie completa de snapshots de cuenta como DataFrame.

        Es la base para reconstruir la curva de capital y calcular el
        drawdown en la pantalla de Cuenta.
        """
        with self.Session() as session:
            rows = (
                session.execute(
                    select(AccountSnapshot).order_by(
                        AccountSnapshot.snapshot_time,
                        AccountSnapshot.id,
                    )
                )
                .scalars()
                .all()
            )

        return pd.DataFrame([
            {
                "id": row.id,
                "snapshot_time": row.snapshot_time,
                "broker": row.broker,
                "balance": row.balance,
                "equity": row.equity,
                "margin": row.margin,
                "free_margin": row.free_margin,
                "profit": row.profit,
            }
            for row in rows
        ])
