import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def change(name, edits):
    path=ROOT/name;source=path.read_text(encoding='utf-8')
    for before,after in edits:
        if source.count(before)!=1:raise ValueError(f'{name}: ambiguous anchor {before[:70]}')
        source=source.replace(before,after)
    temporary=path.with_name(path.name+'.step-control.tmp')
    temporary.write_text(source,encoding='utf-8');os.replace(temporary,path)

change('strategy/execution/live_trading_engine.py', [
    ('        min_adx = float(getattr(self.config, "step_min_adx", 25.0))\n        if is_step_worker:',
     '''        min_adx = float(getattr(self.config, "step_min_adx", 25.0))
        snr_step = (str(self.config.bot_profile or '').upper()=='MALAYSIAN_SNR'
            and str(signal.get('strategy_name') or '').upper()=='MALAYSIAN_SNR')
        if snr_step:
            from strategy.malaysian_snr.universe import resolve_symbol_settings
            import math
            try:
                controls=(analysis or {}).get('runtime_controls') or self.malaysian_snr_strategy.settings_snapshot()
                controls=resolve_symbol_settings(controls,symbol)
                min_adx=float(controls['step_min_adx'])
            except Exception:
                return {'symbol':str(symbol),'action':'MSNR_SETTINGS_UNAVAILABLE',
                    'reason':'MSNR_STEP_EXECUTION_SETTINGS_UNAVAILABLE'}
            if adx is None or not math.isfinite(float(adx)) or float(adx)<min_adx:
                return {'symbol':str(symbol),'action':'STEP_ADX_LOW',
                    'reason':'MSNR_STEP_EXECUTION_ADX_BELOW_MINIMUM',
                    'adx':float(adx) if adx is not None and math.isfinite(float(adx)) else None,
                    'min_adx':min_adx,'adx_timeframe':signal.get('structure_timeframe'),
                    'runtime_settings_version':controls.get('version')}
            signal['step_execution_quality']={'minimum_adx':min_adx,'captured_adx':float(adx),
                'runtime_settings_version':controls.get('version')}
        if is_step_worker:''')])
# The generic branch must not apply the legacy 25 a second time to SNR.
change('strategy/execution/live_trading_engine.py', [
    ('        elif adx is not None and float(adx) < min_adx:\n            return {\n                "symbol": str(symbol),\n                "action": "STEP_ADX_LOW",',
     '        elif not snr_step and adx is not None and float(adx) < min_adx:\n            return {\n                "symbol": str(symbol),\n                "action": "STEP_ADX_LOW",')])

change('dashboard/msnr_settings_panel.py', [
    ('  <fieldset><legend>Recuperación selectiva por activo</legend>',
     '''  <fieldset><legend>Filtro de ejecución Step para Malaysian SNR</legend>
    <div class="msnr-field"><label for="msnrStepExecutionAdx">ADX mínimo de ejecución Step SNR</label><input id="msnrStepExecutionAdx" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
    <p class="muted msnr-help">Referencia 25. Es el filtro adicional del motor para Step: la señal SNR puede traer ADX H1. Cada Step puede sobrescribirlo abajo; vacío hereda este valor. No cambia los otros motores ni elimina el ADX de formación de Continuación.</p>
  </fieldset>
  <fieldset><legend>Recuperación selectiva por activo</legend>'''),
    ('      details.appendChild(line);',
     '''      if(row.symbol.startsWith('Step Index')) {
        const field=document.createElement('div');field.className='msnr-field';
        const input=document.createElement('input');input.id='msnrAssetAdx'+row.i;input.type='number';input.min='0';input.max='100';input.step='any';input.placeholder='Heredar ADX general';input.oninput=markMsnrSettingsChanged;
        const label=document.createElement('label');label.htmlFor=input.id;label.textContent='ADX de ejecución · '+row.symbol;field.append(label,input);line.appendChild(field);
      }
      details.appendChild(line);'''),
    ('const msnrFields = {',"const msnrFields = {\n  step_min_adx:['msnrStepExecutionAdx','number'],"),
    ('  return values;\n}\nfunction msnrFormValid',
     '''  values.step_symbol_min_adx={};
  msnrAssetCatalog.forEach((row,i)=>{const input=document.getElementById('msnrAssetAdx'+i);if(input?.value.trim()) values.step_symbol_min_adx[row.symbol]=input.valueAsNumber;});
  return values;
}
function msnrFormValid'''),
    ("  return Object.entries(msnrFields).every(([key,[id,type]]) =>", "  return Array.from(document.querySelectorAll('[id^=msnrAssetAdx]')).every(input=>!input.value.trim() || Number.isFinite(input.valueAsNumber) && input.checkValidity()) && Object.entries(msnrFields).every(([key,[id,type]]) =>"),
    ("  for(const [key,prefix] of [['asset_modes','msnrAssetMode'],['m5_symbol_modes','msnrAssetM5'],['continuation_symbol_modes','msnrAssetContinuation']])\n    msnrAssetCatalog.forEach((row,i)=>document.getElementById(prefix+i).value=settings[key]?.[row.symbol] || 'inherit');",
     "  for(const [key,prefix] of [['asset_modes','msnrAssetMode'],['m5_symbol_modes','msnrAssetM5'],['continuation_symbol_modes','msnrAssetContinuation']])\n    msnrAssetCatalog.forEach((row,i)=>document.getElementById(prefix+i).value=settings[key]?.[row.symbol] || 'inherit');\n  msnrAssetCatalog.forEach((row,i)=>{const input=document.getElementById('msnrAssetAdx'+i);if(input) input.value=settings.step_symbol_min_adx?.[row.symbol] ?? '';});"),
    ("    'Continuación por defecto: Operar, distancia 0,50 ATR H1, mecha máxima 25%. Quasimodo: distancia 0,50 ATR H1.',",
     "    'ADX de ejecución Step SNR: 25; por activo Heredar, sin excepciones.',\n    'Continuación por defecto: Operar, distancia 0,50 ATR H1, mecha máxima 25%. Quasimodo: distancia 0,50 ATR H1.',")])
print('Step SNR execution ADX controls installed')
