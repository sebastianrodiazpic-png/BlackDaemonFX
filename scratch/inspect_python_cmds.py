import subprocess
import json

ps_cmd = """
Get-CimInstance Win32_Process | Where-Object {$_.Name -eq 'python.exe'} |
    Select-Object ProcessId, CommandLine,
        @{Name='WS_MB';Expression={[math]::Round($_.WorkingSetSize / 1MB, 1)}},
        @{Name='PageFile_MB';Expression={[math]::Round($_.PageFileUsage / 1KB, 1)}} |
    ConvertTo-Json
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
if res.stdout.strip():
    data = json.loads(res.stdout)
    if isinstance(data, dict):
        data = [data]
    for p in sorted(data, key=lambda x: -x.get('WS_MB', 0)):
        print(f"PID: {p.get('ProcessId')}, WS: {p.get('WS_MB')} MB, PageFile: {p.get('PageFile_MB')} MB")
        print(f"  CMD: {p.get('CommandLine')}\n")
else:
    print("No output:", res.stderr)
