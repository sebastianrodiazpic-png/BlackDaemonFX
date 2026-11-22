"""
strategy/execution/commodity_spread_gate.py
===========================================
Filtro Dinámico de Spread y Guardián de Liquidez para Materias Primas (Commodities & Metals).

Blindaje institucional para:
- Oro spot (XAUUSD, XAUUSDmicro, XAUEUR, XAUEURmicro)
- Plata spot (XAGUSD, XAGUSDmicro)
- Energías: Petróleo WTI (US Oil) y Petróleo Brent (UK Brent Oil)

Reglas de protección:
1. Pausa Estricta en Rollover y Mantenimiento Diario de Commodities (16:45 a 18:00 NY).
2. Techo Máximo de Spread Absoluto por Materia Prima (Hard Cap).
3. Ratio Máximo Spread / Stop Loss <= 1.5% (max_risk_ratio configurable).
4. Estabilización de cotizaciones tras aperturas y noticias (requiere N muestras estables).
5. Persistencia atómica de línea base en storage/runtime/commodity_spread/.
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
ROOT = Path(__file__).resolve().parents[2] / 'storage/runtime/commodity_spread'

# Parámetros institucionales por Materia Prima
COMMODITY_SPECS = {
    'XAUUSD': {'pip': 0.10, 'max_spread': 0.45, 'descr': 'Oro Spot USD (45c max)'},
    'XAUUSDMICRO': {'pip': 0.10, 'max_spread': 0.45, 'descr': 'Oro Micro USD'},
    'MICROXAUUSD': {'pip': 0.10, 'max_spread': 0.45, 'descr': 'Oro Micro USD'},
    'XAUEUR': {'pip': 0.10, 'max_spread': 0.45, 'descr': 'Oro Spot EUR'},
    'XAUEURMICRO': {'pip': 0.10, 'max_spread': 0.45, 'descr': 'Oro Micro EUR'},
    'MICROXAUEUR': {'pip': 0.10, 'max_spread': 0.45, 'descr': 'Oro Micro EUR'},
    'XAGUSD': {'pip': 0.01, 'max_spread': 0.06, 'descr': 'Plata Spot USD (6c max)'},
    'XAGUSDMICRO': {'pip': 0.01, 'max_spread': 0.06, 'descr': 'Plata Micro USD'},
    'MICROXAGUSD': {'pip': 0.01, 'max_spread': 0.06, 'descr': 'Plata Micro USD'},
    'US OIL': {'pip': 0.01, 'max_spread': 0.08, 'descr': 'Petróleo WTI (8c max)'},
    'USOIL': {'pip': 0.01, 'max_spread': 0.08, 'descr': 'Petróleo WTI'},
    'UK BRENT OIL': {'pip': 0.01, 'max_spread': 0.09, 'descr': 'Petróleo Brent (9c max)'},
    'UKBRENTOIL': {'pip': 0.01, 'max_spread': 0.09, 'descr': 'Petróleo Brent'},
}

DEFAULT_COMMODITY_SPEC = {'pip': 0.01, 'max_spread': 0.50, 'descr': 'Commodity Genérico'}


def is_commodity_symbol(symbol: str) -> bool:
    """Identifica si un símbolo pertenece a la familia de Materias Primas (Metales y Energías)."""
    s = str(symbol or "").strip().upper()
    return any(k in s for k in ("XAU", "XAG", "OIL", "GOLD", "SILVER", "BRENT", "WTI"))


def get_commodity_spec(symbol: str) -> dict:
    norm = str(symbol).strip().upper()
    return COMMODITY_SPECS.get(norm, DEFAULT_COMMODITY_SPEC)


def is_commodity_rollover(now: datetime | None = None) -> bool:
    """Verifica si la hora actual cae en el horario de rollover diario de commodities (16:45 - 18:00 NY)."""
    now = now or datetime.now(timezone.utc)
    ny = now.astimezone(ZoneInfo('America/New_York'))
    # De domingo a viernes: 16:45 a 18:00 NY
    hour = ny.hour + ny.minute / 60.0 + ny.second / 3600.0
    return 16.75 <= hour < 18.0


class CommoditySpreadGuard:
    """Guardián de liquidez y spreads para materias primas con memoria histórica y tolerancia al riesgo."""

    def __init__(
        self,
        worker: str = "COMMODITIES",
        root: Path | str | None = None,
        minimum_samples: int = 15,
        multiplier: float = 2.0,
        max_risk_ratio: float = 0.015,
        stable_samples: int = 3,
    ):
        self.worker = str(worker)
        self.path = Path(root or ROOT) / f"{self.worker}.json"
        self.minimum_samples = int(minimum_samples)
        self.multiplier = float(multiplier)
        self.max_risk_ratio = float(os.getenv("DAEMONBLACKFX_COMMODITY_MAX_RISK_RATIO", str(max_risk_ratio)))
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
        ny = now.astimezone(ZoneInfo('America/New_York'))
        session = (ny.date() if ny.hour >= 18 else ny.date() - timedelta(days=1)).isoformat()

        item = self.state['symbols'].setdefault(symbol, {'samples': [], 'stable_count': 0})
        if item.get('session') != session:
            item.update(session=session, stable_count=0, last_stable_at=None)

        previous = item.get('observed_at')
        if previous and (now - datetime.fromisoformat(previous)).total_seconds() > 95:
            item['stable_count'] = 0

        item.update(observed_at=now.isoformat(), quote=dict(quote))

        # 1. Comprobación de Rollover
        in_rollover = is_commodity_rollover(now)
        if in_rollover:
            item['stable_count'] = 0
            item.update(
                normal=False,
                ready=False,
                reason='COMMODITY_ROLLOVER_MAINTENANCE'
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

        # 3. Reglas específicas por commodity
        spec = get_commodity_spec(symbol)
        pip = spec['pip']
        max_spread = spec['max_spread']

        # Limpieza de muestras históricas (últimos 7 días)
        cutoff_7d = (now - timedelta(days=7)).isoformat()
        samples = [x for x in item['samples'] if x['at'] >= cutoff_7d]

        median = statistics.median(x['spread'] for x in samples) if len(samples) >= self.minimum_samples else None

        # Condición de normalidad: spread <= techo absoluto Y spread <= mediana * multiplicador
        spread_ok = (spread <= max_spread)
        spike_ok = (median is None or spread <= median * self.multiplier)
        normal = bool(valid and spread_ok and spike_ok)

        spaced = previous is None or (now - datetime.fromisoformat(previous)).total_seconds() >= 10
        if not normal:
            item['stable_count'] = 0
        elif spaced:
            item['stable_count'] += 1

        # Acumular muestra si no estamos en rollover y la cotización es razonable
        if valid and spaced and not in_rollover and spread_ok and (median is None or spread <= median * self.multiplier):
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
            spread_pips=round(spread / pip, 2),
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
        """Audita si una orden puede ejecutarse según el costo de spread frente a la distancia de Stop Loss."""
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
