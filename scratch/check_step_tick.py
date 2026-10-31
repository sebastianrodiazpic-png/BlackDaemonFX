import sys
sys.path.insert(0, ".")
from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider

conn = MT5Connector()
prov = MT5DataProvider(conn)
prov.connect()
tick = prov.get_current_tick("Step Index")
print("Step Index Current Tick:", tick)
prov.disconnect()
