@echo off
cd /d %~dp0
python -m app.main --mode report-daemon --report-interval 30
pause
