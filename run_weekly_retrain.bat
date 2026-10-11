@echo off
cd /d %~dp0
echo ============================================================
echo DAEMONBLACKFX - RE-ENTRENAMIENTO SEMANAL DE META-MODELOS IA
echo ============================================================
.\.venv\Scripts\python.exe -m strategy.ai.auto_retrain --lookback-days 45 --min-samples 15
pause
