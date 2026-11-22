"""Test de integridad estructural y sintáctica de la página /decisions."""
import re
import shutil
import subprocess
from dashboard.decisions_page import _DECISIONS_BASE, DECISIONS_HTML


def test_decisions_page_html_structure():
    """Valida que el HTML contenga todos los contenedores DOM requeridos."""
    required_ids = [
        "days",
        "cards",
        "pillEvents",
        "pillVetoes",
        "pillTrades",
        "coverageNote",
        "tblActions",
        "tblDays",
        "tblStrat",
        "tblSyms",
        "tblVetoes",
        "tblHC",
        "tblAI",
        "tblTStrat",
        "tblRecent",
        "stamp",
        "reload",
    ]
    for dom_id in required_ids:
        assert (f'id="{dom_id}"' in _DECISIONS_BASE) or (f"id='{dom_id}'" in _DECISIONS_BASE), (
            f"Falta el elemento DOM con id='{dom_id}' en _DECISIONS_BASE"
        )


def test_decisions_page_loading_wrapper():
    """Valida que la página esté envuelta con with_page_loading y gestione el spinner."""
    assert "pageLoadingBar" in DECISIONS_HTML
    assert "pageLoading" in DECISIONS_HTML
    assert "pageLoading.done()" in _DECISIONS_BASE
    assert "pageLoading.fail(" in _DECISIONS_BASE


def test_decisions_page_javascript_syntax():
    """Si node está presente en el entorno, valida la sintaxis completa del script JS."""
    node = shutil.which("node")
    if not node:
        return
    scripts = re.findall(r"<script>(.*?)</script>", _DECISIONS_BASE, re.DOTALL)
    assert len(scripts) >= 1, "No se encontró bloque <script> en _DECISIONS_BASE"
    for idx, script in enumerate(scripts):
        proc = subprocess.run(
            [node, "--check"],
            input=script,
            text=True,
            capture_output=True,
        )
        assert proc.returncode == 0, f"Error de sintaxis JS en script {idx}: {proc.stderr}"
