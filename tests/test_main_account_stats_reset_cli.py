
from pathlib import Path


def test_main_exposes_account_stats_reset_command_and_confirmation():
    root = Path(__file__).resolve().parents[1]
    text = (root / "app" / "main.py").read_text(encoding="utf-8")
    assert '"--reset-account-stats"' in text
    assert '"--confirm-reset-account-stats"' in text
    assert '"reset-account-stats"' in text
    assert 'input("Escriba RESET para continuar: ")' in text
    assert "reset_account_statistics" in text
