from datetime import datetime, timezone
from urllib.error import HTTPError

from services.financial_news_service import (
    FinancialNewsService,
    classify_news_impact,
    parse_economic_calendar,
    parse_rss,
)


def test_high_impact_news_is_classified_in_spanish():
    assert classify_news_impact("La Fed mantiene los tipos de interés") == "ALTO"
    assert classify_news_impact("Las bolsas europeas avanzan") == "MEDIO"


def test_rss_parser_returns_spanish_news_and_impact():
    payload = b"""<?xml version="1.0"?><rss><channel><item>
        <title>Inflacion de Estados Unidos sorprende al mercado</title>
        <link>https://example.test/news</link>
        <description>El IPC cambia las expectativas.</description>
        <pubDate>Thu, 03 Sep 2026 18:00:00 GMT</pubDate>
    </item></channel></rss>"""

    result = parse_rss(payload)

    assert result[0]["language"] == "es"
    assert result[0]["impact"] == "ALTO"
    assert result[0]["title"].startswith("Inflacion")


def test_economic_calendar_exposes_upcoming_event_in_spanish():
    payload = b"""[
        {
            "title": "Non-Farm Employment Change",
            "country": "USD",
            "date": "2026-09-04T08:30:00-04:00",
            "impact": "High",
            "forecast": "75K",
            "previous": "73K"
        }
    ]"""

    events = parse_economic_calendar(
        payload,
        now=datetime(2026, 9, 4, 12, tzinfo=timezone.utc),
    )

    assert events == [{
        "title": "Cambio de empleo no agrícola",
        "title_original": "Non-Farm Employment Change",
        "country": "USD",
        "impact": "ALTO",
        "event_at": "2026-09-04T12:30:00+00:00",
        "forecast": "75K",
        "previous": "73K",
        "language": "es",
    }]


def test_calendar_failure_preserves_headlines_and_reports_status(monkeypatch):
    class Response:
        def __init__(self, body):
            self.body = body

        def read(self):
            return self.body

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    rss = b"""<?xml version="1.0"?><rss><channel><item>
        <title>Inflacion de Estados Unidos sorprende al mercado</title>
        <link>https://example.test/news</link>
        <description>El IPC cambia las expectativas.</description>
        <pubDate>Thu, 03 Sep 2026 18:00:00 GMT</pubDate>
    </item></channel></rss>"""
    calls = 0

    def fake_urlopen(*_, **__):
        nonlocal calls
        calls += 1
        if calls == 1:
            return Response(rss)
        raise HTTPError("https://calendar.test", 429, "Too Many Requests", {}, None)

    monkeypatch.setattr("services.financial_news_service.urlopen", fake_urlopen)
    service = FinancialNewsService(feed_url="https://rss.test", calendar_url="https://calendar.test")
    service.refresh()

    snapshot = service.snapshot()
    assert len(snapshot["items"]) == 1
    assert snapshot["calendar"]["events"] == []
    assert "HTTPError" in snapshot["calendar"]["status"]
