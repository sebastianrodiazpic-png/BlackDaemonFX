from pathlib import Path

path = Path("strategy/execution/live_trading_engine.py")
content = path.read_text(encoding="utf-8")

old_block = """        direction = str(signal.get("direction") or "").upper()
        try:
            candles = self.provider.get_candles(symbol, "M5", count=4)
            if candles is not None and not candles.empty and len(candles) >= 2:
                last_two = candles.tail(2)
                non_confirming = 0
                for _, c in last_two.iterrows():
                    o = float(c.get("open", 0.0))
                    cl = float(c.get("close", 0.0))
                    if direction == "BUY" and cl <= o:
                        non_confirming += 1
                    elif direction == "SELL" and cl >= o:
                        non_confirming += 1
                if non_confirming > 0:
                    return {
                        "symbol": str(symbol),
                        "action": "JUMP_STRICT_FILTER_REJECTED",
                        "reason": "JUMP_REQUIRES_TWO_CONSECUTIVE_CONFIRMING_CANDLES",
                        "failures": ["JUMP_TWO_CONSECUTIVE_CONFIRMING_CANDLES_REQUIRED"],
                        "direction": direction,
                    }
        except Exception:
            pass"""

new_block = """        direction = str(signal.get("direction") or "").upper()
        strat_name = str(signal.get("strategy_name") or "").upper()
        if strat_name not in {"ICT_SABRI_MALLE", "MALAYSIAN_SNR"}:
            try:
                candles = self.provider.get_candles(symbol, "M5", count=4)
                if candles is not None and not candles.empty and len(candles) >= 2:
                    last_two = candles.tail(2)
                    non_confirming = 0
                    for _, c in last_two.iterrows():
                        o = float(c.get("open", 0.0))
                        cl = float(c.get("close", 0.0))
                        if direction == "BUY" and cl <= o:
                            non_confirming += 1
                        elif direction == "SELL" and cl >= o:
                            non_confirming += 1
                    if non_confirming > 0:
                        return {
                            "symbol": str(symbol),
                            "action": "JUMP_STRICT_FILTER_REJECTED",
                            "reason": "JUMP_REQUIRES_TWO_CONSECUTIVE_CONFIRMING_CANDLES",
                            "failures": ["JUMP_TWO_CONSECUTIVE_CONFIRMING_CANDLES_REQUIRED"],
                            "direction": direction,
                        }
            except Exception:
                pass"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    path.write_text(content, encoding="utf-8", newline="")
    print("REPLACED OK")
else:
    print("OLD BLOCK NOT FOUND")
