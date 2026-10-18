"""Persistent operator preferences, independently importable during dashboard reloads."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class StrategyRuntimePreference(Base):
    __tablename__ = 'strategy_runtime_preferences'
    __table_args__ = (Index('ix_strategy_runtime_preferences_lookup', 'source', 'strategy_name', 'id'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), default='DEMO')
    strategy_name: Mapped[str] = mapped_column(String(64))
    settings_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
