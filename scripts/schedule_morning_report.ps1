# Programador de Tarea de Windows para Reporte Matutino Diario
# Ejecuta diariamente a las 09:00 AM (Hora local de Chile)

$TaskName = "DaemonBlackFx_Morning_Report_0900"
$ProjectPath = "C:\TradingBoot\smc_synthetic_bot"
$BatPath = "$ProjectPath\run_morning_report.bat"

Write-Host "Verificando archivo bat: $BatPath" -ForegroundColor Cyan
if (-Not (Test-Path $BatPath)) {
    Write-Error "No se encontro el archivo $BatPath"
    exit 1
}

$Action = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $ProjectPath
$Trigger = New-ScheduledTaskTrigger -Daily -At 9am
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Write-Host "Registrando tarea programada: $TaskName ..." -ForegroundColor Yellow
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Reporte diario matutino de auditoria integral DaemonBlackFx a las 09:00 AM CL" | Out-Null
    Write-Host "[OK] Tarea programada registrada exitosamente: $TaskName" -ForegroundColor Green
    Write-Host "Horario: Todos los dias a las 09:00 AM (Hora de Chile)" -ForegroundColor Green
} catch {
    Write-Warning "Intentando con schtasks.exe..."
    schtasks /Create /TN $TaskName /TR "\"$BatPath\"" /SC DAILY /ST 09:00 /F
}
