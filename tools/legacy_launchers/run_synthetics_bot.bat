@echo off
cd /d %~dp0
python -m app.main --mode synthetic-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
pause
