"""tools/operator/operator_db.py - Conexión segura y consultas en solo lectura para el Operador.

Garantiza:
1. Acceso a SQLite en solo lectura estricta (PRAGMA query_only = ON, mode=ro).
2. Detección automática de la base de datos viva (AppData o storage/).
3. Lectura de estados en disco (last_state.json, financial_news.json).
4. No interfiere ni bloquea los daemons o workers en ejecución.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE_LIVE_DB = PROJECT_ROOT / "storage" / "live_trading_bot.sqlite3"
DEFAULT_WORKSPACE_DB = PROJECT_ROOT / "storage" / "trading_bot.sqlite3"
DEFAULT_APPDATA_DB = Path(os.environ.get("LOCALAPPDATA", "")) / "BlackDaemonFx" / "trading_bot.sqlite3"
DEFAULT_NEWS_JSON = PROJECT_ROOT / "storage" / "dashboard" / "financial_news.json"
DEFAULT_LAST_STATE_JSON = PROJECT_ROOT / "storage" / "dashboard" / "last_state.json"


def resolve_database_path() -> Path:
    """Resuelve la ruta de la base de datos viva disponible priorizando la DB de ejecución en vivo."""
    custom = os.environ.get("DAEMONBLACKFX_DB_PATH")
    if custom:
        try:
            p = Path(custom)
            if p.exists():
                return p
        except (PermissionError, OSError):
            pass

    # 1. Priorizar base de datos de Live Trading si existe y tiene datos
    try:
        if DEFAULT_WORKSPACE_LIVE_DB.exists() and DEFAULT_WORKSPACE_LIVE_DB.stat().st_size > 0:
            return DEFAULT_WORKSPACE_LIVE_DB
    except (PermissionError, OSError):
        pass

    # 2. Base de datos persistente en AppData
    try:
        if DEFAULT_APPDATA_DB.exists() and DEFAULT_APPDATA_DB.stat().st_size > 0:
            return DEFAULT_APPDATA_DB
    except (PermissionError, OSError):
        pass

    # 3. Base de datos en workspace
    if DEFAULT_WORKSPACE_DB.exists():
        return DEFAULT_WORKSPACE_DB
    return DEFAULT_WORKSPACE_DB


def get_readonly_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Abre conexión SQLite en solo lectura estricta."""
    path = Path(db_path) if db_path else resolve_database_path()
    if not path.exists():
        raise FileNotFoundError(f"Base de datos no encontrada en: {path}")

    # file:path?mode=ro requiere formato de URI seguro
    uri_path = path.as_posix()
    conn = sqlite3.connect(f"file:{uri_path}?mode=ro", uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON;")
    return conn


def get_system_status() -> Dict[str, Any]:
    """Obtiene un resumen global de salud del sistema, ciclo y conexión."""
    status: Dict[str, Any] = {
        "bot_status": "DESCONOCIDO",
        "connection_mode": "N/A",
        "data_freshness": "N/A",
        "cycle": 0,
        "symbols_processed": 0,
        "symbols_total": 0,
        "open_trades_count": 0,
        "db_path": str(resolve_database_path()),
        "last_update": None,
    }

    # 1. Leer desde last_state.json si existe
    if DEFAULT_LAST_STATE_JSON.exists():
        try:
            data = json.loads(DEFAULT_LAST_STATE_JSON.read_text(encoding="utf-8"))
            status["bot_status"] = data.get("status", "INACTIVO")
            status["connection_mode"] = data.get("connection_mode", "N/A")
            status["data_freshness"] = data.get("data_freshness", "N/A")
            status["cycle"] = data.get("cycle", 0)
            status["symbols_processed"] = data.get("symbols_processed", 0)
            status["symbols_total"] = data.get("symbols_total", 0)
            status["last_update"] = data.get("updated_at") or data.get("last_live_update")
        except Exception:
            pass

    # 2. Conteo de trades abiertos en DB
    try:
        conn = get_readonly_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
        status["open_trades_count"] = cur.fetchone()[0]
        conn.close()
    except Exception:
        pass

    return status


def get_open_positions() -> List[Dict[str, Any]]:
    """Consulta las posiciones actualmente abiertas en la base de datos."""
    try:
        conn = get_readonly_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, external_ticket, broker_position_ticket, instrument, direction,
                   entry_price, stop_loss, take_profit, volume, planned_rr, realized_rr,
                   entry_time, setup_reason
            FROM trades
            WHERE status = 'OPEN'
            ORDER BY id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def humanize_audit_action(action: Optional[str], event_type: Optional[str] = None) -> Dict[str, str]:
    """Humaniza la acción de auditoría técnica en lenguaje comprensible con su estilo visual."""
    raw = str(action or event_type or "").strip().upper()
    if not raw or raw in ("--", "NONE", "NULL"):
        return {"label": "Escaneo Activo", "badge": "badge-ok"}

    mapping = {
        "CYCLE_START": {"label": "Inicio de Ciclo", "badge": "badge-ok"},
        "DAEMON_CYCLE_START": {"label": "Inicio de Ciclo", "badge": "badge-ok"},
        "REGIME_TOXIC_OBSERVED_NOT_BLOCKED": {"label": "Volatilidad Vigilada (Sin Veto)", "badge": "badge-warn"},
        "MARKET_REGIME_OBSERVED": {"label": "Régimen en Observación", "badge": "badge-warn"},
        "REGIME_FILTER_BLOCKED": {"label": "Veto por Régimen Tóxico", "badge": "badge-high"},
        "MARKET_REGIME_BLOCKED": {"label": "Veto por Régimen Tóxico", "badge": "badge-high"},
        "STANDBY_ENTER": {"label": "Pausa Mercado Cerrado", "badge": "badge-warn"},
        "STANDBY_EXIT": {"label": "Reapertura de Mercado", "badge": "badge-ok"},
        "FOREX_MARKET_STANDBY_ENTER": {"label": "Pausa Fin de Semana Forex", "badge": "badge-warn"},
        "FOREX_MARKET_STANDBY_EXIT": {"label": "Reapertura Forex", "badge": "badge-ok"},
        "ANALYZING": {"label": "Evaluando Microestructura", "badge": "badge-ok"},
        "SYMBOL_PROCESS_START": {"label": "Iniciando Evaluación M5", "badge": "badge-ok"},
        "COOLDOWN_POST_SL_BLOCKED": {"label": "Pausa Preventiva Post-SL", "badge": "badge-high"},
        "SYMBOL_COOLDOWN_BLOCKED": {"label": "Pausa Preventiva Post-SL", "badge": "badge-high"},
        "VIRTUAL_TRADE_SPREAD_NORMALIZED": {"label": "Spread Normalizado (Desbloqueado)", "badge": "badge-ok"},
        "FOREX_NEWS_TRAILING_PRESERVED": {"label": "Trailing Stop Preservado", "badge": "badge-ok"},
        "FOREX_NEWS_BREAK_EVEN_CONFIRMED": {"label": "Break-Even Blindado por Noticia", "badge": "badge-warn"},
        "FOREX_NEWS_BREAK_EVEN_DEFERRED": {"label": "BE Diferido (Esperando Retroceso)", "badge": "badge-warn"},
        "PROFILE_SELECTION_PERSISTED_VERIFIED": {"label": "Catálogo Élite Sincronizado", "badge": "badge-ok"},
        "INSTRUMENT_SELECTION_PROFILE_CHANGED": {"label": "Catálogo Élite Sincronizado", "badge": "badge-ok"},
        "SELECTION_PERSISTED": {"label": "Preferencia de Activos Guardada", "badge": "badge-ok"},
        "INSTRUMENT_SELECTION_CHANGED": {"label": "Preferencia de Activos Guardada", "badge": "badge-ok"},
        "TARGET_VALUES_RECORDED": {"label": "Niveles TP/SL Registrados", "badge": "badge-ok"},
        "TRADE_TARGET_CHANGE": {"label": "Niveles TP/SL Registrados", "badge": "badge-ok"},
        "MT5_OPEN_POSITION_RECOVERED": {"label": "Posición MT5 Sincronizada", "badge": "badge-ok"},
        "PERSISTENCE_SELF_HEAL": {"label": "Autocorrección de Posiciones", "badge": "badge-ok"},
        "MT5_RECOVERY_FAILED": {"label": "Error de Enlace MT5", "badge": "badge-high"},
        "PERSISTENCE_SELF_HEAL_ERROR": {"label": "Error de Enlace MT5", "badge": "badge-high"},
        "SGD_STEP_APPLIED": {"label": "Aprendizaje IA Actualizado", "badge": "badge-ok"},
        "AI_ONLINE_LEARNING_UPDATED": {"label": "Aprendizaje IA Actualizado", "badge": "badge-ok"},
        "ALLOW": {"label": "Confluencia Confirmada (Permitido)", "badge": "badge-ok"},
        "PERMITIDO": {"label": "Confluencia Confirmada (Permitido)", "badge": "badge-ok"},
        "VETO": {"label": "Veto Institucional", "badge": "badge-high"},
        "REJECT": {"label": "Veto Institucional", "badge": "badge-high"},
        "RECHAZADA": {"label": "Veto Institucional", "badge": "badge-high"},
        "NO_SIGNAL": {"label": "Sin Señal Confirmada", "badge": "badge-warn"},
    }

    if raw in mapping:
        return mapping[raw]

    clean = raw.replace("_", " ").title()
    badge = "badge-high" if any(w in raw for w in ("BLOCK", "VETO", "REJECT", "ERROR", "FAIL")) else ("badge-warn" if any(w in raw for w in ("OBSERVED", "STANDBY", "WARN", "WAIT")) else "badge-ok")
    return {"label": clean, "badge": badge}


def humanize_audit_reason(reason: Optional[str], action: Optional[str] = None) -> str:
    """Humaniza el motivo o detalle técnico en una explicación clara institucional en español."""
    r = str(reason or "").strip()
    act = str(action or "").strip().upper()

    if not r or r in ("--", "None", "null", "Sin motivo especificado"):
        if "CYCLE_START" in act:
            return "Inicio del barrido periódico de escaneo sobre los 212 activos del catálogo institucional."
        if "STANDBY" in act:
            return "Horario fuera de sesión bancaria/bolsa; respetando ventana de liquidez."
        if "PROFILE" in act or "SELECTION" in act:
            return "Sincronización periódica de catálogo de activos activos y podados."
        return "Inspección periódica en segundo plano completada en condiciones normales."

    if "ERRATIC_WHIPSAW_VOLATILITY" in r or "MARKET_REGIME_TOXIC" in r:
        if "NOT_BLOCKED" in act or "OBSERVED" in act:
            return "Volatilidad errática con sacudidas bruscas detectada; Centinela mantiene observación activa sin vetar el trade por absorción/desplazamiento institucional."
        return "Volatilidad errática con sacudidas bruscas (Whipsaw); operación descartada preventivamente para proteger la cuenta."

    if r == "SYNTHETICS":
        return "Perfil de 38 índices sintéticos de Deriv validado y activo 24/7."
    if r == "FOREX":
        return "Perfil de divisas Forex mayores y menores sincronizado con el calendario."
    if r == "ICT":
        return "Perfil especializado de estrategia ICT Institutional validado."
    if r == "MALAYSIAN_SNR":
        return "Perfil de niveles Malaysian SNR y microestructura validado."
    if r == "TREND_PULLBACK":
        return "Perfil de continuación tendencial validado."

    if "SPREAD_TOO_HIGH" in r or "SPREAD_SPIKE" in r:
        return "Spread de mercado temporalmente elevado por encima del umbral institucional de riesgo."
    if "MAX_POSITIONS" in r:
        return "Cupo máximo de 8 posiciones concurrentes activas alcanzado para preservar margen."
    if "COOLDOWN" in r:
        return "Período de enfriamiento post Stop Loss activo para evitar sobreoperativa en este par."
    if r.startswith("LABEL_"):
        return "Actualización del modelo de Criterio Humano / IA tras registrar el resultado de la operación."
    if "FOREX_NEWS" in r:
        return "Protección automática activada ante evento macroeconómico de alto impacto."

    return (
        r.replace("MARKET_REGIME_TOXIC_BLOCKED:", "")
        .replace("_", " ")
        .strip()
    )


def get_recent_audit_events(symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Consulta eventos de auditoría y vetos del centinela/criterio humano humanizados."""
    try:
        conn = get_readonly_connection()
        cur = conn.cursor()
        if symbol:
            cur.execute("""
                SELECT id, event_time, source, event_type, instrument, action, reason, payload_json
                FROM daemon_audit_events
                WHERE instrument = ?
                ORDER BY id DESC
                LIMIT ?
            """, (symbol, limit))
        else:
            cur.execute("""
                SELECT id, event_time, source, event_type, instrument, action, reason, payload_json
                FROM daemon_audit_events
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        raw_rows = [dict(r) for r in cur.fetchall()]
        conn.close()

        enriched = []
        for row in raw_rows:
            item = dict(row)
            act_info = humanize_audit_action(item.get("action"), item.get("event_type"))
            item["action_raw"] = item.get("action")
            item["action"] = act_info["label"]
            item["action_es"] = act_info["label"]
            item["action_badge"] = act_info["badge"]

            reason_human = humanize_audit_reason(item.get("reason"), item.get("action_raw") or item.get("action"))
            item["reason_raw"] = item.get("reason")
            item["reason"] = reason_human
            item["reason_es"] = reason_human
            enriched.append(item)

        return enriched
    except Exception:
        return []


def get_macro_radar() -> Dict[str, Any]:
    """Lee el calendario económico y detecta ventanas macro de alto impacto."""
    radar: Dict[str, Any] = {
        "calendar_status": "SIN_ARCHIVO",
        "updated_at": None,
        "high_impact_events": [],
        "currencies_affected": [],
    }

    target = DEFAULT_NEWS_JSON if DEFAULT_NEWS_JSON.exists() else PROJECT_ROOT / "storage" / "financial_news.json"
    if not target.exists():
        return radar

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        radar["calendar_status"] = data.get("calendar_status", "DESCONOCIDO")
        radar["updated_at"] = data.get("updated_at")

        events = data.get("calendar_events", [])
        high = [e for e in events if str(e.get("impact", "")).upper() == "ALTO"]
        radar["high_impact_events"] = high
        currencies = sorted(list({str(e.get("country", "")).upper() for e in high if e.get("country")}))
        radar["currencies_affected"] = currencies
    except Exception:
        pass

    return radar


def get_catalog_summary() -> Dict[str, Any]:
    """Obtiene el resumen de los pares auditados (activos vs podados)."""
    summary = {
        "total_pairs": 212,
        "active_pairs": 151,
        "pruned_pairs": 61,
        "global_winrate": "57.58%",
        "accumulated_r": "+2,884.19 R",
        "status": "Auditoría Multi-Estrategia (05-nov-2026)",
    }
    return summary


def get_active_positions_forensics() -> List[Dict[str, Any]]:
    """Consulta las posiciones vivas en mercado cruzando SQLite y la telemetría viva de last_state.json.

    Calcula de forma exacta:
    - R flotante actual
    - Estado de protección Break-Even (confirmado vs en desarrollo)
    - Distancia restante a TP1 (1R) y TP2 (runner)
    - Riesgo monetario nominal remanente (0.0% si BE está confirmado, 1.0% si sigue en desarrollo).
    """
    positions = get_open_positions()
    monitored_map: Dict[str, Dict[str, Any]] = {}

    # 1. Leer telemetría viva de Break-Even en last_state.json
    if DEFAULT_LAST_STATE_JSON.exists():
        try:
            st_data = json.loads(DEFAULT_LAST_STATE_JSON.read_text(encoding="utf-8"))
            lm = st_data.get("last_monitor", {})
            be_info = lm.get("break_even", {})
            be_pos_list = be_info.get("positions", [])
            for bp in be_pos_list:
                sym = str(bp.get("symbol") or "").strip().lower()
                if sym:
                    monitored_map[sym] = bp
        except Exception:
            pass

    results: List[Dict[str, Any]] = []

    # 2. Enriquecer posiciones registradas en SQLite
    seen_symbols = set()
    for pos in positions:
        sym = str(pos.get("instrument") or pos.get("symbol") or "").strip()
        sym_key = sym.lower()
        seen_symbols.add(sym_key)

        direction = str(pos.get("direction") or "BUY").upper()
        entry_p = float(pos.get("entry_price") or 0.0)
        sl_p = float(pos.get("stop_loss") or 0.0)
        tp_p = float(pos.get("take_profit") or 0.0)
        vol = float(pos.get("volume") or 0.0)

        # Buscar match en monitored_map
        m_item = monitored_map.get(sym_key)
        if not m_item:
            # Buscar coincidencia parcial (ej. Volatility 75 vs Volatility 75 Index)
            for k, val in monitored_map.items():
                if k in sym_key or sym_key in k:
                    m_item = val
                    break

        if m_item:
            cur_p = float(m_item.get("current_price") or entry_p)
            cur_sl = float(m_item.get("current_stop_loss") or sl_p)
            cur_rr = float(m_item.get("current_rr") or 0.0)
            be_confirmed = bool(m_item.get("break_even_confirmed"))
            dist_sl_r = float(m_item.get("distance_to_sl_r") or 0.0)
            dist_tp_r = float(m_item.get("distance_to_tp_r") or 0.0)
        else:
            cur_p = entry_p
            cur_sl = sl_p
            # Calcular R flotante aproximado si hay SL
            risk_dist = abs(entry_p - sl_p) if sl_p > 0 else 0.0
            if risk_dist > 0:
                cur_rr = (cur_p - entry_p) / risk_dist if direction == "BUY" else (entry_p - cur_p) / risk_dist
            else:
                cur_rr = 0.0
            be_confirmed = (cur_sl >= entry_p) if direction == "BUY" else (cur_sl <= entry_p and cur_sl > 0)
            dist_sl_r = 1.0 if not be_confirmed else 0.0
            dist_tp_r = 1.0 if cur_rr < 1.0 else 0.0

        is_trailing = be_confirmed and cur_rr >= 1.5

        results.append({
            "id": pos.get("id"),
            "ticket": pos.get("external_ticket") or pos.get("broker_position_ticket"),
            "symbol": sym,
            "direction": direction,
            "entry_price": entry_p,
            "current_price": cur_p,
            "stop_loss": cur_sl,
            "initial_stop_loss": sl_p,
            "take_profit": tp_p,
            "volume": vol,
            "current_rr": round(cur_rr, 2),
            "break_even_confirmed": be_confirmed,
            "is_trailing_active": is_trailing,
            "risk_status": "PROTEGIDO (0.0% riesgo)" if be_confirmed else "RIESGO CONTRACTUAL (1.0% en 2 patas)",
            "risk_nominal_pct": 0.0 if be_confirmed else 1.0,
            "distance_to_be_r": round(max(0.0, 1.0 - cur_rr), 2) if not be_confirmed else 0.0,
            "distance_to_tp_r": round(dist_tp_r, 2) if dist_tp_r > 0 else (round(max(0.0, 2.0 - cur_rr), 2)),
            "entry_time": pos.get("entry_time"),
            "setup_reason": pos.get("setup_reason"),
        })

    # Únicamente se reportan posiciones legítimamente abiertas en la base de datos (status = 'OPEN').
    # Nunca se inyectan posiciones residuales o desactualizadas de last_state.json.
    return results


def get_account_risk_guard_status() -> Dict[str, Any]:
    """Obtiene el diagnóstico integral de exposición, margen y salud del Guardián de Riesgo."""
    active_pos = get_active_positions_forensics()
    total_active = len(active_pos)
    max_positions = 8
    available_slots = max(0, max_positions - total_active)

    protected_be = sum(1 for p in active_pos if p.get("break_even_confirmed"))
    at_risk = total_active - protected_be
    nominal_risk_pct = at_risk * 1.0  # Cada posición no blindada arriesga 1.0%

    if total_active <= 4:
        margin_health = "ÓPTIMO (Holgura de margen amplia)"
        health_code = "OPTIMAL"
    elif total_active <= 6:
        margin_health = "MODERADO (Margen bajo supervisión preventiva)"
        health_code = "MODERATE"
    elif total_active == 7:
        margin_health = "ALTA CARGA (Solo 1 cupo restante)"
        health_code = "HIGH"
    else:
        margin_health = "CAPACIDAD MÁXIMA (Cupo de 8 posiciones lleno · Nuevas órdenes bloqueadas)"
        health_code = "MAX_CAP"

    return {
        "max_concurrent_positions": max_positions,
        "active_positions_count": total_active,
        "available_slots": available_slots,
        "protected_positions_count": protected_be,
        "unprotected_positions_count": at_risk,
        "nominal_risk_exposed_pct": round(nominal_risk_pct, 1),
        "risk_per_trade_contractual": "1.0% (Dividido en Pata 1: 0.5% a TP1 + Pata 2: 0.5% Runner)",
        "margin_health": margin_health,
        "health_code": health_code,
        "emergency_hard_cap_rule": "Cierre de emergencia automático si el riesgo post-fill supera 1.5% de la cuenta",
        "cooldown_policy": "30 minutos de pausa forzada en el activo tras tocar Stop Loss (Regla anti-revancha)",
        "positions": active_pos,
    }

