import subprocess
import csv
import io

cmd = ['tasklist', '/fo', 'csv', '/v']
out = subprocess.check_output(cmd, text=True, errors='ignore')
reader = csv.reader(io.StringIO(out))
header = next(reader)
print("Header:", header)

for row in reader:
    if len(row) > 1:
        pname = row[0].lower()
        if 'python' in pname or 'terminal' in pname or 'metatrader' in pname or 'cmd' in pname or 'powershell' in pname:
            print(f"PID: {row[1]} | Image: {row[0]} | Mem: {row[4]} | User: {row[6]} | Title: {row[8] if len(row) > 8 else ''}")
