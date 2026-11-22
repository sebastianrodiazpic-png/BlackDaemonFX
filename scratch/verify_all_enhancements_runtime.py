import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategy.confluence.tripartite_confluence_gate import (
    TripartiteConfluenceGate,
    TripartiteConfluenceConfig,
    canonical_symbol,
    normalize_strategy_key,
)
from strategy.confluence.entry_decision import (
    build_entry_decision_record,
    aggregate_decision_events,
    aggregate_trade_decisions,
    normalize_strategy_name,
)
from dashboard.realtime_dashboard import _build_confluence_matrix

print("=" * 80)
print("1. VALIDACIÓN CONFLUENCIA TRIPARTITA (CASOS ESQUINA Y NORMALIZACIÓN)")
print("=" * 80)
gate = TripartiteConfluenceGate()

# Casos de Poda Estricta
cases_pruned = [
    ("AUDCAD", "ICT", "SELL"),
    ("AUDCADmicro", "ICT", "SELL"),
    ("microAUDCAD", "ICT", "SELL"),
    ("AUDCAD", "ICT_SABRI_MALLE", "BUY"),
    ("AUDCADmicro", "ICT_SABRI_MALLE", "BUY"),
    ("Crash 300 Index", "ORB", "BUY"),
]
for sym, strat, dir_ in cases_pruned:
    dec = gate.evaluate_confluence(symbol=sym, strategy_name=strat, direction=dir_, signal={"sl": 1, "tp": 2})
    assert dec.allowed is False, f"Fallo: {sym} debió ser bloqueado"
    assert dec.action == "VETO_STRICT_PRUNING", f"Fallo acción {sym}: {dec.action}"
    print(f"  [OK] {sym} ({strat}) -> {dec.action} | {dec.reason[:70]}...")

# Casos de Activos Rehabilitados
cases_rehab = [
    ("EURUSD", "ICT"),
    ("EURUSDmicro", "ICT"),
    ("microEURUSD", "ICT"),
    ("USDJPY", "ICT_SABRI_MALLE"),
    ("USDJPYmicro", "ICT_SABRI_MALLE"),
    ("Jump 100 Index", "ICT"),
    ("Crash 1000 Index", "ICT"),
]
for sym, strat in cases_rehab:
    dec = gate.evaluate_confluence(symbol=sym, strategy_name=strat, direction="BUY", signal={"sl": 1, "tp": 2})
    assert dec.is_rehabilitated_asset is True, f"Fallo rehab: {sym} debió ser marcado como rehabilitado"
    print(f"  [OK] {sym} ({strat}) -> is_rehab={dec.is_rehabilitated_asset}")

# Casos de variantes de SL y TP
sl_tp_variants = [
    {"sl_price": 100.0, "tp_price": 200.0},
    {"stop_price": 100.0, "take_profit_price": 200.0},
    {"stop_loss_price": 100.0, "planned_rr": 2.0},
    {"stop": 100.0, "tp1_price": 150.0},
    {"sl": 100.0, "runner_rr": 3.0},
]
for v in sl_tp_variants:
    dec = gate.evaluate_confluence(symbol="Step Index", strategy_name="ICT", direction="BUY", signal=v)
    assert dec.strategy_pillar_ok is True, f"Fallo pilar estrategia con {v}"
    assert dec.action != "VETO_STRATEGY_PILLAR", f"Veto inesperado con {v}"
    print(f"  [OK] SL/TP keys {list(v.keys())} -> Strategy Pillar OK")

# Escudo Anti-Spike Crash / Boom
dec_crash_buy = gate.evaluate_confluence(symbol="Crash 500 Index", strategy_name="ICT", direction="BUY", signal={"sl": 1, "tp": 2}, is_spike_danger=True)
assert dec_crash_buy.allowed is False and dec_crash_buy.action == "VETO_HUMAN_CRITERIA_ANTI_SPIKE"
print(f"  [OK] Crash 500 BUY con riesgo de spike -> {dec_crash_buy.action}")

dec_boom_sell = gate.evaluate_confluence(symbol="Boom 1000 Index", strategy_name="ICT", direction="SELL", signal={"sl": 1, "tp": 2}, is_spike_danger=True)
assert dec_boom_sell.allowed is False and dec_boom_sell.action == "VETO_HUMAN_CRITERIA_ANTI_SPIKE"
print(f"  [OK] Boom 1000 SELL con riesgo de spike -> {dec_boom_sell.action}")

print("\n" + "=" * 80)
print("2. VALIDACIÓN RESILIENCIA CONCURRENTE SQLITE (REINTENTOS DEFENSIVOS)")
print("=" * 80)
from database.repository import TradingRepository
import sqlite3

class MockSessionWithTransientLock:
    attempts = 0

    def __enter__(self):
        MockSessionWithTransientLock.attempts += 1
        if MockSessionWithTransientLock.attempts < 3:
            raise sqlite3.OperationalError("database is locked")
        # En el tercer intento tiene éxito
        mock_sess = MagicMock()
        mock_row = MagicMock()
        mock_row.id = 999
        mock_sess.execute.return_value.scalar_one_or_none.return_value = mock_row
        return mock_sess

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Instanciamos repo sin tocar el filesystem real
repo = TradingRepository.__new__(TradingRepository)
repo.Session = MockSessionWithTransientLock
repo._dt = lambda x: None
repo._float_or_none = lambda x: x
repo._json_or_none = lambda x: x

res_id = repo.upsert_worker_runtime_state(
    bot_profile="VOLATILITY_2",
    daemon_magic=26082402,
    status="SCANNING",
    current_symbol="Volatility 75 Index",
)
assert res_id == 999, f"Fallo de reintento: esperaba 999, obtuve {res_id}"
print("  [OK] upsert_worker_runtime_state: 2 fallos de 'database is locked' absorbidos y éxito en 3er intento.")

print("\n" + "=" * 80)
print("3. VALIDACIÓN MATRIZ CENTINELA Y ANÁLISIS RECIENTES")
print("=" * 80)
state_matrix = {
    "worker_candidates": {
        "FOREX_1": {"symbol": "NZDUSD", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "FOREX_2": {"symbol": "AUDUSD", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "FOREX_3": {"symbol": "EURUSD", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "FOREX_4": {"symbol": "USDJPY", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "FOREX_5": {"symbol": "GBPUSD", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "INDICESB_SNR": {"symbol": "US Tech 100", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "STEP": {"symbol": "Step Index", "action": "WAITING_ICT", "reason": "OUTSIDE_KILLZONE"},
        "ORB": {"symbol": "Wall Street 30", "action": "ORB_SWEEP_CONFIRMED", "reason": "NY_OPEN"},
    },
    "recent": [],
}
matrix = _build_confluence_matrix(state_matrix)
print(f"Total activos en Matriz Centinela: {len(matrix)}")
for m in matrix:
    print(f"  Symbol: {m['symbol']:<16} | Strat: {m['strategy']:<15} | Key: {m['strategy_key']:<15} | Badge: {m.get('strat_badge')}")
    if m['symbol'] in ["NZDUSD", "AUDUSD", "EURUSD", "USDJPY", "GBPUSD", "US Tech 100", "Step Index"]:
        assert m['strategy_key'] == "MULTISTRATEGY"
        assert m['strategy'] == "MultiStrategia"
    elif m['symbol'] == "Wall Street 30":
        assert m['strategy_key'] == "ORB"

print("\n" + "=" * 80)
print("4. VALIDACIÓN DE REPORTE Y AGREGACIONES EN /decisions")
print("=" * 80)
events_test = [
    {"event_type": "HUMAN_CRITERIA_EVALUATED", "action": "HUMAN_CRITERIA_PASSED", "instrument": "EURUSD", "payload": {"strategy_key": "ICT_SABRI_MALLE"}},
    {"event_type": "HUMAN_CRITERIA_EVALUATED", "action": "HUMAN_CRITERIA_PASSED", "instrument": "GBPUSD", "payload": {"strategy_key": "ICT"}},
    {"event_type": "TRIPARTITE_CONFLUENCE_EVALUATED", "action": "APPROVED", "instrument": "EURUSD", "payload": {"strategy_key": "ICT_SABRI_MALLE"}},
    {"event_type": "TRIPARTITE_CONFLUENCE_EVALUATED", "action": "APPROVED", "instrument": "Step Index", "payload": {"strategy_key": "MALAYSIAN_SNR"}},
]
trades_test = [
    {"id": 1, "instrument": "EURUSD", "details": {"metadata": {"entry_decision": {"strategy_key": "ICT_SABRI_MALLE"}}}, "status": "CLOSED", "result": "WIN", "realized_rr": 1.5},
    {"id": 2, "instrument": "GBPUSD", "details": {"metadata": {"entry_decision": {"strategy_key": "ICT"}}}, "status": "CLOSED", "result": "WIN", "realized_rr": 2.0},
    {"id": 3, "instrument": "Step Index", "details": {"metadata": {"entry_decision": {"strategy_key": "MALAYSIAN_SNR"}}}, "status": "CLOSED", "result": "LOSS", "realized_rr": -1.0},
]
agg_ev = aggregate_decision_events(events_test)
agg_tr = aggregate_trade_decisions(trades_test)

print("Estrategias agregadas en eventos:", list(agg_ev["by_strategy"].keys()))
assert "ICT" in agg_ev["by_strategy"]
assert agg_ev["by_strategy"]["ICT"]["CH:HUMAN_CRITERIA_PASSED"] == 2
assert agg_ev["by_strategy"]["ICT"]["TRI:APPROVED"] == 1

print("Estrategias agregadas en trades:", list(agg_tr["by_strategy"].keys()))
assert "ICT" in agg_tr["by_strategy"]
ict_stats = agg_tr["by_strategy"]["ICT"]
assert ict_stats["trades"] == 2
assert ict_stats["wins"] == 2
assert ict_stats["win_rate"] == 100.0
assert ict_stats["r_total"] == 3.5
print(f"  [OK] Métricas consolidadas ICT: {ict_stats['trades']} ops, {ict_stats['wins']} wins, WR {ict_stats['win_rate']}%, R={ict_stats['r_total']}")

print("\n" + "=" * 80)
print("¡TODAS LAS PRUEBAS DE VALIDACIÓN TÉCNICA PASARON AL 100%!")
print("=" * 80)
