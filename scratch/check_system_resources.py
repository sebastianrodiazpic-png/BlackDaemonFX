import subprocess
import json

ps_cmd = """
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 20 ProcessName, Id, CPU,
    @{Name='WS_MB';Expression={[math]::Round($_.WorkingSet64 / 1MB, 1)}},
    @{Name='VM_MB';Expression={[math]::Round($_.VirtualMemorySize64 / 1MB, 1)}},
    @{Name='PM_MB';Expression={[math]::Round($_.PagedMemorySize64 / 1MB, 1)}} |
    ConvertTo-Json
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
if res.stdout.strip():
    data = json.loads(res.stdout)
    if isinstance(data, dict):
        data = [data]
    print(f"{'PID':<8} {'ProcessName':<25} {'WS(MB)':<10} {'VM(MB)':<12} {'PM(MB)':<10} {'CPU(s)':<10}")
    print("-" * 75)
    for p in data:
        print(f"{p.get('Id'):<8} {str(p.get('ProcessName'))[:24]:<25} {p.get('WS_MB', 0):<10} {p.get('VM_MB', 0):<12} {p.get('PM_MB', 0):<10} {round(p.get('CPU') or 0, 1):<10}")
else:
    print("No output from powershell:", res.stderr)
