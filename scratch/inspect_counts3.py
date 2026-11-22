with open('scratch/instruments_full.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = 0
while True:
    pos = text.find("updateCount", pos)
    if pos == -1:
        break
    print(f"Found at {pos}:")
    print(text[max(0, pos-80):min(len(text), pos+120)])
    print("="*40)
    pos += 11
