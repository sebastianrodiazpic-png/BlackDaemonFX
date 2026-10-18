@echo off
cd /d %~dp0
.venv\Scripts\python.exe -m app.main --mode multi-bot-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.0 --report-interval 30
pause
