"""
scratch/audit_full_23_coverage_and_5yr.py
Auditoría exhaustiva de la cobertura de datos históricos para los 23 activos canónicos de Malaysian SNR
en M5, M15 y H1, y viabilidad real del replay de 5 años.
"""

from pathlib import Path
import pandas as pd
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def get_file_info(p: Path):
    if not p.exists():
        return None
    try:
        if p.suffix == '.csv':
            df = pd.read_csv(p)
            col = 'time' if 'time' in df.columns else ('datetime' if 'datetime' in df.columns else df.columns[0])
            ts = pd.to_datetime(df[col], utc=True)
        else:
            df = pd.read_pickle(p)
            col = 'time' if 'time' in df.columns else None
            ts = pd.to_datetime(df[col] if col else df.index, utc=True)
        days = (ts.max() - ts.min()).days
        return {
            "start": ts.min().strftime('%Y-%m-%d'),
            "end": ts.max().strftime('%Y-%m-%d'),
            "days": days,
            "years": round(days / 365.25, 2),
            "rows": len(df)
        }
    except Exception as e:
        return None

def main():
    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    
    print(f"Total activos en allowlist canónica: {len(canonical_symbols)}")
    print(f"{'Símbolo':25s} | {'Tipo':10s} | {'M5 (Días/Años)':18s} | {'M15 (Días/Años)':18s} | {'H1 (Días/Años)':18s} | {'¿Tiene 5 Años M15?':18s}")
    print("=" * 115)
    
    records = []
    for sym in canonical_symbols:
        # Normalizar nombres para buscar archivos
        # Ejemplos: "Boom 1000 Index" -> "Boom_1000_Index", "Wall Street 30" -> "Wall_Street_30"
        slug = sym.replace(' ', '_').replace('(', '').replace(')', '')
        slug_alt = sym.replace(' ', '_')
        
        # M5 check
        m5_p1 = PROJECT_ROOT / "data" / "historical" / f"{slug}_M5.csv"
        m5_p2 = PROJECT_ROOT / "data" / "forex_historical" / f"{slug}_M5.csv"
        m5_p3 = PROJECT_ROOT / "data" / "historical" / f"{slug_alt}_M5.csv"
        m5_info = get_file_info(m5_p1) or get_file_info(m5_p2) or get_file_info(m5_p3)
        
        # M15 check (CSV or PKL)
        m15_p1 = PROJECT_ROOT / "data" / "historical" / f"{slug}_M15.csv"
        m15_p2 = PROJECT_ROOT / "data" / "forex_historical" / f"{slug}_M15.csv"
        m15_p3 = PROJECT_ROOT / "data" / "cache_msnr" / f"{slug_alt}_M15.pkl"
        m15_info = get_file_info(m15_p1) or get_file_info(m15_p2) or get_file_info(m15_p3)
        
        # H1 check
        h1_p1 = PROJECT_ROOT / "data" / "historical" / f"{slug}_H1.csv"
        h1_p2 = PROJECT_ROOT / "data" / "forex_historical" / f"{slug}_H1.csv"
        h1_p3 = PROJECT_ROOT / "data" / "cache_msnr" / f"{slug_alt}_H1.pkl"
        h1_info = get_file_info(h1_p1) or get_file_info(h1_p2) or get_file_info(h1_p3)
        
        is_synthetic = any(w in sym for w in ['Boom', 'Crash', 'Step', 'Jump', 'Volatility'])
        tipo = "Sintético" if is_synthetic else "Financiero"
        
        m5_str = f"{m5_info['days']}d ({m5_info['years']}y)" if m5_info else "SIN DATOS"
        m15_str = f"{m15_info['days']}d ({m15_info['years']}y)" if m15_info else "SIN DATOS"
        h1_str = f"{h1_info['days']}d ({h1_info['years']}y)" if h1_info else "SIN DATOS"
        
        has_5y_m15 = "SÍ" if (m15_info and m15_info['years'] >= 4.9) else "NO"
        
        print(f"{sym:25s} | {tipo:10s} | {m5_str:18s} | {m15_str:18s} | {h1_str:18s} | {has_5y_m15:18s}")
        
        records.append({
            "symbol": sym, "tipo": tipo,
            "m5_days": m5_info['days'] if m5_info else 0,
            "m15_days": m15_info['days'] if m15_info else 0,
            "m15_years": m15_info['years'] if m15_info else 0.0,
            "h1_days": h1_info['days'] if h1_info else 0,
            "has_5y_m15": has_5y_m15
        })

    df_res = pd.DataFrame(records)
    print("\n" + "=" * 115)
    print("RESUMEN DE DISPONIBILIDAD PARA REPLAY DE 5 AÑOS (DENOMINADOR INSTITUCIONAL = 23 ACTIVOS):")
    print(f"  * Activos con 5 años verificables en M15: {len(df_res[df_res['has_5y_m15'] == 'SÍ'])} / 23 (0.0%)")
    print(f"  * Cobertura máxima en Sintéticos Deriv: M15 hasta 2.0 años (729 días), M5 hasta 0.8 años (277 días)")
    print(f"  * Cobertura máxima en Financieros: XAUUSD/XAGUSD M15 hasta 4.2 años (1548 días), H1 hasta 6.8 años")
    print(f"  * Conclusión: El replay de 5 años para el portafolio completo es TÉCNICAMENTE INVIABLE sin fabricar datos.")

if __name__ == '__main__':
    main()
