with open('storage/analysis/replay_5y_perfect_strategy_bases.csv', 'r', encoding='utf-8') as f:
    lines = [f.readline() for _ in range(3)]

print('Header columns count:', len(lines[0].strip().split(',')))
print('Header:', lines[0].strip())
print('Row 1 columns count:', len(lines[1].strip().split(',')))
print('Row 1:', lines[1].strip())
