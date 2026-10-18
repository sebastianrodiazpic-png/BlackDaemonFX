# Programador de Tarea de Windows para Re-entrenamiento Semanal de IA
# Ejecuta cada domingo a las 02:00 AM (mercados forex cerrados, optimo para sinteticos y modelos)

$TaskName = "DaemonBlackFx_Weekly_AI_Retrain"
$ProjectPath = "C:\TradingBoot\smc_synthetic_bot"
$BatPath = "$ProjectPath\run_weekly_retrain.bat"

Write-Host "Verificando archivo: $BatPath" -ForegroundColor Cyan
if (-Not (Test-Path $BatPath)) {
    Write-Error "No se encontro el archivo $BatPath"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $ProjectPath
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Write-Host "Registrando tarea programada: $TaskName ..." -ForegroundColor Yellow
try {
    # Unregister previo si existe
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Re-entrenamiento automatico semanal de modelos de IA LightGBM para DaemonBlackFx" | Out-Null
    Write-Host "[OK] Tarea programada registrada exitosamente: $TaskName" -ForegroundColor Green
    Write-Host "Horario: Todos los Domingos a las 02:00 AM" -ForegroundColor Green
} catch {
    Write-Warning "No se pudo registrar la tarea con PowerShell directo (requiere permisos de Administrador o usar schtasks): $_"
    Write-Host "Intentando con schtasks.exe..." -ForegroundColor Cyan
    schtasks /Create /TN $TaskName /TR "\"$BatPath\"" /SC WEEKLY /D SUN /ST 02:00 /F
}
