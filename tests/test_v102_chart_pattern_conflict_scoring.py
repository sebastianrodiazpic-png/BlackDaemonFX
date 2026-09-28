"""v102: el conflicto chartista debe reflejarse siempre en el trade_score.

Dos defectos corregidos:
1. La penalización se restaba antes del recorte a 100. Como los pesos suman 110
   y el bonus añade 8, existían ~18 puntos de holgura donde el castigo era
   invisible justo en los setups más fuertes.
2. Un patrón contrario más fuerte por menos de 5 puntos se clasificaba como
   FUERZAS_SIMILARES en lugar de CONTRA_MAS_FUERTE, evitando el bloqueo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import strategy.smc.confirmation_engine as confirmation_module  # noqa: E402
from strategy.smc.chart_patterns import _explain_chart_pattern_conflict  # noqa: E402
from strategy.smc.confirmation_engine import (  # noqa: E402
    M5ConfirmationConfig,
    evaluate_m5_confirmation,
)


def _m5_data():
    rows = [
        ("2026-01-01 00:00", 100, 101, 99, 100.5),
        ("2026-01-01 00:05", 100.5, 101, 99.5, 100),
        ("2026-01-01 00:10", 100, 100.4, 99.2, 99.8),
        ("2026-01-01 00:15", 99.8, 102.5, 99.7, 102.3),
    ]
    frame = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close"])
    frame["time"] = pd.to_datetime(frame["time"], utc=True)
    return frame


def _setup(frame):
    return pd.Series({
        "setup_time": frame.iloc[1]["time"],
        "ob_low": 99.0,
        "ob_high": 101.0,
        "trend_ok": True,
        "sweep_ok": True,
        "structure_break_ok": True,
        "premium_discount_ok": True,
    })


def _evaluate(monkeypatch, chart_pattern, **config_kwargs):
    frame = _m5_data()
    monkeypatch.setattr(
        confirmation_module,
        "detect_chart_pattern_confirmation",
        lambda *_a, **_k: chart_pattern,
    )
    return evaluate_m5_confirmation(
        data=frame,
        setup=_setup(frame),
        retest_index=2,
        confirmation_index=3,
        direction="long",
        config=M5ConfirmationConfig(
            minimum_trade_score=70,
            require_fvg=False,
            block_similar_chart_pattern_forces=False,
            **config_kwargs,
        ),
    )


def _conflict_pattern(level="FUERZAS_SIMILARES"):
    return {
        "chart_pattern_confirmed": True,
        "chart_pattern_conflict": True,
        "chart_pattern_conflict_level": level,
        "chart_pattern_strength": 0.72,
        "chart_pattern_bonus": 8.0,
    }


def _clean_pattern():
    return {
        "chart_pattern_confirmed": True,
        "chart_pattern_conflict": False,
        "chart_pattern_conflict_level": "NONE",
        "chart_pattern_strength": 0.72,
        "chart_pattern_bonus": 8.0,
    }


class TestConflictClassification:
    def test_stronger_contra_is_never_classified_as_similar(self):
        supporting = {"pattern": "ROUNDING_BOTTOM", "direction": "BUY", "strength": 0.72}
        conflicting = {"pattern": "ASCENDING_BROADENING_WEDGE", "direction": "SELL", "strength": 0.74}
        level, reason, delta = _explain_chart_pattern_conflict(supporting, conflicting, "BUY")
        assert level == "CONTRA_MAS_FUERTE"
        assert delta == pytest.approx(0.02)
        assert "más fuerte" in reason

    def test_exact_tie_remains_similar_forces(self):
        supporting = {"pattern": "A", "direction": "BUY", "strength": 0.72}
        conflicting = {"pattern": "B", "direction": "SELL", "strength": 0.72}
        level, _, _ = _explain_chart_pattern_conflict(supporting, conflicting, "BUY")
        assert level == "FUERZAS_SIMILARES"

    def test_narrow_aligned_advantage_is_still_similar(self):
        supporting = {"pattern": "A", "direction": "BUY", "strength": 0.72}
        conflicting = {"pattern": "B", "direction": "SELL", "strength": 0.69}
        level, _, _ = _explain_chart_pattern_conflict(supporting, conflicting, "BUY")
        assert level == "FUERZAS_SIMILARES"

    def test_dominant_aligned_pattern_is_secondary_conflict(self):
        supporting = {"pattern": "A", "direction": "BUY", "strength": 0.72}
        conflicting = {"pattern": "B", "direction": "SELL", "strength": 0.50}
        level, _, _ = _explain_chart_pattern_conflict(supporting, conflicting, "BUY")
        assert level == "CONTRA_SECUNDARIO"

    def test_missing_aligned_pattern_is_dominant_contra(self):
        conflicting = {"pattern": "B", "direction": "SELL", "strength": 0.60}
        level, _, _ = _explain_chart_pattern_conflict(None, conflicting, "BUY")
        assert level == "DOMINANT_CONTRA"


class TestPenaltyReachesVisibleScore:
    def test_conflict_lowers_score_below_perfect_setup(self, monkeypatch):
        clean = _evaluate(monkeypatch, _clean_pattern())
        conflicted = _evaluate(monkeypatch, _conflict_pattern())

        assert conflicted["chart_pattern_conflict_penalty"] == 10.0
        # El defecto original devolvía 100.0 en ambos casos.
        assert conflicted["trade_score"] < clean["trade_score"]
        assert conflicted["trade_score"] == pytest.approx(clean["trade_score"] - 10.0)

    def test_saturated_setup_no_longer_hides_the_penalty(self, monkeypatch):
        conflicted = _evaluate(monkeypatch, _conflict_pattern())
        # raw_trade_score conserva el bruto sin penalizar para auditoría.
        assert conflicted["raw_trade_score"] > 100.0
        # Antes de la corrección el recorte a 100 absorbía los 10 puntos.
        assert conflicted["trade_score"] == 90.0

    def test_clean_setup_keeps_full_score(self, monkeypatch):
        clean = _evaluate(monkeypatch, _clean_pattern())
        assert clean["chart_pattern_conflict_penalty"] == 0.0
        assert clean["trade_score"] == 100.0

    def test_score_never_goes_negative(self, monkeypatch):
        conflicted = _evaluate(
            monkeypatch,
            _conflict_pattern(),
            chart_pattern_secondary_conflict_penalty=500.0,
        )
        assert conflicted["trade_score"] == 0.0

    def test_narrow_conflict_is_penalty_instead_of_gate_failure(self, monkeypatch):
        blocked = _evaluate(monkeypatch, _conflict_pattern(level="CONTRA_MAS_FUERTE"))
        assert blocked["chart_pattern_conflict_blocked"] is False
        assert blocked["chart_pattern_conflict_penalty"] > 0.0
        assert "MATERIAL_CHART_PATTERN_CONFLICT" not in blocked["structural_gate_failures"]

    def test_dominant_strong_contrary_pattern_remains_structural_gate(self, monkeypatch):
        pattern = _conflict_pattern(level="DOMINANT_CONTRA")
        pattern.update({
            "chart_pattern_supporting_strength": 0.70,
            "chart_pattern_conflicting_strength": 0.85,
            "chart_pattern_conflict_strength_delta": 0.15,
        })
        blocked = _evaluate(monkeypatch, pattern)
        assert blocked["chart_pattern_conflict_blocked"] is True
        assert "MATERIAL_CHART_PATTERN_CONFLICT" in blocked["structural_gate_failures"]


class TestRegressionOfReportedTrade:
    def test_reported_entry_would_no_longer_score_a_plus(self, monkeypatch):
        """ROUNDING_BOTTOM 72% BUY vs ASCENDING_BROADENING_WEDGE 74% SELL."""
        level, _, _ = _explain_chart_pattern_conflict(
            {"pattern": "ROUNDING_BOTTOM", "direction": "BUY", "strength": 0.72},
            {"pattern": "ASCENDING_BROADENING_WEDGE", "direction": "SELL", "strength": 0.74},
            "BUY",
        )
        assert level == "CONTRA_MAS_FUERTE"

        result = _evaluate(monkeypatch, _conflict_pattern(level=level))
        assert result["chart_pattern_conflict_blocked"] is False
        assert result["chart_pattern_conflict_penalty"] > 0.0
        assert "MATERIAL_CHART_PATTERN_CONFLICT" not in result["structural_gate_failures"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
