import subprocess
ps_cmd = """
$c = Get-Counter -Counter '\PhysicalDisk(_Total)\% Disk Time', '\PhysicalDisk(_Total)\Current Disk Queue Length'
$c.CounterSamples | Select-Object Path, CookedValue
"""
res = subprocess.run(['powershell', '-NoProfile', '-Command', ps_cmd], capture_output=True, text=True)
print(res.stdout)
