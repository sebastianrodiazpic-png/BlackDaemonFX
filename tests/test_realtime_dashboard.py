from dashboard.realtime_dashboard import RealtimeDashboardService


class Repo:
    def open_trades(self, source=None):
        return [{
            "id": 10,
            "instrument": "Volatility 75 Index",
            "direction": "BUY",
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "take_profit": 120.0,
            "risk_percent": 0.5,
            "risk_amount": 50.0,
            "details": {"metadata": {
                "trade_leg": "RUNNER",
                "execution_mode": "SPLIT",
                "break_even_confirmed": True,
                "trade_score": 88.0,
                "confirmation_percentage": 82.0,
            }},
        }]


def test_dashboard_extracts_realtime_trade_quality():
    dash = RealtimeDashboardService(repository=Repo())
    dash.cycle_start(3, 12)
    dash.symbol_start("Volatility 75 Index", 1, 12)
    dash.symbol_result({
        "symbol": "Volatility 75 Index",
        "action": "SPLIT_ORDER_OPENED",
        "signal": {
            "direction": "BUY",
            "trade_score": 88,
            "confirmation_percentage": 82,
            "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
            "confirmations_passed": 9,
            "confirmations_total": 11,
            "passed_confirmations": ["h1_trend", "liquidity_sweep", "m15_structure", "fresh_order_block"],
            "missing_confirmations": ["strong_close"],
            "critical_confirmation_failures": [],
            "divergence_confirmation": True,
            "divergence_type": "DIVERGENCIA_ALCISTA_REGULAR",
            "harmonic_confirmed": False,
            "m15_structure_break_type": "CHOCH",
            "m15_zone": "DISCOUNT",
        },
    }, 1, 12, 0.45)
    state = dash.snapshot()
    last = state["recent"][0]
    assert last["score"] == 88.0
    assert last["grade"] == "A"
    assert last["confirmation_percentage"] == 82.0
    assert last["divergence_confirmed"] is True
    assert last["structure_break"] == "CHOCH"
    assert "Barrido de liquidez" in last["passed"]
    assert "Cierre fuerte" in last["missing"]
    assert state["open_positions"][0]["break_even_confirmed"] is True


def test_dashboard_position_health_detects_opposite_confirmed_signal():
    dash = RealtimeDashboardService(repository=Repo())
    dash.cycle_start(1, 1)
    dash.monitor_result({
        "checked": 1,
        "activated": 0,
        "positions": [{
            "trade_id": 10,
            "symbol": "Volatility 75 Index",
            "direction": "BUY",
            "current_price": 104.0,
            "current_rr": 0.4,
            "distance_to_sl_r": 1.4,
            "distance_to_tp_r": 1.6,
            "initial_stop_loss": 90.0,
            "break_even_confirmed": False,
        }],
    })
    dash.symbol_result({
        "symbol": "Volatility 75 Index",
        "action": "NO_TRADE",
        "signal": {
            "direction": "SELL",
            "trade_score": 88,
            "confirmation_percentage": 82,
            "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
            "passed_confirmations": ["m15_structure", "displacement"],
            "critical_confirmation_failures": [],
            "divergence_confirmation": True,
            "divergence_type": "DIVERGENCIA_BAJISTA_REGULAR",
        },
    }, 1, 1, 0.2)
    state = dash.snapshot()
    pos = state["open_positions"][0]
    assert pos["current_rr"] == 0.4
    assert pos["recommendation"] in {"PROTEGER", "SALIDA A EVALUAR"}
    assert any("dirección contraria" in reason for reason in pos["reasons"])
    assert pos["advisory_only"] is True


def test_dashboard_position_health_keeps_aligned_profitable_trade():
    dash = RealtimeDashboardService(repository=Repo())
    dash.cycle_start(1, 1)
    dash.monitor_result({
        "checked": 1,
        "activated": 0,
        "positions": [{
            "trade_id": 10,
            "symbol": "Volatility 75 Index",
            "direction": "BUY",
            "current_price": 112.0,
            "current_rr": 1.2,
            "distance_to_sl_r": 2.2,
            "distance_to_tp_r": 0.8,
            "initial_stop_loss": 90.0,
            "break_even_confirmed": True,
        }],
    })
    dash.symbol_result({
        "symbol": "Volatility 75 Index",
        "action": "NO_NEW_ORDER",
        "signal": {
            "direction": "BUY",
            "trade_score": 86,
            "confirmation_percentage": 80,
            "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
            "passed_confirmations": ["m15_structure", "displacement"],
            "critical_confirmation_failures": [],
            "divergence_confirmation": True,
            "divergence_type": "DIVERGENCIA_ALCISTA_REGULAR",
        },
    }, 1, 1, 0.2)
    pos = dash.snapshot()["open_positions"][0]
    assert pos["recommendation"] == "MANTENER"
    assert pos["health_score"] >= 75
    assert any("alineado" in reason for reason in pos["reasons"])


def test_dashboard_instrument_catalog_is_grouped_and_sorted_and_dynamic():
    dash = RealtimeDashboardService(repository=Repo())
    selected = dash.set_instrument_catalog({
        "volatility": ["Volatility 75 Index", "Volatility 10 Index"],
        "boom": ["Boom 1000 Index", "Boom 500 Index"],
        "step": ["Step Index 500", "Step Index 100"],
    }, selected_symbols=["Volatility 75 Index", "Boom 500 Index"])

    assert selected == ["Boom 500 Index", "Volatility 75 Index"]
    state = dash.snapshot()
    labels = [group["label"] for group in state["instrument_catalog"]]
    assert labels == sorted(labels, key=str.casefold)
    for group in state["instrument_catalog"]:
        assert group["symbols"] == sorted(group["symbols"], key=str.casefold)

    result = dash.update_selected_symbols(["Step Index 100", "Boom 1000 Index"])
    assert result["ok"] is True
    assert dash.get_selected_symbols() == ["Boom 1000 Index", "Step Index 100"]


def test_dashboard_rejects_empty_or_unknown_instrument_selection():
    dash = RealtimeDashboardService(repository=Repo())
    dash.set_instrument_catalog({"volatility": ["Volatility 75 Index"]}, selected_symbols=["Volatility 75 Index"])

    empty = dash.update_selected_symbols([])
    assert empty["ok"] is False
    assert dash.get_selected_symbols() == ["Volatility 75 Index"]

    unknown = dash.update_selected_symbols(["Unknown Index"])
    assert unknown["ok"] is False
    assert unknown["invalid"] == ["Unknown Index"]
    assert dash.get_selected_symbols() == ["Volatility 75 Index"]


def test_dashboard_attaches_m5_chart_and_nested_break_even_snapshot_to_open_position():
    dash = RealtimeDashboardService(repository=Repo())
    dash.cycle_start(1, 1)
    dash.monitor_result({
        "break_even": {
            "checked": 1,
            "positions": [{
                "trade_id": 10,
                "symbol": "Volatility 75 Index",
                "direction": "BUY",
                "current_price": 105.0,
                "current_stop_loss": 100.02,
                "current_rr": 0.5,
                "distance_to_sl_r": 1.5,
                "distance_to_tp_r": 1.5,
                "initial_stop_loss": 90.0,
                "break_even_confirmed": True,
            }],
        },
        "charts": {
            "Volatility 75 Index": {
                "symbol": "Volatility 75 Index",
                "timeframe": "M5",
                "candles": [
                    {"time": "2026-08-28T20:00:00+00:00", "open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0},
                ],
                "events": [
                    {"time": "2026-08-28T20:00:00+00:00", "type": "choch_bullish", "label": "CHOCH alcista", "direction": "BUY", "price": 99.0},
                ],
            }
        },
    })
    pos = dash.snapshot()["open_positions"][0]
    assert pos["current_rr"] == 0.5
    assert pos["current_stop_loss"] == 100.02
    assert pos["chart"]["timeframe"] == "M5"
    assert pos["chart"]["candles"][0]["close"] == 105.0
    assert pos["chart"]["events"][0]["label"] == "CHOCH alcista"


def test_dashboard_exposes_separate_instrument_management_route():
    import urllib.request

    dash = RealtimeDashboardService(repository=Repo(), host="127.0.0.1", port=0)
    dash.set_instrument_catalog({
        "volatility": ["Volatility 75 Index", "Volatility 10 Index"],
        "step": ["Step Index 400"],
    }, selected_symbols=["Volatility 75 Index"])
    try:
        dash.start()
        assert dash.instruments_url.endswith("/instruments")
        main = urllib.request.urlopen(dash.url, timeout=2).read().decode("utf-8")
        instruments = urllib.request.urlopen(dash.instruments_url, timeout=2).read().decode("utf-8")
        assert "Administrar instrumentos" in main
        assert "Instrumentos para nuevas entradas" in instruments
        assert "Buscar instrumento" in instruments
        assert "Volver al dashboard" in instruments
    finally:
        dash.stop()


def test_dashboard_preserves_entry_thesis_separately_from_latest_analysis():
    class RichRepo:
        def open_trades(self, source=None):
            return [{
                "id": 77,
                "instrument": "Volatility 75 Index",
                "direction": "BUY",
                "entry_time": "2026-08-28T20:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 90.0,
                "take_profit": 120.0,
                "risk_percent": 0.5,
                "risk_amount": 50.0,
                "details": {"metadata": {
                    "trade_leg": "RUNNER",
                    "execution_mode": "SPLIT",
                    "trade_score": 88.0,
                    "trade_grade": "A",
                    "confirmation_percentage": 82.0,
                    "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
                    "passed_confirmations": ["h1_trend", "liquidity_sweep", "m15_structure", "fresh_order_block"],
                    "missing_confirmations": ["strong_close"],
                    "critical_confirmation_failures": [],
                    "divergence_confirmation": True,
                    "divergence_type": "DIVERGENCIA_ALCISTA_REGULAR",
                    "h1_doji_confirmation": True,
                    "h1_doji_type": "DOJI_LIBELULA_H1_EXTREMO_ALCISTA",
                    "h1_doji_zone": "DISCOUNT",
                    "harmonic_confirmed": False,
                    "h1_trend": "BULLISH",
                    "m15_structure_break_type": "CHOCH",
                    "m15_zone": "DISCOUNT",
                }},
            }]

    dash = RealtimeDashboardService(repository=RichRepo())
    dash.cycle_start(1, 1)
    dash.symbol_result({
        "symbol": "Volatility 75 Index",
        "signal": {
            "direction": "SELL",
            "trade_score": 78,
            "confirmation_percentage": 76,
            "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
            "passed_confirmations": ["m15_structure"],
            "divergence_confirmation": True,
            "divergence_type": "DIVERGENCIA_BAJISTA_REGULAR",
        },
    }, 1, 1, 0.1)

    pos = dash.snapshot()["open_positions"][0]
    entry = pos["entry_strategy_view"]
    current = pos["latest_strategy_view"]
    assert pos["entry_time"] == "2026-08-28T20:00:00+00:00"
    assert entry["direction"] == "BUY"
    assert entry["score"] == 88.0
    assert entry["divergence_confirmed"] is True
    assert entry["h1_doji_confirmed"] is True
    assert "Barrido de liquidez" in entry["passed"]
    assert current["direction"] == "SELL"
    assert current["score"] == 78.0


def test_dashboard_html_exposes_audit_layers_and_rsi_panel():
    import urllib.request

    dash = RealtimeDashboardService(repository=Repo(), host="127.0.0.1", port=0)
    try:
        dash.start()
        main = urllib.request.urlopen(dash.url, timeout=2).read().decode("utf-8")
        assert "CHOCH / BOS" in main
        assert "Liquidez" in main
        assert "Order Blocks" in main
        assert "Divergencia / Doji / Armónico" in main
        assert "RSI 14" in main
        assert "Tesis al abrir" in main
        assert "Lo que ve ahora" in main
    finally:
        dash.stop()


def test_dashboard_translates_recent_analysis_codes_to_trader_friendly_spanish():
    dash = RealtimeDashboardService(repository=Repo())
    dash.cycle_start(1, 1)
    dash.symbol_result({
        "symbol": "Step Index 400",
        "action": "EMERGENCY_RISK_EXIT",
        "reason": "POST_FILL_RISK_HARD_CAP_BREACH",
        "signal": {
            "direction": "BUY",
            "trade_score": 84,
            "confirmation_percentage": 80,
            "confirmation_decision": "ADAPTIVE_75_CONFIRMED",
        },
    }, 1, 1, 0.15)
    row = dash.snapshot()["recent"][0]
    assert row["action_es"] == "Cierre de emergencia por protección de riesgo"
    assert "después de ser ejecutada" in row["reason_es"]
    assert row["decision_es"] == "Confirmada por regla adaptativa ≥75%"
    assert row["operational_state"]["label"] == "PROTECCIÓN / RIESGO"
    assert row["reason"] == "POST_FILL_RISK_HARD_CAP_BREACH"


def test_dashboard_marks_no_signal_as_waiting_and_explains_reason():
    dash = RealtimeDashboardService(repository=Repo())
    dash.cycle_start(1, 1)
    dash.symbol_result({
        "symbol": "Volatility 75 Index",
        "action": "NO_SIGNAL",
        "reason": "NO_M5_CONFIRMATION",
        "signal": {
            "direction": "BUY",
            "trade_score": 68,
            "confirmation_percentage": 66,
            "confirmation_decision": "REJECTED",
        },
    }, 1, 1, 0.2)
    row = dash.snapshot()["recent"][0]
    assert row["action_es"] == "Sin oportunidad confirmada"
    assert "M5 todavía no confirma" in row["reason_es"]
    assert row["operational_state"]["label"] == "ESPERANDO"


def test_dashboard_account_payload_and_route(tmp_path):
    import urllib.request
    from database.repository import TradingRepository

    repo = TradingRepository(db_path=tmp_path / "account.sqlite3")
    repo.save_account_snapshot({"broker": "Deriv-Demo", "balance": 10000, "equity": 10025, "free_margin": 9900, "margin": 100, "profit": 25})
    repo.create_trade({
        "source": "DEMO", "instrument": "Volatility 75 Index", "direction": "BUY", "status": "CLOSED",
        "result": "WIN", "planned_rr": 1.0, "realized_rr": 1.0, "net_pnl": 50,
        "details": {"metadata": {"trade_leg": "TP1"}},
    })
    repo.create_trade({
        "source": "DEMO", "instrument": "Step Index 400", "direction": "SELL", "status": "CLOSED",
        "result": "LOSS", "planned_rr": 2.0, "realized_rr": -1.0, "net_pnl": -50,
        "details": {"metadata": {"trade_leg": "RUNNER"}},
    })

    dash = RealtimeDashboardService(repository=repo, host="127.0.0.1", port=0)
    dash.cycle_start(1, 1)
    state = dash.snapshot()
    assert state["account"]["snapshot"]["balance"] == 10000
    assert state["account"]["stats"]["tp1"] == 1
    assert state["account"]["stats"]["stop_loss"] == 1
    assert state["account"]["stats"]["win_rate"] == 50.0

    dash.start()
    try:
        with urllib.request.urlopen(dash.account_url, timeout=2) as response:
            html = response.read().decode("utf-8")
        assert "Cuenta activa" in html
        assert "Stop Loss" in html
    finally:
        dash.stop()



def test_account_api_reads_sqlalchemy_directly_and_survives_dashboard_state_loss(tmp_path):
    import json
    import urllib.request
    from database.repository import TradingRepository

    db = tmp_path / "persistent_account.sqlite3"
    state_file = tmp_path / "dashboard_state.json"
    repo = TradingRepository(db_path=db)
    repo.save_account_snapshot({
        "broker": "Deriv-Demo", "balance": 10027.51, "equity": 10064.23,
        "free_margin": 10013.33, "margin": 50.90, "profit": 36.72,
    })
    repo.create_trade({
        "source": "DEMO", "instrument": "Skew Step Index 5 Down", "direction": "BUY",
        "status": "OPEN", "planned_rr": 1.0, "risk_percent": 0.49,
        "execution_key": "persist-test:TP1", "external_ticket": "persist-001",
        "details": {"metadata": {"trade_leg": "TP1", "execution_mode": "SPLIT"}},
    })
    closed_id = repo.create_trade({
        "source": "DEMO", "instrument": "Skew Step Index 5 Down", "direction": "BUY",
        "status": "OPEN", "planned_rr": 2.0, "risk_percent": 0.49,
        "execution_key": "persist-test:RUNNER", "external_ticket": "persist-002",
        "details": {"metadata": {"trade_leg": "RUNNER", "execution_mode": "SPLIT"}},
    })
    repo.close_trade(closed_id, {
        "result": "WIN", "exit_price": 102.0, "realized_rr": 2.0, "net_pnl": 25.0,
    })

    dash = RealtimeDashboardService(
        repository=repo, host="127.0.0.1", port=0, state_path=state_file
    )
    dash.start()
    try:
        with urllib.request.urlopen(dash.url + "/api/account", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["data_source"] == "SQLALCHEMY_LOCAL_ONLY"
        assert payload["persistence"]["transient_dashboard_state_used"] is False
        assert payload["stats"]["total"] == 2
        assert payload["stats"]["open"] == 1
        assert payload["stats"]["closed"] == 1
        assert payload["stats"]["wins"] == 1
        assert payload["stats"]["win_rate"] == 100.0
        assert payload["stats"]["net_pnl"] == 25.0
        assert payload["snapshot"]["balance"] == 10027.51
    finally:
        dash.stop()

    if state_file.exists():
        state_file.unlink()

    # Nuevo servicio, sin last_state.json: la página debe reconstruirse igual desde DB.
    dash2 = RealtimeDashboardService(
        repository=repo, host="127.0.0.1", port=0, state_path=state_file
    )
    dash2.start(live=False)
    try:
        with urllib.request.urlopen(dash2.url + "/api/account", timeout=2) as response:
            payload2 = json.loads(response.read().decode("utf-8"))
        assert payload2["stats"]["total"] == 2
        assert payload2["stats"]["open"] == 1
        assert payload2["stats"]["closed"] == 1
        assert payload2["stats"]["win_rate"] == 100.0
        assert payload2["snapshot"]["equity"] == 10064.23
    finally:
        dash2.stop()

def test_smc_visual_context_exposes_structure_liquidity_ob_fvg_and_pd():
    import pandas as pd
    from dashboard.smc_visual_context import build_smc_visual_context

    times = pd.date_range('2026-08-29T00:00:00Z', periods=7, freq='5min')
    frame = pd.DataFrame({
        'time': times,
        'open':  [100, 101, 102, 105, 106, 107, 108],
        'high':  [102, 103, 103, 106, 108, 109, 110],
        'low':   [99, 100, 101, 104, 105, 106, 107],
        'close': [101, 102, 102.5, 105.5, 107, 108, 109],
        'swing_high': [False, False, True, False, False, False, False],
        'swing_low': [True, False, False, False, False, False, False],
        'structure': ['HL', None, 'HH', None, None, None, None],
        'choch_bullish': [False, False, False, True, False, False, False],
        'choch_bearish': [False] * 7,
        'bos_bullish': [False, False, False, False, True, False, False],
        'bos_bearish': [False] * 7,
        'bullish_sweep': [False, False, False, True, False, False, False],
        'bearish_sweep': [False] * 7,
        'buy_side_liquidity': [False, False, True, False, False, False, False],
        'sell_side_liquidity': [True, False, False, False, False, False, False],
        'liquidity_level': [99.5, None, 103.0, None, None, None, None],
        'sweep_level': [None, None, None, 99.5, None, None, None],
        'ob_low': [None, 100.0, None, None, None, None, None],
        'ob_high': [None, 103.0, None, None, None, None, None],
        'ob_type': [None, 'bullish', None, None, None, None, None],
        'range_high': [110.0] * 7,
        'range_low': [90.0] * 7,
        'equilibrium': [100.0] * 7,
        'zone': ['premium'] * 7,
    })
    visual = build_smc_visual_context(frame)
    types = {e['type'] for e in visual['events']}
    assert 'swing_high' in types
    assert 'choch_bullish' in types
    assert 'bos_bullish' in types
    assert any(x['type'] == 'buy_side_liquidity' for x in visual['levels'])
    assert any(z['layer'] == 'orderblock' for z in visual['zones'])
    assert any(z['layer'] == 'fvg' for z in visual['zones'])
    assert visual['context']['equilibrium'] == 100.0
    assert visual['context']['premium_discount_available'] is True


def test_dashboard_html_exposes_complete_smc_audit_layers():
    import urllib.request

    dash = RealtimeDashboardService(repository=Repo(), host='127.0.0.1', port=0)
    try:
        dash.start()
        main = urllib.request.urlopen(dash.url, timeout=2).read().decode('utf-8')
        assert 'Swings HH/HL/LH/LL' in main
        assert 'BSL / SSL / Sweeps' in main
        assert 'FVG / Imbalances' in main
        assert 'Premium / Discount' in main
        assert 'Contexto SMC multi-timeframe' in main
        assert 'contexto SMC auxiliar' in main
    finally:
        dash.stop()


def test_dashboard_persists_open_positions_and_restores_offline_state(tmp_path):
    state_file = tmp_path / "dashboard_state.json"
    live = RealtimeDashboardService(repository=Repo(), state_path=state_file)
    live.mark_live()
    live.monitor_result({
        "positions": [{
            "trade_id": 10,
            "symbol": "Volatility 75 Index",
            "direction": "BUY",
            "current_price": 107.0,
            "current_rr": 0.7,
            "distance_to_sl_r": 1.7,
            "distance_to_tp_r": 1.3,
            "initial_stop_loss": 90.0,
            "break_even_confirmed": False,
        }],
        "charts": {
            "Volatility 75 Index": {
                "symbol": "Volatility 75 Index",
                "timeframe": "M5",
                "candles": [{
                    "time": "2026-08-29T01:00:00+00:00",
                    "open": 100.0,
                    "high": 108.0,
                    "low": 99.0,
                    "close": 107.0,
                }],
                "events": [],
            }
        },
    })
    live.mark_offline()
    assert state_file.exists()

    offline = RealtimeDashboardService(repository=Repo(), state_path=state_file)
    state = offline.snapshot()
    assert state["connection_mode"] == "OFFLINE"
    assert "PERSISTIDO" in state["status"]
    assert len(state["open_positions"]) == 1
    pos = state["open_positions"][0]
    assert pos["persistence_status"] == "PERSISTED"
    assert pos["broker_verification"] == "PENDIENTE DE RECONCILIAR CON MT5"
    assert pos["current_price"] == 107.0
    assert pos["chart"]["timeframe"] == "M5"
    assert pos["recommendation"] == "SIN VALIDACIÓN EN VIVO"


def test_dashboard_offline_http_marks_data_as_persisted(tmp_path):
    import urllib.request

    state_file = tmp_path / "dashboard_state.json"
    dash = RealtimeDashboardService(repository=Repo(), host="127.0.0.1", port=0, state_path=state_file)
    try:
        dash.start(live=False)
        import json
        state = json.loads(urllib.request.urlopen(dash.url + "/api/state", timeout=2).read().decode("utf-8"))
        assert state["connection_mode"] == "OFFLINE"
        assert state["open_positions"][0]["persistence_status"] == "PERSISTED"
    finally:
        dash.stop()


def test_dashboard_shows_external_mt5_positions_without_managing_them(tmp_path):
    from database.repository import TradingRepository

    repo = TradingRepository(db_path=tmp_path / "external.sqlite3")
    repo.create_trade({
        "source": "MT5_EXTERNAL", "instrument": "Volatility 10 Index", "direction": "BUY",
        "status": "OPEN", "entry_price": 100.0, "stop_loss": 99.0, "take_profit": 102.0,
        "broker_position_ticket": "88001",
        "details": {"metadata": {"managed_by_daemon": False, "adopted_from_mt5": True}},
    })
    dash = RealtimeDashboardService(repository=repo, host="127.0.0.1", port=0)
    state = dash.snapshot()
    assert len(state["open_positions"]) == 1
    row = state["open_positions"][0]
    assert row["source"] == "MT5_EXTERNAL"
    assert row["managed_by_daemon"] is False
    assert row["recommendation"] == "SOLO VISUALIZACIÓN"


def test_dashboard_chart_controls_apply_only_to_graph_and_support_timeframes_navigation():
    import urllib.request

    dash = RealtimeDashboardService(repository=Repo(), host="127.0.0.1", port=0)
    try:
        dash.start()
        main = urllib.request.urlopen(dash.url, timeout=2).read().decode("utf-8")
        assert 'id="chartViewportShell"' in main
        assert 'id="chartFullscreenBtn"' in main
        assert 'Pantalla completa' in main
        assert 'id="chartMinimizeBtn"' in main
        assert 'Minimizar' in main
        assert "function chartCard(){return $('chartViewportShell')}" in main
        assert 'chartPlotCollapsed' in main
        for tf in ("M1", "M5", "M15", "H1"):
            assert f'data-tf="{tf}"' in main
        assert 'id="chartZoomInBtn"' in main
        assert 'id="chartZoomOutBtn"' in main
        assert 'id="chartResetViewBtn"' in main
        assert "addEventListener('wheel'" in main
        assert "addEventListener('pointermove'" in main
        assert 'id="chartZoomBadge"' in main
        assert 'Y 1.0× · X 1.0×' in main
        assert 'Scroll ↑/↓ = escala vertical' in main
        assert 'arrastrar = mover gráfico completo X/Y' in main
        assert 'Ctrl+scroll = zoom de velas' in main
        assert 'priceZoom:1' in main
        assert 'dragStartX:0' in main
        assert 'dragStartOffset:0' in main
        assert 'chartViewState.dragStartOffset+dx' in main
        assert 'chartViewState.dragStartPricePan+(dy/height)' in main
        assert 'maxPriceZoom:20' in main
        assert "addEventListener('dblclick'" in main
        assert 'maxZoom:12' in main
        assert 'minVisible:8' in main
    finally:
        dash.stop()

def test_fvg_zone_labels_follow_chart_time_coordinates_without_viewport_clamp():
    import inspect
    from dashboard import realtime_dashboard
    source = inspect.getsource(realtime_dashboard)
    assert 'function chartObjectX(allCandles,win,time,plotW,padLeft)' in source
    assert 'class="zoneChartLabel"' in source
    assert 'const xx=chartObjectX(allCandles,win,z.time,plotW,pad.l)' in source
    assert 'x="${xx+6}"' in source


def test_dashboard_instrument_selection_is_saved_to_sqlalchemy_and_restored(tmp_path):
    from database.repository import TradingRepository

    db = tmp_path / "instrument_selection.sqlite3"
    repo = TradingRepository(db)
    dash = RealtimeDashboardService(
        repository=repo,
        state_path=tmp_path / "state.json",
    )
    categorized = {
        "volatility": ["Volatility 75 Index", "Volatility 100 Index"],
        "orb_ny_xauusd": ["XAUUSD"],
    }
    dash.set_instrument_catalog(
        categorized,
        selected_symbols=["Volatility 75 Index", "XAUUSD"],
    )
    result = dash.update_selected_symbols(["XAUUSD"])
    assert result["ok"] is True
    assert result["persistent"] is True

    persisted = repo.latest_instrument_selection(source="DEMO")
    assert persisted["selected_symbols"] == ["XAUUSD"]

    # Nuevo dashboard y sin last_state.json: SQLAlchemy conserva la preferencia.
    dash2 = RealtimeDashboardService(
        repository=TradingRepository(db),
        state_path=tmp_path / "other_state.json",
    )
    selected = dash2.set_instrument_catalog(categorized, selected_symbols=None)
    assert selected == ["XAUUSD"]


def test_dashboard_explicit_initial_selection_temporarily_overrides_persisted_preference(tmp_path):
    from database.repository import TradingRepository

    db = tmp_path / "instrument_override.sqlite3"
    repo = TradingRepository(db)
    repo.save_instrument_selection(["XAUUSD"], source="DEMO")

    dash = RealtimeDashboardService(
        repository=repo,
        state_path=tmp_path / "override_state.json",
    )
    categorized = {
        "volatility": ["Volatility 75 Index"],
        "orb_ny_xauusd": ["XAUUSD"],
    }
    selected = dash.set_instrument_catalog(
        categorized,
        selected_symbols=["Volatility 75 Index"],
    )
    assert selected == ["Volatility 75 Index"]
    # El override visual no modifica la preferencia guardada.
    assert repo.latest_instrument_selection(source="DEMO")["selected_symbols"] == ["XAUUSD"]
