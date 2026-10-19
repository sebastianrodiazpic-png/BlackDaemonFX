"""
scratch/audit_data_coverage_universe.py
Inspección forense de la cobertura de datos en data/cache_msnr y data/historical
"""
import pickle
import pandas as pd
from pathlib import Path

def main():
    cache_dir = Path("data/cache_msnr")
    print("=" * 100)
    print("AUDITORÍA DE UNIVERSO Y COBERTURA TEMPORAL REAL EN data/cache_msnr")
    print("=" * 100)
    
    files = sorted(list(cache_dir.glob("*_M15.pkl")))
    print(f"Total archivos M15 encontrados en data/cache_msnr: {len(files)}")
    
    records = []
    for f in files:
        symbol = f.stem.replace("_M15", "")
        h1_file = cache_dir / f"{symbol}_H1.pkl"
        
        try:
            with open(f, "rb") as pkl_f:
                df_m15 = pickle.load(pkl_f)
            
            m15_len = len(df_m15)
            # Detectar columna datetime
            dt_col = 'time' if 'time' in df_m15.columns else 'datetime' if 'datetime' in df_m15.columns else df_m15.index.name or 'index'
            if dt_col in df_m15.columns:
                m15_start = pd.to_datetime(df_m15[dt_col].iloc[0])
                m15_end = pd.to_datetime(df_m15[dt_col].iloc[-1])
            else:
                m15_start = pd.to_datetime(df_m15.index[0])
                m15_end = pd.to_datetime(df_m15.index[-1])
                
            m15_days = (m15_end - m15_start).total_seconds() / 86400.0
            m15_years = m15_days / 365.25
            
            h1_len = 0
            h1_years = 0
            if h1_file.exists():
                with open(h1_file, "rb") as h1_f:
                    df_h1 = pickle.load(h1_f)
                h1_len = len(df_h1)
                dt_h1 = 'time' if 'time' in df_h1.columns else 'datetime' if 'datetime' in df_h1.columns else df_h1.index.name or 'index'
                if dt_h1 in df_h1.columns:
                    h1_start = pd.to_datetime(df_h1[dt_h1].iloc[0])
                    h1_end = pd.to_datetime(df_h1[dt_h1].iloc[-1])
                else:
                    h1_start = pd.to_datetime(df_h1.index[0])
                    h1_end = pd.to_datetime(df_h1.index[-1])
                h1_years = (h1_end - h1_start).total_seconds() / (86400.0 * 365.25)
            
            has_5y_m15 = m15_years >= 4.9
            
            records.append({
                "symbol": symbol,
                "m15_rows": m15_len,
                "m15_start": str(m15_start)[:10],
                "m15_end": str(m15_end)[:10],
                "m15_years": round(m15_years, 2),
                "h1_rows": h1_len,
                "h1_years": round(h1_years, 2),
                "has_5y_m15": has_5y_m15
            })
        except Exception as e:
            records.append({
                "symbol": symbol,
                "error": str(e)
            })
            
    df_out = pd.DataFrame(records)
    print(df_out.to_string())
    
    print("\n" + "=" * 100)
    print("RESUMEN DE COBERTURA 5 AÑOS M15:")
    print("=" * 100)
    print(f"Total activos analizados: {len(df_out)}")
    if 'has_5y_m15' in df_out.columns:
        cnt_5y = df_out['has_5y_m15'].sum()
        print(f"Activos con >= 4.9 años en M15: {cnt_5y}")
        print(f"Activos sin 5 años en M15: {len(df_out) - cnt_5y}")
        print("\nDistribución de años M15:")
        print(df_out['m15_years'].describe())

if __name__ == '__main__':
    main()
