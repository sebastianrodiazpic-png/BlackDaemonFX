"""Construcción del feed Deriv-only con modo external/shadow/mt5."""

from dataclasses import dataclass
import json
import os
from pathlib import Path

from .cache import MarketDataCache
from .deriv import DerivMarketDataProvider
from .router import DerivOnlyMarketDataRouter, MarketDataConfigurationError
from .shadow import ShadowMarketDataProvider


def _load_project_dotenv():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def _json_mapping(raw):
    if not str(raw or "").strip():
        return {}
    try:
        value = json.loads(str(raw))
    except json.JSONDecodeError as exc:
        raise MarketDataConfigurationError(f"DAEMON_DERIV_SYMBOL_MAP_JSON inválido: {exc}") from exc
    if not isinstance(value, dict):
        raise MarketDataConfigurationError("El mapeo Deriv debe ser un objeto JSON")
    return {str(key): str(native) for key, native in value.items()}


@dataclass(frozen=True)
class ExternalMarketDataSettings:
    mode: str = "shadow"
    provider: str = "deriv"
    deriv_endpoint: str = "wss://api.derivws.com/trading/v1/options/ws/public"
    deriv_symbol_map_json: str | None = None
    candle_cache_ttl_seconds: float = 2.0
    tick_cache_ttl_seconds: float = 0.5
    shadow_output_path: str = "storage/analysis/market_data_shadow.jsonl"
    shadow_maximum_close_divergence_atr: float = 0.10

    @classmethod
    def from_environment(cls, mode=None):
        _load_project_dotenv()
        return cls(
            mode=str(mode or os.getenv("DAEMON_MARKET_DATA_MODE", "shadow")).casefold(),
            provider=str(os.getenv("DAEMON_MARKET_DATA_PROVIDER", "deriv")).casefold(),
            deriv_endpoint=os.getenv(
                "DERIV_WEBSOCKET_ENDPOINT",
                "wss://api.derivws.com/trading/v1/options/ws/public",
            ),
            deriv_symbol_map_json=os.getenv("DAEMON_DERIV_SYMBOL_MAP_JSON") or None,
            candle_cache_ttl_seconds=float(os.getenv("DAEMON_CANDLE_CACHE_TTL_SECONDS", "2.0")),
            tick_cache_ttl_seconds=float(os.getenv("DAEMON_TICK_CACHE_TTL_SECONDS", "0.5")),
            shadow_output_path=os.getenv(
                "DAEMON_MARKET_DATA_SHADOW_PATH",
                "storage/analysis/market_data_shadow.jsonl",
            ),
            shadow_maximum_close_divergence_atr=float(os.getenv(
                "DAEMON_SHADOW_MAX_CLOSE_DIVERGENCE_ATR", "0.10"
            )),
        )


def build_market_data_provider(metadata_provider, *, settings=None):
    settings = settings or ExternalMarketDataSettings.from_environment()
    mode = str(settings.mode).casefold()
    if mode not in {"external", "shadow", "mt5"}:
        raise MarketDataConfigurationError(f"DAEMON_MARKET_DATA_MODE inválido: {settings.mode}")
    if mode == "mt5":
        return metadata_provider
    if str(settings.provider).casefold() != "deriv":
        raise MarketDataConfigurationError(
            "v113.1 sólo admite DAEMON_MARKET_DATA_PROVIDER=deriv"
        )
    deriv = DerivMarketDataProvider(
        endpoint=settings.deriv_endpoint,
        symbol_map=_json_mapping(settings.deriv_symbol_map_json),
    )
    router = DerivOnlyMarketDataRouter(
        deriv_provider=deriv,
        metadata_provider=metadata_provider,
        cache=MarketDataCache(),
        candle_cache_ttl_seconds=settings.candle_cache_ttl_seconds,
        tick_cache_ttl_seconds=settings.tick_cache_ttl_seconds,
    )
    if mode == "shadow":
        return ShadowMarketDataProvider(
            router,
            metadata_provider,
            output_path=settings.shadow_output_path,
            maximum_close_divergence_atr=settings.shadow_maximum_close_divergence_atr,
        )
    return router
