with open('storage/logs/bots/jump.log', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    start = max(0, 297135 - 100)
    end = 297135 + 20
    for i in range(start, end):
        if any(k in lines[i] for k in ['ORDEN', 'ORDER', 'EJECUC', 'EXEC', 'Ticket', 'ticket', '478285', 'Jump 10']):
            print(f"{i+1}: {lines[i].strip()}")
