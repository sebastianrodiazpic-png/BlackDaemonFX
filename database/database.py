"""Configuración de la base de datos SQLite: rutas, motor y migraciones ligeras.

Resuelve DONDE vive la base de datos y deja el motor SQLAlchemy listo para
un uso concurrente por varios workers.

UBICACION ESTABLE: la base no se guarda dentro de la carpeta del proyecto,
que cambia con cada version, sino en un directorio persistente del usuario
(`%LOCALAPPDATA%\\BlackDaemonFx` en Windows). Asi el historico sobrevive a
las actualizaciones. La variable `DAEMONBLACKFX_DB_PATH` permite forzar una
ruta concreta, y `DAEMONBLACKFX_DATA_DIR` el directorio.

ARRANQUE CON MIGRACION: al resolver la ruta por defecto se buscan bases de
versiones anteriores y, si la ubicacion estable esta vacia, se adopta la que
mas actividad tenga, para no perder el historial.

CONCURRENCIA: se configura WAL y unos PRAGMA por conexion, de modo que varios
workers escriban a la vez sin bloquearse, con espera amplia ante bloqueos.

Vinculaciones:
- `database.models` define las tablas sobre la `Base` declarada aqui.
- `database.repository` obtiene de aqui sus sesiones.
- Todo el proyecto persiste a traves de esta configuracion.
"""

from __future__ import annotations

from contextlib import closing
import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
LEGACY_PROJECT_DB_PATH = BASE_DIR / "trading_bot.sqlite3"


def _stable_data_dir() -> Path:
    """Directorio persistente independiente de la carpeta de versión."""
    explicit_dir = os.getenv("DAEMONBLACKFX_DATA_DIR")
    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()
    if os.name == "nt":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
        if base:
            return Path(base) / "BlackDaemonFx"
    return Path.home() / ".blackdaemonfx"


def _explicit_db_path() -> Path | None:
    """Devuelve la ruta forzada por `DAEMONBLACKFX_DB_PATH`, o `None`.

    Cuando esta definida, tiene prioridad sobre cualquier otra logica y
    desactiva la migracion automatica desde versiones anteriores.
    """
    value = os.getenv("DAEMONBLACKFX_DB_PATH")
    return Path(value).expanduser().resolve() if value else None


def _sqlite_activity_score(path: Path) -> tuple[int, int, int, int]:
    """(trade_journal, trades, account_snapshots, total) sin modificar el archivo."""
    if not path.exists() or path.stat().st_size <= 0:
        return (0, 0, 0, 0)
    counts = []
    try:
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=2)
        try:
            names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table in ("trade_journal", "trades", "account_snapshots"):
                if table in names:
                    counts.append(int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]))
                else:
                    counts.append(0)
        finally:
            conn.close()
    except Exception:
        return (0, 0, 0, 0)
    return (*counts, sum(counts))


def _legacy_candidates() -> list[Path]:
    """Busca bases de versiones hermanas sin recorrer el disco completo."""
    candidates = []
    for p in (
        LEGACY_PROJECT_DB_PATH,
        *(PROJECT_ROOT.parent.glob("*/database/trading_bot.sqlite3") if PROJECT_ROOT.parent.exists() else []),
    ):
        try:
            p = Path(p).resolve()
        except Exception:
            continue
        if p not in candidates and p.exists():
            candidates.append(p)
    return candidates


def backup_sqlite_database(source_path: str | Path, destination_path: str | Path) -> Path:
    """Crea una copia consistente que incorpora WAL mediante la API de SQLite."""
    source = Path(source_path).expanduser().resolve()
    destination = Path(destination_path).expanduser().resolve()
    if source == destination:
        raise ValueError("La base de origen y destino deben ser diferentes")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".backing_up")
    if tmp.exists():
        tmp.unlink()
    source_uri = f"file:{source.as_posix()}?mode=ro"
    try:
        # sqlite3.Connection.__exit__ sólo confirma/revierte la transacción: no
        # cierra el handle. Windows impide replace/unlink mientras ese handle
        # permanece abierto, por eso usamos closing() de forma explícita.
        with closing(sqlite3.connect(source_uri, uri=True, timeout=30)) as source_db:
            with closing(sqlite3.connect(tmp, timeout=30)) as target_db:
                source_db.backup(target_db, pages=1024, sleep=0.01)
                integrity = target_db.execute("PRAGMA integrity_check").fetchone()
                if not integrity or str(integrity[0]).lower() != "ok":
                    raise sqlite3.DatabaseError(
                        f"La copia SQLite no superó integrity_check: {integrity}"
                    )
        tmp.replace(destination)
        return destination
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                # No ocultar el error original con un segundo WinError durante
                # la limpieza. En el siguiente arranque se reintentará borrar.
                pass
        raise


def _bootstrap_stable_database(stable_path: Path) -> dict:
    """Recupera automáticamente la DB histórica sólo si la estable está vacía.

    Elegimos el candidato con mayor cantidad de registros persistentes y,
    ante empate, el de modificación más reciente. Nunca sobreescribimos una
    base estable que ya tenga actividad.
    """
    stable_path.parent.mkdir(parents=True, exist_ok=True)
    current_score = _sqlite_activity_score(stable_path)
    result = {
        "path": str(stable_path),
        "recovered": False,
        "recovered_from": None,
        "current_score": current_score,
        "candidates": [],
    }
    if current_score[-1] > 0:
        return result

    ranked = []
    for candidate in _legacy_candidates():
        if candidate == stable_path:
            continue
        score = _sqlite_activity_score(candidate)
        result["candidates"].append({"path": str(candidate), "score": score})
        if score[-1] > 0:
            try:
                mtime = candidate.stat().st_mtime
            except Exception:
                mtime = 0
            ranked.append((score[-1], score[0], score[1], score[2], mtime, candidate))

    if not ranked:
        return result

    ranked.sort(reverse=True, key=lambda row: row[:-1])
    source = ranked[0][-1]
    try:
        # Una copia directa del archivo principal no es segura si SQLite está en
        # WAL: puede dejar fuera transacciones confirmadas o mezclar páginas de
        # instantes distintos. La API backup crea una imagen consistente aun
        # cuando la base de origen siga abierta.
        backup_sqlite_database(source, stable_path)
        result["recovered"] = True
        result["recovered_from"] = str(source)
        result["current_score"] = _sqlite_activity_score(stable_path)
        print(
            "[DB CONTINUIDAD] Base histórica recuperada automáticamente: "
            f"{source} -> {stable_path}"
        )
    except Exception as exc:
        result["recovery_error"] = str(exc)
        print(f"[DB CONTINUIDAD ERROR] No fue posible recuperar {source}: {exc}")
    return result


_EXPLICIT_DB = _explicit_db_path()
DEFAULT_DB_PATH = _EXPLICIT_DB or (_stable_data_dir() / "trading_bot.sqlite3")
_DB_BOOTSTRAP_INFO = None


class Base(DeclarativeBase):
    """Clase base declarativa de la que heredan todos los modelos ORM.

    `database.models` la usa para definir las tablas, e `init_database` crea
    a partir de sus metadatos el esquema completo.
    """

    pass


def resolve_db_path(db_path: str | Path | None = None) -> Path:
    """Resuelve la ruta definitiva de la base de datos y garantiza su carpeta.

    Si no se indica ruta y tampoco hay una forzada por variable de entorno,
    ejecuta el arranque con migracion: busca bases de versiones anteriores y
    adopta la de mayor actividad si la ubicacion estable esta vacia.

    Args:
        db_path: ruta explicita; si falta se usa la ubicacion estable.

    Returns:
        Ruta absoluta, con el directorio padre ya creado.
    """
    global _DB_BOOTSTRAP_INFO
    path = Path(db_path).expanduser().resolve() if db_path else Path(DEFAULT_DB_PATH).expanduser().resolve()
    if db_path is None and _EXPLICIT_DB is None:
        _DB_BOOTSTRAP_INFO = _bootstrap_stable_database(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def database_diagnostics(db_path: str | Path | None = None) -> dict:
    """Informa del estado de la base de datos sin modificarla.

    Sirve para responder a la pregunta "¿esta el bot leyendo la base que
    creo?", habitual tras una actualizacion de version.

    Returns:
        Dict con la ruta en uso, si existe, su tamano, el recuento de filas
        de las tablas de actividad, el resultado de la migracion de arranque
        y las variables de entorno implicadas.
    """
    path = resolve_db_path(db_path)
    score = _sqlite_activity_score(path)
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "trade_journal_rows": score[0],
        "trade_rows": score[1],
        "account_snapshot_rows": score[2],
        "total_activity_rows": score[3],
        "bootstrap": _DB_BOOTSTRAP_INFO,
        "explicit_env_path": os.getenv("DAEMONBLACKFX_DB_PATH"),
        "stable_data_dir": str(_stable_data_dir()),
    }


def get_engine(db_path: str | Path | None = None):
    """Crea el motor SQLAlchemy configurado para acceso concurrente.

    Aplica los ajustes que hacen viable que varios workers escriban a la vez:

    - `journal_mode=WAL`: los lectores no bloquean al escritor.
    - `busy_timeout=30000`: ante un bloqueo se espera hasta 30 s en lugar de
      fallar de inmediato.
    - `synchronous=NORMAL`: equilibrio entre durabilidad y rendimiento.
    - Limites de checkpoint y tamano de journal, mas cache en memoria.

    Los PRAGMA se aplican mediante un escucha del evento `connect`, de modo
    que TODA conexion los reciba, sin depender de quien abrio la base.

    Args:
        db_path: ruta explicita; si falta se usa la ubicacion estable.

    Returns:
        El motor SQLAlchemy listo para usar.
    """
    path = resolve_db_path(db_path)
    engine = create_engine(
        f"sqlite:///{path}",
        future=True,
        connect_args={"timeout": 30},
        pool_pre_ping=True,
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, _connection_record):
        """Aplica los PRAGMA de concurrencia a cada conexión nueva."""
        cursor = dbapi_connection.cursor()
        try:
            # PRAGMAs por conexión: todos los workers comparten los mismos
            # límites de espera/checkpoint y no dependen de quién abrió la DB.
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA wal_autocheckpoint=2000")
            cursor.execute("PRAGMA journal_size_limit=67108864")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA cache_size=-32768")
        finally:
            cursor.close()

    with engine.begin() as connection:
        connection.execute(text("PRAGMA journal_mode=WAL"))
    return engine


def get_session_factory(db_path: str | Path | None = None):
    """Crea la fábrica de sesiones ORM sobre el motor configurado.

    Desactiva `autoflush` y `autocommit` para que las escrituras sean
    explicitas: nada llega a disco hasta que se confirma la transaccion.
    """
    engine = get_engine(db_path)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _ensure_trade_columns(engine):
    """Añade a `trades` las columnas que falten, migrando bases antiguas.

    MIGRACION LIGERA sin herramienta externa: el proyecto ha ido sumando
    columnas (tickets del broker, RR planificado y realizado, motivo de
    cierre, metricas de drawdown, detalles JSON) y una base creada por una
    version anterior no las tiene.

    Compara las columnas presentes con las requeridas y emite un `ALTER
    TABLE` solo por las ausentes, por lo que es idempotente y seguro de
    ejecutar en cada arranque. No elimina ni modifica columnas existentes,
    de modo que nunca destruye datos.
    """
    inspector = inspect(engine)
    if "trades" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("trades")}
    required = {
        "source": "VARCHAR(32) NOT NULL DEFAULT 'LIVE'",
        "execution_key": "VARCHAR(256)",
        "broker_order_ticket": "VARCHAR(128)",
        "broker_deal_ticket": "VARCHAR(128)",
        "broker_position_ticket": "VARCHAR(128)",
        "planned_rr": "FLOAT",
        "realized_rr": "FLOAT",
        "bars_held": "INTEGER",
        "exit_reason": "TEXT",
        "equity": "FLOAT",
        "peak_balance": "FLOAT",
        "drawdown_amount": "FLOAT",
        "drawdown_percent": "FLOAT",
        "details_json": "TEXT",
    }

    with engine.begin() as connection:
        for name, sql_type in required.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE trades ADD COLUMN {name} {sql_type}"))


def _ensure_performance_indexes(engine):
    """Índices compatibles con instalaciones existentes y alta concurrencia."""
    statements = (
        "CREATE INDEX IF NOT EXISTS ix_audit_type_time "
        "ON daemon_audit_events (event_type, event_time)",
        "CREATE INDEX IF NOT EXISTS ix_audit_source_time "
        "ON daemon_audit_events (source, event_time)",
        "CREATE INDEX IF NOT EXISTS ix_trades_source_status "
        "ON trades (source, status)",
        "CREATE INDEX IF NOT EXISTS ix_runtime_source_profile "
        "ON worker_runtime_states (source, bot_profile)",
    )
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(text("PRAGMA optimize"))


def init_database(db_path: str | Path | None = None):
    """Inicializa la base: crea el esquema, migra columnas y crea los índices.

    Punto de entrada de arranque. La importacion de los modelos dentro de la
    funcion es necesaria para registrarlos en los metadatos de `Base` antes
    de crear las tablas, y evita ademas un ciclo de importacion.

    Es idempotente: crea solo lo que falte, por lo que puede ejecutarse en
    cada arranque sin riesgo.

    Args:
        db_path: ruta explicita; si falta se usa la ubicacion estable.

    Returns:
        El motor ya inicializado.
    """
    from database.models import Trade, Signal, AccountSnapshot, TradeJournal, AccountStatsReset, InstrumentSelectionPreference, InstrumentSelectionProfilePreference, DaemonAuditEvent, WorkerRuntimeState, PositionVisualAudit, TradeVisualAudit, TradeAuditSnapshot  # noqa: F401
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    _ensure_trade_columns(engine)
    _ensure_performance_indexes(engine)
    return engine
