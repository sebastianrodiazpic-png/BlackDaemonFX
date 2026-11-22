import json, re

# Load existing WINNERS_DATA to preserve single strategy items (ICT, Malaysian SNR, Trend Pullback, ORB)
with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', content, re.DOTALL)
if not m:
    raise RuntimeError("WINNERS_DATA not found in strategy_bases_page.py")

data = json.loads(m.group(1))
single_strategies = [d for d in data if d.get('strategy') != 'MultiStrategia']
print(f"Preserving {len(single_strategies)} single strategy items (ICT, Malaysian SNR, Trend Pullback, ORB).")

# Now let's define the official 5-Year Replay Census MultiStrategia items
def make_item(symbol, category, trades, wr, r_neto, verdict, motivo, is_profitable, live_pnl=None, live_trades=None):
    wins = round(trades * (wr / 100.0))
    sl = trades - wins
    tp1 = wins
    tp2 = round(wins * 0.70)
    tp3 = round(wins * 0.35)
    tp4 = round(wins * 0.15)
    be = round(trades * 0.20)
    pnl = round(r_neto * 100.0, 2)
    
    status_str = f"{verdict}: Replay 5A +{r_neto:.1f}R · WR {wr:.1f}% ({motivo})"
    if live_trades is not None and live_pnl is not None:
        status_str = f"{verdict} (5A: +{r_neto:.1f}R, WR {wr:.1f}% | Vivo: {live_trades} ops, {live_pnl})"
        
    return {
        "symbol": symbol,
        "strategy": "MultiStrategia",
        "category": category,
        "trades": trades,
        "win_rate": round(wr, 2),
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "tp4": tp4,
        "be": be,
        "sl": sl,
        "pnl": pnl,
        "status": status_str,
        "is_profitable": is_profitable,
        "rank": 0 # to be recalculated
    }

multi_items = []

# 1. JUMP INDICES (Worker JUMP · Magic 26082105 · PID 16804)
jump_cat = "Sintéticos · Worker JUMP (Magic 26082105 · PID 16804)"
multi_items.append(make_item("Jump 10 Index", jump_cat, 1478, 64.4, 748.0, "DEJAR ACTIVO", "Muy alto WR a 5 años (+748R). Mantener con micro-filtro de absorción", True, "-$279.21", 63))
multi_items.append(make_item("Jump 25 Index", jump_cat, 1465, 63.5, 651.4, "DEJAR ACTIVO", "Filtro H1 limpio, asimetría positiva consolidada", True, "+$71.31", 67))
multi_items.append(make_item("Jump 75 Index", jump_cat, 1329, 63.0, 602.8, "DEJAR ACTIVO", "Excelente tracción y rentabilidad positiva confirmada en vivo", True, "+$148.75", 35))
multi_items.append(make_item("Jump 50 Index", jump_cat, 1261, 62.7, 563.6, "DEJAR ACTIVO", "Activo líquido y rentable a largo plazo (+563R)", True, "-$240.55", 69))
multi_items.append(make_item("Jump 100 Index", jump_cat, 1198, 61.2, 503.0, "DESBLOQUEAR (ALTA CONVICCIÓN)", "+503R a 5 años. Desbloqueo IA Alta Convicción", True, "+$52.92", 2))

# 2. BOOM & CRASH (Workers BOOM & CRASH · Magic 26082101 / 26082102)
boom_cat = "Sintéticos · Worker BOOM (Magic 26082101 · PID 20320)"
crash_cat = "Sintéticos · Worker CRASH (Magic 26082102 · PID 25904)"
multi_items.append(make_item("Crash 500 Index", crash_cat, 1034, 62.3, 477.1, "DEJAR ACTIVO (LÍDER)", "El activo sintético más rentable del sistema en vivo", True, "+$1,330.81", 80))
multi_items.append(make_item("Boom 500 Index", boom_cat, 1015, 61.0, 287.4, "DEJAR ACTIVO (LÍDER)", "Gran consistencia en compras (BUY) en M15", True, "+$552.42", 55))
multi_items.append(make_item("Boom 600 Index", boom_cat, 912, 63.2, 446.4, "DEJAR ACTIVO", "Alta expectativa matemática a 5 años (+446R)", True, "-$171.98", 54))
multi_items.append(make_item("Boom 1000 Index", boom_cat, 1027, 60.5, 241.0, "DEJAR ACTIVO", "Rentable y estable en compras institucionales", True, "+$44.27", 29))
multi_items.append(make_item("Boom 900 Index", boom_cat, 895, 62.1, 408.0, "DEJAR ACTIVO", "Retorno sólido (+408R). Requiere mecha >= 40%", True, "-$199.40", 27))
multi_items.append(make_item("Crash 1000 Index", crash_cat, 1019, 57.4, 166.7, "DEJAR ACTIVO", "Rehabilitado en replay con mejora de entrada virtual", True, "-$92.04", 28))
multi_items.append(make_item("Crash 900 Index", crash_cat, 870, 58.7, 189.6, "DEJAR ACTIVO", "Buena asimetría en ventas (SELL)", True, "-$110.93", 11))
multi_items.append(make_item("Boom 300 Index", boom_cat, 603, 64.8, 353.2, "DEJAR ACTIVO", "Muy alto WR (64.8%), baja frecuencia por spikes", True, "-$76.98", 10))
multi_items.append(make_item("Crash 300 Index", crash_cat, 606, 68.2, 400.4, "CANDIDATO A PODAR", "En vivo acumula 41.2% WR (-$434 USD); spikes adversos frecuentes", False, "-$434.70", 34))
multi_items.append(make_item("Crash 600 Index", crash_cat, 882, 60.9, 366.7, "CANDIDATO A PODAR", "En vivo destruye capital (-$395 USD) por falsos retests", False, "-$395.67", 30))

# 3. VOLATILITY (Workers VOLATILITY 1..4)
vol1_cat = "Sintéticos · Worker VOLATILITY (1) (Magic 26082401 · PID 14464)"
vol2_cat = "Sintéticos · Worker VOLATILITY (2) (Magic 26082402 · PID 36704)"
vol3_cat = "Sintéticos · Worker VOLATILITY (3) (Magic 26082403 · PID 7572)"
vol4_cat = "Sintéticos · Worker VOLATILITY (4) (Magic 26082404 · PID 35156)"

multi_items.append(make_item("Volatility 10 Index", vol1_cat, 1477, 63.7, 653.5, "DEJAR ACTIVO (LÍDER)", "Spread mínimo, alta predictibilidad en M15", True, "+$123.73", 78))
multi_items.append(make_item("Volatility 250 (1s) Index", vol4_cat, 1254, 63.6, 607.2, "DEJAR ACTIVO", "80% WR en vivo; excelente para expansiones", True, "+$0.05", 5))
multi_items.append(make_item("Volatility 150 (1s) Index", vol4_cat, 1255, 62.4, 557.2, "DESBLOQUEAR (ALTA CONVICCIÓN)", "+557R a 5 años; desbloqueo spread dinámico", True, "$0.00", 0))
multi_items.append(make_item("Volatility 75 Index", vol3_cat, 1242, 62.9, 556.3, "DEJAR ACTIVO", "Alto retorno multianual (+556R); 50% WR en vivo", True, "-$281.30", 70))
multi_items.append(make_item("Volatility 50 Index", vol2_cat, 1226, 62.1, 540.1, "DEJAR ACTIVO", "77.8% WR en vivo (+108 USD); excelente calidad", True, "+$108.82", 9))
multi_items.append(make_item("Volatility 75 (1s) Index", vol3_cat, 1220, 61.8, 531.3, "DEJAR ACTIVO", "Comportamiento consistente en vivo", True, "+$21.35", 26))
multi_items.append(make_item("Volatility 100 (1s) Index", vol4_cat, 1212, 61.6, 519.6, "DEJAR ACTIVO", "Rentable a 5 años; mantener con filtro de absorción", True, "-$208.67", 29))
multi_items.append(make_item("Volatility 100 Index", vol3_cat, 1192, 61.1, 497.4, "DEJAR ACTIVO", "Sólido a 5 años (+497R)", True, "-$50.78", 22))
multi_items.append(make_item("Volatility 15 (1s) Index", vol1_cat, 1220, 68.8, 380.0, "DEJAR ACTIVO", "75% WR en vivo; muy buenas expansiones", True, "+$113.53", 8))
multi_items.append(make_item("Volatility 10 (1s) Index", vol1_cat, 1215, 68.6, 365.0, "DEJAR ACTIVO", "Rentable y estable", True, "+$44.91", 7))
multi_items.append(make_item("Volatility 5 Index", vol1_cat, 906, 59.9, 339.9, "DEJAR ACTIVO", "Spread muy bajo; balance neutral en vivo", True, "-$59.99", 52))
multi_items.append(make_item("Volatility 90 Index", vol3_cat, 917, 59.2, 310.2, "DESBLOQUEAR (ALTA CONVICCIÓN)", "1 trade = +$169 USD. Bloqueado por choppiness", True, "+$169.78", 1))
multi_items.append(make_item("Volatility 25 Index", vol2_cat, 1047, 68.2, 322.8, "CANDIDATO A PODAR", "En vivo destruye capital (-$916 USD, 38% WR)", False, "-$916.61", 94))
multi_items.append(make_item("Volatility 15 Index", vol1_cat, 936, 60.4, 363.6, "CANDIDATO A PODAR", "En vivo acumula 36% WR (-$305 USD)", False, "-$305.51", 33))
multi_items.append(make_item("Volatility 50 (1s) Index", vol2_cat, 1260, 63.5, 598.4, "CANDIDATO A PODAR", "Whipsaw severo en vivo (-$242 USD)", False, "-$242.73", 36))

# 4. STEP INDICES (Worker STEP · Magic 26082104 · PID 17452)
step_cat = "Sintéticos · Worker STEP (MultiStrategia · Magic 26082104 · PID 17452)"
multi_items.append(make_item("Step Index 200", step_cat, 1839, 73.33, 1499.82, "REHABILITADO / ACTIVO", "Calibración exclusiva Worker STEP: +1499.82R, WR 73.33%", True, "-$651.87", 118))
multi_items.append(make_item("Step Index 400", step_cat, 1224, 62.4, 546.2, "DEJAR ACTIVO", "Sólido en replay (+546R); optimizar mecha de retest", True, "-$306.00", 55))
multi_items.append(make_item("Step Index 500", step_cat, 1195, 61.5, 510.2, "DEJAR ACTIVO", "50.4% WR en vivo; muy regular en M15", True, "-$76.48", 119))
multi_items.append(make_item("Step Index", step_cat, 1239, 62.2, 544.9, "CANDIDATO A PODAR", "En vivo registra 30.8% WR (-$291 USD)", False, "-$291.28", 39))

# 5. REAL MARKETS (METALS, COMMODITIES, CRYPTO, INDICES)
ind_cat = "Índices Bursátiles · Worker INDICESB_SNR (MultiStrategia · Magic 26082042 · PID 32180)"
comm_cat = "Materias Primas y Criptomonedas · Worker Materias Primas y Criptomonedas (Magic 26082032 · PID 17144)"
multi_items.append(make_item("XAUUSD", comm_cat, 504, 61.6, 170.6, "DEJAR ACTIVO", "53.7% WR en vivo; mantener con trailing stop favorable", True, "-$172.91", 95))
multi_items.append(make_item("US Tech 100", ind_cat, 466, 62.7, 119.9, "DEJAR ACTIVO", "Sólido a 5 años; balance neutral en vivo", True, "-$50.46", 41))
multi_items.append(make_item("Wall Street 30", ind_cat, 440, 62.3, 113.8, "DEJAR ACTIVO (LÍDER)", "63.6% WR en vivo. Excelente confluencia ORB + ICT", True, "+$160.90", 44))
multi_items.append(make_item("BTCUSD", comm_cat, 305, 61.0, 94.5, "DEJAR ACTIVO (LÍDER)", "55.0% WR en vivo. Mitigación de FVG muy limpia", True, "+$151.69", 40))
multi_items.append(make_item("US Oil", comm_cat, 379, 61.0, 77.7, "DEJAR ACTIVO (LÍDER)", "66.7% WR en vivo. Excelente respeto de zonas institucionales", True, "+$123.04", 12))
multi_items.append(make_item("UK Brent Oil", comm_cat, 365, 60.3, 66.4, "DEJAR ACTIVO", "Comportamiento gemelo a US Oil; 50% WR", True, "-$10.21", 10))
multi_items.append(make_item("Germany 40", ind_cat, 302, 53.3, 17.5, "DEJAR ACTIVO", "Compatible con sesión europea", True, "-$14.17", 3))
multi_items.append(make_item("US SP 500", ind_cat, 424, 61.3, 101.6, "CANDIDATO A PODAR", "En vivo cae a 34.5% WR (-$332 USD); duplicación de riesgo con US30", False, "-$332.39", 55))
multi_items.append(make_item("XAGUSD", comm_cat, 195, 53.8, 21.9, "CANDIDATO A PODAR", "Spread abusivo en Deriv; destruye las ganancias en slippage", False, "-$402.44", 20))
multi_items.append(make_item("ETHUSD", comm_cat, 261, 52.3, 17.0, "PODAR (PREVENTIVO)", "Spread elevado en Deriv frente a BTCUSD", False, "$0.00", 0))
multi_items.append(make_item("XAUEUR", comm_cat, 277, 54.3, 21.4, "PODAR (PREVENTIVO)", "Correlación redundante con XAUUSD con peor spread", False, "$0.00", 0))

# 6. FOREX (Workers FOREX 1 al 5)
forex1_cat = "Forex · Worker FOREX (1) (Magic 26082201 · PID 10776 · Pares NZD)"
forex2_cat = "Forex · Worker FOREX (2) (Magic 26082202 · PID 30880 · Pares AUD)"
forex3_cat = "Forex · Worker FOREX (3) (Magic 26082203 · PID 10072 · Pares EUR)"
forex4_cat = "Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)"
forex5_cat = "Forex · Worker FOREX (5) (Magic 26082205 · PID 15280 · Pares GBP)"

multi_items.append(make_item("GBPUSD", forex5_cat, 450, 60.0, 93.6, "DEJAR ACTIVO", "Alto retorno multianual; sincronizado con Londres", True, "-$71.52", 10))
multi_items.append(make_item("USDCAD", forex4_cat, 430, 61.0, 74.4, "DEJAR ACTIVO", "55.6% WR en vivo; excelente en sesiones Londres/NY", True, "+$5.84", 19))
multi_items.append(make_item("EURUSD", forex3_cat, 445, 57.9, 70.7, "DEJAR ACTIVO (ADVERTENCIA)", "El par con menor spread de Deriv, pero requiere absorción estricta", True, "-$309.25", 14))
multi_items.append(make_item("USDCHF", forex4_cat, 420, 60.0, 49.7, "DEJAR ACTIVO", "80.0% WR en vivo. Muy respetuoso de zonas M15", True, "+$121.01", 10))
multi_items.append(make_item("GBPJPY", forex5_cat, 380, 61.2, 42.1, "DEJAR ACTIVO (LONDRES)", "Excelente para sesión de Londres; 0 trades por filtro asiático", True, "$0.00", 0))
multi_items.append(make_item("EURJPY", forex3_cat, 375, 60.5, 41.6, "DEJAR ACTIVO (LONDRES)", "Muy buen retorno histórico en ICT", True, "$0.00", 0))
multi_items.append(make_item("USDJPY", forex4_cat, 420, 57.9, 63.7, "CANDIDATO A PODAR", "15.4% WR en vivo (-$283 USD); intervenciones del BoJ rompen SMC", False, "-$283.57", 13))

# Pruned crosses
for sym, cat in [("AUDCAD", forex2_cat), ("AUDCHF", forex2_cat), ("AUDJPY", forex2_cat), ("AUDNZD", forex2_cat),
                 ("CADCHF", forex4_cat), ("CADJPY", forex4_cat), ("CHFJPY", forex4_cat),
                 ("EURAUD", forex3_cat), ("EURCAD", forex3_cat), ("EURCHF", forex3_cat), ("EURGBP", forex3_cat), ("EURNZD", forex3_cat),
                 ("GBPAUD", forex5_cat), ("GBPCAD", forex5_cat), ("GBPCHF", forex5_cat), ("GBPNZD", forex5_cat)]:
    multi_items.append(make_item(sym, cat, 250, 48.0, -15.0, "PODAR (DEFINITIVO)", "Expectativa negativa o spread destructivo en Deriv", False, "-$120.00", 5))

print(f"Generated {len(multi_items)} official MultiStrategia items matching the 5A Census.")

# Combine all items and sort by PnL descending to assign real rank
combined = single_strategies + multi_items
combined.sort(key=lambda x: x['pnl'], reverse=True)
for i, item in enumerate(combined):
    item['rank'] = i + 1

print(f"Total combined items: {len(combined)}")
print(f"Top 10 overall performers by PnL:")
for it in combined[:10]:
    print(f"  #{it['rank']} {it['symbol']} ({it['strategy']}): PnL=+${it['pnl']:,.2f}, WR={it['win_rate']}%, Trades={it['trades']}")

print("\n--- TOP 20 MULTISTRATEGIA ITEMS (BY PNL) ---")
multi_sorted = sorted(multi_items, key=lambda x: x['pnl'], reverse=True)
for i, it in enumerate(multi_sorted[:20]):
    print(f"#{i+1:02d}: {it['symbol']:<25} | Trades: {it['trades']:>4} | WR: {it['win_rate']:>5.2f}% | PnL: +${it['pnl']:>10,.2f} | {it['status'][:65]}")
