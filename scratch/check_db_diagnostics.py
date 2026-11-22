import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.database import database_diagnostics, DEFAULT_DB_PATH, _stable_data_dir

print("DEFAULT_DB_PATH:", DEFAULT_DB_PATH)
print("Stable data dir:", _stable_data_dir())

diag = database_diagnostics()
print("\nDatabase diagnostics:")
for k, v in diag.items():
    print(f"  {k}: {v}")
