import urllib.request
import json

for port in [8765, 8000, 5000]:
    try:
        url = f"http://127.0.0.1:{port}/api/status"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as response:
            data = json.loads(response.read().decode())
            print(f"Puerto {port}: HTTP 200 OK - Status keys: {list(data.keys())}")
            if "workers" in data:
                print(f"Workers activos ({len(data['workers'])}):")
                for w in data["workers"][:5]:
                    print(" ", w.get("bot_profile"), w.get("status"), w.get("daemon_magic"))
            break
    except Exception as e:
        print(f"Puerto {port}: {e}")
