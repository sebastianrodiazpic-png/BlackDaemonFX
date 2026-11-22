@echo off
cd /d %~dp0
echo ============================================================
echo LIMPIEZA DE PROCESOS HUERFANOS DE DAEMONBLACKFX
echo ============================================================
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe' -and $_.CommandLine -match 'app.main'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('[TERMINADO] Proceso Python PID: ' + $_.ProcessId) }"
echo.
echo Limpieza finalizada. Ya puedes iniciar el bot limpiamente.
pause
