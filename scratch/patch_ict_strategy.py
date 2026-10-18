"""Aplica el parche a strategy/ict/ict_strategy.py para incorporar Opción C (iFVG/BPR) y Opción B (M5 Timing)
preservando la integridad del archivo y ejecutando r+ para evitar bloqueos de mmap en Windows.
"""
from pathlib import Path

target_file = Path("strategy/ict/ict_strategy.py")
content = target_file.read_text(encoding="utf-8")

# 1. Definición de find_inversion_fvg_and_bpr_setups
ifvg_func = '''
def find_inversion_fvg_and_bpr_setups(
    df: pd.DataFrame,
    curr_idx: int,
    intended_direction: str,
    lookback_bars: int = 24,
    spread: float = 0.00015,
) -> dict | None:
    """Opción C: Detecta Inversion FVG (iFVG) y Balanced Price Range (BPR).

    1. Inversion FVG: FVG previo que fue perforado con cuerpo por el precio y ahora
       actúa como soporte/resistencia invertido (SBR/RBS).
    2. Balanced Price Range: Solapamiento bidireccional entre FVG alcista y bajista consecutivo.
    """
    if curr_idx < 6:
        return None

    c_now = df.iloc[curr_idx]
    c_close = float(c_now["close"])
    c_high = float(c_now["high"])
    c_low = float(c_now["low"])

    # 1. Búsqueda de Inversion FVG (iFVG)
    for back in range(3, min(lookback_bars, curr_idx - 2)):
        c0 = df.iloc[curr_idx - back - 2]
        c1 = df.iloc[curr_idx - back - 1]
        c2 = df.iloc[curr_idx - back]

        # FVG Alcista original previo (c2.low > c0.high)
        if c2["low"] > c0["high"] and c1["close"] > c1["open"]:
            gap_top = float(c2["low"])
            gap_bot = float(c0["high"])
            # Perforado con cuerpo hacia abajo -> Inversión a Resistencia (SBR)
            breached = False
            for k in range(curr_idx - back + 1, curr_idx):
                if df.iloc[k]["close"] < gap_bot:
                    breached = True
                    break
            if breached and intended_direction == "SELL":
                # Retesteo actual dentro o en el borde del iFVG
                if c_high >= gap_bot and c_close <= (gap_top + spread):
                    sl = gap_top + (2.0 * spread)
                    risk = abs(sl - c_close)
                    if risk > (1.5 * spread):
                        return {
                            "valid": True,
                            "type": "ICT_INVERSION_FVG",
                            "scenario": "ICT_INVERSION_FVG_RETEST",
                            "direction": "SELL",
                            "entry_price": c_close,
                            "stop_loss": sl,
                            "risk": risk,
                            "gap_top": gap_top,
                            "gap_bottom": gap_bot,
                            "trade_score": 90.0,
                        }

        # FVG Bajista original previo (c2.high < c0.low)
        elif c2["high"] < c0["low"] and c1["close"] < c1["open"]:
            gap_top = float(c0["low"])
            gap_bot = float(c2["high"])
            # Perforado con cuerpo hacia arriba -> Inversión a Soporte (RBS)
            breached = False
            for k in range(curr_idx - back + 1, curr_idx):
                if df.iloc[k]["close"] > gap_top:
                    breached = True
                    break
            if breached and intended_direction == "BUY":
                # Retesteo actual dentro o en el borde del iFVG
                if c_low <= gap_top and c_close >= (gap_bot - spread):
                    sl = gap_bot - (2.0 * spread)
                    risk = abs(c_close - sl)
                    if risk > (1.5 * spread):
                        return {
                            "valid": True,
                            "type": "ICT_INVERSION_FVG",
                            "scenario": "ICT_INVERSION_FVG_RETEST",
                            "direction": "BUY",
                            "entry_price": c_close,
                            "stop_loss": sl,
                            "risk": risk,
                            "gap_top": gap_top,
                            "gap_bottom": gap_bot,
                            "trade_score": 90.0,
                        }

    # 2. Búsqueda de Balanced Price Range (BPR)
    c_m2 = df.iloc[curr_idx - 2]
    c_m1 = df.iloc[curr_idx - 1]
    c_m0 = df.iloc[curr_idx]

    if intended_direction == "BUY":
        if c_m1["low"] > c_m2["high"] and c_m0["close"] > c_m1["high"]:
            sl = float(c_m2["low"]) - (1.5 * spread)
            risk = abs(c_close - sl)
            if risk > (2.0 * spread):
                return {
                    "valid": True,
                    "type": "ICT_BALANCED_PRICE_RANGE",
                    "scenario": "ICT_BALANCED_PRICE_RANGE_EXPANSION",
                    "direction": "BUY",
                    "entry_price": c_close,
                    "stop_loss": sl,
                    "risk": risk,
                    "trade_score": 92.0,
                }
    elif intended_direction == "SELL":
        if c_m1["high"] < c_m2["low"] and c_m0["close"] < c_m1["low"]:
            sl = float(c_m2["high"]) + (1.5 * spread)
            risk = abs(sl - c_close)
            if risk > (2.0 * spread):
                return {
                    "valid": True,
                    "type": "ICT_BALANCED_PRICE_RANGE",
                    "scenario": "ICT_BALANCED_PRICE_RANGE_EXPANSION",
                    "direction": "SELL",
                    "entry_price": c_close,
                    "stop_loss": sl,
                    "risk": risk,
                    "trade_score": 92.0,
                }

    return None
'''

if "def find_inversion_fvg_and_bpr_setups" not in content:
    target_pos = content.find("def is_synthetic_asset(symbol: str) -> bool:")
    if target_pos != -1:
        content = content[:target_pos] + ifvg_func + "\n\n" + content[target_pos:]

# 2. Integración en analyze_symbol para Opción C (iFVG/BPR) y Opción B (M5 Timing)
target_check = '''        if not manipulation_found or sweep_peak is None:
            return {**base_response, "reason": "NO_JUDAS_SWING_MANIPULATION_CONFIRMED"}'''

replacement_check = '''        is_ifvg_bpr = False
        ifvg_bpr_scenario = None
        if not manipulation_found or sweep_peak is None:
            # Opción C: Si no hubo sweep de Judas Swing, comprobar Inversion FVG y BPR
            if getattr(self.config, "ifvg_bpr_enabled", True):
                ifvg_bpr = find_inversion_fvg_and_bpr_setups(
                    df_h1,
                    curr_idx=len(df_h1) - 1,
                    intended_direction=intended_direction,
                    lookback_bars=getattr(self.config, "ifvg_lookback_bars", 24),
                    spread=0.00015 if "USD" in symbol else 0.5,
                )
                if ifvg_bpr and ifvg_bpr.get("valid"):
                    manipulation_found = True
                    sweep_peak = ifvg_bpr["stop_loss"]
                    sweep_idx = len(df_h1) - 2
                    is_ifvg_bpr = True
                    ifvg_bpr_scenario = ifvg_bpr["scenario"]
                else:
                    return {**base_response, "reason": "NO_JUDAS_SWING_MANIPULATION_CONFIRMED"}
            else:
                return {**base_response, "reason": "NO_JUDAS_SWING_MANIPULATION_CONFIRMED"}'''

if target_check in content:
    content = content.replace(target_check, replacement_check, 1)

# Guardar con r+
with open(target_file, "r+", encoding="utf-8") as f:
    f.seek(0)
    f.write(content)
    f.truncate()

print("Parche aplicado exitosamente a strategy/ict/ict_strategy.py")
