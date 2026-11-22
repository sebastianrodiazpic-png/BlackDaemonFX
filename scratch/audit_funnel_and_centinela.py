import sqlite3, os, json
from pathlib import Path
from collections import Counter

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("================ 1. SIGNALS TABLE BREAKDOWN ================")
cur.execute("SELECT COUNT(*) FROM signals")
total_sig = cur.fetchone()[0]
print(f"Total signals in DB: {total_sig}")

cur.execute("""
    SELECT instrument, direction, valid, COUNT(*) as cnt
    FROM signals
    WHERE id >= (SELECT MAX(id) - 3000 FROM signals)
    GROUP BY instrument, direction, valid
    ORDER BY cnt DESC
    LIMIT 20
""")
for r in cur.fetchall():
    print(f"  {r['instrument']:25} | {r['direction']:4} | valid={r['valid']} | count={r['cnt']}")

print("\n================ 2. SIGNALS DETAILS_JSON CHECK ================")
cur.execute("SELECT details_json FROM signals ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    try:
        det = json.loads(r['details_json'])
        # Compact sample
        print("  Signal detail keys:", list(det.keys())[:10])
        reason = det.get('reason') or det.get('setup_reason') or det.get('filter_reason')
        strat = det.get('strategy_name')
        print(f"    strat={strat}, reason={reason}")
    except Exception as e:
        print("    parse error:", e)

print("\n================ 3. CENTINELA BLOCKS BY INSTRUMENT ================")
cur.execute("SELECT MAX(id) FROM daemon_audit_events")
max_id = cur.fetchone()[0] or 0
cur.execute(f"""
    SELECT instrument, reason, COUNT(*) as cnt
    FROM daemon_audit_events
    WHERE id >= {max_id - 30000}
      AND (action LIKE '%REGIME%' OR reason LIKE '%REGIME%')
    GROUP BY instrument, reason
    ORDER BY cnt DESC
    LIMIT 25
""")
for r in cur.fetchall():
    print(f"  [{r['cnt']:4}x] {str(r['instrument']):25} | {r['reason']}")

print("\n================ 4. POSITION VISUAL AUDITS DETAILS ================")
cur.execute("SELECT * FROM position_visual_audits ORDER BY id DESC LIMIT 3")
for r in cur.fetchall():
    d = dict(r)
    chart_json = d.get('chart_json')
    meta = {}
    if chart_json:
        try:
            chart = json.loads(chart_json)
            meta = {
                "symbol": chart.get("chart", {}).get("symbol"),
                "timeframe": chart.get("chart", {}).get("timeframe"),
                "strategy": chart.get("strategy", {}).get("name"),
                "levels": chart.get("trade_levels"),
                "confluence": chart.get("confluence_score"),
            }
        except Exception:
            pass
    print(f"  Audit #{d['id']} | Profile={d['bot_profile']} | Magic={d['daemon_magic']} | meta={meta}")

print("\n================ 5. DATABASE SIZE & VACUUM / PRAGMA ANALYSIS ================")
cur.execute("PRAGMA page_count")
page_count = cur.fetchone()[0]
cur.execute("PRAGMA page_size")
page_size = cur.fetchone()[0]
cur.execute("PRAGMA freelist_count")
freelist_count = cur.fetchone()[0]
cur.execute("PRAGMA journal_mode")
journal_mode = cur.fetchone()[0]
cur.execute("PRAGMA synchronous")
synchronous = cur.fetchone()[0]

print(f"Page size: {page_size} bytes | Page count: {page_count:,} ({page_count*page_size/(1024*1024):.1f} MB)")
print(f"Freelist pages: {freelist_count:,} ({freelist_count*page_size/(1024*1024):.1f} MB wasted)")
print(f"Journal mode: {journal_mode} | Synchronous: {synchronous}")

conn.close()
