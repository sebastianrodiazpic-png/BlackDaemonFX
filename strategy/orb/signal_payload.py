"""ORB signal contract and audit: quality is descriptive, never a probability."""
import logging


def build_signal_payload(signal_type, entry_price, sl_price, tp1_price, tp2_price,
                         quality_label, *, atr_frozen_m5=None, volume_status="VOLUMEN_NO_EVALUADO",
                         range_amplitude_ratio=None, levels_source="STRATEGY_PROJECTION", be_enabled=True):
    return {
        "strategy": "ORB_NY_v4", "signal": signal_type,
        "entry_price": float(entry_price), "sl_price": float(sl_price),
        "tp1_price": float(tp1_price), "tp2_price": float(tp2_price),
        "execution_policy": {"fixed_targets": True, "be_at_tp1": bool(be_enabled),
                             "be_protects_spread": bool(be_enabled)},
        "audit_metadata": {"atr_frozen_m5": atr_frozen_m5,
            "technical_quality": quality_label, "volume_status": volume_status,
            "range_amplitude_ratio": range_amplitude_ratio, "levels_source": levels_source,
            "quality_is_probability": False},
    }


def log_audit_summary(logger, signal_payload, risk_check_passed=None, *, execution_status="NOT_SENT"):
    audit = signal_payload.get("audit_metadata", {})
    policy = signal_payload.get("execution_policy", {})
    risk = "APROBADO" if risk_check_passed is True else "RECHAZADO" if risk_check_passed is False else "NO_CONFIRMADO"
    status = ("ENTRADA_AUTORIZADA" if risk_check_passed is True else
              "RECHAZADA_POR_RIESGO" if risk_check_passed is False else "PENDIENTE_DE_VALIDACION")
    record = {"status": status, "technical_status": "VALIDA", "risk_status": risk,
              "execution_status": execution_status, "signal_payload": signal_payload}
    message = (
        "AUDITORÍA ORB NY v4 | Estado=%s | Técnica=VALIDA | Calidad=%s (no es probabilidad) | "
        "Riesgo=%s | Ejecución=%s | %s @ %s | SL=%s TP1=%s TP2=%s | "
        "BE tras TP1=%s Protege spread=%s | ATR congelado=%s Ratio rango=%s Volumen=%s"
    )
    logger.log(logging.WARNING if risk_check_passed is False else logging.INFO, message,
        status, audit.get("technical_quality"), risk, execution_status,
        signal_payload["signal"], signal_payload["entry_price"], signal_payload["sl_price"],
        signal_payload["tp1_price"], signal_payload["tp2_price"], policy.get("be_at_tp1"),
        policy.get("be_protects_spread"), audit.get("atr_frozen_m5"),
        audit.get("range_amplitude_ratio"), audit.get("volume_status"))
    return record
