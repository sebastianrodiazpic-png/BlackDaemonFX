# -*- coding: utf-8 -*-
"""
Script para actualizar y humanizar la Sección 4:
'Fundamentos y Reglas de Ejecución de las Estrategias Implementadas'
convirtiéndola al diseño legendario (.daemon-card) e incorporando las 4 estrategias.
"""

import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ubicar la Sección 4
sec4_pattern = re.compile(
    r'(<!-- SECCIÓN 4: BASES TEÓRICAS Y REGLAS OPERATIVAS DE LAS ESTRATEGIAS -->\s*<section class="card"[^>]*>.*?)(?=</main>\s*</div>\s*<script>)',
    re.DOTALL
)

m = sec4_pattern.search(content)
if not m:
    print("ERROR: No se encontró la Sección 4!")
    # Intentar buscar solo <section class="card">\s*<div class="card-header">\s*<h2 class="card-title">\s*<span class="icon">📚</span>\s*Fundamentos y Reglas
    sec4_alt = re.compile(
        r'(<section class="card"[^>]*>\s*<div class="card-header"[^>]*>\s*<h2 class="card-title"[^>]*>\s*<span class="icon">📚</span>\s*Fundamentos y Reglas.*?)(?=</main>\s*</div>\s*<script>)',
        re.DOTALL
    )
    m = sec4_alt.search(content)
    if not m:
        print("ERROR ALT: Tampoco se encontró con patrón alternativo!")
        sys.exit(1)

print("Sección 4 encontrada, longitud:", len(m.group(0)))

new_sec4_html = '''<!-- SECCIÓN 4: BASES TEÓRICAS Y REGLAS OPERATIVAS DE LAS ESTRATEGIAS -->
      <section class="card" style="border: 1px solid rgba(215, 155, 25, 0.35); border-radius: 14px; background: #0c1015; padding: 20px; margin-bottom: 24px;">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(91, 69, 20, 0.4); padding-bottom: 14px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
          <h2 class="card-title" style="margin: 0; font-size: 17px; font-weight: 800; color: #ffffff; display: flex; align-items: center; gap: 9px; letter-spacing: -0.01em;">
            <span class="icon">📑</span>
            Fundamentos y Reglas de Ejecución de las Estrategias Implementadas
          </h2>
          <div style="border: 1px solid #725116; border-radius: 999px; padding: 5px 14px; background: #0d1214; color: #ffd465; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">
            Arquitectura Institucional BlackDaemonFX · 4 Motores de Alta Probabilidad
          </div>
        </div>

        <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; margin-bottom: 8px;">

          <!-- ESTRATEGIA 1: MALAYSIAN SNR -->
          <div class="daemon-card" style="--strat-accent: var(--g); --strat-glow: rgba(0, 219, 121, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">🇲🇾 1. Malaysian SNR Institucional</div>
                <div class="daemon-card-badge">64 Ganadores · 63.8% WR</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Lectura milimétrica de soportes y resistencias sobre <strong>precios de cierre reales (gráfico de líneas H1)</strong>, eliminando por completo el ruido engañoso de las mechas. Espera a que el mercado barra a los impacientes y confirma el cambio de tendencia antes de disparar.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    🔑 Niveles Sin Ruido (Cierres H1/H4/D1)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Trazamos zonas solo en precios de cierre. Si una vela deja solo mecha pero no cierra más allá, se considera trampa de liquidez y no se autoriza ninguna orden.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Regla Estricta de los 2 Toques
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Un nivel solo es confiable las primeras 2 visitas del precio. Al tercer toque se descarta inmediatamente porque la liquidez se agota y suele romperse en contra.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Retesteo de Quiebre (+4.4R Ganador)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    La entrada óptima comprobada es el retesteo directo a la zona rota. Descartamos entrar a la mitad de mechas (-17.9R) o bloques profundos (-25.7R) por alta tasa de fallo.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--g); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--g); text-transform: uppercase; margin-bottom: 3px;">
                    ⚖️ Doble Orden (50% + 50%) a Riesgo Cero
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    La orden 1 cobra beneficio en 1:1 (TP1) y pasa inmediatamente la orden 2 a <strong>Break-Even (cero riesgo)</strong> para buscar 1:2 o 1:4, eliminando rachas perdedoras.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">10,288 Trades · 63.8% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: var(--g); margin-top: 2px;">+3,093.36 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">ALCHEMIST INSTITUTIONAL · DUAL-LEG ENGINE</div>
              </div>
            </div>
          </div>

          <!-- ESTRATEGIA 2: ORB NEW YORK SWEEP -->
          <div class="daemon-card" style="--strat-accent: #f5bd36; --strat-glow: rgba(245, 189, 54, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">🗽 2. ORB New York Sweep</div>
                <div class="daemon-card-badge">11 Ganadores · +177.12R</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Captura la apertura bursátil más líquida del mundo: <strong>Wall Street (09:30 a 11:30 NY)</strong>. Deja que el mercado manipule los primeros 15 minutos para atrapar a traders impacientes, montándose en la verdadera expansión institucional.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    ⏱️ Rango de Apertura Inicial (09:30 a 09:45 NY)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Medimos los extremos con 3 velas M5 cerradas. Jamás disparamos de inmediato: dejamos que el volumen institucional defina los techos y pisos de liquidez.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    🧹 Barrido de Trampa (Sweep) Obligatorio
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Exige que el precio barra primero los máximos/mínimos de Londres o Asia antes de reingresar al rango. Si no hay barrido previo, la señal se cancela por riesgo de trampa.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    🛑 Stop Loss al 50% del Rango (Equilibrium)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    El Stop Loss se ubica estrictamente en el 50% del rango de apertura con desplazamiento confirmado, cortando rápido cualquier pérdida antes de que crezca.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid #f5bd36; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: #f5bd36; text-transform: uppercase; margin-bottom: 3px;">
                    🚫 Poda de Sintéticos 24/7 y Pares con Ruido
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Los 38 sintéticos quedan apagados por no tener apertura física en Wall Street, operando solo activos core comprobados (Oro, Bitcoin, USDCAD, GBPUSD y WTI).
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">4,169 Trades · 56.5% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: #f5bd36; margin-top: 2px;">+177.12 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">WALL STREET OPEN · LIQUIDITY SWEEP</div>
              </div>
            </div>
          </div>

          <!-- ESTRATEGIA 3: ICT SMART MONEY & IA -->
          <div class="daemon-card" style="--strat-accent: var(--cyan); --strat-glow: rgba(56, 189, 248, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">🏛️ 3. Estrategia ICT con IA</div>
                <div class="daemon-card-badge">59 Ganadores · +8,038R</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Sigue la huella del dinero de los grandes fondos bancarios detectando <strong>vacíos de liquidez (Fair Value Gaps en M15)</strong>. Cada entrada es validada por un modelo de Inteligencia Artificial que descarta falsas señales con 83% de precisión.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Entradas en el 50% del Vacío (FVG M15)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    No perseguimos el precio cuando se dispara: esperamos con orden límite en la mitad del vacío de liquidez (Consequent Encroachment) para entrar con el mejor descuento.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    🤖 Filtro Predictivo con IA (83% Precisión)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Nuestro modelo de Inteligencia Artificial analiza el contexto previo; si la señal ocurre en un rango sucio o la probabilidad cae de 55%, la operación se bloquea al instante.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Cierre Intradía Anti-Swap (Cero Rollover)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    En Forex y Metales, todas las órdenes cierran antes de las 16:30 NY, evitando comisiones nocturnas de swap bancario y blindando +68.6R adicionales en ganancias.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--cyan); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--cyan); text-transform: uppercase; margin-bottom: 3px;">
                    ⚡ Especialidad en Sintéticos (33 Activos ON)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Rinde con máxima regularidad en Crash 300 (+170.3R netos, 66.98% acierto) y Volatility 25 (+55.3R), excluyendo 14 pares con ruido para proteger tu cuenta.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">37,918 Trades · 60.5% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: var(--cyan); margin-top: 2px;">+8,038.81 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">SMART MONEY CONCEPTS · AI VALIDATOR</div>
              </div>
            </div>
          </div>

          <!-- ESTRATEGIA 4: TREND PULLBACK H1/M15 -->
          <div class="daemon-card" style="--strat-accent: var(--purple); --strat-glow: rgba(192, 132, 252, 0.28);">
            <div class="daemon-card-inner">
              <div class="daemon-card-head">
                <div class="daemon-card-title">📈 4. Trend Pullback H1/M15</div>
                <div class="daemon-card-badge">30 Ganadores · +811.45R</div>
              </div>

              <div class="daemon-card-body">
                <div style="font-size: 12.5px; color: #e2e8f0; line-height: 1.6; margin-bottom: 14px;">
                  Estrategia tendencial de continuación pura diseñada para la regularidad continua de los <strong>índices sintéticos de Deriv (24/7)</strong>. Nunca intenta adivinar techos ni pisos: se sube con disciplina a tendencias ya confirmadas.
                </div>

                <!-- REGLA 1 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    📈 Dirección Obligatoria en H1 (EMA 20/50)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Solo compramos si la media rápida (EMA 20) viaja por encima de la lenta (EMA 50), y solo vendemos si está por debajo. Prohibido operar contra la marea institucional.
                  </div>
                </div>

                <!-- REGLA 2 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    🌊 Zona de Valor y Rechazo con Mecha
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Esperamos a que el precio retroceda hacia el canal entre ambas medias y cierre fuera de él demostrando absorción activa, evitando entrar cuando el precio está sobreextendido.
                  </div>
                </div>

                <!-- REGLA 3 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    🎯 Gatillo en M15 con Quiebre Estructural
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    No entramos por simple toque: bajamos a 15 minutos y exigimos rompimiento confirmado del último swing, garantizando que el retroceso terminó y arranca el impulso.
                  </div>
                </div>

                <!-- REGLA 4 -->
                <div style="background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid var(--purple); border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                  <div style="font-size: 11px; font-weight: 800; color: var(--purple); text-transform: uppercase; margin-bottom: 3px;">
                    🛡️ Poda de Forex y Metales (35 Activos OFF)
                  </div>
                  <div style="font-size: 11.5px; color: #cbd5e1; line-height: 1.5;">
                    Confinada 100% a 30 sintéticos continuos. Los 35 pares de mercados reales quedan en OFF porque los cierres diarios y falta de volumen nocturno rompen la fluidez tendencial.
                  </div>
                </div>

                <!-- STATS -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Replay 5 Años</div>
                    <div style="font-size: 12px; font-weight: 900; color: #fff; margin-top: 2px;">29,373 Trades · 50.9% WR</div>
                  </div>
                  <div style="background: rgba(0, 0, 0, 0.45); border-radius: 7px; padding: 7px 9px; border: 1px solid rgba(255, 255, 255, 0.06);">
                    <div style="font-size: 9.5px; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Retorno Neto</div>
                    <div style="font-size: 12px; font-weight: 900; color: var(--purple); margin-top: 2px;">+811.45 R Netos</div>
                  </div>
                </div>
              </div>

              <div class="daemon-card-plate">
                <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                <div class="daemon-card-plate-sub">TREND FOLLOWING · DYNAMIC VALUE ZONE</div>
              </div>
            </div>
          </div>

        </div>
      </section>

      '''

new_content = content[:m.start()] + new_sec4_html + content[m.end():]

with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Sección 4 actualizada con éxito.")
