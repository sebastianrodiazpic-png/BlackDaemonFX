"""Reload the one supervised SNR worker only if it has no broker exposure."""
import json
from pathlib import Path
import MetaTrader5 as mt5

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'storage/analysis/msnr_v28_recovery_20261012'
if not mt5.initialize():
    raise SystemExit('Broker exposure check unavailable; no process changed')
try:
    positions,orders=mt5.positions_get(),mt5.orders_get()
    if positions is None or orders is None:
        raise SystemExit('Broker exposure check failed; no process changed')
    if any(p.magic==26082031 for p in positions) or any(o.magic==26082031 for o in orders):
        raise SystemExit('SNR has positions or pending orders; reload deferred')
    evidence={'safe_for_reload':True,'snr_positions':0,'snr_pending_orders':0}
    print(json.dumps(evidence))
finally:
    mt5.shutdown()
