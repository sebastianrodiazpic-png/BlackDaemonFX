"""Proveedor OANDA v20 para Forex, oro e indices tradicionales."""

from __future__ import annotations

import json
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from .normalization import MarketDataIdentity, MarketDataValidationError, normalize_candles, normalize_tick


OANDA_GRANULARITY = {
    "M1": "M1", "M2": "M2", "M3": "M3", "M4": "M4", "M5": "M5",
    "M10": "M10", "M15": "M15", "M30": "M30", "H1": "H1",
    "H2": "H2", "H4": "H4", "D1": "D",
}


class OandaAPIError(RuntimeError):
    pass


class OandaHTTPTransport:
    def __init__(self, base_url, token, timeout_seconds=12.0):
        self.base_url = str(base_url).rstrip("/")
        self.token = str(token)
        self.timeout_seconds = float(timeout_seconds)

    def get(self, path, params=None):
        url = f"{self.base_url}/{str(path).lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(url, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept-Datetime-Format": "RFC3339",
            "User-Agent": "DaemonBlackFx/market-data",
        })
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise OandaAPIError(f"OANDA no respondio para {path}: {exc}") from exc


class OandaMarketDataProvider:
    source_name = "OANDA_V20"

    def __init__(self, *, token, account_id=None, environment="practice", symbol_map=None, transport=None):
        if not str(token or "").strip() and transport is None:
            raise MarketDataValidationError(
                "Falta OANDA_API_TOKEN para analizar FOREX, GOLD y ORB sin MT5"
            )
        base = (
            "https://api-fxpractice.oanda.com/v3"
            if str(environment).casefold() == "practice"
            else "https://api-fxtrade.oanda.com/v3"
        )
        self.transport = transport or OandaHTTPTransport(base, str(token))
        self.account_id = str(account_id or "").strip() or None
        self.symbol_map = {str(k).casefold(): str(v) for k, v in (symbol_map or {}).items()}

    def connect(self): return True
    def disconnect(self): return True

    @staticmethod
    def _forex_native(execution_symbol):
        letters = "".join(ch for ch in str(execution_symbol).upper() if ch.isalpha())
        if len(letters) >= 6:
            base, counter = letters[:3], letters[3:6]
            known = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"}
            if base in known and counter in known:
                return f"{base}_{counter}"
        return None

    def resolve_native_symbol(self, execution_symbol):
        requested = str(execution_symbol).strip()
        explicit = self.symbol_map.get(requested.casefold())
        if explicit:
            return explicit
        automatic = self._forex_native(requested)
        if automatic:
            return automatic
        raise MarketDataValidationError(
            f"No existe mapeo OANDA para '{requested}'. Definalo en DAEMON_OANDA_SYMBOL_MAP_JSON."
        )

    def get_candles(self, execution_symbol, timeframe="M5", count=1000):
        native = self.resolve_native_symbol(execution_symbol)
        granularity = OANDA_GRANULARITY.get(str(timeframe).upper())
        if not granularity:
            raise ValueError(f"Timeframe OANDA no soportado: {timeframe}")
        response = self.transport.get(
            f"instruments/{quote(native, safe='_')}/candles",
            {"count": min(5000, max(3, int(count))), "granularity": granularity, "price": "M", "smooth": "false"},
        )
        if response.get("errorMessage"):
            raise OandaAPIError(str(response["errorMessage"]))
        rows = []
        for candle in response.get("candles") or []:
            mid = candle.get("mid") or {}
            rows.append({
                "time": candle.get("time"), "open": mid.get("o"), "high": mid.get("h"),
                "low": mid.get("l"), "close": mid.get("c"),
                "tick_volume": candle.get("volume", 0), "real_volume": 0, "spread": 0,
                "complete": bool(candle.get("complete", False)),
            })
        return normalize_candles(
            rows,
            identity=MarketDataIdentity(str(execution_symbol), native, self.source_name),
            timeframe=timeframe,
        )

    def get_current_tick(self, execution_symbol):
        native = self.resolve_native_symbol(execution_symbol)
        identity = MarketDataIdentity(str(execution_symbol), native, self.source_name)
        if self.account_id:
            response = self.transport.get(
                f"accounts/{quote(self.account_id, safe='-')}/pricing", {"instruments": native},
            )
            prices = list(response.get("prices") or [])
            if prices:
                price = prices[0]
                bids, asks = price.get("bids") or [], price.get("asks") or []
                return normalize_tick({
                    "bid": (bids[0] or {}).get("price") if bids else price.get("closeoutBid"),
                    "ask": (asks[0] or {}).get("price") if asks else price.get("closeoutAsk"),
                    "time": price.get("time"),
                    "volume": ((bids[0] or {}).get("liquidity", 0) if bids else 0),
                }, identity=identity)
        candles = self.get_candles(execution_symbol, "M1", count=3)
        last = float(candles.iloc[-1]["close"])
        return normalize_tick({
            "last": last, "bid": last, "ask": last, "time": candles.iloc[-1]["time"],
        }, identity=identity)
