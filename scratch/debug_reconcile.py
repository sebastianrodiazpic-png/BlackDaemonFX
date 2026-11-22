import sys
sys.path.insert(0, ".")
import pathlib, tempfile
from types import SimpleNamespace
from database.repository import TradingRepository

with tempfile.TemporaryDirectory() as td:
    db_file = pathlib.Path(td) / "test.db"
    repo = TradingRepository(db_path=str(db_file))

    # Crear trade hermano TP1
    tp1_payload = {
        "external_ticket": "11111",
        "execution_key": "DEMO:UK Brent Oil:ORB:NY:M1:2026-11-09T09:25:00:BUY:TP1",
        "broker_position_ticket": "11111",
        "source": "DEMO",
        "broker": "MT5",
        "instrument": "UK Brent Oil",
        "timeframe": "M5",
        "direction": "BUY",
        "status": "OPEN",
        "result": "OPEN",
        "entry_price": 95.8,
        "stop_loss": 95.3,
        "take_profit": 96.3,
        "planned_rr": 1.0,
        "details": {
            "metadata": {
                "trade_leg": "TP1",
                "strategy_name": "ORB_NEW_YORK",
                "parent_execution_key": "DEMO:UK Brent Oil:ORB:NY:M1:2026-11-09T09:25:00:BUY",
            }
        },
        "strategy_version": "orb-ny-v5-sweep",
    }
    repo.create_trade_once(tp1_payload)

    mt5_positions = [{
        "position_ticket": 22222,
        "symbol": "UK Brent Oil",
        "direction": "BUY",
        "entry_price": 95.8,
        "stop_loss": 95.3,
        "take_profit": 98.0,
        "volume": 1.0,
        "magic": 26082028,
        "comment": "BlackDaemonFx",
        "identifier": 22222,
        "current_price": 95.8,
        "floating_profit": 0.0,
        "swap": 0.0,
    }]

    mock_executor = SimpleNamespace(
        list_open_positions=lambda: mt5_positions,
        account_info=lambda: {"equity": 5000.0},
    )

    res = repo.import_open_mt5_positions(
        mock_executor,
        source="DEMO",
        magic=26082028,
    )
    print("res:", res)
    ids = res.get("ids", [])
    if ids:
        t = repo.get_trade(ids[0])
        rec_meta = (t.get("details") or {}).get("metadata") or {}
        print("Recovered trade leg:", rec_meta.get("trade_leg"))
        print("Recovered parent_key:", rec_meta.get("parent_execution_key"))
        print("Recovered strategy:", rec_meta.get("strategy_name"))
        print("Recovered execution_mode:", rec_meta.get("execution_mode"))
    repo = None
    import gc; gc.collect()
