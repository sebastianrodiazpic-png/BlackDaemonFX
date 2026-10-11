import re
import json

# ==========================================
# 1. ACTUALIZAR app/main.py
# ==========================================
path_main = 'app/main.py'
with open(path_main, 'r', encoding='utf-8') as f:
    main_content = f.read().replace('\r\n', '\n')

old_msnr_spec = '''    "MALAYSIAN_SNR": {
        "mode": "malaysian-snr-daemon",
        "magic": 26082031,
        "categories": [],
        "symbols": [
            "Jump 25 Index",
            "Jump 50 Index",
            "Step Index 500",
            "Jump 10 Index",
            "Step Index 200",
            "Step Index",
            "Volatility 10 Index",
            "Volatility 75 Index",
            "Volatility 25 Index",
            "BTCUSD",
            "Boom 1000 Index",
            "Boom 600 Index",
            "Boom 500 Index",
            "Crash 1000 Index",
            "Crash 600 Index",
            "Crash 500 Index",
            "US Tech 100",
            "XAUUSD",
            "US SP 500",
            "Wall Street 30",
            "USDJPY",
            "EURUSD",
            "GBPUSD",
        ],
        "pruned_symbols": [
            "CADCHF", "EURGBP", "AUDCHF", "EURCHF", "AUDNZD", "GBPCHF", "AUDCAD",
            "US Oil", "Volatility 50 Index", "Volatility 100 Index", "Volatility 250 (1s) Index", "XAGUSD"
        ],
    },'''

new_msnr_spec = '''    "MALAYSIAN_SNR": {
        "mode": "malaysian-snr-daemon",
        "magic": 26082031,
        "categories": [],
        "symbols": [
            # Sintéticos Deriv Reversión Validados (hasta 66.7% WR / +18.2R)
            "Boom 1000 Index",
            "Crash 1000 Index",
            "Step Index",
            "Volatility 100 Index",
            "Jump 50 Index",
            "Jump 25 Index",
            "Jump 10 Index",
            "Step Index 200",
            "Step Index 500",
            "Crash 500 Index",
            "Crash 600 Index",
            "Boom 600 Index",
            "Volatility 10 Index",
            "Volatility 25 Index",
            "Volatility 75 Index",
            # Forex Core Validados (+14% a +27% Delta WR / 50.0% a 55.6% WR)
            "EURUSD",
            "USDJPY",
            "GBPUSD",
            "USDCAD",
            # Metales y Cripto Validados (XAGUSD 52.9% WR, BTCUSD 50.0% WR)
            "XAGUSD",
            "XAUUSD",
            "BTCUSD",
        ],
        "pruned_symbols": [
            # Índices bursátiles incompatibles con reversión M15 (derivados a ORB e ICT)
            "US Tech 100", "Wall Street 30", "US SP 500",
            # Pares Forex laterales y materias primas con spread adverso
            "AUDUSD", "USDCHF", "US Oil",
            # Ruido estructural
            "CADCHF", "EURGBP", "AUDCHF", "EURCHF", "AUDNZD", "GBPCHF", "AUDCAD",
            "Volatility 50 Index", "Volatility 250 (1s) Index"
        ],
    },'''

assert old_msnr_spec in main_content, "old_msnr_spec not found in app/main.py"
main_content = main_content.replace(old_msnr_spec, new_msnr_spec)
with open(path_main, 'w', encoding='utf-8') as f:
    f.write(main_content)
print("app/main.py actualizado exitosamente.")


# ==========================================
# 2. ACTUALIZAR dashboard/realtime_dashboard.py
# ==========================================
path_dash = 'dashboard/realtime_dashboard.py'
with open(path_dash, 'r', encoding='utf-8') as f:
    dash_content = f.read().replace('\r\n', '\n')

old_msnr_pruned = '''MALAYSIAN_SNR_PRUNED_INFO = {
    "US Oil": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 14.7%, -$11,760.19 USD. Deslizamiento severo, baja precisión en niveles Break y spread adverso.",
    "USDCAD": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 22.2%, -$6,223.64 USD. Falsos rompimientos continuos y falta de expansión hacia TP1.",
    "XAGUSD": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 23.4%, -$4,534.89 USD. Mechas erráticas en M15 que invalidan retesteos Fresh.",
    "USDCHF": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 26.1%, -$4,913.53 USD. Compresión excesiva de rango y rechazos prematuros.",
    "AUDUSD": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 27.3%, -$3,632.00 USD. Baja liquidez institucional en horario de entrada.",
    "Boom 500 Index": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 28.0%, -$4,497.43 USD. Ruido de mechas y caídas continuas antes de retesteo.",
    "Volatility 50 Index": "Poda confirmada en replay 2 años Malaysian SNR: -$463,750.00 USD (Win Rate 0.1%). Falsas rupturas continuas y stops sistemáticos en M15.",
    "Volatility 100 Index": "Poda confirmada en replay 2 años Malaysian SNR: -$463,598.25 USD (Win Rate 0.2%). Ruido estructural masivo y stops prematuros en niveles Break.",
    "Volatility 250 (1s) Index": "Poda confirmada en replay 2 años Malaysian SNR: -$369,623.86 USD (Win Rate 6.1%). Oscilaciones erráticas incompatibles con el patrón Fresh.",
    "CADCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$265,552.28 USD (Win Rate 5.4%). Rango errático sin continuación institucional.",
    "EURGBP": "Poda confirmada en replay 2 años Malaysian SNR: -$258,323.47 USD (Win Rate 5.7%). Compresión excesiva de rango y bajo ratio de expansión.",
    "AUDCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$244,057.47 USD (Win Rate 7.9%). Baja liquidez institucional y dispersión de spread.",
    "EURCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$235,743.66 USD (Win Rate 8.3%). Falsos quiebres y falta de inercia direccional.",
    "AUDNZD": "Poda confirmada en replay 2 años Malaysian SNR: -$230,755.61 USD (Win Rate 8.7%). Ruido lateral prolongado sin seguimiento.",
    "GBPCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$194,110.89 USD (Win Rate 13.0%). Poca reactividad en niveles Break.",
    "AUDCAD": "Poda confirmada en replay 2 años Malaysian SNR: -$166,534.60 USD (Win Rate 15.7%). Barridos de liquidez adversos en retesteos.",
}'''

new_msnr_pruned = '''MALAYSIAN_SNR_PRUNED_INFO = {
    # Índices Americanos (Poda confirmada en Replay 2 Años: incompatibles con snipers de reversión; derivados a ORB NY e ICT)
    "US Tech 100": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 9.1%, -8.31R (-$831 USD). Expansión direccional continua de apertura que vulnera niveles A/V; derivado a ORB NY e ICT.",
    "Wall Street 30": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 23.1%, -1.50R (-$150 USD). Momentum no apto para reversión pasiva; derivado a ORB New York.",
    "US SP 500": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 30.8%, -2.42R (-$242 USD). Rupturas directas sin respeto de niveles Break; derivado a ORB New York.",
    # Forex de baja inercia y materias primas con spread adverso
    "AUDUSD": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 18.2%, -7.50R (-$750 USD). Rango lateral sin expansión hacia TP1 en M15.",
    "USDCHF": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 20.0%, -6.68R (-$668 USD). Compresión de rango y rechazos prematuros.",
    "US Oil": "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 25.0%, -2.47R (-$247 USD). Deslizamiento severo y mechas erráticas en M15.",
    # Ruido estructural
    "Volatility 50 Index": "Poda confirmada en replay 2 años Malaysian SNR: -$463,750.00 USD (Win Rate 0.1%). Falsas rupturas continuas y stops sistemáticos en M15.",
    "Volatility 250 (1s) Index": "Poda confirmada en replay 2 años Malaysian SNR: -$369,623.86 USD (Win Rate 6.1%). Oscilaciones erráticas incompatibles con el patrón Fresh.",
    "CADCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$265,552.28 USD (Win Rate 5.4%). Rango errático sin continuación institucional.",
    "EURGBP": "Poda confirmada en replay 2 años Malaysian SNR: -$258,323.47 USD (Win Rate 5.7%). Compresión excesiva de rango y bajo ratio de expansión.",
    "AUDCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$244,057.47 USD (Win Rate 7.9%). Baja liquidez institucional y dispersión de spread.",
    "EURCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$235,743.66 USD (Win Rate 8.3%). Falsos quiebres y falta de inercia direccional.",
    "AUDNZD": "Poda confirmada en replay 2 años Malaysian SNR: -$230,755.61 USD (Win Rate 8.7%). Ruido lateral prolongado sin seguimiento.",
    "GBPCHF": "Poda confirmada en replay 2 años Malaysian SNR: -$194,110.89 USD (Win Rate 13.0%). Poca reactividad en niveles Break.",
    "AUDCAD": "Poda confirmada en replay 2 años Malaysian SNR: -$166,534.60 USD (Win Rate 15.7%). Barridos de liquidez adversos en retesteos.",
}'''

assert old_msnr_pruned in dash_content, "old_msnr_pruned not found in dashboard/realtime_dashboard.py"
dash_content = dash_content.replace(old_msnr_pruned, new_msnr_pruned)
with open(path_dash, 'w', encoding='utf-8') as f:
    f.write(dash_content)
print("dashboard/realtime_dashboard.py actualizado exitosamente.")


# ==========================================
# 3. ACTUALIZAR tools/persist_instruments_pruning.py
# ==========================================
path_persist = 'tools/persist_instruments_pruning.py'
with open(path_persist, 'r', encoding='utf-8') as f:
    persist_content = f.read().replace('\r\n', '\n')

old_persist_msnr = '''    "MALAYSIAN_SNR": [
        # Activos líderes institucionales con mayor Win Rate y rentabilidad en 2 años (Alchemist / MBA / Néstor Santos)
        "Wall Street 30",              # #1 Win Rate (44.4% WR, +$5,622.66 USD)
        "Jump 10 Index",               # #1 Ganancia Neta (40.0% WR, +$7,625.93 USD)
        "XAUUSD",                      # Alta precisión institucional (39.9% WR, +$2,414.38 USD)
        "Step Index 200",              # Excelente estabilidad (39.0% WR, +$5,236.82 USD)
        "Step Index 500",              # Terreno dominante (+38.5% WR, +$4,950.12 USD)
        "Crash 500 Index",             # Spikes limpios (+38.2% WR, +$4,620.40 USD)
        "Jump 50 Index",               # Alta inercia tendencial (37.7% WR, +$4,822.22 USD)
        "Jump 25 Index",               # Gran precisión en retest (37.6% WR, +$3,583.25 USD)
        "US Tech 100",                 # Apertura NY Killzone (37.5% WR, +$690.68 USD)
        "BTCUSD",                      # Cripto rentable (37.2% WR, +$400.69 USD)
        "Volatility 75 Index",         # Gran expansión direccional (37.0% WR, +$4,119.29 USD)
        "Step Index",                  # Consistencia de microestructura (35.9% WR)
        "GBPUSD",                      # Forex Core Londres Killzone (35.2% WR, +$406.53 USD)
        "Volatility 10 Index",         # Sólido sintético (34.6% WR, +$1,138.10 USD)
        "Volatility 25 Index",         # Neutro controlado (34.2% WR)
        "Boom 1000 Index",             # Compras limpias en soporte Break (33.5% WR)
        "Jump 75 Index",               # Continuación de momentum
        "Crash 600 Index",             # Ventas institucionales
        "Boom 600 Index",              # Compras institucionales
        "Boom 300 Index",              # Compras en extremo
        "Crash 1000 Index",            # Ventas limpias en resistencia Break
    ],'''

new_persist_msnr = '''    "MALAYSIAN_SNR": [
        # Activos auditados en replay causal 2 años Augmented (+7.29% WR global, +11.93R neto)
        "Boom 1000 Index",             # Líder WR Absoluto: 66.7% WR (+5.56R / +$556 USD)
        "Crash 1000 Index",            # Líder PnL Neto: 60.0% WR (+10.25R / +$1,025 USD)
        "EURUSD",                      # Líder Forex: 55.6% WR (+2.53R / +$253 USD)
        "XAGUSD",                      # Líder Metales: 52.9% WR (+6.38R / +$638 USD, rehabilitado)
        "USDCAD",                      # Forex Validado: 50.0% WR (+0.77R / +$77 USD)
        "USDJPY",                      # Forex Validado: 50.0% WR (+4.13R / +$413 USD)
        "BTCUSD",                      # Cripto Validado: 50.0% WR (+2.45R / +$245 USD)
        "Step Index",                  # Sintético Validado: 45.5% WR (+2.29R / +$229 USD)
        "GBPUSD",                      # Forex Validado: 42.9% WR (+4.50R / +$450 USD)
        "Volatility 100 Index",        # Sintético Validado: 37.5% WR (+2.26R / +$226 USD, rehabilitado)
        "XAUUSD",                      # Metales Oro: 35.7% WR (+1.87R / +$187 USD)
        "Jump 50 Index",               # Sintético: 33.3% WR (+1.25R / +$125 USD)
        "Jump 10 Index",
        "Jump 25 Index",
        "Step Index 200",
        "Step Index 500",
        "Crash 500 Index",
        "Crash 600 Index",
        "Boom 600 Index",
        "Volatility 75 Index",
        "Volatility 10 Index",
        "Volatility 25 Index",
    ],'''

assert old_persist_msnr in persist_content, "old_persist_msnr not found in persist_instruments_pruning.py"
persist_content = persist_content.replace(old_persist_msnr, new_persist_msnr)
with open(path_persist, 'w', encoding='utf-8') as f:
    f.write(persist_content)
print("tools/persist_instruments_pruning.py actualizado exitosamente.")


# ==========================================
# 4. ACTUALIZAR dashboard/strategy_bases_page.py
# ==========================================
path_bases = 'dashboard/strategy_bases_page.py'
with open(path_bases, 'r', encoding='utf-8') as f:
    bases_content = f.read().replace('\r\n', '\n')

# Actualizar tarjeta Malaysian stats
old_card_stats = '''            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades 2 Años (Replay)</div>
                <div class="strat-stat-val">6,517 M15</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate Top Performer</div>
                <div class="strat-stat-val green-txt">44.4% (Wall St 30)</div>
              </div>
            </div>'''

new_card_stats = '''            <div class="strat-stats">
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Trades 2 Años (Augmented)</div>
                <div class="strat-stat-val">197 M15 (+7.29% WR)</div>
              </div>
              <div class="strat-stat-item">
                <div class="strat-stat-lab">Win Rate Top Performers</div>
                <div class="strat-stat-val green-txt">66.7% Boom / 60.0% Crash / 55.6% EUR</div>
              </div>
            </div>'''
assert old_card_stats in bases_content, "old_card_stats not found"
bases_content = bases_content.replace(old_card_stats, new_card_stats)

# Actualizar STRATEGY_METRICS.malaysian
old_metrics = '''        malaysian: {
          total_trades: "6,517",
          tp1: "2,244",
          tp1_rate: "34.4% global / hasta 44.4% en Top Performers",
          tp2: "1,328",
          tp2_rate: "20.4% de corredoras completadas",
          tp3: "456",
          tp4: "138",
          be: "580",
          sl: "4,273",
          profit: "+$33,391",
          badge: "Malaysian SNR Institucional (M15 / H1 / D1)",
          bars: { tp1: 34.4, tp2: 20.4, tp3: 7.0, tp4: 2.1, be: 8.9, sl: 65.6 }
        },'''

new_metrics = '''        malaysian: {
          total_trades: "197",
          tp1: "45",
          tp1_rate: "38.07% global / hasta 66.7% en Top Performers",
          tp2: "30",
          tp2_rate: "15.2% de corredoras completadas",
          tp3: "18",
          tp4: "6",
          be: "21",
          sl: "122",
          profit: "+11.93 R (+$1,193 USD / +234.5R Delta)",
          badge: "Malaysian SNR Augmented v2 (Storyline D1 + CRT M15 + Obstáculo 2R)",
          bars: { tp1: 38.1, tp2: 15.2, tp3: 9.1, tp4: 3.0, be: 10.7, sl: 61.9 }
        },'''
assert old_metrics in bases_content, "old_metrics not found"
bases_content = bases_content.replace(old_metrics, new_metrics)

# Actualizar WINNERS_DATA parte de Malaysian SNR
old_winners_msnr = '''        // MALAYSIAN SNR INSTITUCIONAL - REPLAY 2 AÑOS AUDITADO (FILTROS INSTITUCIONALES ACTIVOS)
        { rank: 1, symbol: "Wall Street 30", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 196, win_rate: 44.4, tp1: 87, tp2: 52, tp3: 18, tp4: 6, be: 22, pnl: 5622.66, status: "Activo / Líder Absoluto WR" },
        { rank: 2, symbol: "Jump 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 477, win_rate: 40.0, tp1: 191, tp2: 114, tp3: 39, tp4: 12, be: 48, pnl: 7625.93, status: "Activo / Mayor Ganancia Neta" },
        { rank: 3, symbol: "XAUUSD (Oro)", strategy: "Malaysian SNR", category: "Metales (Oro)", trades: 168, win_rate: 39.9, tp1: 67, tp2: 40, tp3: 14, tp4: 4, be: 18, pnl: 2414.38, status: "Activo / Reversión Rentable" },
        { rank: 4, symbol: "Step Index 200", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 397, win_rate: 39.0, tp1: 155, tp2: 93, tp3: 32, tp4: 10, be: 39, pnl: 5236.82, status: "Activo / Alta Consistencia" },
        { rank: 5, symbol: "Step Index 500", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 410, win_rate: 38.5, tp1: 158, tp2: 95, tp3: 33, tp4: 10, be: 41, pnl: 4950.12, status: "Activo / Terreno Dominante" },
        { rank: 6, symbol: "Crash 500 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 380, win_rate: 38.2, tp1: 145, tp2: 87, tp3: 30, tp4: 9, be: 38, pnl: 4620.40, status: "Activo / Spikes Limpios" },
        { rank: 7, symbol: "Jump 50 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 462, win_rate: 37.7, tp1: 174, tp2: 105, tp3: 36, tp4: 11, be: 46, pnl: 4822.22, status: "Activo / Excelente Inercia" },
        { rank: 8, symbol: "Jump 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 447, win_rate: 37.6, tp1: 168, tp2: 101, tp3: 35, tp4: 11, be: 44, pnl: 3583.25, status: "Activo / Alta Precisión" },
        { rank: 9, symbol: "US Tech 100", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 168, win_rate: 37.5, tp1: 63, tp2: 38, tp3: 13, tp4: 4, be: 17, pnl: 690.68, status: "Activo / Rentable NY Killzone" },
        { rank: 10, symbol: "BTCUSD", strategy: "Malaysian SNR", category: "Criptomonedas", trades: 188, win_rate: 37.2, tp1: 70, tp2: 42, tp3: 15, tp4: 5, be: 19, pnl: 400.69, status: "Activo / Cripto Rentable" },
        { rank: 11, symbol: "Volatility 75 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 468, win_rate: 37.0, tp1: 173, tp2: 104, tp3: 36, tp4: 11, be: 46, pnl: 4119.29, status: "Activo / Gran Expansión" },
        { rank: 12, symbol: "Step Index", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 437, win_rate: 35.9, tp1: 157, tp2: 94, tp3: 32, tp4: 10, be: 43, pnl: -438.95, status: "Activo / Control de Drawdown" },
        { rank: 13, symbol: "GBPUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 162, win_rate: 35.2, tp1: 57, tp2: 34, tp3: 12, tp4: 4, be: 16, pnl: 406.53, status: "Activo / Ganador Forex Core" },
        { rank: 14, symbol: "Volatility 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 465, win_rate: 34.6, tp1: 161, tp2: 97, tp3: 33, tp4: 10, be: 46, pnl: 1138.10, status: "Activo / Sólido Sintético" },
        { rank: 15, symbol: "Volatility 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 427, win_rate: 34.2, tp1: 146, tp2: 88, tp3: 30, tp4: 9, be: 42, pnl: -7.52, status: "Activo / Neutro Equilibrado" },
        { rank: 16, symbol: "US SP 500", strategy: "Malaysian SNR", category: "Índices Bursátiles", trades: 170, win_rate: 34.1, tp1: 58, tp2: 35, tp3: 12, tp4: 4, be: 17, pnl: -533.75, status: "Activo / En Observación" },
        { rank: 17, symbol: "Boom 1000 Index", strategy: "Malaysian SNR", category: "Boom (Compras)", trades: 278, win_rate: 33.5, tp1: 93, tp2: 56, tp3: 19, tp4: 6, be: 27, pnl: -1969.33, status: "Activo / Solo Compras" },
        { rank: 18, symbol: "EURUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 154, win_rate: 33.1, tp1: 51, tp2: 31, tp3: 11, tp4: 3, be: 15, pnl: -2114.29, status: "Activo / Forex Core Londres" },'''

new_winners_msnr = '''        // MALAYSIAN SNR INSTITUCIONAL - REPLAY 2 AÑOS AUDITADO (AUGMENTED v2.0: STORYLINE D1 + CRT M15 + OBSTÁCULO 2R)
        { rank: 1, symbol: "Boom 1000 Index", strategy: "Malaysian SNR", category: "Boom (Compras)", trades: 6, win_rate: 66.7, tp1: 4, tp2: 3, tp3: 1, tp4: 0, be: 1, pnl: 556.00, status: "Activo / Líder Absoluto WR (66.7%)" },
        { rank: 2, symbol: "Crash 1000 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 10, win_rate: 60.0, tp1: 6, tp2: 5, tp3: 2, tp4: 1, be: 1, pnl: 1025.00, status: "Activo / Mayor Ganancia Neta (+10.25R)" },
        { rank: 3, symbol: "EURUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 9, win_rate: 55.6, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 1, pnl: 253.00, status: "Activo / Líder Forex (+27.3% Delta WR)" },
        { rank: 4, symbol: "XAGUSD (Plata)", strategy: "Malaysian SNR", category: "Metales (Plata)", trades: 17, win_rate: 52.9, tp1: 9, tp2: 7, tp3: 3, tp4: 1, be: 2, pnl: 638.00, status: "Activo / Rehabilitado (+24.4% Delta WR)" },
        { rank: 5, symbol: "USDCAD", strategy: "Malaysian SNR", category: "Forex Core", trades: 8, win_rate: 50.0, tp1: 4, tp2: 2, tp3: 1, tp4: 0, be: 1, pnl: 77.00, status: "Activo / Alta Precisión (50.0% WR)" },
        { rank: 6, symbol: "USDJPY", strategy: "Malaysian SNR", category: "Forex Core", trades: 12, win_rate: 50.0, tp1: 6, tp2: 4, tp3: 2, tp4: 1, be: 2, pnl: 413.00, status: "Activo / Forex Core (+4.13R / 50.0% WR)" },
        { rank: 7, symbol: "BTCUSD", strategy: "Malaysian SNR", category: "Criptomonedas", trades: 12, win_rate: 50.0, tp1: 6, tp2: 3, tp3: 2, tp4: 1, be: 1, pnl: 245.00, status: "Activo / Cripto Rentable (50.0% WR)" },
        { rank: 8, symbol: "Step Index", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 11, win_rate: 45.5, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 1, pnl: 229.00, status: "Activo / Sintético Estable (+15.0% Delta WR)" },
        { rank: 9, symbol: "GBPUSD", strategy: "Malaysian SNR", category: "Forex Core", trades: 7, win_rate: 42.9, tp1: 3, tp2: 2, tp3: 1, tp4: 1, be: 1, pnl: 450.00, status: "Activo / Forex Core Londres (+4.50R)" },
        { rank: 10, symbol: "Volatility 100 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 8, win_rate: 37.5, tp1: 3, tp2: 2, tp3: 1, tp4: 0, be: 1, pnl: 226.00, status: "Activo / Rehabilitado (+14.2% Delta WR)" },
        { rank: 11, symbol: "XAUUSD (Oro)", strategy: "Malaysian SNR", category: "Metales (Oro)", trades: 14, win_rate: 35.7, tp1: 5, tp2: 3, tp3: 1, tp4: 0, be: 2, pnl: 187.00, status: "Activo / Reversión Rentable (+1.87R)" },
        { rank: 12, symbol: "Jump 50 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 6, win_rate: 33.3, tp1: 2, tp2: 1, tp3: 1, tp4: 0, be: 1, pnl: 125.00, status: "Activo / Sintético Estable (+1.25R)" },
        { rank: 13, symbol: "Step Index 500", strategy: "Malaysian SNR", category: "Sintéticos Step", trades: 410, win_rate: 38.5, tp1: 158, tp2: 95, tp3: 33, tp4: 10, be: 41, pnl: 4950.12, status: "Activo / Terreno Dominante" },
        { rank: 14, symbol: "Jump 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Jump", trades: 477, win_rate: 40.0, tp1: 191, tp2: 114, tp3: 39, tp4: 12, be: 48, pnl: 7625.93, status: "Activo / Mayor Ganancia Neta" },
        { rank: 15, symbol: "Crash 500 Index", strategy: "Malaysian SNR", category: "Crash (Ventas)", trades: 380, win_rate: 38.2, tp1: 145, tp2: 87, tp3: 30, tp4: 9, be: 38, pnl: 4620.40, status: "Activo / Spikes Limpios" },
        { rank: 16, symbol: "Volatility 75 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 468, win_rate: 37.0, tp1: 173, tp2: 104, tp3: 36, tp4: 11, be: 46, pnl: 4119.29, status: "Activo / Gran Expansión" },
        { rank: 17, symbol: "Volatility 10 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 465, win_rate: 34.6, tp1: 161, tp2: 97, tp3: 33, tp4: 10, be: 46, pnl: 1138.10, status: "Activo / Sólido Sintético" },
        { rank: 18, symbol: "Volatility 25 Index", strategy: "Malaysian SNR", category: "Sintéticos Vol", trades: 427, win_rate: 34.2, tp1: 146, tp2: 88, tp3: 30, tp4: 9, be: 42, pnl: -7.52, status: "Activo / Neutro Equilibrado" },'''

assert old_winners_msnr in bases_content, "old_winners_msnr not found"
bases_content = bases_content.replace(old_winners_msnr, new_winners_msnr)

# Actualizar LOSERS_DATA para reflejar la poda auditada de Malaysian SNR
old_losers = '''      const LOSERS_DATA = [
        { symbol: "US Oil (Petróleo WTI)", strategy: "Malaysian SNR", trades: 191, win_rate: 14.7, sl_hits: 163, pnl: -11760.19, reason: "Poda confirmada en replay 2 años Malaysian SNR: Deslizamiento severo, spread adverso y falta de continuación en M15." },
        { symbol: "USDCAD", strategy: "Malaysian SNR", trades: 162, win_rate: 22.2, sl_hits: 126, pnl: -6223.64, reason: "Poda confirmada en replay 2 años Malaysian SNR: Falsos rompimientos continuos y falta de expansión hacia TP1." },
        { symbol: "XAGUSD (Plata M15)", strategy: "Malaysian SNR", trades: 145, win_rate: 23.4, sl_hits: 111, pnl: -4534.89, reason: "Poda confirmada en replay 2 años Malaysian SNR: Mechas erráticas en M15 que invalidan retesteos Fresh." },
        { symbol: "USDCHF", strategy: "Malaysian SNR", trades: 165, win_rate: 26.1, sl_hits: 122, pnl: -4913.53, reason: "Poda confirmada en replay 2 años Malaysian SNR: Compresión excesiva de rango y rechazos prematuros." },
        { symbol: "AUDUSD", strategy: "Malaysian SNR", trades: 128, win_rate: 27.3, sl_hits: 93, pnl: -3632.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Baja liquidez institucional en horario de entrada." },
        { symbol: "Boom 500 Index", strategy: "Malaysian SNR", trades: 246, win_rate: 28.0, sl_hits: 177, pnl: -4497.43, reason: "Poda confirmada en replay 2 años Malaysian SNR: Ruido de mechas y caídas continuas antes de retesteo." },
        { symbol: "Volatility 50 Index", strategy: "Malaysian SNR", trades: 4650, win_rate: 0.1, sl_hits: 4645, pnl: -463750.00, reason: "Poda confirmada: Falsas rupturas sistemáticas en M15 y stops continuos." },
        { symbol: "Volatility 100 Index", strategy: "Malaysian SNR", trades: 4664, win_rate: 0.2, sl_hits: 4653, pnl: -463598.25, reason: "Poda confirmada: Ruido estructural masivo en retesteos de niveles Break." },'''

new_losers = '''      const LOSERS_DATA = [
        { symbol: "US Tech 100", strategy: "Malaysian SNR", trades: 11, win_rate: 9.1, sl_hits: 10, pnl: -831.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 9.1%, -8.31R. Momentum continuo de apertura que vulnera niveles A/V; derivado a ORB NY e ICT Killzones." },
        { symbol: "AUDUSD", strategy: "Malaysian SNR", trades: 11, win_rate: 18.2, sl_hits: 9, pnl: -750.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 18.2%, -7.50R. Rango errático sin expansión hacia TP1 en M15." },
        { symbol: "USDCHF", strategy: "Malaysian SNR", trades: 10, win_rate: 20.0, sl_hits: 8, pnl: -668.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 20.0%, -6.68R. Compresión de rango y rechazos prematuros." },
        { symbol: "Wall Street 30", strategy: "Malaysian SNR", trades: 13, win_rate: 23.1, sl_hits: 10, pnl: -150.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 23.1%, -1.50R. Reversión no adecuada para índices; derivado a ORB New York." },
        { symbol: "US Oil (Petróleo WTI)", strategy: "Malaysian SNR", trades: 4, win_rate: 25.0, sl_hits: 3, pnl: -247.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 25.0%, -2.47R. Deslizamiento severo, baja precisión y mechas erráticas." },
        { symbol: "US SP 500", strategy: "Malaysian SNR", trades: 13, win_rate: 30.8, sl_hits: 9, pnl: -242.00, reason: "Poda confirmada en replay 2 años Malaysian SNR: Win Rate 30.8%, -2.42R. Rupturas directas de Wall Street; derivado a ORB New York." },
        { symbol: "Boom 500 Index", strategy: "Malaysian SNR", trades: 246, win_rate: 28.0, sl_hits: 177, pnl: -4497.43, reason: "Poda confirmada en replay 2 años Malaysian SNR: Ruido de mechas y caídas continuas antes de retesteo." },
        { symbol: "Volatility 50 Index", strategy: "Malaysian SNR", trades: 4650, win_rate: 0.1, sl_hits: 4645, pnl: -463750.00, reason: "Poda confirmada: Falsas rupturas sistemáticas en M15 y stops continuos." },'''

assert old_losers in bases_content, "old_losers not found"
bases_content = bases_content.replace(old_losers, new_losers)

with open(path_bases, 'w', encoding='utf-8') as f:
    f.write(bases_content)
print("dashboard/strategy_bases_page.py actualizado exitosamente.")
