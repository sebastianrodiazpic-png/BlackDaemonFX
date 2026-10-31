from pathlib import Path
import os

target_file = Path("app") / "main.py"
tmp_file = Path("app") / "main.py.tmp"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "def _recover_empty_synthetic_selection(repo, catalog, profiles):"
end_marker = "def _assert_v53_runtime_compatibility(repo):"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    raise ValueError(f"Markers not found: start={start_idx}, end={end_idx}")

new_func = '''def _recover_empty_synthetic_selection(repo, catalog, profiles):
    """Restaura el catálogo sintético y perfiles dedicados si su preferencia persistida quedó vacía."""
    reader = getattr(repo, "latest_instrument_selection_profile", None)
    writer = getattr(repo, "save_instrument_selection_profile", None)
    if not callable(reader) or not callable(writer):
        return None

    active_profiles = {str(profile or "").upper() for profile in (profiles or [])}
    saved = None

    if active_profiles.intersection(SYNTHETIC_SPLIT_PROFILES) or "SYNTHETICS" in active_profiles:
        preference = reader("SYNTHETICS", source="DEMO")
        if preference is None or not preference.get("selected_symbols"):
            synthetic_symbols = sorted(
                {
                    str(symbol)
                    for category, symbols in (catalog or {}).items()
                    if str(category).lower() != "forex"
                    and not str(category).lower().startswith("orb_ny_")
                    for symbol in (symbols or [])
                    if symbol
                },
                key=str.casefold,
            )
            if synthetic_symbols:
                saved = writer(
                    synthetic_symbols, selection_profile="SYNTHETICS", source="DEMO"
                )
                try:
                    repo.save_audit_event(
                        "EMPTY_SYNTHETIC_SELECTION_RECOVERED",
                        source="DEMO",
                        action="RESTORED_ALL_SYNTHETIC_SYMBOLS",
                        reason="El coordinador no puede iniciar seis familias con SYNTHETICS vacío",
                        payload={
                            "symbols_restored": len(synthetic_symbols),
                            "previous_version": (preference or {}).get("version"),
                            "new_version": saved.get("version"),
                            "version": DAEMONBLACKFX_VERSION,
                        },
                    )
                except Exception:
                    pass
                print(
                    "[RECUPERACIÓN] SYNTHETICS estaba vacío: "
                    f"se habilitaron {len(synthetic_symbols)} instrumentos del catálogo."
                )

    # v110: Garantizar que los workers GOLD y ORB cuenten con selección activa en DEMO
    if "GOLD" in active_profiles or not active_profiles:
        gold_pref = reader("GOLD", source="DEMO")
        if gold_pref is None or not gold_pref.get("selected_symbols"):
            gold_symbols = ["XAUUSD", "XAUUSDmicro", "microXAUUSD"]
            writer(gold_symbols, selection_profile="GOLD", source="DEMO")
            print("[RECUPERACIÓN] Perfil GOLD activado con instrumentos XAUUSD.")

    if "ORB" in active_profiles or not active_profiles:
        orb_pref = reader("ORB", source="DEMO")
        if orb_pref is None or not orb_pref.get("selected_symbols"):
            orb_symbols = ["Wall Street 30", "XAUUSD", "XAUUSDmicro", "microXAUUSD", "US Tech 100", "BTCUSD"]
            writer(orb_symbols, selection_profile="ORB", source="DEMO")
            print("[RECUPERACIÓN] Perfil ORB activado con instrumentos principales NY.")

    # Saneamiento y recuperación de TREND_PULLBACK y MALAYSIAN_SNR
    if "TREND_PULLBACK" in active_profiles or not active_profiles:
        tp_pref = reader("TREND_PULLBACK", source="DEMO")
        if tp_pref is None or not tp_pref.get("selected_symbols"):
            from strategy.trend_pullback.config import DEFAULT_PULLBACK_SYMBOLS
            tp_symbols = list(DEFAULT_PULLBACK_SYMBOLS)
            writer(tp_symbols, selection_profile="TREND_PULLBACK", source="DEMO")
            print(f"[RECUPERACIÓN] Perfil TREND_PULLBACK activado con {len(tp_symbols)} instrumentos.")

    if "MALAYSIAN_SNR" in active_profiles or not active_profiles:
        msnr_pref = reader("MALAYSIAN_SNR", source="DEMO")
        if msnr_pref and msnr_pref.get("selected_symbols"):
            unlisted = {"Vol over Boom 550", "Vol over Crash 550"}
            curr_syms = list(msnr_pref.get("selected_symbols"))
            cleaned_syms = [s for s in curr_syms if s not in unlisted]
            if len(cleaned_syms) != len(curr_syms):
                writer(cleaned_syms, selection_profile="MALAYSIAN_SNR", source="DEMO")
                print(f"[SANEAMIENTO] Perfil MALAYSIAN_SNR purgado de símbolos deslistados ({len(curr_syms)} -> {len(cleaned_syms)}).")

    return saved


'''

content = content[:start_idx] + new_func + content[end_idx:]

with open(tmp_file, "w", encoding="utf-8") as f:
    f.write(content)

os.replace(tmp_file, target_file)
print("Updated _recover_empty_synthetic_selection successfully.")
