import sqlite3, json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
pref = conn.execute("SELECT id, selection_profile, selected_symbols_json FROM instrument_selection_profile_preferences WHERE selection_profile='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone()
if pref:
    syms = json.loads(pref[2])
    print(f"DB instrument_selection_profile_preferences (id={pref[0]}): count={len(syms)}")
    print(syms)
else:
    print("No instrument_selection_profile_preferences found for MALAYSIAN_SNR")

strat = conn.execute("SELECT id, settings_json FROM strategy_runtime_preferences WHERE strategy_name='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone()
if strat:
    st = json.loads(strat[1])
    am = st.get('asset_modes', {})
    print(f"\nDB strategy_runtime_preferences (id={strat[0]}):")
    print("additional_symbols_mode:", st.get('additional_symbols_mode'))
    print("additional_symbols:", st.get('additional_symbols'))
    print("asset_modes count:", len(am))
    print("asset_modes off:", [k for k,v in am.items() if v == 'off'])
    print("asset_modes live:", [k for k,v in am.items() if v == 'live'])
else:
    print("No strategy_runtime_preferences found for MALAYSIAN_SNR")
