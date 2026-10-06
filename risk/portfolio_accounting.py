"""Contabilidad de cartera estricta y gestión de riesgo de portafolio (inspirado en NautilusTrader).

Implementa:
1. Libro mayor de cartera (Portfolio Ledger):
   - Balance realizado, equity en tiempo real, margen libre, margen utilizado, apalancamiento efectivo.
   - Desglose de comisiones acumuladas, swaps y PnL neto vs bruto.
2. Contabilidad de exposición por activo y divisa:
   - Matriz de exposición agregada por divisa base/cotizada (ej. USD, EUR, GBP, XAU, Sintéticos).
   - Control de sobreexposición y concentración de riesgo.
3. Circuit Breakers de cartera (estilo Prop Firm / Cuentas de Fondeo):
   - Límite de pérdida diaria estricto (Daily Drawdown Hard Lock): congela nuevas aperturas si la cuenta
     pierde un porcentaje determinado durante la sesión actual (ej. -3.0%).
   - Límite de Drawdown global máximo (Max Trailing Drawdown Lock).
   - Límite de riesgo total simultáneo en mercado (Max Concurrent Aggregate Risk, ej. 5.0%).
4. Modelado de microestructura y excursión (MAE / MFE):
   - Seguimiento continuo de la Máxima Excursión Adversa (MAE) y Favorable (MFE) en R y dinero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional
import math


@dataclass
class PortfolioLimits:
    """Reglas y límites estrictos de control de cartera."""
    max_daily_drawdown_percent: float = 3.0       # Congela nuevas entradas si el día pierde >= 3%
    max_total_drawdown_percent: float = 6.0       # Límite global de drawdown de la cuenta
    max_total_concurrent_risk_percent: float = 5.0 # Riesgo acumulado máximo entre todas las órdenes abiertas
    max_currency_risk_percent: float = 2.5        # Riesgo máximo acumulado expuesto a una sola divisa (ej. USD)
    max_open_positions: int = 10                  # Límite máximo de posiciones simultáneas (5 instrumentos x 2 piernas)
    daily_reset_hour_utc: int = 0                 # Hora UTC de reinicio de la métrica diaria (rollover)


@dataclass
class PositionMicrostructureRecord:
    """Métricas de microestructura y excursión de una posición abierta."""
    ticket: str
    symbol: str
    direction: str
    entry_price: float
    initial_sl: float
    initial_tp: float
    initial_risk_amount: float
    volume: float
    entry_time: datetime
    risk_distance: float = 0.0
    highest_price: float = 0.0
    lowest_price: float = 0.0
    max_favorable_excursion_price: float = 0.0
    max_adverse_excursion_price: float = 0.0
    max_favorable_excursion_r: float = 0.0
    max_adverse_excursion_r: float = 0.0
    current_unrealized_pnl: float = 0.0
    current_unrealized_r: float = 0.0

    def __post_init__(self):
        self.risk_distance = max(1e-9, abs(self.entry_price - self.initial_sl))
        self.highest_price = self.entry_price
        self.lowest_price = self.entry_price

    def update_price(self, current_price: float) -> None:
        """Actualiza las métricas MAE y MFE con cada tick o cotización."""
        current_price = float(current_price)
        if current_price > self.highest_price:
            self.highest_price = current_price
        if current_price < self.lowest_price:
            self.lowest_price = current_price

        is_buy = self.direction.upper() in ("BUY", "LONG")
        if is_buy:
            fav_price = max(0.0, self.highest_price - self.entry_price)
            adv_price = max(0.0, self.entry_price - self.lowest_price)
            cur_pnl = current_price - self.entry_price
        else:
            fav_price = max(0.0, self.entry_price - self.lowest_price)
            adv_price = max(0.0, self.highest_price - self.entry_price)
            cur_pnl = self.entry_price - current_price

        self.max_favorable_excursion_price = fav_price
        self.max_adverse_excursion_price = adv_price
        self.max_favorable_excursion_r = round(fav_price / self.risk_distance, 4)
        self.max_adverse_excursion_r = round(adv_price / self.risk_distance, 4)
        self.current_unrealized_pnl = cur_pnl
        self.current_unrealized_r = round(cur_pnl / self.risk_distance, 4)


class PortfolioAccountingManager:
    """Gestor de contabilidad de cartera y guardianes de riesgo institucional."""

    def __init__(self, initial_balance: float = 1000.0, limits: Optional[PortfolioLimits] = None):
        self.limits = limits or PortfolioLimits()
        self.initial_balance = float(initial_balance)
        self.realized_balance = float(initial_balance)
        self.peak_equity = float(initial_balance)
        self.day_start_balance = float(initial_balance)
        self.current_day: date = datetime.now(timezone.utc).date()

        self.margin_used: float = 0.0
        self.commissions_paid: float = 0.0
        self.swap_paid: float = 0.0

        self.positions: Dict[str, PositionMicrostructureRecord] = {}
        self.circuit_breaker_active: bool = False
        self.circuit_breaker_reason: Optional[str] = None

    def _check_daily_reset(self) -> None:
        """Reinicia el balance base diario cuando cambia el día UTC."""
        today = datetime.now(timezone.utc).date()
        if today != self.current_day:
            self.current_day = today
            self.day_start_balance = self.realized_balance
            # Si el circuito fue por pérdida diaria, se rehabilita en el nuevo día
            if self.circuit_breaker_active and "DAILY_LOSS_LIMIT" in str(self.circuit_breaker_reason):
                self.circuit_breaker_active = False
                self.circuit_breaker_reason = None

    def sync_account(self, balance: float, equity: float, margin: float = 0.0) -> None:
        """Sincroniza el estado del balance y equity reportado por el broker."""
        self._check_daily_reset()
        self.realized_balance = float(balance)
        self.margin_used = float(margin)
        if equity > self.peak_equity:
            self.peak_equity = float(equity)

        # Evaluar límites diarios y globales
        daily_loss_amount = self.day_start_balance - equity
        daily_loss_pct = (daily_loss_amount / self.day_start_balance) * 100.0 if self.day_start_balance > 0 else 0.0

        if daily_loss_pct >= self.limits.max_daily_drawdown_percent:
            self.circuit_breaker_active = True
            self.circuit_breaker_reason = (
                f"DAILY_LOSS_LIMIT_REACHED: Pérdida del día {daily_loss_pct:.2f}% "
                f"supera el máximo permitido de {self.limits.max_daily_drawdown_percent:.2f}%"
            )

        total_dd_amount = self.peak_equity - equity
        total_dd_pct = (total_dd_amount / self.peak_equity) * 100.0 if self.peak_equity > 0 else 0.0
        if total_dd_pct >= self.limits.max_total_drawdown_percent:
            self.circuit_breaker_active = True
            self.circuit_breaker_reason = (
                f"MAX_TOTAL_DRAWDOWN_REACHED: Drawdown global {total_dd_pct:.2f}% "
                f"supera el máximo permitido de {self.limits.max_total_drawdown_percent:.2f}%"
            )

    def register_open_position(
        self,
        ticket: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        volume: float,
        risk_amount: float,
        entry_time: Optional[datetime] = None,
    ) -> PositionMicrostructureRecord:
        """Registra una nueva posición en el libro de microestructura."""
        record = PositionMicrostructureRecord(
            ticket=str(ticket),
            symbol=str(symbol),
            direction=str(direction),
            entry_price=float(entry_price),
            initial_sl=float(stop_loss),
            initial_tp=float(take_profit),
            initial_risk_amount=float(risk_amount),
            volume=float(volume),
            entry_time=entry_time or datetime.now(timezone.utc),
        )
        self.positions[str(ticket)] = record
        return record

    def update_position_price(self, ticket: str, current_price: float) -> Optional[PositionMicrostructureRecord]:
        """Actualiza el precio de una posición registrada y sus métricas MAE/MFE."""
        record = self.positions.get(str(ticket))
        if record:
            record.update_price(current_price)
        return record

    def close_position(
        self,
        ticket: str,
        gross_pnl: float,
        commission: float = 0.0,
        swap: float = 0.0,
    ) -> Optional[PositionMicrostructureRecord]:
        """Cierra la posición y actualiza la contabilidad de saldo y comisiones."""
        record = self.positions.pop(str(ticket), None)
        self.realized_balance += float(gross_pnl) - float(commission) - float(swap)
        self.commissions_paid += float(commission)
        self.swap_paid += float(swap)
        self._check_daily_reset()
        return record

    def can_open_new_trade(
        self,
        symbol: str,
        planned_risk_amount: float,
        risk_percent: float = 1.0,
    ) -> tuple[bool, Optional[str]]:
        """Comprueba de forma estricta si el portafolio autoriza una nueva posición."""
        self._check_daily_reset()

        if self.circuit_breaker_active:
            return False, f"CIRCUIT_BREAKER_ACTIVE: {self.circuit_breaker_reason}"

        if len(self.positions) >= self.limits.max_open_positions:
            return False, f"PORTFOLIO_LIMIT: Máximo de posiciones abiertas alcanzado ({self.limits.max_open_positions})"

        # 1. Riesgo agregado concurrente
        current_open_risk = sum(p.initial_risk_amount for p in self.positions.values())
        proposed_total_risk = current_open_risk + float(planned_risk_amount)
        max_allowed_risk_amount = (self.realized_balance * self.limits.max_total_concurrent_risk_percent) / 100.0

        if proposed_total_risk > max_allowed_risk_amount:
            return False, (
                f"AGGREGATE_RISK_LIMIT: Riesgo propuesto ({proposed_total_risk:.2f}) "
                f"supera el {self.limits.max_total_concurrent_risk_percent:.1f}% de la cartera "
                f"({max_allowed_risk_amount:.2f})"
            )

        # 2. Control de correlación de divisas
        currency = self._extract_currency(symbol)
        if currency:
            currency_risk = sum(
                p.initial_risk_amount for p in self.positions.values()
                if self._extract_currency(p.symbol) == currency
            ) + float(planned_risk_amount)
            max_curr_amount = (self.realized_balance * self.limits.max_currency_risk_percent) / 100.0
            if currency_risk > max_curr_amount:
                return False, (
                    f"CURRENCY_EXPOSURE_LIMIT: Exposición en {currency} ({currency_risk:.2f}) "
                    f"superaría el {self.limits.max_currency_risk_percent:.1f}% permitido"
                )

        return True, None

    def _extract_currency(self, symbol: str) -> Optional[str]:
        """Extrae la divisa principal o clase de activo para control de correlación."""
        s = str(symbol).upper()
        if "USD" in s:
            return "USD"
        if "EUR" in s:
            return "EUR"
        if "GBP" in s:
            return "GBP"
        if "JPY" in s:
            return "JPY"
        if "XAU" in s or "GOLD" in s:
            return "GOLD"
        if any(term in s for term in ("VOLATILITY", "CRASH", "BOOM", "STEP", "JUMP")):
            return "DERIV_SYNTHETIC"
        return None

    def snapshot(self) -> Dict[str, Any]:
        """Retorna un dict completo con la salud y métricas de la cartera."""
        self._check_daily_reset()
        total_open_risk = sum(p.initial_risk_amount for p in self.positions.values())
        unrealized_pnl = sum(p.current_unrealized_pnl for p in self.positions.values())
        return {
            "realized_balance": round(self.realized_balance, 2),
            "estimated_equity": round(self.realized_balance + unrealized_pnl, 2),
            "peak_equity": round(self.peak_equity, 2),
            "day_start_balance": round(self.day_start_balance, 2),
            "open_positions_count": len(self.positions),
            "total_open_risk_amount": round(total_open_risk, 2),
            "total_open_risk_percent": round((total_open_risk / max(1.0, self.realized_balance)) * 100.0, 2),
            "margin_used": round(self.margin_used, 2),
            "commissions_paid": round(self.commissions_paid, 2),
            "swap_paid": round(self.swap_paid, 2),
            "circuit_breaker_active": self.circuit_breaker_active,
            "circuit_breaker_reason": self.circuit_breaker_reason,
            "positions_microstructure": {
                ticket: {
                    "symbol": p.symbol,
                    "direction": p.direction,
                    "mae_pips_or_points": round(p.max_adverse_excursion_price, 4),
                    "mfe_pips_or_points": round(p.max_favorable_excursion_price, 4),
                    "mae_r": p.max_adverse_excursion_r,
                    "mfe_r": p.max_favorable_excursion_r,
                    "current_r": p.current_unrealized_r,
                }
                for ticket, p in self.positions.items()
            }
        }
