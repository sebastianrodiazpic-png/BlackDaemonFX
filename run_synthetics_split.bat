@echo off
cd /d %~dp0
echo ============================================================
echo DAEMONBLACKFX v59 - SINTETICOS MULTI-PROCESO POR FAMILIA
echo BOOM ^| CRASH ^| VOLATILITY ^| STEP ^| JUMP ^| FLIP
echo Dashboard central: http://127.0.0.1:8765
echo ============================================================
python -m app.main --mode synthetics-split-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --report-interval 30 --dashboard --dashboard-port 8765
pause
