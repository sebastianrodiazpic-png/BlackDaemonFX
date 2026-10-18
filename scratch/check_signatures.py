import sqlite3, json, hashlib

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
for r in conn.execute('SELECT id, settings_json FROM strategy_runtime_preferences WHERE strategy_name="MALAYSIAN_SNR" ORDER BY id DESC LIMIT 5').fetchall():
    st = json.loads(r[1])
    excluded = {'version', 'updated_at', 'enable_candidate_audit', 'observe_candidate_outcomes',
        'candidate_outcome_hours', 'enable_setup_diagnostics', 'enable_structure_cache',
        'prioritize_pending_retests', 'analysis_outside_entry_lock', 'asset_modes',
        'm5_symbol_modes', 'continuation_symbol_modes', 'step_symbol_min_adx',
        'research_min_frequency_ratio', 'research_min_resolved_trades',
        'research_min_win_rate_improvement_pp',
        'additional_symbols', 'additional_symbols_mode'}
    vals = {k:v for k,v in st.items() if k not in excluded and not k.startswith('ai_')}
    h = hashlib.sha256(json.dumps(vals, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    print(f'id={r[0]}: hash={h}')

    # Also test old excluded without additional_symbols
    excluded_old = {'version', 'updated_at', 'enable_candidate_audit', 'observe_candidate_outcomes',
        'candidate_outcome_hours', 'enable_setup_diagnostics', 'enable_structure_cache',
        'prioritize_pending_retests', 'analysis_outside_entry_lock', 'asset_modes',
        'm5_symbol_modes', 'continuation_symbol_modes', 'step_symbol_min_adx',
        'research_min_frequency_ratio', 'research_min_resolved_trades',
        'research_min_win_rate_improvement_pp'}
    vals_old = {k:v for k,v in st.items() if k not in excluded_old and not k.startswith('ai_')}
    h_old = hashlib.sha256(json.dumps(vals_old, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    print(f'   old_hash={h_old}')
