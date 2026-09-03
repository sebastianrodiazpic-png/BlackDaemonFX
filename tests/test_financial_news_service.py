from services.financial_news_service import classify_news_impact, parse_rss


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
