import subprocess

out = subprocess.check_output(['wmic', 'process', 'where', "name='python.exe'", 'get', 'processid,commandline'], text=True)
for line in out.splitlines():
    if line.strip():
        print(line.strip()[:140])
