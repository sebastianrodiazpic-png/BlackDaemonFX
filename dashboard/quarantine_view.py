"""Read-only quarantine diagnostics. Never releases symbols or changes risk limits."""
import json
from datetime import datetime, timezone
from pathlib import Path


def quarantine_snapshot(path=None, now=None):
    path = Path(path) if path else Path(__file__).resolve().parents[1] / "storage/risk_quarantine.json"
    now = now or datetime.now(timezone.utc)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Formato de cuarentena inválido")
        records = []
        for symbol, record in payload.items():
            if not isinstance(record, dict):
                raise ValueError("Registro de cuarentena inválido")
            expiry = record.get("expires_at")
            expired = False
            if expiry:
                dt = datetime.fromisoformat(str(expiry).replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                expired = dt <= now
            temporary = bool(record.get("recoverable")) and bool(expiry)
            status = ("PENDIENTE_REEVALUACION" if expired else "TEMPORAL") if temporary else "REVISION_MANUAL"
            records.append({
                "symbol": symbol, "since": record.get("quarantined_at"),
                "reason": record.get("reason"), "status": status,
                "expires_at": expiry, "direction": record.get("direction"),
                "trade_leg": record.get("trade_leg"),
                "target_risk": record.get("target_risk_amount"),
                "actual_risk": record.get("actual_risk_amount"),
                "hard_cap": record.get("hard_risk_cap"),
                "excess_ratio": record.get("risk_excess_ratio"),
                "actions": [
                    "Comparar precio calculado y ejecutado, spread y deslizamiento.",
                    "Revisar lote mínimo, paso de volumen y distancia del stop.",
                    "Evaluar una reserva previa al fill o rechazar tamaños que excedan el límite; validar en demo.",
                    "Revisar la causa antes de liberar manualmente; no aumentar el límite para ocultar el exceso."
                ] if record.get("reason") == "POST_FILL_RISK_HARD_CAP_BREACH" else [
                    "Revisar el motivo y la auditoría de ejecución antes de liberar el instrumento."
                ],
            })
        return {"status": "OK", "items": sorted(records, key=lambda x:x["symbol"]), "checked_at": now.isoformat()}
    except FileNotFoundError:
        return {"status": "OK", "items": [], "checked_at": now.isoformat()}
    except (OSError, ValueError, TypeError) as exc:
        return {"status": "ERROR", "items": [], "error": str(exc), "checked_at": now.isoformat()}
