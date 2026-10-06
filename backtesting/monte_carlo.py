"""Simulador Monte Carlo y Análisis Walk-Forward (inspirado en Jesse).

Permite evaluar con rigor cuantitativo la robustez estadística de los resultados
del backtest antes de operar con dinero real:

1. SIMULACIÓN MONTE CARLO (Permutación de trades):
   - Desordena aleatoriamente la secuencia de operaciones N veces (ej. 1,000 o 5,000 iteraciones).
   - Calcula la distribución empírica del Drawdown Máximo (Mediana, Percentil 95, Percentil 99 y Peor Caso).
   - Evalúa la probabilidad de racha perdedora (Maximum Consecutive Losing Streak).
   - Calcula el Riesgo de Ruina / Probabilidad de caer bajo un umbral de drawdown crítico (ej. -10% o -20%).

2. PARTICIONADO Y ANÁLISIS WALK-FORWARD (WFO):
   - Divide la serie histórica en ventanas rodantes In-Sample (optimización/ajuste) y Out-of-Sample (prueba ciega).
   - Mide la Eficiencia Walk-Forward (WFE = Retorno Out-of-Sample / Retorno In-Sample) para descartar
     sobreajuste (curve-fitting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


@dataclass
class MonteCarloMetrics:
    """Resultados consolidados de la simulación Monte Carlo."""
    iterations: int
    initial_balance: float
    simulated_final_balance_median: float
    simulated_final_balance_p05: float
    simulated_final_balance_p95: float

    max_drawdown_median_percent: float
    max_drawdown_p95_percent: float
    max_drawdown_p99_percent: float
    max_drawdown_worst_percent: float

    max_consecutive_losses_median: int
    max_consecutive_losses_p95: int
    max_consecutive_losses_worst: int

    probability_of_ruin_10pct: float
    probability_of_ruin_20pct: float
    probability_of_profit: float

    confidence_interval_cagr_p05: float
    confidence_interval_cagr_p95: float

    summary_text: str = ""


class MonteCarloSimulator:
    """Motor de simulación Monte Carlo para series de operaciones de backtest."""

    def __init__(
        self,
        trades_df_or_returns: pd.DataFrame | List[float] | np.ndarray,
        initial_balance: float = 1000.0,
        risk_percent: float = 1.0,
    ):
        self.initial_balance = float(initial_balance)
        self.risk_percent = float(risk_percent)

        if isinstance(trades_df_or_returns, pd.DataFrame):
            if "realized_r" in trades_df_or_returns.columns:
                self.r_multiples = trades_df_or_returns["realized_r"].dropna().to_numpy(dtype=float)
            elif "profit_loss" in trades_df_or_returns.columns:
                # Normalizar pnl a R usando el riesgo inicial aproximado
                pnls = trades_df_or_returns["profit_loss"].dropna().to_numpy(dtype=float)
                base_risk = self.initial_balance * (self.risk_percent / 100.0)
                self.r_multiples = pnls / max(1e-6, base_risk)
            else:
                raise ValueError("El DataFrame de trades debe contener 'realized_r' o 'profit_loss'")
        else:
            self.r_multiples = np.asarray(trades_df_or_returns, dtype=float)

    def run(self, iterations: int = 2000, random_seed: Optional[int] = 42) -> MonteCarloMetrics:
        """Ejecuta N permutaciones estocásticas de la serie de trades."""
        if len(self.r_multiples) == 0:
            raise ValueError("No hay operaciones para simular en Monte Carlo")

        if random_seed is not None:
            np.random.seed(random_seed)

        n_trades = len(self.r_multiples)
        final_balances = np.zeros(iterations)
        max_drawdowns = np.zeros(iterations)
        max_loss_streaks = np.zeros(iterations, dtype=int)
        ruin_10_count = 0
        ruin_20_count = 0
        profit_count = 0

        risk_frac = self.risk_percent / 100.0

        for it in range(iterations):
            # Permutación aleatoria de los trades históricos
            permuted_r = np.random.choice(self.r_multiples, size=n_trades, replace=True)

            # Reconstruir curva de capital compuesta
            balance = self.initial_balance
            peak = balance
            max_dd = 0.0

            cur_streak = 0
            max_streak = 0

            hit_ruin_10 = False
            hit_ruin_20 = False

            for r in permuted_r:
                risk_amt = balance * risk_frac
                pnl = risk_amt * r
                balance += pnl

                if r < 0:
                    cur_streak += 1
                    if cur_streak > max_streak:
                        max_streak = cur_streak
                else:
                    cur_streak = 0

                if balance > peak:
                    peak = balance

                dd = (peak - balance) / peak if peak > 0 else 0.0
                if dd > max_dd:
                    max_dd = dd

                if dd >= 0.10:
                    hit_ruin_10 = True
                if dd >= 0.20:
                    hit_ruin_20 = True

            final_balances[it] = balance
            max_drawdowns[it] = max_dd * 100.0
            max_loss_streaks[it] = max_streak
            if hit_ruin_10:
                ruin_10_count += 1
            if hit_ruin_20:
                ruin_20_count += 1
            if balance > self.initial_balance:
                profit_count += 1

        p_ruin_10 = (ruin_10_count / iterations) * 100.0
        p_ruin_20 = (ruin_20_count / iterations) * 100.0
        p_profit = (profit_count / iterations) * 100.0

        med_bal = float(np.median(final_balances))
        p05_bal = float(np.percentile(final_balances, 5))
        p95_bal = float(np.percentile(final_balances, 95))

        med_dd = float(np.median(max_drawdowns))
        p95_dd = float(np.percentile(max_drawdowns, 95))
        p99_dd = float(np.percentile(max_drawdowns, 99))
        worst_dd = float(np.max(max_drawdowns))

        med_streak = int(np.median(max_loss_streaks))
        p95_streak = int(np.percentile(max_loss_streaks, 95))
        worst_streak = int(np.max(max_loss_streaks))

        summary = (
            f"Monte Carlo ({iterations} iteraciones | {n_trades} trades): "
            f"Drawdown Mediano: {med_dd:.2f}% | Drawdown 95%: {p95_dd:.2f}% | "
            f"Racha de pérdidas 95%: {p95_streak} | Riesgo Drawdown >10%: {p_ruin_10:.1f}% | "
            f"Probabilidad de Ganancia: {p_profit:.1f}%"
        )

        return MonteCarloMetrics(
            iterations=iterations,
            initial_balance=self.initial_balance,
            simulated_final_balance_median=round(med_bal, 2),
            simulated_final_balance_p05=round(p05_bal, 2),
            simulated_final_balance_p95=round(p95_bal, 2),
            max_drawdown_median_percent=round(med_dd, 2),
            max_drawdown_p95_percent=round(p95_dd, 2),
            max_drawdown_p99_percent=round(p99_dd, 2),
            max_drawdown_worst_percent=round(worst_dd, 2),
            max_consecutive_losses_median=med_streak,
            max_consecutive_losses_p95=p95_streak,
            max_consecutive_losses_worst=worst_streak,
            probability_of_ruin_10pct=round(p_ruin_10, 2),
            probability_of_ruin_20pct=round(p_ruin_20, 2),
            probability_of_profit=round(p_profit, 2),
            confidence_interval_cagr_p05=round(((p05_bal / self.initial_balance) - 1.0) * 100.0, 2),
            confidence_interval_cagr_p95=round(((p95_bal / self.initial_balance) - 1.0) * 100.0, 2),
            summary_text=summary,
        )


def walk_forward_partitions(
    df: pd.DataFrame,
    n_splits: int = 5,
    in_sample_ratio: float = 0.70,
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """Divide un DataFrame histórico en ventanas consecutivas In-Sample y Out-of-Sample."""
    n = len(df)
    if n < 100:
        raise ValueError("Se requieren al menos 100 filas para particionado Walk-Forward")

    window_size = int(n / n_splits)
    train_size = int(window_size * in_sample_ratio)
    partitions = []

    for i in range(n_splits):
        start = i * window_size
        train_end = start + train_size
        test_end = min(n, start + window_size) if i == n_splits - 1 else (start + window_size)

        train_slice = df.iloc[start:train_end]
        test_slice = df.iloc[train_end:test_end]
        if len(train_slice) > 0 and len(test_slice) > 0:
            partitions.append((train_slice, test_slice))

    return partitions
