import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

if not mt5.initialize():
    print("MT5 initialize failed")
    exit(0)

# Ver ultimas 24 horas
from_date = datetime.now(timezone.utc) - timedelta(hours=24)
to_date = datetime.now(timezone.utc) + timedelta(hours=1)

print(f"Buscando historial MT5 desde {from_date} hasta {to_date}")
deals = mt5.history_deals_get(from_date, to_date)
if deals is None:
    print("No deals found")
else:
    print(f"Total deals encontrados: {len(deals)}")
    for d in deals[-30:]:
        d_time = datetime.fromtimestamp(d.time, tz=timezone.utc)
        print(f"[{d_time}] Symbol: {d.symbol} | Type: {d.type} | Volume: {d.volume} | Price: {d.price} | Profit: {d.profit} | Comment: {d.comment}")

orders = mt5.history_orders_get(from_date, to_date)
if orders is not None:
    print(f"\nTotal orders encontradas: {len(orders)}")
    for o in orders[-20:]:
        o_time = datetime.fromtimestamp(o.time_setup, tz=timezone.utc)
        print(f"[{o_time}] Symbol: {o.symbol} | Type: {o.type} | State: {o.state} | Vol: {o.volume_initial} | Comment: {o.comment}")

# Ver posiciones abiertas actuales
pos = mt5.positions_get()
print(f"\nPosiciones abiertas actuales: {len(pos) if pos else 0}")
if pos:
    for p in pos:
        p_time = datetime.fromtimestamp(p.time, tz=timezone.utc)
        print(f"[{p_time}] Ticket: {p.ticket} | Symbol: {p.symbol} | Type: {p.type} | Volume: {p.volume} | Price: {p.price_open} | Profit: {p.profit}")

mt5.shutdown()
