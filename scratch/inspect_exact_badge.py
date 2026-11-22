with open('scratch/instruments_full.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('let badge = isPruned')
pos_end = text.find('const selectiveAllowed = Boolean(', pos)
print("--- EXACT ORIGINAL REGION ---")
print(text[pos:pos_end])
print("--- END ---")
