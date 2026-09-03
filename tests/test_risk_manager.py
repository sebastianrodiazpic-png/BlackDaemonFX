import pandas as pd

from strategy.risk.risk_manager import (
    validate_direction,
    validate_stop_loss_direction,
    validate_take_profit_direction,
    calculate_risk_reward,
    validate_risk_reward,
    calculate_current_risk,
    calculate_max_loss_amount,
    calculate_daily_loss,
    count_consecutive_losses,
    calculate_current_drawdown,
    calculate_open_positions_risk,
    check_daily_loss_limit,
    check_drawdown_limit,
    evaluate_trade_risk,
    evaluate_risk,
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


# ============================================================
# TEST 1
# VALIDAR DIRECCIONES
# ============================================================

def test_validate_direction():

    print_section(
        "TEST 1 - VALIDAR DIRECCIONES"
    )

    directions = [
        "BUY",
        "SELL",
        "LONG",
        "SHORT"
    ]

    for direction in directions:

        result = validate_direction(
            direction
        )

        print(
            f"{direction} -> {result}"
        )

        assert result == direction


# ============================================================
# TEST 2
# STOP LOSS BUY VÁLIDO
# ============================================================

def test_stop_loss_buy_valid():

    print_section(
        "TEST 2 - STOP LOSS BUY VÁLIDO"
    )

    result = validate_stop_loss_direction(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0
    )

    print_result(
        result
    )

    assert result["valid"] is True


# ============================================================
# TEST 3
# STOP LOSS BUY INVÁLIDO
# ============================================================

def test_stop_loss_buy_invalid():

    print_section(
        "TEST 3 - STOP LOSS BUY INVÁLIDO"
    )

    result = validate_stop_loss_direction(
        direction="BUY",
        entry_price=100.0,
        stop_loss=105.0
    )

    print_result(
        result
    )

    assert result["valid"] is False


# ============================================================
# TEST 4
# STOP LOSS SELL VÁLIDO
# ============================================================

def test_stop_loss_sell_valid():

    print_section(
        "TEST 4 - STOP LOSS SELL VÁLIDO"
    )

    result = validate_stop_loss_direction(
        direction="SELL",
        entry_price=100.0,
        stop_loss=105.0
    )

    print_result(
        result
    )

    assert result["valid"] is True


# ============================================================
# TEST 5
# TAKE PROFIT BUY VÁLIDO
# ============================================================

def test_take_profit_buy_valid():

    print_section(
        "TEST 5 - TAKE PROFIT BUY VÁLIDO"
    )

    result = validate_take_profit_direction(
        direction="BUY",
        entry_price=100.0,
        take_profit=110.0
    )

    print_result(
        result
    )

    assert result["valid"] is True


# ============================================================
# TEST 6
# TAKE PROFIT SELL VÁLIDO
# ============================================================

def test_take_profit_sell_valid():

    print_section(
        "TEST 6 - TAKE PROFIT SELL VÁLIDO"
    )

    result = validate_take_profit_direction(
        direction="SELL",
        entry_price=100.0,
        take_profit=90.0
    )

    print_result(
        result
    )

    assert result["valid"] is True


# ============================================================
# TEST 7
# CALCULAR RISK / REWARD
# ============================================================

def test_calculate_risk_reward():

    print_section(
        "TEST 7 - CALCULAR RISK / REWARD"
    )

    result = calculate_risk_reward(
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0
    )

    print_result(
        result
    )

    assert result[
        "risk_distance"
    ] == 5.0

    assert result[
        "reward_distance"
    ] == 10.0

    assert result[
        "risk_reward_ratio"
    ] == 2.0


# ============================================================
# TEST 8
# VALIDAR RISK / REWARD
# ============================================================

def test_validate_risk_reward():

    print_section(
        "TEST 8 - VALIDAR RISK / REWARD"
    )

    result = validate_risk_reward(
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        min_risk_reward=1.5
    )

    print_result(
        result
    )

    assert result["valid"] is True

    assert result[
        "risk_reward_ratio"
    ] == 2.0


# ============================================================
# TEST 9
# RISK / REWARD INVÁLIDO
# ============================================================

def test_validate_risk_reward_invalid():

    print_section(
        "TEST 9 - RISK / REWARD INVÁLIDO"
    )

    result = validate_risk_reward(
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=102.0,
        min_risk_reward=1.0
    )

    print_result(
        result
    )

    assert result["valid"] is False


# ============================================================
# TEST 10
# CALCULAR RIESGO Y POSITION SIZE
# ============================================================

def test_calculate_current_risk():

    print_section(
        "TEST 10 - CALCULAR RIESGO ACTUAL"
    )

    result = calculate_current_risk(
        account_balance=10000.0,
        entry_price=100.0,
        stop_loss=95.0,
        risk_percent=1.0,
        point_value=1.0
    )

    print_result(
        result
    )

    assert result[
        "risk_amount"
    ] == 100.0

    assert result[
        "position_size"
    ] == 20.0


# ============================================================
# TEST 11
# CALCULAR PÉRDIDA MÁXIMA
# ============================================================

def test_calculate_max_loss_amount():

    print_section(
        "TEST 11 - CALCULAR PÉRDIDA MÁXIMA"
    )

    result = calculate_max_loss_amount(
        account_balance=10000.0,
        max_loss_percent=3.0
    )

    print(
        f"Pérdida máxima: {result}"
    )

    assert result == 300.0


# ============================================================
# TEST 12
# CALCULAR PÉRDIDA DIARIA
# ============================================================

def test_calculate_daily_loss():

    print_section(
        "TEST 12 - CALCULAR PÉRDIDA DIARIA"
    )

    trades = pd.DataFrame(
        {
            "exit_time": [
                "2026-08-24 09:00:00",
                "2026-08-24 10:00:00",
                "2026-08-24 11:00:00"
            ],

            "pnl": [
                -100.0,
                -50.0,
                25.0
            ]
        }
    )

    result = calculate_daily_loss(
        trades=trades,
        current_time="2026-08-24 12:00:00"
    )

    print_result(
        result
    )

    assert result[
        "daily_pnl"
    ] == -125.0

    assert result[
        "daily_loss"
    ] == 125.0

    assert result[
        "trades_today"
    ] == 3


# ============================================================
# TEST 13
# PÉRDIDAS CONSECUTIVAS
# ============================================================

def test_count_consecutive_losses():

    print_section(
        "TEST 13 - PÉRDIDAS CONSECUTIVAS"
    )

    trades = pd.DataFrame(
        {
            "pnl": [
                100.0,
                -50.0,
                -75.0,
                -25.0
            ]
        }
    )

    result = count_consecutive_losses(
        trades
    )

    print(
        f"Pérdidas consecutivas: {result}"
    )

    assert result == 3


# ============================================================
# TEST 14
# CALCULAR DRAWDOWN
# ============================================================

def test_calculate_current_drawdown():

    print_section(
        "TEST 14 - CALCULAR DRAWDOWN"
    )

    trades = pd.DataFrame(
        {
            "balance_after": [
                10500.0,
                10300.0,
                10000.0,
                10200.0
            ]
        }
    )

    result = calculate_current_drawdown(
        trades=trades,
        initial_balance=10000.0
    )

    print_result(
        result
    )

    assert result[
        "peak_balance"
    ] == 10500.0

    assert result[
        "current_balance"
    ] == 10200.0

    assert result[
        "max_drawdown_amount"
    ] == 500.0


# ============================================================
# TEST 15
# RIESGO DE POSICIONES ABIERTAS
# ============================================================

def test_calculate_open_positions_risk():

    print_section(
        "TEST 15 - RIESGO DE POSICIONES ABIERTAS"
    )

    open_positions = [
        {
            "actual_risk_amount": 100.0
        },
        {
            "actual_risk_amount": 50.0
        }
    ]

    result = calculate_open_positions_risk(
        open_positions
    )

    print_result(
        result
    )

    assert result[
        "open_positions_count"
    ] == 2

    assert result[
        "total_open_risk_amount"
    ] == 150.0


# ============================================================
# TEST 16
# VALIDAR LÍMITE DE PÉRDIDA DIARIA
# ============================================================

def test_check_daily_loss_limit():

    print_section(
        "TEST 16 - LÍMITE DE PÉRDIDA DIARIA"
    )

    trades = pd.DataFrame(
        {
            "exit_time": [
                "2026-08-24 09:00:00",
                "2026-08-24 10:00:00"
            ],

            "pnl": [
                -100.0,
                -50.0
            ]
        }
    )

    result = check_daily_loss_limit(
        trades=trades,
        account_balance=10000.0,
        max_daily_loss_percent=3.0,
        current_time="2026-08-24 12:00:00"
    )

    print_result(
        result
    )

    assert result["allowed"] is True

    assert result[
        "max_daily_loss_amount"
    ] == 300.0


# ============================================================
# TEST 17
# BLOQUEAR POR PÉRDIDA DIARIA
# ============================================================

def test_check_daily_loss_limit_blocked():

    print_section(
        "TEST 17 - BLOQUEAR POR PÉRDIDA DIARIA"
    )

    trades = pd.DataFrame(
        {
            "exit_time": [
                "2026-08-24 09:00:00",
                "2026-08-24 10:00:00"
            ],

            "pnl": [
                -200.0,
                -150.0
            ]
        }
    )

    result = check_daily_loss_limit(
        trades=trades,
        account_balance=10000.0,
        max_daily_loss_percent=3.0,
        current_time="2026-08-24 12:00:00"
    )

    print_result(
        result
    )

    assert result["allowed"] is False


# ============================================================
# TEST 18
# VALIDAR LÍMITE DE DRAWDOWN
# ============================================================

def test_check_drawdown_limit():

    print_section(
        "TEST 18 - VALIDAR DRAWDOWN"
    )

    trades = pd.DataFrame(
        {
            "balance_after": [
                10500.0,
                10200.0,
                10000.0
            ]
        }
    )

    result = check_drawdown_limit(
        trades=trades,
        initial_balance=10000.0,
        max_drawdown_percent=10.0
    )

    print_result(
        result
    )

    assert result["allowed"] is True


# ============================================================
# TEST 19
# OPERACIÓN BUY APROBADA
# ============================================================

def test_evaluate_trade_risk_buy_approved():

    print_section(
        "TEST 19 - BUY APROBADO"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0,
        risk_percent=1.0,
        point_value=1.0,
        min_position_size=0.01,
        min_risk_reward=1.5
    )

    print_result(
        result
    )

    assert result["approved"] is True

    assert result[
        "position_size"
    ] == 20.0

    assert result[
        "risk_reward_ratio"
    ] == 2.0


# ============================================================
# TEST 20
# OPERACIÓN SELL APROBADA
# ============================================================

def test_evaluate_trade_risk_sell_approved():

    print_section(
        "TEST 20 - SELL APROBADO"
    )

    result = evaluate_trade_risk(
        direction="SELL",
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=90.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0,
        risk_percent=1.0,
        point_value=1.0,
        min_position_size=0.01,
        min_risk_reward=1.5
    )

    print_result(
        result
    )

    assert result["approved"] is True

    assert result[
        "position_size"
    ] == 20.0


# ============================================================
# TEST 21
# BUY RECHAZADO POR STOP LOSS
# ============================================================

def test_evaluate_trade_risk_invalid_stop_loss():

    print_section(
        "TEST 21 - BUY RECHAZADO POR STOP LOSS"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0
    )

    print_result(
        result
    )

    assert result["approved"] is False


# ============================================================
# TEST 22
# SELL RECHAZADO POR TAKE PROFIT
# ============================================================

def test_evaluate_trade_risk_invalid_take_profit():

    print_section(
        "TEST 22 - SELL RECHAZADO POR TAKE PROFIT"
    )

    result = evaluate_trade_risk(
        direction="SELL",
        entry_price=100.0,
        stop_loss=105.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0
    )

    print_result(
        result
    )

    assert result["approved"] is False


# ============================================================
# TEST 23
# RECHAZADO POR RISK / REWARD
# ============================================================

def test_evaluate_trade_risk_low_rr():

    print_section(
        "TEST 23 - RECHAZADO POR RISK / REWARD"
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=102.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0,
        min_risk_reward=1.0
    )

    print_result(
        result
    )

    assert result["approved"] is False


# ============================================================
# TEST 24
# RECHAZADO POR PÉRDIDAS CONSECUTIVAS
# ============================================================

def test_evaluate_trade_risk_consecutive_losses():

    print_section(
        "TEST 24 - RECHAZADO POR PÉRDIDAS CONSECUTIVAS"
    )

    trades = pd.DataFrame(
        {
            "pnl": [
                -100.0,
                -50.0,
                -75.0
            ]
        }
    )

    result = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=trades,
        initial_balance=10000.0,
        max_consecutive_losses=3
    )

    print_result(
        result
    )

    assert result["approved"] is False

    assert result[
        "consecutive_losses"
    ] == 3


# ============================================================
# TEST 25
# RECHAZADO POR POSICIÓN ABIERTA
# ============================================================

def test_evaluate_trade_risk_max_positions():

    print_section(
        "TEST 25 - RECHAZADO POR POSICIONES ABIERTAS"
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
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0,
        open_positions=open_positions,
        max_open_positions=1
    )

    print_result(
        result
    )

    assert result["approved"] is False


# ============================================================
# TEST 26
# RECHAZADO POR RIESGO TOTAL
# ============================================================

def test_evaluate_trade_risk_total_risk():

    print_section(
        "TEST 26 - RECHAZADO POR RIESGO TOTAL"
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
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0,
        risk_percent=1.0,
        point_value=1.0,
        open_positions=open_positions,
        max_open_positions=5,
        max_total_risk_percent=2.0
    )

    print_result(
        result
    )

    assert result["approved"] is False

    assert result[
        "total_risk_percent"
    ] > 2.0


# ============================================================
# TEST 27
# EVALUATE_RISK ALIAS
# ============================================================

def test_evaluate_risk_alias():

    print_section(
        "TEST 27 - EVALUATE RISK ALIAS"
    )

    result = evaluate_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0
    )

    print_result(
        result
    )

    assert result["approved"] is True


# ============================================================
# TEST 28
# RESUMEN DE RIESGO
# ============================================================

def test_get_risk_summary():

    print_section(
        "TEST 28 - RESUMEN DE RIESGO"
    )

    evaluation = evaluate_trade_risk(
        direction="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        account_balance=10000.0,
        trades=pd.DataFrame(),
        initial_balance=10000.0
    )

    result = get_risk_summary(
        evaluation
    )

    print_result(
        result
    )

    assert result["approved"] is True

    assert result[
        "position_size"
    ] == 20.0


# ============================================================
# EJECUTAR TODOS LOS TESTS
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("INICIANDO TESTS DE RISK MANAGER")
    print("=" * 70)

    test_validate_direction()

    test_stop_loss_buy_valid()

    test_stop_loss_buy_invalid()

    test_stop_loss_sell_valid()

    test_take_profit_buy_valid()

    test_take_profit_sell_valid()

    test_calculate_risk_reward()

    test_validate_risk_reward()

    test_validate_risk_reward_invalid()

    test_calculate_current_risk()

    test_calculate_max_loss_amount()

    test_calculate_daily_loss()

    test_count_consecutive_losses()

    test_calculate_current_drawdown()

    test_calculate_open_positions_risk()

    test_check_daily_loss_limit()

    test_check_daily_loss_limit_blocked()

    test_check_drawdown_limit()

    test_evaluate_trade_risk_buy_approved()

    test_evaluate_trade_risk_sell_approved()

    test_evaluate_trade_risk_invalid_stop_loss()

    test_evaluate_trade_risk_invalid_take_profit()

    test_evaluate_trade_risk_low_rr()

    test_evaluate_trade_risk_consecutive_losses()

    test_evaluate_trade_risk_max_positions()

    test_evaluate_trade_risk_total_risk()

    test_evaluate_risk_alias()

    test_get_risk_summary()

    print("\n")
    print("=" * 70)
    print("TODOS LOS TESTS DE RISK MANAGER FINALIZARON CORRECTAMENTE")
    print("=" * 70)
    print("\n")