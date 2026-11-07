import json

import os

import re

import subprocess

from pathlib import Path



from dashboard.strategy_bases_page import STRATEGY_BASES_HTML





def test_strategy_bases_excludes_connors_and_gold_tab_buttons():

    # Buttons for connors_rsi2 and gold should not exist in tab bar

    assert "setStrategyTab('connors_rsi2')" not in STRATEGY_BASES_HTML

    assert "setStrategyTab('gold')" not in STRATEGY_BASES_HTML

    # Active strategies should remain

    assert "setStrategyTab('all')" in STRATEGY_BASES_HTML

    assert "setStrategyTab('malaysian')" in STRATEGY_BASES_HTML

    assert "setStrategyTab('orb')" in STRATEGY_BASES_HTML

    assert "setStrategyTab('ict')" in STRATEGY_BASES_HTML

    assert "setStrategyTab('trend_pullback')" in STRATEGY_BASES_HTML





def test_strategy_bases_excludes_msnr_runtime_settings_by_default():

    # By default, the heavy parameterizable MSNR settings panel is removed

    assert '<section class="card" id="msnrRuntimeSettings"' not in STRATEGY_BASES_HTML

    assert "Ajustes de Malaysian SNR" not in STRATEGY_BASES_HTML

    assert "Diagnóstico y seguimiento de setups" not in STRATEGY_BASES_HTML

    assert "Consultar valores por defecto" not in STRATEGY_BASES_HTML

    # But Malaysian SNR audit panel stays intact

    assert 'id="msnrAuditPanel"' in STRATEGY_BASES_HTML

    assert "Malaysian SNR Híbrido Institucional" in STRATEGY_BASES_HTML





def test_strategy_bases_winners_and_losers_contain_no_connors_or_gold():

    winners_match = re.search(r"const WINNERS_DATA = (\[.*?\]);", STRATEGY_BASES_HTML, re.S)

    assert winners_match is not None

    winners = json.loads(winners_match.group(1))



    losers_match = re.search(r"const LOSERS_DATA = (\[.*?\]);", STRATEGY_BASES_HTML, re.S)

    assert losers_match is not None

    losers = json.loads(losers_match.group(1))



    # Assert no Connors RSI or Gold Quarters

    for w in winners:

        strat = w.get("strategy", "").lower()

        assert "connors" not in strat, f"Found Connors in winners: {w}"

        assert "gold" not in strat, f"Found Gold in winners: {w}"



    for l in losers:

        strat = l.get("strategy", "").lower()

        assert "connors" not in strat, f"Found Connors in losers: {l}"

        assert "gold" not in strat, f"Found Gold in losers: {l}"



    # Assert active strategies are intact

    winner_strats = {w.get("strategy") for w in winners}

    assert "Malaysian SNR" in winner_strats

    assert "ICT Sabri Malle" in winner_strats

    assert "ORB New York" in winner_strats

    assert "Trend Pullback" in winner_strats



    # Total counts match expectations

    assert len(winners) == 292

    assert len([w for w in winners if w.get("is_profitable")]) == 151

    assert len(losers) == 141





def test_strategy_bases_javascript_syntax_valid():

    scripts = re.findall(r"<script>(.*?)</script>", STRATEGY_BASES_HTML, re.S)

    assert len(scripts) >= 1

    root = Path(__file__).resolve().parents[1]

    for idx, script in enumerate(scripts):

        test_js = root / "storage" / f"test_strat_bases_syntax_{idx}.js"

        test_js.parent.mkdir(parents=True, exist_ok=True)

        test_js.write_text(script, encoding="utf-8")

        res = subprocess.run(["node", "--check", str(test_js)], capture_output=True, text=True)

        assert res.returncode == 0, f"Script {idx} failed syntax check: {res.stderr}"





def test_strategy_bases_msnr_settings_toggle_configurable(monkeypatch):

    import importlib

    import dashboard.strategy_bases_page as sbp



    # When toggled on with env var, it can be restored without code changes

    monkeypatch.setenv("DAEMONBLACKFX_SHOW_MSNR_RUNTIME_SETTINGS", "1")

    importlib.reload(sbp)

    assert '<section class="card" id="msnrRuntimeSettings"' in sbp.STRATEGY_BASES_HTML



    # Clean up

    monkeypatch.delenv("DAEMONBLACKFX_SHOW_MSNR_RUNTIME_SETTINGS", raising=False)

    importlib.reload(sbp)

    assert '<section class="card" id="msnrRuntimeSettings"' not in sbp.STRATEGY_BASES_HTML





def test_strategy_bases_5y_replay_panels_and_trend_pullback():

    assert 'id="trendPullbackAuditPanel"' in STRATEGY_BASES_HTML

    assert 'Auditoría Replay Fiel 5 Años Trend Pullback' in STRATEGY_BASES_HTML

    assert 'id="triMotorAuditPanel"' in STRATEGY_BASES_HTML

    assert 'Replay Fiel de 5 Años' in STRATEGY_BASES_HTML

    assert 'id="msnrAuditPanel"' in STRATEGY_BASES_HTML

    assert 'id="orbAuditPanel"' in STRATEGY_BASES_HTML

    assert 'id="ictAuditPanel"' in STRATEGY_BASES_HTML

