import json

data = json.load(open('scratch/mock_state.json', encoding='utf-8'))
catalog = data.get('instrument_catalog', [])
print("Catalog categories count:", len(catalog))
for c in catalog:
    print(c.get('category'), c.get('selection_profile'), len(c.get('symbols', [])))
