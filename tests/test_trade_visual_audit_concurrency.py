import threading
import pytest
from database.repository import TradingRepository

def test_upsert_trade_visual_audit_concurrency(tmp_path):
    # Initialize a temporary isolated sqlite database
    db_file = tmp_path / "test_concurrency.sqlite3"
    repo = TradingRepository(db_path=db_file)

    trade_id = 99999
    results = []
    errors = []

    def worker_upsert(worker_id):
        try:
            row_id = repo.upsert_trade_visual_audit(
                trade_id=trade_id,
                instrument="Jump 25 Index",
                bot_profile="JUMP",
                daemon_magic=12345,
                broker_position_ticket=f"TICKET_{worker_id}",
                entry_context={"worker": worker_id, "score": 95},
                latest_market={"bid": 100.0 + worker_id},
            )
            results.append(row_id)
        except Exception as e:
            errors.append(e)

    # Launch 6 concurrent threads trying to insert the same trade_id simultaneously
    threads = [threading.Thread(target=worker_upsert, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # None should have failed with IntegrityError
    assert len(errors) == 0, f"Errors encountered: {errors}"
    assert len(results) == 6
    # All should reference the exact same persistent visual audit row ID
    assert len(set(results)) == 1

    # Verify data in database
    audit = repo.get_trade_visual_audit(trade_id)
    assert audit is not None
    assert audit["trade_id"] == trade_id
    assert audit["instrument"] == "Jump 25 Index"
    assert audit["entry_context"] is not None
