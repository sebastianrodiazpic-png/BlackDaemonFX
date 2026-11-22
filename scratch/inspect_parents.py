import subprocess
import json

ps_cmd = """
Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -in @(12932, 13288)} |
    Select-Object ProcessId, ParentProcessId, CommandLine, CreationDate |
    ConvertTo-Json
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
print(res.stdout)
