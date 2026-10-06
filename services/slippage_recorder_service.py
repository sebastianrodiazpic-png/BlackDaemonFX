"""Grabador y auditor de Spread y Slippage a nivel de Tick (Microstructure Recorder).

Inspirado en prácticas de alta frecuencia y auditoría de brokers:
1. En el momento de la señal y envío de orden registra:
   - `signal_price` (Bid/Ask proyectado al validar la entrada)
   - `fill_price` (Precio real reportado en el ticket de deal de MT5)
   - `slippage_points` y `adverse_slippage_points`
   - `sl_distance` (Distancia en puntos al Stop Loss estructural)
   - `slippage_percent_of_sl` (% del Stop Loss consumido por deslizamiento)
   - `spread_current` vs `spread_average_5m` (expansión de spread anómala)
   - `execution_latency_ms` (milisegundos que tardó el broker en responder)
2. Guarda los registros en SQLite para auditoría forense persistente.
3. Alerta y Cuarentena Automática:
   - Si `slippage_percent_of_sl >= 20.0%`, activa cuarentena preventiva sobre el instrumento
     para proteger la cuenta de spikes severos (comunes en Boom/Crash o Volatility 75).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SlippageRecord:
    timestamp: str
    symbol: str
    direction: str
    deal_ticket: Optional[str]
    order_ticket: Optional[str]
    signal_price: float
    fill_price: float
    stop_loss: float
    sl_distance: float
    slippage_points: float
    adverse_slippage_points: float
    slippage_percent_of_sl: float
    spread_current: float
    spread_average_5m: float
    spread_expansion_ratio: float
    execution_latency_ms: float
    quarantine_triggered: bool
    quarantine_reason: Optional[str] = None


class SlippageRecorderService:
    """Registrador forense de slippage, spread y latencia en base de datos SQLite."""

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = self._resolve_db_path(db_path)
        self._init_db()

    def _resolve_db_path(self, db_path: Optional[Path | str]) -> Path:
        if db_path:
            p = Path(db_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
        default_dir = Path(__file__).resolve().parents[1] / "storage" / "database"
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir / "trading.db"

    def _init_db(self) -> None:
        """Crea la tabla de auditoría si no existe."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_microstructure_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    deal_ticket TEXT,
                    order_ticket TEXT,
                    signal_price REAL NOT NULL,
                    fill_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    sl_distance REAL NOT NULL,
                    slippage_points REAL NOT NULL,
                    adverse_slippage_points REAL NOT NULL,
                    slippage_percent_of_sl REAL NOT NULL,
                    spread_current REAL NOT NULL,
                    spread_average_5m REAL NOT NULL,
                    spread_expansion_ratio REAL NOT NULL,
                    execution_latency_ms REAL NOT NULL,
                    quarantine_triggered INTEGER NOT NULL DEFAULT 0,
                    quarantine_reason TEXT,
                    details_json TEXT
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_microstructure_symbol ON execution_microstructure_records (symbol)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_microstructure_quarantine ON execution_microstructure_records (quarantine_triggered)"
            )
            conn.commit()
        finally:
            conn.close()

    def record_execution(
        self,
        symbol: str,
        direction: str,
        signal_price: float,
        fill_price: float,
        stop_loss: float,
        spread_current: float = 0.0,
        spread_average_5m: float = 0.0,
        execution_latency_ms: float = 0.0,
        deal_ticket: Optional[str] = None,
        order_ticket: Optional[str] = None,
        quarantine_threshold_pct: float = 20.0,
    ) -> SlippageRecord:
        """Calcula el deslizamiento exacto y lo persiste en la base de datos."""
        signal_price = float(signal_price)
        fill_price = float(fill_price)
        stop_loss = float(stop_loss)
        spread_current = float(spread_current)
        spread_average_5m = float(spread_average_5m)
        execution_latency_ms = float(execution_latency_ms)

        is_buy = str(direction).upper() in ("BUY", "LONG")
        # Deslizamiento firmado: positivo = compramos más caro o vendimos más barato
        raw_slippage = (fill_price - signal_price) if is_buy else (signal_price - fill_price)
        adverse_slippage = max(0.0, raw_slippage)

        sl_distance = max(1e-9, abs(signal_price - stop_loss))
        slippage_pct_of_sl = (adverse_slippage / sl_distance) * 100.0

        spread_ratio = (spread_current / spread_average_5m) if spread_average_5m > 1e-9 else 1.0

        # Regla de Cuarentena Automática por Slippage Excesivo (> 20% del SL)
        quarantine_triggered = False
        quarantine_reason = None
        if slippage_pct_of_sl >= quarantine_threshold_pct:
            quarantine_triggered = True
            quarantine_reason = (
                f"SLIPPAGE_EXCEEDED_{quarantine_threshold_pct:.0f}PCT_SL: Deslizamiento adverso de "
                f"{slippage_pct_of_sl:.2f}% superó el umbral de seguridad del Stop Loss ({adverse_slippage:.4f} pts)"
            )

        now_str = datetime.now(timezone.utc).isoformat()
        rec = SlippageRecord(
            timestamp=now_str,
            symbol=str(symbol).upper(),
            direction=str(direction).upper(),
            deal_ticket=str(deal_ticket) if deal_ticket else None,
            order_ticket=str(order_ticket) if order_ticket else None,
            signal_price=round(signal_price, 5),
            fill_price=round(fill_price, 5),
            stop_loss=round(stop_loss, 5),
            sl_distance=round(sl_distance, 5),
            slippage_points=round(raw_slippage, 5),
            adverse_slippage_points=round(adverse_slippage, 5),
            slippage_percent_of_sl=round(slippage_pct_of_sl, 2),
            spread_current=round(spread_current, 5),
            spread_average_5m=round(spread_average_5m, 5),
            spread_expansion_ratio=round(spread_ratio, 2),
            execution_latency_ms=round(execution_latency_ms, 2),
            quarantine_triggered=quarantine_triggered,
            quarantine_reason=quarantine_reason,
        )

        self._save_to_sqlite(rec)
        return rec

    def _save_to_sqlite(self, rec: SlippageRecord) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO execution_microstructure_records (
                    timestamp, symbol, direction, deal_ticket, order_ticket,
                    signal_price, fill_price, stop_loss, sl_distance,
                    slippage_points, adverse_slippage_points, slippage_percent_of_sl,
                    spread_current, spread_average_5m, spread_expansion_ratio,
                    execution_latency_ms, quarantine_triggered, quarantine_reason,
                    details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.timestamp, rec.symbol, rec.direction, rec.deal_ticket, rec.order_ticket,
                    rec.signal_price, rec.fill_price, rec.stop_loss, rec.sl_distance,
                    rec.slippage_points, rec.adverse_slippage_points, rec.slippage_percent_of_sl,
                    rec.spread_current, rec.spread_average_5m, rec.spread_expansion_ratio,
                    rec.execution_latency_ms, 1 if rec.quarantine_triggered else 0, rec.quarantine_reason,
                    json.dumps(asdict(rec), ensure_ascii=False)
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_slippage_records(self, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Recupera los registros recientes de slippage para el dashboard y auditoría."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            if symbol:
                cursor.execute(
                    """
                    SELECT * FROM execution_microstructure_records
                    WHERE symbol = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (str(symbol).upper(), limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM execution_microstructure_records
                    ORDER BY id DESC LIMIT ?
                    """,
                    (limit,),
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
