"""
Diagnóstico de Latencia de Órdenes Críticas:
Verifica la discrepancia entre el tiempo real de resolución del Gateway (Callback/Event)
y la medición sesgada por iteración secuencial de futures.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scratch.isolated_serialized_mt5_gateway import (
    MockMT5Connector,
    SerializedMT5Gateway,
    PRIORITY_CRITICAL,
    PRIORITY_DATA,
)

conn = MockMT5Connector(io_delay_sec=0.03)
gw = SerializedMT5Gateway(conn)

futures = []
t0 = time.perf_counter()

# 1. Encolar 9 datos
for i in range(9):
    t_sub = time.perf_counter()
    f = gw.submit(conn.copy_rates_from_pos, f"SYM_{i}", "M5", 0, 100, priority=PRIORITY_DATA)
    futures.append(("DATA", f, t_sub, i))

# 2. Encolar 1 crítico
t_sub_crit = time.perf_counter()
f_crit = gw.submit(conn.order_send, {"symbol": "CRIT_ORDER"}, priority=PRIORITY_CRITICAL)
futures.append(("CRIT", f_crit, t_sub_crit, 999))

# 3. Encolar 9 datos más
for i in range(9, 18):
    t_sub = time.perf_counter()
    f = gw.submit(conn.copy_rates_from_pos, f"SYM_{i}", "M5", 0, 100, priority=PRIORITY_DATA)
    futures.append(("DATA", f, t_sub, i))

# Registro de callback exacto cuando el Gateway resuelve el Future
callback_latencies = {}
def on_done(fut):
    callback_latencies["CRIT"] = (time.perf_counter() - t_sub_crit) * 1000

f_crit.add_done_callback(on_done)

# 4. Simulación del bucle de consumo de la versión anterior del benchmark
loop_latencies = {}
for tag, fut, t_s, idx in futures:
    res = fut.result()
    time.sleep(0.001)  # Análisis sintético en CPU
    loop_latencies[f"{tag}_{idx}"] = (time.perf_counter() - t_s) * 1000

gw.shutdown(wait=True)

print("=" * 70)
print("DIAGNÓSTICO FORENSE DE LATENCIA CRÍTICA EN GATEWAY SERIAL")
print("=" * 70)
print(f"Latencia REAL de resolución del Gateway (Callback) : {callback_latencies['CRIT']:.2f} ms")
print(f"Latencia MEDIDA en el bucle iterativo secuencial   : {loop_latencies['CRIT_999']:.2f} ms")
print(f"Orden de procesamiento en el worker del Gateway     : {gw.processed_requests_log}")
print("=" * 70)
