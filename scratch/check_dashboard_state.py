import urllib.request, json

req = urllib.request.urlopen("http://127.0.0.1:8765/api/state", timeout=5)
data = json.loads(req.read().decode('utf-8'))
print("Keys in state:", list(data.keys()))
print("Selection profiles:", {k: len(v) for k, v in (data.get('selection_profiles') or {}).items()})
print("MALAYSIAN_SNR selection_profiles:", data.get('selection_profiles', {}).get('MALAYSIAN_SNR'))
workers = data.get('workers') or []
print(f"Workers count: {len(workers)}")
for w in workers:
    print(w.get('name'), w.get('profile'), w.get('status'), w.get('symbols_processed'), "/", w.get('symbols_total'))
