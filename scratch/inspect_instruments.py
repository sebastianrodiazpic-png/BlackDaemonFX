from pathlib import Path

dashboard_path = Path("dashboard/realtime_dashboard.py")
text = dashboard_path.read_text(encoding="utf-8")

target = "visibleInstrumentGroups"
pos = text.find(target)
if pos != -1:
    print(text[pos-100:pos+1500].encode('ascii', errors='replace').decode('ascii'))
