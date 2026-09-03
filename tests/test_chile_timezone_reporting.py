from datetime import datetime, timezone

from reporting.trade_report_exporter import TradeReportExporter


def test_chile_timezone_conversion_winter_and_summer():
    # Chile continental usa America/Santiago; en 2026 cambia de UTC-4 a UTC-3.
    winter = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)
    summer = datetime(2026, 9, 7, 12, 0, tzinfo=timezone.utc)

    winter_local = TradeReportExporter._format_chile_datetime(winter)
    summer_local = TradeReportExporter._format_chile_datetime(summer)

    assert "2026-08-27 08:00:00 CLT (UTC-04:00)" == winter_local
    assert "2026-09-07 09:00:00 CLST (UTC-03:00)" == summer_local
