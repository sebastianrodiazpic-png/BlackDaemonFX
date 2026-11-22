with open('scratch/instruments_full.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = 0
while True:
    pos = text.find("selectedCount", pos)
    if pos == -1:
        break
    print(f"Found at {pos}:")
    print(text[max(0, pos-100):min(len(text), pos+300)])
    print("="*40)
    pos += 13
