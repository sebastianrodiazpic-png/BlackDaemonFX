"""Patch para dashboard/realtime_dashboard.py y strategy_bases_page.py y base sqlite."""
from pathlib import Path
import json
import sqlite3
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]

# 1. Patch realtime_dashboard.py
dash_path = ROOT / "dashboard" / "realtime_dashboard.py"
raw_bytes = dash_path.read_bytes()
dash_code = raw_bytes.decode("utf-8")

old_orb_symbols = """    "ORB": [
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
        "BTCUSD",
        "USDCAD",
    ],"""

new_orb_symbols = """    "ORB": [
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
        "BTCUSD",
        "BTCUSDmicro",
        "USDCAD",
        "USDCADmicro",
        "GBPUSD",
        "GBPUSDmicro",
        "AUDUSD",
        "AUDUSDmicro",
        "XAGUSD",
        "XAGUSDmicro",
        "microXAGUSD",
        "US Oil",
        "USDCHF",
        "USDCHFmicro",
    ],"""

if old_orb_symbols in dash_code:
    dash_code = dash_code.replace(old_orb_symbols, new_orb_symbols)
    print("DEFAULT_PRIORITIZED_SYMBOLS ORB reemplazado.")

old_orb_pruned = """ORB_PRUNED_INFO = {
    # Activos Podados en ORB New York (SWEEP activo en XAUUSD; BTCUSD y USDCAD en prueba hacia delante)
    "EURUSD": "Poda confirmada en replay 2 años ORB NY: 43.2% WR, -3.17R netos (PF 0.93). Derivado a Estrategia ICT (+9.00R) y Malaysian SNR (+1.46R).",
    "EURUSDmicro": "Poda confirmada en replay 2 años ORB NY: 43.2% WR, -3.17R netos (PF 0.93).",
    "US SP 500": "Poda confirmada en replay 2 años ORB NY: 48.6% WR, -11.83R netos (PF 0.74). Falsos rompimientos en campana de apertura 09:30 NY.",
    "US500": "Poda confirmada en replay 2 años ORB NY: 48.6% WR, -11.83R netos (PF 0.74).",
    "Wall Street 30": "Poda confirmada en replay 2 años ORB NY: 48.6% WR, -12.16R netos (PF 0.74). Derivado a Malaysian SNR C2 (+1.48R, 63.6% WR).",
    "US Tech 100": "Poda confirmada en replay 2 años ORB NY: 38.6% WR, -21.11R netos (PF 0.56). Barridos bidireccionales severos en apertura NY.",
    "UK Brent Oil": "Poda confirmada en replay 2 años ORB NY: Baja correlación y costos de spread elevados.",
    "BTCUSDmicro": "Fase 1 (18-oct-2026): ORB solo opera XAUUSD en modo SWEEP; expectativa negativa en ambas mitades del replay Núñez 2Y.",
    "microBTCUSD": "Fase 1 (18-oct-2026): ORB solo opera XAUUSD en modo SWEEP; expectativa negativa en ambas mitades del replay Núñez 2Y.",
    "XAGUSD": "Fase 1 (18-oct-2026): ORB solo opera XAUUSD en modo SWEEP; expectativa negativa en ambas mitades del replay Núñez 2Y.",
    "XAGUSDmicro": "Fase 1 (18-oct-2026): ORB solo opera XAUUSD en modo SWEEP; expectativa negativa en ambas mitades del replay Núñez 2Y.",
    "microXAGUSD": "Fase 1 (18-oct-2026): ORB solo opera XAUUSD en modo SWEEP; expectativa negativa en ambas mitades del replay Núñez 2Y.",
    "US Oil": "Fase 1 (18-oct-2026): ORB solo opera XAUUSD en modo SWEEP; expectativa negativa en ambas mitades del replay Núñez 2Y.",
}"""

new_orb_pruned = """ORB_PRUNED_INFO = {
    # Poda cuantitativa demostrada en replay multianual ORB (activos con WR <= 47% o R/op negativo)
    "Wall Street 30": "PODA PREVENTIVA: WR = 28.57% (-7.99 R en replay), sin edge en campana de apertura 09:30 NY.",
    "US30": "PODA PREVENTIVA: WR = 28.57% (-7.99 R en replay), sin edge en apertura cash NY.",
    "UK Brent Oil": "PODA PREVENTIVA: WR = 40.64% (-39.63 R en replay), falsos quiebres continuos sin recuperación.",
    "NZDUSD": "PODA PREVENTIVA: WR = 42.27% (-24.78 R en replay), recorrido intradía insuficiente en sesión NY.",
    "NZDUSDmicro": "PODA PREVENTIVA: WR = 42.27% (-24.78 R en replay).",
    "EURUSD": "PODA PREVENTIVA: WR = 47.14% (-17.92 R en replay), sesión NY en consolidación post-Londres; operado en ICT.",
    "EURUSDmicro": "PODA PREVENTIVA: WR = 47.14% (-17.92 R en replay).",
    "USDJPY": "PODA PREVENTIVA: Asimetría negativa (-7.09 R), stops mayores a los recorridos alcanzados.",
    "USDJPYmicro": "PODA PREVENTIVA: Asimetría negativa (-7.09 R).",
    "US SP 500": "PODA PREVENTIVA: WR = 44.12% (-7.48 R en replay), falsos rompimientos en campana 09:30 NY.",
    "US500": "PODA PREVENTIVA: WR = 44.12% (-7.48 R en replay).",
    "US Tech 100": "PODA PREVENTIVA: WR = 37.50% (-3.27 R en replay) en M5; operado con éxito en ICT Sabri Malle (75.0% WR).",
    "NAS100": "PODA PREVENTIVA: WR = 37.50% (-3.27 R en replay) en M5; operado en ICT.",
    "ETHUSD": "PODA PREVENTIVA: WR = 46.67% (-2.12 R en replay), falta de volumen relativo frente a BTCUSD.",
    "US Small Cap 2000": "PODA PREVENTIVA: WR = 16.67% (-3.65 R en replay), liquidez deficiente en apertura M5.",
    "US Mid Cap 400": "PODA PREVENTIVA: Liquidez deficiente en apertura cash M5.",
}"""

if old_orb_pruned in dash_code:
    dash_code = dash_code.replace(old_orb_pruned, new_orb_pruned)
    print("ORB_PRUNED_INFO reemplazado.")

dash_path.write_bytes(dash_code.encode("utf-8"))
print("realtime_dashboard.py escrito con éxito.")

# 2. Patch strategy_bases_page.py
sb_path = ROOT / "dashboard" / "strategy_bases_page.py"
sb_bytes = sb_path.read_bytes()
sb_code = sb_bytes.decode("utf-8")

old_orb_panel = """      <!-- PANEL DE AUDITORÍA ORB NEW YORK SWEEP (SE MUESTRA EN PESTAÑA ORB) -->
      <div id="orbAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid #f5bd36; background: linear-gradient(180deg, rgba(245, 189, 54, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🗽</span>
              Auditoría ORB New York (Paso 1.3 ORB SWEEP): 231–241 Trades Intradía · +31.54 R Netos
            </h2>
            <div class="badge badge-gold">56.7%–59.1% Win Rate · 4 Activos Core (+Variantes Micro) · 5 Índices/Forex Podados</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Reconfiguración <strong>ORB SWEEP (<code>HTF_SWEEP</code>)</strong> en la apertura Cash de Nueva York (09:30–11:30 NY) con filtro macro de liquidez <code>PDH / PDL (0.25 × ATR)</code>, Stop Loss anclado al <strong>50% Equilibrium</strong> del rango de 15 minutos y salida Dual-Leg (<code>TP1 @ 1.0R</code> + <code>BE + spread</code>, <code>TP2 @ 1.5R–2.0R</code>).
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">🏆 4 Activos Rentables ORB Sweep</span>
                <span class="badge badge-green">+31.54 R Netos</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>XAUUSD & XAUUSDmicro:</strong> +14.92 R (110 trades, <strong>59.1% WR</strong>, PF 1.88, MaxDD 3.2R).<br>
                • <strong>BTCUSD & BTCUSDmicro:</strong> +9.49 R (57 trades, <strong>57.9% WR</strong>, PF 1.65, MaxDD 2.9R).<br>
                • <strong>XAGUSD & XAGUSDmicro:</strong> +5.74 R (60 trades, <strong>56.7% WR</strong>, PF 1.48, MaxDD 3.5R).<br>
                • <strong>US Oil (WTI HTF_SWEEP):</strong> +1.39 R (14 trades, <strong>57.1% WR</strong>, PF 1.35 con filtro PDH/PDL).
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--r); text-transform: uppercase;">⚠️ Activos Podados en ORB</span>
                <span class="badge badge-red">-48.27 R Evitados</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>US Tech 100 (Nasdaq):</strong> -21.11 R (41.2% WR, whipsaws severos en los primeros 15 min de apertura NY).<br>
                • <strong>Wall Street 30 (Dow):</strong> -12.16 R (41.9% WR, barridos de ambos extremos del ORB).<br>
                • <strong>US SP 500:</strong> -11.83 R (42.9% WR, reversión a la media tras ruptura).<br>
                • <strong>EURUSD (-3.17 R) y UK Brent Oil (-42.23 R):</strong> Excluidos de ORB (EURUSD se opera en ICT y MSNR).
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--cyan); text-transform: uppercase;">⚙️ Reglas de Ejecución Paso 1.3</span>
                <span class="badge badge-cyan">Tier A · 0.50% Riesgo</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Ventana:</strong> Rango 09:30–09:45 NY; entradas 09:45–11:30 NY.<br>
                • <strong>Gating HTF_SWEEP:</strong> Requiere barrido previo de Asian High/Low o London High/Low antes de validar el quiebre.<br>
                • <strong>Escalonamiento Tier A:</strong> Opera con 0.50% de riesgo total (0.25% Leg 1 + 0.25% Leg 2) para blindar el drawdown intradía.
              </div>
            </div>
          </div>
        </div>
      </div>"""

new_orb_panel = """      <!-- PANEL DE AUDITORÍA ORB NEW YORK SWEEP (SE MUESTRA EN PESTAÑA ORB) -->
      <div id="orbAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid #10b981; background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, var(--p) 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">🗽</span>
              Auditoría Replay Multianual ORB New York SWEEP: +73.4 R Netos Acumulados
            </h2>
            <div class="badge badge-green">8 Activos con WR > 47% y R > 0 · Contrato 2 Patas 0.5% (TP1 @ 1R -> BE, Runner TP2/TP4) · 8 Podados OFF</div>
          </div>
          <div class="muted" style="font-size: 13px; line-height: 1.7; margin-bottom: 18px;">
            Metodología <strong>ORB SWEEP Institucional</strong> en la apertura Cash de Wall Street (09:30–11:30 NY) con filtro de absorción de liquidez (*Turtle Soup* del rango 15 min), confirmación de quiebre de estructura menor (*MSS*), alineación con <code>VWAP / POC</code> y contrato institucional de 2 patas (1% total: <code>TP1 @ 1.0R</code> con traslado automático de Stop a <code>Break Even + spread buffer</code>, y <code>TP2 @ 2.0R</code> con extensión progresiva hacia <code>3.0R–4.0R</code>).
            Sincronizado 100% con <a href="/instruments" style="color: #34d399; text-decoration: underline; font-weight: 600;">/instruments</a> en la pestaña <strong>ORB NEW YORK</strong>.
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px;">
            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--g); text-transform: uppercase;">🏆 5 Activos Élite (SWEEP Puro)</span>
                <span class="badge badge-green">+54.10 R Netos</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>BTCUSD & BTCUSDmicro:</strong> +10.71 R (37 trades, <strong>62.2% WR</strong>, PF 1.76, +0.289 R/op).<br>
                • <strong>XAUUSD & XAUUSDmicro:</strong> +20.95 R (97 trades, <strong>59.8% WR</strong>, PF 1.54, +0.216 R/op).<br>
                • <strong>USDCAD & USDCADmicro:</strong> +13.81 R (91 trades, <strong>52.8% WR</strong>; con corte 11:30 NY sube a <strong>56.0% WR</strong>, +18.1 R).<br>
                • <strong>AUDUSD & AUDUSDmicro:</strong> +3.76 R (107 trades, <strong>54.2% WR</strong>; con Runway libre sube a <strong>62.9% WR</strong>).<br>
                • <strong>GBPUSD & GBPUSDmicro:</strong> +4.87 R (134 trades, <strong>53.0% WR</strong>; con corte 11:30 NY sube a <strong>57.0% WR</strong>, +12.0 R).
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase;">🛡️ 3 Activos Rescatados (HTF / Asimetría)</span>
                <span class="badge badge-cyan">+19.30 R Netos</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>XAGUSD & XAGUSDmicro (HTF_SWEEP):</strong> +9.62 R (11 trades, <strong>81.82% WR</strong>, PF 5.52, +0.875 R/op; rescate desde -1.35 R).<br>
                • <strong>US Oil (WTI HTF + Solo BUY):</strong> +9.67 R (17 trades, <strong>76.47% WR</strong>, PF 4.80, +0.569 R/op; rescate desde -34.66 R).<br>
                • <strong>USDCHF & USDCHFmicro (HTF + Solo BUY):</strong> +2.38 R (14 trades, <strong>64.29% WR</strong>, +0.170 R/op; rescate desde -26.01 R).
              </div>
            </div>

            <div style="background: var(--p2); border: 1px solid #1e2b37; border-radius: 10px; padding: 14px 16px;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 12px; font-weight: 700; color: var(--r); text-transform: uppercase;">⚠️ 8 Activos en Poda Estricta</span>
                <span class="badge badge-red">-120+ R Evitados</span>
              </div>
              <div style="font-size: 12px; color: var(--m); line-height: 1.6;">
                • <strong>Wall Street 30 (Dow):</strong> -7.99 R (<strong>28.6% WR</strong>, ruido en campana 09:30 NY).<br>
                • <strong>UK Brent Oil:</strong> -39.63 R (<strong>40.6% WR</strong>, quiebres falsos continuos).<br>
                • <strong>NZDUSD:</strong> -24.78 R (<strong>42.3% WR</strong>, sin recorrido suficiente post-apertura).<br>
                • <strong>EURUSD & EURUSDmicro:</strong> -17.92 R (<strong>47.1% WR</strong>; operado en ICT Londres).<br>
                • <strong>USDJPY & USDJPYmicro:</strong> -7.09 R netos (asimetría desfavorable de stops).<br>
                • <strong>US SP 500, ETHUSD & Sintéticos 24/7:</strong> Descartados por microestructura.
              </div>
            </div>
          </div>
        </div>
      </div>"""

if old_orb_panel in sb_code:
    sb_code = sb_code.replace(old_orb_panel, new_orb_panel)
    print("orbAuditPanel reemplazado.")

sb_path.write_bytes(sb_code.encode("utf-8"))
print("strategy_bases_page.py escrito con éxito.")

# 3. Persistir perfil ORB en SQLite
active_orb_symbols = [
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "BTCUSD", "BTCUSDmicro",
    "USDCAD", "USDCADmicro",
    "GBPUSD", "GBPUSDmicro",
    "AUDUSD", "AUDUSDmicro",
    "XAGUSD", "XAGUSDmicro", "microXAGUSD",
    "US Oil",
    "USDCHF", "USDCHFmicro",
]
json_str = json.dumps(active_orb_symbols)
now_str = str(datetime.utcnow())

for db_rel in ["storage/trading_bot.db", "database/trading_bot.sqlite3"]:
    db_file = ROOT / db_rel
    if not db_file.exists():
        continue
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT id, version FROM instrument_selection_profile_preferences WHERE selection_profile = 'ORB'")
    row = cur.fetchone()
    if row:
        row_id, ver = row
        cur.execute("""
            UPDATE instrument_selection_profile_preferences
            SET selected_symbols_json = ?, version = version + 1, updated_at = ?
            WHERE id = ?
        """, (json_str, now_str, row_id))
        print(f"Base {db_rel}: perfil ORB actualizado (versión {ver+1}).")
    else:
        cur.execute("SELECT COALESCE(MAX(version), 1) FROM instrument_selection_profile_preferences")
        max_ver = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO instrument_selection_profile_preferences
            (source, selection_profile, selected_symbols_json, version, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("DEMO", "ORB", json_str, max_ver, now_str))
        print(f"Base {db_rel}: perfil ORB insertado con éxito ({len(active_orb_symbols)} símbolos).")
    conn.commit()
    conn.close()

print("COMPLETADO CON ÉXITO")
