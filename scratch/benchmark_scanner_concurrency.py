import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

arch_dir = Path("storage/runtime/m1_prospective_cache")
runner = ProspectiveM1ReplayRunner(dry_run=True, archive_dir=arch_dir)
symbols = ["Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Jump 10 Index", "Crash 600 Index", "Boom 300 Index"]
runner.fetch_market_data(symbols)

def mock_analyze_symbol(sym):
    """Simula el tiempo de cómputo de indicadores SMC/MSNR sobre 1000 velas M1."""
    df = runner.cache_m1[sym]
    # Operaciones numéricas reales típicas: EMA, ATR, detección de fractales
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    
    # 1. Simulación de ATR y medias móviles
    tr = [max(h - l, abs(h - c), abs(l - c)) for h, l, c in zip(highs[1:], lows[1:], closes[:-1])]
    atr = sum(tr[-14:]) / 14.0
    
    # 2. Búsqueda de fractales y FVG
    fvg_count = 0
    for i in range(2, len(df)):
        if highs[i-2] < lows[i]:  # Bullish FVG
            fvg_count += 1
        elif lows[i-2] > highs[i]:  # Bearish FVG
            fvg_count += 1
            
    # Simulación de latencia de I/O de red/broker típica (100 ms por símbolo en MT5/Deriv)
    time.sleep(0.05)
    return {"symbol": sym, "atr": atr, "fvg_count": fvg_count}

print("=" * 80)
print("BENCHMARK AISLADO: ESCANEO SECUENCIAL VS CONCURRENTE")
print("=" * 80)

# 1. Escaneo Secuencial (Arquitectura Actual de live_trading_engine.py)
t0 = time.perf_counter()
seq_results = []
latencies_seq = {}
for idx, sym in enumerate(symbols):
    t_start = time.perf_counter()
    res = mock_analyze_symbol(sym)
    t_end = time.perf_counter()
    seq_results.append(res)
    # Latencia acumulada hasta que el símbolo es atendido desde el inicio del ciclo
    latencies_seq[sym] = t_end - t0
    print(f"  [SECUENCIAL] Símbolo {idx+1}/{len(symbols)} ({sym:<16}): Demora acumulada = {latencies_seq[sym]:.4f}s")
t_total_seq = time.perf_counter() - t0
print(f"--> Tiempo total secuencial (6 símbolos): {t_total_seq:.4f}s | Proyección para 18 símbolos: {t_total_seq * 3:.2f}s\n")

# 2. Escaneo Concurrente (Arquitectura Optimizada Event-Driven / Worker Pool)
t0 = time.perf_counter()
latencies_conc = {}
with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
    futures = {executor.submit(mock_analyze_symbol, sym): sym for sym in symbols}
    for fut in futures:
        sym = futures[fut]
        res = fut.result()
        t_done = time.perf_counter() - t0
        latencies_conc[sym] = t_done
        print(f"  [CONCURRENTE] Símbolo ({sym:<16}): Atendido y completado en {latencies_conc[sym]:.4f}s")
t_total_conc = time.perf_counter() - t0
print(f"--> Tiempo total concurrente (6 símbolos): {t_total_conc:.4f}s | Proyección para 18 símbolos: ~{t_total_conc:.2f}s\n")

print("=" * 80)
print("RESUMEN DE REDUCCIÓN DE LATENCIA DE SONDEO:")
print(f"  - Máxima espera en cola (Secuencial): {max(latencies_seq.values()):.4f}s")
print(f"  - Máxima espera en cola (Concurrente): {max(latencies_conc.values()):.4f}s")
print(f"  - Factor de aceleración en disponibilidad de señales: {max(latencies_seq.values()) / max(latencies_conc.values()):.1f}x")
print("=" * 80)
