import sys
sys.path.insert(0, '.')
from pathlib import Path
from app.main import _MultiBotInstanceGuard

guard = _MultiBotInstanceGuard(Path('.'))
print("Mutex name:", guard.mutex_name)
print("Owner in json:", guard._owner())
try:
    guard.acquire()
    print("ACQUIRED MUTEX SUCCESSFULLY! (No other coordinator is holding the mutex)")
    guard.release()
except SystemExit as e:
    print("COULD NOT ACQUIRE MUTEX - BLOCKED BY EXISTING PROCESS:\n", e)
except Exception as e:
    print("Error acquiring mutex:", e)
