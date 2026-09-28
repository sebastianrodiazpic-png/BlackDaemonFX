"""Read-only comparison of SMC diagnostic variants; not a PnL backtest.

Usage: python -m tools.smc_shadow_report --database PATH --since UTC_ISO
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3


def summarize(rows):
    counts = Counter()
    for payload, in rows:
        result = json.loads(payload or "{}").get("result", {})
        if result.get("strategy_name") != "SMC":
            continue
        counts["smc_evaluations"] += 1
        comparison = result.get("entry_location_comparison") or {}
        if comparison:
            counts["location_compared"] += 1
            counts["h1_only_extra_passes"] += int(bool(comparison.get("H1_PRIMARY", {}).get("valid")) and not bool(comparison.get("ALL_TIMEFRAMES", {}).get("valid")))
        retest = result.get("retest_comparison") or {}
        if retest:
            counts["retest_compared"] += 1
            counts["atr_extra_clean_retests"] += int(bool(retest.get("atr_bounded_clean")) and not bool(retest.get("strict_clean")))
        for reason in result.get("critical_confirmation_failures") or []:
            counts["critical:" + str(reason)] += 1
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--since", required=True, help="UTC ISO timestamp")
    args = parser.parse_args()
    uri = Path(args.database).resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        rows = connection.execute("SELECT payload_json FROM daemon_audit_events WHERE event_type='SYMBOL_PROCESS_RESULT' AND event_time >= ?", (args.since,))
        print(json.dumps(summarize(rows), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
