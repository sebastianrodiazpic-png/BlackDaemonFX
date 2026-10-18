"""Editable Malaysian SNR controls and reversible loading of reference defaults."""
import importlib
import dashboard.msnr_action_guide as _action_guide
importlib.reload(_action_guide)
GUIDE_HTML, GUIDE_JS = _action_guide.GUIDE_HTML, _action_guide.GUIDE_JS
PANEL_HTML = r'''
<section class="card" id="msnrRuntimeSettings" aria-labelledby="msnrSettingsTitle" hidden style="display:none;">
  <div class="card-header"><h2 class="card-title" id="msnrSettingsTitle">🇲🇾 Ajustes de Malaysian SNR</h2><span class="badge badge-purple">Configuración dinámica</span></div>
  <style>
    #msnrRuntimeSettings fieldset{border:1px solid var(--border);border-radius:10px;padding:16px;margin:0 0 16px;}
    #msnrRuntimeSettings legend{font-weight:700;padding:0 8px;}
    #msnrRuntimeSettings .msnr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:16px;}
    #msnrRuntimeSettings .msnr-field label{display:block;font-weight:600;margin-bottom:8px;}
    #msnrRuntimeSettings input[type=number],#msnrRuntimeSettings select{padding:8px;width:100%;max-width:265px;background:var(--bg);color:inherit;border:1px solid var(--border);border-radius:8px;}
    #msnrRuntimeSettings .msnr-toggle{display:flex;gap:10px;align-items:center;margin:10px 0;}
    #msnrRuntimeSettings input[type=checkbox]{width:18px;height:18px;accent-color:var(--purple);}
    #msnrRuntimeSettings .msnr-help{margin:10px 0 0;line-height:1.6;}
    #msnrRuntimeSettings summary{cursor:pointer;font-weight:600;margin:10px 0;}
  </style>
  <fieldset><legend>Alternativas de los videos y calidad del contexto</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrBreakerPairMode">Breaker Pair — dos velas H1 sin exigir gap</label><select id="msnrBreakerPairMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrBreakerPairBody">Cuerpo mínimo de ambas velas (%)</label><input id="msnrBreakerPairBody" type="number" min="1" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrBreakerPairDisplacement">Desplazamiento del segundo cierre (ATR H1)</label><input id="msnrBreakerPairDisplacement" type="number" min="0.001" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrPinbarMode">Confirmación con rechazo Pinbar</label><select id="msnrPinbarMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrPinbarWick">Mecha mínima de rechazo (%)</label><input id="msnrPinbarWick" type="number" min="1" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrPinbarClose">Posición mínima del cierre favorable (%)</label><input id="msnrPinbarClose" type="number" min="50" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrSessionPolicy">Horario de entradas</label><select id="msnrSessionPolicy" disabled onchange="markMsnrSettingsChanged()"><option value="legacy_utc">Horario UTC anterior</option><option value="market_hours">Por mercado — Londres / Nueva York; cripto 24/7</option></select></div>
      <div class="msnr-field"><label for="msnrObstacleDefinition">Definición de obstáculos H1 y D1</label><select id="msnrObstacleDefinition" disabled onchange="markMsnrSettingsChanged()"><option value="engulfing">Envolvente</option><option value="body_turns">Giro de cuerpos — sin exigir envolvente</option></select></div>
      <div class="msnr-field"><label for="msnrH4ObstacleMode">Obstáculos H4</label><select id="msnrH4ObstacleMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin veto</option><option value="live">Aplicar filtro y ajustar objetivo</option></select></div>
    </div>
    <p class="muted msnr-help">Referencia: Breaker Pair y Pinbar en Observación; cuerpos 50%, desplazamiento 0,50 ATR, mecha 55%, cierre favorable 75%. Se conserva el horario UTC anterior y el mapa de obstáculos por envolventes; H4 en Observación. El replay piloto no justificó activar las alternativas en conjunto. Los ajustes guardados tienen prioridad sobre los valores por defecto.</p>
  </fieldset>
  <fieldset><legend>Fractal y contexto</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrFractalBodyPercent">Cuerpo mínimo del Fractal H1 (%)</label><input id="msnrFractalBodyPercent" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrFractalMaxDistanceAtr">Distancia máxima de entrada Fractal (ATR H1)</label><input id="msnrFractalMaxDistanceAtr" type="number" min="0" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrRetestWindowMinutes">Ventana máxima de retest (minutos)</label><input id="msnrRetestWindowMinutes" type="number" min="15" max="360" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <label class="msnr-toggle"><input id="msnrSyntheticD1Veto" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Exigir dirección D1 en sintéticos</label>
    <p class="muted msnr-help">El cuerpo se mide como |cierre − apertura| / (máximo − mínimo). La distancia se verifica en la confirmación M15 y en el precio real de entrada. Los obstáculos D1 y la dirección permitida de Boom/Crash se conservan; los instrumentos tradicionales mantienen su filtro D1.</p>
  </fieldset>
  <fieldset><legend>Activos candidatos adicionales</legend>
    <div class="msnr-field"><label for="msnrAdditionalSymbolsMode">Modo de los activos adicionales</label><select id="msnrAdditionalSymbolsMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
    <div id="msnrAdditionalSymbols" class="msnr-grid"></div>
    <p class="muted msnr-help">Los activos elegidos se añaden a la selección habitual. Observación registra señales sin abrir posiciones. Su WinRate con los ajustes actuales todavía requiere validación.</p>
  </fieldset>
  <fieldset><legend>Continuación A/V Fresh</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrContinuationMode">Modo de continuación A/V</label><select id="msnrContinuationMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrContinuationBodyPercent">Cuerpo mínimo H1 de continuación (%)</label><input id="msnrContinuationBodyPercent" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrContinuationAdx">ADX mínimo H1 de continuación</label><input id="msnrContinuationAdx" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrContinuationDistance">Distancia máxima Continuación / A/V (ATR H1)</label><input id="msnrContinuationDistance" type="number" min="0" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrContinuationWick">Mecha máxima de ruptura Continuación (%)</label><input id="msnrContinuationWick" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrQmDistance">Distancia máxima Quasimodo (ATR H1)</label><input id="msnrQmDistance" type="number" min="0" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <label class="msnr-toggle"><input id="msnrContinuationFreshOnly" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Exigir nivel realmente Fresh en continuación</label>
    <p class="muted msnr-help">Añade rupturas A/V con retest M15 fuerte. Los niveles consumidos siguen bloqueados y la entrada debe tener espacio suficiente hasta los obstáculos. Su modo se ajusta por separado del Fractal.</p>
  </fieldset>
  <fieldset><legend>Filtro de ejecución Step para Malaysian SNR</legend>
    <div class="msnr-field"><label for="msnrStepExecutionAdx">ADX mínimo de ejecución Step SNR</label><input id="msnrStepExecutionAdx" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
    <p class="muted msnr-help">Referencia 25. Es el filtro adicional del motor para Step: la señal SNR puede traer ADX H1. Cada Step puede sobrescribirlo abajo; vacío hereda este valor. No cambia los otros motores ni elimina el ADX de formación de Continuación.</p>
  </fieldset>
  <fieldset><legend>Recuperación selectiva por activo</legend>
    <p class="muted msnr-help">Cada activo puede usar Desactivado, Observación u Operar. Heredar conserva la selección habitual o el modo general. Un modo propio tiene prioridad sobre los activos adicionales. Observación registra candidatos y resultados sin órdenes. Los filtros de estructura, dirección autorizada y ejecución siguen vigentes.</p>
    <div id="msnrAssetPolicies"></div>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrResearchFrequency">Frecuencia mínima frente a la base (%)</label><input id="msnrResearchFrequency" type="number" min="0" max="500" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrResearchWinRate">Mejora mínima de WinRate (puntos porcentuales)</label><input id="msnrResearchWinRate" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrResearchSample">Muestra mínima resuelta por comparación</label><input id="msnrResearchSample" type="number" min="10" max="10000" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <p class="muted msnr-help">Referencia: frecuencia 105% (5% más entradas), mejora de WinRate de 1 punto porcentual y 50 resultados resueltos por variante. Se exige también expectativa positiva y beneficio total superior. Son criterios de investigación en las mismas fechas y feed; no filtran órdenes actuales ni activan variantes automáticamente.</p>
  </fieldset>
  <fieldset><legend>Niveles A/V ampliados</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrAvEntryMode">Modo de A/V ampliado</label><select id="msnrAvEntryMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrAvDefinition">Definición A/V para las variantes</label><select id="msnrAvDefinition" disabled onchange="markMsnrSettingsChanged()"><option value="engulfing">Envolvente de cuerpos</option><option value="body_turns">Giro de cuerpos — sin envolvente</option></select></div>
    </div>
    <p class="muted msnr-help">Evalúa niveles adicionales sin cambiar la continuación original ni el mapa de obstáculos. Conserva sus mínimos de cuerpo H1, ADX y mecha, la política Fresh y el retest M15. La definición elegida también se usa en SBR/RBS.</p>
  </fieldset>
  <fieldset><legend>Cambio de función SBR/RBS</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrRoleFlipMode">Modo de cambio de función</label><select id="msnrRoleFlipMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrRoleFlipMaxChanges">Máximo de cambios de función por nivel</label><input id="msnrRoleFlipMaxChanges" type="number" min="1" max="3" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrRoleFlipDisplacement">Desplazamiento mínimo de la ruptura (ATR H1)</label><input id="msnrRoleFlipDisplacement" type="number" min="0.001" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <p class="muted msnr-help">Renueva un episodio únicamente tras una ruptura cerrada que cambia soporte por resistencia o viceversa. Guarda el historial y exige el primer retest M15. No duplica la primera ruptura Fresh de continuación; comparte sus mínimos de cuerpo y ADX.</p>
  </fieldset>
  <fieldset><legend>Quasimodo con swings intermedios</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrQmExtendedMode">Modo de Quasimodo ampliado</label><select id="msnrQmExtendedMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrQmSwingWindow">Ventana máxima de swings confirmados</label><input id="msnrQmSwingWindow" type="number" min="4" max="12" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrQmHeadDepth">Profundidad mínima de cabeza (ATR H1)</label><input id="msnrQmHeadDepth" type="number" min="0.001" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <p class="muted msnr-help">Busca hombro, neckline y cabeza aunque haya swings menores entre ellos. Todos deben estar confirmados antes de la primera ruptura; conserva la invalidación de cabeza y el retest del hombro.</p>
  </fieldset>
  <fieldset><legend>Dirección macro por estructura</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrMacroStructureMode">Modo de dirección macro estructural</label><select id="msnrMacroStructureMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado — última vela D1</option><option value="shadow">Observación — comparar con D1</option><option value="live">Operar — usar estructura</option></select></div>
      <div class="msnr-field"><label for="msnrMacroBiasMethod">Método de dirección estructural</label><select id="msnrMacroBiasMethod" disabled onchange="markMsnrSettingsChanged()"><option value="d1_structure">Estructura D1</option><option value="h4_structure">Estructura H4</option><option value="d1_h4_structure">Confluencia D1 y H4</option></select></div>
      <div class="msnr-field"><label for="msnrMacroPivotRadius">Velas de confirmación a cada lado del pivote</label><input id="msnrMacroPivotRadius" type="number" min="1" max="5" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <p class="muted msnr-help">Observación conserva las entradas actuales y registra las recuperadas por estructura sin órdenes. Operar sustituye el color D1 por pivotes y rupturas confirmadas; sin dirección definida espera. Solo aplica cuando el filtro macro es obligatorio: no reactiva el veto D1 en sintéticos.</p>
  </fieldset>
  <fieldset><legend>Open–Close / Decision Levels</legend>
    <div class="msnr-grid">
      <div class="msnr-field"><label for="msnrGapMode">Modo de niveles Open–Close</label><select id="msnrGapMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
      <div class="msnr-field"><label for="msnrGapTimeframe">Marco de formación Open–Close</label><select id="msnrGapTimeframe" disabled onchange="markMsnrSettingsChanged()"><option value="H1">H1</option><option value="H4">H4 — Decision Levels</option></select></div>
      <div class="msnr-field"><label for="msnrGapMinSize">Separación mínima Open–Close (ATR del marco)</label><input id="msnrGapMinSize" type="number" min="0.001" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrGapMinTicks">Separación mínima en ticks</label><input id="msnrGapMinTicks" type="number" min="1" max="100" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
      <div class="msnr-field"><label for="msnrGapSpreadMultiple">Separación mínima respecto al spread (veces)</label><input id="msnrGapSpreadMultiple" type="number" min="0.001" max="10" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
    </div>
    <p class="muted msnr-help">Exige dos velas cerradas del mismo color, separación direccional y una banda sin retest durante su formación. Usa el mayor de los tres mínimos y confirma el retorno en M15. Comparte el cuerpo y ADX de continuación. Sin tick o spread verificable no genera esta variante. Los valores iniciales son hipótesis pendientes de replay.</p>
  </fieldset>
<fieldset><legend>Historial útil</legend><div class="msnr-grid">
<label class="msnr-toggle"><input id="msnrAdaptiveHistoryEnabled" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Ampliar historial si faltan velas cerradas</label>
<div class="msnr-field"><label for="msnrHistoryMinH1">Mínimo de velas H1 útiles</label><input id="msnrHistoryMinH1" type="number" min="28" max="200" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrHistoryMinD1">Mínimo de velas D1 para contexto</label><input id="msnrHistoryMinD1" type="number" min="7" max="200" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrHistoryMaxRequest">Límite de velas por consulta</label><input id="msnrHistoryMaxRequest" type="number" min="200" max="3200" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
</div><p class="muted msnr-help">Amplía la consulta hasta obtener suficientes velas cerradas, sin fabricar barras ni usar velas abiertas. Un error de datos no se interpreta como neutralidad.</p></fieldset>
<fieldset><legend>Confirmación M5 y contexto H4</legend><div class="msnr-grid">
<div class="msnr-field"><label for="msnrM5ConfirmationMode">Confirmación M5 dentro del setup H1</label><select id="msnrM5ConfirmationMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
<div class="msnr-field"><label for="msnrRecoveryWindowMinutes">Ventana de recuperación (minutos)</label><input id="msnrRecoveryWindowMinutes" type="number" min="5" max="90" step="5" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrRecoveryMinBodyRatio">Cuerpo mínimo de recuperación (%)</label><input id="msnrRecoveryMinBodyRatio" type="number" min="0.001" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrH4NeutralFallbackMode">Usar H4 cuando la estructura D1 sea neutral</label><select id="msnrH4NeutralFallbackMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin órdenes</option><option value="live">Operar</option></select></div>
</div><p class="muted msnr-help">M5 conserva estructura y ATR H1, primer retest, invalidación y obstaculos. La ventana se mide en minutos. H4 solo aplica con D1 estructural neutral y datos suficientes; no elimina un sesgo D1 contrario. Observación no envia órdenes.</p></fieldset>
<fieldset><legend>IA propia de Malaysian SNR</legend><div class="msnr-grid">
<div class="msnr-field"><label for="msnrAiMode">Modo de IA Malaysian SNR</label><select id="msnrAiMode" disabled onchange="markMsnrSettingsChanged()"><option value="off">Desactivado</option><option value="shadow">Observación — sin veto IA</option><option value="filter">Filtro compatible</option></select></div>
<div class="msnr-field"><label for="msnrAiIncompatiblePolicy">Si el modelo no es compatible</label><select id="msnrAiIncompatiblePolicy" disabled onchange="markMsnrSettingsChanged()"><option value="block">Bloquear candidato</option><option value="observe">Observar IA — solo DEMO</option></select></div>
<div class="msnr-field"><label for="msnrAiMinProbability">Probabilidad mínima general (%)</label><input id="msnrAiMinProbability" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrAiMinProbabilityForex">Probabilidad mínima Forex y plata (%)</label><input id="msnrAiMinProbabilityForex" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrAiMinProbabilityGold">Probabilidad mínima oro (%)</label><input id="msnrAiMinProbabilityGold" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrAiMinProbabilityVolatility">Probabilidad mínima Volatility (%)</label><input id="msnrAiMinProbabilityVolatility" type="number" min="0" max="100" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
<div class="msnr-field"><label for="msnrAiMinNetExpectancyR">Expectativa mínima (R)</label><input id="msnrAiMinNetExpectancyR" type="number" min="-1" max="5" step="any" disabled oninput="markMsnrSettingsChanged()"></div>
</div><p class="muted msnr-help">Filtro exige un modelo compatible y validado. Por defecto bloquea si no lo hay. Observar un modelo incompatible permite evaluar la estrategia sin su veto solo en DEMO. Los umbrales no acreditan WinRate.</p></fieldset>
<fieldset><legend>Candidatos y resultados</legend><div class="msnr-grid">
<label class="msnr-toggle"><input id="msnrEnableCandidateAudit" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Registrar candidatos únicos y sus bloqueos</label>
<label class="msnr-toggle"><input id="msnrObserveCandidateOutcomes" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Seguir resultados de candidatos sin abrir órdenes</label>
<div class="msnr-field"><label for="msnrCandidateOutcomeHours">Horizonte de observacion (horas)</label><input id="msnrCandidateOutcomeHours" type="number" min="1" max="72" step="1" disabled oninput="markMsnrSettingsChanged()"></div>
</div><p class="muted msnr-help">Cada episodio se cuenta una vez; las variantes se comparan por separado. Resultados observados, ambiguos y costes faltantes se separan de operaciónes reales. No se entrenan modelos con ganancias estimadas sin costes verificados.</p></fieldset>
<p id="msnrModelStatus" class="muted msnr-help" aria-live="polite"></p>
<p class="muted msnr-help">Las cifras históricas de esta página corresponden a configuraciones anteriores. Aún no hay un WinRate validado para los ajustes actuales.</p>
<p id="msnrCandidateFunnel" class="muted msnr-help" aria-live="polite">Consultando candidatos...</p>
<p id="msnrCandidateBlockers" class="muted msnr-help" aria-live="polite"></p>
  <details><summary>Diagnóstico y seguimiento de setups</summary>
    <label class="msnr-toggle"><input id="msnrSetupDiagnostics" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Registrar motivos detallados de rechazo H1</label>
    <label class="msnr-toggle"><input id="msnrStructureCache" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Reutilizar estructura H1 mientras la vela y los ajustes no cambien</label>
    <label class="msnr-toggle"><input id="msnrPrioritizeRetests" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Priorizar setups vivos esperando retest</label>
    <label class="msnr-toggle"><input id="msnrAnalysisOutsideLock" type="checkbox" disabled onchange="markMsnrSettingsChanged()">Separar el análisis del bloqueo de envío de órdenes</label>
    <p class="muted msnr-help">El envío conserva la comprobación de posiciones, la deduplicación y la validación del precio de entrada. La información H1 se registra una vez por vela cerrada y versión de ajustes.</p>
  </details>
  <details><summary>Consultar valores por defecto</summary><ul id="msnrDefaultsNote" class="muted"></ul></details>
  <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:18px;">
    <button class="btn" id="msnrSaveSettings" type="button" disabled onclick="saveMsnrSettings()">Guardar ajustes</button>
    <button class="btn" id="msnrRestoreDefaults" type="button" disabled onclick="restoreMsnrDefaults()">Volver a valores por defecto</button>
    <button class="btn" id="msnrRefreshSettings" type="button" onclick="loadMsnrSettings()">Actualizar estado</button>
  </div>
  <p id="msnrSettingsStatus" role="status" aria-live="polite" class="muted">Consultando configuración…</p>
  <p class="muted msnr-help">Restaurar carga los valores de referencia en el formulario: revisa y pulsa Guardar ajustes para aplicarlos. Los ajustes guardados se aplican al siguiente análisis y se conservan al reiniciar. Las estadísticas históricas no se recalculan al modificarlos.</p>
</section>
'''

PANEL_JS = r'''
let msnrSavedSettings = null;
let msnrDefaults = null;
let msnrCatalog = [];
let msnrAssetCatalog = [];
function renderMsnrAssetPolicies() {
  const container=document.getElementById('msnrAssetPolicies'); container.replaceChildren();
  const families={synthetics:'Sintéticos',forex:'Forex',crypto:'Criptos',metals:'Metales',indices:'Índices',commodities:'Materias primas'};
  for(const family of Object.keys(families)) {
    const rows=msnrAssetCatalog.map((row,i)=>({...row,i})).filter(row=>row.family===family);
    if(!rows.length) continue;
    const details=document.createElement('details'); details.open=family==='crypto';
    const title=document.createElement('summary');title.textContent=families[family]+' · '+rows.length+' activos';details.appendChild(title);
    for(const row of rows) {
      const line=document.createElement('div');line.className='msnr-grid';line.style.marginBottom='12px';
      const name=document.createElement('strong');name.textContent=row.symbol;line.appendChild(name);
      for(const [prefix,labelText] of [['msnrAssetMode','Modo del activo'],['msnrAssetContinuation','Continuación'],['msnrAssetM5','Confirmación M5']]) {
        const field=document.createElement('div');field.className='msnr-field';
        const select=document.createElement('select');select.id=prefix+row.i;select.onchange=markMsnrSettingsChanged;
        const label=document.createElement('label');label.htmlFor=select.id;label.textContent=labelText+' · '+row.symbol;
        for(const [value,text] of [['inherit',prefix==='msnrAssetMode'?'Heredar ('+(row.base_mode==='live'?'Operar si está seleccionado':'Fuera de selección')+')':'Heredar modo general'],['off','Desactivado'],['shadow','Observación — sin órdenes'],['live','Operar']]) {
          const option=document.createElement('option');option.value=value;option.textContent=text;select.appendChild(option);
        }
        field.append(label,select);line.appendChild(field);
      }
      if(row.symbol.startsWith('Step Index')) {
        const field=document.createElement('div');field.className='msnr-field';
        const input=document.createElement('input');input.id='msnrAssetAdx'+row.i;input.type='number';input.min='0';input.max='100';input.step='any';input.placeholder='Heredar ADX general';input.oninput=markMsnrSettingsChanged;
        const label=document.createElement('label');label.htmlFor=input.id;label.textContent='ADX de ejecución · '+row.symbol;field.append(label,input);line.appendChild(field);
      }
      details.appendChild(line);
    }
    container.appendChild(details);
  }
}
const msnrFields = {
  breaker_pair_mode:['msnrBreakerPairMode','mode'],
  breaker_pair_min_body_ratio:['msnrBreakerPairBody','percent'],
  breaker_pair_min_displacement_atr:['msnrBreakerPairDisplacement','number'],
  retest_pinbar_mode:['msnrPinbarMode','mode'],
  retest_pinbar_min_wick_ratio:['msnrPinbarWick','percent'],
  retest_pinbar_min_close_ratio:['msnrPinbarClose','percent'],
  session_policy:['msnrSessionPolicy','mode'],
  obstacle_av_definition:['msnrObstacleDefinition','mode'],
  h4_obstacle_mode:['msnrH4ObstacleMode','mode'],
  step_min_adx:['msnrStepExecutionAdx','number'],
  enable_synthetic_daily_storyline_filter:['msnrSyntheticD1Veto','bool'],
  fractal_min_body_ratio:['msnrFractalBodyPercent','percent'],
  fractal_max_entry_distance_atr:['msnrFractalMaxDistanceAtr','number'],
  retest_window_minutes:['msnrRetestWindowMinutes','number'],
  additional_symbols_mode:['msnrAdditionalSymbolsMode','mode'],
  continuation_mode:['msnrContinuationMode','mode'],
  continuation_min_body_ratio:['msnrContinuationBodyPercent','percent'],
  continuation_min_adx:['msnrContinuationAdx','number'],
  continuation_max_entry_distance_atr:['msnrContinuationDistance','number'],
  continuation_maximum_breakout_wick_ratio:['msnrContinuationWick','percent'],
  qm_max_entry_distance_atr:['msnrQmDistance','number'],
  research_min_frequency_ratio:['msnrResearchFrequency','percent'],
  research_min_resolved_trades:['msnrResearchSample','number'],
  research_min_win_rate_improvement_pp:['msnrResearchWinRate','number'],
  continuation_fresh_only:['msnrContinuationFreshOnly','bool'],
  enable_setup_diagnostics:['msnrSetupDiagnostics','bool'],
  enable_structure_cache:['msnrStructureCache','bool'],
  prioritize_pending_retests:['msnrPrioritizeRetests','bool'],
  analysis_outside_entry_lock:['msnrAnalysisOutsideLock','bool'],
  av_entry_mode:['msnrAvEntryMode','mode'],
  av_entry_definition:['msnrAvDefinition','mode'],
  role_flip_mode:['msnrRoleFlipMode','mode'],
  role_flip_max_changes:['msnrRoleFlipMaxChanges','number'],
  role_flip_min_displacement_atr:['msnrRoleFlipDisplacement','number'],
  qm_extended_mode:['msnrQmExtendedMode','mode'],
  qm_extended_swing_window:['msnrQmSwingWindow','number'],
  qm_extended_min_head_depth_atr:['msnrQmHeadDepth','number'],
  macro_structure_mode:['msnrMacroStructureMode','mode'],
  macro_bias_method:['msnrMacroBiasMethod','mode'],
  macro_pivot_radius:['msnrMacroPivotRadius','number'],
  gap_mode:['msnrGapMode','mode'],
  gap_timeframe:['msnrGapTimeframe','mode'],
  gap_min_size_atr:['msnrGapMinSize','number'],
  gap_min_ticks:['msnrGapMinTicks','number'],
  gap_min_spread_multiple:['msnrGapSpreadMultiple','number'],
  adaptive_history_enabled:['msnrAdaptiveHistoryEnabled', 'bool'],
  history_min_h1:['msnrHistoryMinH1', 'number'],
  history_min_d1:['msnrHistoryMinD1', 'number'],
  history_max_request:['msnrHistoryMaxRequest', 'number'],
  m5_confirmation_mode:['msnrM5ConfirmationMode', 'mode'],
  recovery_window_minutes:['msnrRecoveryWindowMinutes', 'number'],
  recovery_min_body_ratio:['msnrRecoveryMinBodyRatio', 'percent'],
  h4_neutral_fallback_mode:['msnrH4NeutralFallbackMode', 'mode'],
  ai_mode:['msnrAiMode', 'mode'],
  ai_incompatible_policy:['msnrAiIncompatiblePolicy', 'mode'],
  ai_min_probability:['msnrAiMinProbability', 'percent'],
  ai_min_probability_forex:['msnrAiMinProbabilityForex', 'percent'],
  ai_min_probability_gold:['msnrAiMinProbabilityGold', 'percent'],
  ai_min_probability_volatility:['msnrAiMinProbabilityVolatility', 'percent'],
  ai_min_net_expectancy_r:['msnrAiMinNetExpectancyR', 'number'],
  enable_candidate_audit:['msnrEnableCandidateAudit', 'bool'],
  observe_candidate_outcomes:['msnrObserveCandidateOutcomes', 'bool'],
  candidate_outcome_hours:['msnrCandidateOutcomeHours', 'number']
};
function msnrFormValues() {
  const values = {};
  for(const [key,[id,type]] of Object.entries(msnrFields)) {
    const input=document.getElementById(id);
    if(type==='bool') values[key]=input.checked;
    else if(type==='mode') values[key]=input.value;
    else {
      values[key]=input.value.trim() && input.checkValidity() ? input.valueAsNumber : NaN;
      if(type==='percent') values[key]/=100;
    }
  }
  values.additional_symbols=msnrCatalog.filter((_,i)=>document.getElementById('msnrExtra'+i)?.checked);
  for(const [key,prefix] of [['asset_modes','msnrAssetMode'],['m5_symbol_modes','msnrAssetM5'],['continuation_symbol_modes','msnrAssetContinuation']]) {
    values[key]={};
    msnrAssetCatalog.forEach((row,i)=>{const value=document.getElementById(prefix+i)?.value;if(value && value!=='inherit') values[key][row.symbol]=value;});
  }
  values.step_symbol_min_adx={};
  msnrAssetCatalog.forEach((row,i)=>{const input=document.getElementById('msnrAssetAdx'+i);if(input?.value.trim()) values.step_symbol_min_adx[row.symbol]=input.valueAsNumber;});
  return values;
}
function msnrFormValid(values) {
  return Array.from(document.querySelectorAll('[id^=msnrAssetAdx]')).every(input=>!input.value.trim() || Number.isFinite(input.valueAsNumber) && input.checkValidity()) && Object.entries(msnrFields).every(([key,[id,type]]) =>
    type==='bool' || type==='mode' || (Number.isFinite(values[key]) && document.getElementById(id).checkValidity()));
}
function msnrDirty(values) {
  if(!msnrSavedSettings) return false;
  return Object.keys(values).some(key => typeof values[key]==='number' ?
    Math.abs(values[key]-msnrSavedSettings[key])>1e-12 : JSON.stringify(values[key])!==JSON.stringify(msnrSavedSettings[key]));
}
function msnrSavedStatus() {
  return 'Guardado: Fractal H1 '+Number((msnrSavedSettings.fractal_min_body_ratio*100).toPrecision(15))+
    '%, distancia '+msnrSavedSettings.fractal_max_entry_distance_atr+' ATR H1, retest '+msnrSavedSettings.retest_window_minutes+
    ' min. D1 en sintéticos '+(msnrSavedSettings.enable_synthetic_daily_storyline_filter?'activado.':'desactivado.');
}
function applyMsnrSettings(settings, remember=true) {
  if(remember) { msnrSavedSettings=settings; renderMsnrActionGuide(settings); }
  for(const [key,[id,type]] of Object.entries(msnrFields)) {
    const input=document.getElementById(id);
    if(type==='bool') input.checked=settings[key];
    else input.value=type==='percent'?Number((settings[key]*100).toPrecision(15)):settings[key];
  }
  msnrCatalog.forEach((symbol,i)=>document.getElementById('msnrExtra'+i).checked=settings.additional_symbols.includes(symbol));
  for(const [key,prefix] of [['asset_modes','msnrAssetMode'],['m5_symbol_modes','msnrAssetM5'],['continuation_symbol_modes','msnrAssetContinuation']])
    msnrAssetCatalog.forEach((row,i)=>document.getElementById(prefix+i).value=settings[key]?.[row.symbol] || 'inherit');
  msnrAssetCatalog.forEach((row,i)=>{const input=document.getElementById('msnrAssetAdx'+i);if(input) input.value=settings.step_symbol_min_adx?.[row.symbol] ?? '';});
}
function setMsnrControlsBusy(busy) {
  document.querySelectorAll('#msnrRuntimeSettings input,#msnrRuntimeSettings select').forEach(input=>input.disabled=busy || !msnrSavedSettings);
  const values=msnrFormValues();
  document.getElementById('msnrSaveSettings').disabled=busy || !msnrSavedSettings || !msnrFormValid(values) || !msnrDirty(values);
  document.getElementById('msnrRefreshSettings').disabled=busy;
  document.getElementById('msnrRestoreDefaults').disabled=busy || !msnrDefaults || !msnrSavedSettings;
}
function markMsnrSettingsChanged() {
  const values=msnrFormValues();
  setMsnrControlsBusy(false);
  document.getElementById('msnrSettingsStatus').textContent=!msnrFormValid(values)?
    'Revisa los campos numéricos: ingresa valores dentro de los límites indicados.':
    msnrDirty(values)?'Cambios pendientes de guardar.':msnrSavedSettings?msnrSavedStatus():'Consultando configuración…';
}
async function requestMsnrSettings(options={}) {
  const response=await fetch('/api/strategies/malaysian-snr/settings',{cache:'no-store',...options});
  const data=await response.json();
  if(!response.ok || !data.ok) throw new Error(data.error || 'No se pudo consultar la configuración.');
  if(!data.settings || typeof data.settings.enable_synthetic_daily_storyline_filter!=='boolean' || !Array.isArray(data.settings.additional_symbols))
    throw new Error('El estado recibido no es válido.');
  return data;
}
function renderMsnrDefaults() {
  const note=document.getElementById('msnrDefaultsNote'); note.replaceChildren();
  const mode={off:'Desactivado',shadow:'Observación',live:'Operar'};
  const lines=[
    'ADX de ejecución Step SNR: 25; por activo Heredar, sin excepciones.',
    'Continuación por defecto: Operar, distancia 0,50 ATR H1, mecha máxima 25%. Quasimodo: distancia 0,50 ATR H1.',
    'Por activo: Heredar la selección y los modos generales. Los activos recuperados guardados se observan hasta cambiar su modo.',
    'Comparación por defecto: frecuencia '+msnrDefaults.research_min_frequency_ratio*100+'%, mejora WinRate '+msnrDefaults.research_min_win_rate_improvement_pp+' puntos, muestra '+msnrDefaults.research_min_resolved_trades+' por variante. Sin promoción automática.',
    'Fractal H1: cuerpo '+msnrDefaults.fractal_min_body_ratio*100+'%; distancia '+msnrDefaults.fractal_max_entry_distance_atr+' ATR H1.',
    'Retest: '+msnrDefaults.retest_window_minutes+' minutos. Exigir D1 en sintéticos: '+(msnrDefaults.enable_synthetic_daily_storyline_filter?'Sí':'No')+'.',
    'Activos adicionales: '+msnrDefaults.additional_symbols.join(', ')+'; modo '+mode[msnrDefaults.additional_symbols_mode]+'.',
    'Continuación A/V: '+mode[msnrDefaults.continuation_mode]+', cuerpo '+msnrDefaults.continuation_min_body_ratio*100+'%, ADX '+msnrDefaults.continuation_min_adx+', exigir Fresh: '+(msnrDefaults.continuation_fresh_only?'Sí':'No')+'.',
    ...['enable_setup_diagnostics','enable_structure_cache','prioritize_pending_retests','analysis_outside_entry_lock'].map(key=>{
      const input=document.getElementById(msnrFields[key][0]); return input.parentElement.textContent.trim()+': '+(msnrDefaults[key]?'Activado':'Desactivado')+'.';
    })
  ];
  for(const key of ['breaker_pair_mode','breaker_pair_min_body_ratio','breaker_pair_min_displacement_atr',
    'retest_pinbar_mode','retest_pinbar_min_wick_ratio','retest_pinbar_min_close_ratio',
    'session_policy','obstacle_av_definition','h4_obstacle_mode',
    'av_entry_mode','av_entry_definition','role_flip_mode','role_flip_max_changes',
    'role_flip_min_displacement_atr','qm_extended_mode','qm_extended_swing_window',
    'qm_extended_min_head_depth_atr','macro_structure_mode','macro_bias_method','macro_pivot_radius',
    'gap_mode','gap_timeframe','gap_min_size_atr','gap_min_ticks','gap_min_spread_multiple',
'adaptive_history_enabled','history_min_h1','history_min_d1','history_max_request','m5_confirmation_mode','recovery_window_minutes','recovery_min_body_ratio','h4_neutral_fallback_mode','ai_mode','ai_incompatible_policy','ai_min_probability','ai_min_probability_forex','ai_min_probability_gold','ai_min_probability_volatility','ai_min_net_expectancy_r','enable_candidate_audit','observe_candidate_outcomes','candidate_outcome_hours']) {
    const input=document.getElementById(msnrFields[key][0]);
    const label=document.querySelector('label[for="'+input.id+'"]');
    const value=input.tagName==='SELECT'?Array.from(input.options).find(o=>o.value===String(msnrDefaults[key]))?.textContent:msnrDefaults[key];
    lines.push((label?label.textContent:input.parentElement.textContent.trim())+': '+(msnrFields[key][1]==='bool'?(msnrDefaults[key]?'Activado':'Desactivado'):msnrFields[key][1]==='percent'?msnrDefaults[key]*100+'%':value)+'.');
  }
  lines.forEach(line=>{const li=document.createElement('li');li.textContent=line;note.appendChild(li);});
}
function restoreMsnrDefaults() {
  if(!msnrDefaults || !msnrSavedSettings) return;
  applyMsnrSettings(msnrDefaults,false); markMsnrSettingsChanged();
  document.getElementById('msnrSettingsStatus').textContent='Valores por defecto cargados. Revisa y pulsa Guardar ajustes para aplicarlos.';
}
async function loadMsnrSettings() {
  setMsnrControlsBusy(true);
  document.getElementById('msnrSettingsStatus').textContent='Consultando configuración…';
  try {
    const data=await requestMsnrSettings(); msnrDefaults=data.defaults; msnrCatalog=data.additional_symbols_catalog; msnrAssetCatalog=data.asset_catalog || [];
    renderMsnrAssetPolicies();
    const box=document.getElementById('msnrAdditionalSymbols'); box.replaceChildren();
    msnrCatalog.forEach((symbol,i)=>{
      const label=document.createElement('label');label.className='msnr-toggle';
      const input=document.createElement('input');input.type='checkbox';input.id='msnrExtra'+i;input.onchange=markMsnrSettingsChanged;
      label.append(input,document.createTextNode(symbol));box.appendChild(label);
    });
    applyMsnrSettings(data.settings); renderMsnrDefaults(); markMsnrSettingsChanged();
    document.getElementById('msnrModelStatus').textContent=data.model_status?.message || '';
    try {
      const audit=await fetch('/api/strategies/malaysian-snr/candidates',{cache:'no-store'}).then(r=>r.json());
      const f=audit.funnel;
      document.getElementById('msnrCandidateFunnel').textContent=audit.ok?
        'Últimos '+f.window_days+' días: '+f.unique_setups+' setups únicos, '+f.confirmed+' confirmados, '+f.executed+' ejecutados; '+f.variants+' variantes y '+f.evaluations+' lecturas. Resultados observados separados del WinRate real.':audit.error;
      const reasons={WAITING_POST_BREAK_RETEST:'Esperando retorno posterior a la ruptura',WAITING_FIRST_RETEST:'Esperando primer retest',LEVEL_CONSUMED:'Nivel consumido',DIRECTION_POLICY_BLOCKED:'Dirección no permitida',SETUP_EXPIRED:'Setup vencido',WAITING_RETEST_RECOVERY:'Esperando recuperación',RETEST_RECOVERY_EXPIRED:'Recuperación vencida'};
      document.getElementById('msnrCandidateBlockers').textContent=audit.ok?
        'Primer motivo registrado: '+(f.first_blockers || []).map(row=>(reasons[row.reason] || row.reason)+': '+row.count).join(' · ')+
        '. Por activo: '+(f.by_symbol || []).map(row=>row.symbol+': '+row.confirmed+'/'+row.unique_setups+' confirmados').join(' · '):'';
    } catch(error) {document.getElementById('msnrCandidateFunnel').textContent='Seguimiento de candidatos aún no disponible.';}

  } catch(error) {msnrSavedSettings=null;document.getElementById('msnrSettingsStatus').textContent=error.message;}
  finally {setMsnrControlsBusy(false);if(typeof pageLoading!=='undefined') pageLoading.done();}
}
async function saveMsnrSettings() {
  const values=msnrFormValues(); if(!msnrFormValid(values)){markMsnrSettingsChanged();return;}
  setMsnrControlsBusy(true);document.getElementById('msnrSettingsStatus').textContent='Guardando ajustes…';
  try {
    const data=await requestMsnrSettings({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)});
    applyMsnrSettings(data.settings);document.getElementById('msnrSettingsStatus').textContent=msnrSavedStatus()+' '+data.message;
  } catch(error) {msnrSavedSettings=null;document.getElementById('msnrSettingsStatus').textContent=error.message+' Actualiza el estado antes de guardar.';}
  finally {setMsnrControlsBusy(false);}
}
'''

PANEL_HTML = PANEL_HTML.replace('  <fieldset><legend>Fractal y contexto</legend>', GUIDE_HTML+'\n  <fieldset><legend>Fractal y contexto</legend>')
PANEL_JS = GUIDE_JS + PANEL_JS
