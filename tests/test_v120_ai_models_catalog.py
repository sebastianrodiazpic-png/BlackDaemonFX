"""Tests para el catálogo completo de modelos de IA en la pantalla /Account (v120)."""

from __future__ import annotations

import pytest
from pathlib import Path
from strategy.ai.model_inventory import scan_trained_models_catalog, classify_worker_family
from dashboard.account_metrics import build_account_payload
from dashboard.account_page import ACCOUNT_HTML


def test_classify_worker_family():
    assert classify_worker_family("BOOM") == "SINTETICOS"
    assert classify_worker_family("VOLATILITY_2") == "SINTETICOS"
    assert classify_worker_family("CRASH_1000") == "SINTETICOS"
    assert classify_worker_family("FOREX_1") == "FOREX"
    assert classify_worker_family("GOLD") == "COMMODITIES"
    assert classify_worker_family("ORB") == "INDICES"
    assert classify_worker_family("MALAYSIAN_SNR") == "MALAYSIAN_SNR"
    assert classify_worker_family("GLOBAL") == "GLOBAL"


def test_scan_trained_models_catalog_finds_all_models():
    catalog = scan_trained_models_catalog()
    assert len(catalog) >= 17

    workers = {m["worker"] for m in catalog}
    expected_workers = {
        "BOOM", "CRASH", "FLIP", "FOREX", "GLOBAL",
        "GOLD", "JUMP", "MALAYSIAN_SNR", "ORB", "STEP",
        "SYNTHETICS", "VOLATILITY", "VOLATILITY_2"
    }
    for w in expected_workers:
        assert w in workers, f"Worker esperado {w} no encontrado en el catálogo"

    for model in catalog:
        assert model["trained"] is True
        assert model["samples"] is not None
        assert "filename" in model
        assert "family" in model
        assert model["status"] == "MODELO ENTRENADO Y ACTIVO"


def test_account_payload_includes_full_ai_models_catalog():
    class DummyRepo:
        def meta_label_decision_summary(self, source=None):
            return {
                "analyzed_total": 500,
                "shadow_scored": 500,
                "filter_allowed": 0,
                "filter_rejected": 0,
                "trained_decisions": 500,
                "untrained_decisions": 0,
                "average_probability": 0.742,
                "average_net_expectancy_r": 0.90,
                "by_worker": [
                    {"worker": "MALAYSIAN_SNR", "analyzed": 497, "shadow": 497, "allowed": 0, "rejected": 0, "trained": True},
                    {"worker": "CRASH", "analyzed": 2, "shadow": 2, "allowed": 0, "rejected": 0, "trained": True},
                    {"worker": "VOLATILITY_1", "analyzed": 1, "shadow": 1, "allowed": 0, "rejected": 0, "trained": True},
                ],
                "rejection_reasons": [],
                "last_trained_at": "2026-10-03T03:34:40+00:00",
                "recent_decisions": [],
            }

    payload = build_account_payload(DummyRepo(), source="DEMO")
    meta = payload["meta_labeling"]

    assert meta is not None
    assert "models_catalog" in meta
    assert len(meta["models_catalog"]) >= 17
    assert meta["models_count"] == len(meta["models_catalog"])

    workers_in_payload = {w["worker"]: w for w in meta["by_worker"]}
    assert "MALAYSIAN_SNR" in workers_in_payload
    assert "CRASH" in workers_in_payload
    assert "VOLATILITY_1" in workers_in_payload

    # Ahora workers que antes estaban excluidos por el límite de 500 o falta de trades en vivo están presentes
    assert "BOOM" in workers_in_payload
    assert "FOREX" in workers_in_payload
    assert "GOLD" in workers_in_payload
    assert "STEP" in workers_in_payload
    assert "JUMP" in workers_in_payload
    assert "ORB" in workers_in_payload

    assert workers_in_payload["BOOM"]["trained"] is True
    assert workers_in_payload["BOOM"]["in_disk"] is True
    assert workers_in_payload["BOOM"]["model_samples"] >= 50


def test_account_page_contains_catalog_markup_and_filters():
    assert 'id="aiWorkerSearch"' in ACCOUNT_HTML
    assert 'id="aiModelsCount"' in ACCOUNT_HTML
    assert 'filterAIWorkers()' in ACCOUNT_HTML
    assert 'setAIFilter(' in ACCOUNT_HTML
    assert 'renderAIWorkersFiltered()' in ACCOUNT_HTML
    assert 'Catálogo de Modelos de IA y Cobertura' in ACCOUNT_HTML
