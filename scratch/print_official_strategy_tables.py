import pandas as pd

df = pd.read_csv('storage/analysis/comparativa_oficial_criterio_humano_activos_rentables.csv')
with open('scratch/full_strategy_breakdown.txt', 'w', encoding='utf-8') as out:
    for strat, group in df.groupby('strategy', sort=False):
        out.write(f'=== STRATEGY: {strat} ({len(group)} activos) ===\n')
        sorted_group = group.sort_values(by='wr_despues', ascending=False)
        for _, r in sorted_group.iterrows():
            out.write(f"  {r['symbol']}: Estrategia={r['wr_antes']}% | Con Criterio={r['wr_despues']}% | Retorno={r['r_despues']}R\n")
        out.write('\n')

print('Done writing scratch/full_strategy_breakdown.txt')
