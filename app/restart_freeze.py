"""Congelación de reinicios del coordinador multi-bot durante la sesión (11-nov-2026).

Cada reinicio borra el estado en memoria de los workers (límites virtuales ICT pendientes, retests MSNR en curso,
muestras de spread estable, estado de sesión ORB) y deja huecos sin operar. El 10→11-nov hubo al menos 10 reinicios
en 18 h y el daemon estuvo parado durante toda la killzone de Londres.

Regla: los reinicios se hacen dentro de la ventana de mantenimiento (por defecto 21:00–23:00 UTC, que coincide con
el rollover bancario, cuando Forex/ICT ya no abren entradas) y como máximo N veces por día. Un arranque en frío
(el bot llevaba parado más de `lookback` minutos) nunca se considera reinicio.

Modos (`DAEMONBLACKFX_RESTART_FREEZE`):
- `warn` (por defecto): registra el reinicio y avisa en consola; no bloquea.
- `enforce`: cancela el arranque fuera de la ventana salvo `DAEMONBLACKFX_RESTART_FREEZE_OVERRIDE=1`.
- `off`: sin registro ni aviso.

El código no puede impedir que alguien detenga el proceso; solo deja constancia y, en `enforce`, exige una
autorización explícita para volver a arrancar fuera de la ventana.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_MODE = "warn"
DEFAULT_MAINTENANCE_UTC = "21:00-23:00"
DEFAULT_LOOKBACK_MINUTES = 30.0
DEFAULT_MAX_PER_DAY = 1
HISTORY_FILE = "multi_bot_daemon.restarts.jsonl"


def parse_windows(text: str) -> list[tuple[int, int]]:
    """"21:00-23:00,05:30-06:00" -> [(1260, 1380), (330, 360)] en minutos UTC. Los tramos mal formados se ignoran."""
    windows = []
    for part in str(text or "").split(","):
        try:
            start, end = part.strip().split("-", 1)
            sh, sm = (int(x) for x in start.strip().split(":", 1))
            eh, em = (int(x) for x in end.strip().split(":", 1))
        except ValueError:
            continue
        if not (0 <= sh < 24 and 0 <= eh <= 24 and 0 <= sm < 60 and 0 <= em < 60):
            continue
        a, b = sh * 60 + sm, eh * 60 + em
        if a != b:
            windows.append((a, b))
    return windows


def in_windows(now_utc: datetime, windows: list[tuple[int, int]]) -> bool:
    """True si la hora UTC cae en algún tramo [inicio, fin). Un tramo puede cruzar la medianoche (22:00-01:00)."""
    minute = now_utc.hour * 60 + now_utc.minute
    return any((a <= minute < b) if a < b else (minute >= a or minute < b) for a, b in windows)


def last_worker_activity(project_root: Path) -> datetime | None:
    """Última escritura de cualquier log de worker: indica cuándo estuvo vivo el bot por última vez."""
    logs = Path(project_root) / "storage" / "logs" / "bots"
    latest = None
    try:
        for path in logs.glob("*.log"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            latest = mtime if latest is None or mtime > latest else latest
    except OSError:
        return None
    return datetime.fromtimestamp(latest, tz=timezone.utc) if latest is not None else None


def load_history(path: Path, since: datetime) -> list[dict]:
    rows = []
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                    if datetime.fromisoformat(row["at"]) >= since:
                        rows.append(row)
                except (ValueError, KeyError, TypeError):
                    continue
    except OSError:
        pass
    return rows


def evaluate(now_utc: datetime, *, mode: str, windows: list[tuple[int, int]], last_activity: datetime | None,
             history: list[dict], lookback_minutes: float, max_per_day: int, override: bool) -> dict:
    """Decide ALLOW / WARN / BLOCK para este arranque. Función pura (sin E/S) para poder probarla."""
    mode = mode if mode in ("off", "warn", "enforce") else DEFAULT_MODE
    idle_minutes = None if last_activity is None else max(0.0, (now_utc - last_activity).total_seconds() / 60.0)
    is_restart = idle_minutes is not None and idle_minutes <= float(lookback_minutes)
    in_maintenance = in_windows(now_utc, windows)
    restarts_24h = sum(1 for row in history if row.get("is_restart") and row.get("decision") != "BLOCK")
    report = {"at": now_utc.isoformat(), "mode": mode, "is_restart": bool(is_restart),
              "idle_minutes": None if idle_minutes is None else round(idle_minutes, 1),
              "in_maintenance_window": bool(in_maintenance), "restarts_last_24h": restarts_24h,
              "max_per_day": int(max_per_day), "override": bool(override)}
    if mode == "off" or not is_restart:
        return {**report, "decision": "ALLOW", "reason": "FREEZE_OFF" if mode == "off" else "COLD_START"}
    reasons = []
    if not in_maintenance:
        reasons.append("RESTART_OUTSIDE_MAINTENANCE_WINDOW")
    if max_per_day > 0 and restarts_24h >= max_per_day:
        reasons.append("RESTART_LIMIT_PER_DAY_REACHED")
    if not reasons:
        return {**report, "decision": "ALLOW", "reason": "RESTART_IN_MAINTENANCE_WINDOW"}
    reason = "+".join(reasons)
    if mode == "enforce" and not override:
        return {**report, "decision": "BLOCK", "reason": reason}
    return {**report, "decision": "WARN", "reason": reason + ("_OVERRIDDEN" if mode == "enforce" else "")}


def format_message(report: dict, maintenance_text: str) -> str:
    head = "[RESTART FREEZE] "
    if report["decision"] == "BLOCK":
        return (head + f"ARRANQUE CANCELADO ({report['reason']}). El bot estaba activo hace "
                f"{report['idle_minutes']} min y los reinicios estan congelados durante la sesion. "
                f"Ventana de mantenimiento UTC: {maintenance_text}. Reinicios en 24 h: {report['restarts_last_24h']} "
                f"(maximo {report['max_per_day']}). Para autorizar este arranque: "
                "set DAEMONBLACKFX_RESTART_FREEZE_OVERRIDE=1 y vuelva a ejecutar.")
    if report["decision"] == "WARN":
        return (head + f"AVISO ({report['reason']}): reinicio durante la sesion (bot activo hace "
                f"{report['idle_minutes']} min). Se pierden limites virtuales, retests y estado de sesion en memoria. "
                f"Ventana de mantenimiento UTC: {maintenance_text}. Reinicios en 24 h: "
                f"{report['restarts_last_24h'] + 1} (maximo {report['max_per_day']}).")
    return head + f"OK ({report['reason']})."


def check_and_record(project_root: Path, now_utc: datetime | None = None, env=None) -> dict:
    """Evalúa este arranque, lo anota en storage/runtime/multi_bot_daemon.restarts.jsonl y devuelve el informe."""
    env = os.environ if env is None else env
    now_utc = now_utc or datetime.now(timezone.utc)
    mode = str(env.get("DAEMONBLACKFX_RESTART_FREEZE", DEFAULT_MODE)).strip().lower()
    maintenance_text = str(env.get("DAEMONBLACKFX_RESTART_MAINTENANCE_UTC", DEFAULT_MAINTENANCE_UTC)).strip()

    def number(name, default):
        try:
            return float(env.get(name, default))
        except (TypeError, ValueError):
            return float(default)

    runtime_dir = Path(project_root) / "storage" / "runtime"
    history_path = runtime_dir / HISTORY_FILE
    report = evaluate(
        now_utc, mode=mode, windows=parse_windows(maintenance_text),
        last_activity=last_worker_activity(project_root),
        history=load_history(history_path, now_utc - timedelta(hours=24)),
        lookback_minutes=number("DAEMONBLACKFX_RESTART_FREEZE_LOOKBACK_MINUTES", DEFAULT_LOOKBACK_MINUTES),
        max_per_day=int(number("DAEMONBLACKFX_RESTART_MAX_PER_DAY", DEFAULT_MAX_PER_DAY)),
        override=str(env.get("DAEMONBLACKFX_RESTART_FREEZE_OVERRIDE", "0")).strip().lower() in ("1", "true", "on", "yes"))
    report["maintenance_utc"] = maintenance_text
    report["message"] = format_message(report, maintenance_text)
    if report["mode"] != "off":
        try:
            runtime_dir.mkdir(parents=True, exist_ok=True)
            with open(history_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({k: v for k, v in report.items() if k != "message"}, ensure_ascii=False) + "\n")
        except OSError:
            pass
    return report
