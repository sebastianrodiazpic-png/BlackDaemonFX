"""Resume la comparación JSONL Deriv Charts frente a MT5."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics


def _percentile(values, percentile):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    index = round((len(ordered) - 1) * float(percentile))
    return ordered[max(0, min(index, len(ordered) - 1))]


def summarize(path):
    path = Path(path)
    if not path.exists():
        return []
    groups = defaultdict(lambda: {
        "records": 0, "comparisons": 0, "within_tolerance": 0,
        "errors": 0, "matched_candles": 0, "ratios": [],
    })
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido en línea {line_number}: {exc}") from exc
            key = (
                str(row.get("kind") or "UNKNOWN"),
                str(row.get("symbol") or "UNKNOWN"),
                str(row.get("timeframe") or "-"),
            )
            group = groups[key]
            group["records"] += 1
            group["comparisons"] += int(bool(row.get("comparison_available")))
            group["within_tolerance"] += int(row.get("within_tolerance") is True)
            group["errors"] += int(bool(row.get("comparison_error")))
            group["matched_candles"] += int(row.get("matched_closed_candles") or 0)
            ratio = row.get("maximum_close_divergence_range_ratio")
            if ratio is not None:
                group["ratios"].append(float(ratio))
    result = []
    for (kind, symbol, timeframe), group in sorted(groups.items()):
        ratios = group.pop("ratios")
        comparisons = group["comparisons"]
        result.append({
            "kind": kind, "symbol": symbol, "timeframe": timeframe, **group,
            "tolerance_pass_rate": (
                round(group["within_tolerance"] / comparisons, 4) if comparisons else None
            ),
            "divergence_ratio_median": round(statistics.median(ratios), 6) if ratios else None,
            "divergence_ratio_p95": round(_percentile(ratios, 0.95), 6) if ratios else None,
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default="storage/analysis/market_data_shadow.jsonl")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    rows = summarize(args.file)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("Sin comparaciones registradas. Ejecute primero el daemon en modo shadow.")
        return
    print("TIPO | SÍMBOLO | TF | REGISTROS | COMPARABLES | OK | ERRORES | P95")
    for row in rows:
        print(
            f"{row['kind']} | {row['symbol']} | {row['timeframe']} | {row['records']} | "
            f"{row['comparisons']} | {row['within_tolerance']} | {row['errors']} | "
            f"{row['divergence_ratio_p95']}"
        )


if __name__ == "__main__":
    main()
