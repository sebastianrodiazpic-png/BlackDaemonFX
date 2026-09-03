@echo off
cd /d %~dp0
echo ============================================================
echo DAEMONBLACKFX v69 - FOREX EVENT SCHEDULER
echo 4 workers ^| nueva vela M5 ^| cache H1/M15 ^| riesgo global
echo Dashboard central: http://127.0.0.1:8766
echo ============================================================
python -m app.main --mode forex-split-daemon --execute --interval 10 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8766
pause
