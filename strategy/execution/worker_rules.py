"""Shared strategy wiring for standalone and coordinated daemon workers."""
import os
from dataclasses import replace

RULESET = 'ict-sabri-malle-v1'


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return float(default)
    try:
        return float(raw)
    except ValueError:
        return float(default)


def configure_worker_rules(config):
    profile = str(config.bot_profile).upper()
    tp1_rr = _env_float("DAEMONBLACKFX_FIRST_TARGET_RR", 1.0)
    tp2_rr = _env_float("DAEMONBLACKFX_SECOND_TARGET_RR", 2.0)
    be_rr = _env_float("DAEMONBLACKFX_BREAK_EVEN_TRIGGER_RR", 1.0)
    ext_t1 = _env_float("DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR", 2.0)
    ext_l1 = _env_float("DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR", 1.0)
    ext_t2 = _env_float("DAEMONBLACKFX_RUNNER_SECOND_TRIGGER_RR", 3.0)
    ext_l2 = _env_float("DAEMONBLACKFX_RUNNER_SECOND_LOCK_RR", 2.5)
    ext_max = _env_float("DAEMONBLACKFX_RUNNER_MAX_TARGET_RR", 4.0)
    smc_max = _env_float("DAEMONBLACKFX_SMC_RUNNER_MAX_TARGET_RR", 4.0)

    config = replace(
        config,
        meta_labeling_enabled=True,
        meta_labeling_mode=os.getenv("DAEMONBLACKFX_META_LABELING_MODE", "FILTER").strip().upper() or "FILTER",
        orb_enabled=(profile == "ORB"),
        symbol_daily_strikes_enabled=False,
        symbol_max_daily_losses=0,
    )
    if profile == "MALAYSIAN_SNR":
        return replace(
            config,
            malaysian_snr_enabled=True,
            dual_m5_m1_trigger_enabled=False,
            h1_location_only=False,
            entry_timeframe='M15',
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            malaysian_snr_tp1_rr=tp1_rr,
            malaysian_snr_runner_rr=tp2_rr,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            min_rr=1.0,
            forex_rollover_guard_enabled=True,
            forex_force_flat_friday=True,
            crypto_rollover_guard_enabled=True,
            crypto_force_flat_friday=True,
            market_regime_sentinel_enabled=True,
            market_regime_sentinel_mode="FILTER",
            meta_labeling_model_type="GBDT",
            symbol_loss_cooldown_enabled=True,
            symbol_loss_cooldown_minutes=60.0,
            symbol_daily_strikes_enabled=False,
            symbol_max_daily_losses=0,
        )
    if profile == "ORB":
        return replace(
            config,
            orb_enabled=True,
            dual_m5_m1_trigger_enabled=False,
            h1_location_only=False,
            entry_timeframe='M5',
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile == "GOLD":
        return replace(
            config,
            gold_quarters_strategy_enabled=True,
            gold_quarter_level_increment=25.0,
            gold_quarter_level_tolerance_price=2.0,
            gold_quarter_level_bonus_points=4.0,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            orb_enabled=False,
        )
    if profile == "TREND_PULLBACK":
        return replace(
            config,
            trend_pullback_enabled=True,
            dual_m5_m1_trigger_enabled=False,
            h1_location_only=False,
            entry_timeframe='M15',
            structure_timeframe='H1',
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            min_rr=1.0,
            symbol_loss_cooldown_enabled=True,
            symbol_loss_cooldown_minutes=60.0,
            symbol_daily_strikes_enabled=False,
            symbol_max_daily_losses=0,
        )
    smc = profile not in {'ORB', 'IDX_OPEN'}
    if not smc:
        return replace(config, dual_m5_m1_trigger_enabled=False, h1_location_only=False)
    if profile in ("VOLATILITY_1", "VOLATILITY_2", "VOLATILITY_3", "VOLATILITY_4"):
        vol_multistrat = os.getenv("DAEMONBLACKFX_VOLATILITY_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=vol_multistrat,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            volatility_first_target_rr=tp1_rr,
            volatility_second_target_rr=tp2_rr,
            smc_runner_max_target_rr=smc_max,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile.startswith("VOLATILITY"):
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            volatility_first_target_rr=tp1_rr,
            volatility_second_target_rr=tp2_rr,
            smc_runner_max_target_rr=smc_max,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile == "BOOM":
        boom_multistrat = os.getenv("DAEMONBLACKFX_BOOM_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=boom_multistrat,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            smc_runner_max_target_rr=smc_max,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile == "CRASH":
        crash_multistrat = os.getenv("DAEMONBLACKFX_CRASH_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=crash_multistrat,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            smc_runner_max_target_rr=smc_max,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile in ("STEP", "STEP_2"):
        step_multistrat = os.getenv("DAEMONBLACKFX_STEP_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=step_multistrat,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            smc_runner_max_target_rr=smc_max,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile == "JUMP":
        jump_multistrat = os.getenv("DAEMONBLACKFX_JUMP_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=jump_multistrat,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            smc_runner_max_target_rr=smc_max,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile in ("FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "FOREX_5"):
        # Validación 5A/1A MSNR Mercados Reales (-255.56 R en 4,652 ops, negativo en ambas mitades):
        # MSNR desactivado por defecto en Forex; reactivable con DAEMONBLACKFX_FOREX_X_MULTISTRATEGY=1.
        forex_multistrat = os.getenv(f"DAEMONBLACKFX_{profile}_MULTISTRATEGY", "0").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=forex_multistrat,
            forex_rollover_guard_enabled=True,
            forex_force_flat_friday=True,
            crypto_rollover_guard_enabled=True,
            crypto_force_flat_friday=True,
            forex_killzone_only_enabled=False,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile.startswith("FOREX"):
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            forex_rollover_guard_enabled=True,
            forex_force_flat_friday=True,
            crypto_rollover_guard_enabled=True,
            crypto_force_flat_friday=True,
            forex_killzone_only_enabled=True,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
        )
    if profile == "ICT":
        # Validación MSNR Mercados Reales (-255.56 R, negativo en ambas mitades):
        # MSNR desactivado por defecto en worker ICT (metales/cripto/petróleo); reactivable con DAEMONBLACKFX_ICT_MULTISTRATEGY=1.
        ict_multistrat = os.getenv("DAEMONBLACKFX_ICT_MULTISTRATEGY", "0").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version='ict-sabri-malle-v1',
            malaysian_snr_enabled=ict_multistrat,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
            crypto_rollover_guard_enabled=True,
            crypto_force_flat_friday=False,
            orb_enabled=False,
        )
    if profile in ("INDICESB_SNR", "INDICES"):
        indices_multistrat = os.getenv("DAEMONBLACKFX_INDICESB_SNR_MULTISTRATEGY", "1").strip().lower() not in ("0", "false", "off")
        return replace(
            config,
            h1_location_only=True,
            smc_entry_location_policy='H1_PRIMARY',
            dual_m5_m1_trigger_enabled=True,
            entry_timeframe='M5',
            strategy_version=RULESET,
            malaysian_snr_enabled=indices_multistrat,
            forex_rollover_guard_enabled=True,
            first_target_rr=tp1_rr,
            second_target_rr=tp2_rr,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=ext_t1,
            runner_extension_first_lock_rr=ext_l1,
            runner_extension_second_trigger_rr=ext_t2,
            runner_extension_second_lock_rr=ext_l2,
            runner_extension_max_target_rr=ext_max,
            break_even_enabled=True,
            break_even_trigger_rr=be_rr,
            min_rr=1.0,
            orb_enabled=False,
        )
    return replace(
        config,
        h1_location_only=True,
        smc_entry_location_policy='H1_PRIMARY',
        dual_m5_m1_trigger_enabled=True,
        entry_timeframe='M5',
        strategy_version=RULESET,
        first_target_rr=tp1_rr,
        second_target_rr=tp2_rr,
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=ext_t1,
        runner_extension_first_lock_rr=ext_l1,
        runner_extension_second_trigger_rr=ext_t2,
        runner_extension_second_lock_rr=ext_l2,
        runner_extension_max_target_rr=ext_max,
        break_even_enabled=True,
        break_even_trigger_rr=be_rr,
        min_rr=1.0,
    )


def worker_poll_interval(profile, interval):
    # The M1 scheduler must get a chance to observe each minute's closed candle.
    cap = int(os.getenv("DAEMONBLACKFX_WORKER_POLL_INTERVAL_CAP", "10"))
    min_cap = max(1, cap)
    return max(1, min(int(interval), min_cap)) if str(profile).upper() not in {'ORB','IDX_OPEN','MALAYSIAN_SNR','TREND_PULLBACK'} else max(1, int(interval))


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
