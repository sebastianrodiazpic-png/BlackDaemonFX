import pandas as pd

from strategy.smc.confirmation_engine import M5ConfirmationConfig, evaluate_m5_confirmation


def _data():
    rows = [
        ("2026-01-01 00:00", 100, 101, 99, 100.5),
        ("2026-01-01 00:05", 100.5, 101, 99.5, 100),
        ("2026-01-01 00:10", 100, 100.4, 99.2, 99.8),  # retest with lower wick
        ("2026-01-01 00:15", 99.8, 102.5, 99.7, 102.3),  # displacement + micro BOS
    ]
    return pd.DataFrame(rows, columns=["time", "open", "high", "low", "close"]).assign(time=lambda x: pd.to_datetime(x.time, utc=True))


def _setup(df):
    return pd.Series({
        "setup_time": df.iloc[1]["time"], "ob_low": 99.0, "ob_high": 101.0,
        "trend_ok": True, "sweep_ok": True, "structure_break_ok": True,
        "premium_discount_ok": True,
    })


def test_high_quality_long_confirmation_is_accepted():
    df = _data()
    result = evaluate_m5_confirmation(
        data=df, setup=_setup(df), retest_index=2, confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=70, require_chart_pattern=False, require_fvg=False,
        ),
    )
    assert result["confirmation_valid"] is True
    assert result["trade_score"] >= 80
    assert result["trade_grade"] in {"A", "A+"}
    assert result["confirmations"]["displacement"] is True
    assert result["confirmations"]["micro_structure"] is True


def test_repeated_order_block_touch_is_rejected():
    df = _data()
    df.loc[2, ["low", "high"]] = [99.5, 100.5]
    result = evaluate_m5_confirmation(
        data=df, setup=_setup(df), retest_index=2, confirmation_index=3,
        direction="long", config=M5ConfirmationConfig(max_ob_touches=0, minimum_trade_score=0),
    )
    assert result["confirmation_valid"] is False
    assert "ORDER_BLOCK_NOT_FRESH" in result["rejection_reasons"]


def test_adaptive_75_mode_accepts_when_only_secondary_confirmation_is_missing():
    df = _data()
    result = evaluate_m5_confirmation(
        data=df,
        setup=_setup(df),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=85,
            require_harmonic=True,
            adaptive_confirmation_enabled=True,
            minimum_confirmation_ratio=0.75,
            minimum_viable_trade_score=75,
            require_chart_pattern=False,
            require_fvg=False,
        ),
    )
    assert result["confirmation_percentage"] >= 75.0
    assert result["critical_confirmations_ok"] is True
    assert result["confirmation_valid"] is True
    assert result["confirmation_decision"] in {"STRICT_CONFIRMED", "ADAPTIVE_75_CONFIRMED"}
    if not result["confirmations"]["harmonic_confirmation"]:
        assert result["confirmation_decision"] == "ADAPTIVE_75_CONFIRMED"
        assert "harmonic_confirmation" in result["missing_confirmations"]


def test_adaptive_75_mode_never_overrides_a_critical_smc_failure():
    df = _data()
    setup = _setup(df)
    setup["premium_discount_ok"] = False
    result = evaluate_m5_confirmation(
        data=df,
        setup=setup,
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=0,
            adaptive_confirmation_enabled=True,
            minimum_confirmation_ratio=0.75,
            minimum_viable_trade_score=0,
        ),
    )
    assert result["confirmation_percentage"] >= 75.0
    assert result["critical_confirmations_ok"] is False
    assert "premium_discount" in result["critical_confirmation_failures"]
    assert result["confirmation_valid"] is False
    assert result["confirmation_decision"] == "REJECTED"
    assert "CRITICAL_CONFIRMATION_MISSING" in result["rejection_reasons"]


def test_default_adaptive_confirmation_threshold_is_80_percent():
    config = M5ConfirmationConfig()
    assert config.minimum_confirmation_ratio == 0.80


def test_adaptive_80_decision_code_reflects_current_threshold():
    df = _data()
    result = evaluate_m5_confirmation(
        data=df,
        setup=_setup(df),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=85,
            require_harmonic=True,
            adaptive_confirmation_enabled=True,
            minimum_confirmation_ratio=0.80,
            minimum_viable_trade_score=75,
            require_chart_pattern=False,
            require_fvg=False,
        ),
    )
    assert result["confirmation_percentage"] >= 80.0
    assert result["confirmation_valid"] is True
    if not result["confirmations"]["harmonic_confirmation"]:
        assert result["confirmation_decision"] == "ADAPTIVE_80_CONFIRMED"
