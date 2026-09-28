"""SMC 25/30/35/10 scoring; mandatory evidence cannot be bought with points."""


def calculate_adaptive_score(h1_data, m15_data, m5_data, confluences):
    points = dict(h1=0, m15=0, m5=0, confluences=0)
    veto_reasons, veto_codes = [], []
    def veto(code, reason):
        veto_codes.append(code)
        veto_reasons.append(reason)

    if not h1_data.get("is_valid_location", False):
        veto("H1_LOCATION_REQUIRED", "H1: Precio fuera de Discount/Premium o en equilibrio")
    elif h1_data.get("source") == "PIVOT":
        points["h1"] = 25
    elif h1_data.get("source") == "FALLBACK_24H":
        points["h1"] = 15
    else:
        veto("H1_SOURCE_REQUIRED", "H1: Fuente del rango desconocida")

    if m15_data.get("is_invalidated", False):
        veto("M15_OB_INVALIDATED", "M15: Order Block invalidado por cierre posterior")
    elif m15_data.get("break_quality") == "BOS":
        points["m15"] = 30
    elif m15_data.get("break_quality") == "SWEEP":
        points["m15"] = 20
    elif m15_data.get("has_displacement", False):
        points["m15"] = 10
    else:
        veto("M15_EVIDENCE_REQUIRED", "M15: OB sin desplazamiento ni ruptura minima")

    from strategy.smc.m5_freshness import evaluate_m5_confirmation_detailed
    m5_detail = evaluate_m5_confirmation_detailed(m5_data,
        current_time_m5=m5_data.get('evaluation_time'),
        max_age_minutes=m5_data.get('max_age_minutes', 10),
        check_freshness=m5_data.get('freshness_required', 'choch_timestamp' in m5_data))
    points['m5'] = m5_detail['m5_score']
    veto_reasons.extend(m5_detail['veto_reasons'])
    veto_codes.extend(m5_detail['veto_codes'])
    points["confluences"] = 5*bool(confluences.get("volume_ok", False)) + 5*bool(confluences.get("exhaustion_or_div", False))
    score = sum(points.values())
    status = ("REJECTED" if veto_reasons else "STRICT_APPROVED" if score >= 85 else
              "ADAPTIVE_APPROVED" if score >= 70 else "REJECTED_LOW_SCORE")
    return dict(approved=status in {"STRICT_APPROVED", "ADAPTIVE_APPROVED"},
                status=status, final_score=score, score_breakdown=points, m5_detail=m5_detail,
                reasons=veto_reasons if veto_reasons else ([f"Puntuacion insuficiente ({score}/70)"] if score < 70 else []),
                veto_codes=veto_codes,
                fvg_missing_but_allowed=not m5_data.get("has_fvg", False) and status in {"STRICT_APPROVED", "ADAPTIVE_APPROVED"})
