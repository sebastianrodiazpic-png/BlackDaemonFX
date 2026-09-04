# Measure endpoint response times
Write-Host "Measuring API endpoint response times..."
Write-Host "============================================"

$endpoints = @(
    "http://127.0.0.1:8765/",
    "http://127.0.0.1:8765/api/state",
    "http://127.0.0.1:8765/api/account",
    "http://127.0.0.1:8765/api/instruments"
)

foreach ($endpoint in $endpoints) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $response = curl -s -w "`n%{http_code}" -m 10 "$endpoint" 2>&1
        $sw.Stop()
        $lines = $response -split "`n"
        $statusCode = $lines[-1]
        $timeMs = $sw.ElapsedMilliseconds
        Write-Host "Endpoint: $endpoint"
        Write-Host "Status: $statusCode"
        Write-Host "Time: ${timeMs}ms"
        Write-Host "---"
    } catch {
        Write-Host "Endpoint: $endpoint"
        Write-Host "Error: $_"
        Write-Host "---"
    }
}

Write-Host "Measurement complete"
