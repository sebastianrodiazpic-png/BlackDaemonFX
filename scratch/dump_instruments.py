with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('_INSTRUMENTS_HTML = r\'\'\'')
end_pos = text.find("'''\n\n_STRATEGY_BASES_HTML", pos)
if end_pos == -1:
    end_pos = text.find("'''", pos + 25)

print(f"Start pos: {pos}, End pos: {end_pos}, Total chars: {end_pos - pos}")
inst_html = text[pos:end_pos]

with open('scratch/instruments_full.html', 'w', encoding='utf-8') as out:
    out.write(inst_html)

print("Saved to scratch/instruments_full.html")
