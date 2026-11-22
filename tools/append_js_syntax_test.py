# -*- coding: utf-8 -*-
with open('tests/test_v121_instruments_tri_motor_worker_control.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_test = """

def test_instruments_javascript_syntax_valid():
    \"\"\"Valida que todos los scripts incrustados en /instruments tengan sintaxis JavaScript 100% válida sin errores en Node.js.\"\"\"
    import re
    import subprocess
    from pathlib import Path

    scripts = re.findall(r"<script>(.*?)</script>", _INSTRUMENTS_HTML, re.DOTALL)
    assert len(scripts) >= 1
    root = Path(__file__).resolve().parents[1]
    for idx, script in enumerate(scripts):
        test_js = root / "storage" / f"test_instruments_syntax_{idx}.js"
        test_js.parent.mkdir(parents=True, exist_ok=True)
        test_js.write_text(script, encoding="utf-8")
        res = subprocess.run(["node", "--check", str(test_js)], capture_output=True, text=True)
        assert res.returncode == 0, f"Script {idx} in /instruments failed JS syntax check: {res.stderr}"
"""

if "test_instruments_javascript_syntax_valid" not in text:
    text += new_test
    with open('tests/test_v121_instruments_tri_motor_worker_control.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added test_instruments_javascript_syntax_valid")
else:
    print("Already present")
