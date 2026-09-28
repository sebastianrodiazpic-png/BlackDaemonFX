"""Shared strategy wiring for standalone and coordinated daemon workers."""
from dataclasses import replace

RULESET = 'smc-h1-adaptive-dual-m5-m1-position-guard-v4'


def configure_worker_rules(config):
    smc = str(config.bot_profile).upper() not in {'ORB', 'IDX_OPEN'}
    if not smc:
        return replace(config, dual_m5_m1_trigger_enabled=False, h1_location_only=False)
    return replace(config, h1_location_only=True, smc_entry_location_policy='H1_PRIMARY',
        dual_m5_m1_trigger_enabled=True, entry_timeframe='M5', strategy_version=RULESET)


def worker_poll_interval(profile, interval):
    # The M1 scheduler must get a chance to observe each minute's closed candle.
    return max(1, min(int(interval), 10)) if str(profile).upper() not in {'ORB','IDX_OPEN'} else max(1, int(interval))


def worker_rules_manifest(engine):
    config, pipeline = engine.config, engine.pipeline_config
    return dict(ruleset=RULESET, profile=config.bot_profile,
        strategy_version=config.strategy_version,
        h1_location_only=config.h1_location_only, h1_location_policy=config.smc_entry_location_policy,
        dual_m5_m1=config.dual_m5_m1_trigger_enabled,
        entry_timeframe=config.entry_timeframe, event_timeframe=engine._smc_event_timeframe(),
        h1_fractal_left=pipeline.h1_fractal_left, h1_fractal_right=pipeline.h1_fractal_right,
        h1_fallback_bars=pipeline.h1_fallback_bars,
        m5_max_signal_age_minutes=pipeline.m5_max_signal_age_minutes,
        position_guard='BROKER_POSITIONS_AND_PENDING_ORDERS',
        telemetry_worker=pipeline.telemetry_bot_name,
        execution_enabled=config.execution_enabled)


def stamp_confirmation_times(signal):
    """Stamp the actual selected candle timeframe without rewriting trigger age."""
    import pandas as pd
    minutes = {'M1':1, 'M5':5, 'M15':15, 'H1':60}
    frame = str(signal.get('confirmation_timeframe') or signal.get('timeframe') or 'M5').upper()
    if frame not in minutes:
        return
    stamp = pd.to_datetime(signal.get('entry_time'), utc=True, errors='coerce')
    if pd.notna(stamp):
        signal['confirmation_open_at'] = stamp.isoformat()
        signal['confirmation_closed_at'] = (stamp+pd.Timedelta(minutes=minutes[frame])).isoformat()
