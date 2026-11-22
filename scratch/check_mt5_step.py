from brokers.mt5_connector import MT5Connector
import MetaTrader5 as mt5

conn = MT5Connector()
print('MT5 connected:', conn.connect())
if conn.connected:
    for sym in ['Step Index', 'Step Index 200', 'Step Index 300', 'Step Index 400', 'Step Index 500']:
        mt5.symbol_select(sym, True)
        info = mt5.symbol_info(sym)
        tick = mt5.symbol_info_tick(sym)
        if info:
            spread = (tick.ask - tick.bid) if tick else info.spread * info.point
            point = info.point
            digits = info.digits
            min_lot = info.volume_min
            step_lot = info.volume_step
            bid = getattr(tick, "bid", None)
            ask = getattr(tick, "ask", None)
            print(f"{sym}: bid={bid}, ask={ask}, spread={spread:.4f}, point={point}, digits={digits}, min_lot={min_lot}, trade_mode={info.trade_mode}")
        else:
            print(f"{sym}: NOT FOUND")
    conn.disconnect()
