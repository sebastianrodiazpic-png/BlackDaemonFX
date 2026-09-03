import pandas as pd

from strategy.risk.risk_manager import (
    evaluate_trade_risk,
    get_risk_summary
)


# ============================================================
# UTILIDADES
# ============================================================

def print_section(title):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_result(result):

    for key, value in result.items():

        print(f"{key}: {value}")


def assert_result(
    result,
    expected_approved,
    test_name
):

    approved = result.get(
        "approved",
        False
    )

    if approved != expected_approved:

        raise AssertionError(
            f"{test_name} FALLÓ. "
            f"Esperado approved={expected_approved}, "
            f"obtenido approved={approved}. "
            f"Reason: {result.get('reason')}"
        )

    print(
        f"\n[OK] {test_name} completado correctamente."
    )


# ============================================================
# DATOS BASE
# ============================================================

ACCOUNT_BALANCE = 10000.0
INITIAL_BALANCE = 10000.0
RISK_PERCENT = 1.0
POINT_VALUE = 1.0


# ============================================================
# TEST 1
# OPERACIÓN BUY COMPLETAMENTE VÁLIDA
# ============================================================

def test_valid_buy():

    print_section(
        "TEST 1 - BUY VÁLIDO"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        min_risk_reward=2.0
    )

    print_result(
        result
    )

    assert_result(
        result,
        True,
        "TEST 1 - BUY VÁLIDO"
    )


# ============================================================
# TEST 2
# OPERACIÓN SELL COMPLETAMENTE VÁLIDA
# ============================================================

def test_valid_sell():

    print_section(
        "TEST 2 - SELL VÁLIDO"
    )

    result = evaluate_trade_risk(
        direction="SELL",
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=90.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        min_risk_reward=2.0
    )

    print_result(
        result
    )

    assert_result(
        result,
        True,
        "TEST 2 - SELL VÁLIDO"
    )


# ============================================================
# TEST 3
# RECHAZAR STOP LOSS BUY INCORRECTO
# ============================================================

def test_invalid_buy_stop_loss():

    print_section(
        "TEST 3 - BUY RECHAZADO POR STOP LOSS"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 3 - STOP LOSS BUY"
    )


# ============================================================
# TEST 4
# RECHAZAR TAKE PROFIT SELL INCORRECTO
# ============================================================

def test_invalid_sell_take_profit():

    print_section(
        "TEST 4 - SELL RECHAZADO POR TAKE PROFIT"
    )

    result = evaluate_trade_risk(
        direction="SELL",
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 4 - TAKE PROFIT SELL"
    )


# ============================================================
# TEST 5
# RECHAZAR RISK / REWARD INSUFICIENTE
# ============================================================

def test_invalid_risk_reward():

    print_section(
        "TEST 5 - RECHAZADO POR RISK / REWARD"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=102.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        min_risk_reward=1.0
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 5 - RISK / REWARD"
    )


# ============================================================
# TEST 6
# RECHAZAR POR PÉRDIDA DIARIA
# ============================================================

def test_daily_loss_limit():

    print_section(
        "TEST 6 - RECHAZADO POR PÉRDIDA DIARIA"
    )

    trades = pd.DataFrame(
        [
            {
                "exit_time": "2026-08-24 10:00:00",
                "pnl": -350.0
            }
        ]
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=trades,
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        max_daily_loss_percent=3.0,
        current_time="2026-08-24 12:00:00"
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 6 - PÉRDIDA DIARIA"
    )


# ============================================================
# TEST 7
# RECHAZAR POR DRAWDOWN
# ============================================================

def test_drawdown_limit():

    print_section(
        "TEST 7 - RECHAZADO POR DRAWDOWN"
    )

    trades = pd.DataFrame(
        [
            {
                "exit_time": "2026-08-20 10:00:00",
                "pnl": 0.0,
                "balance_after": 10000.0
            },
            {
                "exit_time": "2026-08-21 10:00:00",
                "pnl": 0.0,
                "balance_after": 8500.0
            }
        ]
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=trades,
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        max_daily_loss_percent=3.0,
        max_drawdown_percent=10.0,
        current_time="2026-08-24 12:00:00"
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 7 - DRAWDOWN"
    )


# ============================================================
# TEST 8
# RECHAZAR POR PÉRDIDAS CONSECUTIVAS
# ============================================================

def test_consecutive_losses():

    print_section(
        "TEST 8 - RECHAZADO POR PÉRDIDAS CONSECUTIVAS"
    )

    trades = pd.DataFrame(
        [
            {"exit_time": "2026-08-20 10:00:00", "pnl": -50.0},
            {"exit_time": "2026-08-21 10:00:00", "pnl": -50.0},
            {"exit_time": "2026-08-22 10:00:00", "pnl": -50.0}
        ]
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=trades,
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        max_consecutive_losses=3
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 8 - PÉRDIDAS CONSECUTIVAS"
    )


# ============================================================
# TEST 9
# RECHAZAR POR POSICIONES ABIERTAS
# ============================================================

def test_open_positions_limit():

    print_section(
        "TEST 9 - RECHAZADO POR POSICIONES ABIERTAS"
    )

    open_positions = [
        {
            "actual_risk_amount": 100.0
        }
    ]

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE,
        open_positions=open_positions,
        max_open_positions=1
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 9 - POSICIONES ABIERTAS"
    )


# ============================================================
# TEST 10
# RECHAZAR POR RIESGO TOTAL
# ============================================================

def test_total_risk_limit():

    print_section(
        "TEST 10 - RECHAZADO POR RIESGO TOTAL"
    )

    open_positions = [
        {
            "actual_risk_amount": 150.0
        }
    ]

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=1.0,
        point_value=POINT_VALUE,
        open_positions=open_positions,
        max_open_positions=2,
        max_total_risk_percent=2.0
    )

    print_result(
        result
    )

    assert_result(
        result,
        False,
        "TEST 10 - RIESGO TOTAL"
    )


# ============================================================
# TEST 11
# RESUMEN DE RIESGO
# ============================================================

def test_risk_summary():

    print_section(
        "TEST 11 - RESUMEN DE RIESGO"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=ACCOUNT_BALANCE,
        initial_balance=INITIAL_BALANCE,
        trades=pd.DataFrame(),
        risk_percent=RISK_PERCENT,
        point_value=POINT_VALUE
    )

    summary = get_risk_summary(
        result
    )

    print_result(
        summary
    )

    if not summary["approved"]:

        raise AssertionError(
            "TEST 11 FALLÓ. "
            "La operación debería estar aprobada."
        )

    print(
        "\n[OK] TEST 11 - RESUMEN DE RIESGO "
        "completado correctamente."
    )


# ============================================================
# EJECUTAR TODOS LOS TESTS
# ============================================================

def run_all_tests():

    print("\n" + "=" * 70)
    print("INICIANDO TEST DE INTEGRACIÓN - RISK MANAGER")
    print("=" * 70)

    test_valid_buy()

    test_valid_sell()

    test_invalid_buy_stop_loss()

    test_invalid_sell_take_profit()

    test_invalid_risk_reward()

    test_daily_loss_limit()

    test_drawdown_limit()

    test_consecutive_losses()

    test_open_positions_limit()

    test_total_risk_limit()

    test_risk_summary()

    print("\n" + "=" * 70)
    print("TODOS LOS TESTS DE INTEGRACIÓN FINALIZARON CORRECTAMENTE")
    print("=" * 70 + "\n")


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":

    run_all_tests()