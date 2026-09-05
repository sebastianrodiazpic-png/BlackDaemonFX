"""Chart-pattern confluence detector for DaemonBlackFx SMC.

Patterns are deliberately a *soft confluence* by default.  They never replace
liquidity/structure/OB/M5 gates.  The detector returns auditable anchors so the
dashboard can draw what was recognized.

Reference vocabulary mirrors the user's chart-pattern reference sheet:
triangles, double/triple tops/bottoms, pennants, wedges, rectangles, flags,
cup/handle, rounding bottom, diamond top/bottom and H&S variants.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import math
import numpy as np
import pandas as pd


@dataclass
class ChartPatternConfig:
    enabled: bool = True
    lookback: int = 80
    pivot_window: int = 2
    price_tolerance: float = 0.006
    # El antiguo 0.6% fijo era demasiado amplio para M5 en Forex/Oro y podía
    # convertir pivotes claramente distintos en dobles/triples techos o pisos.
    # La tolerancia efectiva queda limitada por la volatilidad reciente.
    volatility_adjusted_tolerance: bool = True
    price_tolerance_range_multiplier: float = 1.50
    minimum_price_tolerance: float = 0.00010
    minimum_strength: float = 0.72
    bonus_points: float = 8.0
    require_pattern: bool = False


BULLISH_PATTERNS = {
    "DOUBLE_BOTTOM", "TRIPLE_BOTTOM", "INVERTED_HEAD_AND_SHOULDERS",
    "ASCENDING_TRIANGLE", "BULLISH_PENNANT", "BULLISH_FLAG",
    "FALLING_WEDGE", "DESCENDING_BROADENING_WEDGE", "BULLISH_RECTANGLE",
    "CUP_AND_HANDLE", "ROUNDING_BOTTOM", "DIAMOND_BOTTOM",
}
BEARISH_PATTERNS = {
    "DOUBLE_TOP", "TRIPLE_TOP", "HEAD_AND_SHOULDERS",
    "DESCENDING_TRIANGLE", "BEARISH_PENNANT", "BEARISH_FLAG",
    "RISING_WEDGE", "ASCENDING_BROADENING_WEDGE", "BEARISH_RECTANGLE",
    "DIAMOND_TOP",
}
NEUTRAL_PATTERNS = {"SYMMETRICAL_TRIANGLE", "BROADENING_TRIANGLE"}


def _iso(v):
    try:
        return pd.Timestamp(v).isoformat()
    except Exception:
        return str(v)


def _lin_slope(values):
    a=np.asarray(values,dtype=float)
    if len(a)<2 or not np.all(np.isfinite(a)): return 0.0
    x=np.arange(len(a),dtype=float)
    den=float(np.sum((x-x.mean())**2))
    return 0.0 if den<=0 else float(np.sum((x-x.mean())*(a-a.mean()))/den)


def _pivots(df, w=2):
    highs=[]; lows=[]
    h=df["high"].astype(float).to_numpy()
    l=df["low"].astype(float).to_numpy()
    for i in range(w,len(df)-w):
        if h[i] >= np.max(h[i-w:i+w+1]): highs.append(i)
        if l[i] <= np.min(l[i-w:i+w+1]): lows.append(i)
    return highs,lows


def _near(a,b,tol):
    den=max(abs(float(a)),abs(float(b)),1e-12)
    return abs(float(a)-float(b))/den <= tol


def _effective_price_tolerance(df: pd.DataFrame, cfg: ChartPatternConfig) -> float:
    """Tolera pivotes equivalentes en unidades comparables entre contratos.

    ``price_tolerance`` continúa siendo el techo reproducible. El rango mediano
    de las velas cerradas evita que un 0.6% fijo sea enorme para FX/Oro y, al
    mismo tiempo, conserva una tolerancia útil en sintéticos más volátiles.
    """
    configured = max(0.0, float(cfg.price_tolerance))
    if not bool(cfg.volatility_adjusted_tolerance) or df is None or df.empty:
        return configured
    try:
        ranges = (df["high"].astype(float) - df["low"].astype(float)).abs()
        median_range = float(ranges.tail(min(40, len(ranges))).median())
        reference_price = float(df["close"].astype(float).abs().tail(min(40, len(df))).median())
        if not math.isfinite(median_range) or not math.isfinite(reference_price) or reference_price <= 0:
            return configured
        volatility_tolerance = (
            median_range / reference_price
            * max(0.0, float(cfg.price_tolerance_range_multiplier))
        )
        floor = max(0.0, float(cfg.minimum_price_tolerance))
        return min(configured, max(floor, volatility_tolerance))
    except Exception:
        return configured


def _evidence(df, pattern, direction, strength, anchors, note):
    pts=[]
    for idx,kind in anchors:
        if idx is None or idx<0 or idx>=len(df): continue
        price=float(df.iloc[idx]["high"] if kind=="high" else df.iloc[idx]["low"])
        pts.append({"time":_iso(df.iloc[idx]["time"]),"price":price,"kind":kind})
    return {
        "pattern": pattern,
        "direction": direction,
        "strength": round(float(max(0,min(1,strength))),3),
        "anchors": pts,
        "note": note,
    }


def _explain_chart_pattern_conflict(supporting, conflicting, wanted):
    """Devuelve nivel, razón y delta sin alterar la decisión de trading.

    Un patrón contrario estrictamente más fuerte que el alineado siempre es
    CONTRA_MAS_FUERTE, aunque la diferencia sea pequeña. FUERZAS_SIMILARES
    queda reservado al empate real o al caso en que el alineado domina por un
    margen insuficiente para considerarlo superior.
    """
    if not conflicting:
        return "NONE", None, None

    support_strength=float((supporting or {}).get("strength") or 0.0)
    oppose_strength=float((conflicting or {}).get("strength") or 0.0)
    delta=round(oppose_strength-support_strength,3)

    if supporting is None:
        return (
            "DOMINANT_CONTRA",
            f"Patrón contrario {conflicting['pattern']} {conflicting['direction']} "
            f"{oppose_strength*100:.0f}% sin patrón alineado equivalente para {wanted}.",
            delta,
        )
    if oppose_strength > support_strength:
        return (
            "CONTRA_MAS_FUERTE",
            f"{conflicting['pattern']} {conflicting['direction']} {oppose_strength*100:.0f}% "
            f"es más fuerte que {supporting['pattern']} {supporting['direction']} "
            f"{support_strength*100:.0f}%.",
            delta,
        )
    if support_strength - oppose_strength <= 0.05:
        return (
            "FUERZAS_SIMILARES",
            f"Patrones opuestos con fuerza similar: "
            f"{supporting['pattern']} {supporting['direction']} {support_strength*100:.0f}% vs "
            f"{conflicting['pattern']} {conflicting['direction']} {oppose_strength*100:.0f}%.",
            delta,
        )
    return (
        "CONTRA_SECUNDARIO",
        f"Existe patrón contrario {conflicting['pattern']} {conflicting['direction']} "
        f"{oppose_strength*100:.0f}%, pero el patrón alineado "
        f"{supporting['pattern']} {supporting['direction']} {support_strength*100:.0f}% "
        f"es más fuerte.",
        delta,
    )


def detect_chart_pattern_confirmation(data: pd.DataFrame, direction: str,
                                      confirmation_index: int,
                                      config: ChartPatternConfig|None=None) -> dict[str,Any]:
    cfg=config or ChartPatternConfig()
    empty={"chart_pattern_enabled":bool(cfg.enabled),"chart_pattern_confirmed":False,
           "chart_pattern_aligned":False,"chart_pattern_conflict":False,
           "chart_pattern_name":None,"chart_pattern_direction":None,
           "chart_pattern_strength":0.0,"chart_pattern_bonus":0.0,
           "chart_pattern_evidence":{},
           # v72: explicación explícita del conflicto chartista.
           "chart_pattern_supporting_pattern":None,
           "chart_pattern_supporting_direction":None,
           "chart_pattern_supporting_strength":0.0,
           "chart_pattern_supporting_evidence":{},
           "chart_pattern_conflicting_pattern":None,
           "chart_pattern_conflicting_direction":None,
           "chart_pattern_conflicting_strength":0.0,
           "chart_pattern_conflicting_evidence":{},
           "chart_pattern_conflict_level":"NONE",
           "chart_pattern_conflict_reason":None,
           "chart_pattern_conflict_strength_delta":None}
    if not cfg.enabled or data is None or data.empty or confirmation_index < 8:
        return empty

    start=max(0,int(confirmation_index)-int(cfg.lookback)+1)
    df=data.iloc[start:int(confirmation_index)+1].copy().reset_index(drop=True)
    needed={"time","open","high","low","close"}
    if not needed.issubset(df.columns) or len(df)<9: return empty
    hi,lo=_pivots(df,max(1,int(cfg.pivot_window)))
    close=float(df.iloc[-1]["close"])
    tol=_effective_price_tolerance(df, cfg)
    empty["chart_pattern_configured_price_tolerance"] = float(cfg.price_tolerance)
    empty["chart_pattern_effective_price_tolerance"] = float(tol)
    empty["chart_pattern_volatility_adjusted_tolerance"] = bool(cfg.volatility_adjusted_tolerance)
    candidates=[]

    # Double/triple top/bottom and H&S.
    if len(hi)>=2:
        a,b=hi[-2],hi[-1]
        if _near(df.iloc[a].high,df.iloc[b].high,tol):
            neck=float(df.iloc[a:b+1].low.min())
            strength=.72+min(.18,max(0,(neck-close)/max(abs(neck),1e-12))*30) if close<neck else .72
            candidates.append(_evidence(df,"DOUBLE_TOP","SELL",strength,[(a,"high"),(b,"high")],"Dos máximos equivalentes; neckline/intermedio validado."))
    if len(lo)>=2:
        a,b=lo[-2],lo[-1]
        if _near(df.iloc[a].low,df.iloc[b].low,tol):
            neck=float(df.iloc[a:b+1].high.max())
            strength=.72+min(.18,max(0,(close-neck)/max(abs(neck),1e-12))*30) if close>neck else .72
            candidates.append(_evidence(df,"DOUBLE_BOTTOM","BUY",strength,[(a,"low"),(b,"low")],"Dos mínimos equivalentes; neckline/intermedio validado."))
    if len(hi)>=3:
        a,b,c=hi[-3:]
        vals=[float(df.iloc[x].high) for x in (a,b,c)]
        if _near(vals[0],vals[1],tol) and _near(vals[1],vals[2],tol):
            candidates.append(_evidence(df,"TRIPLE_TOP","SELL",.78,[(a,"high"),(b,"high"),(c,"high")],"Tres máximos equivalentes."))
        if vals[1] > vals[0] and vals[1] > vals[2] and _near(vals[0],vals[2],tol*1.8):
            candidates.append(_evidence(df,"HEAD_AND_SHOULDERS","SELL",.82,[(a,"high"),(b,"high"),(c,"high")],"Hombro-cabeza-hombro con hombros similares."))
    if len(lo)>=3:
        a,b,c=lo[-3:]
        vals=[float(df.iloc[x].low) for x in (a,b,c)]
        if _near(vals[0],vals[1],tol) and _near(vals[1],vals[2],tol):
            candidates.append(_evidence(df,"TRIPLE_BOTTOM","BUY",.78,[(a,"low"),(b,"low"),(c,"low")],"Tres mínimos equivalentes."))
        if vals[1] < vals[0] and vals[1] < vals[2] and _near(vals[0],vals[2],tol*1.8):
            candidates.append(_evidence(df,"INVERTED_HEAD_AND_SHOULDERS","BUY",.82,[(a,"low"),(b,"low"),(c,"low")],"HCH invertido con hombros similares."))

    # Trend-line families: triangles / wedges / broadening.
    if len(hi)>=3 and len(lo)>=3:
        hs=hi[-4:]; ls=lo[-4:]
        hvals=[float(df.iloc[i].high) for i in hs]
        lvals=[float(df.iloc[i].low) for i in ls]
        sh=_lin_slope(hvals); sl=_lin_slope(lvals)
        scale=max(np.mean(np.abs(hvals+lvals)),1e-12)
        nh, nl = sh/scale, sl/scale
        flat=2.5e-4
        if abs(nh)<=flat and nl>flat:
            candidates.append(_evidence(df,"ASCENDING_TRIANGLE","BUY",.76,[(hs[-1],"high"),(ls[-1],"low")],"Resistencia plana y mínimos ascendentes."))
        elif nh<-flat and abs(nl)<=flat:
            candidates.append(_evidence(df,"DESCENDING_TRIANGLE","SELL",.76,[(hs[-1],"high"),(ls[-1],"low")],"Máximos descendentes y soporte plano."))
        elif nh<0 and nl>0:
            candidates.append(_evidence(df,"SYMMETRICAL_TRIANGLE","NEUTRAL",.74,[(hs[-1],"high"),(ls[-1],"low")],"Compresión convergente."))
        elif nh>0 and nl<0:
            candidates.append(_evidence(df,"BROADENING_TRIANGLE","NEUTRAL",.73,[(hs[-1],"high"),(ls[-1],"low")],"Expansión divergente."))
        elif nh<0 and nl<0 and nl>nh:
            candidates.append(_evidence(df,"FALLING_WEDGE","BUY",.77,[(hs[-1],"high"),(ls[-1],"low")],"Wedge descendente convergente."))
        elif nh>0 and nl>0 and nh<nl:
            candidates.append(_evidence(df,"RISING_WEDGE","SELL",.77,[(hs[-1],"high"),(ls[-1],"low")],"Wedge ascendente convergente."))
        elif nh<0 and nl<0 and nl<nh:
            candidates.append(_evidence(df,"DESCENDING_BROADENING_WEDGE","BUY",.74,[(hs[-1],"high"),(ls[-1],"low")],"Wedge descendente expansivo."))
        elif nh>0 and nl>0 and nh>nl:
            candidates.append(_evidence(df,"ASCENDING_BROADENING_WEDGE","SELL",.74,[(hs[-1],"high"),(ls[-1],"low")],"Wedge ascendente expansivo."))

    # Recent compact consolidation: rectangle / flag / pennant.
    tail=df.tail(min(20,len(df)))
    rng=float(tail.high.max()-tail.low.min())
    avg_body=float((tail.close-tail.open).abs().mean())
    compact= rng <= max(avg_body*8, abs(close)*.02)
    if compact:
        slope=_lin_slope(tail.close.astype(float).to_numpy())/max(abs(close),1e-12)
        if abs(slope)<2e-4:
            candidates.append(_evidence(df,"BULLISH_RECTANGLE" if str(direction).lower() in {"long","buy"} else "BEARISH_RECTANGLE",
                                        "BUY" if str(direction).lower() in {"long","buy"} else "SELL",.72,
                                        [(len(df)-1,"high"),(len(df)-1,"low")],"Consolidación rectangular compacta."))
        elif slope<0 and str(direction).lower() in {"long","buy"}:
            candidates.append(_evidence(df,"BULLISH_FLAG","BUY",.73,[(len(df)-1,"high"),(len(df)-1,"low")],"Canal correctivo descendente tras impulso."))
        elif slope>0 and str(direction).lower() in {"short","sell"}:
            candidates.append(_evidence(df,"BEARISH_FLAG","SELL",.73,[(len(df)-1,"high"),(len(df)-1,"low")],"Canal correctivo ascendente tras impulso."))

    # Rounded structures / cup-handle (lower priority, longer horizon).
    if len(df)>=35:
        c=df.close.astype(float).to_numpy()
        q=len(c)//4
        left=float(np.mean(c[:q])); mid=float(np.mean(c[q:3*q])); right=float(np.mean(c[3*q:]))
        if mid < min(left,right) and _near(left,right,tol*3):
            strength=.72
            pname="CUP_AND_HANDLE" if _lin_slope(c[-max(5,q):])<0 else "ROUNDING_BOTTOM"
            candidates.append(_evidence(df,pname,"BUY",strength,[(int(np.argmin(c)),"low"),(len(df)-1,"high")],
                                        "Base redondeada/copa detectada en ventana amplia."))

    if not candidates: return empty
    wanted="BUY" if str(direction).lower() in {"long","buy"} else "SELL"
    aligned=[c for c in candidates if c["direction"] in {wanted,"NEUTRAL"}]
    conflicts=[c for c in candidates if c["direction"] not in {wanted,"NEUTRAL"}]

    supporting=max(aligned,key=lambda x:x["strength"]) if aligned else None
    conflicting=max(conflicts,key=lambda x:x["strength"]) if conflicts else None
    best=supporting or max(candidates,key=lambda x:x["strength"])
    confirmed=bool(supporting and supporting["strength"]>=float(cfg.minimum_strength))
    conflict=bool(conflicting and conflicting["strength"]>=float(cfg.minimum_strength))

    conflict_level="NONE"
    conflict_reason=None
    conflict_delta=None
    if conflict:
        conflict_level, conflict_reason, conflict_delta = _explain_chart_pattern_conflict(
            supporting,
            conflicting,
            wanted,
        )

    return {
        **empty,
        "chart_pattern_confirmed": confirmed,
        "chart_pattern_aligned": bool(aligned),
        "chart_pattern_conflict": conflict,
        "chart_pattern_name": best["pattern"],
        "chart_pattern_direction": best["direction"],
        "chart_pattern_strength": best["strength"],
        "chart_pattern_bonus": float(cfg.bonus_points) if confirmed else 0.0,
        "chart_pattern_evidence": best,
        "chart_pattern_supporting_pattern": (supporting or {}).get("pattern"),
        "chart_pattern_supporting_direction": (supporting or {}).get("direction"),
        "chart_pattern_supporting_strength": float((supporting or {}).get("strength") or 0.0),
        "chart_pattern_supporting_evidence": supporting or {},
        "chart_pattern_conflicting_pattern": (conflicting or {}).get("pattern"),
        "chart_pattern_conflicting_direction": (conflicting or {}).get("direction"),
        "chart_pattern_conflicting_strength": float((conflicting or {}).get("strength") or 0.0),
        "chart_pattern_conflicting_evidence": conflicting or {},
        "chart_pattern_conflict_level": conflict_level,
        "chart_pattern_conflict_reason": conflict_reason,
        "chart_pattern_conflict_strength_delta": conflict_delta,
        "chart_pattern_candidates": sorted(candidates,key=lambda x:x["strength"],reverse=True)[:5],
    }
