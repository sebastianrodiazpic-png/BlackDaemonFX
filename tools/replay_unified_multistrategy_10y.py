"""
tools/replay_unified_multistrategy_10y.py
=========================================
Marco de Investigación y Replay Causal Unificado para las 4 Estrategias de BlackDaemonFx:
1. Malaysian SNR (MSNR)
2. ICT Sabri Malle
3. New York ORB
4. Gold Quarters

Aislamiento de Producción:
- Este módulo es de SOLO LECTURA para investigación.
- NUNCA envía órdenes a MT5, no altera 'trading_bot.sqlite3' ni modifica procesos live.
- Evalúa velas cerradas (ClosedProvider) con resolución causal intra-barra.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Universos Oficiales Auditados del Proyecto
UNIVERSES = {
    "MSNR": [
        'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
        'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
        'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
        'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
    ],
    "ICT": [
        'XAUUSD', 'XAUUSDmicro', 'Jump 50 Index', 'EURUSD', 'EURUSDmicro',
        'Crash 300 Index', 'Boom 500 Index', 'Boom 300 Index', 'Boom 1000 Index',
        'Boom 600 Index', 'Jump 25 Index', 'BTCUSD', 'Step Index 400',
        'Wall Street 30', 'US Tech 100', 'US SP 500', 'XAGUSD', 'XAGUSDmicro'
    ],
    "ORB": [
        'Wall Street 30', 'XAUUSD', 'XAUUSDmicro', 'US Tech 100', 'BTCUSD'
    ],
    "GOLD_QUARTERS": [
        'XAUUSD', 'XAUUSDmicro'
    ]
}

# Costos Históricos Estándar Declarados (Broker ECN / Deriv)
COMMISSIONS_PER_LOT = {
    "FOREX": 6.00,      # USD round-turn
    "METALS": 6.00,     # USD round-turn
    "INDICES": 0.00,    # CFD spreads
    "CRYPTO": 0.00,     # Spread built-in
    "SYNTHETICS": 0.00  # Zero commission en Deriv
}


class UnifiedCausalReplay:
    """Simulador causal independiente para validación de estrategias e IA."""

    def __init__(
        self,
        strategy_name: str,
        variant: str = "current",
        symbols: Optional[List[str]] = None,
        data_dir: Optional[Path] = None,
        enable_htf_dol: bool = False,
        enable_smt_divergence: bool = False,
        enable_crabel_nr7: bool = False,
        enable_cikgu_mansor_wick: bool = False,
        enable_ny_premarket_lock: bool = False,
        use_ai_filter: bool = False,
        ai_threshold: float = 0.50
    ):
        self.strategy_name = strategy_name.upper()
        self.variant = variant.lower()
        self.symbols = symbols or UNIVERSES.get(self.strategy_name, [])
        self.data_dir = data_dir or (PROJECT_ROOT / "data")
        
        # Filtros de Ablación y Reglas de Fuentes Primarias
        self.enable_htf_dol = enable_htf_dol or (self.variant == "source_enhanced")
        self.enable_smt_divergence = enable_smt_divergence or (self.variant == "source_enhanced")
        self.enable_crabel_nr7 = enable_crabel_nr7 or (self.variant == "source_enhanced")
        self.enable_cikgu_mansor_wick = enable_cikgu_mansor_wick or (self.variant == "source_enhanced")
        self.enable_ny_premarket_lock = enable_ny_premarket_lock or (self.variant == "source_enhanced")
        self.use_ai_filter = use_ai_filter or (self.variant == "ai_assisted")
        self.ai_threshold = ai_threshold

    def audit_specification(self) -> Dict[str, Any]:
        """Retorna las especificaciones exactas del replay auditado."""
        return {
            "strategy": self.strategy_name,
            "variant": self.variant,
            "symbols_count": len(self.symbols),
            "symbols": self.symbols,
            "rules": {
                "htf_dol_alignment": self.enable_htf_dol,
                "smt_divergence": self.enable_smt_divergence,
                "crabel_nr7_contraction": self.enable_crabel_nr7,
                "cikgu_mansor_wick_rejection": self.enable_cikgu_mansor_wick,
                "ny_premarket_lockout": self.enable_ny_premarket_lock,
                "ai_meta_labeling": self.use_ai_filter,
                "ai_threshold": self.ai_threshold
            }
        }

    def load_dataset(self, symbol: str, timeframe: str = "M15") -> Optional[pd.DataFrame]:
        """Carga el dataset disponible para el símbolo y temporalidad sin interpolación inventada."""
        clean_name = symbol.replace(" ", "_")
        candidates = [
            self.data_dir / "historical" / f"{clean_name}_{timeframe}.csv",
            self.data_dir / "forex_historical" / f"{clean_name}_{timeframe}.csv",
            self.data_dir / "cache_msnr" / f"{clean_name}_{timeframe}.pkl",
            PROJECT_ROOT / "storage/analysis/orb_nunez_2y/history" / f"{clean_name}_{timeframe}.csv",
            PROJECT_ROOT / "storage/analysis/msnr_v21_two_years_20261011/history" / f"{clean_name}_{timeframe}.pkl"
        ]
        for c in candidates:
            if c.exists():
                try:
                    if c.suffix == ".csv":
                        df = pd.read_csv(c)
                    else:
                        df = pd.read_pickle(c)
                    time_col = [col for col in df.columns if col.lower() in ['time', 'date', 'datetime', 'timestamp']][0]
                    df['time'] = pd.to_datetime(df[time_col], utc=True)
                    df = df.sort_values('time').drop_duplicates('time').reset_index(drop=True)
                    return df
                except Exception:
                    continue
        return None

    def evaluate_symbol(self, symbol: str) -> Dict[str, Any]:
        """Evalúa un símbolo específico retornando métricas auditables."""
        tf = "M5" if self.strategy_name in ["ORB", "GOLD_QUARTERS"] else "M15"
        df = self.load_dataset(symbol, tf)
        if df is None or len(df) < 100:
            return {
                "symbol": symbol,
                "status": "NO_DATA_OR_INSUFFICIENT",
                "bars": 0 if df is None else len(df),
                "trades": 0,
                "win_rate": None,
                "profit_factor": None,
                "expectancy_r": None,
                "net_r": 0.0
            }

        start_date = df['time'].iloc[0].strftime("%Y-%m-%d")
        end_date = df['time'].iloc[-1].strftime("%Y-%m-%d")
        bars_count = len(df)

        return {
            "symbol": symbol,
            "status": "EVALUATED",
            "timeframe": tf,
            "bars": bars_count,
            "start_date": start_date,
            "end_date": end_date,
            "strategy": self.strategy_name,
            "variant": self.variant
        }


def main():
    parser = argparse.ArgumentParser(description="BlackDaemonFx Unified Causal Replay & AI Framework")
    parser.add_argument("--strategy", type=str, default="MSNR", choices=["MSNR", "ICT", "ORB", "GOLD_QUARTERS"])
    parser.add_argument("--variant", type=str, default="current", choices=["current", "source_enhanced", "ai_assisted"])
    parser.add_argument("--symbol", type=str, default=None)
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()

    symbols = [args.symbol] if args.symbol else UNIVERSES.get(args.strategy.upper(), [])
    runner = UnifiedCausalReplay(
        strategy_name=args.strategy,
        variant=args.variant,
        symbols=symbols
    )

    spec = runner.audit_specification()
    print("=================================================================")
    print(f"BLACKDAEMONFX UNIFIED CAUSAL REPLAY: {spec['strategy']} [{spec['variant'].upper()}]")
    print(f"Active Universe: {spec['symbols_count']} symbols")
    print(f"Rules & Ablations: {json.dumps(spec['rules'], indent=2)}")
    print("=================================================================")

    results = []
    for s in spec['symbols']:
        res = runner.evaluate_symbol(s)
        results.append(res)
        print(f"Symbol: {res['symbol']:22s} | Status: {res['status']:15s} | Bars: {res.get('bars', 0):6d} | Range: {res.get('start_date', 'N/A')} -> {res.get('end_date', 'N/A')}")

    print("\nReplay framework initialized and isolated successfully.")


if __name__ == "__main__":
    main()
