import ast
from pathlib import Path

from marketdata.deriv import DerivMarketDataProvider
from marketdata.rate_limit import InterprocessRequestRateLimiter, NoopRequestRateLimiter


class SequenceTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def connect(self):
        return True

    def disconnect(self):
        return True

    def request(self, payload):
        self.requests.append(dict(payload))
        return self.responses.pop(0)


def test_rate_limit_response_is_retried(monkeypatch):
    transport = SequenceTransport([
        {"error": {"message": "Rate limit exceeded"}},
        {"active_symbols": [{
            "underlying_symbol_name": "Boom 900 Index",
            "underlying_symbol": "BOOM900",
        }]},
    ])
    monkeypatch.setattr("marketdata.deriv.time.sleep", lambda _seconds: None)
    provider = DerivMarketDataProvider(
        transport=transport,
        rate_limiter=NoopRequestRateLimiter(),
    )

    assert provider.resolve_native_symbol("Boom 900 Index") == "BOOM900"
    assert len(transport.requests) == 2


def test_us_sp_500_safe_alias_maps_to_current_public_catalog():
    transport = SequenceTransport([{
        "active_symbols": [{
            "underlying_symbol_name": "US 500",
            "underlying_symbol": "OTC_SPC",
        }]
    }])
    provider = DerivMarketDataProvider(transport=transport)
    assert provider.resolve_native_symbol("US SP 500") == "OTC_SPC"


def test_interprocess_limiter_persists_shared_timestamp(tmp_path):
    state = tmp_path / "deriv.lock"
    limiter = InterprocessRequestRateLimiter(state, minimum_interval_seconds=0.001)
    limiter.wait()
    limiter.wait()
    assert state.exists()
    assert float(state.read_text(encoding="ascii")) > 0


def _load_app_helpers(*names):
    source = Path("app/main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    selected = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names
    ]
    namespace = {}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "app/main.py", "exec"), namespace)
    return namespace


def test_forex_variants_remain_together_but_are_not_deleted():
    helpers = _load_app_helpers("_forex_native_family_key", "_stable_grouped_symbol_shard")
    shard = helpers["_stable_grouped_symbol_shard"]
    key = helpers["_forex_native_family_key"]
    symbols = ["EURUSD", "EURUSDmicro", "GBPUSD", "GBPUSDmicro", "USDJPY"]
    shards = [shard(symbols, index, 4, key) for index in range(4)]

    assert sorted(item for values in shards for item in values) == sorted(symbols)
    assert any({"EURUSD", "EURUSDmicro"}.issubset(set(values)) for values in shards)
    assert any({"GBPUSD", "GBPUSDmicro"}.issubset(set(values)) for values in shards)


def test_preflight_and_coordinator_contain_recovery_guards():
    source = Path("app/main.py").read_text(encoding="utf-8")
    assert '"deferred": transient_failure(message)' in source
    assert '"symbols": [row["symbol"] for row in runnable]' in source
    assert "DAEMON_WORKER_STALL_TIMEOUT_SECONDS" in source
    assert "STALL_RESTART_BLOCKED_OPEN_POSITIONS" in source
