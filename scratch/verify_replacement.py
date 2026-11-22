with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos_start = text.find('_INSTRUMENTS_HTML = r\'\'\'')
end_quote = text.find("'''\n\n\n\n\n\n\n\n_HTML = with_page_loading(_HTML)", pos_start)

print(f"Start pos: {pos_start}")
print(f"End quote pos: {end_quote}")
print("Checking matching length...")
orig_sub = text[pos_start:end_quote]
print(f"Original length: {len(orig_sub)}")

with open('scratch/instruments_new.html', 'r', encoding='utf-8') as f:
    new_sub = f.read()

print(f"New length: {len(new_sub)}")
