import pytest
from unittest.mock import MagicMock
from strategy.ai.meta_labeling import MetaLabelingConfig, MetaLabelingEngine, MetaLabelDecision


def test_resolve_min_probability_split_adjustment():
    config = MetaLabelingConfig(
        min_probability=0.47,
        min_probability_volatility=0.47,
        min_probability_gold=0.55,
        min_probability_forex=0.55,
        split_tp1_min_probability=0.46,
        split_tp1_probability_adjustment_enabled=True,
    )
    engine = MetaLabelingEngine(config=config, worker="VOLATILITY_1")

    # 1. En entrada estándar (single / sin split), umbral base intacto
    prob_single_vol = engine.resolve_min_probability("Volatility 75 Index", is_split_tp1=False)
    assert prob_single_vol == 0.47

    prob_single_gold = engine.resolve_min_probability("XAUUSD", is_split_tp1=False)
    assert prob_single_gold == 0.55

    # 2. En entrada dividida (split TP1 1.0R / +0.5% neto), umbral adaptado
    prob_split_vol = engine.resolve_min_probability("Volatility 75 Index", is_split_tp1=True)
    assert prob_split_vol == 0.46

    prob_split_gold = engine.resolve_min_probability("XAUUSD", is_split_tp1=True)
    assert prob_split_gold == 0.50

    # 3. Con toggle desactivado, umbral permanece en el base
    config_disabled = MetaLabelingConfig(
        min_probability=0.47,
        split_tp1_probability_adjustment_enabled=False,
    )
    engine_disabled = MetaLabelingEngine(config=config_disabled, worker="VOLATILITY_1")
    assert engine_disabled.resolve_min_probability("Volatility 75 Index", is_split_tp1=True) == 0.47


def test_score_signal_split_tp1_allows_marginal_high_wr_trade():
    config = MetaLabelingConfig(
        enabled=True,
        mode="FILTER",
        min_probability=0.47,
        min_net_expectancy_r=0.01,
        split_tp1_min_probability=0.46,
        split_tp1_probability_adjustment_enabled=True,
    )
    engine = MetaLabelingEngine(config=config, worker="VOLATILITY_1")

    # Mockeamos el modelo cargado para que reporte probabilidad 0.465 y expectativa positiva
    mock_model = MagicMock()
    mock_model.trained = True
    mock_model.probability.return_value = 0.465
    mock_model.net_expectancy_r.return_value = 0.08
    engine.load_model = lambda strat: mock_model

    # Evaluación estándar: 0.465 < 0.47 -> Rechazada
    dec_single = engine.score_signal(
        symbol="Volatility 75 Index",
        signal={"risk_reward_ratio": 2.0},
        analysis={},
        market={},
        is_split_tp1=False,
    )
    assert dec_single.allowed is False
    assert dec_single.reason == "PROBABILITY_BELOW_THRESHOLD"

    # Evaluación split TP1: 0.465 >= 0.46 -> Aceptada con éxito
    dec_split = engine.score_signal(
        symbol="Volatility 75 Index",
        signal={"risk_reward_ratio": 2.0},
        analysis={},
        market={},
        is_split_tp1=True,
    )
    assert dec_split.allowed is True
    assert dec_split.reason == "PROBABILITY_AND_EXPECTANCY_ACCEPTED"
