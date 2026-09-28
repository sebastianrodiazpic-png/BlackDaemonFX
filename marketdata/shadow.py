"""Compara Deriv contra MT5 sin permitir que MT5 decida el análisis."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading

import pandas as pd


class ShadowMarketDataProvider:
    source_name = "DERIV_PRIMARY_WITH_MT5_SHADOW"

    def __init__(self, primary, reference, *, output_path, maximum_close_divergence_atr=0.10):
        self.primary = primary
        self.reference = reference
        self.connector = getattr(primary, "connector", None)
        self.output_path = Path(output_path)
        self.maximum_close_divergence_atr = max(0.0, float(maximum_close_divergence_atr))
        self._write_lock = threading.Lock()

    def __getattr__(self, name):
        return getattr(self.primary, name)

    def connect(self):
        self.primary.connect()
        return True

    def disconnect(self):
        self.primary.disconnect()

    @staticmethod
    def _closed(frame):
        if "complete" in frame.columns:
            rows = frame[frame["complete"].astype(bool)]
            if not rows.empty:
                return rows
        return frame.iloc[:-1] if len(frame) > 1 else frame.iloc[0:0]

    def _write(self, payload):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":")) + "\n"
        # Una sola escritura append reduce intercalado entre los workers Windows.
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        with self._write_lock:
            descriptor = os.open(str(self.output_path), flags, 0o600)
            try:
                os.write(descriptor, line.encode("utf-8"))
            finally:
                os.close(descriptor)

    def get_candles(self, symbol, timeframe="M5", count=1000):
        primary = self.primary.get_candles(symbol, timeframe=timeframe, count=count)
        payload = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "kind": "CANDLES",
            "symbol": str(symbol),
            "timeframe": str(timeframe).upper(),
            "primary_source": primary.attrs.get("market_data_source"),
            "primary_rows": len(primary),
            "comparison_available": False,
        }
        try:
            reference = self.reference.get_candles(symbol, timeframe=timeframe, count=count)
            left = self._closed(primary)[["time", "high", "low", "close"]]
            right = self._closed(reference)[["time", "close"]]
            left, right = left.copy(), right.copy()
            left["time"] = pd.to_datetime(left["time"], utc=True)
            right["time"] = pd.to_datetime(right["time"], utc=True)
            left = left.sort_values("time").drop_duplicates("time")
            right = right.sort_values("time").drop_duplicates("time")
            payload.update({"latest_primary_time": str(left["time"].max()),
                            "latest_reference_time": str(right["time"].max()),
                            "quote_basis": "PROVIDER_CLOSE_BASIS_UNVERIFIED", "mode": "SHADOW_ONLY"})
            merged = left.merge(right, on="time", suffixes=("_deriv", "_mt5"))
            payload.update({
                "reference_rows": len(reference),
                "matched_closed_candles": len(merged),
            })
            if not merged.empty:
                candle_range = (merged["high"] - merged["low"]).abs().replace(0, pd.NA)
                median_range = float(candle_range.median()) if pd.notna(candle_range.median()) else 0.0
                delta = (merged["close_deriv"] - merged["close_mt5"]).abs()
                ratio = float(delta.max()) / median_range if median_range > 0 else None
                signed_delta = merged["close_deriv"] - merged["close_mt5"]
                median_offset = float(signed_delta.median())
                payload.update({"median_signed_offset": median_offset,
                    "offset_adjusted_maximum_delta": float((signed_delta - median_offset).abs().max()),
                    "latest_close_delta": float(delta.iloc[-1]),
                    "latest_close_divergence_range_ratio": float(delta.iloc[-1])/median_range if median_range > 0 else None,
                    "matched_fraction": len(merged)/max(len(left), len(right)) if max(len(left),len(right)) else 0})
                payload.update({
                    "comparison_available": True,
                    "latest_common_time": merged.iloc[-1]["time"],
                    "mean_close_delta": float(delta.mean()),
                    "maximum_close_delta": float(delta.max()),
                    "median_candle_range": median_range,
                    "maximum_close_divergence_range_ratio": ratio,
                    "within_tolerance": (
                        ratio is not None and ratio <= self.maximum_close_divergence_atr
                    ),
                })
        except Exception as exc:
            payload["comparison_error"] = str(exc)
        self._write(payload)
        primary.attrs["shadow_comparison"] = payload
        return primary

    def get_current_tick(self, symbol):
        tick = self.primary.get_current_tick(symbol)
        payload = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "kind": "TICK",
            "symbol": str(symbol),
            "primary_source": tick.get("source"),
            "comparison_available": False,
        }
        try:
            reference = self.reference.get_current_tick(symbol)
            deriv_mid = (float(tick["bid"]) + float(tick["ask"])) / 2
            mt5_mid = (float(reference["bid"]) + float(reference["ask"])) / 2
            payload.update({
                "comparison_available": True,
                "deriv_mid": deriv_mid,
                "mt5_mid": mt5_mid,
                "absolute_delta": abs(deriv_mid - mt5_mid),
                "primary_bid": tick.get("bid"), "primary_ask": tick.get("ask"),
                "reference_bid": reference.get("bid"), "reference_ask": reference.get("ask"),
                "primary_spread": float(tick["ask"])-float(tick["bid"]),
                "reference_spread": float(reference["ask"])-float(reference["bid"]),
                "mode": "SHADOW_ONLY",
            })
        except Exception as exc:
            payload["comparison_error"] = str(exc)
        self._write(payload)
        tick["shadow_comparison"] = payload
        return tick
