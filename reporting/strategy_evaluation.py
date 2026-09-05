"""Informe de diagnostico offline sobre las evaluaciones de simbolo.

Responde a preguntas de calibracion que no se ven operando en vivo:
por que se rechazan las senales, que confirmacion falta mas a menudo, cuanto
tarda cada estrategia en evaluar y si el riesgo solicitado se alcanza de
verdad al dimensionar.

Se ejecuta como script independiente (`python -m reporting.strategy_evaluation`)
y NO forma parte del ciclo de trading: solo lee la bitacora de auditoria.

Vinculaciones:
    - `database.repository.TradingRepository.recent_symbol_evaluation_events`:
      unica fuente de datos.
    - Productor de esos eventos: `strategy.execution.live_trading_engine`.
    - Salida por defecto: `storage/analysis/strategy_evaluation.json`.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean, median

from database.repository import TradingRepository


def _number(value):
    """Convierte a float devolviendo `None` en vez de lanzar.

    Los payloads de auditoria son JSON heterogeneo; un campo puede llegar como
    texto, `None` o ausente. Se descarta en silencio en lugar de romper el
    informe completo.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _distribution(values):
    """Resume una serie en count/min/mediana/media/max.

    Se incluye la mediana junto a la media porque la latencia tiene colas muy
    largas: un unico ciclo lento distorsiona la media pero no la mediana.
    Devuelve la estructura con `None` si no hay valores validos.
    """
    clean = sorted(value for value in (_number(item) for item in values) if value is not None)
    if not clean:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "count": len(clean),
        "min": round(clean[0], 6),
        "median": round(median(clean), 6),
        "mean": round(mean(clean), 6),
        "max": round(clean[-1], 6),
    }


def build_strategy_evaluation(repository, *, source="DEMO", hours=24.0) -> dict:
    """Agrega los eventos de evaluacion de una ventana en un informe unico.

    Args:
        repository: `TradingRepository` desde el que se leen los eventos.
        source: entorno a analizar (DEMO, LIVE, PAPER).
        hours: tamano de la ventana hacia atras.

    Returns:
        dict con recuentos por accion y por estrategia, confirmaciones que mas
        faltan, distribucion de latencia por estrategia, el bloque
        `risk_reachability` (riesgo solicitado frente al realmente aplicado,
        clave para detectar simbolos donde el lote minimo impide respetar el
        riesgo) y el detalle fila a fila en `evaluations`.

    `configuration_guardrails` viaja siempre en `False`: es un recordatorio
    explicito de que este informe describe la configuracion vigente y no
    modifica umbrales de frescura M5 ni puertas estructurales.
    """
    events = repository.recent_symbol_evaluation_events(source=source, hours=hours)
    actions = Counter()
    strategies = Counter()
    strategy_actions = defaultdict(Counter)
    missing = defaultdict(Counter)
    elapsed = defaultdict(list)
    risk_reachability = []
    detail_rows = []

    for event in events:
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        action = str(result.get("action") or event.get("action") or "UNKNOWN")
        strategy = str(result.get("strategy_name") or "SMC").upper()
        actions[action] += 1
        strategies[strategy] += 1
        strategy_actions[strategy][action] += 1
        elapsed_value = _number(payload.get("elapsed_seconds"))
        if elapsed_value is not None:
            elapsed[strategy].append(elapsed_value)
        for key in result.get("missing_confirmations") or []:
            missing[strategy][str(key)] += 1

        risk_metrics = result.get("risk_metrics") if isinstance(result.get("risk_metrics"), dict) else {}
        if risk_metrics or action in {
            "REJECTED_RISK_TARGET_UNREACHABLE",
            "OPERACION_RECHAZADA_POR_RIESGO",
            "REJECTED_MARGIN_EXCEEDED",
        }:
            requested = _number(risk_metrics.get("risk_amount"))
            actual = _number(risk_metrics.get("actual_risk_amount"))
            ratio = actual / requested if requested and actual is not None else None
            risk_reachability.append({
                "event_time": str(event.get("event_time")),
                "instrument": event.get("instrument"),
                "strategy_name": strategy,
                "action": action,
                "reason": result.get("reason") or event.get("reason"),
                "requested_risk_amount": requested,
                "actual_risk_amount": actual,
                "actual_to_requested_ratio": None if ratio is None else round(ratio, 6),
                "metrics": risk_metrics,
            })

        detail_rows.append({
            "event_time": str(event.get("event_time")),
            "instrument": event.get("instrument"),
            "strategy_name": strategy,
            "action": action,
            "reason": result.get("reason") or event.get("reason"),
            "direction": result.get("direction"),
            "valid": bool(result.get("valid", False)),
            "trade_score": result.get("trade_score"),
            "confirmation_percentage": result.get("confirmation_percentage"),
            "missing_confirmations": result.get("missing_confirmations") or [],
            "elapsed_seconds": elapsed_value,
            "signal_age": result.get("signal_age") or {},
            "risk_metrics": risk_metrics,
        })

    total = len(events)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source).upper(),
        "window_hours": float(hours),
        "total_evaluations": total,
        "configuration_guardrails": {
            "m5_freshness_changed": False,
            "structural_gates_changed": False,
            "minimum_risk_threshold_changed": False,
        },
        "actions": dict(actions.most_common()),
        "strategies": dict(strategies.most_common()),
        "strategy_actions": {
            strategy: dict(counter.most_common())
            for strategy, counter in strategy_actions.items()
        },
        "missing_confirmations": {
            strategy: dict(counter.most_common())
            for strategy, counter in missing.items()
        },
        "elapsed_seconds": {
            strategy: _distribution(values)
            for strategy, values in elapsed.items()
        },
        "risk_reachability": {
            "events": len(risk_reachability),
            "rows": risk_reachability,
        },
        "evaluations": detail_rows,
    }


def write_strategy_evaluation(report: dict, output_path) -> Path:
    """Guarda el informe en JSON mediante escritura atomica.

    Escribe primero en un `.tmp` y despues hace `replace`, de modo que un lector
    concurrente nunca vea un JSON a medias. `default=str` evita fallos con tipos
    no serializables como fechas.

    Returns:
        La ruta absoluta del fichero escrito.
    """
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)
    return path


def main():
    """Punto de entrada CLI: `--hours`, `--source` y `--output`.

    Construye el informe, lo escribe y muestra por pantalla un resumen breve
    con la ruta, el total de evaluaciones y el recuento por accion.
    """
    parser = argparse.ArgumentParser(
        description="Resume latencia y alcance de riesgo desde auditoría compacta."
    )
    parser.add_argument("--hours", type=float, default=24.0)
    parser.add_argument("--source", default="DEMO")
    parser.add_argument(
        "--output",
        default="storage/analysis/strategy_evaluation.json",
    )
    args = parser.parse_args()
    repository = TradingRepository()
    report = build_strategy_evaluation(
        repository,
        source=args.source,
        hours=args.hours,
    )
    path = write_strategy_evaluation(report, args.output)
    print(json.dumps({
        "output": str(path),
        "total_evaluations": report["total_evaluations"],
        "actions": report["actions"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
