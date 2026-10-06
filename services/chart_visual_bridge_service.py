"""Servicio Chart Visual Bridge para proyectar Order Blocks, FVGs y Liquidez en MT5.

Permite que el cerebro de análisis en Python transmita en tiempo real las zonas
institucionales calculadas (H1 Order Blocks, M15 Fair Value Gaps y barridos de liquidez)
para que un indicador nativo en MetaTrader 5 (`tools/DaemonVisualBridge.mq5`) los dibuje
automáticamente sobre las velas del gráfico.

Mecanismo:
1. Detecta la ruta de datos del terminal MT5 (`MQL5/Files/`) o un directorio compartido.
2. Guarda un archivo JSON específico por símbolo: `blackdaemon_visual_bridge_{symbol}.json`.
3. Cada zona contiene:
   - Tipo de objeto: `ORDER_BLOCK` (azul translúcido), `FVG` (verde/rojo), `SWEEP` (línea punteada).
   - Coordenadas temporales: `time_start`, `time_end`.
   - Coordenadas de precio: `price_high`, `price_low`.
   - Metadatos: timeframe de origen (H1, M15, M5), score, estado de mitigación.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import MetaTrader5 as mt5
except ModuleNotFoundError:
    mt5 = None


@dataclass
class VisualZone:
    zone_id: str
    zone_type: str  # ORDER_BLOCK, FVG, SWEEP, TRADE_LEVEL
    timeframe: str  # H1, M15, M5
    direction: str  # BULLISH, BEARISH, NEUTRAL
    price_high: float
    price_low: float
    time_start: str  # ISO UTC o YYYY.MM.DD HH:MM
    time_end: str
    label: str
    color_hex: str
    line_style: str = "SOLID"  # SOLID, DOT, DASH
    translucent: bool = True
    mitigated: bool = False


class ChartVisualBridgeService:
    """Gestiona y sincroniza los objetos gráficos proyectados en MetaTrader 5."""

    def __init__(self, custom_files_dir: Optional[Path | str] = None):
        self.files_dir = self._resolve_files_directory(custom_files_dir)
        self.active_zones: Dict[str, List[VisualZone]] = {}

    def _resolve_files_directory(self, custom_path: Optional[Path | str]) -> Path:
        if custom_path:
            p = Path(custom_path)
            p.mkdir(parents=True, exist_ok=True)
            return p

        # Intentar consultar la ruta de MT5 si está inicializado
        if mt5 is not None:
            try:
                term_info = mt5.terminal_info()
                if term_info and getattr(term_info, "data_path", None):
                    mt5_files = Path(term_info.data_path) / "MQL5" / "Files"
                    mt5_files.mkdir(parents=True, exist_ok=True)
                    return mt5_files
            except Exception:
                pass

        # Fallback a directorio local persistente del bot
        local_dir = Path(__file__).resolve().parents[1] / "storage" / "visual_bridge"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir

    def add_order_block(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        price_high: float,
        price_low: float,
        time_start: str | datetime,
        time_end: str | datetime,
        label: str = "H1 Order Block",
    ) -> VisualZone:
        """Registra un Order Block (Azul translúcido para H1)."""
        t_start = time_start.isoformat() if isinstance(time_start, datetime) else str(time_start)
        t_end = time_end.isoformat() if isinstance(time_end, datetime) else str(time_end)
        zid = f"OB_{symbol}_{timeframe}_{t_start}_{price_high:.5f}"

        zone = VisualZone(
            zone_id=zid,
            zone_type="ORDER_BLOCK",
            timeframe=timeframe,
            direction=str(direction).upper(),
            price_high=float(price_high),
            price_low=float(price_low),
            time_start=t_start,
            time_end=t_end,
            label=f"[{timeframe}] {label}",
            color_hex="#1e90ff",  # DodgerBlue
            line_style="SOLID",
            translucent=True,
        )
        self._append_zone(symbol, zone)
        return zone

    def add_fvg(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        price_high: float,
        price_low: float,
        time_start: str | datetime,
        time_end: str | datetime,
        label: str = "M15 FVG",
    ) -> VisualZone:
        """Registra un Fair Value Gap (Verde suave para alcista, Rojo suave para bajista)."""
        t_start = time_start.isoformat() if isinstance(time_start, datetime) else str(time_start)
        t_end = time_end.isoformat() if isinstance(time_end, datetime) else str(time_end)
        zid = f"FVG_{symbol}_{timeframe}_{t_start}_{price_high:.5f}"
        is_bull = str(direction).upper() in ("BUY", "BULLISH", "LONG")
        color = "#2e8b57" if is_bull else "#cd5c5c"  # SeaGreen o IndianRed

        zone = VisualZone(
            zone_id=zid,
            zone_type="FVG",
            timeframe=timeframe,
            direction=str(direction).upper(),
            price_high=float(price_high),
            price_low=float(price_low),
            time_start=t_start,
            time_end=t_end,
            label=f"[{timeframe}] {label}",
            color_hex=color,
            line_style="SOLID",
            translucent=True,
        )
        self._append_zone(symbol, zone)
        return zone

    def add_liquidity_sweep(
        self,
        symbol: str,
        timeframe: str,
        level_price: float,
        time_start: str | datetime,
        time_end: str | datetime,
        label: str = "Liquidity Sweep",
    ) -> VisualZone:
        """Registra una línea de puntos dorada de barrido de liquidez."""
        t_start = time_start.isoformat() if isinstance(time_start, datetime) else str(time_start)
        t_end = time_end.isoformat() if isinstance(time_end, datetime) else str(time_end)
        zid = f"SWEEP_{symbol}_{t_start}_{level_price:.5f}"

        zone = VisualZone(
            zone_id=zid,
            zone_type="SWEEP",
            timeframe=timeframe,
            direction="NEUTRAL",
            price_high=float(level_price),
            price_low=float(level_price),
            time_start=t_start,
            time_end=t_end,
            label=f"[{timeframe}] {label}",
            color_hex="#ffd700",  # Gold
            line_style="DOT",
            translucent=False,
        )
        self._append_zone(symbol, zone)
        return zone

    def _append_zone(self, symbol: str, zone: VisualZone) -> None:
        sym = str(symbol).upper()
        if sym not in self.active_zones:
            self.active_zones[sym] = []
        # Reemplazar si existe el mismo id
        self.active_zones[sym] = [z for z in self.active_zones[sym] if z.zone_id != zone.zone_id]
        self.active_zones[sym].append(zone)

    def clear_symbol_zones(self, symbol: str) -> None:
        self.active_zones[str(symbol).upper()] = []
        self.publish(symbol)

    def publish(self, symbol: Optional[str] = None) -> List[Path]:
        """Escribe los archivos JSON listos para ser consumidos por MT5."""
        written = []
        targets = [str(symbol).upper()] if symbol else list(self.active_zones.keys())

        for sym in targets:
            zones = self.active_zones.get(sym, [])
            clean_sym = sym.replace(" ", "_")
            out_file = self.files_dir / f"blackdaemon_visual_bridge_{clean_sym}.json"

            payload = {
                "symbol": sym,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "zones_count": len(zones),
                "zones": [asdict(z) for z in zones],
            }

            try:
                out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
                written.append(out_file)
            except Exception as exc:
                print(f"Error escribiendo bridge visual para {sym}: {exc}")

        return written
