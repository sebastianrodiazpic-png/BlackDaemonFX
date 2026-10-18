"""Atomic installation of research criteria and the in-page action guide."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def change(name, edits):
    path = ROOT/name
    source = path.read_text(encoding='utf-8')
    for before, after in edits:
        if source.count(before)!=1:
            raise ValueError(f'{name}: expected exactly one edit anchor: {before[:80]}')
        source=source.replace(before,after)
    temporary=path.with_name(path.name+'.guided.tmp')
    temporary.write_text(source,encoding='utf-8')
    os.replace(temporary,path)

change('strategy/malaysian_snr/runtime_settings.py', [
    ("    'research_min_resolved_trades': 30,", "    'research_min_resolved_trades': 30,\n    'research_min_win_rate_improvement_pp': 0.0,"),
    ("        elif key in ('continuation_maximum_breakout_wick_ratio', 'research_min_frequency_ratio'):",
     "        elif key in ('research_min_frequency_ratio', 'research_min_win_rate_improvement_pp'):\n            upper = 5 if key=='research_min_frequency_ratio' else 100\n            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=upper:\n                raise ValueError('Objetivo de comparación fuera de rango: frecuencia 0–500% y mejora WinRate 0–100 puntos')\n            value=float(value)\n        elif key == 'continuation_maximum_breakout_wick_ratio':")])
change('strategy/malaysian_snr/ai_policy.py', [
    ("'research_min_frequency_ratio', 'research_min_resolved_trades'}", "'research_min_frequency_ratio', 'research_min_resolved_trades',\n        'research_min_win_rate_improvement_pp'}")])
change('strategy/malaysian_snr/research_comparison.py', [
    ("    base_total=sum(float(r['rr']) for r in base)",
     "    base_win_rate=100*sum(float(r['rr'])>0 for r in base)/len(base) if base else None\n    trial_win_rate=100*sum(float(r['rr'])>0 for r in trial)/len(trial) if trial else None\n    win_rate_delta=trial_win_rate-base_win_rate if base_win_rate is not None and trial_win_rate is not None else None\n    if win_rate_delta is None:\n        reasons.append('MISSING_COMPARABLE_WIN_RATE')\n    elif win_rate_delta+1e-10<settings.get('research_min_win_rate_improvement_pp',0.):\n        reasons.append('WIN_RATE_IMPROVEMENT_BELOW_TARGET')\n    base_total=sum(float(r['rr']) for r in base)"),
    ("        'frequency_preserved':frequency,", "        'baseline_win_rate_pct':base_win_rate,'candidate_win_rate_pct':trial_win_rate,\n        'win_rate_improvement_pp':win_rate_delta,'required_win_rate_improvement_pp':settings.get('research_min_win_rate_improvement_pp',0.),\n        'frequency_preserved':frequency,")])
change('dashboard/msnr_settings_panel.py', [
    ('"""Editable Malaysian SNR controls and reversible loading of reference defaults."""',
     '"""Editable Malaysian SNR controls and reversible loading of reference defaults."""\nfrom dashboard.msnr_action_guide import GUIDE_HTML, GUIDE_JS'),
    ('id="msnrResearchFrequency" type="number" min="0" max="100"', 'id="msnrResearchFrequency" type="number" min="0" max="500"'),
    ('<label for="msnrResearchFrequency">Frecuencia mínima conservada al comparar (%)</label>', '<label for="msnrResearchFrequency">Frecuencia mínima frente a la base (%)</label>'),
    ('<div class="msnr-field"><label for="msnrResearchSample">', '<div class="msnr-field"><label for="msnrResearchWinRate">Mejora mínima de WinRate (puntos porcentuales)</label><input id="msnrResearchWinRate" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>\n      <div class="msnr-field"><label for="msnrResearchSample">'),
    ("  research_min_resolved_trades:['msnrResearchSample','number'],", "  research_min_resolved_trades:['msnrResearchSample','number'],\n  research_min_win_rate_improvement_pp:['msnrResearchWinRate','number'],"),
    ("  if(remember) msnrSavedSettings=settings;", "  if(remember) { msnrSavedSettings=settings; renderMsnrActionGuide(settings); }"),
    ("'Comparación: frecuencia mínima 80%, muestra mínima de 30 resultados resueltos. Sin promoción automática.',", "'Comparación por defecto: frecuencia mínima 80%, mejora WinRate 0 puntos (sin deterioro), muestra mínima de 30 resultados resueltos. Sin promoción automática.',")])
path=ROOT/'dashboard/msnr_settings_panel.py'
source=path.read_text(encoding='utf-8')
source += "\nPANEL_HTML = PANEL_HTML.replace('  <fieldset><legend>Fractal y contexto</legend>', GUIDE_HTML+'\\n  <fieldset><legend>Fractal y contexto</legend>')\nPANEL_JS = GUIDE_JS + PANEL_JS\n"
temporary=path.with_name(path.name+'.guided.tmp')
temporary.write_text(source,encoding='utf-8');os.replace(temporary,path)
print('Installed guide and comparison controls')
