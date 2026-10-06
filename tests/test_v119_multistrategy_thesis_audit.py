from datetime import datetime, timezone
import pytest

from dashboard.realtime_dashboard import RealtimeDashboardService


class MockRepo:
    def __init__(self, trades, visuals=None, markets=None):
        self._trades = trades
        self._visuals = visuals or {}
        self._markets = markets or {}

    def open_trades(self, source=None):
        return self._trades

    def trade_visual_audits(self, source=None):
        return list(self._visuals.values())

    def latest_symbol_process_result(self, symbol, source=None):
        return {
            "symbol": symbol,
            "action": "BLOCKED_ACTIVE_TRADE",
            "status": "BLOCKED_ACTIVE_TRADE",
            "reason": f"Posicion activa: esperando cierre TP/SL/BE. Simbolo {symbol}; tickets [4745944409]",
        }

    def trade_audit_snapshots(self, trade_id):
        return []

    def get_runtime_state(self, key):
        return None

    def set_runtime_state(self, key, value):
        pass


def test_malaysian_snr_thesis_at_entry_and_live_tracking():
    trade = {
        "id": 991,
        "instrument": "Step Index 500",
        "direction": "SELL",
        "entry_price": 8200.50,
        "stop_loss": 8225.00,
        "take_profit": 8150.00,
        "planned_rr": 2.0,
        "entry_time": "2026-10-04T02:00:00+00:00",
        "broker_position_ticket": "4745944409",
        "strategy_name": "MALAYSIAN_SNR",
        "bot_profile": "MALAYSIAN_SNR",
        "details": {
            "metadata": {
                "strategy_name": "MALAYSIAN_SNR",
                "scenario": "ESC_1_CONTINUATION",
                "ref_level": 8220.00,
                "break_level": 8205.50,
                "momentum_adx": 28.5,
                "body_ratio": 0.68,
                "runner_target_name": "TP3",
                "runner_rr": 3.0,
                "managed_by_daemon": True,
            }
        },
    }

    # Trade visual con market en profit (+1.45R) pero con gatekeeper block persistido
    visual = {
        "trade_id": 991,
        "entry_context": {},
        "latest_market": {
            "current_price": 8164.00,
            "current_rr": 1.45,
            "current_strategy_view": {
                "action": "BLOCKED_ACTIVE_TRADE",
                "status": "BLOCKED_ACTIVE_TRADE",
                "reason": "Posicion activa: esperando cierre TP/SL/BE. Simbolo Step Index 500; tickets [4745944409]",
            },
        },
    }

    repo = MockRepo([trade], visuals={"991": visual})
    dash = RealtimeDashboardService(repository=repo)
    snap = dash.snapshot()

    assert len(snap["open_positions"]) == 1
    pos = snap["open_positions"][0]

    # 1. Tesis al abrir (Entry thesis)
    entry_view = pos["entry_strategy_view"]
    assert entry_view["strategy_name"] == "MALAYSIAN_SNR"
    assert entry_view["scenario"] == "ESC_1_CONTINUATION"
    assert entry_view["break_level"] == 8205.50
    assert entry_view["ref_level"] == 8220.00
    assert entry_view["momentum_adx"] == 28.5
    assert entry_view["body_ratio"] == 0.68
    assert entry_view["runner_target_name"] == "TP3"
    assert entry_view["runner_rr"] == 3.0
    assert entry_view["score"] >= 85.0
    assert "MALAYSIAN SNR" in entry_view["decision"]
    assert len(entry_view["passed"]) >= 4
    assert any("Ruptura de Nivel H1" in p for p in entry_view["passed"])
    assert any("Retest M15 Confirmado" in p for p in entry_view["passed"])
    assert any("ADX 28.5" in p for p in entry_view["passed"])

    # 2. Sincronización en la fila de posición abierta del dashboard
    assert pos["quality_score"] == 90.0
    assert pos["confirmation_percentage"] == 100.0
    assert pos["duration_str"] != "—"

    # 3. Lo que ve ahora (Live thesis tracking)
    latest_view = pos["latest_strategy_view"]
    assert latest_view["strategy_name"] == "MALAYSIAN_SNR"
    assert "BLOCKED_ACTIVE_TRADE" not in latest_view["decision"]
    assert "TESIS VIGENTE" in latest_view["decision"]
    assert "+1.45R" in latest_view["decision"]
    assert len(latest_view["passed"]) >= 3
    assert any("Estructura de mercado" in p for p in latest_view["passed"])
    assert any("Daemon de Supervisión" in p for p in latest_view["passed"])
    assert any("TP1 superado" in p for p in latest_view["passed"])
    assert "Monitoreo continuo en vivo" in latest_view["reason"]


def test_orb_and_gold_quarters_theses_enrichment():
    orb_trade = {
        "id": 992,
        "instrument": "US Tech 100",
        "direction": "BUY",
        "entry_price": 20100.0,
        "stop_loss": 20050.0,
        "take_profit": 20250.0,
        "planned_rr": 3.0,
        "entry_time": "2026-10-04T13:45:00+00:00",
        "strategy_name": "ORB_NEW_YORK",
        "bot_profile": "ORB",
        "details": {
            "metadata": {
                "strategy_name": "ORB_NEW_YORK",
                "opening_range_high": 20090.0,
                "opening_range_low": 20020.0,
                "opening_range_midpoint": 20055.0,
                "session_vwap": 20060.0,
                "managed_by_daemon": True,
            }
        },
    }

    gold_trade = {
        "id": 993,
        "instrument": "XAUUSD",
        "direction": "BUY",
        "entry_price": 2650.0,
        "stop_loss": 2640.0,
        "take_profit": 2675.0,
        "planned_rr": 2.5,
        "entry_time": "2026-10-04T10:00:00+00:00",
        "strategy_name": "GOLD_QUARTERS",
        "bot_profile": "GOLD",
        "details": {
            "metadata": {
                "strategy_name": "GOLD_QUARTERS",
                "major_quarter": 2650.0,
                "quarters_level": 2650.0,
                "target_quarter": 2675.0,
                "managed_by_daemon": True,
            }
        },
    }

    repo = MockRepo([orb_trade, gold_trade])
    dash = RealtimeDashboardService(repository=repo)
    snap = dash.snapshot()

    orb_pos = next(p for p in snap["open_positions"] if p["id"] == 992)
    assert orb_pos["entry_strategy_view"]["strategy_name"] == "ORB_NEW_YORK"
    assert orb_pos["entry_strategy_view"]["opening_range_high"] == 20090.0
    assert any("Rango M15 NY" in p for p in orb_pos["entry_strategy_view"]["passed"])
    assert any("Quiebre de Rango Confirmado" in p for p in orb_pos["entry_strategy_view"]["passed"])

    gold_pos = next(p for p in snap["open_positions"] if p["id"] == 993)
    assert gold_pos["entry_strategy_view"]["strategy_name"] == "GOLD_QUARTERS"
    assert gold_pos["entry_strategy_view"]["major_quarter"] == 2650.0
    assert any("Cuadrante Mayor" in p for p in gold_pos["entry_strategy_view"]["passed"])
    assert any("Proyección hacia Target" in p for p in gold_pos["entry_strategy_view"]["passed"])


def test_position_health_developing_trade_gets_fair_score_and_mantener():
    from dashboard.realtime_dashboard import _position_health

    # 1. Test directo de la función asesora _position_health:
    # Trade en desarrollo +0.6R (sin invalidaciones)
    direct_health = _position_health(
        position={"direction": "BUY"},
        market={"current_rr": 0.6, "current_price": 106.0},
        latest={"direction": "BUY", "decision": "WAITING_TRADE_RESOLUTION"},
    )
    # 50 base + 15 (>= 0.4R) = 65 -> MANTENER!
    assert direct_health["health_score"] >= 65.0
    assert direct_health["recommendation"] == "MANTENER"

    # 2. Test integrado en el dashboard con telemetría en vivo
    trade = {
        "id": 888,
        "instrument": "Volatility 75 Index",
        "direction": "BUY",
        "entry_price": 100.0,
        "stop_loss": 90.0,
        "take_profit": 130.0,
        "planned_rr": 3.0,
        "current_price": 106.0,
        "entry_time": "2026-10-04T12:00:00+00:00",
        "broker_position_ticket": "4745944409",
        "strategy_name": "MALAYSIAN_SNR",
        "bot_profile": "SYNTHETICS",
        "details": {
            "metadata": {
                "strategy_name": "MALAYSIAN_SNR",
                "score": 88.0,
                "confirmation_percentage": 100.0,
                "managed_by_daemon": True,
            }
        },
    }

    dash = RealtimeDashboardService(repository=MockRepo([trade]))
    dash.cycle_start(1, 1)
    dash.monitor_result({
        "checked": 1,
        "activated": 0,
        "positions": [{
            "trade_id": 888,
            "symbol": "Volatility 75 Index",
            "direction": "BUY",
            "current_price": 106.0,
            "current_rr": 0.6,
            "distance_to_sl_r": 1.6,
            "distance_to_tp_r": 2.4,
            "initial_stop_loss": 90.0,
            "break_even_confirmed": False,
        }],
    })
    snap = dash.snapshot()
    pos = snap["open_positions"][0]

    assert pos["health_score"] >= 65.0
    assert pos["recommendation"] == "MANTENER"
    assert pos["quality_score"] == 88.0
    assert pos["confirmation_percentage"] == 100.0
    assert pos["duration_str"] != "—"

