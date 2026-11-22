import sys, re
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove Section 3 (Podados)
idx_p = text.find('id="losersTable"')
if idx_p != -1:
    start_p = text.rfind('<!--', 0, idx_p)
    end_p = text.find('</section>', idx_p) + len('</section>')
    # Clean any trailing whitespace
    while end_p < len(text) and text[end_p] in ' \t\r\n':
        end_p += 1
    print(f"Removing Podados section: {start_p} to {end_p}")
    text = text[:start_p] + text[end_p:]
else:
    print("Podados section not found!")

# 2. Remove Section 5 (Datasets)
idx_d = text.find('Datasets y Artefactos Persistidos')
if idx_d != -1:
    start_d = text.rfind('<!--', 0, idx_d)
    end_d = text.find('</section>', idx_d) + len('</section>')
    while end_d < len(text) and text[end_d] in ' \t\r\n':
        end_d += 1
    print(f"Removing Datasets section: {start_d} to {end_d}")
    text = text[:start_d] + text[end_d:]
else:
    print("Datasets section not found!")

# 3. Add guard to renderLosersTable
old_render = "function renderLosersTable() {\n        const tbody = document.getElementById('losersTableBody');\n        tbody.innerHTML = '';"
new_render = "function renderLosersTable() {\n        const tbody = document.getElementById('losersTableBody');\n        if (!tbody) return;\n        tbody.innerHTML = '';"

if old_render in text:
    text = text.replace(old_render, new_render)
    print("Added guard to renderLosersTable successfully.")
else:
    text = re.sub(
        r"function renderLosersTable\(\)\s*\{\s*const tbody = document\.getElementById\('losersTableBody'\);\s*tbody\.innerHTML = '';",
        "function renderLosersTable() {\n        const tbody = document.getElementById('losersTableBody');\n        if (!tbody) return;\n        tbody.innerHTML = '';",
        text
    )
    print("Added guard with regex.")

# Save file
with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved updated dashboard/strategy_bases_page.py")
