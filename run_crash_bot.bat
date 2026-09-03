@echo off
cd /d %~dp0
python -m app.main --mode crash-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8772
pause
