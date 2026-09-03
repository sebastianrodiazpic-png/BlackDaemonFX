from reporting.console_reporting_service import ConsoleReportingConfig, ConsoleReportingService


def test_normal_mode_hides_no_signal(capsys):
    reporter = ConsoleReportingService(ConsoleReportingConfig(verbose=False))
    reporter.print_result({"symbol": "Boom 100 Index", "action": "NO_SIGNAL", "reason": "WAITING"}, 1, 1)
    assert capsys.readouterr().out == ""


def test_verbose_mode_prints_reason(capsys):
    reporter = ConsoleReportingService(ConsoleReportingConfig(verbose=True))
    reporter.print_result({"symbol": "Volatility 90 Index", "action": "RR_TOO_LOW", "reason": "1.20 < 1.50", "direction": "BUY"}, 1, 1)
    output = capsys.readouterr().out
    assert "VOLATILITY 90 INDEX" not in output.upper() or "Volatility 90 Index" in output
    assert "RELACIÓN RIESGO/BENEFICIO INSUFICIENTE" in output
    assert "1.20 < 1.50" in output


def test_summary_counts_actions(capsys):
    reporter = ConsoleReportingService()
    reporter.summarize([
        {"action": "NO_SIGNAL"},
        {"action": "ORDER_OPENED"},
        {"action": "RR_TOO_LOW"},
    ], sync=2, cycle_number=3, interval=30)
    output = capsys.readouterr().out
    assert "RESUMEN DEL CICLO #0003" in output
    assert "Nuevas órdenes: 1" in output
    assert "Operaciones cerradas sincronizadas: 2" in output
