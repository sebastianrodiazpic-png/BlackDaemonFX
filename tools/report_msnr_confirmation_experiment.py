"""Spanish, reviewable report of a completed experiment and actual coverage."""
import argparse
import json
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.fetch_msnr_confirmation_history import OUT, TF, save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-name', default='pilot_7d_all60')
    args = parser.parse_args()
    if Path(args.run_name).name!=args.run_name:
        parser.error('Invalid run name')
    directory = OUT/args.run_name
    run = json.loads((directory/'run.json').read_text())
    summary = json.loads((directory/'summary.json').read_text())
    manifest = json.loads((OUT/'confirmation_history_manifest.json').read_text())
    core = set(manifest['core_symbols'])
    historic = pd.read_csv(ROOT/'storage/analysis/replay_malaysian_snr_60_assets_2y_summary.csv')
    selected = historic[historic.symbol.isin(core)]
    rejected = historic[~historic.symbol.isin(core)]
    live = {'captured_at': datetime.now(timezone.utc).isoformat()}
    for name in ('settings', 'candidates'):
        try:
            with urllib.request.urlopen('http://127.0.0.1:8765/api/strategies/malaysian-snr/'+name, timeout=5) as response:
                live[name] = json.load(response)
        except (OSError, ValueError) as exc:
            live[name] = {'error': str(exc)}
    save_json(OUT/'live_reference_verified.json', live)
    preference = run['settings']
    lines = ['# Malaysian SNR: referencia DEMO y comparación de confirmaciones', '',
        'La configuración de referencia está aplicada en DEMO. M5 y el apoyo H4 continúan en observación en el bot. '
        'El experimento es offline y no envía órdenes ni activa activos descartados.', '',
        '## Configuración aplicada', '',
        f"- Versión de preferencias: {preference['version']}; estrategia: {run['strategy_version']}.",
        '- IA en Filtro; ante un modelo incompatible, Observar solo en DEMO. REAL conserva el bloqueo.',
        f"- Fractal H1: cuerpo {100*preference['fractal_min_body_ratio']:.0f}%; distancia {preference['fractal_max_entry_distance_atr']:.2f} ATR.",
        f"- Retest: {preference['retest_window_minutes']} minutos; recuperación: {preference['recovery_window_minutes']} minutos y cuerpo {100*preference['recovery_min_body_ratio']:.0f}%.",
        '- Selección operativa de Malaysian SNR: los 23 activos actuales. Los otros 37 se evalúan en una cohorte aparte.',
        '- Los controles siguen disponibles en /strategy-bases, pestaña Malaysian SNR; restaurar carga el formulario y Guardar aplica los valores.', '',
        '## Contraste de la auditoría adjunta', '',
        f"El CSV histórico reproduce {int(selected.trades_augmented.sum())} operaciones y {selected.total_r_augmented.sum():+.2f} R para los 23 activos. "
        f"Su WinRate ponderado, usando porcentajes redondeados del CSV, es {(selected.trades_augmented*selected.wr_augmented).sum()/selected.trades_augmented.sum():.3f}%.", '',
        f"Para los 37 restantes, el archivo suma {rejected.total_r_augmented.sum():+.2f} R, frente a −189,7 R citados en el documento. "
        f"El conjunto de 60 suma {int(historic.trades_augmented.sum())} operaciones y {historic.total_r_augmented.sum():+.2f} R. "
        'Esta diferencia debe reconciliarse antes de usar el documento como certificación.', '',
        'La selección de 23 activos se hizo usando esos resultados históricos. Por tanto, el 43,7% no es una prueba independiente '
        'de las reglas actuales ni una garantía de resultados futuros.', '',
        'Además, el generador histórico disponible (tools/replay_malaysian_snr_full_universe.py) identifica setups '
        'usando el cierre H1, les asigna la hora de apertura H1 y empieza la simulación M15 desde esa hora. '
        'Eso puede incluir recorrido anterior a la disponibilidad de la señal. Sus runners de 2,5/3,5/5 R '
        'también difieren de los actuales. Sin una fuente causal congelada que respalde el CSV, sus cifras '
        'no deben considerarse una validación del bot actual.', '',
        '## Cobertura comprobada', '',
        f"Ventana solicitada: {manifest['requested_start']} a {manifest['requested_end']}. "
        f"Límite de MetaTrader observado: {manifest['maxbars']:,} barras. "
        f"Activos con inicio de dos años cubierto en todos los marcos: {sum(r.get('complete_two_year_start', False) for r in manifest['symbols'])}/60.", '',
        'No se reconstruye M5 desde M15. Cada archivo contiene velas nativas con una huella SHA-256. '
        'Una sola vela antigua devuelta por el terminal no cuenta como cobertura.', '',
        '| Activo operativo | Inicio M5 nativo | Inicio común de los cinco marcos |',
        '|---|---|---|']
    for row in manifest['symbols']:
        if row['cohort']=='core23':
            lines.append(f"| {row['symbol']} | {row['frames'].get('M5', {}).get('start', 'Sin datos')[:10]} | {(row.get('common_available_start') or 'Sin datos')[:10]} |")
    lines += ['', 'Para completar la comparación de dos años falta ampliar el historial M5 nativo desde octubre de 2024 '
        'y volver a capturar los datos. Un límite de 500.000 barras permite solicitar esa cantidad, pero no garantiza '
        'que el broker conserve toda la historia. Step Index 400 y Volatility 90 también tienen comienzos posteriores '
        'en los otros marcos y deben conservar su etiqueta de cobertura parcial.', '',
        'El nuevo límite requiere reiniciar la plataforma, según '
        '[la documentación de MetaTrader](https://www.metatrader5.com/en/terminal/help/startworking/settings). '
        'Ese reinicio no se realizó: otras estrategias mantienen posiciones abiertas.', '',
        'El control de MetaTrader se detuvo con Escape; no se cambió ese límite ni se reinició el terminal.', '',
        '## Piloto ejecutado', '',
        f"Período común: {summary['requested_start']} a {summary['requested_end']}. "
        f"Procesados: {summary['symbols_completed']}/60; errores: {len(summary['failed_symbols'])}.", '',
        '| Variante | Cohorte | Cerrados | WinRate estimado | R por operación | PF | Ambiguos | Censurados |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    def display(value, suffix=''):
        return 'Sin muestra' if value is None else f'{value:.3f}{suffix}'
    for key, result in summary['groups'].items():
        m = result['conservative_ohlc']
        variant_key = key.rsplit('_core23', 1)[0] if key.endswith('_core23') else key.rsplit('_historically_pruned37', 1)[0]
        variant_label = {'M15': 'M15 actual', 'M15_M5': 'M15 + M5', 'M15_H4': 'M15 + H4 neutral'}[variant_key]
        lines.append(f"| {variant_label} "
            f"| {'23 operativos' if key.endswith('_core23') else '37 descartados'} | {m['trades']} | {display(m['win_pct'], '%')} "
            f"| {display(m['expectancy_r'])} | {display(m['profit_factor']) if m['profit_factor'] is not None else '—'} | {result['ambiguous']} | {result['censored']} |")
    lines += ['', 'Estas cifras son un piloto corto sobre velas OHLC y spread histórico aproximado. '
        'No acreditan un incremento sostenido de WinRate ni sustituyen los dos años solicitados. '
        'Los intervalos Wilson del JSON son descriptivos y no corrigen la dependencia entre operaciones.', '',
        'Se conservan una posición por símbolo y la deduplicación del episodio H1; la confirmación M15 tiene prioridad '
        'si M15 y M5 coinciden. El fill se toma de la apertura M5, con spread de la última vela cerrada. '
        'La simulación divide el riesgo 50/50, apunta a 2R y un runner contextual hasta 4R, y mueve el runner a BE '
        'más spread de TP1 y dos puntos. Una colisión intrabar se cuenta de forma conservadora y se etiqueta ambigua; '
        'huecos y finales sin resolución se censuran.', '',
        'Comisiones, swaps, deslizamiento, redondeo a tick, distancia mínima de stop y límites agregados de cartera '
        'no están reproducidos. Se publican sensibilidades de coste adicional de 0,05 R y 0,10 R. '
        'Ningún resultado de este replay se incorpora como etiqueta de entrenamiento verificada.', '',
        '## Estado observado del bot', '']
    funnel = live.get('candidates', {}).get('funnel', {})
    if funnel:
        lines += [f"Candidatos únicos: {funnel.get('unique_setups')}; lecturas: {funnel.get('evaluations')}; "
                  f"confirmados: {funnel.get('confirmed')}; ejecutados: {funnel.get('executed')}. "
                  'El WinRate operativo aún no tiene muestra.', '',
                  '| Último bloqueo del candidato | Candidatos |', '|---|---:|']
        for block in funnel.get('blockers', []):
            lines.append(f"| {block['last_reason']} | {block['count']} |")
        lines += ['', 'Estos son estados actuales de candidatos únicos; no son conteos de pérdidas ni pruebas '
                       'de que quitar un filtro mejore la calidad.']
    lines += ['', '## Validación y siguiente decisión', '',
        '- 63 pruebas pasan: causalidad, ejecución, cierre de velas, M5, H4, persistencia y política IA.',
        '- Paridad contra la estrategia sin cachés verificada en XAGUSD: señales y motivos idénticos, incluida una entrada M5.',
        '- Las preferencias y el código del experimento quedan congelados con sus huellas; no se reutilizan checkpoints con otras reglas.',
        '- No se promovió M5, H4 ni ninguno de los 37 descartados a operación automática.', '',
        'Antes de promover una variante: completar la cobertura; dividir el período cronológicamente; evaluar las nuevas '
        'operaciones y los episodios compartidos; contrastar expectativa, PF, drawdown, costes y WinRate por familia '
        'con incertidumbre que respete la agrupación temporal; confirmar después en DEMO con costes de ejecución reales. '
        'Una variante con más entradas y expectativa negativa debe seguir en observación.', '',
        'Archivos: confirmation_history_manifest.json; live_reference_verified.json; parity_verification.json; '
        f'{args.run_name}/run.json, summary.json y trades.csv, dentro de storage/analysis/msnr_v27_m5_reference_20261012.', '',
        'Referencia técnica del límite de históricos y tiempos UTC: '
        '[MetaTrader 5 copy_rates_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).']
    text = '\n'.join(lines)
    path = ROOT/'MSNR_REFERENCIA_DEMO_Y_REPLAY_20261012.md'
    temp = path.with_suffix('.md.tmp')
    temp.write_text(text, encoding='utf-8')
    temp.replace(path)
    print(json.dumps({'report': str(path), 'symbols': summary['symbols_completed'], 'complete': summary['symbols_completed']==60}))


if __name__=='__main__':
    main()
