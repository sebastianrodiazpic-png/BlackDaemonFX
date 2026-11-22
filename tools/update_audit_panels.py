# -*- coding: utf-8 -*-
"""
Script para sincronizar los textos explicativos y badges de los paneles de auditoría
(triMotorAuditPanel, msnrAuditPanel, orbAuditPanel, ictAuditPanel, trendPullbackAuditPanel)
en dashboard/strategy_bases_page.py con los datos exactos de Confluencia Tripartita.
"""
import sys

def main():
    with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Actualizar título y texto de ictAuditPanel
    # Antes: +3,712.44 R Netos (73 Instrumentos · 34,325 Trades)
    # 51 Activos Rentables (WR ≥ 50%) · 22 Podados Preventivamente
    old_ict_header = 'Auditoría Replay Fiel 5 Años ICT: +3,712.44 R Netos (73 Instrumentos · 34,325 Trades)'
    new_ict_header = 'Auditoría Replay Fiel 5 Años ICT (Confluencia Tripartita): +8,038.81 R Netos (73 Instrumentos · 37,918 Trades)'
    
    old_ict_badge = 'Replay Fiel 5 Años · 51 Activos Rentables (WR ≥ 50%) · 22 Podados Preventivamente · 73 Instrumentos Evaluados'
    new_ict_badge = 'Confluencia Tripartita 5A · 59 Activos Rentables (WR ≥ 50%) · 14 Podados Preventivamente · 73 Instrumentos Evaluados'

    content = content.replace(old_ict_header, new_ict_header)
    content = content.replace(old_ict_badge, new_ict_badge)

    # Reemplazo de la mención de Crash 300 en ICT:
    # `Crash 300` (rescatado <strong>+35.5R, 60.85% WR</strong>, PF 1.48, t=+2.50, 3/3 años +)
    old_c300_ict = '<code>Crash 300</code> (rescatado <strong>+35.5R, 60.85% WR</strong>, PF 1.48, t=+2.50, 3/3 años +)'
    new_c300_ict = '<code>Crash 300</code> (optimizado Confluencia Tripartita <strong>+170.34R, 66.98% WR</strong>, 430 trades, 3/3 años +)'
    content = content.replace(old_c300_ict, new_c300_ict)

    # Reemplazo de Crash 1000 en ICT sintéticos:
    # Antes: `Crash 1000` (44.60% WR, -27.5R)
    # Con Tripartita, Crash 1000 fue REHABILITADO con 814 trades, 55.41% WR, +86.18 R
    old_c1000_poda = '<code>Crash 1000</code> (44.60% WR, -27.5R)'
    new_c1000_rehab = '<code>Crash 1000</code> (rehabilitado con IA: <strong>+86.18R, 55.41% WR</strong>, 814 trades)'
    content = content.replace(old_c1000_poda, new_c1000_rehab)

    # Reemplazo del párrafo descriptivo en ICT
    old_ict_desc = '<strong>51 activos resultan netamente rentables acumulando 34,325 trades tomados, 55.14% de Win Rate y +3,712.44 R netos</strong> bajo el contrato de 2 patas. Los <strong>22 activos con Win Rate < 50% o expectativa negativa quedan en PODA PREVENTIVA</strong> (como Crash 1000, Volatility 90 1s, High Frequency Vol 50/100 y cruces FX con bajo volumen en Londres).'
    new_ict_desc = '<strong>59 activos resultan netamente rentables acumulando 37,918 trades tomados, 60.45% de Win Rate ponderado y +8,038.81 R netos</strong> bajo el filtro activo de Confluencia Tripartita (Estrategia SMC + Criterio Humano + Filtro Activo de IA). Crash 300 alcanza <strong>430 trades con 66.98% de Win Rate y +170.34 R</strong>, y activos como Crash 1000 fueron rehabilitados (+86.18 R, 55.41% WR). Solo <strong>14 activos de baja liquidez quedan en PODA PREVENTIVA</strong>.'
    content = content.replace(old_ict_desc, new_ict_desc)

    # 2. Actualizar triMotorAuditPanel badge
    old_tri_badge = 'Replay Fiel 5 Años · 156 Activos Rentables · 136 Podados Preventivamente · 292 Registros Verificados'
    new_tri_badge = 'Confluencia Tripartita 5A · 177 Activos Rentables (+26 Rehabilitados) · 115 Podados Preventivamente · 292 Registros Verificados'
    content = content.replace(old_tri_badge, new_tri_badge)

    # 3. Actualizar orbAuditPanel
    old_orb_header = 'Auditoría Replay Fiel 5 Años ORB New York SWEEP: +177.12 R Netos en Mercados de Sesión'
    new_orb_header = 'Auditoría Replay Fiel 5 Años ORB New York SWEEP (Confluencia Tripartita): +482.53 R Netos en Mercados de Sesión'
    old_orb_badge = 'Replay Fiel 5 Años · 11 Activos Élite (WR ≥ 50%) · 24 Podados en Forex/Metales/Índices · 38 Sintéticos Descartados'
    new_orb_badge = 'Confluencia Tripartita 5A · 17 Activos Rentables (+6 Rehabilitados con IA) · 18 Podados FX · 38 Sintéticos Descartados Estructuralmente'
    content = content.replace(old_orb_header, new_orb_header)
    content = content.replace(old_orb_badge, new_orb_badge)

    # 4. Actualizar mención en Trend Pullback líder
    # Crash 300 (+86.25 R, 60.1% WR) -> Crash 300 (+120.60 R, 72.98% WR con Tripartita)
    old_tp_c300 = 'Crash 300 (+86.25 R, 60.1% WR)'
    new_tp_c300 = 'Crash 300 (+120.60 R, 66.67% WR)'
    content = content.replace(old_tp_c300, new_tp_c300)

    with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Actualización de paneles completada exitosamente.")

if __name__ == '__main__':
    main()
