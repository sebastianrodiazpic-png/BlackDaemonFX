import subprocess, json

cmd = "Get-CimInstance Win32_Process -Filter \"name like 'python%' or name like 'terminal64%'\" | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, WorkingSetSize | ConvertTo-Json"
res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True)

try:
    data = json.loads(res.stdout)
    if isinstance(data, dict):
        data = [data]
    print(f"{'Name':14} | {'PID':5} | {'PPID':5} | {'RAM (MB)':8} | Path")
    print("-" * 80)
    for p in sorted(data, key=lambda x: x.get('ProcessId') or 0):
        pid = p.get('ProcessId')
        ppid = p.get('ParentProcessId')
        name = p.get('Name')
        path = p.get('ExecutablePath') or ''
        ws = (p.get('WorkingSetSize') or 0) / (1024 * 1024)
        print(f"{name:14} | {pid:5} | {ppid:5} | {ws:8.1f} | {path}")
except Exception as e:
    print("Error parsing:", e, res.stdout[:500])
