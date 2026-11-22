with open('scratch/instruments_full.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos1 = text.find("profileNote")
pos2 = text.find("profileNote", pos1 + 20)
print(f"Pos 2: {pos2}")
print(text[pos2:pos2+1500])
