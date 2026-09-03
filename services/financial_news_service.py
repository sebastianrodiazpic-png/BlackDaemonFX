from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
import json
import threading
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree


DEFAULT_NEWS_FEED = (
    "https://news.google.com/rss/search?"
    "q=mercados+financieros+bolsa+economia&hl=es-419&gl=US&ceid=US:es-419"
)

_HIGH_IMPACT_TERMS = (
    "fed", "federal reserve", "banco central", "tipos de interes",
    "tasas de interes", "inflacion", "ipc", "pib", "empleo",
    "nominas", "desempleo", "nonfarm", "nfp", "cpi", "fomc",
    "recesion", "guerra", "arancel", "crisis bancaria", "default",
    "petroleo", "opec", "elecciones",
)


def _clean(value: str | None) -> str:
    return " ".join(unescape(str(value or "")).split())


def _published_at(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return raw


def classify_news_impact(title: str, description: str = "") -> str:
    text = f"{title} {description}".casefold()
    return "ALTO" if any(term in text for term in _HIGH_IMPACT_TERMS) else "MEDIO"


def parse_rss(xml_payload: bytes, limit: int = 20) -> list[dict]:
    root = ElementTree.fromstring(xml_payload)
    items = []
    for item in root.findall(".//item")[: max(1, int(limit))]:
        title = _clean(item.findtext("title"))
        link = _clean(item.findtext("link"))
        description = _clean(item.findtext("description"))
        published = _published_at(item.findtext("pubDate"))
        if not title or not link:
            continue
        items.append({
            "title": title,
            "description": description,
            "link": link,
            "published_at": published,
            "impact": classify_news_impact(title, description),
            "language": "es",
        })
    return items


class FinancialNewsService:
    def __init__(
        self,
        feed_url: str = DEFAULT_NEWS_FEED,
        state_path: str | Path | None = None,
        refresh_seconds: int = 600,
        timeout_seconds: int = 8,
    ):
        self.feed_url = str(feed_url)
        self.state_path = Path(state_path) if state_path else None
        self.refresh_seconds = max(60, int(refresh_seconds))
        self.timeout_seconds = max(2, int(timeout_seconds))
        self._lock = threading.RLock()
        self._news: list[dict] = []
        self._status = "PENDIENTE"
        self._updated_at = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._load()

    def _load(self):
        if not self.state_path or not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._news = list(data.get("news") or [])
                self._status = str(data.get("status") or "PERSISTIDA")
                self._updated_at = data.get("updated_at")
        except (OSError, ValueError, TypeError):
            self._status = "SIN_DATOS"

    def _persist(self):
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "news": self._news,
            "status": self._status,
            "updated_at": self._updated_at,
        }
        self.state_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def refresh(self) -> list[dict]:
        request = Request(self.feed_url, headers={"User-Agent": "DaemonBlackFx/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            news = parse_rss(response.read())
        high_impact = [row for row in news if row["impact"] == "ALTO"]
        ordered = high_impact + [row for row in news if row["impact"] != "ALTO"]
        with self._lock:
            self._news = ordered[:20]
            self._status = "ACTUALIZADA"
            self._updated_at = datetime.now(timezone.utc).isoformat()
            self._persist()
            return list(self._news)

    def _run(self):
        while not self._stop.is_set():
            try:
                self.refresh()
            except (HTTPError, URLError, TimeoutError, OSError, ElementTree.ParseError):
                with self._lock:
                    self._status = "NO DISPONIBLE · ÚLTIMO ESTADO"
            self._stop.wait(self.refresh_seconds)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="financial-news")
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread = None

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "items": list(self._news),
                "status": self._status,
                "updated_at": self._updated_at,
                "source_language": "es",
                "source": "Google News RSS",
            }
