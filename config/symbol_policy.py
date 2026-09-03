from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolDirectionPolicy:
    symbol: str
    category: str
    allowed_direction: str | None
    reason: str


def classify_synthetic_symbol(symbol: str) -> str:
    name = str(symbol or '').strip().lower()
    if 'boom' in name and 'crash' not in name:
        return 'boom'
    if 'crash' in name and 'boom' not in name:
        return 'crash'
    return 'other'


def get_symbol_direction_policy(symbol: str) -> SymbolDirectionPolicy:
    category = classify_synthetic_symbol(symbol)
    if category == 'boom':
        return SymbolDirectionPolicy(
            symbol=str(symbol), category=category, allowed_direction='BUY',
            reason='BOOM_BUY_ONLY',
        )
    if category == 'crash':
        return SymbolDirectionPolicy(
            symbol=str(symbol), category=category, allowed_direction='SELL',
            reason='CRASH_SELL_ONLY',
        )
    return SymbolDirectionPolicy(
        symbol=str(symbol), category=category, allowed_direction=None,
        reason='NO_DIRECTION_RESTRICTION',
    )


def normalize_direction(direction: str | None) -> str | None:
    value = str(direction or '').upper()
    aliases = {'LONG': 'BUY', 'SHORT': 'SELL'}
    value = aliases.get(value, value)
    return value if value in {'BUY', 'SELL'} else None


def is_direction_allowed(symbol: str, direction: str | None) -> bool:
    policy = get_symbol_direction_policy(symbol)
    normalized = normalize_direction(direction)
    return normalized is not None and (
        policy.allowed_direction is None or normalized == policy.allowed_direction
    )


def direction_policy_diagnostics(symbol: str, direction: str | None = None) -> dict:
    policy = get_symbol_direction_policy(symbol)
    normalized = normalize_direction(direction)
    return {
        'symbol': policy.symbol,
        'category': policy.category,
        'allowed_direction': policy.allowed_direction,
        'requested_direction': normalized,
        'policy_reason': policy.reason,
        'allowed': None if normalized is None else is_direction_allowed(symbol, normalized),
    }
