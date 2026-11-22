"""Tests unitarios para la suite interactiva del operador (tools/operator)."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import pytest

from tools.operator.operator_db import (
    get_system_status,
    get_open_positions,
    get_recent_audit_events,
    get_macro_radar,
    get_catalog_summary,
    get_readonly_connection,
)
from tools.operator.cmd_status import run_status
from tools.operator.cmd_audit import run_audit
from tools.operator.cmd_macro import run_macro
from tools.operator.cmd_catalog import run_catalog


def test_operator_db_readonly_connection_enforces_query_only(tmp_path: Path):
    db_file = tmp_path / "test_bot.sqlite3"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);")
    conn.execute("INSERT INTO test_table (name) VALUES ('demo');")
    conn.commit()
    conn.close()

    ro_conn = get_readonly_connection(db_file)
    cur = ro_conn.cursor()
    cur.execute("SELECT name FROM test_table WHERE id = 1;")
    row = cur.fetchone()
    assert row["name"] == "demo"

    # Verificar que cualquier intento de escritura falla estrictamente
    with pytest.raises(sqlite3.OperationalError):
        ro_conn.execute("INSERT INTO test_table (name) VALUES ('fail');")
    ro_conn.close()


def test_get_catalog_summary_returns_audited_metrics():
    summary = get_catalog_summary()
    assert summary["total_pairs"] == 212
    assert summary["active_pairs"] == 151
    assert summary["pruned_pairs"] == 61
    assert "57.58%" in summary["global_winrate"]


def test_audit_event_humanization():
    from tools.operator.operator_db import humanize_audit_action, humanize_audit_reason

    # Test CYCLE_START
    act1 = humanize_audit_action("CYCLE_START")
    assert act1["label"] == "Inicio de Ciclo"
    assert act1["badge"] == "badge-ok"
    reas1 = humanize_audit_reason("--", "CYCLE_START")
    assert "Inicio del barrido periódico" in reas1

    # Test REGIME_TOXIC_OBSERVED_NOT_BLOCKED
    act2 = humanize_audit_action("REGIME_TOXIC_OBSERVED_NOT_BLOCKED")
    assert "Volatilidad Vigilada" in act2["label"]
    assert act2["badge"] == "badge-warn"
    reas2 = humanize_audit_reason("MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY", "REGIME_TOXIC_OBSERVED_NOT_BLOCKED")
    assert "sin vetar el trade" in reas2


def test_cmd_runners_execute_without_error(capsys):
    assert run_status() == 0
    assert run_audit(limit=2) == 0
    assert run_macro() == 0
    assert run_catalog() == 0

    captured = capsys.readouterr()
    assert "BLACKDAEMONFX — ESTADO OPERATIVO DEL SISTEMA" in captured.out
    assert "BLACKDAEMONFX — RADAR MACROECONÓMICO Y NOTICIAS" in captured.out
    assert "BLACKDAEMONFX — ESTADO DEL CATÁLOGO DE 212 PARES" in captured.out


def test_operator_dashboard_page_and_api_structure():
    from dashboard.operator_page import OPERATOR_HTML
    assert "Suite Interactiva del Operador" in OPERATOR_HTML
    assert "/api/operator" in OPERATOR_HTML
    assert "Radar Macroeconómico" in OPERATOR_HTML
    assert "btnClearChat" in OPERATOR_HTML
    assert "btnToggleScroll" in OPERATOR_HTML
    assert "chatWindow" in OPERATOR_HTML
    assert "humanizeAuditAction" in OPERATOR_HTML
    assert "humanizeAuditReason" in OPERATOR_HTML

    # Verificar que el payload de la API está completo y estructurado
    status = get_system_status()
    macro = get_macro_radar()
    positions = get_open_positions()
    audit = get_recent_audit_events(limit=5)
    catalog = get_catalog_summary()

    assert isinstance(status, dict)
    assert isinstance(macro, dict)
    assert isinstance(positions, list)
    assert isinstance(audit, list)
    assert isinstance(catalog, dict)
    assert "high_impact_events" in macro


def test_operator_chatbot_humanized_responses():
    from dashboard.operator_chatbot import process_operator_chat_message

    # 1. Saludo
    res_greet = process_operator_chat_message("Hola buenos días")
    assert res_greet["ok"] is True
    assert "BlackDaemonFX" in res_greet["reply"]

    # 2. Consulta de cuenta
    res_account = process_operator_chat_message("¿Cómo va la cuenta y el bot?")
    assert res_account["ok"] is True
    assert "Posiciones Abiertas" in res_account["reply"]

    # 3. Consulta de noticias macro
    res_macro = process_operator_chat_message("¿Hay noticias macro hoy?")
    assert res_macro["ok"] is True
    assert "Radar Macroeconómico" in res_macro["reply"]

    # 4. Consulta de instrumento sintético con diagrama técnico
    res_vol = process_operator_chat_message("¿Qué ves en Volatility 75?")
    assert res_vol["ok"] is True
    assert res_vol["symbol"] == "Volatility 75 Index"
    assert "Volatility 75 Index" in res_vol["reply"]
    assert "¿Qué le falta para gatillar la operación?" in res_vol["reply"]
    assert "0% de impacto macroeconómico" in res_vol["reply"]
    assert "Diagrama Técnico en Pantalla" in res_vol["reply"]
    assert res_vol["has_chart"] is True
    assert res_vol["chart_data"] is not None
    assert len(res_vol["chart_data"]["candles"]) == 26
    assert res_vol["chart_data"]["current_price"] > 0
    assert res_vol["chart_data"]["entry_price"] > 0
    assert res_vol["chart_data"]["stop_loss"] > 0
    assert res_vol["chart_data"]["take_profit_1"] > 0

    # 5. Consulta de Step Index 400
    res_step = process_operator_chat_message("Analízame Step Index 400 por favor")
    assert res_step["ok"] is True
    assert res_step["symbol"] == "Step Index 400"
    assert "Step Index 400" in res_step["reply"]
    assert res_step["has_chart"] is True
    assert res_step["chart_data"]["symbol"] == "Step Index 400"

    # 6. Consulta de Crash 1000
    res_crash = process_operator_chat_message("¿Cómo está Crash 1000?")
    assert res_crash["ok"] is True
    assert "SELL (Venta Exclusiva)" in res_crash["reply"]
    assert res_crash["has_chart"] is True
    assert res_crash["chart_data"]["direction"] == "SELL"

    # 7. Consulta de instrumentos por realizar trade / inminentes
    res_near = process_operator_chat_message("¿Qué instrumento está por realizar un trade?")
    assert res_near["ok"] is True
    assert "Radar de Oportunidades y Activos Próximos a Gatillar" in res_near["reply"]
    assert res_near["has_chart"] is True
    assert res_near["chart_data"] is not None
    assert res_near["symbol"] is not None
    assert "Confluencia:" in res_near["reply"]

    # Variante de pregunta
    res_near_var = process_operator_chat_message("¿Qué activo está cerca de entrar?")
    assert res_near_var["ok"] is True
    assert "Radar de Oportunidades" in res_near_var["reply"]

    # 8. Consulta de Oro / XAUUSD con estado institucional y precio fiel
    res_gold = process_operator_chat_message("¿Qué ves en el Oro hoy?")
    assert res_gold["ok"] is True
    assert res_gold["symbol"] == "XAUUSD"
    assert "XAUUSD" in res_gold["reply"]
    assert "Killzone" in res_gold["reply"]
    assert "Commodity Spread Gate" in res_gold["reply"]
    assert res_gold["has_chart"] is True
    # El precio del oro debe ser fiel a cotización real (~2600-2800 USD/oz)
    assert 2200.0 <= res_gold["chart_data"]["current_price"] <= 3200.0
    assert f"{res_gold['chart_data']['current_price']:,.2f}" in res_gold["reply"]
    # La confluencia nunca debe ser 0.0 pts artificial
    assert "Confluencia: 0.0/100" not in res_gold["reply"]

    # 9. Consulta de Criterios Humanos
    res_human = process_operator_chat_message("¿Estas respuestas consideran los criterios humanos establecidos?")
    assert res_human["ok"] is True
    assert "HumanCriteriaEngine" in res_human["reply"]
    assert "Marea Mayor HTF" in res_human["reply"]
    assert "Microestructura y Confirmación M5" in res_human["reply"]

    # 10. Consulta de Conflicto de Temporalidades / Sesgo (Pregunta real de usuario)
    res_conflict = process_operator_chat_message("PORQUE VEZ EL ORO ALCISTA SI EN TEMPORALIDAD H1 SE VE BAJISTA?")
    assert res_conflict["ok"] is True
    assert res_conflict["symbol"] == "XAUUSD"
    assert res_conflict["has_chart"] is True
    assert "Resolución de Conflicto de Temporalidades en XAUUSD" in res_conflict["reply"]
    assert "Tienes toda la razón en tu observación técnica" in res_conflict["reply"]
    assert "BAJISTA" in res_conflict["reply"]
    assert "EMA 50 H1:" in res_conflict["reply"]
    assert "Barrido de Liquidez Sell-Side (SSL Hunt)" in res_conflict["reply"]
    assert "NUNCA compra a ciegas contra la tendencia mayor de H1" in res_conflict["reply"]
    assert "CHOCH / MSS" in res_conflict["reply"]
    assert "ESPERA / STANDBY" in res_conflict["reply"]

    # 11. Consulta de Sesiones y Killzones en Sintéticos
    res_synth_sess = process_operator_chat_message(
        "validame que las killzone o zonas de no operar esten afectando a los indices sinteticos, ya que veo que en Asia no estan operando y no deberia ser asi"
    )
    assert res_synth_sess["ok"] is True
    assert "24 horas al día, 7 días a la semana" in res_synth_sess["reply"]
    assert "Bypass Explícito de Killzones de Forex" in res_synth_sess["reply"]
    assert "Jump 50 Index" in res_synth_sess["reply"]
    assert "05:25:10 UTC" in res_synth_sess["reply"]

    # 12. Consulta de por qué no ha operado un activo
    res_why_xau = process_operator_chat_message("¿Por qué no ha operado el oro?")
    assert res_why_xau["ok"] is True
    assert "Auditoría de Inactividad / Espera en XAUUSD" in res_why_xau["reply"]
    assert "Filtro de Confluencia Institucional" in res_why_xau["reply"]

    # 13. Consulta de por qué se ingresó en un activo (Caso Germany 40)
    res_why_ger = process_operator_chat_message("PORQUE INGRESASTE EN GERMANY 40")
    assert res_why_ger["ok"] is True
    assert res_why_ger["symbol"] == "Germany 40"
    assert res_why_ger["has_chart"] is True
    assert "Auditoría de Entrada y Tesis Operativa en Germany 40" in res_why_ger["reply"]
    assert "Ventana de Volumen Europeo (Frankfurt / Londres)" in res_why_ger["reply"]
    assert "Estrategia ORB + ICT" in res_why_ger["reply"]
    assert "Index Spread Gate" in res_why_ger["reply"]
    assert "Criterio Humano y Gestión de Riesgo Contractual" in res_why_ger["reply"]
    # Coherencia estricta de precio: Germany 40 cotiza en ~25,990 pts, nunca en los obsoletos 19,250
    assert res_why_ger["chart_data"]["current_price"] >= 25000.0
    assert res_why_ger["chart_data"]["current_price"] <= 32000.0

    # 13b. Caso con Posición Abierta viva en Germany 40 vinculada al gráfico
    from unittest.mock import patch
    fake_pos = [{
        "ticket": 998877,
        "symbol": "Germany 40",
        "direction": "SELL",
        "entry_price": 25992.30,
        "stop_loss": 26084.33,
        "take_profit": 25900.27,
        "volume": 0.5,
        "profit": 0.0,
        "open_time": "2026-11-18 10:00:00",
    }]
    with patch("dashboard.operator_chatbot.get_open_positions", return_value=fake_pos):
        res_why_pos = process_operator_chat_message("PORQUE INGRESASTE EN GERMANY 40")
        assert res_why_pos["ok"] is True
        assert "25,992.30" in res_why_pos["reply"]
        assert "26,084.33" in res_why_pos["reply"]
        assert res_why_pos["chart_data"]["current_price"] == 25992.3
        assert res_why_pos["chart_data"]["entry_price"] == 25992.3
        assert res_why_pos["chart_data"]["stop_loss"] == 26084.3
        assert res_why_pos["chart_data"]["take_profit_1"] == 25900.3
        assert res_why_pos["chart_data"]["direction"] == "SELL"

    # 14. Consulta no identificada
    res_unknown = process_operator_chat_message("Cosas aleatorias 12345")
    assert res_unknown["ok"] is True
    assert "No logré identificar con claridad" in res_unknown["reply"]

    # 15. Consulta sobre calificación de setup / grado B+
    res_b_plus = process_operator_chat_message("que significa b+")
    assert res_b_plus["ok"] is True
    assert "QUÉ SIGNIFICA EL GRADO 'B+'" in res_b_plus["reply"]
    assert "80.0 a 84.9 pts" in res_b_plus["reply"]
    assert "ESCALA COMPLETA DE CALIFICACIÓN" in res_b_plus["reply"]

    # 16. Consulta sobre Puntos de Vista de Ambas Estrategias (ICT vs Malaysian SNR)
    res_strats = process_operator_chat_message("podrias responderme cuales son los puntos de vista de ambas estrategias en el chatbot")
    assert res_strats["ok"] is True
    assert "ESTRATEGIA ICT" in res_strats["reply"]
    assert "ESTRATEGIA MALAYSIAN SNR" in res_strats["reply"]
    assert "Súper-Confluencia Cruzada" in res_strats["reply"]
    assert "Veto por Conflicto Direccional" in res_strats["reply"]
    assert "Motor de Subasta Competitiva" in res_strats["reply"]

    # 16b. Variante con símbolo específico
    res_strats_sym = process_operator_chat_message("cuales son los puntos de vista de ambas estrategias en el Oro")
    assert res_strats_sym["ok"] is True
    assert res_strats_sym["symbol"] == "XAUUSD"
    assert res_strats_sym["has_chart"] is True
    assert "Estado Actual Específico en XAUUSD" in res_strats_sym["reply"]
    assert "Grado A+" in res_b_plus["reply"]
    assert "1% de riesgo total" in res_b_plus["reply"]

    # 17. Consulta de con qué estrategia se argumenta el análisis (Pregunta exacta de usuario)
    res_arg = process_operator_chat_message("con que estrategia argumentas ese analisis?")
    assert res_arg["ok"] is True
    assert "Fundamento y Tesis Estratégica del Análisis" in res_arg["reply"]
    assert "Pilar de Microestructura: Estrategia ICT" in res_arg["reply"]
    assert "Pilar de Macroestructura: Estrategia Malaysian SNR" in res_arg["reply"]
    assert "Criterio Humano de Admisión" in res_arg["reply"]
    assert "1% de riesgo total" in res_arg["reply"]

    # 18. Verificar que las notas de riesgo / salidas de emergencia no corrompan la descripción visual
    from dashboard.operator_chatbot import generate_humanized_analysis
    reply_step, chart_step = generate_humanized_analysis("Step Index 400")
    assert "¿Qué estamos viendo en el gráfico?" in reply_step
    # La descripción del gráfico debe describir microestructura técnica, no la nota de riesgo
    seeing_section = reply_step.split("¿Qué estamos viendo en el gráfico?")[1].split("¿Qué le falta para gatillar la operación?")[0]
    assert "microestructura" in seeing_section.lower() or "desplazamiento institucional" in seeing_section.lower() or "zona de mitigación" in seeing_section.lower()
    # Si hay nota de auditoría, debe estar claramente segregada bajo su encabezado de advertencia
    if "El riesgo real de la posición" in reply_step:
        assert "Nota de Control de Margen y Auditoría" in reply_step

    # 19. Preservación estricta del contexto conversacional entre turnos (Sin cambio errático a Volatility 75)
    from dashboard.operator_chatbot import clear_conversation_context
    clear_conversation_context()

    # Turno 1: Usuario pregunta por Step Index 400
    turn1 = process_operator_chat_message("que ves en el step 400")
    assert turn1["ok"] is True
    assert turn1["symbol"] == "Step Index 400"

    # Turno 2: Usuario pregunta "¿en qué estrategia se basa este análisis?" sin nombrar el símbolo
    turn2 = process_operator_chat_message("en que estrategia se basa este analisis?")
    assert turn2["ok"] is True
    # El contexto DEBE mantenerse en Step Index 400, NUNCA cambiar a Volatility 75
    assert turn2["symbol"] == "Step Index 400"
    assert "Step Index 400" in turn2["reply"]
    assert "Volatility 75" not in turn2["reply"]

    # 20. Coherencia Direccional Absoluta entre Texto y Gráfico (Cero contradicciones BUY/SELL)
    assert "Sesgo Operativo:" in turn1["reply"]
    if turn1["chart_data"]["direction"] == "SELL":
        assert "SELL" in turn1["reply"]
        assert "BAJISTA" in turn1["reply"]
        assert "microestructura ALCISTA (BUY) con marea mayor favorable en H1/H4 (BAJISTA)" not in turn1["reply"]
    elif turn1["chart_data"]["direction"] == "BUY":
        assert "BUY" in turn1["reply"]
        assert "ALCISTA" in turn1["reply"]

    # 21. Consulta coloquial con falta ortográfica ("en que estrategia vez esto") hereda contexto y responde tesis
    turn_colloquial = process_operator_chat_message("en que estrategia vez esto")
    assert turn_colloquial["ok"] is True
    assert turn_colloquial["symbol"] == "Step Index 400"
    assert "Fundamento y Tesis Estratégica del Análisis en Step Index 400" in turn_colloquial["reply"]
    assert "Estrategia ICT (Smart Money Concepts - SMC)" in turn_colloquial["reply"]
    assert "Estrategia Malaysian SNR (Support & Resistance)" in turn_colloquial["reply"]
    assert turn_colloquial["has_chart"] is True
    assert turn_colloquial["chart_data"]["symbol"] == "Step Index 400"

    # 22. Radar de Próximos Trades: Cero contaminación de eventos de riesgo y sincronización 100% Texto-Gráfico
    from dashboard.operator_chatbot import generate_near_trades_analysis
    radar_text, radar_chart = generate_near_trades_analysis()
    assert "Radar de Oportunidades y Activos Próximos a Gatillar" in radar_text
    # Ninguna oportunidad debe reportar "superó el límite máximo" ni "cierre de emergencia"
    assert "superó el límite máximo" not in radar_text
    assert "EMERGENCY_RISK_EXIT" not in radar_text
    # La dirección del candidato 1 debe ser idéntica a la dirección dibujada en radar_chart
    radar_lines = [l for l in radar_text.split("\n") if "1. ⚡" in l]
    assert len(radar_lines) == 1
    c1_line = radar_lines[0]
    # El candidato 1 debe ser el activo con mayor confluencia (Step Index 400 con 84 pts, NUNCA Volatility 75 rechazada con 68 pts)
    assert "Step Index 400" in c1_line
    assert radar_chart["symbol"] == "Step Index 400"
    if radar_chart["direction"] == "SELL":
        assert "SELL" in c1_line
        assert "BUY" not in c1_line
    elif radar_chart["direction"] == "BUY":
        assert "BUY" in c1_line
        assert "SELL" not in c1_line

    # 23. Solución de Raíz a Precios Incoherentes: Cotizaciones 100% realistas en todos los instrumentos
    from dashboard.operator_chatbot import build_chart_data_for_symbol, is_same_instrument
    btc_chart = build_chart_data_for_symbol("BTCUSD", "SELL")
    assert 70000.0 <= btc_chart["current_price"] <= 120000.0, f"BTCUSD precio erróneo: {btc_chart['current_price']}"
    assert abs(btc_chart["current_price"] - 82793.9) > 5000.0  # Nunca el precio sintético desactualizado de 82k

    gold_chart = build_chart_data_for_symbol("XAUUSD", "BUY")
    assert 2200.0 <= gold_chart["current_price"] <= 3200.0, f"XAUUSD precio erróneo: {gold_chart['current_price']}"
    assert abs(gold_chart["current_price"] - 3800.0) > 400.0  # Nunca el número ficticio de 3800

    ger_chart = build_chart_data_for_symbol("Germany 40", "SELL")
    assert 22000.0 <= ger_chart["current_price"] <= 28000.0, f"Germany 40 precio erróneo: {ger_chart['current_price']}"
    assert abs(ger_chart["current_price"] - 19250.0) > 4000.0  # Nunca el precio viejo de 19250

    step400_chart = build_chart_data_for_symbol("Step Index 400", "BUY")
    assert 7500.0 <= step400_chart["current_price"] <= 11500.0, f"Step 400 precio erróneo: {step400_chart['current_price']}"

    # 24. El guardián jamás descarta datos en vivo con desvío > 15%
    from unittest.mock import patch
    mock_live_btc = {
        "candles": [{"open": 105100.0, "high": 105300.0, "low": 105000.0, "close": 105250.0}] * 10,
        "current_price": 105250.0,
        "atr": 450.0,
        "digits": 1,
        "spread": 2.0,
        "matched_symbol": "BTCUSD",
        "timeframe": "M5",
    }
    with patch("dashboard.operator_chatbot.fetch_live_mt5_candles", return_value=mock_live_btc):
        live_chart = build_chart_data_for_symbol("BTCUSD", "BUY")
        assert live_chart["current_price"] == 105250.0
        assert len(live_chart["candles"]) == 10

    # 25. Matching semántico fiel de instrumentos entre broker y catálogo
    assert is_same_instrument("Germany 40", "GER40") is True
    assert is_same_instrument("Germany 40", "DAX40") is True
    assert is_same_instrument("Germany 40", "DAX") is True
    assert is_same_instrument("XAUUSD", "GOLD") is True
    assert is_same_instrument("XAUUSD", "XAUUSDmicro") is True
    assert is_same_instrument("BTCUSD", "BITCOIN") is True
    assert is_same_instrument("Step Index 400", "Step Index 500") is False

    # 26. Nueva Capacidad: Auditoría Forense de Entradas Desacreditadas / Rechazadas
    from dashboard.operator_chatbot import is_why_discredited_inquiry, handle_why_discredited_inquiry

    # Verificación de detección de intención
    assert is_why_discredited_inquiry("en la pantalla /Operator tambien quiero que seas capaz de identificar porque se desacredito una entrada") is True
    assert is_why_discredited_inquiry("¿Por qué se desacreditó la entrada en Step Index 400?") is True
    assert is_why_discredited_inquiry("¿Por qué desacreditaste la entrada en Volatility 75?") is True
    assert is_why_discredited_inquiry("¿Por qué fue rechazada la entrada?") is True
    assert is_why_discredited_inquiry("¿Por qué se descartó el trade?") is True
    assert is_why_discredited_inquiry("¿Qué invalidó la entrada de Oro?") is True
    assert is_why_discredited_inquiry("¿Por qué entraste en Germany 40?") is False
    assert is_why_discredited_inquiry("¿Por qué no operas hoy?") is False

    # Consulta específica sobre Step Index 400 (Caso Hard Cap de Riesgo / Margen)
    res_disc_step = process_operator_chat_message("¿Por qué se desacreditó la entrada en Step Index 400?")
    assert res_disc_step["ok"] is True
    assert res_disc_step["symbol"] == "Step Index 400"
    assert res_disc_step["has_chart"] is True
    assert "Auditoría Forense · Motivos de Desacreditación / Rechazo de Entrada en Step Index 400" in res_disc_step["reply"]
    assert "Intervención del Guardián de Riesgo Contractual y Margen" in res_disc_step["reply"]
    assert "1% contractual estricto" in res_disc_step["reply"]
    assert res_disc_step["chart_data"]["current_price"] >= 7500.0

    # Consulta específica sobre Volatility 75 (Caso Falta de Gatillo M5 / Score)
    res_disc_vol = process_operator_chat_message("¿Por qué fue rechazada la entrada en Volatility 75?")
    assert res_disc_vol["ok"] is True
    assert res_disc_vol["symbol"] == "Volatility 75 Index"
    assert res_disc_vol["has_chart"] is True
    assert "Auditoría Forense · Motivos de Desacreditación / Rechazo de Entrada en Volatility 75 Index" in res_disc_vol["reply"]
    assert "Falta de Gatillo Fractal M5 y Confluencia Insuficiente" in res_disc_vol["reply"]
    assert "68.0" in res_disc_vol["reply"]

    # Consulta general de desacreditación (solicitud textual del usuario)
    res_disc_gen = process_operator_chat_message("en la pantalla /Operator tambien quiero que seas capaz de identificar porque se desacredito una entrada")
    assert res_disc_gen["ok"] is True
    assert res_disc_gen["has_chart"] is True
    assert "Auditoría Forense Global · Entradas Desacreditadas y Vetadas Recientemente" in res_disc_gen["reply"]
    assert "Step Index 400" in res_disc_gen["reply"]
    assert "Volatility 75 Index" in res_disc_gen["reply"]

    # Comprobación de no-regresión: ¿Por qué ingresaste en Germany 40? sigue yendo al handler afirmativo
    res_why_ger_check = process_operator_chat_message("PORQUE INGRESASTE EN GERMANY 40")
    assert "Auditoría de Entrada y Tesis Operativa en Germany 40" in res_why_ger_check["reply"]


def test_operator_live_trades_and_risk_guard_queries():
    """Valida las consultas de traders sobre operaciones vivas, Break-Even y gestión de riesgo."""
    from unittest.mock import patch
    from dashboard.operator_chatbot import (
        is_live_trades_inquiry,
        is_break_even_inquiry,
        is_risk_and_margin_inquiry,
        process_operator_chat_message,
    )
    from tools.operator.operator_db import (
        get_active_positions_forensics,
        get_account_risk_guard_status,
    )

    # 1. Verificación de detección de intenciones
    assert is_live_trades_inquiry("¿Cómo van los trades abiertos?") is True
    assert is_live_trades_inquiry("cómo van las operaciones vivas") is True
    assert is_live_trades_inquiry("estado de los trades") is True
    assert is_live_trades_inquiry("¿Cómo va el trade de Step Index 400?") is True
    assert is_live_trades_inquiry("¿Por qué ingresaste en Germany 40?") is False

    assert is_break_even_inquiry("¿Cuándo pasas a Break Even?") is True
    assert is_break_even_inquiry("¿Está en BE la operación?") is True
    assert is_break_even_inquiry("ya protegiste el trade a riesgo cero") is True
    assert is_break_even_inquiry("debería operar en Asia") is False  # 'debería' no debe disparar BE

    assert is_risk_and_margin_inquiry("¿Cuánto estamos arriesgando?") is True
    assert is_risk_and_margin_inquiry("¿Cuál es el riesgo actual de la cuenta?") is True
    assert is_risk_and_margin_inquiry("¿Cuántas posiciones más podemos abrir?") is True
    assert is_risk_and_margin_inquiry("gestión de riesgo y capacidad de margen") is True

    # 2. Métricas de tools/operator/operator_db
    guard = get_account_risk_guard_status()
    assert isinstance(guard, dict)
    assert guard["max_concurrent_positions"] == 8
    assert "1.0%" in guard["risk_per_trade_contractual"]
    assert "cooldown_policy" in guard

    forensics = get_active_positions_forensics()
    assert isinstance(forensics, list)

    # 3. Consulta de Riesgo y Margen en Chatbot
    res_risk = process_operator_chat_message("¿Cuánto estamos arriesgando y cuál es el margen?")
    assert res_risk["ok"] is True
    assert "Panel Cuantitativo del Guardián de Riesgo" in res_risk["reply"]
    assert "Riesgo Contractual Fijo (1.0% por trade en 2 patas)" in res_risk["reply"]
    assert "Cierre de Emergencia Anti-Slippage" in res_risk["reply"]
    assert "Política Anti-Revancha" in res_risk["reply"]

    # 4. Consulta de Break-Even institucional
    res_be = process_operator_chat_message("¿Cuándo pasas a Break Even?")
    assert res_be["ok"] is True
    assert "Política Institucional de Break-Even y Protección de Capital" in res_be["reply"]
    assert "Activación Automática de Break-Even en +1.0 R" in res_be["reply"]
    assert "Trailing Stop Progresivo en Ganancias" in res_be["reply"]

    # 5. Consulta de Trades Vivos (Caso con posición viva en Step Index 400)
    fake_active_pos = [
        {
            "id": 101,
            "ticket": 884422,
            "symbol": "Step Index 400",
            "direction": "BUY",
            "entry_price": 12500.0,
            "current_price": 12530.0,
            "stop_loss": 12500.0,  # En BE
            "initial_stop_loss": 12470.0,
            "take_profit": 12560.0,
            "volume": 0.5,
            "current_rr": 1.0,
            "break_even_confirmed": True,
            "is_trailing_active": False,
            "risk_status": "PROTEGIDO (0.0% riesgo)",
            "risk_nominal_pct": 0.0,
            "distance_to_be_r": 0.0,
            "distance_to_tp_r": 1.0,
            "entry_time": "2026-11-22 15:30:00",
            "setup_reason": "Confluencia ICT + MSNR",
        }
    ]
    with patch("dashboard.operator_chatbot.get_active_positions_forensics", return_value=fake_active_pos):
        # 5a. Consulta específica del trade
        res_trade_step = process_operator_chat_message("¿Cómo va el trade de Step Index 400?")
        assert res_trade_step["ok"] is True
        assert res_trade_step["has_chart"] is True
        assert "Seguimiento en Vivo del Trade en Step Index 400 (Ticket #884422)" in res_trade_step["reply"]
        assert "BREAK-EVEN CONFIRMADO" in res_trade_step["reply"]
        assert "0.0% Riesgo" in res_trade_step["reply"]
        assert "+1.00 R" in res_trade_step["reply"]

        # 5b. Consulta general de trades abiertos
        res_all_trades = process_operator_chat_message("¿Cómo van las operaciones abiertas?")
        assert res_all_trades["ok"] is True
        assert "Monitor de Posiciones Vivas en Cartera (1 de 8 permitidas)" in res_all_trades["reply"]
        assert "Step Index 400" in res_all_trades["reply"]
        assert "BE ACTIVO (Riesgo 0%)" in res_all_trades["reply"]
        assert "Resumen Consolidado de Riesgo y Cartera" in res_all_trades["reply"]
        assert "Posiciones Blindadas (0% Riesgo):** **1 de 1**" in res_all_trades["reply"]

        # 5c. Consulta de BE en el activo abierto
        res_be_step = process_operator_chat_message("¿Está en BE Step Index 400?")
        assert res_be_step["ok"] is True
        assert "Estado Específico de tu Posición en Step Index 400" in res_be_step["reply"]
        assert "¡Break-Even ya está confirmado y activo!" in res_be_step["reply"]

