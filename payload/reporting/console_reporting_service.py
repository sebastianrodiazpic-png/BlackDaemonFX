"""Capa de presentacion en consola del motor de trading.

Traduce los diccionarios crudos que devuelve el motor a texto legible en
espanol, sin volcar JSON completos salvo en modo `debug`. Es puramente de
salida: no consulta la base de datos, no toca el broker y no altera ninguna
decision.

Tres niveles de verbosidad controlados por `ConsoleReportingConfig`:
    - normal: resumen por ciclo y eventos importantes;
    - `verbose`: ademas rechazos y diagnostico de confirmaciones;
    - `debug`: vuelca el diccionario completo de cada resultado.

Vinculaciones:
    - Consumidor: `strategy.execution.live_trading_engine` y `app.main`, que
      le pasan las filas de resultado de cada simbolo.
    - Los diccionarios de etiquetas (`ACTION_LABELS_ES`, `REASON_LABELS_ES`,
      `CONFIRMATION_LABELS_ES`) traducen las claves tecnicas que generan
      `strategy.smc` y el motor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable
import json
import math


@dataclass
class ConsoleReportingConfig:
    """Opciones de verbosidad y ancho de la salida por consola.

    Attributes:
        verbose: imprime tambien rechazos y detalle de confirmaciones.
        debug: vuelca el diccionario completo de cada resultado en JSON.
        show_no_signal: muestra los simbolos sin senal (muy ruidoso).
        show_cycle_summary: imprime el bloque de resumen al cerrar cada ciclo.
        width: ancho en caracteres de las lineas separadoras.
    """

    verbose: bool = False
    debug: bool = False
    show_no_signal: bool = False
    show_cycle_summary: bool = True
    width: int = 88


class ConsoleReportingService:
    """Presenta resultados del motor de trading sin volcar diccionarios completos.

    Los diagnósticos completos siguen viajando en los resultados del motor y solo se
    muestran cuando ``debug=True``. En ``verbose=True`` se imprimen rechazos y señales
    relevantes; en modo normal se muestra un resumen por ciclo y los eventos importantes.
    """

    IMPORTANT_ACTIONS = {
        "ORDER_OPENED",
        "EXECUTION_REJECTED",
        "DRY_RUN_VALIDATED",
        "REJECTED_ORDER_CHECK",
        "REJECTED_INVALID_MARKET_STOP",
        "REJECTED_RISK_EXCEEDED",
        "MARKET_INVALIDATED_SIGNAL",
        "ENTRY_PRICE_DRIFT_TOO_LARGE",
        "RR_TOO_LOW",
        "NO_H4_CONTEXT",
        "HTF_TREND_DIVERGENCE",
        "DIRECTION_POLICY_BLOCKED",
        "POSITION_ALREADY_OPEN_FOR_SYMBOL",
        "MAX_TOTAL_OPEN_POSITIONS",
        "ALREADY_EXECUTED",
        "INVALID_DIRECTION",
        "INVALID_RISK_BASE",
        "INVALID_RISK_CONFIGURATION",
        "ERROR",
    }

    REASON_LABELS_ES = {
        "BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK": "el volumen máximo del broker no permite alcanzar el riesgo objetivo",
        "POST_FILL_RISK_HARD_CAP_BREACH": "el riesgo real después de ejecutar la orden superó el límite máximo",
        "RISK_INCIDENT_TEMPORARY_COOLDOWN": "cuarentena temporal por desviación marginal de ejecución",
        "RISK_INCIDENT_REQUIRES_MANUAL_REVIEW": "cuarentena de seguridad que requiere revisión manual",
        "INSUFFICIENT_TRADE_SCORE": "calidad de la operación insuficiente",
        "CRITICAL_CONFIRMATION_MISSING": "falta una confirmación estructural crítica",
        "CONFIRMATION_PERCENTAGE_BELOW_THRESHOLD": "porcentaje de confirmaciones inferior al 80%",
        "VIABLE_TRADE_SCORE_BELOW_THRESHOLD": "calidad inferior al mínimo viable",
        "REJECTION_NOT_CONFIRMED": "rechazo del precio no confirmado",
        "DISPLACEMENT_NOT_CONFIRMED": "desplazamiento no confirmado",
        "MICRO_STRUCTURE_NOT_CONFIRMED": "microestructura M5 no confirmada",
        "STRONG_CLOSE_NOT_CONFIRMED": "cierre fuerte no confirmado",
        "HARMONIC_PATTERN_NOT_CONFIRMED": "patrón armónico no confirmado",
        "ORDER_BLOCK_NOT_FRESH": "Order Block no está fresco",
        "CONFIRMATION_MODE_NOT_SATISFIED": "modo de confirmación no satisfecho",
    }

    @classmethod
    def _reason_label(cls, key: str) -> str:
        """Traduce un codigo de motivo al espanol.

        Si la clave no esta en `REASON_LABELS_ES` devuelve el propio codigo con
        los guiones bajos sustituidos, de modo que un motivo nuevo se muestra
        legible sin necesidad de tocar este fichero.
        """
        return cls.REASON_LABELS_ES.get(str(key), str(key).replace("_", " ").lower())

    def __init__(self, config: ConsoleReportingConfig | None = None):
        """Guarda la configuracion; sin argumento usa el perfil silencioso."""
        self.config = config or ConsoleReportingConfig()

    def _line(self, char: str = "-") -> str:
        """Linea separadora del ancho configurado."""
        return char * self.config.width

    @staticmethod
    def _fmt(value: Any, digits: int = 3) -> str:
        """Formatea un valor para consola.

        `None` se muestra como `-`, los flotantes con los decimales pedidos y
        los no finitos (nan/inf) en crudo para que la anomalia sea visible en
        vez de quedar disimulada como `0.000`.
        """
        if value is None:
            return "-"
        if isinstance(value, float):
            if not math.isfinite(value):
                return str(value)
            return f"{value:.{digits}f}"
        return str(value)

    ACTION_LABELS_ES = {
        "ORDER_OPENED": "ORDEN ABIERTA",
        "SPLIT_ORDER_OPENED": "OPERACIÓN ABIERTA EN DOS ENTRADAS",
        "DRY_RUN_VALIDATED": "OPERACIÓN VALIDADA (SIMULACIÓN)",
        "NO_SIGNAL": "SIN SEÑAL",
        "OPERACION_RECHAZADA_POR_RIESGO": "OPERACIÓN RECHAZADA POR RIESGO",
        "REJECTED_RISK_EXCEEDED": "RIESGO SUPERIOR AL PERMITIDO",
        "REJECTED_RISK_TARGET_UNREACHABLE": "EL BROKER NO PERMITE ALCANZAR EL RIESGO OBJETIVO",
        "REJECTED_TOTAL_SPLIT_RISK_EXCEEDED": "RIESGO TOTAL DIVIDIDO SUPERIOR AL PERMITIDO",
        "EMERGENCY_RISK_EXIT": "CIERRE DE EMERGENCIA POR RIESGO",
        "SYMBOL_QUARANTINED": "INSTRUMENTO EN CUARENTENA DE RIESGO",
        "ENTRY_PRICE_DRIFT_TOO_LARGE": "PRECIO DEMASIADO ALEJADO DE LA ENTRADA",
        "REJECTED_ORDER_CHECK": "ORDEN RECHAZADA EN VALIDACIÓN MT5",
        "REJECTED_INVALID_MARKET_STOP": "STOP LOSS NO VÁLIDO PARA EL MERCADO",
        "RR_TOO_LOW": "RELACIÓN RIESGO/BENEFICIO INSUFICIENTE",
        "DIRECTION_POLICY_BLOCKED": "DIRECCIÓN BLOQUEADA POR POLÍTICA DEL INSTRUMENTO",
        "NO_H4_CONTEXT": "ESPERANDO TENDENCIA VÁLIDA EN H4",
        "HTF_TREND_DIVERGENCE": "H4 Y H1 NO CONVERGEN",
        "POSITION_ALREADY_OPEN_FOR_SYMBOL": "YA EXISTE UNA POSICIÓN ABIERTA EN EL INSTRUMENTO",
        "MAX_TOTAL_OPEN_POSITIONS": "MÁXIMO DE POSICIONES ABIERTAS ALCANZADO",
        "ERROR": "ERROR",
    }

    CONFIRMATION_LABELS_ES = {
        "h1_trend": "tendencia H1",
        "m15_setup": "configuración SMC M15",
        "liquidity_sweep": "barrido de liquidez",
        "m15_structure": "estructura CHOCH/BOS M15",
        "premium_discount": "zona Premium/Discount",
        "fresh_order_block": "Order Block fresco",
        "clean_retest": "retest limpio",
        "rejection": "rechazo del precio",
        "displacement": "desplazamiento",
        "micro_structure": "microestructura M5",
        "momentum": "momentum",
        "strong_close": "cierre fuerte",
        "directional_candle": "vela en dirección de la entrada",
        "confirmation_mode_ok": "modo de confirmación",
        "harmonic_confirmation": "patrón armónico",
        "divergence_confirmation": "divergencia confirmada",
        "h1_extreme_doji_confirmation": "Doji H1 en extremo",
    }

    @classmethod
    def _label(cls, action: str | None) -> str:
        """Traduce un codigo de accion del motor a su etiqueta en espanol."""
        key = str(action or "UNKNOWN")
        return cls.ACTION_LABELS_ES.get(key, key.replace("_", " "))

    @classmethod
    def _confirmation_label(cls, key: str) -> str:
        """Traduce el nombre tecnico de una confirmacion SMC a espanol."""
        return cls.CONFIRMATION_LABELS_ES.get(str(key), str(key).replace("_", " "))

    def print_startup(self, *, account: dict, execute: bool, symbols: Iterable[str], interval: int,
                      risk_percent: float, min_rr: float, report_path: Any) -> None:
        """Cabecera de arranque: cuenta, modo, riesgo y pipeline.

        Deja explicito si se opera de verdad o en DRY RUN, dato critico para no
        confundir una sesion simulada con una real. La lista completa de
        instrumentos solo se imprime en modo `verbose`.
        """
        symbols = list(symbols)
        print(self._line("="))
        print("BOT SMC MT5 - DERIV DEMO")
        print(self._line("="))
        print(f"Cuenta: {account.get('login', '-') } | Servidor: {account.get('server', '-')}")
        print(f"Balance: {self._fmt(account.get('balance'), 2)} {account.get('currency', '')}")
        print(f"Modo: {'EJECUCIÓN DEMO' if execute else 'DRY RUN - no se enviarán órdenes'}")
        print(f"Riesgo por trade: {self._fmt(risk_percent, 2)}% | R:R mínimo: {self._fmt(min_rr, 2)}")
        print(f"Intervalo: {interval}s | Símbolos: {len(symbols)}")
        if self.config.verbose:
            print("Instrumentos:")
            for index, symbol in enumerate(symbols, start=1):
                print(f"  {index:02d}. {symbol}")
        print(f"Reporte XLSX: {report_path}")
        print("Pipeline: SMC -> TradeLifecycleManager -> MT5TradeExecutor -> SQLite -> XLSX")
        print(self._line("="))

    def print_daemon_started(
        self,
        interval: int,
        symbols_count: int,
        position_monitor_interval: int | None = None,
    ) -> None:
        """Confirma que el daemon arranco e informa de sus dos cadencias.

        El intervalo de senales y el del monitor de posiciones/break-even son
        independientes: el monitor corre mucho mas a menudo porque vigila
        posiciones ya abiertas.
        """
        monitor = "-" if position_monitor_interval is None else f"{position_monitor_interval}s"
        print(
            f"Daemon activo: señales={interval}s | monitor posiciones/BE={monitor} | "
            f"símbolos={symbols_count}"
        )
        print("Progreso: se mostrará cada símbolo y su tiempo de análisis.")

    def print_cycle_start(
        self,
        cycle_number: int,
        started_at: datetime | None = None,
        total_symbols: int | None = None,
    ) -> None:
        """Abre un ciclo con su numero correlativo y la marca temporal UTC.

        La hora se imprime siempre en UTC para poder cruzar el log con la
        auditoria de la base de datos, que tambien es UTC.
        """
        started_at = started_at or datetime.now(timezone.utc)
        print()
        print(self._line("="))
        total = "" if total_symbols is None else f" | símbolos={total_symbols}"
        print(f"CICLO #{cycle_number:04d} | {started_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}{total}")
        print(self._line("="))

    def print_symbol_start(self, *, index: int, total: int, symbol: str) -> None:
        """Marca START de un simbolo, con `flush` para ver el avance en vivo.

        Emparejado con `print_symbol_result`, permite detectar que simbolo dejo
        colgado un ciclo si el proceso se bloquea.
        """
        print(f"[{index:02d}/{total:02d}] START {symbol}", flush=True)

    def print_symbol_result(
        self,
        *,
        row: dict,
        index: int,
        total: int,
        elapsed_seconds: float,
    ) -> None:
        """Marca END de un simbolo con su duracion y accion resultante.

        Amplia con motivo, campos de la operacion y diagnostico de
        confirmaciones salvo que la accion sea `NO_SIGNAL` y no se pidio modo
        verbose: ese caso es el 90% del volumen y saturaria la consola.
        """
        action = self._label(str(row.get("action") or "UNKNOWN"))
        symbol = row.get("symbol", "-")
        print(
            f"[{index:02d}/{total:02d}] END   {symbol} | {elapsed_seconds:.2f}s | {action}",
            flush=True,
        )
        if self.config.verbose or str(row.get("action") or "") not in {"NO_SIGNAL"}:
            reason = self._reason(row)
            if reason and reason != action:
                print(f"    Motivo: {reason}", flush=True)
            if str(row.get("action") or "") in {"ORDER_OPENED", "SPLIT_ORDER_OPENED", "DRY_RUN_VALIDATED"}:
                self._print_trade_fields(row)
            self._print_confirmation_diag(row)


    @staticmethod
    def _extract_confirmation_diag(row: dict) -> dict | None:
        """Localiza el diagnostico de confirmaciones en dos ubicaciones.

        1. `analysis.signal` / `analysis.entry`: la senal que si se genero.
        2. `analysis.diagnostics.m5.latest_rejected_candidate`: el mejor
           candidato descartado, util para entender POR QUE no hubo senal.

        Returns:
            dict normalizado con porcentaje, calidad, decision, faltantes,
            fallos criticos y divergencias; `None` si no hay nada que mostrar.
        """
        analysis = row.get("analysis") or {}
        signal = analysis.get("signal") or analysis.get("entry") or {}
        if signal and signal.get("confirmation_percentage") is not None:
            return {
                "percentage": signal.get("confirmation_percentage"),
                "score": signal.get("trade_score"),
                "decision": signal.get("confirmation_decision"),
                "passed": signal.get("confirmations_passed"),
                "total": signal.get("confirmations_total"),
                "missing": signal.get("missing_confirmations", []),
                "critical_ok": signal.get("critical_confirmations_ok"),
                "critical_failures": signal.get("critical_confirmation_failures", []),
                "reasons": signal.get("rejection_reasons", []),
                "divergence": signal.get("divergence_confirmation"),
                "divergence_type": signal.get("divergence_type"),
                "h1_doji": signal.get("h1_doji_confirmation"),
                "h1_doji_type": signal.get("h1_doji_type"),
                "h1_doji_zone": signal.get("h1_doji_zone"),
            }
        diagnostics = analysis.get("diagnostics") or {}
        m5 = diagnostics.get("m5") or {}
        candidate = m5.get("latest_rejected_candidate") or {}
        if candidate:
            return {
                "percentage": candidate.get("confirmation_percentage"),
                "score": candidate.get("trade_score"),
                "decision": candidate.get("confirmation_decision", "REJECTED"),
                "passed": candidate.get("confirmations_passed"),
                "total": candidate.get("confirmations_total"),
                "missing": candidate.get("missing_confirmations", []),
                "critical_ok": candidate.get("critical_confirmations_ok"),
                "critical_failures": candidate.get("critical_confirmation_failures", []),
                "reasons": candidate.get("rejection_reasons", []),
                "divergence": candidate.get("divergence_confirmation"),
                "divergence_type": candidate.get("divergence_type"),
            }
        return None

    def _print_confirmation_diag(self, row: dict) -> None:
        """Imprime el bloque de confirmaciones ya traducido al espanol.

        Muestra el recuento aprobadas/totales, el porcentaje, la calidad y la
        decision (estricta o adaptativa >=75/80%), y solo anade las lineas de
        faltantes, criticas, divergencia, doji H1 y rechazo tecnico cuando
        realmente contienen algo.
        """
        diag = self._extract_confirmation_diag(row)
        if not diag:
            return
        pct = diag.get("percentage")
        score = diag.get("score")
        decision = diag.get("decision") or "-"
        passed = diag.get("passed")
        total = diag.get("total")
        pct_text = "-" if pct is None else f"{float(pct):.1f}%"
        count_text = "-" if passed is None or total is None else f"{passed}/{total}"
        decision_es = {
            "STRICT_CONFIRMED": "CONFIRMADA ESTRICTAMENTE",
            "ADAPTIVE_75_CONFIRMED": "CONFIRMADA POR REGLA ADAPTATIVA >=75%",
            "ADAPTIVE_80_CONFIRMED": "CONFIRMADA POR REGLA ADAPTATIVA >=80%",
            "REJECTED": "RECHAZADA",
        }.get(str(decision), str(decision))
        print(f"    Confirmaciones: {count_text} | {pct_text} | calidad={self._fmt(score, 2)} | decisión={decision_es}")
        missing = diag.get("missing") or []
        if missing:
            print(f"    Faltantes: {', '.join(self._confirmation_label(x) for x in missing)}")
        critical_failures = diag.get("critical_failures") or []
        if critical_failures:
            print(f"    Críticas faltantes: {', '.join(self._confirmation_label(x) for x in critical_failures)}")
        if diag.get("divergence"):
            print(f"    Divergencia: CONFIRMADA | {diag.get('divergence_type') or 'precio/RSI'}")
        if diag.get("h1_doji"):
            print(f"    Doji H1 extremo: CONFIRMADO | {diag.get('h1_doji_type') or 'DOJI'} | zona={diag.get('h1_doji_zone') or '-'}")
        reasons = diag.get("reasons") or []
        if reasons:
            print(f"    Rechazo técnico: {', '.join(self._reason_label(x) for x in reasons)}")

    def print_position_monitor(
        self,
        *,
        checked: int,
        activated: int,
        errors: list,
        sync: int,
        elapsed_seconds: float,
        phase: str,
        runner_updates: list | None = None,
    ) -> None:
        """Resumen de una pasada del monitor de posiciones abiertas.

        Guarda silencio absoluto si no hubo nada que reportar (ni posiciones,
        ni break-even, ni cierres, ni eventos de runner): el monitor corre cada
        pocos segundos y de otro modo inundaria la consola.

        Detalla cada evento del runner distinguiendo cierre para proteger
        ganancia, extension con SL asegurado y error.
        """
        runner_updates = list(runner_updates or [])
        # No inundar la consola cuando no hay posiciones ni eventos relevantes.
        if checked or activated or errors or sync or runner_updates:
            print(
                f"[MONITOR {phase}] posiciones={checked} | BE activados={activated} | "
                f"runner eventos={len(runner_updates)} | cierres={int(sync or 0)} | "
                f"{elapsed_seconds:.2f}s",
                flush=True,
            )
            for event in runner_updates:
                stage = event.get("stage") or "RUNNER"
                if event.get("closed"):
                    print(
                        f"    RUNNER {event.get('symbol','-')}: {stage} · "
                        f"cerrado para proteger ganancia · {event.get('decision','')}",
                        flush=True,
                    )
                elif event.get("extended"):
                    print(
                        f"    RUNNER {event.get('symbol','-')}: {stage} · "
                        f"SL protegido en +{event.get('profit_lock_rr')}R · "
                        f"objetivo máximo {event.get('target_rr')}R",
                        flush=True,
                    )
                elif event.get("error"):
                    print(
                        f"    RUNNER {event.get('symbol','-')}: {stage} · "
                        f"{event.get('error')}",
                        flush=True,
                    )
            if errors:
                print(f"    Errores monitor: {errors}", flush=True)

    def _reason(self, row: dict) -> str:
        """Motivo legible de la fila: `reason`, `error` o, si no, la accion."""
        reason = row.get("reason") or row.get("error")
        if reason:
            return self.REASON_LABELS_ES.get(str(reason), str(reason))
        action = str(row.get("action") or "")
        return self._label(action)

    def _print_trade_fields(self, row: dict) -> None:
        """Imprime los campos del plan que esten presentes.

        Cada linea se omite si el campo falta, para no mostrar filas de guiones.
        Distingue "Riesgo objetivo" (el solicitado) de "Riesgo calculado" (el
        que resulta tras normalizar el lote): su diferencia revela simbolos
        donde el lote minimo impide respetar el riesgo configurado.
        """
        if row.get("direction"):
            print(f"    Dirección: {row.get('direction')}")
        if row.get("entry_price") is not None:
            print(f"    Entrada: {self._fmt(row.get('entry_price'))}")
        if row.get("stop_loss") is not None:
            print(f"    Stop Loss: {self._fmt(row.get('stop_loss'))}")
        if row.get("take_profit") is not None:
            print(f"    Take Profit: {self._fmt(row.get('take_profit'))}")
        rr = row.get("planned_rr", row.get("risk_reward_ratio"))
        if rr is not None:
            print(f"    R:R: {self._fmt(rr, 2)}")
        if row.get("volume") is not None:
            print(f"    Volumen: {self._fmt(row.get('volume'), 2)}")
        if row.get("execution_mode_es"):
            print(f"    Modalidad de ejecución: {row.get('execution_mode_es')}")
        if row.get("risk_amount") is not None:
            print(f"    Riesgo objetivo: {self._fmt(row.get('risk_amount'), 2)}")
        if row.get("actual_risk_amount") is not None:
            print(f"    Riesgo calculado: {self._fmt(row.get('actual_risk_amount'), 2)}")

    def print_result(self, row: dict, index: int | None = None, total: int | None = None) -> None:
        """Ficha detallada de un resultado (formato de bloque, no de linea).

        Se salta por completo las filas `NO_SIGNAL` salvo que `verbose` o
        `show_no_signal` esten activos. Para ordenes abiertas anade ticket e
        id de ejecucion; para el resto, el motivo y, en verbose, la edad de la
        senal. Si `debug` esta activo termina volcando el diccionario integro.
        """
        action = str(row.get("action") or "UNKNOWN")
        symbol = row.get("symbol", "-")
        prefix = ""
        if index is not None and total is not None:
            prefix = f"[{index:02d}/{total:02d}] "

        if action == "NO_SIGNAL" and not (self.config.verbose or self.config.show_no_signal):
            return

        if action == "NO_SIGNAL":
            print(f"{prefix}{symbol}")
            print(f"    Estado: SIN SEÑAL | Motivo: {self._reason(row)}")
            return

        print(f"{prefix}{symbol}")
        print(f"    Estado: {self._label(action)}")

        if action in {"ORDER_OPENED", "SPLIT_ORDER_OPENED", "DRY_RUN_VALIDATED"}:
            self._print_trade_fields(row)
            if action in {"ORDER_OPENED", "SPLIT_ORDER_OPENED"}:
                print(f"    Position ticket: {row.get('position_ticket', '-')}")
                print(f"    Execution ID: {row.get('execution_id', '-')}")
                print("    Resultado: ORDEN ABIERTA")
            else:
                print("    Resultado: VALIDADA, NO ENVIADA (DRY RUN)")
        else:
            if row.get("direction"):
                print(f"    Dirección: {row.get('direction')}")
            print(f"    Motivo: {self._reason(row)}")
            if self.config.verbose:
                self._print_trade_fields(row)
                market = row.get("market_signal_diagnostics") or {}
                if market.get("signal_age_candles") is not None:
                    print(f"    Edad señal: {market.get('signal_age_candles')} velas")

        self._print_confirmation_diag(row)

        if self.config.debug:
            self.print_debug(row)

    def print_debug(self, row: dict) -> None:
        """Vuelca la fila completa en JSON indentado (`default=str`)."""
        print("    DEBUG:")
        print(json.dumps(row, default=str, ensure_ascii=False, indent=2))

    def summarize(self, results: list[dict], sync: int = 0, cycle_number: int | None = None,
                  elapsed_seconds: float | None = None, interval: int | None = None,
                  next_delay_seconds: float | None = None,
                  overrun_seconds: float | None = None) -> None:
        """Bloque de cierre del ciclo con el reparto por categorias.

        Clasifica cada accion en: sin senal, rechazadas, bloqueadas por estado
        o limites, validadas en DRY RUN, ordenes nuevas y errores. La categoria
        `waiting` ("Esperando/otros") se calcula por resta, de modo que ninguna
        accion desconocida desaparezca del recuento.

        Avisa explicitamente cuando el ciclo excedio su intervalo objetivo
        (`overrun_seconds`), sintoma de que el bot va por detras del mercado.
        """
        if not self.config.show_cycle_summary:
            return
        actions = [str(row.get("action") or "UNKNOWN") for row in results]
        no_signal = sum(action == "NO_SIGNAL" for action in actions)
        errors = sum(action == "ERROR" for action in actions)
        opened = sum(action in {"ORDER_OPENED", "SPLIT_ORDER_OPENED"} for action in actions)
        validated = sum(action == "DRY_RUN_VALIDATED" for action in actions)
        rejected = sum(
            action.startswith("REJECTED")
            or action in {"RR_TOO_LOW", "DIRECTION_POLICY_BLOCKED", "MARKET_INVALIDATED_SIGNAL", "ENTRY_PRICE_DRIFT_TOO_LARGE", "EXECUTION_REJECTED", "OPERACION_RECHAZADA_POR_RIESGO"}
            for action in actions
        )
        blocked = sum(action in {"ALREADY_EXECUTED", "POSITION_ALREADY_OPEN_FOR_SYMBOL", "MAX_TOTAL_OPEN_POSITIONS"} for action in actions)
        waiting = len(results) - no_signal - errors - opened - validated - rejected - blocked

        print(self._line("-"))
        title = "RESUMEN DEL CICLO" if cycle_number is None else f"RESUMEN DEL CICLO #{cycle_number:04d}"
        print(title)
        print(f"Símbolos analizados: {len(results)}")
        print(f"Sin señal: {no_signal}")
        print(f"Esperando/otros: {waiting}")
        print(f"Señales rechazadas: {rejected}")
        print(f"Bloqueadas por estado/límites: {blocked}")
        print(f"Validadas DRY RUN: {validated}")
        print(f"Nuevas órdenes: {opened}")
        print(f"Operaciones cerradas sincronizadas: {int(sync or 0)}")
        print(f"Errores: {errors}")
        if elapsed_seconds is not None:
            print(f"Duración del ciclo: {elapsed_seconds:.2f}s")
        if interval is not None:
            print(f"Intervalo objetivo: {interval}s")
        if next_delay_seconds is not None:
            print(f"Próximo ciclo en: {next_delay_seconds:.2f}s")
        if overrun_seconds is not None and overrun_seconds > 0:
            print(f"[AVISO] Ciclo excedio el intervalo por: {overrun_seconds:.2f}s")
        print(self._line("-"))

    def print_cycle_error(self, exc: Exception, cycle_started: datetime | None = None) -> None:
        """Enmarca un fallo de ciclo con lineas de admiracion muy visibles.

        Solo informa: el daemon decide por su cuenta si continua o se detiene.
        """
        print(self._line("!"))
        print("ERROR EN EL CICLO DEL DEMONIO")
        print(f"Error: {exc}")
        if cycle_started is not None:
            print(f"Inicio del ciclo: {cycle_started.isoformat()}")
        print(self._line("!"))
