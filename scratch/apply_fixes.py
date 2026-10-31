with open("app/main.py", "r", encoding="utf-8") as f:
    content = f.read()

target1 = """    elif profile.startswith("FOREX"):
        try:
            forex_syms = list(manager.discovery.get_tradeable_forex())
        except Exception:
            forex_syms = list(manager.get_active_symbols(categories=["forex"]))
        allowed = set(PRUNED_ASSET_UNIVERSE.get("FOREX", ("USDCAD", "EURUSD", "USDCHF", "AUDUSD")))
        universe = sorted(forex_syms or allowed)
    else:"""

replacement1 = """    elif profile.startswith("FOREX"):
        try:
            forex_syms = list(manager.discovery.get_tradeable_forex())
        except Exception:
            forex_syms = list(manager.get_active_symbols(categories=["forex"]))
        allowed = set(PRUNED_ASSET_UNIVERSE.get("FOREX", ("USDCAD", "EURUSD", "USDCHF", "AUDUSD")))
        universe = sorted(forex_syms or allowed)
    elif profile == "TREND_PULLBACK":
        from strategy.trend_pullback.config import DEFAULT_PULLBACK_SYMBOLS
        candidates = list(DEFAULT_PULLBACK_SYMBOLS or spec.get("symbols", []))
        universe = []
        for sym in candidates:
            try:
                if provider.get_symbol_info(sym):
                    universe.append(sym)
            except Exception:
                pass
        universe = sorted(set(universe or candidates))
    else:"""

# Normalizar saltos para buscar y reemplazar
if target1 in content:
    content = content.replace(target1, replacement1, 1)
    print("target1 replaced with LF")
else:
    target1_crlf = target1.replace("\n", "\r\n")
    replacement1_crlf = replacement1.replace("\n", "\r\n")
    if target1_crlf in content:
        content = content.replace(target1_crlf, replacement1_crlf, 1)
        print("target1 replaced with CRLF")
    else:
        print("ERROR: target1 NOT found!")

target2 = """    orb_pref = reader("ORB", source="DEMO")
    if orb_pref is None or not orb_pref.get("selected_symbols"):
        orb_symbols = ["Wall Street 30", "XAUUSD", "XAUUSDmicro", "microXAUUSD", "US Tech 100", "BTCUSD"]
        writer(orb_symbols, selection_profile="ORB", source="DEMO")
        print("[RECUPERACIÓN] Perfil ORB activado con instrumentos principales NY.")

    return saved if 'saved' in locals() else None"""

replacement2 = """    orb_pref = reader("ORB", source="DEMO")
    if orb_pref is None or not orb_pref.get("selected_symbols"):
        orb_symbols = ["Wall Street 30", "XAUUSD", "XAUUSDmicro", "microXAUUSD", "US Tech 100", "BTCUSD"]
        writer(orb_symbols, selection_profile="ORB", source="DEMO")
        print("[RECUPERACIÓN] Perfil ORB activado con instrumentos principales NY.")

    # Saneamiento y recuperación de TREND_PULLBACK y MALAYSIAN_SNR
    tp_pref = reader("TREND_PULLBACK", source="DEMO") if callable(reader) else None
    if tp_pref is None or not tp_pref.get("selected_symbols"):
        from strategy.trend_pullback.config import DEFAULT_PULLBACK_SYMBOLS
        tp_symbols = list(DEFAULT_PULLBACK_SYMBOLS)
        if callable(writer):
            writer(tp_symbols, selection_profile="TREND_PULLBACK", source="DEMO")
            print(f"[RECUPERACIÓN] Perfil TREND_PULLBACK activado con {len(tp_symbols)} instrumentos.")

    msnr_pref = reader("MALAYSIAN_SNR", source="DEMO") if callable(reader) else None
    if msnr_pref and msnr_pref.get("selected_symbols") and callable(writer):
        unlisted = {"Vol over Boom 550", "Vol over Crash 550"}
        curr_syms = list(msnr_pref.get("selected_symbols"))
        cleaned_syms = [s for s in curr_syms if s not in unlisted]
        if len(cleaned_syms) != len(curr_syms):
            writer(cleaned_syms, selection_profile="MALAYSIAN_SNR", source="DEMO")
            print(f"[SANEAMIENTO] Perfil MALAYSIAN_SNR purgado de símbolos deslistados ({len(curr_syms)} -> {len(cleaned_syms)}).")

    return saved if 'saved' in locals() else None"""

if target2 in content:
    content = content.replace(target2, replacement2, 1)
    print("target2 replaced with LF")
else:
    target2_crlf = target2.replace("\n", "\r\n")
    replacement2_crlf = replacement2.replace("\n", "\r\n")
    if target2_crlf in content:
        content = content.replace(target2_crlf, replacement2_crlf, 1)
        print("target2 replaced with CRLF")
    else:
        print("ERROR: target2 NOT found!")

with open("app/main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("app/main.py written successfully.")
