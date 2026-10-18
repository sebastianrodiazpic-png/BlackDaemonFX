@echo off
chcp 65001 >nul
cd /d "C:\TradingBoot\smc_synthetic_bot"
echo =======================================================
echo Generando Reporte Matutino DaemonBlackFx (09:00 AM CL)
echo =======================================================
call .venv\Scripts\python.exe scripts\generate_morning_report.py
if %ERRORLEVEL% EQU 0 (
    echo [EXITO] Reporte generado correctamente.
) else (
    echo [ERROR] Error al generar el reporte.
)
