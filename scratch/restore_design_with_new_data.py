"""
scratch/restore_design_with_new_data.py
Restaura el diseño 100% exacto de commit 8162056 pero inyecta los datos actualizados
de WINNERS_DATA y LOSERS_DATA sin tocar NINGUNA etiqueta HTML, clase CSS o estructura de diseño.
"""
import json
import re
import subprocess
from pathlib import Path

# 1. Obtener el archivo original con el diseño perfecto de 8162056
p = subprocess.run(
    ["git", "show", "8162056:dashboard/strategy_bases_page.py"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)
original_file = p.stdout
assert len(original_file) > 100000, "Error obteniendo el archivo de git"

# 2. Cargar los datos actuales de WINNERS_DATA y LOSERS_DATA que tienen la información actualizada
current_file = Path("dashboard/strategy_bases_page.py").read_text(encoding="utf-8")

m_curr_win = re.search(r"const WINNERS_DATA = (\[.*?\]);", current_file, re.DOTALL)
m_curr_los = re.search(r"const LOSERS_DATA = (\[.*?\]);", current_file, re.DOTALL)

assert m_curr_win is not None, "No se encontró WINNERS_DATA en current_file"
assert m_curr_los is not None, "No se encontró LOSERS_DATA en current_file"

updated_winners_json = m_curr_win.group(1)
updated_losers_json = m_curr_los.group(1)

# Verificar que los datos actualizados tienen Crash 300 al 78.8%
winners_list = json.loads(updated_winners_json)
c300_msnr = next(w for w in winners_list if w["symbol"] == "Crash 300 Index" and w["strategy"] == "Malaysian SNR")
print(f"Crash 300 MSNR en datos a inyectar: {c300_msnr['trades']} trades, {c300_msnr['win_rate']}% WR, ${c300_msnr['pnl']}")
assert c300_msnr['win_rate'] == 78.8

# 3. En el archivo original de diseño (8162056), encontrar ÚNICAMENTE los bloques de datos y reemplazarlos
# Localizar const WINNERS_DATA = [...] y const LOSERS_DATA = [...] en original_file
m_orig_win = re.search(r"(const WINNERS_DATA\s*=\s*)\[.*?\];", original_file, re.DOTALL)
assert m_orig_win is not None, "No se encontró WINNERS_DATA en original_file"

# Reemplazar WINNERS_DATA
temp_file = original_file[:m_orig_win.start(0)] + f"const WINNERS_DATA = {updated_winners_json};" + original_file[m_orig_win.end(0):]

# Localizar const LOSERS_DATA = [...] en temp_file
m_orig_los = re.search(r"(const LOSERS_DATA\s*=\s*)\[.*?\];", temp_file, re.DOTALL)
assert m_orig_los is not None, "No se encontró LOSERS_DATA en original_file"

final_file = temp_file[:m_orig_los.start(0)] + f"const LOSERS_DATA = {updated_losers_json};" + temp_file[m_orig_los.end(0):]

# 4. Guardar en dashboard/strategy_bases_page.py
Path("dashboard/strategy_bases_page.py").write_text(final_file, encoding="utf-8")
print(f"Restaurado con éxito. Longitud final: {len(final_file)} caracteres.")
