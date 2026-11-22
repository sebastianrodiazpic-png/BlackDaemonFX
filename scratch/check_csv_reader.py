import csv

with open('storage/analysis/replay_5y_perfect_strategy_bases.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if len(row) != 39:
            print(f'Row {i} has {len(row)} columns')
            break
    else:
        print('All existing rows have exactly 39 columns!')
