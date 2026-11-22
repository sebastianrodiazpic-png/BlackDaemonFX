import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.operator.operator_db import get_open_positions

pos = get_open_positions()
print("Total open positions:", len(pos))
for p in pos:
    print(p)
