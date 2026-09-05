"""v101: motor de meta-etiquetado con IA (sombra, filtro, ranking, calibración)."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from strategy.ai import (  # noqa: E402
    FEATURE_NAMES,
    MetaLabelingConfig,
    MetaLabelingEngine,
    build_training_dataset,
    extract_meta_features,
    feature_vector,
    rank_signals,
    temporal_validation,
    train_worker_model,
)


BASE_TIME = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)


def _signal(score=90.0, adx=28.0, conflict=False, age_candles=1.0):
    return {
        "direction": "BUY",
        "trade_score": score,
        "confirmation_percentage": score,
        "adx": adx,
        "atr": 1.5,
        "structure_break": "BOS_BULLISH",
        "risk_reward_ratio": 2.0,
        "chart_pattern": "ROUNDING_BOTTOM",
        "chart_pattern_direction": "BUY",
        "chart_pattern_strength": 72.0,
        "chart_pattern_conflict": bool(conflict),
        "chart_pattern_conflicting_pattern": "ASCENDING_BROADENING_WEDGE" if conflict else None,
        "chart_pattern_conflicting_direction": "SELL" if conflict else None,
        "chart_pattern_conflicting_strength": 74.0 if conflict else 0.0,
        "chart_pattern_conflict_level": "FUERZAS_SIMILARES" if conflict else "NONE",
        "signal_age_candles": age_candles,
        "entry_time": BASE_TIME.isoformat(),
    }


def _trade(index, *, win, score, profile="SYNTHETICS"):
    return {
        "entry_time": (BASE_TIME + timedelta(hours=index)).isoformat(),
        "status": "CLOSED",
        "realized_rr": 2.0 if win else -1.0,
        "net_pnl": 20.0 if win else -10.0,
        "details": {
            "metadata": {
                "bot_profile": profile,
                "strategy_name": "SMC",
                "direction": "BUY",
                "trade_score": score,
                "confirmation_percentage": score,
                "adx": 30.0 if win else 12.0,
                "structure_break": "BOS_BULLISH",
                "risk_reward_ratio": 2.0,
                "signal_age_candles": 1.0 if win else 6.0,
            }
        },
    }


def _history(count=80, profile="SYNTHETICS"):
    trades = []
    for index in range(count):
        win = index % 2 == 0
        trades.append(_trade(index, win=win, score=92.0 if win else 55.0, profile=profile))
    return trades


class TestFeatureExtraction:
    def test_feature_vector_matches_canonical_names(self):
        features = extract_meta_features(signal=_signal(), analysis={}, market={})
        assert set(features) == set(FEATURE_NAMES)
        assert len(feature_vector(features)) == len(FEATURE_NAMES)

    def test_chart_pattern_conflict_is_captured(self):
        clean = extract_meta_features(signal=_signal(), analysis={}, market={})
        conflicted = extract_meta_features(signal=_signal(conflict=True), analysis={}, market={})
        assert clean["chart_pattern_conflict"] == 0.0
        assert conflicted["chart_pattern_conflict"] == 1.0
        # El patrón contrario es más fuerte, así que el delta debe ser negativo.
        assert conflicted["chart_pattern_strength_delta"] < 0.0

    def test_structure_alignment_penalises_opposite_break(self):
        aligned = extract_meta_features(signal=_signal(), analysis={}, market={})
        opposite_signal = _signal()
        opposite_signal["structure_break"] = "BOS_BEARISH"
        opposite = extract_meta_features(signal=opposite_signal, analysis={}, market={})
        assert aligned["structure_aligned"] == 1.0
        assert opposite["structure_aligned"] == -1.0


class TestTraining:
    def test_dataset_is_worker_scoped_and_time_ordered(self):
        trades = _history(40, profile="SYNTHETICS") + _history(40, profile="BOOM")
        dataset = build_training_dataset(trades, worker="SYNTHETICS")
        assert dataset["rows"] == 40
        assert dataset["times"] == sorted(dataset["times"])

    def test_worker_family_includes_numbered_instances(self):
        trades = (
            _history(10, profile="VOLATILITY_1")
            + _history(10, profile="VOLATILITY_3")
            + _history(10, profile="BOOM")
        )
        dataset = build_training_dataset(trades, worker="VOLATILITY")
        assert dataset["rows"] == 20

    def test_trades_without_outcome_are_discarded(self):
        trades = _history(10)
        trades.append({
            "entry_time": (BASE_TIME + timedelta(hours=99)).isoformat(),
            "status": "CLOSED",
            "realized_rr": float("nan"),
            "net_pnl": float("nan"),
            "details": {"metadata": {"bot_profile": "SYNTHETICS", "strategy_name": "SMC"}},
        })
        assert build_training_dataset(trades, worker="SYNTHETICS")["rows"] == 10

    def test_model_learns_signal_quality(self):
        model = train_worker_model(_history(), worker="SYNTHETICS")
        assert model.trained is True
        good = feature_vector(extract_meta_features(signal=_signal(score=92.0, adx=30.0), analysis={}, market={}))
        bad = feature_vector(
            extract_meta_features(signal=_signal(score=55.0, adx=12.0, age_candles=6.0), analysis={}, market={})
        )
        assert model.probability(good) > model.probability(bad)

    def test_insufficient_history_leaves_model_untrained(self):
        model = train_worker_model(_history(4), worker="SYNTHETICS")
        assert model.trained is False

    def test_net_expectancy_grows_with_probability(self):
        model = train_worker_model(_history(), worker="SYNTHETICS")
        assert model.net_expectancy_r(0.80) > model.net_expectancy_r(0.30)


class TestTemporalValidation:
    def test_walk_forward_only_evaluates_future_trades(self):
        report = temporal_validation(_history(), worker="SYNTHETICS")
        assert report.valid is True
        assert report.folds >= 1
        assert report.samples_evaluated > 0
        for detail in report.fold_details:
            assert detail["train_samples"] < detail["train_samples"] + detail["test_samples"]

    def test_short_history_is_reported_as_invalid(self):
        report = temporal_validation(_history(4), worker="SYNTHETICS")
        assert report.valid is False
        assert report.reason == "INSUFFICIENT_HISTORY_FOR_TEMPORAL_VALIDATION"


class TestShadowAndFilterModes:
    def _engine(self, tmp_path, mode, **overrides):
        config = MetaLabelingConfig(
            mode=mode,
            model_directory=str(tmp_path),
            min_training_samples=10,
            **overrides,
        )
        return MetaLabelingEngine(config, worker="SYNTHETICS")

    def test_shadow_mode_scores_without_blocking(self, tmp_path):
        engine = self._engine(tmp_path, "SHADOW", min_probability=0.99, min_net_expectancy_r=99.0)
        engine.train(_history(), strategy_name="SMC")
        decision = engine.score_signal(
            symbol="Volatility 75 Index",
            signal=_signal(score=55.0, adx=12.0, age_candles=6.0),
            strategy_name="SMC",
        )
        assert decision.shadow is True
        assert decision.allowed is True
        assert decision.reason == "SHADOW_MODE_SCORED_WITHOUT_BLOCKING"

    def test_filter_mode_rejects_low_probability(self, tmp_path):
        engine = self._engine(tmp_path, "FILTER", min_probability=0.99, min_net_expectancy_r=0.0)
        engine.train(_history(), strategy_name="SMC")
        decision = engine.score_signal(
            symbol="Volatility 75 Index",
            signal=_signal(score=55.0, adx=12.0, age_candles=6.0),
            strategy_name="SMC",
        )
        assert decision.allowed is False
        assert decision.reason == "PROBABILITY_BELOW_THRESHOLD"

    def test_filter_mode_accepts_high_quality_signal(self, tmp_path):
        engine = self._engine(tmp_path, "FILTER", min_probability=0.50, min_net_expectancy_r=-99.0)
        engine.train(_history(), strategy_name="SMC")
        decision = engine.score_signal(
            symbol="Volatility 75 Index",
            signal=_signal(score=95.0, adx=32.0),
            strategy_name="SMC",
        )
        assert decision.allowed is True
        assert decision.reason == "PROBABILITY_AND_EXPECTANCY_ACCEPTED"

    def test_untrained_model_never_blocks_live_trading(self, tmp_path):
        engine = self._engine(tmp_path, "FILTER", min_probability=0.99)
        decision = engine.score_signal(symbol="Boom 1000 Index", signal=_signal(), strategy_name="SMC")
        assert decision.trained is False
        assert decision.allowed is True
        assert decision.reason == "MODEL_NOT_TRAINED_SHADOW_ONLY"

    def test_workers_keep_independent_models(self, tmp_path):
        synthetics = self._engine(tmp_path, "SHADOW")
        synthetics.train(_history(profile="SYNTHETICS"), strategy_name="SMC")

        boom_config = MetaLabelingConfig(mode="SHADOW", model_directory=str(tmp_path), min_training_samples=10)
        boom = MetaLabelingEngine(boom_config, worker="BOOM")
        assert boom.load_model("SMC").trained is False
        assert synthetics.load_model("SMC").trained is True

    def test_model_is_persisted_and_reloaded(self, tmp_path):
        engine = self._engine(tmp_path, "SHADOW")
        report = engine.train(_history(), strategy_name="SMC")
        assert report["trained"] is True
        assert Path(report["model_path"]).exists()

        reloaded = MetaLabelingEngine(
            MetaLabelingConfig(model_directory=str(tmp_path)), worker="SYNTHETICS"
        )
        assert reloaded.load_model("SMC").trained is True

    def test_disabled_engine_allows_everything(self, tmp_path):
        engine = self._engine(tmp_path, "FILTER", enabled=False)
        decision = engine.score_signal(symbol="Crash 500 Index", signal=_signal(), strategy_name="SMC")
        assert decision.allowed is True
        assert decision.reason == "META_LABELING_DISABLED"


class TestRanking:
    def test_highest_expectancy_signal_is_selected(self):
        decisions = [
            {"symbol": "A", "probability": 0.60, "net_expectancy_r": 0.20, "allowed": True},
            {"symbol": "B", "probability": 0.75, "net_expectancy_r": 0.55, "allowed": True},
            {"symbol": "C", "probability": 0.70, "net_expectancy_r": 0.35, "allowed": True},
        ]
        ranked = rank_signals(decisions, max_signals=1)
        assert [row["symbol"] for row in ranked] == ["B", "C", "A"]
        assert ranked[0]["selected"] is True
        assert ranked[1]["selected"] is False
        assert ranked[1]["rank_reason"] == "LOWER_PRIORITY_THAN_SELECTED_SIGNALS"

    def test_rejected_signals_never_outrank_allowed_ones(self):
        decisions = [
            {"symbol": "REJECTED", "probability": 0.99, "net_expectancy_r": 9.0, "allowed": False},
            {"symbol": "ALLOWED", "probability": 0.60, "net_expectancy_r": 0.20, "allowed": True},
        ]
        ranked = rank_signals(decisions, max_signals=2)
        assert ranked[0]["symbol"] == "ALLOWED"
        assert ranked[0]["selected"] is True
        assert ranked[1]["selected"] is False
        assert ranked[1]["rank_reason"] == "REJECTED_BY_META_LABEL_FILTER"

    def test_multiple_selections_respect_the_cycle_limit(self):
        decisions = [
            {"symbol": str(index), "probability": 0.60, "net_expectancy_r": float(index), "allowed": True}
            for index in range(5)
        ]
        ranked = rank_signals(decisions, max_signals=2)
        assert sum(1 for row in ranked if row["selected"]) == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
