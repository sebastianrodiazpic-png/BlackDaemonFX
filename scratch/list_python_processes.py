import subprocess
import json

cmd = "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Select-Object ProcessId, CommandLine | ConvertTo-Json"
proc = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)
if proc.stdout:
    try:
        data = json.loads(proc.stdout)
        if isinstance(data, dict):
            data = [data]
        for p in data:
            print(f"PID {p.get('ProcessId')}: {p.get('CommandLine')}")
    except Exception as e:
        print("Raw output:", proc.stdout)
else:
    print("Stderr:", proc.stderr)
