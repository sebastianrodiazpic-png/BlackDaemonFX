"""Noticias financieras y calendario macroeconomico para el dashboard.

Descarga en segundo plano un RSS de noticias y la agenda semanal de eventos de
alto impacto, los normaliza a UTC y en espanol, y los persiste en un JSON para
que otros procesos los lean sin repetir la descarga.

IMPORTANTE: este servicio es INFORMATIVO y, cuando se usa como filtro, solo
bloquea la APERTURA de nuevas entradas en Forex durante ventanas de noticia.
Nunca cierra una posicion ya abierta: un evento macro no invalida la estructura
de una operacion en curso.

Toda la red esta aislada: cualquier fallo degrada el estado a "NO DISPONIBLE"
conservando el ultimo dato bueno, jamas propaga la excepcion al bot.

Vinculaciones:
    - `dashboard.realtime_dashboard`: consumidor de `snapshot()`.
    - `load_economic_calendar_state`: lectura del JSON persistido por procesos
      que no ejecutan el dashboard.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
DEFAULT_ECONOMIC_CALENDAR_URL = (
    "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
)

_HIGH_IMPACT_TERMS = (
    "fed", "federal reserve", "banco central", "tipos de interes",
    "tasas de interes", "inflacion", "ipc", "pib", "empleo",
    "nominas", "desempleo", "nonfarm", "nfp", "cpi", "fomc",
    "recesion", "guerra", "arancel", "crisis bancaria", "default",
    "petroleo", "opec", "elecciones",
)

_CALENDAR_IMPACT_LABELS = {
    "HIGH": "ALTO",
    "MEDIUM": "MEDIO",
    "LOW": "BAJO",
    "HOLIDAY": "FERIADO",
}

_CALENDAR_TITLE_TRANSLATIONS = (
    ("Non-Farm Employment Change", "Cambio de empleo no agrícola"),
    ("Unemployment Rate", "Tasa de desempleo"),
    ("Average Hourly Earnings", "Ganancias medias por hora"),
    ("Federal Funds Rate", "Tasa de fondos federales"),
    ("Interest Rate Decision", "Decisión de tasas de interés"),
    ("Monetary Policy Statement", "Comunicado de política monetaria"),
    ("Consumer Price Index", "Índice de precios al consumidor"),
    ("Core CPI", "IPC subyacente"),
    ("Inflation Rate", "Tasa de inflación"),
    ("Gross Domestic Product", "Producto interno bruto"),
    ("Retail Sales", "Ventas minoristas"),
    ("Industrial Production", "Producción industrial"),
    ("Manufacturing PMI", "PMI manufacturero"),
    ("Services PMI", "PMI de servicios"),
    ("Consumer Confidence", "Confianza del consumidor"),
    ("Bank Holiday", "Feriado bancario"),
    ("Prelim", "Preliminar"),
    ("Final", "Final"),
    ("m/m", "mensual"),
    ("q/q", "trimestral"),
    ("y/y", "anual"),
)


def _clean(value: str | None) -> str:
    """Normaliza texto HTML: desescapa entidades y colapsa espacios."""
    return " ".join(unescape(str(value or "")).split())


def _published_at(value: str | None) -> str:
    """Convierte una fecha RFC-2822 de RSS a ISO-8601 UTC.

    Si no se puede interpretar devuelve el texto original en lugar de fallar:
    una fecha rara no debe tumbar la lectura del feed completo.
    """
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return raw


def classify_news_impact(title: str, description: str = "") -> str:
    """Clasifica una noticia como ALTO o MEDIO impacto.

    Heuristica por palabras clave (`_HIGH_IMPACT_TERMS`): banca central,
    inflacion, empleo, geopolitica. Es deliberadamente simple; solo alimenta el
    orden de presentacion, no decisiones de trading.
    """
    text = f"{title} {description}".casefold()
    return "ALTO" if any(term in text for term in _HIGH_IMPACT_TERMS) else "MEDIO"


def parse_rss(xml_payload: bytes, limit: int = 20) -> list[dict]:
    """Extrae los items de un feed RSS a diccionarios normalizados.

    Descarta entradas sin titulo o sin enlace. Funcion pura: recibe los bytes
    ya descargados, por lo que es directamente testeable sin red.

    Args:
        xml_payload: contenido XML del feed.
        limit: maximo de items a procesar.

    Returns:
        Lista de dicts con title, description, link, published_at e impact.
    """
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


def _calendar_time(value: str | None) -> datetime | None:
    """Interpreta la fecha ISO de un evento y la lleva a UTC.

    Asume UTC cuando el valor viene sin zona horaria. Devuelve `None` si no es
    interpretable, para que el evento se descarte sin romper el resto.
    """
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def translate_calendar_title(title: str) -> str:
    """Traduce al espanol los nombres de eventos macro mas habituales.

    Sustitucion por tabla (`_CALENDAR_TITLE_TRANSLATIONS`); lo no reconocido se
    deja tal cual, por eso tambien se conserva `title_original`.
    """
    translated = _clean(title)
    for source, target in _CALENDAR_TITLE_TRANSLATIONS:
        translated = translated.replace(source, target)
    return translated


def parse_economic_calendar(
    json_payload: bytes,
    *,
    now: datetime | None = None,
    limit: int = 20,
) -> list[dict]:
    """Normaliza los próximos eventos macroeconómicos a UTC para el dashboard."""
    raw_events = json.loads(json_payload.decode("utf-8"))
    if not isinstance(raw_events, list):
        raise ValueError("El calendario económico no contiene una lista de eventos")
    reference = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = reference - timedelta(minutes=5)
    events = []
    for row in raw_events:
        if not isinstance(row, dict):
            continue
        event_time = _calendar_time(row.get("date"))
        title = _clean(row.get("title"))
        if event_time is None or event_time < cutoff or not title:
            continue
        impact = _CALENDAR_IMPACT_LABELS.get(
            str(row.get("impact") or "").upper(),
            "MEDIO",
        )
        events.append({
            "title": translate_calendar_title(title),
            "title_original": title,
            "country": _clean(row.get("country")) or "GLOBAL",
            "impact": impact,
            "event_at": event_time.isoformat(),
            "forecast": _clean(row.get("forecast")),
            "previous": _clean(row.get("previous")),
            "language": "es",
        })
    return sorted(
        events,
        key=lambda event: (
            event["event_at"],
            {"ALTO": 0, "MEDIO": 1, "BAJO": 2, "FERIADO": 3}.get(
                event["impact"],
                4,
            ),
        ),
    )[:max(1, int(limit))]


def load_economic_calendar_state(state_path: str | Path) -> dict:
    """Lee la agenda persistida para consumidores que no ejecutan el dashboard."""
    path = Path(state_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"events": [], "status": "SIN_ARCHIVO_DE_AGENDA", "updated_at": None}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        return {
            "events": [],
            "status": f"AGENDA_NO_LEIBLE:{type(error).__name__}",
            "updated_at": None,
        }
    if not isinstance(payload, dict):
        return {"events": [], "status": "AGENDA_CONTRATO_INVALIDO", "updated_at": None}
    events = payload.get("calendar_events")
    return {
        "events": list(events) if isinstance(events, list) else [],
        "status": str(payload.get("calendar_status") or "PENDIENTE"),
        "updated_at": payload.get("updated_at"),
    }


class FinancialNewsService:
    """Recolector en segundo plano de noticias y agenda macro.

    Mantiene el ultimo estado bueno en memoria y en disco. El hilo es `daemon`
    para que no impida cerrar el proceso, y todo acceso al estado compartido
    pasa por un `RLock` porque el dashboard lee mientras el hilo escribe.
    """

    def __init__(
        self,
        feed_url: str = DEFAULT_NEWS_FEED,
        calendar_url: str = DEFAULT_ECONOMIC_CALENDAR_URL,
        state_path: str | Path | None = None,
        refresh_seconds: int = 600,
        timeout_seconds: int = 8,
    ):
        """Configura fuentes y periodicidad, y rehidrata el estado del disco.

        Args:
            feed_url: RSS de noticias.
            calendar_url: JSON del calendario economico semanal.
            state_path: fichero donde se persiste el ultimo snapshot.
            refresh_seconds: periodo de refresco; se fuerza un minimo de 60 s
                para no abusar de las fuentes publicas.
            timeout_seconds: timeout de red; minimo 2 s.
        """
        self.feed_url = str(feed_url)
        self.calendar_url = str(calendar_url)
        self.state_path = Path(state_path) if state_path else None
        self.refresh_seconds = max(60, int(refresh_seconds))
        self.timeout_seconds = max(2, int(timeout_seconds))
        self._lock = threading.RLock()
        self._news: list[dict] = []
        self._calendar_events: list[dict] = []
        self._status = "PENDIENTE"
        self._calendar_status = "PENDIENTE"
        self._updated_at = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._load()

    def _load(self):
        """Rehidrata el estado desde `state_path` al arrancar.

        Permite que el dashboard muestre datos al instante aunque todavia no se
        haya completado el primer refresco. Un fichero corrupto solo deja el
        estado en "SIN_DATOS".
        """
        if not self.state_path or not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self._news = list(data.get("news") or [])
                self._calendar_events = list(data.get("calendar_events") or [])
                self._status = str(data.get("status") or "PERSISTIDA")
                self._calendar_status = str(
                    data.get("calendar_status") or self._status
                )
                self._updated_at = data.get("updated_at")
        except (OSError, ValueError, TypeError):
            self._status = "SIN_DATOS"

    def _persist(self):
        """Vuelca el estado actual al JSON compartido (si hay `state_path`).

        Se invoca siempre dentro del lock, desde `refresh()`.
        """
        if not self.state_path:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "news": self._news,
            "calendar_events": self._calendar_events,
            "status": self._status,
            "calendar_status": self._calendar_status,
            "updated_at": self._updated_at,
        }
        self.state_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def refresh(self) -> list[dict]:
        """Descarga noticias y calendario, y actualiza el estado persistido.

        El calendario se descarga en un `try` propio: si falla, se conservan
        los eventos anteriores y solo se degrada `calendar_status`, de modo que
        un problema en la agenda no deja al dashboard sin noticias. Las de
        impacto ALTO se colocan primero y se recortan a 20.

        Returns:
            Copia de la lista de noticias vigente.

        Raises:
            Errores de red del feed RSS: los captura `_run`.
        """
        request = Request(self.feed_url, headers={"User-Agent": "DaemonBlackFx/1.0"})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            news = parse_rss(response.read())
        calendar_events = None
        calendar_status = "ACTUALIZADA"
        try:
            calendar_request = Request(
                self.calendar_url,
                headers={"User-Agent": "DaemonBlackFx/1.0"},
            )
            with urlopen(calendar_request, timeout=self.timeout_seconds) as response:
                calendar_events = parse_economic_calendar(response.read())
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            calendar_status = (
                "NO DISPONIBLE · ÚLTIMO ESTADO "
                f"({type(error).__name__})"
            )
        high_impact = [row for row in news if row["impact"] == "ALTO"]
        ordered = high_impact + [row for row in news if row["impact"] != "ALTO"]
        with self._lock:
            self._news = ordered[:20]
            if calendar_events is not None:
                self._calendar_events = calendar_events
            self._status = "ACTUALIZADA"
            self._calendar_status = calendar_status
            self._updated_at = datetime.now(timezone.utc).isoformat()
            self._persist()
            return list(self._news)

    def _run(self):
        """Bucle del hilo: refresca y espera hasta que se pida parar.

        Usa `Event.wait` en vez de `sleep` para que `stop()` corte la espera de
        inmediato. Absorbe todo error de red manteniendo el ultimo estado.
        """
        while not self._stop.is_set():
            try:
                self.refresh()
            except (HTTPError, URLError, TimeoutError, OSError, ElementTree.ParseError):
                with self._lock:
                    self._status = "NO DISPONIBLE · ÚLTIMO ESTADO"
            self._stop.wait(self.refresh_seconds)

    def start(self):
        """Arranca el hilo de refresco. Idempotente: no duplica el hilo."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="financial-news")
        self._thread.start()

    def stop(self):
        """Senala la parada del hilo; al ser `daemon` no se hace join."""
        self._stop.set()
        self._thread = None

    def snapshot(self) -> dict:
        """Devuelve una copia coherente del estado para la interfaz.

        Copia las listas dentro del lock para que el consumidor nunca vea una
        estructura mutando bajo sus pies.

        Returns:
            dict con `items` (noticias), `calendar`, `status` y `updated_at`.
        """
        with self._lock:
            return {
                "items": list(self._news),
                "calendar": {
                    "events": list(self._calendar_events),
                    "status": self._calendar_status,
                    "source": "Forex Factory calendar",
                    "timezone": "America/Santiago",
                },
                "status": self._status,
                "updated_at": self._updated_at,
                "source_language": "es",
                "source": "Google News RSS",
            }
