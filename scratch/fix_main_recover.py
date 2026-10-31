from pathlib import Path
import os

target_file = Path("app") / "main.py"
tmp_file = Path("app") / "main.py.tmp"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

bad_block = """    preference = reader("SYNTHETICS", source="DEMO")
    if preference is None or preference.get("selected_symbols"):
        return None
    synthetic_symbols = sorted("""

good_block = """    preference = reader("SYNTHETICS", source="DEMO")
    if preference is None or not preference.get("selected_symbols"):
        synthetic_symbols = sorted("""

# Y al final del bloque de synthetic_symbols:
bad_block2 = """        print(
            "[RECUPERACIÓN] SYNTHETICS estaba vacío: "
            f"se habilitaron {len(synthetic_symbols)} instrumentos del catálogo."
        )

    # v110: Garantizar que los workers GOLD y ORB cuenten con selección activa en DEMO"""

good_block2 = """        print(
            "[RECUPERACIÓN] SYNTHETICS estaba vacío: "
            f"se habilitaron {len(synthetic_symbols)} instrumentos del catálogo."
        )

    # v110: Garantizar que los workers GOLD y ORB cuenten con selección activa en DEMO"""

if bad_block in content:
    content = content.replace(bad_block, good_block, 1)
    print("Fixed bad_block with LF")
else:
    bad_crlf = bad_block.replace("\n", "\r\n")
    good_crlf = good_block.replace("\n", "\r\n")
    if bad_crlf in content:
        content = content.replace(bad_crlf, good_crlf, 1)
        print("Fixed bad_block with CRLF")
    else:
        print("ERROR: bad_block NOT found")

with open(tmp_file, "w", encoding="utf-8") as f:
    f.write(content)

os.replace(tmp_file, target_file)
print("app/main.py updated successfully.")
