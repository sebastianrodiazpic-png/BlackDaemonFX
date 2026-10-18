import urllib.request, json

req = urllib.request.urlopen("http://127.0.0.1:8765/api/state")
data = json.loads(req.read().decode('utf-8'))
workers = data.get('workers', [])
for w in workers:
    if w.get('name') == 'MALAYSIAN_SNR':
        print("MALAYSIAN_SNR Worker in dashboard:")
        print("Status:", w.get('status'))
        print("Symbols processed:", w.get('symbols_processed'), "/", w.get('symbols_total'))
        print("Current symbol:", w.get('current_symbol'))
        print("Progress message:", w.get('progress_message'))
print("\nGlobal symbols_total:", data.get('symbols_total'))
print("Global symbols_processed:", data.get('symbols_processed'))
print("Selection version:", data.get('selection_version'))
