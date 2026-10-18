"""Atomic, narrowly scoped wiring for large existing dashboard/engine modules."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
changes={
 'dashboard/realtime_dashboard.py': [
  ("            from strategy.malaysian_snr.ai_policy import active_model_status\n",
   "            from strategy.malaysian_snr.ai_policy import active_model_status\n            from strategy.malaysian_snr.universe import catalogue\n            from strategy.malaysian_snr.config import MalaysianSNRConfig\n"),
  ("'defaults': msnr_default_settings(), 'additional_symbols_catalog': list(ADDITIONAL_SYMBOLS),\n",
   "'defaults': msnr_default_settings(), 'additional_symbols_catalog': list(ADDITIONAL_SYMBOLS),\n                    'asset_catalog': catalogue(MalaysianSNRConfig().allowed_symbols),\n")],
 'strategy/execution/live_trading_engine.py': [
  ("and __import__('strategy.malaysian_snr.universe', fromlist=['resolve_symbol_settings']).resolve_symbol_settings(",
   "and resolve_symbol_settings("),
  ("        # Trasladar confirmación técnica a velas de M15 (descartar M5/M1)\n",
   "        from strategy.malaysian_snr.universe import resolve_symbol_settings\n        # Trasladar confirmación técnica a velas de M15 (descartar M5/M1)\n"),
  ("                from strategy.malaysian_snr.ai_policy import score_candidate\n",
   "                from strategy.malaysian_snr.ai_policy import score_candidate\n                from strategy.malaysian_snr.universe import resolve_symbol_settings\n"),
  ("source=self.config.source, settings=self.malaysian_snr_strategy.settings_snapshot())",
   "source=self.config.source, settings=analysis.get('runtime_controls') or resolve_symbol_settings(\n                        self.malaysian_snr_strategy.settings_snapshot(), symbol))")],
}
for name,replacements in changes.items():
 path=ROOT/name
 source=path.read_text(encoding='utf-8-sig')
 for old,new in replacements:
  if new in source: continue
  if source.count(old)!=1: raise ValueError(f'Unexpected source: {name} {source.count(old)}')
  source=source.replace(old,new)
 tmp=path.with_suffix(path.suffix+'.selective.tmp')
 tmp.write_text(source,encoding='utf-8')
 os.replace(tmp,path)
 print(name)
