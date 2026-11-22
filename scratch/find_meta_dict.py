with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '_WORKER_PROFILE_META = {' in l:
        print(f'_WORKER_PROFILE_META starts at line {i+1}')
        for j in range(i, i+150):
            if '"ICT":' in lines[j]:
                print(f'"ICT" in _WORKER_PROFILE_META at line {j+1}')
                for k in range(j, j+20):
                    print(f'{k+1}: {lines[k].rstrip()}')
                break
