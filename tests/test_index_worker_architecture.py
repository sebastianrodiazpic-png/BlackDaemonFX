# -*- coding: utf-8 -*-
"""
Test de arquitectura de los workers aislados:
- commodities-snr (COMMODITIES_SNR)
- indicesb-snr (INDICESB_SNR)
y su integración obligatoria en multi-bot-daemon.
"""

import pytest
from app.main import (
    BOT_PROFILES,
    FULL_MULTI_BOT_PROFILES,
    _selection_profile_for_bot,
)
from config.strategy_config import PRUNED_ASSET_UNIVERSE


def test_indicesb_snr_worker_profile_configuration():
    assert "INDICESB_SNR" in BOT_PROFILES, "INDICESB_SNR debe estar registrado en BOT_PROFILES"
    profile = BOT_PROFILES["INDICESB_SNR"]
    assert profile["mode"] == "indicesb-snr-daemon"
    assert profile["magic"] == 26082042
    assert "Wall Street 30" in profile["symbols"]
    assert "US Tech 100" in profile["symbols"]
    assert "US SP 500" in profile["symbols"]
    assert "Germany 40" in profile["symbols"]


def test_commodities_snr_worker_profile_configuration():
    assert "COMMODITIES_SNR" in BOT_PROFILES, "COMMODITIES_SNR debe estar registrado en BOT_PROFILES"
    profile = BOT_PROFILES["COMMODITIES_SNR"]
    assert profile["mode"] == "commodities-snr-daemon"
    assert profile["magic"] == 26082041
    assert "XAUUSD" in profile["symbols"]
    assert "XAGUSD" in profile["symbols"]
    assert "US Oil" in profile["symbols"]
    assert "UK Brent Oil" in profile["symbols"]


def test_full_multibot_includes_both_commodities_and_indices_snr():
    assert "COMMODITIES_SNR" in FULL_MULTI_BOT_PROFILES, (
        "COMMODITIES_SNR debe estar en FULL_MULTI_BOT_PROFILES para ejecución automática desde multi-bot-daemon"
    )
    assert "INDICESB_SNR" in FULL_MULTI_BOT_PROFILES, (
        "INDICESB_SNR debe estar en FULL_MULTI_BOT_PROFILES para ejecución automática desde multi-bot-daemon"
    )


def test_selection_profile_mapping_for_indices_and_commodities_snr():
    assert _selection_profile_for_bot("INDICESB_SNR") == "INDICESB_SNR"
    assert _selection_profile_for_bot("INDICES") == "INDICESB_SNR"
    assert _selection_profile_for_bot("COMMODITIES_SNR") == "COMMODITIES_SNR"
    assert _selection_profile_for_bot("COMMODITIES") == "COMMODITIES_SNR"


def test_pruned_asset_universe_indicesb_and_commodities_snr():
    assert "INDICESB_SNR" in PRUNED_ASSET_UNIVERSE
    indices = PRUNED_ASSET_UNIVERSE["INDICESB_SNR"]
    for sym in ("Wall Street 30", "US Tech 100", "US SP 500", "Germany 40"):
        assert sym in indices, f"{sym} debe estar en PRUNED_ASSET_UNIVERSE['INDICESB_SNR']"

    assert "COMMODITIES_SNR" in PRUNED_ASSET_UNIVERSE
    comm = PRUNED_ASSET_UNIVERSE["COMMODITIES_SNR"]
    for sym in ("XAUUSD", "XAGUSD", "US Oil", "UK Brent Oil"):
        assert sym in comm, f"{sym} debe estar en PRUNED_ASSET_UNIVERSE['COMMODITIES_SNR']"


def test_dashboard_set_instrument_catalog_commodities_and_indices(tmp_path):
    from database.repository import TradingRepository
    from dashboard.realtime_dashboard import RealtimeDashboardService, _catalog_symbols_by_profile

    catalog_dict = {
        "commodities_snr": ["XAUUSD", "US Oil"],
        "indicesb_snr": ["Wall Street 30", "US Tech 100"],
        "volatility": ["Volatility 75 Index"],
    }
    catalog_list = [
        {"category": k, "symbols": v} for k, v in catalog_dict.items()
    ]
    allowed = _catalog_symbols_by_profile(catalog_list)
    assert "COMMODITIES_SNR" in allowed
    assert "INDICESB_SNR" in allowed
    assert "XAUUSD" in allowed["COMMODITIES_SNR"]
    assert "Wall Street 30" in allowed["INDICESB_SNR"]

    repo = TradingRepository(db_path=tmp_path / "dash_test.db")
    dash = RealtimeDashboardService(repository=repo, port=0, state_path=tmp_path / "state.json")
    dash.set_instrument_catalog(catalog_dict, selected_symbols=None)
    snap = dash.snapshot()
    assert "COMMODITIES_SNR" in snap["selection_profiles"]
    assert "INDICESB_SNR" in snap["selection_profiles"]


def test_malaysian_snr_strictly_excludes_commodities_and_indices():
    """Valida que MALAYSIAN_SNR no contenga commodities ni índices, reservándolos para COMMODITIES_SNR e INDICESB_SNR."""
    from app.main import BOT_PROFILES, _apply_msnr_wr45_prune
    _apply_msnr_wr45_prune()

    msnr_spec = BOT_PROFILES["MALAYSIAN_SNR"]
    all_msnr_symbols = set(msnr_spec.get("symbols", [])) | set(msnr_spec.get("pruned_symbols", []))

    forbidden_commodities = {"XAUUSD", "XAUUSDmicro", "XAUEUR", "XAUEURmicro", "XAGUSD", "US Oil", "UK Brent Oil"}
    forbidden_indices = {"Wall Street 30", "US Tech 100", "US SP 500", "Germany 40"}

    overlap_comm = all_msnr_symbols.intersection(forbidden_commodities)
    overlap_idx = all_msnr_symbols.intersection(forbidden_indices)

    assert not overlap_comm, f"MALAYSIAN_SNR contiene commodities que deben ir a COMMODITIES_SNR: {overlap_comm}"
    assert not overlap_idx, f"MALAYSIAN_SNR contiene índices que deben ir a INDICESB_SNR: {overlap_idx}"

    comm_symbols = set(BOT_PROFILES["COMMODITIES_SNR"]["symbols"])
    for c in ("XAUUSD", "US Oil", "UK Brent Oil"):
        assert c in comm_symbols, f"{c} debe estar en COMMODITIES_SNR"

    idx_symbols = set(BOT_PROFILES["INDICESB_SNR"]["symbols"])
    for i in ("Wall Street 30", "US Tech 100", "US SP 500", "Germany 40"):
        assert i in idx_symbols, f"{i} debe estar en INDICESB_SNR"


