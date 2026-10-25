"""Rendimiento del front: /api/state ligero, gzip, cachés y consultas acotadas (20-oct-2026).

Antes: /api/state tardaba 19-33 s y pesaba 15 MB (decodificaba ~4.000 auditorías visuales y la cuenta completa
en cada refresco). Después: ~1-2 s y ~0,45 MB comprimido.
"""
import gzip
import json
import time
from datetime import datetime, timezone

from dashboard.realtime_dashboard import (
    RealtimeDashboardService,
    _build_confluence_matrix,
    _light_smc_trial,
    _light_state_payload,
    _maybe_gzip,
)


def test_gzip_only_for_large_text_when_accepted():
    body = json.dumps({"x": "a" * 5000}).encode()
    gz, enc = _maybe_gzip(body, "application/json; charset=utf-8", "gzip, deflate, br")
    assert enc == "gzip" and gzip.decompress(gz) == body and len(gz) < len(body)
    assert _maybe_gzip(body, "application/json", "") == (body, None)            # cliente sin gzip
    assert _maybe_gzip(b"{}", "application/json", "gzip") == (b"{}", None)       # muy pequeño
    assert _maybe_gzip(body, "image/png", "gzip") == (body, None)                # binario


def test_light_state_keeps_only_account_snapshot():
    state = {"account": {"snapshot": {"balance": 1}, "stats": {"n": 1}, "recent_trades": [1] * 1000,
                         "monthly_daily_performance": {"a": 1}, "period_performance": {"b": 2}}, "recent": [1]}
    light = _light_state_payload(state)
    assert light["account"] == {"snapshot": {"balance": 1}, "stats": {"n": 1}}
    assert light["recent"] == [1]
    assert "recent_trades" in state["account"]  # no muta el estado original


def test_light_smc_trial_sends_counts_and_last_30_blocks():
    blocks = {f"b{i}": {"symbol": "X"} for i in range(100)}
    obs = {f"o{i}": {"stale_at_first_seen": i % 2 == 0} for i in range(10)}
    report = {"workers": [{"profile": "P", "m15_blocks": blocks, "signal_observations": obs, "stale_signals": [1, 2, 3]}]}
    w = _light_smc_trial(report)["workers"][0]
    assert w["m15_blocks_count"] == 100 and list(w["m15_blocks"]) == [f"b{i}" for i in range(70, 100)]
    assert w["signal_observations_count"] == 10 and w["signal_observations_stale_count"] == 5
    assert w["stale_signals_count"] == 3 and w["signal_observations"] == {} and w["stale_signals"] == []


def test_front_uses_precomputed_counts():
    from dashboard import realtime_dashboard as rd
    src = open(rd.__file__, encoding="utf-8").read()
    for field in ("w.m15_blocks_count", "w.signal_observations_count", "w.signal_observations_stale_count",
                  "w.stale_signals_count"):
        assert field in src


def test_state_endpoint_serves_light_payload():
    from dashboard import realtime_dashboard as rd
    src = open(rd.__file__, encoding="utf-8").read()
    assert "json.dumps(_light_state_payload(service.snapshot()), ensure_ascii=False)" in src
    assert "_maybe_gzip(body, content_type, self.headers.get(\"Accept-Encoding\", \"\"))" in src


def test_account_stale_while_revalidate_never_blocks():
    svc = RealtimeDashboardService(repository=None)
    svc._account_cache = {"at": time.monotonic() - 3600, "payload": {"snapshot": {"balance": 9}}}
    started = []
    svc._refresh_account_in_background = lambda: started.append(True)
    t = time.perf_counter()
    payload = svc._cached_account_payload(allow_stale=True)
    assert payload == {"snapshot": {"balance": 9}} and started == [True]
    assert time.perf_counter() - t < 0.5


def test_confluence_matrix_row_without_badge_branch_does_not_crash():
    state = {"selection_profiles": {"SYNTHETICS": ["Boom 300 Index"]},
             "recent": [{"symbol": "Boom 300 Index", "bot_profile": "BOOM", "action": "WAITING_ICT",
                         "reason": "ICT_SYMBOL_PRUNED_WINRATE_LE_45", "strategy_name": "ICT_SABRI_MALLE"}]}
    rows = _build_confluence_matrix(state)
    assert all("badge_class" in r for r in rows)


def test_repository_filters_and_entry_context_cache(tmp_path):
    from database.models import PositionVisualAudit, TradeVisualAudit
    from database.repository import TradingRepository
    repo = TradingRepository(tmp_path / "front.sqlite")
    now = datetime.now(timezone.utc)
    with repo.Session() as s:
        for i in range(1, 6):
            s.add(TradeVisualAudit(trade_id=i, source="DEMO", bot_profile="ICT", daemon_magic=1, instrument=f"S{i}", entry_context_json=json.dumps({"i": i}),
                                   entry_chart_json="{}", latest_chart_json="{}", latest_market_json="{}"))
            s.add(PositionVisualAudit(source="DEMO", bot_profile="ICT", daemon_magic=1, instrument=f"S{i}", chart_json="{}", updated_at=now))
        s.commit()
    assert {r["trade_id"] for r in repo.trade_visual_audits(source="DEMO", trade_ids=[2, 4])} == {2, 4}
    assert repo.trade_visual_audits(source="DEMO", trade_ids=[]) == []
    assert len(repo.trade_visual_audits(source="DEMO")) == 5
    assert {r["instrument"] for r in repo.position_visual_audits(source="DEMO", symbols=["S1", "S3"])} == {"S1", "S3"}
    assert repo.position_visual_audits(source="DEMO", symbols=[]) == []
    ctx = repo.trade_visual_audit_entry_contexts(source="DEMO")
    assert ctx == {str(i): {"i": i} for i in range(1, 6)}
    with repo.Session() as s:   # nuevo trade: solo se decodifica el nuevo
        s.add(TradeVisualAudit(trade_id=6, source="DEMO", bot_profile="ICT", daemon_magic=1, instrument="S6", entry_context_json=json.dumps({"i": 6}),
                               entry_chart_json="{}", latest_chart_json="{}", latest_market_json="{}"))
        s.commit()
    assert repo.trade_visual_audit_entry_contexts(source="DEMO")["6"] == {"i": 6}
