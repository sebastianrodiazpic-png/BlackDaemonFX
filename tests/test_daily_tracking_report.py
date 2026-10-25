"""Informe de seguimiento diario demo vs replay (tools/daily_tracking_report.py, 20-oct-2026)."""
import json
from datetime import date, datetime

from database.models import TradeJournal
from database.repository import TradingRepository
from tools import daily_tracking_report as rep


def _leg(s, key, sym, version, exit_time, pnl, risk=10.0, bot="VOLATILITY_1"):
    s.add(TradeJournal(journal_key=key, source="DEMO", instrument=sym, direction="BUY", status="CLOSED", net_pnl=pnl,
                       risk_amount=risk, execution_key=key, strategy_version=version, exit_time=exit_time,
                       details_json=json.dumps({"metadata": {"parent_execution_key": key.rsplit(":", 1)[0], "bot_profile": bot}})))


def _db(tmp_path):
    repo = TradingRepository(tmp_path / "t.sqlite")
    with repo.Session() as s:
        d20, d21 = datetime(2026, 10, 20, 12), datetime(2026, 10, 21, 9)
        _leg(s, "A:TP1", "Volatility 10 Index", "ict-sabri-malle-v2-fase1", d20, 10)   # op A: +1R
        _leg(s, "A:RUNNER", "Volatility 10 Index", "ict-sabri-malle-v2-fase1", d20, 10)
        _leg(s, "B:TP1", "Jump 75 Index", "ict-sabri-malle-v2-fase1", d21, -10)
        _leg(s, "B:RUNNER", "Jump 75 Index", "ict-sabri-malle-v2-fase1", d21, -10)
        _leg(s, "C:TP1", "Boom 500 Index", "msnr-v3.1-synthetics", d21, 5, bot="MALAYSIAN_SNR")
        _leg(s, "D:TP1", "US Oil", "ict-sabri-malle-v2-fase1", d21, -10, bot="ICT")
        s.commit()
    return tmp_path / "t.sqlite"


def test_family_classification():
    assert rep.family("ict-sabri-malle-v2-fase1", "High Frequency Vol 50 Index") == "ICT sintéticos"
    assert rep.family("ict-sabri-malle-v2-fase1", "XAUUSD") == "ICT mercados reales"
    assert rep.family("msnr-v3.1-synthetics", "Step Index 400") == "MSNR sintéticos"
    assert rep.family("msnr-video-v1", "Step Index 400") == "MSNR Vídeos"
    assert rep.family("orb-ny-sweep", "XAUUSD") == "ORB"
    assert rep.family("smc-v1", "Crash Boom Flip 1000 Index") == "Otros"


def test_report_groups_legs_into_operations_and_accumulates(tmp_path):
    db = _db(tmp_path)
    text, daily = rep.build_report(db, date(2026, 10, 21), date(2026, 10, 20))
    by = daily.set_index("familia")
    assert by.loc["ICT sintéticos", "operaciones"] == 1 and by.loc["ICT sintéticos", "R_op"] == -1.0
    assert by.loc["MSNR sintéticos", "R_op"] == 0.5 and by.loc["ICT mercados reales", "R_op"] == -1.0
    assert "## Acumulado" in text and "| ICT sintéticos | 2 | +0.000 |" in text  # +1R el 20 y −1R el 21
    assert "Jump 75 Index" in text


def test_verdict_flags_underperformance():
    import pandas as pd
    ops = pd.DataFrame({"family": ["ICT sintéticos"] * 100, "R": [-0.5] * 100, "pnl": [-5.0] * 100})
    s = rep.summarize(ops).iloc[0]
    assert s.veredicto == "POR DEBAJO" and s.z < -2
    ops = pd.DataFrame({"family": ["ICT sintéticos"] * 10, "R": [0.1] * 10, "pnl": [1.0] * 10})
    assert rep.summarize(ops).iloc[0].veredicto == "en línea"


def test_main_writes_report_and_history_idempotently(tmp_path):
    db = _db(tmp_path)
    out = tmp_path / "out"
    for _ in range(2):
        assert rep.main(["--db", str(db), "--day", "2026-10-21", "--since", "2026-10-20", "--out", str(out)]) == 0
    assert (out / "informe_2026-10-21.md").exists()
    import pandas as pd
    hist = pd.read_csv(out / "seguimiento_diario.csv")
    assert len(hist) == 3 and set(hist.dia) == {"2026-10-21"}  # sin duplicados al repetir el día
