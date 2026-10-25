"""ICT en índices US analiza con las velas del broker MT5 y no con Deriv (23-oct-2026)."""
import os
import subprocess
import sys
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, _SymbolRoutedProvider, _symbol_routed_provider


def _providers():
    deriv = SimpleNamespace(get_candles=lambda s, timeframe="M5", count=1000: ("deriv", s, timeframe),
                            get_current_tick=lambda s: ("deriv-tick", s), resolve_symbol=lambda s: s, name="deriv")
    mt5 = SimpleNamespace(get_candles=lambda s, timeframe="M5", count=1000: ("mt5", s, timeframe),
                          get_current_tick=lambda s: ("mt5-tick", s))
    shadow = SimpleNamespace(get_candles=deriv.get_candles, get_current_tick=deriv.get_current_tick,
                             resolve_symbol=deriv.resolve_symbol, reference=mt5, name="shadow")
    return shadow, mt5


def test_default_symbols_are_the_three_us_indices():
    assert LiveTradingConfig().ict_broker_candle_symbols == ("US SP 500", "US Tech 100", "Wall Street 30")


def test_routing_sends_us_indices_to_broker_and_rest_to_primary():
    shadow, _ = _providers()
    routed = _symbol_routed_provider(shadow, ("US SP 500", "US Tech 100", "Wall Street 30"))
    assert isinstance(routed, _SymbolRoutedProvider)
    assert routed.get_candles("US Tech 100", "H1", count=81)[0] == "mt5"
    assert routed.get_current_tick("Wall Street 30")[0] == "mt5-tick"
    assert routed.get_candles("XAUUSD", "H1", count=81)[0] == "deriv"           # oro: Deriv ≈ MT5, sin cambio
    assert routed.get_candles("Volatility 75 Index", "M15")[0] == "deriv"       # sintéticos sin cambio
    assert routed.resolve_symbol("US SP 500") == "US SP 500" and routed.name == "shadow"  # resto delegado


def test_no_wrapping_without_broker_reference_or_symbols():
    shadow, mt5 = _providers()
    assert _symbol_routed_provider(mt5, ("US SP 500",)) is mt5                  # modo mt5: ya es el broker
    assert _symbol_routed_provider(shadow, ()) is shadow                         # interruptor vacío


def test_engine_builds_ict_strategy_with_routed_provider():
    src = open(sys.modules[LiveTradingConfig.__module__].__file__, encoding="utf-8").read()
    assert 'data_provider=_symbol_routed_provider(provider, getattr(self.config, "ict_broker_candle_symbols", ())),' in src


def test_env_switch_empties_list():
    code = "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().ict_broker_candle_symbols)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         env={**os.environ, "DAEMONBLACKFX_ICT_BROKER_CANDLE_SYMBOLS": ""}, cwd=os.getcwd())
    assert out.stdout.strip() == "()", out.stderr


def test_regime_sentinel_reads_broker_candles_for_us_indices():
    src = open(sys.modules[LiveTradingConfig.__module__].__file__, encoding="utf-8").read()
    i = src.index("    def _market_regime_entry_gate(self, symbol: str)")
    body = src[i:i + 2500]
    assert 'regime_provider = _symbol_routed_provider(self.provider, getattr(self.config, "ict_broker_candle_symbols", ()))' in body
