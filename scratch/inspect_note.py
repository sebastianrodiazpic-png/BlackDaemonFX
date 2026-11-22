with open('scratch/instruments_full.html', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find("profileNote")
print(text[pos:pos+3000])
