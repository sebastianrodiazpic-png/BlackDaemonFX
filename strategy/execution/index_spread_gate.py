"""
strategy/execution/index_spread_gate.py
=======================================
Filtro Dinámico de Spread y Guardián de Sesión de Contado para Índices Bursátiles (Indices Worker).

Blindaje institucional para:
- Wall Street 30 (Dow Jones 30)
- US Tech 100 (Nasdaq 100)
- US SP 500 (S&P 500)
- Germany 40 (DAX 40)

Reglas de protección:
1. Horario Estricto de Sesión de Contado (Cash Session):
   - Índices US: 09:30 a 16:00 NY (Lunes a Viernes). Cero operativa en pre-market o noche con spreads abiertos.
   - Germany 40: 08:00 a 16:30 CET / Frankfurt (Lunes a Viernes).
2. Techo Máximo de Spread Absoluto por Índice (Hard Cap en puntos):
   - Wall Street 30: max 4.0 pts
   - US Tech 100: max 2.5 pts
   - US SP 500: max 0.8 pts
   - Germany 40: max 3.0 pts
3. Ratio Máximo Spread / Stop Loss <= 1.5% (max_risk_ratio configurable vía DAEMONBLACKFX_INDEX_MAX_RISK_RATIO).
4. Persistencia atómica de línea base en storage/runtime/index_spread/.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import math
import os
import statistics
import threading
import time

_LOCK = threading.RLock()
ROOT = Path(__file__).resolve().parents[2] / 'storage/runtime/index_spread'

# Calibración Institucional de Índices (v117): Pre-Market 08:00 NY y Ratio de Spread 2.5%
DAEMONBLACKFX_INDEX_PREMARKET_ENABLED = os.getenv("DAEMONBLACKFX_INDEX_PREMARKET_ENABLED", "1").strip().lower() in ("1", "true", "on")
DAEMONBLACKFX_INDEX_US_OPEN_HOUR = float(os.getenv("DAEMONBLACKFX_INDEX_US_OPEN_HOUR", "8.0" if DAEMONBLACKFX_INDEX_PREMARKET_ENABLED else "9.5"))
DAEMONBLACKFX_INDEX_DEFAULT_MAX_RISK_RATIO = float(os.getenv("DAEMONBLACKFX_INDEX_MAX_RISK_RATIO", "0.025"))

INDEX_SPECS = {
    'WALL STREET 30': {'max_spread': 4.0, 'point': 1.0, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'WALLSTREET30': {'max_spread': 4.0, 'point': 1.0, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'US30': {'max_spread': 4.0, 'point': 1.0, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'US TECH 100': {'max_spread': 2.5, 'point': 0.1, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'USTECH100': {'max_spread': 2.5, 'point': 0.1, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'NAS100': {'max_spread': 2.5, 'point': 0.1, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'US SP 500': {'max_spread': 0.8, 'point': 0.01, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'USSP500': {'max_spread': 0.8, 'point': 0.01, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'US500': {'max_spread': 0.8, 'point': 0.01, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0},
    'GERMANY 40': {'max_spread': 3.0, 'point': 0.1, 'tz': 'Europe/Berlin', 'open': 8.0, 'close': 16.5},
    'GERMANY40': {'max_spread': 3.0, 'point': 0.1, 'tz': 'Europe/Berlin', 'open': 8.0, 'close': 16.5},
    'GER40': {'max_spread': 3.0, 'point': 0.1, 'tz': 'Europe/Berlin', 'open': 8.0, 'close': 16.5},
    'DAX40': {'max_spread': 3.0, 'point': 0.1, 'tz': 'Europe/Berlin', 'open': 8.0, 'close': 16.5},
}

DEFAULT_INDEX_SPEC = {'max_spread': 5.0, 'point': 1.0, 'tz': 'America/New_York', 'open': DAEMONBLACKFX_INDEX_US_OPEN_HOUR, 'close': 16.0}


def is_index_symbol(symbol: str) -> bool:
    """True si el instrumento pertenece a la familia de Índices Bursátiles."""
    s = str(symbol or "").strip().upper()
    return any(k in s for k in ("WALL", "TECH 100", "TECH100", "SP 500", "SP500", "GERMANY", "GER40", "DAX", "US30", "US500", "NAS100"))


def get_index_spec(symbol: str) -> dict:
    norm = str(symbol or "").strip().upper()
    return INDEX_SPECS.get(norm, DEFAULT_INDEX_SPEC)


def is_index_cash_session(symbol: str, now: datetime | None = None) -> bool:
    """Valida si el mercado de contado del índice está abierto con volumen institucional pleno."""
    now = now or datetime.now(timezone.utc)
    spec = get_index_spec(symbol)
    local = now.astimezone(ZoneInfo(spec['tz']))
    # Solo de Lunes (0) a Viernes (4)
    if local.weekday() > 4:
        return False
    hour = local.hour + local.minute / 60.0 + local.second / 3600.0
    return spec['open'] <= hour < spec['close']


class IndexSpreadGuard:
    """Guardián de liquidez y spreads para índices bursátiles con restricción de sesión de contado."""

    def __init__(
        self,
        worker: str = "INDICES",
        root: Path | str | None = None,
        minimum_samples: int = 15,
        multiplier: float = 2.0,
        max_risk_ratio: float = 0.025,
        stable_samples: int = 3,
    ):
        self.worker = str(worker)
        self.path = Path(root or ROOT) / f"{self.worker}.json"
        self.minimum_samples = int(minimum_samples)
        self.multiplier = float(multiplier)
        self.max_risk_ratio = float(os.getenv("DAEMONBLACKFX_INDEX_MAX_RISK_RATIO", str(max_risk_ratio)))
        self.stable_samples = int(stable_samples)

        try:
            self.state = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.state = {'worker': self.worker, 'symbols': {}}

    def observe(self, symbol: str, quote: dict, now: datetime | None = None) -> dict:
        with _LOCK:
            return self._observe(symbol, quote, now)

    def _observe(self, symbol: str, quote: dict, now: datetime | None = None) -> dict:
        now = now or datetime.now(timezone.utc)
        item = self.state['symbols'].setdefault(symbol, {'samples': [], 'stable_count': 0})

        previous = item.get('observed_at')
        if previous and (now - datetime.fromisoformat(previous)).total_seconds() > 95:
            item['stable_count'] = 0

        item.update(observed_at=now.isoformat(), quote=dict(quote))

        # 1. Comprobación de Sesión de Contado
        in_session = is_index_cash_session(symbol, now)
        if not in_session:
            item['stable_count'] = 0
            item.update(
                normal=False,
                ready=False,
                reason='INDEX_OFF_MARKET_HOURS'
            )
            return dict(item)

        # 2. Validación de cotización
        valid = quote.get('spread_status') == 'AVAILABLE' and quote.get('spread_source') == 'MT5_EXECUTION'
        try:
            stamp = datetime.fromisoformat(str(quote['spread_quote_time']).replace('Z', '+00:00'))
            age = (now - stamp).total_seconds()
            valid = valid and (0 <= age <= 30)
        except (ValueError, KeyError, TypeError):
            valid = False

        spread = quote.get('spread')
        valid = valid and isinstance(spread, (float, int)) and math.isfinite(spread) and spread >= 0

        if not valid:
            item['stable_count'] = 0
            item.update(normal=False, ready=False, reason='QUOTE_UNAVAILABLE')
            return dict(item)

        # 3. Techo duro de spread por índice
        spec = get_index_spec(symbol)
        max_spread = spec['max_spread']

        cutoff_7d = (now - timedelta(days=7)).isoformat()
        samples = [x for x in item['samples'] if x['at'] >= cutoff_7d]
        median = statistics.median(x['spread'] for x in samples) if len(samples) >= self.minimum_samples else None

        spread_ok = (spread <= max_spread)
        spike_ok = (median is None or spread <= median * self.multiplier)
        normal = bool(valid and spread_ok and spike_ok)

        spaced = previous is None or (now - datetime.fromisoformat(previous)).total_seconds() >= 10
        if not normal:
            item['stable_count'] = 0
        elif spaced:
            item['stable_count'] += 1

        if valid and spaced and in_session and spread_ok and (median is None or spread <= median * self.multiplier):
            samples.append({'at': now.isoformat(), 'spread': spread})
        item['samples'] = samples[-720:]

        ready = bool(normal and (item['stable_count'] >= self.stable_samples or median is None))

        reason = (
            'SPREAD_ABOVE_HARD_CAP' if not spread_ok else
            'SPREAD_SPIKE_DETECTED' if not spike_ok else
            'BASELINE_WARMUP' if median is None else
            'WAITING_STABLE_SPREAD' if item['stable_count'] < self.stable_samples else
            'SPREAD_NORMALIZED'
        )

        item.update(
            baseline=median,
            samples_count=len(samples),
            spread_actual=round(spread, 4),
            max_spread_cap=max_spread,
            normal=normal,
            ready=ready,
            reason=reason
        )

        self._persist_state(now)
        return dict(item)

    def check(
        self,
        symbol: str,
        quote: dict,
        direction: str,
        stop: float,
        max_risk_ratio: float | None = None,
        now: datetime | None = None,
    ) -> dict:
        """Audita si una entrada en un índice bursátil cumple con el horario de contado y el límite de spread."""
        item = self.observe(symbol, quote, now)
        if not item.get('ready'):
            return {
                'allowed': False,
                'reason': item.get('reason', 'SPREAD_NOT_READY'),
                'spread_actual': item.get('spread_actual'),
                'max_spread_cap': item.get('max_spread_cap'),
                'spread_risk_ratio': None,
                'max_risk_ratio': max_risk_ratio or self.max_risk_ratio,
                'baseline': item.get('baseline'),
                'quote': quote,
            }

        limit_ratio = float(max_risk_ratio if max_risk_ratio is not None else self.max_risk_ratio)
        entry = quote.get('execution_ask' if str(direction).upper() == 'BUY' else 'execution_bid')
        distance = (entry - stop if str(direction).upper() == 'BUY' else stop - entry) if isinstance(entry, (float, int)) else 0.0

        spread = quote.get('spread', 0.0)
        ratio = (spread / distance) if (distance > 0 and spread is not None) else None

        allowed = bool(item['ready'] and ratio is not None and ratio <= limit_ratio)
        reason = 'SPREAD_ACCEPTED' if allowed else ('SPREAD_RISK_RATIO_EXCEEDED' if ratio and ratio > limit_ratio else item['reason'])

        return {
            'allowed': allowed,
            'reason': reason,
            'spread_actual': round(spread, 4) if spread is not None else None,
            'max_spread_cap': item.get('max_spread_cap'),
            'distance_to_sl': round(distance, 4),
            'spread_risk_ratio': round(ratio, 4) if ratio is not None else None,
            'max_risk_ratio': limit_ratio,
            'baseline': item.get('baseline'),
            'stable_count': item.get('stable_count', 0),
            'quote': quote,
        }

    def _persist_state(self, now: datetime):
        self.state['updated_at'] = now.isoformat()
        self.state['limits'] = {
            'max_risk_ratio': self.max_risk_ratio,
            'minimum_samples': self.minimum_samples,
            'stable_samples': self.stable_samples,
            'multiplier': self.multiplier,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(f'.{os.getpid()}.tmp')
        try:
            temp.write_text(json.dumps(self.state, ensure_ascii=False), encoding='utf-8')
            for attempt in range(3):
                try:
                    temp.replace(self.path)
                    break
                except PermissionError:
                    if attempt == 2:
                        raise
                    time.sleep(0.05 * (attempt + 1))
        except OSError:
            pass
        finally:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
