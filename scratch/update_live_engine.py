with open('strategy/execution/live_trading_engine.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Reemplazar importación y uso
old_import = """        from strategy.ict.ict_strategy import ICTSabriMalleStrategy
        from strategy.ict.config import ICTSabriMalleConfig
        _is_selective_pruned_worker = str(getattr(self.config, "bot_profile", "") or "").upper() in ("VOLATILITY_2", "FOREX_2")
        self.ict_strategy = ICTSabriMalleStrategy(
            data_provider=_symbol_routed_provider(provider, getattr(self.config, "ict_broker_candle_symbols", ())),
            config=ICTSabriMalleConfig("""

new_import = """        from strategy.ict.ict_strategy import ICTStrategy, ICTSabriMalleStrategy
        from strategy.ict.config import ICTConfig, ICTSabriMalleConfig
        _is_selective_pruned_worker = str(getattr(self.config, "bot_profile", "") or "").upper() in ("VOLATILITY_2", "FOREX_2")
        self.ict_strategy = ICTStrategy(
            data_provider=_symbol_routed_provider(provider, getattr(self.config, "ict_broker_candle_symbols", ())),
            config=ICTConfig("""

# Reemplazar occurrences de 'ICT_SABRI_MALLE' donde se devuelve strategy_name
text_updated = text.replace(old_import, new_import)
print('Old import replaced:', text != text_updated)

# Reemplazar strategy_name: ICT_SABRI_MALLE en returns
old_sn = '"strategy_name": "ICT_SABRI_MALLE"'
new_sn = '"strategy_name": "ICT"'
print('Occurrences of old_sn:', text_updated.count(old_sn))
text_updated = text_updated.replace(old_sn, new_sn)

# Reemplazar peer_strategy
old_peer = 'confluence_info["peer_strategy"] = "ICT_SABRI_MALLE"'
new_peer = 'confluence_info["peer_strategy"] = "ICT"'
text_updated = text_updated.replace(old_peer, new_peer)

# Reemplazar trigger
old_trig = 'symbol, trigger["direction"], trigger["stop"], "ICT_SABRI_MALLE",'
new_trig = 'symbol, trigger["direction"], trigger["stop"], "ICT",'
text_updated = text_updated.replace(old_trig, new_trig)

with open('strategy/execution/live_trading_engine.py', 'w', encoding='utf-8') as f:
    f.write(text_updated)

print('live_trading_engine.py updated successfully')
