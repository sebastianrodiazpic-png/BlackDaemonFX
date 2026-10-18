"""
scratch/compute_wilson_sample_size.py
Cálculo riguroso de intervalos de confianza de Wilson y tamaños de muestra mínimos
para respaldar estadísticamente una tasa de acierto de 60-70% con significancia p < 0.05.
"""

import numpy as np

def wilson_interval(k, n, z=1.95996):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (center - margin, center + margin)

def min_sample_for_lower_bound(target_p, lower_target=0.55, z=1.95996):
    # Find minimum n such that Wilson lower bound >= lower_target when observed p = target_p
    for n in range(10, 1000):
        k = int(round(n * target_p))
        low, high = wilson_interval(k, n, z)
        if low >= lower_target:
            return n, k, low, high
    return None

def main():
    print("=" * 80)
    print("ANÁLISIS ESTADÍSTICO DE SIGNIFICANCIA PARA LA META DE 60-70% DE EFECTIVIDAD")
    print("=" * 80)
    
    # Current candidate: N=40, k=20 (50.0%)
    low40, high40 = wilson_interval(20, 40)
    print(f"Candidato Actual (N=40, W=20):")
    print(f"  Win Rate Observado: 50.0%")
    print(f"  IC Wilson al 95%:   [{low40*100:.1f}%, {high40*100:.1f}%]")
    print(f"  Incertidumbre:      Margen de error de +/- { (high40 - low40)/2 * 100:.1f} puntos porcentuales.\n")

    # If observed win rate were 60% with N=40
    low40_60, high40_60 = wilson_interval(24, 40)
    print(f"Escenario Hipotético N=40 con 60.0% (24 wins):")
    print(f"  IC Wilson al 95%:   [{low40_60*100:.1f}%, {high40_60*100:.1f}%]")
    print(f"  Conclusión:         El límite inferior ({low40_60*100:.1f}%) incluye 44.7%, por lo que N=40 NO descarta que el sistema sea inferior a 50%.\n")

    # Minimum sample sizes to confirm true edge > 50% and edge >= 55%
    for obs_p in [0.60, 0.65, 0.70]:
        n_50, k_50, l_50, h_50 = min_sample_for_lower_bound(obs_p, lower_target=0.50)
        n_55, k_55, l_55, h_55 = min_sample_for_lower_bound(obs_p, lower_target=0.55)
        print(f"Para Tasa Observada = {obs_p*100:.0f}%:")
        print(f"  • Mínimo N para descartar aleatoriedad (>50% al 95% conf): N={n_50:3d} ({k_50} wins) -> IC [{l_50*100:.1f}%, {h_50*100:.1f}%]")
        print(f"  • Mínimo N para confirmar ventaja robusta (>=55% al 95% conf): N={n_55:3d} ({k_55} wins) -> IC [{l_55*100:.1f}%, {h_55*100:.1f}%]")

if __name__ == '__main__':
    main()
