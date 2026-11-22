import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.operator_chatbot import MASTER_PRICE_PROFILES, resolve_price_profile_and_bounds

print("Germany 40 profile before fix:", MASTER_PRICE_PROFILES.get("Germany 40"))
MASTER_PRICE_PROFILES["Germany 40"] = (25990.0, 35.0, 1, (21000.0, 32000.0))
print("Germany 40 profile after fix:", resolve_price_profile_and_bounds("Germany 40"))
