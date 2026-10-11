# Registra una tarea programada en Windows Task Scheduler para el re-entrenamiento semanal de IA
$Action = New-ScheduledTaskAction -Execute "C:\TradingBoot\smc_synthetic_bot\run_weekly_retrain.bat" -WorkingDirectory "C:\TradingBoot\smc_synthetic_bot"
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 00:00AM
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$TaskName = "DaemonBlackFx_Weekly_AI_Retrain"

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Re-entrenamiento semanal de Meta-Modelos SMC con datos recientes de mercado." -Force
    Write-Host "[OK] Tarea programada registrada exitosamente: $TaskName (Todos los domingos a las 00:00)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] No se pudo registrar la tarea. Ejecute PowerShell como Administrador." -ForegroundColor Red
}
