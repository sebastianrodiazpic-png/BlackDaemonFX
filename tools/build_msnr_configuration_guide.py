"""Build the complete user guide from the exact exported SNR settings."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dashboard.msnr_action_guide import ACTION_GUIDE
from strategy.malaysian_snr.research_comparison import compare_samples
from tools.replay_msnr_confirmations import stats

OUT=ROOT/'storage/analysis/msnr_configuracion_guiada_20261012'
RUN=ROOT/'storage/analysis/msnr_v27_m5_reference_20261012/steps_v28_30d_current'
MODE={'off':'Desactivado','shadow':'Observación','live':'Operar','filter':'Filtro compatible',
    'observe':'Observar solo DEMO','block':'Bloquear','body_turns':'Giro de cuerpos',
    'engulfing':'Envolvente','d1_structure':'Estructura D1','h4_structure':'Estructura H4',
    'd1_h4_structure':'Confluencia D1/H4'}

def value(key,item):
    if isinstance(item,bool):return 'Activado' if item else 'Desactivado'
    if isinstance(item,list):return ', '.join(item) or 'Sin activos'
    if isinstance(item,dict):return '<br>'.join(f'{symbol}: {MODE.get(mode,str(mode))}' for symbol,mode in item.items()) or 'Heredar, sin excepciones'
    if key=='research_min_win_rate_improvement_pp':return f'{item:g} puntos porcentuales'
    if 'ratio' in key or key.startswith('ai_min_probability'):return f'{item*100:g}%'
    return MODE.get(item,str(item))

def main():
    exported=json.loads((OUT/'settings_after.json').read_text(encoding='utf-8-sig'))
    settings=exported['settings']
    step_symbols=('Step Index','Step Index 200','Step Index 400','Step Index 500')
    symbols=(*step_symbols,'Crash 600 Index','Crash 1000 Index')
    crash_run=ROOT/'storage/analysis/msnr_v27_m5_reference_20261012/crash_v28_30d_current'
    results=[json.loads(((RUN if symbol in step_symbols else crash_run)/(symbol.replace(' ','_')+'.json')).read_text()) for symbol in symbols]
    if any(result.get('error') for result in results):raise ValueError('Replay has failed assets; document the errors explicitly')
    variants=('M15','M15_M5','M15_H4')
    all_records={variant:[trade for result in results for trade in result['variants'][variant]['trades']] for variant in variants}
    assessment={symbol:{variant:compare_samples(result['variants']['M15']['trades'],result['variants'][variant]['trades'],settings,
        same_window_and_feed=True) for variant in variants[1:]} for symbol,result in zip(symbols,results)}
    assessment['combined']={variant:compare_samples(all_records['M15'],all_records[variant],settings,same_window_and_feed=True) for variant in variants[1:]}
    selective=[]
    for result in results:
        symbol=result['symbol']
        if settings.get('asset_modes',{}).get(symbol)=='shadow':continue
        mode=settings.get('m5_symbol_modes',{}).get(symbol,settings['m5_confirmation_mode'])
        selective.extend(result['variants']['M15_M5' if mode=='live' else 'M15']['trades'])
    all_records['PERFIL_SELECTIVO']=selective
    assessment['combined']['PERFIL_SELECTIVO']=compare_samples(all_records['M15'],selective,settings,same_window_and_feed=True)
    (OUT/'steps_30d_reassessment.json').write_text(json.dumps(assessment,indent=2,ensure_ascii=False),encoding='utf-8')
    baseline=json.loads((OUT/'settings_before.json').read_text(encoding='utf-8-sig'))['settings']
    actual_before=[]
    for result in results:
        mode=baseline.get('m5_symbol_modes',{}).get(result['symbol'],baseline['m5_confirmation_mode'])
        actual_before.extend(result['variants']['M15_M5' if mode=='live' else 'M15']['trades'])
    all_records['BASE_GUARDADA_V12']=actual_before
    assessment['combined']['PERFIL_VS_CONFIGURACION_ANTERIOR']=compare_samples(actual_before,selective,settings,same_window_and_feed=True)
    (OUT/'steps_30d_reassessment.json').write_text(json.dumps(assessment,indent=2,ensure_ascii=False),encoding='utf-8')
    changes={key:{'before':baseline.get(key),'after':item} for key,item in settings.items() if key not in ('version','updated_at') and item!=baseline.get(key)}
    (OUT/'configuration_changes.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False),encoding='utf-8')
    live_m5=', '.join(symbol for symbol,mode in settings['m5_symbol_modes'].items() if mode=='live') or 'ninguno'
    shadow_step_m5=', '.join(symbol for symbol in step_symbols if settings['m5_symbol_modes'].get(symbol)=='shadow') or 'ninguno'
    text=f'''# Malaysian SNR: configuraciones para ampliar entradas y evaluar su efectividad

Configuración guardada el {settings['updated_at']}, versión {settings['version']}. Esta guía documenta los valores aplicados, no una promesa de WinRate. Está disponible también dentro de `/strategy-bases`, pestaña Malaysian SNR, en **Guía de cada acción**.

## Qué quedó aplicado

La versión 12 ya tenía los cuatro Step con activo, Continuación y M5 en Operar. El perfil conserva M5 en Operar para **{live_m5}**. El modo general M5 permanece en Observación. Se expuso el filtro adicional de ejecución de Step, con referencia general 25 y excepción **23 solo para Step Index**. Los otros Step siguen en 25. Esto no altera los motores STEP o SYNTHETICS. Es una hipótesis DEMO elegida después de observar estos datos; no existe validación independiente de ventaja. Continuación, A/V ampliado, cambio de función, QM ampliado y Open–Close mantienen sus modos Operar previos. Se conservaron Fractal 45%, distancias de 0,50 ATR H1, mecha de 25%, ADX de formación 20, recuperación de 35% y ventanas de 90/45 minutos.

Se añadieron a Observación Volatility 15 Index, Volatility 75 (1s) Index, CADCHF, USDCAD y CHFJPY. Son candidatos con algún resultado positivo en la prueba anterior de siete días, con muestras de solo una o dos operaciones; eso no justifica habilitar sus órdenes. Sus controles M5 quedaron explícitamente en Observación. Los otros siete recuperados que seguían en Observación se conservaron; Step 500 ya había sido pasado a Operar. El catálogo permite cambiar el modo de cualquiera de los 60 instrumentos sin modificar código.

Se ajustaron los criterios de investigación para exigir conjuntamente **105% de las entradas de la base, mejora de WinRate de al menos un punto porcentual, 50 resultados resueltos por variante, expectativa positiva y beneficio total superior**. La frecuencia admite objetivos superiores al 100%. Un punto porcentual significa, por ejemplo, pasar del 40% al 41%, no una mejora relativa del 1%. Estos criterios no filtran las órdenes actuales ni activan variantes automáticamente.

No se flexibilizaron cuerpo, mecha, retest o distancia. La relajación elegida afecta exclusivamente el ADX adicional de Step Index. La primera comparación sin filtros compartidos sugería apagar M5 en Step 400, pero al aplicar el filtro del motor esa conclusión cambió: algunos candidatos M15 favorables también estaban bloqueados. Por eso se conservaron los modos M5 existentes. Ninguno de los cuatro perfiles de expansión Crash cumplió todos los objetivos; M5 de Crash permanece en observación. Todos los perfiles comparados figuran en `configuration_candidates.json`, incluidos los desfavorables. La selección del umbral 23 es retrospectiva y debe probarse en fechas nuevas.

## Resultado de la comprobación de 30 días

Período: **11 de septiembre de 2026, 00:00 UTC, a 11 de octubre de 2026, 00:00 UTC**. Cuatro Step y dos Crash. Es una muestra parcial de seis instrumentos; no representa todos los activos ni la cartera del bot. Los resultados corresponden a la configuración operativa de la versión 12; los criterios nuevos no cambian la formación de sus entradas. Cada variante reutiliza el mismo feed, período y configuración base. M5 y la alternativa H4 son hipótesis del replay, no órdenes enviadas. BASE_GUARDADA_V12 usa M5 en los cuatro Step y M15 en los dos Crash. La fila de modos aplicados conserva esa selección y por eso da el mismo resultado en la capa SNR: esta tabla omite el filtro adicional de ejecución Step. El efecto del ajuste ADX 23 se comprueba en el diagnóstico siguiente.

| Variante | Entradas simuladas | Resueltas | Incompletas | WinRate resuelto | Resultado en R |
|---|---:|---:|---:|---:|---:|
'''
    for variant in ('BASE_GUARDADA_V12',*variants,'PERFIL_SELECTIVO'):
        result=stats(all_records[variant]);m=result['conservative_ohlc']
        label='MODOS_APLICADOS_SIN_FILTRO_STEP' if variant=='PERFIL_SELECTIVO' else variant
        text+=f"| {label} | {len(all_records[variant])} | {m['trades']} | {result['censored']} | {m['win_pct']}% | {m.get('total_r',0):.5f}R |\n"
    text+='\n| Activo | Variante | Entradas | Resueltas | WinRate | Resultado R |\n|---|---|---:|---:|---:|---:|\n'
    for result in results:
        for variant in ('M15','M15_M5'):
            records=result['variants'][variant]['trades'];m=stats(records)['conservative_ohlc']
            text+=f"| {result['symbol']} | {variant} | {len(records)} | {m['trades']} | {m['win_pct']}% | {m.get('total_r',0):.5f}R |\n"
    text+='\nEvaluación con los objetivos actuales:\n\n'
    for symbol,comparisons in assessment.items():
        trial=comparisons['M15_M5']
        text+=f"- {symbol}: {'cumple los criterios aritméticos' if trial['research_checks_passed'] else 'no cumple'}; motivos: {', '.join(trial['reasons']) or 'ninguno'}. Sin promoción automática.\n"
    trial=assessment['combined']['PERFIL_VS_CONFIGURACION_ANTERIOR']
    sensitivity=stats(selective)['extra_cost_0_10r']
    text+=f"\nComparación de los modos de la capa SNR, todavía sin el filtro de ejecución Step: {'cumple' if trial['research_checks_passed'] else 'no cumple'}; motivos: {', '.join(trial['reasons']) or 'ninguno'}. Sensibilidad a coste adicional de 0,10R por resultado resuelto: {sensitivity.get('total_r',0):.5f}R. Esta comparación no mide el efecto del nuevo umbral ADX y el coste hipotético no sustituye costes de ejecución verificados.\n"
    text+='''
Un resultado favorable en este período sigue siendo investigación: las fechas se eligieron después de observar una semana contenida en ellas. No es un período independiente ni una validación de dos años. Las métricas se calculan sobre resultados resueltos; los incompletos y la ambigüedad impiden aprobar los criterios. El replay aproxima spread con datos históricos, no verifica todas las comisiones, slippage, swap, redondeos o límites simultáneos de cartera. También omite los filtros compartidos del ejecutor de Step y Boom/Crash: mide candidatos de la capa SNR, no reproduce todas las decisiones del motor en vivo. No se usa para entrenar modelos. Un WinRate alto con pérdida neta no satisface el objetivo.

## Diagnóstico del filtro de ejecución antes y después

Se reconstruyeron los candidatos ya capturados y se comprobaron los filtros reales de Step y Boom/Crash. Para Step Index, bajar el mínimo adicional de 25 a 23 hace pasar cinco candidatos M5 frente a cuatro, conservando los demás requisitos. El candidato añadido tenía ADX 23,57 y un resultado simulado de +1,01451R. Es una sola observación elegida retrospectivamente: no demuestra que el umbral 23 sea superior en el futuro.

La tabla siguiente es un **subconjunto diagnóstico**, no un replay completo del motor. Rechazar una posición cambiaría las ventanas en las que se admiten otras señales; filtrar filas no reproduce ese efecto. Se mantienen las variantes operativas previas: M5 para los cuatro Step y M15 para los dos Crash.

| Filtro | Candidatos capturados que pasan | Resueltos | WinRate del subconjunto | Resultado del subconjunto |
|---|---:|---:|---:|---:|
'''
    subset_checks={}
    for title,filename in [('Antes: ADX 25','shared_quality_gates_before.json'),('Después: Step Index ADX 23','shared_quality_gates_after.json')]:
        checked=json.loads((OUT/filename).read_text())
        subset=[]
        for symbol,variants_checked in checked['symbols'].items():
            mode=baseline['m5_symbol_modes'].get(symbol,baseline['m5_confirmation_mode'])
            subset.extend(variants_checked['M15_M5' if mode=='live' else 'M15']['passing_records'])
        metric=stats(subset)['conservative_ohlc']
        text+=f"| {title} | {len(subset)} | {metric['trades']} | {metric['win_pct']}% | {metric.get('total_r',0):.5f}R |\n"
        subset_checks[title]={'entries':len(subset),'metrics':stats(subset)}
    (OUT/'shared_quality_subset_comparison.json').write_text(json.dumps(subset_checks,indent=2,ensure_ascii=False),encoding='utf-8')
    text+='''
La cantidad de este subconjunto aumenta de 21 a 22, un 4,76%; todavía no alcanza el objetivo de 5%, ni el mínimo de 50 resultados por variante. No se debe presentar como cumplimiento de todos los objetivos. La ganancia aparente de WinRate tampoco tiene validación independiente ni todos los costes verificados. El perfil queda como ensayo DEMO y requiere seguimiento en fechas nuevas.

## Qué permite cada acción

La columna Guardado corresponde a la configuración aplicada. El efecto de cualquier ajuste sobre WinRate debe medirse; un filtro más estricto no garantiza mayor acierto.

| Acción | Guardado | Qué permite | Qué cambia al ajustarlo |
|---|---|---|---|
'''
    for key,label,effect,adjustment in ACTION_GUIDE:
        text+='| '+' | '.join(part.replace('|','\\|') for part in (label,value(key,settings[key]),effect,adjustment))+' |\n'
    text+='''
## Botones y modos: cómo aplicar un cambio

1. **Heredar** elimina la excepción por activo y vuelve a su selección habitual o modo general. Un activo ajeno a la selección no empieza a operar por aparecer en el catálogo.
2. **Observación del activo** impide todas sus órdenes. Poner M5 en Operar no supera esa restricción. **Desactivado** lo retira del escaneo. **Operar** permite evaluar la entrada y añadir el instrumento al escaneo; todavía exige una señal válida.
3. Ajustar un campo deja un cambio pendiente. **Guardar ajustes** persiste la configuración y se aplica al siguiente análisis. La guía muestra los valores guardados, no el borrador aún sin guardar.
4. **Actualizar estado** vuelve a leer la configuración y descarta el borrador. **Volver a valores por defecto** solo carga las referencias en el formulario: hay que guardar para aplicarlas. Vacía excepciones por activo y vuelve a la selección habitual y los candidatos adicionales por defecto; no restaura este perfil personalizado.
5. Para deshacer solo el ensayo de Step Index, borrar su campo **ADX de ejecución** y guardar hace que herede 25. También se puede escribir 25 expresamente. Esto conserva los demás modos y ajustes del perfil.

## Secuencia para buscar más entradas y más efectividad

1. Tomar como base los ajustes guardados y contar episodios únicos, no lecturas repetidas ni las dos piernas como dos oportunidades independientes.
2. Revisar el primer bloqueo: falta de datos se resuelve con historial; espera de retorno no se resuelve apagando ADX; precio alejado no se resuelve ampliando la caducidad; D1 neutral de Forex requiere evaluar contexto, no ignorar errores del proveedor.
3. Cambiar una condición o un grupo pequeño de activos. Mantener una versión de referencia y medir la misma ventana y feed. Registrar cada prueba, incluidas las desfavorables.
4. Exigir los objetivos de frecuencia, WinRate y beneficio a la vez. WinRate aquí significa resultado total positivo en R; los breakeven con beneficio parcial positivo cuentan como ganancia, no equivale necesariamente a tocar TP2.
5. Validar en otro período y con costes de ejecución. El mínimo de 50 no constituye por sí solo una prueba estadística de ventaja. Considerar también incertidumbre, drawdown y resultados por activo y escenario.
6. Pasar una variante a Operar por activo únicamente después de revisar sus resultados. No se activan todos los instrumentos por una sola semana favorable. El registro observado y el WinRate de operaciones ejecutadas siguen separados.

## Condiciones que no deben confundirse con estos controles

La señal usa velas cerradas, ruptura H1 ya completada y primer retorno posterior; no usa información futura. Se conservan invalidación, obstáculos y espacio mínimo 2R, dirección permitida de Boom/Crash, stop con riesgo positivo, precio real de entrada y deduplicación del episodio. Forex, metales, índices y BTCUSD conservan las sesiones del proyecto: Londres 07–11 UTC y Nueva York 12:30–17 UTC. Desactivar D1 en sintéticos no elimina esas sesiones de otros instrumentos.

Además, el ejecutor conserva controles adicionales. Step ahora permite configurar su mínimo de ejecución **solo para SNR desde esta pestaña**, con el ADX capturado de la señal o el dato disponible del análisis/proveedor. La excepción de Step Index es 23; los otros Step heredan 25. Una señal SNR puede traer ADX H1, aunque el antiguo motivo mencionaba M15. Los otros motores conservan su umbral previo. El diagnóstico nuevo registra el mínimo aplicado y la versión de ajustes; datos ADX ausentes o no finitos no autorizan una entrada SNR. Boom/Crash siguen comprobando extremos H1 de las últimas 24 horas. También existen comprobaciones de exposición y posiciones de otros motores. Bajar ADX de formación de Continuación no elimina el mínimo de ejecución.

La IA actual no tiene validación compatible. Con Filtro + Observar modelo incompatible, únicamente en DEMO, sus umbrales no están demostrando una mejora de calidad. En cuenta real esa excepción no permite saltar el bloqueo. El siguiente paso de IA exige capturas causales y resultados reales completos, calibración independiente y una versión compatible; bajar probabilidades de un modelo incompatible no resuelve la ausencia de validación.

## Fuentes y evidencia

La documentación de [Deriv sobre Step](https://traders-academy.deriv.com/trading-guides/step-indices-evolution-step-multi-step-skew-step) describe su mecánica; no valida este bot ni sus parámetros. La investigación [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) fundamenta la cautela al seleccionar configuraciones por resultados del mismo historial. Ninguna de esas fuentes demuestra que nuestros valores 105% / 1 punto / 50 sean óptimos: son objetivos explícitos de evaluación.

- Ajustes antes/después y cambio exacto: `storage/analysis/msnr_configuracion_guiada_20261012/`.
- Replays de 30 días: `storage/analysis/msnr_v27_m5_reference_20261012/steps_v28_30d_current/` y `crash_v28_30d_current/`. Las fuentes anteriores de los Step también se conservaron en `source_snapshot/`.
- Evaluación con los objetivos nuevos: `storage/analysis/msnr_configuracion_guiada_20261012/steps_30d_reassessment.json`.
- Guía en la interfaz: sección **Guía de cada acción** en Malaysian SNR.

## Verificación del despliegue

El motor confirmó preferencias 13, estado RUNNING y 36 activos en el ciclo. Se conservaron los demás procesos y el modelo de IA. El ADX propio se registra en la señal con el umbral aplicado y la versión de ajustes. Se verificaron los controles por Step, la validación del formulario y la guía de los 59 ajustes.

El primer intento de recarga se aplazó al detectar una posición SNR abierta. Antes de la recarga definitiva se verificaron stop y objetivo activos en el bróker, ausencia de órdenes pendientes y su registro persistente. El motor recupera esa posición desde el bróker y el diario. Después se comprobó que conservó el mismo ticket, stop y objetivo, y que el monitor emitió eventos nuevos. La recarga no envió órdenes ni modificó esa posición.

Validación: 278 pruebas dirigidas de persistencia, API, IA, causalidad, controles, replay y aislamiento entre motores aprobadas en los conjuntos ejecutados. El conjunto final de 78 incluyó los controles nuevos de ejecución Step. JavaScript validado y formulario comprobado en el navegador. Evidencia en `deployment_verification.json`, `step_reload_before.json` y `step_reload_after.json`.
'''
    target=ROOT/'MSNR_GUIA_CONFIGURACIONES_Y_OBJETIVOS_20261012.md'
    target.write_text(text,encoding='utf-8')
    print(json.dumps({'document':str(target),'settings_version':settings['version'],
        'explained_controls':len(ACTION_GUIDE),'changes':list(changes),
        'profile_comparison':assessment['combined']['PERFIL_VS_CONFIGURACION_ANTERIOR']},ensure_ascii=False))

if __name__=='__main__':main()
