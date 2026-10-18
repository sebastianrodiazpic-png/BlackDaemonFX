"""Apply bounded byte replacements while retaining the engine's line endings."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root/'strategy/execution/live_trading_engine.py'
raw = path.read_bytes()
newline = b'\r\n' if b'\r\n' in raw else b'\n'

def change(before, after):
    global raw
    old, new = before.encode().replace(b'\n',newline), after.encode().replace(b'\n',newline)
    if old not in raw and new in raw:
        return
    if raw.count(old)!=1:
        raise RuntimeError(f'Expected one engine occurrence: {before[:70]}')
    raw = raw.replace(old,new)

change("                         'fractal_max_entry_distance_atr', 'max_entry_distance_atr', 'execution_mode'):",
       "                         'fractal_max_entry_distance_atr', 'max_entry_distance_atr', 'execution_mode',\n"
       "                         'structure_timeframe', 'opportunity', 'macro_candle_bias', 'macro_structure_bias',\n"
       "                         'macro_structure_observation', 'macro_bias_method', 'gap_data_reason'):")
change("                'fractal_max_entry_distance_atr', 'max_entry_distance_atr', 'h1_snapshot')\n                if name in diagnostics}",
       "                'fractal_max_entry_distance_atr', 'max_entry_distance_atr', 'h1_snapshot',\n"
       "                'structure_timeframe', 'opportunity', 'variant_mode', 'macro_candle_bias', 'macro_structure_bias')\n"
       "                if name in diagnostics}\n"
       "            compact['shadow_candidates'] = [{\n"
       "                'setup_id':(item.get('signal') or {}).get('setup_id'),\n"
       "                'scenario':(item.get('signal') or {}).get('scenario'),\n"
       "                'direction':(item.get('signal') or {}).get('direction'),\n"
       "                'opportunity':(item.get('signal') or {}).get('opportunity'),\n"
       "                'entry_price':(item.get('signal') or {}).get('entry_price'),\n"
       "                'stop_loss':(item.get('signal') or {}).get('stop_loss'),\n"
       "                'tp1_price':(item.get('signal') or {}).get('tp1_price'),\n"
       "                'tp2_price':(item.get('signal') or {}).get('tp2_price'),\n"
       "                'execution_mode':'SHADOW',\n"
       "                'macro_bias_method':(item.get('signal') or {}).get('macro_bias_method'),\n"
       "                'confirmation_closed_at':(item.get('signal') or {}).get('confirmation_closed_at')\n"
       "            } for item in analysis.get('shadow_candidates',[]) if item.get('shadow_only')]")
path.write_bytes(raw)
