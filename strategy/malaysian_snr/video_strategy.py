"""Estrategia MSNR de los vídeos (worker MSNR, pestaña MSNR de /Instruments) — 20-oct-2026.

Variante independiente de Malaysian SNR basada en el curso Alchemist (ver MSNR_VIDEOS_VS_IMPLEMENTACION_20261020.md):
- Entrada de confirmación H4→H1: H4 rechaza un nivel A/V H4 y H1 rompe un nivel open-close
  (strategy/malaysian_snr/h4h1_confirmation.py). Validada en replay: +0,029 R/t (con política de dirección +0,017),
  positiva en ambos años.
- Storyline diaria D1+H4 (strategy/malaysian_snr/storyline.py): `observe` la registra en la señal; `filter` exige
  operar a su favor (en el replay como filtro no mejoró, por eso `observe` es el valor por defecto).
- Gestión del contrato del usuario: 1 % en 2 patas, TP1 1R, runner a BE tras TP1 y TP2 2R (+ extensión progresiva).
Solo sintéticos.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy, is_synthetic_symbol
from strategy.malaysian_snr.validation import closed_candles

MSNR_VIDEO_STRATEGY = "MSNR_VIDEO"
MSNR_VIDEO_VERSION = "msnr-video-v1"


@dataclass
class MSNRVideoConfig:
    enabled: bool = True
    strategy_name: str = MSNR_VIDEO_STRATEGY
    strategy_version: str = MSNR_VIDEO_VERSION
    storyline_mode: str = "observe"  # off | observe | filter
    synthetics_only: bool = True
    excluded_symbols: tuple = ()
    runner_rr: float = 2.0


class MSNRVideoStrategy:
    def __init__(self, data_provider, config: MSNRVideoConfig | None = None):
        self.provider = data_provider
        self.config = config or MSNRVideoConfig()
        self._engine = MalaysianSNRStrategy(data_provider, MalaysianSNRConfig(
            enabled=True, strategy_name=self.config.strategy_name, strategy_version=self.config.strategy_version,
            enable_h4h1_confirmation=True, h4h1_runner_rr=self.config.runner_rr,
            h4h1_synthetics_only=self.config.synthetics_only,
            excluded_symbols=tuple(self.config.excluded_symbols)))

    def _base(self, symbol, reason):
        return {"valid": False, "strategy_name": self.config.strategy_name, "strategy_version": self.config.strategy_version,
                "symbol": symbol, "action": "WAITING_MSNR_VIDEO", "reason": reason}

    def storyline(self, symbol, now) -> str:
        from strategy.malaysian_snr.storyline import current_storyline
        try:
            d1 = closed_candles(self.provider.get_candles(symbol, "D1", count=200), "D1", now)
            h4 = closed_candles(self.provider.get_candles(symbol, "H4", count=420), "H4", now)
        except Exception:
            return "UNAVAILABLE"
        return current_storyline(d1, h4, now)

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        if not self.config.enabled:
            return self._base(symbol, "STRATEGY_DISABLED")
        if self.config.synthetics_only and not is_synthetic_symbol(symbol):
            return self._base(symbol, "MSNR_VIDEO_SYNTHETICS_ONLY")
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
        result = self._engine._h4h1_signal(symbol, now.to_pydatetime())
        if result is None:
            return self._base(symbol, "NO_H4H1_CONFIRMATION")
        signal = result["signal"]
        mode = str(self.config.storyline_mode or "observe").lower()
        if mode != "off":
            story = self.storyline(symbol, now)
            signal["storyline"] = story
            signal["storyline_alignment"] = ("A_FAVOR" if story == signal["direction"] else
                                             "SIN_STORYLINE" if story in ("NONE", "UNAVAILABLE") else "EN_CONTRA")
            if mode == "filter" and story != signal["direction"]:
                return {**self._base(symbol, f"STORYLINE_{signal['storyline_alignment']}"), "signal": signal}
        signal.update(strategy_name=self.config.strategy_name, strategy_version=self.config.strategy_version)
        result.update(strategy_name=self.config.strategy_name, strategy_version=self.config.strategy_version,
                      action="MSNR_VIDEO_CONFIRMED",
                      reason=f"{signal['scenario']} confirmed ({signal['direction']} on {symbol})")
        return result
