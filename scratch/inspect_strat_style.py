with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('_STRATEGY_BASES_HTML = r\'\'\'')
if pos == -1:
    pos = text.find('_STRATEGY_BASES_HTML = \'\'\'')
if pos == -1:
    pos = text.find('_STRATEGY_BASES_HTML = """')

print(f"Strategy bases pos: {pos}")
# print first 1500 chars of CSS from strategy bases
style_pos = text.find('<style>', pos)
print(text[style_pos:style_pos+2000])
