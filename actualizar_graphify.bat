@echo off
cd /d %~dp0
echo ============================================================
echo Actualizando grafo de graphify (solo codigo, sin LLM)...
echo ============================================================
set PYTHONUTF8=1
.venv\Scripts\graphify.exe update . > graphify-out\update_ultimo.log 2>&1
echo Codigo de salida: %ERRORLEVEL% >> graphify-out\update_ultimo.log
type graphify-out\update_ultimo.log
echo.
echo Listo. Puedes cerrar esta ventana.
pause
