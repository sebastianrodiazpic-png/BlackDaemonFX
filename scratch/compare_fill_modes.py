import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import sqlite3
import pandas as pd
from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

# Run with both fill modes and compare
runner_sig = ProspectiveM1ReplayRunner(dry_run=True, fill_mode="signal_entry")
runner_sig.execute_replay()

runner_lat = ProspectiveM1ReplayRunner(dry_run=True, fill_mode="created_at")
runner_lat.execute_replay()

print("="*80)
print("COMPARACIÓN DETALLADA DE FILL: signal_entry VS created_at")
print("="*80)
