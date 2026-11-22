@echo off
cd /d %~dp0
echo ============================================================
echo DAEMONBLACKFX - MULTIBOT UNIFICADO (PROCESO UNICO LIGERO)
echo Consume < 500 MB RAM y 1 conexion MT5 (70%% menos CPU)
echo ============================================================
set DAEMONBLACKFX_MARKET_REGIME_ICT_REAL_MODE=OBSERVE
set DAEMONBLACKFX_OVERRUN_MIN_SLEEP_SECONDS=2.0
set DAEMONBLACKFX_IDLE_MONITOR_POLL_SECONDS=10.0
set DAEMONBLACKFX_CONCURRENT_SCAN_WORKERS=1
set DAEMONBLACKFX_ADAPTIVE_CONCURRENCY=0
set DAEMONBLACKFX_WORKER_POLL_INTERVAL_CAP=30
set DAEMONBLACKFX_DEDUPLICATE_MICRO_SYMBOLS=1
set DAEMONBLACKFX_PROCESS_PRIORITY=BELOW_NORMAL
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
set VECLIB_MAXIMUM_THREADS=1
set NUMEXPR_NUM_THREADS=1
set DAEMONBLACKFX_DASHBOARD_SNAPSHOT_TTL=12.0
.venv\Scripts\python.exe -m app.main --mode unified-multibot-daemon --execute --interval 30 --position-monitor-interval 5 --risk-percent 1.0 --min-rr 1.0 --report-interval 300 --dashboard --dashboard-port 8765
pause
