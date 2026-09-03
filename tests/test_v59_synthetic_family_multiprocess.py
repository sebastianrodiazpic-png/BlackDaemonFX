import inspect
from pathlib import Path
import app.main as main
EXPECTED={"BOOM":("boom-daemon",26082101,["boom"]),"CRASH":("crash-daemon",26082102,["crash"]),"VOLATILITY":("volatility-daemon",26082103,["volatility"]),"STEP":("step-daemon",26082104,["step"]),"JUMP":("jump-daemon",26082105,["jump"]),"FLIP":("flip-daemon",26082106,["flip"])}
def test_split_guard(): assert main._assert_synthetic_split_architecture() is True
def test_exact_six(): assert tuple(main.SYNTHETIC_SPLIT_PROFILES)==tuple(EXPECTED)
def test_unique_family_contracts():
    modes=[]; magics=[]
    for profile,(mode,magic,cats) in EXPECTED.items():
        spec=main.BOT_PROFILES[profile]; assert (spec["mode"],spec["magic"],spec["categories"])==(mode,magic,cats); modes.append(mode); magics.append(magic)
    assert len(set(modes))==len(set(magics))==6
def test_coordinator_spawns_per_profile():
    s=inspect.getsource(main.run_multi_bot_daemon); assert "for profile in profiles:" in s and "start_worker(profile)" in s; assert "subprocess.Popen(" in s and '"--mode", spec["mode"]' in s and '"--coordinated-worker"' in s
def test_legacy_aggregate_not_in_split(): assert "SYNTHETICS" not in main.SYNTHETIC_SPLIT_PROFILES
def test_launcher():
    t=(Path(__file__).resolve().parents[1]/"run_synthetics_split.bat").read_text(); assert "--mode synthetics-split-daemon" in t and "--dashboard --dashboard-port 8765" in t
