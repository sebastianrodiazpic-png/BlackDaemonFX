with open('strategy/ai/model_inventory.py', 'r', encoding='utf-8') as f:
    text = f.read()
new_text = text.replace('"strategy": "ICT Sabri Malle"', '"strategy": "ICT"')
with open('strategy/ai/model_inventory.py', 'w', encoding='utf-8') as f:
    f.write(new_text)
print('model_inventory.py updated. Replaced:', text.count('"strategy": "ICT Sabri Malle"'))
