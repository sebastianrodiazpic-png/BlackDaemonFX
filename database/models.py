from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from database.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    execution_key: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    broker_order_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    broker_deal_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    broker_position_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(32), default="LIVE", index=True)
    broker: Mapped[str] = mapped_column(String(64), default="MT5")
    instrument: Mapped[str] = mapped_column(String(128), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), default="M5")
    direction: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    result: Mapped[str | None] = mapped_column(String(32), nullable=True)

    entry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)

    planned_rr: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_rr: Mapped[float | None] = mapped_column(Float, nullable=True)
    bars_held: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    balance_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    balance_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    drawdown_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    drawdown_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    risk_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    swap: Mapped[float] = mapped_column(Float, default=0.0)
    net_pnl: Mapped[float] = mapped_column(Float, default=0.0)

    setup_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    strategy_version: Mapped[str] = mapped_column(String(64), default="smc-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument: Mapped[str] = mapped_column(String(128), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), default="M5")
    signal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    direction: Mapped[str | None] = mapped_column(String(8), nullable=True)
    valid: Mapped[bool] = mapped_column(Boolean, default=False)

    trend_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    swing_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    liquidity_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    sweep_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    structure_break_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    order_block_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    retest_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_discount_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmation_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    broker: Mapped[str] = mapped_column(String(64), default="MT5")
    balance: Mapped[float] = mapped_column(Float)
    equity: Mapped[float] = mapped_column(Float)
    margin: Mapped[float] = mapped_column(Float, default=0.0)
    free_margin: Mapped[float] = mapped_column(Float, default=0.0)
    profit: Mapped[float] = mapped_column(Float, default=0.0)


class TradeJournal(Base):
    """Historial permanente de operaciones para Cuenta activa.

    Esta tabla es deliberadamente independiente de ``trades``: el reset
    operativo puede reconstruir la tabla de trabajo sin perder el historial
    auditado de operaciones ya observadas por DaemonBlackFx.
    """
    __tablename__ = "trade_journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    journal_key: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    source_trade_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(32), default="LIVE", index=True)
    broker: Mapped[str] = mapped_column(String(64), default="MT5")
    instrument: Mapped[str] = mapped_column(String(128), index=True)
    direction: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    entry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    planned_rr: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_rr: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    execution_key: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    external_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    broker_position_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    strategy_version: Mapped[str] = mapped_column(String(64), default="smc-v1")
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AccountStatsReset(Base):
    """Marca persistente del inicio de una nueva ventana estadística de Cuenta activa."""

    __tablename__ = "account_stats_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reset_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    reason: Mapped[str] = mapped_column(String(128), default="MANUAL_RESET")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class InstrumentSelectionPreference(Base):
    """Última selección de instrumentos elegida por el usuario para nuevas entradas."""

    __tablename__ = "instrument_selection_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    selected_symbols_json: Mapped[str] = mapped_column(Text, default="[]")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class InstrumentSelectionProfilePreference(Base):
    """Selección persistente independiente por universo operativo."""

    __tablename__ = "instrument_selection_profile_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    selection_profile: Mapped[str] = mapped_column(String(32), index=True)
    selected_symbols_json: Mapped[str] = mapped_column(Text, default="[]")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class DaemonAuditEvent(Base):
    """Bitácora append-only de todo evento operativo relevante de DaemonBlackFx."""
    __tablename__ = "daemon_audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    instrument: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    action: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_key: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    broker_position_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    cycle_number: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WorkerRuntimeState(Base):
    """Estado operacional consolidado por worker multi-bot."""
    __tablename__ = "worker_runtime_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    bot_profile: Mapped[str] = mapped_column(String(32), index=True)
    daemon_magic: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(32), default="STARTING", index=True)
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cycle_number: Mapped[int] = mapped_column(Integer, default=0)
    symbols_total: Mapped[int] = mapped_column(Integer, default=0)
    symbols_processed: Mapped[int] = mapped_column(Integer, default=0)
    current_symbol: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_action: Mapped[str | None] = mapped_column(String(96), nullable=True)
    last_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_elapsed_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PositionVisualAudit(Base):
    """Último snapshot visual multi-timeframe por símbolo/worker."""
    __tablename__ = "position_visual_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    bot_profile: Mapped[str] = mapped_column(String(32), index=True)
    daemon_magic: Mapped[int] = mapped_column(Integer, index=True)
    instrument: Mapped[str] = mapped_column(String(128), index=True)
    chart_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, index=True)


class TradeVisualAudit(Base):
    """Auditoría visual persistente por trade: entrada inmutable + estado actual."""
    __tablename__ = "trade_visual_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    bot_profile: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    daemon_magic: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    instrument: Mapped[str] = mapped_column(String(128), index=True)
    broker_position_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    entry_chart_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    entry_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_chart_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    latest_market_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    latest_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class TradeAuditSnapshot(Base):
    """Serie histórica append-only de Entrada vs. Ahora por trade.

    Guarda datos estructurados suficientes para investigación y backtesting de
    la evolución de la tesis sin sobrescribir la evidencia original.
    """
    __tablename__ = "trade_audit_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(Integer, index=True)
    source: Mapped[str] = mapped_column(String(32), default="DEMO", index=True)
    bot_profile: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    daemon_magic: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    instrument: Mapped[str] = mapped_column(String(128), index=True)
    broker_position_ticket: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    entry_view_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_view_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    visual_context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

