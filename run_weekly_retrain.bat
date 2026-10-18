@echo off
cd /d %~dp0
echo ============================================================
echo DAEMONBLACKFX - RE-ENTRENAMIENTO SEMANAL DE META-MODELOS IA
echo ============================================================
echo 1. Re-entrenamiento sistematico de Meta-Modelos generales...
.\.venv\Scripts\python.exe -m strategy.ai.auto_retrain --lookback-days 45 --min-samples 15

echo.
echo 2. Re-entrenamiento LightGBM GBDT para Malaysian SNR...
.\.venv\Scripts\python.exe tools\apply_msnr_winrate_optimization.py

echo.
echo 3. Re-entrenamiento LightGBM GBDT para ICT Sabri Malle...
.\.venv\Scripts\python.exe tools\train_ict_ai_model.py

echo.
echo ============================================================
echo Re-entrenamiento semanal completado con exito.
echo ============================================================
pause
