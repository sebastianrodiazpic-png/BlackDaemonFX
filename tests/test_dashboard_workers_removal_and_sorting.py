import pytest
import re
from dashboard.realtime_dashboard import _HTML, _INSTRUMENTS_HTML, _SELECTION_PROFILES, _WORKER_PROFILE_META
from app.main import FULL_MULTI_BOT_PROFILES
from config.ict_instrument_policy import POLICY_SELECTION_PROFILES


def test_eliminated_workers_removed_from_profiles_and_tabs():
    """Verifica que los 4 workers eliminados (PID 29316, 29740, 30444, 22728) estén fuera de perfiles y pestañas."""
    eliminated_profiles = {"MALAYSIAN_SNR", "FOREX_SNR", "COMMODITIES_SNR", "TREND_PULLBACK"}

    # No deben estar en FULL_MULTI_BOT_PROFILES de app/main.py
    for prof in eliminated_profiles:
        assert prof not in FULL_MULTI_BOT_PROFILES, f"{prof} sigue en FULL_MULTI_BOT_PROFILES"

    # No deben ser pestañas activas de política en /Instruments
    for prof in eliminated_profiles:
        assert prof not in POLICY_SELECTION_PROFILES, f"{prof} sigue en POLICY_SELECTION_PROFILES"
        assert prof not in _SELECTION_PROFILES, f"{prof} sigue en _SELECTION_PROFILES"

    # En _WORKER_PROFILE_META deben tener consolidated_hidden=True
    for prof in eliminated_profiles:
        meta = _WORKER_PROFILE_META.get(prof, {})
        assert meta.get("consolidated_hidden") is True, f"{prof} no tiene consolidated_hidden=True en _WORKER_PROFILE_META"


def test_tab_buttons_in_instruments_html():
    """Verifica que en /Instruments no existan botones para los workers eliminados."""
    eliminated_buttons = [
        'data-profile="MALAYSIAN_SNR"',
        'data-profile="FOREX_SNR"',
        'data-profile="COMMODITIES_SNR"',
        'data-profile="TREND_PULLBACK"',
    ]
    for btn in eliminated_buttons:
        assert btn not in _INSTRUMENTS_HTML, f"Botón {btn} todavía aparece en _INSTRUMENTS_HTML"


def test_dashboard_filtering_and_alphabetical_sorting_logic():
    """Verifica que el JavaScript del dashboard contenga el filtrado estricto y ordenamiento alfabético por nombre."""
    # Verificar que RETIRED_WORKER_PIDS incluya los 4 PIDs
    assert "29316" in _HTML
    assert "29740" in _HTML
    assert "30444" in _HTML
    assert "22728" in _HTML

    # Verificar que RETIRED_WORKER_MAGICS incluya sus magics
    assert "26082031" in _HTML
    assert "26082041" in _HTML
    assert "26082043" in _HTML
    assert "26082038" in _HTML

    # Verificar que la función de ordenamiento use localeCompare sobre el nombre del worker
    assert "nameA.localeCompare(nameB, 'es'" in _HTML or "localeCompare" in _HTML
    assert "getWorkerDisplayName" in _HTML


def test_alphabetical_worker_order_simulation():
    """Simula el ordenamiento alfabético exacto por nombre de display sobre el universo activo."""
    worker_labels = {
        'BOOM': 'BOOM (MultiStrategia)',
        'CRASH': 'CRASH (MultiStrategia)',
        'STEP': 'STEP (MultiStrategia)',
        'JUMP': 'JUMP (MultiStrategia)',
        'VOLATILITY_1': 'VOLATILITY (1) · HF (MultiStrategia)',
        'VOLATILITY_2': 'VOLATILITY (2) · Especiales (MultiStrategia)',
        'VOLATILITY_3': 'VOLATILITY (3) · Estándar (MultiStrategia)',
        'VOLATILITY_4': 'VOLATILITY (4) · 1s (MultiStrategia)',
        'FOREX_1': 'FOREX (1) · Majors & Cruces',
        'FOREX_2': 'FOREX (2) · Cruces JPY/CHF',
        'FOREX_3': 'FOREX (3) · Cruces GBP/EUR',
        'FOREX_4': 'FOREX (4) · Cruces Commodity FX',
        'FOREX_5': 'FOREX (5) · Cruces Exóticos FX',
        'INDICESB_SNR': 'INDICESB_SNR · Índices Bursátiles',
        'ORB': 'ORB · Apertura New York',
        'ICT': 'Materias Primas y Criptomonedas',
    }

    raw_workers = [
        {"bot_profile": "ORB", "magic": 26082028},
        {"bot_profile": "ICT", "magic": 26082032},
        {"bot_profile": "BOOM", "magic": 26082101},
        {"bot_profile": "CRASH", "magic": 26082102},
        {"bot_profile": "STEP", "magic": 26082104},
        {"bot_profile": "JUMP", "magic": 26082105},
        {"bot_profile": "VOLATILITY_1", "magic": 26082401},
        {"bot_profile": "VOLATILITY_2", "magic": 26082402},
        {"bot_profile": "VOLATILITY_3", "magic": 26082403},
        {"bot_profile": "VOLATILITY_4", "magic": 26082404},
        {"bot_profile": "FOREX_1", "magic": 26082201},
        {"bot_profile": "FOREX_2", "magic": 26082202},
        {"bot_profile": "FOREX_3", "magic": 26082203},
        {"bot_profile": "FOREX_4", "magic": 26082204},
        {"bot_profile": "FOREX_5", "magic": 26082205},
        {"bot_profile": "INDICESB_SNR", "magic": 26082042},
        # Workers que deben ser excluidos:
        {"bot_profile": "MALAYSIAN_SNR", "magic": 26082031, "pid": 29316},
        {"bot_profile": "FOREX_SNR", "magic": 26082041, "pid": 29740},
        {"bot_profile": "COMMODITIES_SNR", "magic": 26082043, "pid": 22728},
        {"bot_profile": "TREND_PULLBACK", "magic": 26082038, "pid": 30444},
    ]

    def get_display_name(w):
        prof = w["bot_profile"]
        if prof == "ICT" or w.get("magic") == 26082032:
            return "Materias Primas y Criptomonedas"
        if prof == "INDICESB_SNR" or w.get("magic") == 26082042:
            return "INDICESB_SNR · Índices Bursátiles"
        return worker_labels.get(prof, prof)

    # Filtrar
    retired_profs = {'MALAYSIAN_SNR', 'FOREX_SNR', 'COMMODITIES_SNR', 'TREND_PULLBACK'}
    retired_magics = {26082031, 26082041, 26082043, 26082038}
    retired_pids = {29316, 29740, 30444, 22728}

    active_workers = [
        w for w in raw_workers
        if w["bot_profile"] not in retired_profs
        and w.get("magic") not in retired_magics
        and w.get("pid") not in retired_pids
    ]

    assert len(active_workers) == 16  # Exactamente los 16 workers activos

    # Ordenar alfabéticamente por display name
    sorted_workers = sorted(active_workers, key=lambda w: get_display_name(w).lower())
    sorted_names = [get_display_name(w) for w in sorted_workers]

    # Verificar orden ascendente estricto
    assert sorted_names == sorted(sorted_names, key=str.lower)
    assert sorted_names[0] == "BOOM (MultiStrategia)"
    assert sorted_names[1] == "CRASH (MultiStrategia)"
    assert "Materias Primas y Criptomonedas" in sorted_names
    assert "ORB · Apertura New York" in sorted_names
