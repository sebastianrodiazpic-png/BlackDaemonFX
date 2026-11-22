with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    text = f.read()

pos_html = text.find('_INSTRUMENTS_HTML = """')
if pos_html == -1:
    pos_html = text.find('_INSTRUMENTS_HTML = \'\'\'')
    if pos_html == -1:
        pos_html = text.find('_INSTRUMENTS_HTML')

print("Pos of _INSTRUMENTS_HTML:", pos_html)
pos_script = text.find('<script>', pos_html)
pos_script_end = text.find('</script>', pos_script)

js_code = text[pos_script+8:pos_script_end]
print("JS length:", len(js_code))

with open('scratch/instruments_extracted.js', 'w', encoding='utf-8') as f_out:
    f_out.write(js_code)

print("Saved to scratch/instruments_extracted.js")
