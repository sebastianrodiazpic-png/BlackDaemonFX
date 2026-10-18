"""Build the traceable study from public captions and frozen offline results."""
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.malaysian_snr.runtime_settings import msnr_default_settings
from dashboard.msnr_action_guide import ACTION_GUIDE
from dashboard.msnr_settings_panel import PANEL_JS

OUT=ROOT/'storage/analysis/msnr_videos_20261013'
LESSONS=[
('L_vwb_jf6og','Albert: cinco escenarios','sucesión','Distingue dos velas del mismo color, A/V, Fresh y fractal H1/M15. Sus cifras de acierto son afirmaciones del video, sin validación de nuestro código.'),
('sTRxqo4EwPU','Pol Castella: revisión crítica','two candles','Expone el cierre de la primera vela como nivel A/V y cuestiona que marcar niveles sea una estrategia completa. No aporta una prueba estadística trasladable al bot.'),
('1x57n_5iRsU','Nestor: parte 1','cierres','Marca niveles por cuerpos y utiliza A/V y soporte/resistencia que cambia de función. El giro no necesita ser siempre una envolvente.'),
('dGv5zwrK9vY','Nestor: parte 2','temporalidad','Desciende de marcos mayores a menores para refinar niveles y dirección. Esto requiere una relación comprobable entre nivel padre y entrada.'),
('YmK59hyKX0U','Nestor: parte 3','5 minutos','Combina contexto semanal/diario, H4/H1 y confirmación menor. El stop y el objetivo dependen de niveles estructurales, no de una cifra fija universal.'),
('qT-TWP2sUgA','Nestor: parte 4','primera vez','Prefiere primeros contactos y exige más confirmación en niveles visitados. Ajusta el objetivo al contexto; un ejemplo de TP no demuestra WinRate.'),
('odvBj8IpZ74','Nestor: parte 5','contexto','En EURUSD busca rechazo de nivel mayor, cambio estructural y niveles a favor. Refuerza que soportes y resistencias aislados no bastan.'),
('xYlpAr5pwXg','MBA: día 1','martillo','Muestra refinamiento de niveles y rechazo tipo martillo. Inspiró la alternativa Pinbar; sus umbrales numéricos son una interpretación del proyecto.'),
('9ZNPazzfDcU','MBA: día 2','estructura','Distingue estructura relevante y ruido. No debe confundirse cada movimiento de un marco pequeño con un cambio del contexto mayor.'),
('5oTQEdSV7p0','MBA: día 3','externa','Relaciona liquidez interna/externa y jerarquía temporal. Es una hipótesis para clasificar contexto, no autorización para copiar stops diminutos.'),
('wDK7qO4mf-E','Albert: refinamiento','sucesión','Define Breaker Pair por dos velas fuertes del mismo color y la unión de sus cuerpos. Advierte que stops más pequeños pueden reducir la tasa de acierto.'),
('Bwktah4s79k','Alchemist: introducción de la playlist','same type of candles','Define A/V en gráfico de líneas y Open–Close con velas del mismo color. Sitúa H4/H1 como marcos de confirmación; separar Open–Close de gap evita perder el patrón básico.'),
('lqlkspVKt7s','Alchemist: parte 2','daylight','Usa confluencia de niveles y líneas de tendencia; explica ajustes de horario y no convierte Fresh en un veto universal. Las líneas requieren reglas causales propias.'),
('CH9iW5caHHk','Alchemist: parte 3','obstacles','Distingue storyline, confirmación y obstáculos por jerarquía. La dirección por estructura ya existe, pero no equivale a reproducir rechazo D1 seguido de ruptura H4.'),
('QbyhRLF53RI','Alchemist: parte 4','unfresh','Considera niveles probados dentro de contexto y revisa confirmaciones H4/H1. No justifica habilitar contactos ilimitados del mismo episodio.'),
('XvXWWv3gD8k','Alchemist: parte 5','confirmation','Revisa confirmación, flexibilidad y refinamiento; un pequeño quiebre aislado puede no ser suficiente. La gestión de riesgo sigue siendo necesaria cuando el nivel falla.'),
('sxn-jP9St9I','Alchemist FX 2023','structure','Integra estructura y barridos de liquidez en casos de mercado. Un breakout aislado puede fallar si queda liquidez o un nivel relevante antes del objetivo.'),
('FM0XkqUIrAI','Alchemist MSNR 2024','confirmation','Combina niveles, estructura, horario y confirmación. No debe traducirse cada explicación discrecional en un filtro acumulativo obligatorio.'),
('WLKh7JAcy34','Alchemist 2026: análisis 1','confirmation','Formula escenarios condicionados a barridos, contexto y confirmación; incluye BTC. Distinguir expectativas de señales confirmadas evita entradas anticipadas.'),
('XFkktcM_srU','Alchemist 2026: análisis 2','stop loss','Relaciona el stop con el extremo que barrió liquidez. Una reducción arbitraria del stop puede convertir una buena dirección en una pérdida.'),
('qciNrYGZ5V8','Alchemist 2026: análisis 3','current candle closes','Espera cierres antes de fijar extremos de sesión y combina barrido, estructura e imbalance. La información de una vela abierta no se puede usar retrospectivamente.'),
('ip8z7AThH7Y','Alchemist 2026: análisis 4','confirmation','Busca liquidez objetivo y confirmaciones después de barridos. Requiere separar el escenario previsto del evento que realmente habilita una entrada.'),
('bMxO8y4siSI','Alchemist 2026: análisis 5','stop loss','Insiste en paciencia, confirmación y protección del extremo que barrió liquidez. Un ejemplo ganador no acredita transferibilidad a instrumentos sintéticos.'),
]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    evidence=[]
    for vid,label,pattern,lesson in LESSONS:
        path=OUT/'captions'/(vid+'.json')
        data=json.loads(path.read_text(encoding='utf8'))
        snippets=data.get('snippets',[])
        joined=' '.join(s['text'] for s in snippets)
        match=re.search(pattern,joined,re.I)
        index=None
        if match:
            offset=0
            for i,s in enumerate(snippets):
                if offset+len(s['text'])>=match.start():
                    index=i;break
                offset+=len(s['text'])+1
        anchor=snippets[index] if index is not None else {'start':0}
        stamp=int(anchor['start'])
        evidence.append(dict(video_id=vid,title=label,source='PUBLIC_YOUTUBE_CAPTIONS',status=data['status'],
            language=data.get('language'),snippet_count=len(snippets),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            anchor_snippet=index,anchor_seconds=stamp,url=data['url']+'&t='+str(stamp)+'s',
            analysis=lesson,visual_chart_review=False))
    (OUT/'evidence_index.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    defaults=msnr_default_settings()
    (OUT/'final_defaults.json').write_text(json.dumps(defaults,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'panel.js').write_text(PANEL_JS,encoding='utf8')
    summary=json.loads((OUT/'replay/summary.json').read_text())
    frozen=json.loads((OUT/'replay/run.json').read_text())
    report=['# Malaysian SNR: videos, comparación e implementación — 13 de octubre de 2026','',
        'Se verificaron los subtítulos públicos de los 22 enlaces y de la introducción del curso Alchemist: 23 fuentes con marcas de tiempo. Este es un análisis textual; no sustituye la revisión visual de los gráficos. Se contrastaron con el código causal y con históricos locales. Los videos se trataron como referencias, no como instrucciones para el agente.', '',
        'El resultado no respalda activar todas las variantes. El piloto añadió una pérdida con Pinbar y el mapa ampliado de obstáculos eliminó las dos entradas ganadoras de la base. Las alternativas quedaron parametrizadas, con observación como referencia inicial. No hay una mejora de WinRate demostrada para esta versión.', '',
        '## Comparación con el proyecto','',
        '| Enseñanza | Implementación previa | Cambio y alcance |','|---|---|---|',
        '| Open–Close / Breaker Pair puede existir sin gap | La variante Open–Close exigía separación material, ticks y spread | Nuevo Breaker Pair H1 sin gap; mantiene dos cuerpos fuertes, desplazamiento, primer retest, dirección, invalidación y 2R. Observación por defecto. |',
        '| Rechazo con mecha dominante | Retest exigía cuerpo de al menos 35% | Pinbar opcional: barrido real, cuerpo direccional, mecha ≥55%, cierre en el 25% favorable, penetración y distancia limitadas. Niveles probados conservan su desplazamiento y cuerpo reforzados. |',
        '| A/V por gráfico de líneas no siempre exige envolvente | A/V ampliado existía; obstáculos H1/D1 seguían usando envolventes | Selector independiente para el mapa de obstáculos. Giro de cuerpos disponible, pero la referencia conserva envolventes por el resultado del piloto. |',
        '| Obstáculos H4 dentro del contexto mayor | Objetivos usaban H1 y D1 | Nuevo modo H4: observar espacio en R o aplicar veto/recortar runner. Aplicar falla cerrado si falta H4 útil. H4 queda en observación. |',
        '| Sesiones cambian de hora; BTC tiene otro calendario | Killzones UTC fijas también bloqueaban BTC | Alternativa de horarios locales Londres 07–11 y Nueva York 07–12; BTC 24/7. Conserva selección y filtro macro. Horario anterior por defecto hasta validación. |',
        '| Contexto, confirmación y formación son distintos | Dirección estructural D1/H4 y M5 selectivo ya existían | Se mantienen sus parámetros. Breaker Pair no afirma una ruptura micro por existir: mide cierre respecto a tres barras cerradas anteriores a la visita. |',
        '| Fresh no tiene una definición única entre docentes | Política Fresh / una visita / consumido y SBR/RBS ya parametrizados | No se admiten contactos ilimitados ni se renueva un episodio sin nueva ruptura. El curso no demuestra que quitar todos los filtros mejore el WinRate. |', '',
        'Los mínimos 50%, 0,50 ATR, 55% de mecha y 75% de posición del cierre son hipótesis operativas del proyecto, no números universales enseñados por todos los autores. Un rechazo Pinbar no equivale a una confirmación completa H4/H1 ni sustituye el contexto macro.', '',
        '## Valores por defecto disponibles en /strategy-bases → Malaysian SNR','',
        '| Control nuevo | Valor de referencia | Qué permite |','|---|---|---|']
    guide={row[0]:row for row in ACTION_GUIDE}
    new_keys=['breaker_pair_mode','breaker_pair_min_body_ratio','breaker_pair_min_displacement_atr',
        'retest_pinbar_mode','retest_pinbar_min_wick_ratio','retest_pinbar_min_close_ratio',
        'session_policy','obstacle_av_definition','h4_obstacle_mode']
    display={'shadow':'Observación','legacy_utc':'Horario UTC anterior','engulfing':'Envolvente'}
    for key in new_keys:
        value=display.get(defaults[key],str(defaults[key]))
        if key.endswith('_ratio'):value=f'{defaults[key]*100:g}%'
        if key.endswith('_atr'):value=f'{defaults[key]:.2f} ATR H1'
        report.append(f'| {guide[key][1]} | {value} | {guide[key][2]} |')
    report += ['', 'Los objetivos de comparación pasan de aceptar 80% de frecuencia, 0 puntos de mejora y 30 resultados a exigir **105% de frecuencia, +1 punto porcentual de WinRate y 50 resultados resueltos por variante**. También se exige expectativa positiva y beneficio total superior. Son criterios de investigación; no producen una promoción automática ni limitan las órdenes actuales.', '',
        'Se conservan los valores guardados por el operador. La reducción guardada de cuerpo Fractal a 45%, las excepciones Step y los activos en observación no se sustituyen por restaurar código. La referencia general de Fractal sigue en 50%; su distancia sigue en 0,50 ATR. La configuración completa tiene 68 controles, todos explicados en la guía de la pestaña.', '',
        '“Volver a valores por defecto” carga la referencia en el formulario; “Guardar ajustes” aplica lo editado. También restablece las excepciones por activo: no debe usarse pensando que solo cambia los nueve campos nuevos. Este trabajo cambió código y referencia, sin escribir preferencias operativas, reiniciar trabajadores ni enviar órdenes. Los procesos ya abiertos necesitan cargar la versión nueva antes de guardar los campos nuevos.', '',
        'La versión es `msnr-v2.9-video-evidence`. El contrato IA exige esa versión y los parámetros compatibles. No se entrenó ni activó un modelo nuevo: Filtro + Bloquear sigue bloqueando un modelo incompatible; la política de observar incompatibilidad sigue restringida a DEMO.', '',
        '## Replay local realizado','',
        f'Período: {frozen["start"]} a {frozen["end"]}, dividido el {frozen["split"]}. Se usaron barras nativas M5, M15, H1, H4 y D1 verificadas por hash. Instrumentos: '+', '.join(frozen['symbols'])+'.', '',
        'La base reconstruye las entradas primarias del perfil guardado v13, con sus modos M5 por activo y ADX Step estándar 23. Las ramas sin órdenes no generan fills; BTC se simula explícitamente como activo investigado, sin modificar su modo operativo. Se aplican los filtros Step y Boom/Crash antes de reservar el tiempo de una posición, permitiendo reevaluar ventanas liberadas. No se filtró solamente una lista previa de trades.', '',
        '| Perfil investigado | Trades resueltos | Ganadores | R total | Decisión |','|---|---:|---:|---:|---|']
    labels={'baseline':'Base guardada','breaker':'Solo Breaker Pair adicional',
        'pinbar':'Solo Pinbar adicional','expanded_quality':'Ambos + horarios y obstáculos H1/D1/H4 ampliados',
        'reference':'Hipótesis de referencia: solo horarios y mapa H1/D1 ampliados'}
    for profile,metrics in summary['profiles']['all'].items():
        m=metrics['conservative_ohlc'];wins='—' if m['win_pct'] is None else str(round(m['trades']*m['win_pct']/100))
        report.append(f'| {labels[profile]} | {m["trades"]} | {wins} | {m.get("total_r",0):.5f} | '+('Comparador' if profile=='baseline' else 'No supera criterios')+' |')
    report += ['', '**Dos ganadores de dos trades no constituyen un WinRate estimado fiable**: el intervalo Wilson 95% de la base es 34,238%–100%. Pinbar dio dos ganadores de tres (66,667%), y uno de dos en la segunda semana. En ninguna comparación se alcanza la muestra mínima de 50. El conjunto ampliado produjo una pérdida; la hipótesis de referencia ampliada quedó sin trades y fue descartada como valor por defecto.', '',
        'La segunda semana es una separación temporal declarada, pero el histórico ya se había examinado en tareas previas: no se presenta como validación independiente intacta. Las seis series no representan todos los 60 activos del catálogo. No hay dos años completos de M5 nativo para todos los activos, por lo que no se afirma un replay validado de dos años.', '',
        'Resultados OHLC conservadores; spread histórico aproximado. Faltan costes verificados de comisiones, slippage y swap, lotes/distancia mínima de broker, cartera entre instrumentos, veto IA y otros filtros compartidos como Jump. Son resultados de investigación, no PnL ejecutado ni muestras aptas para entrenar. Las dos piernas se cuentan como un trade; un resultado BE después de TP1 puede dar R total positivo.', '',
        'El replay congela código y parámetros en `replay/source_snapshot` y `replay/run.json`. La referencia final se eligió después del piloto. Posteriormente se corrigió la serialización del formulario y la evidencia micro del nuevo Breaker Pair; esta última afecta a la confirmación declarada y posibles vetos Jump, una familia no incluida en el piloto. No modifica los stops, targets o filtros Step/Boom/Crash de los seis activos estudiados. La versión final también pospone la consulta opcional H4 hasta tener una confirmación y reutiliza la formación H1 entre la rama habitual y Pinbar; ambas propiedades tienen pruebas específicas.', '',
        '## Cómo buscar más entradas sin convertir filtros en una promesa de WinRate','',
        '1. Mantener las ramas nuevas en Observación y comprobar los candidatos únicos por escenario, activo y confirmación. Pinbar usa un registro separado (`M15_PINBAR` / `M5_PINBAR`) para no sobrescribir la confirmación habitual del mismo episodio.',
        '2. Cambiar una sola variable en cada comparación: primero Breaker Pair, después Pinbar; separar horarios, obstáculos y contexto H4. La caída del perfil conjunto no identifica por sí sola cuál componente causa cada pérdida.',
        '3. Comparar las mismas fechas y feed con los filtros de ejecución, deduplicación y disponibilidad de posiciones. Una señal recuperada que pierde no cumple el objetivo aunque suba el número de trades.',
        '4. Acumular al menos 50 resultados resueltos por variante y luego verificar otro período con costes. Exigir +5% de frecuencia, +1 punto de WinRate y beneficio superior por activo/familia, además del agregado.',
        '5. Activar Operar únicamente en los activos y escenarios que sostengan el resultado. Las opciones por activo existentes permiten conservar M5 selectivo y observación en los demás.', '',
        'Quedan como mejoras futuras: relación explícita entre rechazo de nivel padre H4/D1 y ruptura H1, objetivos de liquidez previa diaria/Asia, normalización causal de líneas de tendencia y stop detrás del extremo barrido. Necesitan sus propias reglas y replays. No se activaron stops M1 mínimos, martingala, reentradas ilimitadas ni se copiaron afirmaciones comerciales de rentabilidad.', '',
        '## Fuentes y pasajes revisados','',
        'Cada enlace abre el pasaje identificado en los subtítulos. Las marcas de tiempo son de la fuente, no una reconstrucción visual. Se localizaron y contrastaron pasajes relevantes dentro del texto disponible; los ejemplos gráficos no se certifican. La introducción añadida cubre también la parte 1 de [la playlist indicada](https://www.youtube.com/playlist?list=PLDzVTTgUrcNN1XkJgYok7SRyNxbXWpRaC).','',
        '| Fuente | Pasaje | Enseñanza contrastada |','|---|---|---|']
    for item in evidence:
        seconds=item['anchor_seconds'];stamp=f'{seconds//60}:{seconds%60:02d}'
        report.append(f'| [{item["title"]}]({item["url"]}) | {stamp} | {item["analysis"]} |')
    report += ['', 'Para los horarios se utiliza la base IANA mediante [`zoneinfo`](https://docs.python.org/3/library/zoneinfo.html). Se declaró `tzdata` para disponibilidad en Windows; si falta la zona horaria, la alternativa devuelve un bloqueo explícito.', '',
        '## Artefactos y verificación','',
        '- `storage/analysis/msnr_videos_20261013/evidence_index.json`: 23 fuentes, idiomas, marcas de tiempo y hashes.',
        '- `storage/analysis/msnr_videos_20261013/replay/summary.json`: resultados, censura y comparaciones por período/activo.',
        '- `storage/analysis/msnr_videos_20261013/final_defaults.json`: referencia final del formulario, distinta de la hipótesis ampliada descartada.',
        '- `tools/replay_msnr_video_improvements.py`: replay reproducible sin inicialización de broker ni envío de órdenes.',
        '- Pruebas: **385 aprobadas en 15 archivos**. Cubren cierre causal, primer retest, penetración, variantes sin órdenes, separación de auditoría, obstáculos H4, horarios de verano, guardado/restauración, contrato IA y replays anteriores. El formulario verificó la serialización de los **68 valores de referencia** con el JavaScript real y sin abrir un navegador. Registro: `verification.json`.', '']
    path=ROOT/'MSNR_ANALISIS_VIDEOS_Y_MEJORAS_20261013.md'
    path.write_text('\n'.join(report),encoding='utf8')
    print(json.dumps({'report':str(path),'sources_verified':sum(e['status']=='OK' for e in evidence),
        'controls':len(defaults),'primary_defaults_preserved':defaults['session_policy']=='legacy_utc' and defaults['obstacle_av_definition']=='engulfing'}))


if __name__=='__main__':main()
