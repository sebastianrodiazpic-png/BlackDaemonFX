
import pandas as pd

from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation


def _base():
    rows = [
        ("2026-01-01 00:00", 100.0, 101.0, 99.0, 100.5),
        ("2026-01-01 00:05", 100.5, 101.0, 99.5, 100.0),
        ("2026-01-01 00:10", 99.9, 100.2, 99.8, 100.1),
        ("2026-01-01 00:15", 100.0, 102.5, 99.9, 102.3),
    ]
    return pd.DataFrame(
        rows, columns=["time", "open", "high", "low", "close"]
    ).assign(time=lambda x: pd.to_datetime(x.time, utc=True))


def _setup(df, structure):
    return pd.Series({
        "setup_time": df.iloc[1]["time"],
        "ob_low": 99.0,
        "ob_high": 101.0,
        "trend_ok": True,
        "sweep_ok": True,
        "structure_break_ok": True,
        "premium_discount_ok": True,
        "structure_break_type": structure,
    })


def test_bos_cannot_be_saved_by_adaptive_score_without_rejection():
    df = _base()
    # Retest con wick inferior pequeño (<30%) => no hay rechazo.
    result = evaluate_m5_confirmation(
        data=df,
        setup=_setup(df, "bos_bullish"),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=0,
            minimum_viable_trade_score=0,
            minimum_confirmation_ratio=0.75,
            adaptive_confirmation_enabled=True,
        ),
    )
    assert result["confirmations"]["rejection"] is False
    assert result["confirmation_valid"] is False
    assert "BOS_REQUIRES_REJECTION" in result["critical_confirmation_failures"]
    assert "BOS_REJECTION_NOT_CONFIRMED" in result["rejection_reasons"]


def test_choch_cannot_be_saved_by_adaptive_score_without_microstructure():
    df = _base()
    # Confirmación alcista pero sin romper el máximo de las dos velas previas.
    df.loc[3, ["open", "high", "low", "close"]] = [100.0, 100.95, 99.9, 100.9]
    # Retest con wick suficiente para que el fallo específico sea microestructura.
    df.loc[2, ["open", "high", "low", "close"]] = [100.2, 100.3, 99.0, 100.1]

    result = evaluate_m5_confirmation(
        data=df,
        setup=_setup(df, "choch_bullish"),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=0,
            minimum_viable_trade_score=0,
            minimum_confirmation_ratio=0.70,
            adaptive_confirmation_enabled=True,
            require_displacement=False,
            require_strong_close=False,
        ),
    )
    assert result["confirmations"]["micro_structure"] is False
    assert result["confirmation_valid"] is False
    assert "CHOCH_REQUIRES_MICRO_STRUCTURE" in result["critical_confirmation_failures"]
    assert "CHOCH_MICRO_STRUCTURE_NOT_CONFIRMED" in result["rejection_reasons"]


def test_visible_trade_score_is_capped_at_100_but_raw_score_is_preserved():
    df = _base()
    # Setup sin structure_break_type para evaluar sólo calibración del score.
    setup = _setup(df, "")
    result = evaluate_m5_confirmation(
        data=df,
        setup=setup,
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=0,
            harmonic_bonus_points=20,
            divergence_bonus_points=20,
        ),
    )
    assert result["trade_score"] <= 100.0
    assert "raw_trade_score" in result
