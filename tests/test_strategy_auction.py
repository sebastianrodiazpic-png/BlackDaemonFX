"""
tests/test_strategy_auction.py
==============================
Pruebas unitarias para el Motor de Subasta Competitiva de Estrategias:
1. Configuración e interruptores por variables de entorno.
2. Modo Bypass (Zero Breaking Changes cuando está desactivado).
3. Victoria individual de estrategia (ICT o Malaysian SNR).
4. Súper-Confluencia Cruzada (Ambas coinciden en dirección -> bonificación de score).
5. Conflicto Direccional (ICT Buy vs MSNR Sell -> VETO preventivo).
6. Rechazo por puntuación insuficiente (< 75 pts en sintéticos).
7. Restricciones direccionales asimétricas (Crash SELL only, Boom BUY only).
8. Preservación del Radar Estructural de Malaysian SNR cuando ninguna tiene orden inmediata.
"""

from datetime import datetime, timezone
import pytest

from strategy.confluence.strategy_auction import (
    CandidateEvaluation,
    StrategyAuctionConfig,
    extract_radar_description,
    extract_signal_direction,
    resolve_competitive_strategy_auction,
)


def test_strategy_auction_config_defaults_and_env(monkeypatch):
    """Verifica la carga de interruptores por defecto y vía variables de entorno."""
    cfg = StrategyAuctionConfig()
    assert cfg.enabled is True
    assert cfg.synthetic_min_score == 75.0
    assert cfg.real_min_score == 65.0
    assert cfg.direction_conflict_veto is True
    assert cfg.cross_strategy_bonus == 5.0

    monkeypatch.setenv("DAEMONBLACKFX_COMPETITIVE_STRATEGY_AUCTION", "0")
    monkeypatch.setenv("DAEMONBLACKFX_AUCTION_SYNTHETIC_MIN_SCORE", "80.0")
    monkeypatch.setenv("DAEMONBLACKFX_AUCTION_CONFLICT_VETO", "0")

    cfg2 = StrategyAuctionConfig()
    assert cfg2.enabled is False
    assert cfg2.synthetic_min_score == 80.0
    assert cfg2.direction_conflict_veto is False


def test_strategy_auction_bypass_mode():
    """Verifica que si la subasta está desactivada, opera exactamente con el cortocircuito legado."""
    cfg = StrategyAuctionConfig(enabled=False)

    msnr_analysis = {
        "valid": True,
        "action": "SELL",
        "signal": {"direction": "SELL", "entry": 1000, "sl": 1050, "tp": 900},
    }
    ict_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {"direction": "BUY", "entry": 1000, "sl": 950, "tp": 1100},
    }

    # En modo bypass, MSNR se evalúa primero por compatibilidad histórica
    res = resolve_competitive_strategy_auction("Volatility 75 Index", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is True
    assert res["strategy_name"] == "MALAYSIAN_SNR"


def test_strategy_auction_single_winner_msnr():
    """Malaysian SNR tiene señal activa y válida; ICT no tiene señal."""
    cfg = StrategyAuctionConfig(enabled=True)

    msnr_analysis = {
        "valid": True,
        "action": "SELL",
        "signal": {
            "direction": "SELL",
            "entry_price": 5000.0,
            "stop_loss": 5050.0,
            "take_profit": 4900.0,
            "confluence_score": 85.0,
        },
    }
    ict_analysis = {
        "valid": False,
        "action": "WAITING_ICT",
        "reason": "SCANNING_LIQUIDITY_M5",
    }

    res = resolve_competitive_strategy_auction("Volatility 75 Index", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is True
    assert res["strategy_name"] == "MALAYSIAN_SNR"
    assert res["auction_metadata"]["winner_strategy"] == "MALAYSIAN_SNR"
    assert res["auction_metadata"]["winner_score"] >= 80.0


def test_strategy_auction_single_winner_ict():
    """ICT tiene señal válida y calificada; Malaysian SNR está en espera de retest."""
    cfg = StrategyAuctionConfig(enabled=True)

    msnr_analysis = {
        "valid": False,
        "action": "WAITING_MALAYSIAN_SNR",
        "reason": "AWAITING_H1_RETEST",
        "scenario": "Esc. 1: Ruptura Fresh",
        "retest_remaining_minutes": 120,
    }
    ict_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {
            "direction": "BUY",
            "entry_price": 1.0850,
            "stop_loss": 1.0820,
            "take_profit": 1.0910,
            "confluence_score": 82.0,
        },
    }

    res = resolve_competitive_strategy_auction("EURUSD", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is True
    assert res["strategy_name"] == "ICT"
    assert res["auction_metadata"]["winner_strategy"] == "ICT"
    assert res["auction_metadata"]["candidates"]["MALAYSIAN_SNR"]["radar_description"] is not None


def test_strategy_auction_cross_strategy_confluence():
    """Ambas estrategias coinciden en BUY: se aplica bonificación de Súper-Confluencia."""
    cfg = StrategyAuctionConfig(enabled=True, cross_strategy_bonus=5.0)

    msnr_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {
            "direction": "BUY",
            "entry_price": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "confluence_score": 80.0,
        },
    }
    ict_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {
            "direction": "BUY",
            "entry_price": 101.0,
            "stop_loss": 97.0,
            "take_profit": 109.0,
            "confluence_score": 86.0,
        },
    }

    res = resolve_competitive_strategy_auction("Step Index", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is True
    assert res["auction_metadata"]["cross_strategy_confluence"] is True
    # Gana ICT porque partía con 86 (+5 = 91) frente a MSNR 80 (+5 = 85)
    assert res["strategy_name"] == "ICT"
    assert res["auction_metadata"]["winner_score"] == 91.0


def test_strategy_auction_direction_conflict_veto():
    """ICT propone BUY y Malaysian SNR propone SELL: VETO preventivo por conflicto institucional."""
    cfg = StrategyAuctionConfig(enabled=True, direction_conflict_veto=True)

    msnr_analysis = {
        "valid": True,
        "action": "SELL",
        "signal": {
            "direction": "SELL",
            "entry_price": 500.0,
            "stop_loss": 520.0,
            "take_profit": 460.0,
            "confluence_score": 85.0,
        },
    }
    ict_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {
            "direction": "BUY",
            "entry_price": 498.0,
            "stop_loss": 485.0,
            "take_profit": 525.0,
            "confluence_score": 82.0,
        },
    }

    res = resolve_competitive_strategy_auction("Jump 25 Index", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is False
    assert res["action"] == "VETO_DIRECTION_CONFLICT"
    assert res["auction_metadata"]["direction_conflict"] is True


def test_strategy_auction_subpar_score_rejected():
    """Ambas estrategias son válidas pero sus puntuaciones no alcanzan el umbral institucional (75 pts)."""
    cfg = StrategyAuctionConfig(enabled=True, synthetic_min_score=75.0)

    msnr_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {
            "direction": "BUY",
            "entry_price": 200.0,
            "stop_loss": 190.0,
            "take_profit": 220.0,
            "confluence_score": 62.0,
        },
    }
    ict_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {
            "direction": "BUY",
            "entry_price": 201.0,
            "stop_loss": 192.0,
            "take_profit": 219.0,
            "confluence_score": 68.0,
        },
    }

    res = resolve_competitive_strategy_auction("Volatility 100 Index", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is False
    assert res["action"] == "AUCTION_SCORES_SUBPAR"


def test_strategy_auction_direction_constraint_crash():
    """En Crash Index solo se permiten ventas (SELL). Una compra de ICT o MSNR queda descalificada."""
    cfg = StrategyAuctionConfig(enabled=True)

    msnr_analysis = {
        "valid": True,
        "action": "BUY",  # Violación: Crash solo opera SELL
        "signal": {
            "direction": "BUY",
            "entry_price": 1000.0,
            "stop_loss": 980.0,
            "take_profit": 1040.0,
            "confluence_score": 85.0,
        },
    }
    ict_analysis = {
        "valid": True,
        "action": "SELL",  # Válido para Crash
        "signal": {
            "direction": "SELL",
            "entry_price": 1000.0,
            "stop_loss": 1020.0,
            "take_profit": 960.0,
            "confluence_score": 78.0,
        },
    }

    res = resolve_competitive_strategy_auction(
        "Crash 1000 Index",
        msnr_analysis,
        ict_analysis,
        direction_constraint="SELL",
        config=cfg,
    )
    assert res["valid"] is True
    assert res["strategy_name"] == "ICT"
    assert res["auction_metadata"]["candidates"]["MALAYSIAN_SNR"]["disqualified"] is True


def test_strategy_auction_preserves_msnr_radar():
    """Ninguna tiene señal inmediata, pero Malaysian SNR tiene un nivel en retest: se conserva el ancla macro."""
    cfg = StrategyAuctionConfig(enabled=True)

    msnr_analysis = {
        "valid": False,
        "action": "WAITING_MALAYSIAN_SNR",
        "reason": "AWAITING_H1_RETEST",
        "scenario": "Esc. 1: Ruptura Fresh",
        "retest_remaining_minutes": 180,
    }
    ict_analysis = {
        "valid": False,
        "action": "WAITING_ICT",
        "reason": "AMD / Judas Swing M5",
    }

    res = resolve_competitive_strategy_auction("Volatility 30 (1s) Index", msnr_analysis, ict_analysis, config=cfg)
    assert res["valid"] is False
    assert res["strategy_name"] == "MALAYSIAN_SNR"
    assert res["context_policy"] == "MALAYSIAN_SNR_NATIVE"
    assert "auction_metadata" in res


def test_live_trading_engine_auction_helper():
    """Verifica que el método `_run_strategy_auction` de LiveTradingEngine opere correctamente."""
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine

    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        competitive_strategy_auction_enabled=True,
        auction_synthetic_min_score=75.0,
    )
    engine.human_criteria_engine = None

    msnr_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {"direction": "BUY", "entry": 100, "sl": 95, "tp": 110, "confluence_score": 88.0},
    }
    ict_analysis = {
        "valid": True,
        "action": "BUY",
        "signal": {"direction": "BUY", "entry": 101, "sl": 97, "tp": 109, "confluence_score": 79.0},
    }

    res = engine._run_strategy_auction("Volatility 75 Index", msnr_analysis, ict_analysis)
    assert res["valid"] is True
    assert res["strategy_name"] == "MALAYSIAN_SNR"
    assert res["auction_metadata"]["winner_strategy"] == "MALAYSIAN_SNR"
    assert res["auction_metadata"]["cross_strategy_confluence"] is True


def test_entry_decision_record_incorporates_auction_metadata():
    """Verifica que `build_entry_decision_record` serialice los metadatos de la subasta."""
    from strategy.confluence.entry_decision import build_entry_decision_record

    signal = {
        "direction": "SELL",
        "auction_metadata": {
            "winner_strategy": "MALAYSIAN_SNR",
            "winner_score": 85.5,
            "winner_grade": "GRADE_A_ELITE",
            "cross_strategy_confluence": True,
            "direction_conflict": False,
        },
    }

    record = build_entry_decision_record(
        symbol="Crash 1000 Index",
        direction="SELL",
        strategy_name="MALAYSIAN_SNR",
        signal=signal,
    )

    assert "auction" in record
    assert record["auction"]["winner_strategy"] == "MALAYSIAN_SNR"
    assert record["auction"]["winner_score"] == 85.5
    assert record["auction"]["cross_strategy_confluence"] is True

