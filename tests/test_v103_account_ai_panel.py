"""v103: panel de meta-etiquetado con IA en la pantalla Cuenta activa."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dashboard.account_metrics import build_account_payload  # noqa: E402
from dashboard.account_page import ACCOUNT_HTML  # noqa: E402


class _Repo:
    """Repositorio mínimo que sólo expone el resumen de meta-etiquetado."""

    def __init__(self, summary=None, raises=False):
        self._summary = summary
        self._raises = raises
        self.received_source = None

    def meta_label_decision_summary(self, *, source=None):
        self.received_source = source
        if self._raises:
            raise RuntimeError("bitacora no disponible")
        return self._summary


def _payload(repo):
    return build_account_payload(repo, source="DEMO")


class TestAccountPayload:
    def test_summary_is_exposed_and_scoped_to_source(self):
        repo = _Repo({"analyzed_total": 7, "shadow_scored": 7})
        payload = _payload(repo)
        assert payload["meta_labeling"]["analyzed_total"] == 7
        assert repo.received_source == "DEMO"

    def test_persistence_documents_the_audit_origin(self):
        payload = _payload(_Repo({"analyzed_total": 0}))
        assert (
            payload["persistence"]["meta_labeling"]
            == "daemon_audit_events.META_LABEL_SIGNAL_SCORED"
        )

    def test_summary_failure_never_breaks_the_account_page(self):
        payload = _payload(_Repo(raises=True))
        assert "error" in payload["meta_labeling"]
        # El resto del payload sigue construyéndose.
        assert "stats" in payload

    def test_repository_without_support_is_tolerated(self):
        payload = build_account_payload(object(), source="DEMO")
        assert payload["meta_labeling"] is None


class TestSummaryAggregation:
    """Verifica la agregación real contra una base SQLite temporal."""

    def _repository(self, tmp_path):
        from database.repository import TradingRepository

        return TradingRepository(tmp_path / "audit.db")

    def _score(self, repo, **decision):
        base = {
            "worker": "FLIP", "strategy_name": "SMC", "mode": "SHADOW",
            "probability": 0.0, "net_expectancy_r": 0.0, "allowed": True,
            "shadow": True, "trained": False, "reason": "SHADOW",
        }
        base.update(decision)
        repo.save_audit_event(
            "META_LABEL_SIGNAL_SCORED",
            source="DEMO",
            instrument="Volatility 75 Index",
            payload={"meta_label": base},
        )

    def test_counts_shadow_allowed_and_rejected_separately(self, tmp_path):
        repo = self._repository(tmp_path)
        self._score(repo)
        self._score(repo, mode="FILTER", shadow=False, allowed=True, trained=True,
                    probability=0.8, net_expectancy_r=0.5)
        self._score(repo, mode="FILTER", shadow=False, allowed=False, trained=True,
                    probability=0.2, net_expectancy_r=-0.3,
                    reason="PROBABILITY_BELOW_THRESHOLD")

        summary = repo.meta_label_decision_summary(source="DEMO")
        assert summary["analyzed_total"] == 3
        assert summary["shadow_scored"] == 1
        assert summary["filter_allowed"] == 1
        assert summary["filter_rejected"] == 1
        assert summary["rejection_reasons"][0]["reason"] == "PROBABILITY_BELOW_THRESHOLD"

    def test_averages_ignore_untrained_placeholder_zeros(self, tmp_path):
        repo = self._repository(tmp_path)
        # Una decisión sin modelo reporta 0.0 por convención; promediarla
        # hundiría la probabilidad media mostrada al usuario.
        self._score(repo, trained=False, probability=0.0)
        self._score(repo, trained=True, probability=0.9, net_expectancy_r=0.6)

        summary = repo.meta_label_decision_summary(source="DEMO")
        assert summary["trained_decisions"] == 1
        assert summary["untrained_decisions"] == 1
        assert summary["average_probability"] == pytest.approx(0.9)
        assert summary["average_net_expectancy_r"] == pytest.approx(0.6)

    def test_no_events_returns_empty_summary(self, tmp_path):
        summary = self._repository(tmp_path).meta_label_decision_summary(source="DEMO")
        assert summary["analyzed_total"] == 0
        assert summary["average_probability"] is None
        assert summary["by_worker"] == []

    def test_workers_are_reported_independently(self, tmp_path):
        repo = self._repository(tmp_path)
        self._score(repo, worker="FLIP")
        self._score(repo, worker="BOOM")
        self._score(repo, worker="BOOM")

        workers = {w["worker"]: w for w in repo.meta_label_decision_summary()["by_worker"]}
        assert workers["BOOM"]["analyzed"] == 2
        assert workers["FLIP"]["analyzed"] == 1

    def test_last_training_timestamp_is_reported(self, tmp_path):
        repo = self._repository(tmp_path)
        repo.save_audit_event(
            "META_LABEL_MODEL_TRAINED", source="DEMO",
            payload={"trained": True, "worker": "FLIP"},
        )
        assert repo.meta_label_decision_summary()["last_trained_at"] is not None

    def test_untrained_training_run_is_not_reported_as_trained(self, tmp_path):
        repo = self._repository(tmp_path)
        repo.save_audit_event(
            "META_LABEL_MODEL_TRAINED", source="DEMO",
            payload={"trained": False, "reason": "INSUFFICIENT_HISTORY_FOR_TRAINING"},
        )
        assert repo.meta_label_decision_summary()["last_trained_at"] is None


class TestAccountPageMarkup:
    def test_panel_elements_exist(self):
        for element in (
            'id="aiTotal"', 'id="aiShadow"', 'id="aiRejected"',
            'id="aiProb"', 'id="aiExp"', 'id="aiMode"',
            'id="aiState"', 'id="aiImprovements"', 'id="aiWorkers"',
        ):
            assert element in ACCOUNT_HTML

    def test_render_invokes_the_ai_panel(self):
        assert "renderAI(a.meta_labeling)" in ACCOUNT_HTML
        assert "function renderAI(" in ACCOUNT_HTML
        assert "function aiImprovements(" in ACCOUNT_HTML

    def test_panel_states_shadow_mode_does_not_block(self):
        assert "sin bloquear ninguna entrada" in ACCOUNT_HTML


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
