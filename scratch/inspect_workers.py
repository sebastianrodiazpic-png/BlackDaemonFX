import sys
sys.path.insert(0, ".")
from dashboard.realtime_dashboard import _WORKER_PROFILE_META

print("Profiles in _WORKER_PROFILE_META:")
for k, v in _WORKER_PROFILE_META.items():
    print(f"  {k:15}: magic={v.get('magic')}, selection_profile={v.get('selection_profile')}, label={v.get('label')}")
