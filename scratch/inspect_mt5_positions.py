import MetaTrader5 as mt5
import sys

if not mt5.initialize():
    print("MT5 initialize failed:", mt5.last_error())
    sys.exit(1)

positions = mt5.positions_get()
print(f"Total open positions in MT5: {len(positions) if positions else 0}")

if positions:
    for p in positions:
        d = p._asdict()
        print("\n--- POSICIÓN ---")
        for k in ("ticket", "symbol", "type", "magic", "volume", "price_open", "sl", "tp", "price_current", "profit", "comment", "time"):
            print(f"  {k}: {d.get(k)}")
        
        # Calcular R:R si tiene SL y TP
        open_price = d.get("price_open", 0)
        sl = d.get("sl", 0)
        tp = d.get("tp", 0)
        p_type = d.get("type", 0) # 0 = BUY, 1 = SELL
        
        risk_dist = abs(open_price - sl) if sl else 0
        reward_dist = abs(tp - open_price) if tp else 0
        rr = (reward_dist / risk_dist) if risk_dist > 0 else 0
        print(f"  -> Distancia Riesgo (SL): {risk_dist:.5f}")
        print(f"  -> Distancia Beneficio (TP): {reward_dist:.5f}")
        print(f"  -> R:R configurado en broker: {rr:.2f} R")

mt5.shutdown()
