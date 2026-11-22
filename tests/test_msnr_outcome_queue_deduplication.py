"""Tests unitarios para la cola de observaciones de desenlaces MSNR con ampliación de tamaño y desduplicación."""
import os
import queue
import time
from unittest.mock import Mock, patch
import pytest

from strategy.malaysian_snr.candidate_audit import schedule_outcomes


def test_schedule_outcomes_default_maxsize_and_custom_env():
    """Verifica que el maxsize por defecto sea 256 y sea configurable por variable de entorno."""
    engine = Mock()
    engine._msnr_outcome_jobs = None
    engine._msnr_outcome_pending_symbols = None
    engine._msnr_outcome_lock = None

    with patch.dict(os.environ, {"DAEMONBLACKFX_MSNR_OUTCOME_QUEUE_MAXSIZE": "512"}):
        with patch("threading.Thread"):
            schedule_outcomes(engine, "Step Index")
            assert engine._msnr_outcome_jobs.maxsize == 512

    engine2 = Mock()
    engine2._msnr_outcome_jobs = None
    engine2._msnr_outcome_pending_symbols = None
    engine2._msnr_outcome_lock = None

    with patch.dict(os.environ, {}, clear=False):
        if "DAEMONBLACKFX_MSNR_OUTCOME_QUEUE_MAXSIZE" in os.environ:
            del os.environ["DAEMONBLACKFX_MSNR_OUTCOME_QUEUE_MAXSIZE"]
        with patch("threading.Thread"):
            schedule_outcomes(engine2, "Volatility 75 Index")
            assert engine2._msnr_outcome_jobs.maxsize == 256


def test_schedule_outcomes_deduplication_prevents_duplicate_entries():
    """Verifica que si un símbolo ya está en espera en la cola, no se vuelva a encolar."""
    engine = Mock()
    engine._msnr_outcome_jobs = None
    engine._msnr_outcome_pending_symbols = None
    engine._msnr_outcome_lock = None

    # Mockeamos el thread para que no consuma inmediatamente de la cola
    with patch("threading.Thread"):
        schedule_outcomes(engine, "Crash 500 Index")
        assert engine._msnr_outcome_jobs.qsize() == 1
        assert "Crash 500 Index" in engine._msnr_outcome_pending_symbols

        # Intentar encolar el mismo símbolo otra vez mientras sigue en espera
        schedule_outcomes(engine, "Crash 500 Index")
        # El qsize debe seguir siendo 1 (desduplicado)
        assert engine._msnr_outcome_jobs.qsize() == 1

        # Encolar otro símbolo diferente
        schedule_outcomes(engine, "Boom 1000 Index")
        assert engine._msnr_outcome_jobs.qsize() == 2
        assert "Boom 1000 Index" in engine._msnr_outcome_pending_symbols


def test_schedule_outcomes_queue_full_graceful_handling():
    """Verifica que si la cola llega a desbordarse, se persista el evento MSNR_OUTCOME_QUEUE_FULL limpiamente."""
    engine = Mock()
    engine._msnr_outcome_jobs = None
    engine._msnr_outcome_pending_symbols = None
    engine._msnr_outcome_lock = None
    events = []
    engine._persist_audit_event = lambda event_type, instrument, action, reason: events.append(
        (event_type, instrument, action, reason)
    )

    with patch.dict(os.environ, {"DAEMONBLACKFX_MSNR_OUTCOME_QUEUE_MAXSIZE": "2"}):
        with patch("threading.Thread"):
            schedule_outcomes(engine, "SymbolA")
            schedule_outcomes(engine, "SymbolB")
            assert engine._msnr_outcome_jobs.qsize() == 2

            # Tercer símbolo debe desbordar la cola de tamaño 2
            schedule_outcomes(engine, "SymbolC")
            assert len(events) == 1
            assert events[0][0] == "MSNR_OUTCOME_QUEUE_FULL"
            assert events[0][1] == "SymbolC"
            assert "SymbolC" not in engine._msnr_outcome_pending_symbols
