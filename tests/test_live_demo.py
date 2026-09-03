from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from brokers.symbol_discovery import DerivSymbolDiscovery
from database.repository import TradingRepository
from strategy.execution.live_trading_engine import (
    LiveTradingConfig,
    LiveTradingEngine,
)


# ============================================================
# UTILIDADES GENERALES
# ============================================================

def print_mapping(title, data, indent="  "):
    """
    Imprime cualquier diccionario de diagnóstico sin depender de
    nombres exactos de campos.

    Esto permite visualizar nuevos diagnósticos agregados por el motor
    sin tener que modificar nuevamente este archivo.
    """
    if not data:
        return

    print(f"{indent}{title}:")

    for key, value in data.items():

        if isinstance(value, dict):

            print_mapping(
                key,
                value,
                indent + "  ",
            )

        elif isinstance(value, list):

            print(f"{indent}  {key}:")

            if not value:
                print(f"{indent}    []")

            else:

                for index, item in enumerate(value):

                    if isinstance(item, dict):

                        print(f"{indent}    [{index}]")

                        for sub_key, sub_value in item.items():
                            print(
                                f"{indent}      "
                                f"{sub_key}: {sub_value}"
                            )

                    else:

                        print(
                            f"{indent}    - {item}"
                        )

        else:

            print(
                f"{indent}  {key}: {value}"
            )


# ============================================================
# OBTENER ANALISIS Y DIAGNOSTICOS
# ============================================================

def get_analysis(result):
    """
    Devuelve el bloque analysis cuando existe.

    En resultados rechazados durante el análisis, algunos motores
    devuelven diagnostics directamente.

    En resultados que ya llegaron a validación de ejecución,
    como DRY_RUN_VALIDATED, los diagnósticos normalmente están dentro
    de result["analysis"]["diagnostics"].
    """
    return result.get("analysis") or {}


def get_diagnostics(result):
    """
    Busca diagnostics en ambos formatos posibles:

    1. result["diagnostics"]
    2. result["analysis"]["diagnostics"]
    """

    diagnostics = result.get("diagnostics")

    if diagnostics:
        return diagnostics

    analysis = get_analysis(result)

    diagnostics = analysis.get("diagnostics")

    if diagnostics:
        return diagnostics

    return {}


# ============================================================
# TRANSICION VISUAL DE ESTADOS
# ============================================================

def print_transition(stage, status, detail=None):
    """
    Imprime una transición uniforme.

    Ejemplo:

      [PASS] H1_CONTEXT
             trend=UPTREND
    """

    print(
        f"    [{status}] {stage}"
    )

    if detail:
        print(
            f"           {detail}"
        )


def print_transition_trace(result):
    """
    Reconstruye visualmente el flujo completo:

        START
          ->
        H1_CONTEXT
          ->
        DIRECTION_POLICY
          ->
        M15_SETUP
          ->
        M5_CONFIRMATION
          ->
        SEQUENCE_VALID
          ->
        SIGNAL_FRESH
          ->
        READY_TO_ENTER
          ->
        MARKET_STOP
          ->
        RISK
          ->
        ORDER_CHECK
          ->
        DRY_RUN_VALIDATED / ORDER_OPENED

    READY_TO_ENTER representa que la estrategia SMC ya aprobó
    H1 -> M15 -> M5 y la señal está lista para entrar al pipeline
    de ejecución.

    No significa necesariamente que la orden haya sido enviada.
    """

    diagnostics = get_diagnostics(result)
    analysis = get_analysis(result)

    action = result.get("action", "UNKNOWN")
    reason = result.get("reason")
    error = result.get("error")

    failed_stage = diagnostics.get("failed_stage")
    sequence_status = diagnostics.get("sequence_status")

    sequence = diagnostics.get("sequence") or {}
    signal_age = diagnostics.get("signal_age") or {}
    direction_policy = (
        diagnostics.get("direction_policy")
        or analysis.get("direction_policy")
        or {}
    )

    h1_info = diagnostics.get("h1") or {}
    m15_info = diagnostics.get("m15") or {}
    m5_info = diagnostics.get("m5") or {}

    analysis_valid = bool(analysis.get("valid", False))

    # Acciones que ocurren DESPUES de que la estrategia SMC
    # ya encontró una señal válida.
    post_analysis_actions = {
        "RR_TOO_LOW",
        "ALREADY_EXECUTED",
        "MAX_TOTAL_OPEN_POSITIONS",
        "POSITION_ALREADY_OPEN_FOR_SYMBOL",
        "REJECTED_INVALID_MARKET_STOP",
        "INVALID_RISK_BASE",
        "INVALID_RISK_CONFIGURATION",
        "REJECTED_RISK_EXCEEDED",
        "REJECTED_ORDER_CHECK",
        "DRY_RUN",
        "DRY_RUN_VALIDATED",
        "ORDER_OPENED",
    }

    smc_ready = (
        analysis_valid
        or action in post_analysis_actions
    )

    print("\n  TRANSITION TRACE")
    print("  " + "-" * 70)

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    print_transition(
        "START",
        "PASS",
        f"symbol={result.get('symbol')}",
    )

    # --------------------------------------------------------
    # H1 CONTEXT
    # --------------------------------------------------------

    h1_setups = h1_info.get("setups")
    h1_confirmations = h1_info.get("confirmations")

    if failed_stage == "H1":

        print_transition(
            "H1_CONTEXT",
            "BLOCKED",
            reason or "H1 context rejected",
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "No se continúa hacia M15/M5",
        )

        return

    print_transition(
        "H1_CONTEXT",
        "PASS",
        (
            f"candles={h1_info.get('candles')} | "
            f"setups={h1_setups} | "
            f"confirmations={h1_confirmations}"
        ),
    )

    # --------------------------------------------------------
    # DIRECTION POLICY
    # --------------------------------------------------------

    if failed_stage == "DIRECTION_POLICY":

        print_transition(
            "DIRECTION_POLICY",
            "BLOCKED",
            reason or "Direction policy rejected",
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "La dirección H1 no cumple la política del símbolo",
        )

        return

    allowed_direction = direction_policy.get(
        "allowed_direction"
    )

    policy_reason = direction_policy.get(
        "reason"
    )

    print_transition(
        "DIRECTION_POLICY",
        "PASS",
        (
            f"allowed_direction={allowed_direction} | "
            f"reason={policy_reason}"
        ),
    )

    # --------------------------------------------------------
    # M15 SETUP
    # --------------------------------------------------------

    if failed_stage == "M15":

        print_transition(
            "M15_SETUP",
            "BLOCKED",
            reason or "No directional M15 setup",
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "Esperando nuevo setup direccional en M15",
        )

        return

    m15_total = sequence.get(
        "m15_setups_total",
        m15_info.get("setups"),
    )

    selected_setup_time = sequence.get(
        "selected_setup_time"
    )

    if m15_total is None:
        m15_status = "WAITING"
    elif int(m15_total) <= 0:
        m15_status = "WAITING"
    else:
        m15_status = "PASS"

    print_transition(
        "M15_SETUP",
        m15_status,
        (
            f"setups_total={m15_total} | "
            f"selected_setup_time={selected_setup_time}"
        ),
    )

    if m15_status != "PASS":

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "Esperando setup válido en M15",
        )

        return

    # --------------------------------------------------------
    # M5 CONFIRMATION
    # --------------------------------------------------------

    m5_total = sequence.get(
        "m5_confirmations_total",
        m5_info.get("confirmations"),
    )

    selected_confirmation_time = sequence.get(
        "selected_confirmation_time"
    )

    eligible_confirmations = sequence.get(
        "eligible_confirmations"
    )

    if action == "NO_M5_CONFIRMATION":

        print_transition(
            "M5_CONFIRMATION",
            "WAITING",
            reason or "No directional M5 confirmation",
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "Esperando confirmación M5",
        )

        return

    if action == "WAITING_M5_AFTER_M15":

        print_transition(
            "M5_CONFIRMATION",
            "FOUND_BUT_NOT_ELIGIBLE",
            (
                f"total={m5_total} | "
                f"eligible_after_latest_m15="
                f"{eligible_confirmations}"
            ),
        )

        print_transition(
            "SEQUENCE_VALID",
            "WAITING",
            reason or sequence_status,
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "Las confirmaciones M5 existentes preceden "
            "al último setup M15",
        )

        return

    if m5_total is None:

        print_transition(
            "M5_CONFIRMATION",
            "UNKNOWN",
            "No diagnostics available",
        )

    elif int(m5_total) <= 0:

        print_transition(
            "M5_CONFIRMATION",
            "WAITING",
            "No confirmations found",
        )

    else:

        print_transition(
            "M5_CONFIRMATION",
            "PASS",
            (
                f"confirmations_total={m5_total} | "
                f"selected_confirmation_time="
                f"{selected_confirmation_time} | "
                f"eligible={eligible_confirmations}"
            ),
        )

    # --------------------------------------------------------
    # SEQUENCE VALID
    # --------------------------------------------------------

    if sequence_status == "VALID_SEQUENCE":

        print_transition(
            "SEQUENCE_VALID",
            "PASS",
            (
                f"M15 setup -> M5 confirmation | "
                f"status={sequence_status}"
            ),
        )

    elif sequence_status == "STALE_M5_CONFIRMATIONS":

        print_transition(
            "SEQUENCE_VALID",
            "WAITING",
            (
                "M5 confirmations exist but do not occur "
                "after latest M15 setup"
            ),
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "Esperando nueva confirmación M5 posterior al setup M15",
        )

        return

    else:

        print_transition(
            "SEQUENCE_VALID",
            "UNKNOWN",
            f"status={sequence_status}",
        )

    # --------------------------------------------------------
    # SIGNAL FRESHNESS
    # --------------------------------------------------------

    if action == "STALE_M5_SIGNAL":

        print_transition(
            "SIGNAL_FRESH",
            "STALE",
            (
                f"age_candles={signal_age.get('age_candles')} | "
                f"age_minutes={signal_age.get('age_minutes')} | "
                f"reason={signal_age.get('reason')}"
            ),
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "La señal M5 ya es demasiado antigua para LIVE ENTRY",
        )

        return

    if signal_age:

        if signal_age.get("valid"):

            print_transition(
                "SIGNAL_FRESH",
                "PASS",
                (
                    f"age_candles={signal_age.get('age_candles')} | "
                    f"age_minutes={signal_age.get('age_minutes')} | "
                    f"max_age_candles="
                    f"{signal_age.get('max_age_candles')}"
                ),
            )

        elif signal_age.get("is_stale"):

            print_transition(
                "SIGNAL_FRESH",
                "STALE",
                (
                    f"age_candles={signal_age.get('age_candles')} | "
                    f"age_minutes={signal_age.get('age_minutes')}"
                ),
            )

        else:

            print_transition(
                "SIGNAL_FRESH",
                "WAITING",
                signal_age.get("reason"),
            )

    else:

        print_transition(
            "SIGNAL_FRESH",
            "UNKNOWN",
            "No signal age diagnostics",
        )

    # --------------------------------------------------------
    # READY TO ENTER
    # --------------------------------------------------------

    if smc_ready:

        direction = (
            result.get("direction")
            or analysis.get("direction")
        )

        entry_time = (
            analysis.get("entry_time")
            or selected_confirmation_time
        )

        print_transition(
            "READY_TO_ENTER",
            "PASS",
            (
                f"direction={direction} | "
                f"entry_time={entry_time}"
            ),
        )

    else:

        print_transition(
            "READY_TO_ENTER",
            "WAITING",
            (
                f"action={action} | "
                f"reason={reason}"
            ),
        )

        return

    # --------------------------------------------------------
    # MARKET STOP
    # --------------------------------------------------------

    if action == "REJECTED_INVALID_MARKET_STOP":

        print_transition(
            "MARKET_STOP",
            "REJECTED",
            reason or "Invalid market stop",
        )

        print_transition(
            "FLOW_STOPPED",
            "STOP",
            "READY_TO_ENTER fue alcanzado, pero el precio actual "
            "invalidó el SL estructural",
        )

        return

    if result.get("stop_validation"):

        stop_validation = result.get(
            "stop_validation"
        ) or {}

        if stop_validation.get("valid"):

            print_transition(
                "MARKET_STOP",
                "PASS",
                stop_validation.get("reason"),
            )

        else:

            print_transition(
                "MARKET_STOP",
                "REJECTED",
                stop_validation.get("reason"),
            )

    else:

        print_transition(
            "MARKET_STOP",
            "NOT_REACHED",
            "No stop validation available",
        )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if action == "REJECTED_RISK_EXCEEDED":

        print_transition(
            "RISK",
            "REJECTED",
            (
                f"actual_risk="
                f"{result.get('actual_risk_amount')} | "
                f"max_allowed="
                f"{result.get('max_allowed_risk')}"
            ),
        )

        return

    if action == "INVALID_RISK_BASE":

        print_transition(
            "RISK",
            "REJECTED",
            f"invalid_risk_base={result.get('reason')}",
        )

        return

    if action == "INVALID_RISK_CONFIGURATION":

        print_transition(
            "RISK",
            "REJECTED",
            (
                f"risk_base={result.get('risk_base')} | "
                f"risk_percent={result.get('risk_percent')}"
            ),
        )

        return

    if result.get("risk_amount") is not None:

        print_transition(
            "RISK",
            "PASS",
            (
                f"risk_amount={result.get('risk_amount')} | "
                f"actual_risk="
                f"{result.get('actual_risk_amount')}"
            ),
        )

    else:

        print_transition(
            "RISK",
            "NOT_REACHED",
            "Risk calculation not available",
        )

    # --------------------------------------------------------
    # ORDER CHECK
    # --------------------------------------------------------

    if action == "REJECTED_ORDER_CHECK":

        order_check = result.get(
            "order_check"
        ) or {}

        print_transition(
            "ORDER_CHECK",
            "REJECTED",
            (
                f"retcode={order_check.get('retcode')} | "
                f"comment={order_check.get('comment')}"
            ),
        )

        return

    order_check = result.get(
        "order_check"
    ) or {}

    if order_check:

        if order_check.get("valid"):

            print_transition(
                "ORDER_CHECK",
                "PASS",
                (
                    f"retcode={order_check.get('retcode')} | "
                    f"comment={order_check.get('comment')}"
                ),
            )

        else:

            print_transition(
                "ORDER_CHECK",
                "REJECTED",
                (
                    f"retcode={order_check.get('retcode')} | "
                    f"comment={order_check.get('comment')}"
                ),
            )

    else:

        print_transition(
            "ORDER_CHECK",
            "NOT_REACHED",
            "No order check available",
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    if action == "DRY_RUN_VALIDATED":

        print_transition(
            "DRY_RUN_VALIDATED",
            "PASS",
            "Señal completamente validada. No se abrió ninguna orden.",
        )

    elif action == "ORDER_OPENED":

        print_transition(
            "ORDER_OPENED",
            "PASS",
            (
                f"trade_id={result.get('trade_id')} | "
                f"position_ticket={result.get('position_ticket')}"
            ),
        )

    elif action == "ALREADY_EXECUTED":

        print_transition(
            "EXECUTION",
            "SKIPPED",
            "La señal ya fue ejecutada anteriormente.",
        )

    elif action == "MAX_TOTAL_OPEN_POSITIONS":

        print_transition(
            "EXECUTION",
            "BLOCKED",
            "Se alcanzó el máximo total de posiciones.",
        )

    elif action == "POSITION_ALREADY_OPEN_FOR_SYMBOL":

        print_transition(
            "EXECUTION",
            "BLOCKED",
            "Ya existe una posición abierta para este símbolo.",
        )

    elif action == "RR_TOO_LOW":

        print_transition(
            "RR_VALIDATION",
            "REJECTED",
            (
                f"rr={result.get('risk_reward_ratio')} | "
                "No cumple el mínimo configurado."
            ),
        )

    else:

        print_transition(
            "FINAL_ACTION",
            "INFO",
            f"action={action}",
        )


# ============================================================
# DIAGNOSTICOS DE ANALISIS
# ============================================================

def print_analysis_diagnostics(result):

    diagnostics = get_diagnostics(result)

    if not diagnostics:
        return

    print("  diagnostics:")

    print(
        "    failed_stage:",
        diagnostics.get("failed_stage"),
    )

    print(
        "    sequence_status:",
        diagnostics.get("sequence_status"),
    )

    # --------------------------------------------------------
    # SEQUENCE
    # --------------------------------------------------------

    sequence = diagnostics.get("sequence") or {}

    if sequence:

        print("    sequence:")

        for key in (
            "m15_setups_total",
            "m5_confirmations_total",
            "require_latest_m15_setup",
            "require_m5_after_m15",
            "selected_setup_time",
            "selected_confirmation_time",
            "eligible_confirmations",
        ):

            if key in sequence:

                print(
                    f"      {key}: "
                    f"{sequence.get(key)}"
                )

    # --------------------------------------------------------
    # TIMEFRAMES
    # --------------------------------------------------------

    for tf in ("h1", "m15", "m5"):

        item = diagnostics.get(tf)

        if item:

            print(
                f"    {tf.upper()}: "
                f"candles={item.get('candles')} "
                f"setups={item.get('setups')} "
                f"confirmations={item.get('confirmations')} "
                f"last={item.get('last_candle_time')}"
            )

    # --------------------------------------------------------
    # SIGNAL AGE
    # --------------------------------------------------------

    signal_age = diagnostics.get(
        "signal_age"
    ) or {}

    if signal_age:

        print("    signal_age:")

        for key in (
            "valid",
            "reason",
            "signal_time",
            "latest_closed_candle_time",
            "signal_found_in_m5",
            "signal_bar_index",
            "latest_bar_index",
            "age_candles",
            "age_minutes",
            "max_age_candles",
            "max_age_minutes",
            "stale_by_candles",
            "stale_by_minutes",
            "is_stale",
        ):

            if key in signal_age:

                print(
                    f"      {key}: "
                    f"{signal_age.get(key)}"
                )

    # --------------------------------------------------------
    # DIRECTION POLICY
    # --------------------------------------------------------

    direction_policy = (
        diagnostics.get("direction_policy")
        or get_analysis(result).get(
            "direction_policy"
        )
        or {}
    )

    if direction_policy:

        print("    direction_policy:")

        for key in (
            "category",
            "allowed_direction",
            "reason",
        ):

            if key in direction_policy:

                print(
                    f"      {key}: "
                    f"{direction_policy.get(key)}"
                )


# ============================================================
# DIAGNOSTICOS DE POSICIONES
# ============================================================

def print_position_diagnostics(result):

    info = result.get(
        "position_diagnostics"
    ) or {}

    if not info:
        return

    print("  position_diagnostics:")

    print(
        "    source:",
        info.get("source"),
    )

    print(
        "    total_open:",
        info.get("total_open"),
    )

    print(
        "    symbol_open:",
        info.get("symbol_open"),
    )

    print(
        "    max_total:",
        info.get("max_total"),
    )

    print(
        "    max_per_symbol:",
        info.get("max_per_symbol"),
    )

    print(
        "    limits_enforced:",
        info.get("limits_enforced"),
    )

    open_trades = info.get(
        "open_trades"
    ) or []

    if open_trades:

        print("    open_trades:")

        for trade in open_trades:

            print(
                "      "
                f"id={trade.get('trade_id')} | "
                f"symbol={trade.get('instrument')} | "
                f"direction={trade.get('direction')} | "
                f"status={trade.get('status')} | "
                f"position_ticket="
                f"{trade.get('broker_position_ticket')}"
            )


# ============================================================
# DIAGNOSTICOS DE EJECUCION
# ============================================================

def print_execution_diagnostics(result):
    """
    Diagnóstico completo para resultados validados y rechazados.

    Especialmente útil para:

      - REJECTED_INVALID_MARKET_STOP
      - REJECTED_ORDER_CHECK
      - errores de filling mode
      - ajustes de SL/TP
      - diferencias entre señal y mercado actual
    """

    # --------------------------------------------------------
    # STOP VALIDATION
    # --------------------------------------------------------

    stop_validation = result.get(
        "stop_validation"
    ) or {}

    if stop_validation:

        print_mapping(
            "stop_validation",
            stop_validation,
        )

    # --------------------------------------------------------
    # MARKET STOP DIAGNOSTICS
    # --------------------------------------------------------

    market_stop_diagnostics = (
        result.get(
            "market_stop_diagnostics"
        )
        or result.get(
            "market_stop_diagnostic"
        )
        or result.get(
            "invalid_market_stop_diagnostics"
        )
        or {}
    )

    if market_stop_diagnostics:

        print_mapping(
            "MARKET_STOP_DIAGNOSTICS",
            market_stop_diagnostics,
        )

    # --------------------------------------------------------
    # MARKET SIGNAL DIAGNOSTICS
    # --------------------------------------------------------

    market_signal_diagnostics = (
        result.get(
            "market_signal_diagnostics"
        ) or {}
    )

    if market_signal_diagnostics:

        print_mapping(
            "MARKET_SIGNAL_DIAGNOSTICS",
            market_signal_diagnostics,
        )

    # --------------------------------------------------------
    # ORDER CHECK
    # --------------------------------------------------------

    order_check = result.get(
        "order_check"
    ) or {}

    if order_check:

        print_mapping(
            "ORDER_CHECK_DIAGNOSTICS",
            order_check,
        )

    # --------------------------------------------------------
    # OTROS DIAGNOSTICOS DE EJECUCION
    # --------------------------------------------------------

    execution_diagnostics = (
        result.get(
            "execution_diagnostics"
        )
        or result.get(
            "mt5_diagnostics"
        )
        or result.get(
            "order_diagnostics"
        )
        or {}
    )

    if execution_diagnostics:

        print_mapping(
            "EXECUTION_DIAGNOSTICS",
            execution_diagnostics,
        )


# ============================================================
# VALORES PRINCIPALES DE LA OPERACION
# ============================================================

def print_trade_values(result):
    """
    Imprime los valores principales disponibles.

    No depende de que action sea DRY_RUN_VALIDATED.
    """

    keys = (
        "direction",
        "entry_price",
        "market_entry_price",
        "signal_entry_price",
        "stop_loss",
        "original_stop_loss",
        "structural_stop_loss",
        "take_profit",
        "planned_rr",
        "risk_reward_ratio",
        "volume",
        "risk_amount",
        "actual_risk_amount",
        "risk_base",
        "risk_base_value",
        "execution_key",
    )

    for key in keys:

        if (
            key in result
            and result.get(key) is not None
        ):

            print(
                f"  {key}: "
                f"{result.get(key)}"
            )


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    connector = MT5Connector()

    provider = MT5DataProvider(
        connector
    )

    try:

        provider.connect()

        repo = TradingRepository()

        # ----------------------------------------------------
        # DESCUBRIR SIMBOLOS
        # ----------------------------------------------------
        #
        # Prueba dirigida:
        #
        # Boom  -> solo BUY
        # Crash -> solo SELL
        #
        # Esto permite comprobar claramente la política
        # direccional H1.
        # ----------------------------------------------------

        discovery = DerivSymbolDiscovery(
            connector
        )

        categorized = discovery.get_deriv_synthetics()

        symbols = (
            categorized.get("boom", [])[:5]
            +
            categorized.get("crash", [])[:5]
        )

        # Fallback si no se encontraron símbolos
        # categorizados.
        if not symbols:

            symbols = discovery.get_tradeable_synthetics()[:10]

        # ----------------------------------------------------
        # MOTOR
        # ----------------------------------------------------
        #
        # PRUEBA SEGURA:
        #
        # execution_enabled=False
        #     No abre órdenes reales.
        #
        # diagnostic_mode=True
        #     Devuelve todos los diagnósticos disponibles.
        #
        # enforce_position_limits_in_dry_run=False
        #     Permite analizar señales aunque existan operaciones
        #     OPEN antiguas en SQLite.
        # ----------------------------------------------------

        engine = LiveTradingEngine(
            provider,
            repo,
            LiveTradingConfig(

                execution_enabled=False,

                diagnostic_mode=True,

                enforce_position_limits_in_dry_run=False,

                max_total_open_positions=3,

                max_open_positions_per_symbol=1,

            ),
        )

        # ----------------------------------------------------
        # CABECERA
        # ----------------------------------------------------

        print("=" * 90)

        print(
            "PRUEBA LIVE DEMO SMC "
            "H1 -> M15 -> M5"
        )

        print(
            "MODO: DRY_RUN VALIDADO "
            "- SIN APERTURA DE ORDENES"
        )

        print(
            "TRANSICION:"
        )

        print(
            "START -> H1_CONTEXT -> DIRECTION_POLICY "
            "-> M15_SETUP -> M5_CONFIRMATION "
            "-> SEQUENCE_VALID -> SIGNAL_FRESH "
            "-> READY_TO_ENTER"
        )

        print(
            "EJECUCION:"
        )

        print(
            "READY_TO_ENTER -> MARKET_STOP "
            "-> RISK -> ORDER_CHECK "
            "-> DRY_RUN_VALIDATED"
        )

        print(
            "VALIDA: SL/TP del símbolo + volumen "
            "+ riesgo + MT5 order_check"
        )

        print(
            "DIAGNOSTICA: MARKET STOP + ORDER CHECK "
            "+ EJECUCION + TRANSICIONES"
        )

        print("=" * 90)

        # ----------------------------------------------------
        # PROCESAR SIMBOLOS
        # ----------------------------------------------------

        results = engine.process_symbols(
            symbols
        )

        summary = {}

        transition_summary = {}

        # ----------------------------------------------------
        # MOSTRAR RESULTADOS
        # ----------------------------------------------------

        for result in results:

            action = result.get(
                "action",
                "UNKNOWN",
            )

            summary[action] = (
                summary.get(action, 0)
                + 1
            )

            print("\n" + "=" * 90)

            print(
                f"{result.get('symbol')} "
                f"-> {action}"
            )

            print("=" * 90)

            if result.get("reason"):

                print(
                    "  reason:",
                    result["reason"],
                )

            if result.get("error"):

                print(
                    "  error:",
                    result["error"],
                )

            # ------------------------------------------------
            # TRANSICION COMPLETA
            # ------------------------------------------------

            print_transition_trace(
                result
            )

            # ------------------------------------------------
            # VALORES DE TRADE
            # ------------------------------------------------

            print_trade_values(
                result
            )

            # ------------------------------------------------
            # DIAGNOSTICOS DE EJECUCION
            # ------------------------------------------------

            print_execution_diagnostics(
                result
            )

            # ------------------------------------------------
            # DIAGNOSTICOS SMC
            # ------------------------------------------------

            print_analysis_diagnostics(
                result
            )

            # ------------------------------------------------
            # DIAGNOSTICOS DE POSICIONES
            # ------------------------------------------------

            print_position_diagnostics(
                result
            )

            # ------------------------------------------------
            # RESUMEN DE TRANSICIONES
            # ------------------------------------------------

            analysis = get_analysis(
                result
            )

            diagnostics = get_diagnostics(
                result
            )

            sequence_status = diagnostics.get(
                "sequence_status"
            )

            if (
                analysis.get("valid")
                or action in {
                    "RR_TOO_LOW",
                    "ALREADY_EXECUTED",
                    "MAX_TOTAL_OPEN_POSITIONS",
                    "POSITION_ALREADY_OPEN_FOR_SYMBOL",
                    "REJECTED_INVALID_MARKET_STOP",
                    "INVALID_RISK_BASE",
                    "INVALID_RISK_CONFIGURATION",
                    "REJECTED_RISK_EXCEEDED",
                    "REJECTED_ORDER_CHECK",
                    "DRY_RUN",
                    "DRY_RUN_VALIDATED",
                    "ORDER_OPENED",
                }
            ):

                transition_summary[
                    "READY_TO_ENTER"
                ] = (
                    transition_summary.get(
                        "READY_TO_ENTER",
                        0,
                    )
                    + 1
                )

            if sequence_status:

                key = (
                    f"SEQUENCE_{sequence_status}"
                )

                transition_summary[key] = (
                    transition_summary.get(
                        key,
                        0,
                    )
                    + 1
                )

        # ----------------------------------------------------
        # RESUMEN DE ACCIONES
        # ----------------------------------------------------

        print("\n" + "=" * 90)

        print("RESUMEN DE ACCIONES")

        print("=" * 90)

        for action, count in sorted(
            summary.items()
        ):

            print(
                f"{action}: {count}"
            )

        # ----------------------------------------------------
        # RESUMEN DE TRANSICIONES
        # ----------------------------------------------------

        print("\n" + "=" * 90)

        print("RESUMEN DE TRANSICIONES")

        print("=" * 90)

        if transition_summary:

            for stage, count in sorted(
                transition_summary.items()
            ):

                print(
                    f"{stage}: {count}"
                )

        else:

            print(
                "No se registraron transiciones."
            )

    finally:

        connector.disconnect()


if __name__ == "__main__":
    main()