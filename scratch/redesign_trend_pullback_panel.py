# -*- coding: utf-8 -*-
import re

with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(
    r'<div id="trendPullbackAuditPanel" style="display: none; margin-bottom: 24px;">.*?(?=\s*<!-- KPI METRICS GRID -->)',
    re.DOTALL
)

match = pattern.search(content)
if not match:
    print("ERROR: No se encontro el bloque id=\"trendPullbackAuditPanel\"")
    exit(1)

print("Bloque trendPullbackAuditPanel encontrado, longitud:", len(match.group(0)))

new_tp_panel = '''<div id="trendPullbackAuditPanel" style="display: none; margin-bottom: 24px;">
        <div class="card" style="border-left: 4px solid var(--purple); border-top: 1px solid #5b4514; border-right: 1px solid #5b4514; border-bottom: 1px solid #5b4514; background: linear-gradient(180deg, rgba(168, 85, 247, 0.08) 0%, #070a0e 100%);">
          <div class="card-header" style="margin-bottom: 12px;">
            <h2 class="card-title">
              <span class="icon">📈</span>
              Auditoría Replay Fiel 5 Años Trend Pullback H1/M15: Montándonos en la Tendencia con Retrocesos Limpios (+811.45 R Netos)
            </h2>
            <div class="badge badge-purple">Replay Fiel 5 Años · 30 Sintéticos Rentables (+50% Acierto) · 29,373 Trades · 8 Sintéticos & 35 Mercados Reales Podados</div>
          </div>
          <div class="muted" style="font-size: 13.5px; line-height: 1.75; margin-bottom: 18px;">
            Auditoría histórica real de <strong>5 años (1,825 días)</strong> vela a vela sin trucos ni suposiciones sobre el catálogo completo.<br>
            La estrategia <strong>Trend Pullback</strong> es pura disciplina tendencial: <strong>nunca intenta adivinar techos ni pisos, sino que se sube a favor de tendencias fuertes ya confirmadas</strong>. Utiliza dos medias móviles de referencia en 1 hora (EMA 20 rápida y EMA 50 lenta) para identificar la <em>"zona de valor"</em> donde el precio toma un respiro (retroceso o pullback).<br>
            En lugar de entrar a ciegas al primer toque, el bot baja a gráficos de 15 minutos y exige un <strong>quiebre de estructura confirmado</strong> antes de disparar, asegurando que el retroceso terminó y la tendencia se reanuda con fuerza.<br>
            Bajo nuestra <strong>fórmula de 2 órdenes</strong> (asegurar ganancia en ratio 1:1, mover a Break-Even y dejar correr hacia 1:2), <strong>30 índices sintéticos de Deriv demostraron una rentabilidad sólida y consistente (+811.45 veces el riesgo asumido)</strong>. Los 35 activos de mercados reales (Forex, Metales e Índices) quedan en <strong>Poda Preventiva</strong> porque los cierres nocturnos y comisiones de rollover degradan la señal.
          </div>

          <div class="daemon-card-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
            <!-- CARD 1: FILTRO DE TENDENCIA H1 -->
            <div class="daemon-card daemon-card-accent-purple">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">📈 Detección de Tendencia en H1</div>
                  <div class="daemon-card-badge">Zona de Valor EMA 20/50</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Alineación Dinámica:</strong> Solo compramos cuando la media rápida (EMA 20) está claramente por encima de la lenta (EMA 50), y solo vendemos si está por debajo. Prohibido operar en contra de la marea institucional.</div>
                  <div class="daemon-card-bullet">• <strong>El Respiro del Precio (Zona de Valor):</strong> Esperamos con paciencia a que el precio retroceda hacia el espacio entre ambas medias móviles, que actúa como soporte o resistencia dinámico.</div>
                  <div class="daemon-card-bullet">• <strong>Rechazo Visible con Mecha:</strong> La vela de 1 hora debe rebotar con fuerza y cerrar fuera de la zona de medias, demostrando que los compradores o vendedores volvieron a entrar con convicción.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">TREND FOLLOWING · DYNAMIC VALUE ZONE</div>
                </div>
              </div>
            </div>

            <!-- CARD 2: GATILLO EN M15 -->
            <div class="daemon-card daemon-card-accent-green">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🎯 Gatillo Preciso en 15 Minutos</div>
                  <div class="daemon-card-badge">Cero Falsas Rupturas</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Prohibido Entrar al Toque:</strong> El error más común del trader minorista es comprar apenas el precio roza una media móvil, quedando atrapado si el retroceso sigue cayendo con fuerza.</div>
                  <div class="daemon-card-bullet">• <strong>Quiebre de Estructura Confirmado:</strong> Exigimos que en 15 minutos el precio rompa con cuerpo de vela el último swing estructural previo, confirmando que la corrección terminó y arranca el nuevo impulso.</div>
                  <div class="daemon-card-bullet">• <strong>Stop Loss Técnico y Ceñido:</strong> El Stop Loss se ubica exactamente en el extremo del retroceso en M15 con un pequeño colchón de spread, ofreciendo una relación riesgo/beneficio óptima.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">STRUCTURE BREAK · PRECISION TRIGGER</div>
                </div>
              </div>
            </div>

            <!-- CARD 3: SINTÉTICOS DERIV 24/7 -->
            <div class="daemon-card daemon-card-accent-cyan">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">⚡ Sintéticos Deriv (30 Ganadores)</div>
                  <div class="daemon-card-badge">+811.45R Netos · 50.9% WR</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Líderes de Gran Consistencia:</strong> Activos como <code>Volatility 25</code> (+133.25R netos, <strong>58.5% de acierto</strong>), <code>Jump 10</code> (+129.00R, <strong>54.5% acierto</strong>), <code>Crash 300</code> (+120.60R, <strong>66.67% acierto</strong>) y <code>Step 200</code> (+83.75R) generan beneficios constantes año tras año.</div>
                  <div class="daemon-card-bullet">• <strong>Tendencias Limpias sin Noticias:</strong> Los índices sintéticos operan 24 horas continuas sin fines de semana ni noticias geopolíticas imprevistas, permitiendo que los retrocesos técnicos funcionen con máxima regularidad matemática.</div>
                  <div class="daemon-card-bullet">• <strong>Gestión de 2 Órdenes:</strong> La primera orden cobra ganancia fija en 1:1 (TP1) y pasa inmediatamente la segunda a Break-Even, garantizando tranquilidad psicológica total.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">DERIV SYNTHETICS · CONTINUOUS MOMENTUM</div>
                </div>
              </div>
            </div>

            <!-- CARD 4: PODA DE MERCADOS REALES -->
            <div class="daemon-card daemon-card-accent-red">
              <div class="daemon-card-inner">
                <div class="daemon-card-head">
                  <div class="daemon-card-title">🛡️ Protección Contra Ruido y Costes</div>
                  <div class="daemon-card-badge">35 Reales & 8 Sintéticos OFF</div>
                </div>
                <div class="daemon-card-body">
                  <div class="daemon-card-bullet">• <strong>Forex y Metales Descartados (35 Activos):</strong> Los cierres diarios de mercado, las sesiones asiáticas sin volumen y los altos cobros de rollover nocturno (*swap*) destruyen la expectativa matemática del pullback en 15 minutos.</div>
                  <div class="daemon-card-bullet">• <strong>8 Sintéticos en Pausa Preventiva:</strong> Índices con exceso de ruido errático o comisiones elevadas (como <code>Crash 1000</code> o <code>HF Vol 50</code>) se mantienen en OFF para no regalar comisiones.</div>
                  <div class="daemon-card-bullet">• <strong>Confinamiento Inteligente:</strong> La estrategia opera exclusivamente en los 30 índices sintéticos con ventaja estadística demostrada, preservando el capital y optimizando el acierto.</div>
                </div>
                <div class="daemon-card-plate">
                  <div class="daemon-card-plate-text">BLACKDAEMON FX</div>
                  <div class="daemon-card-plate-sub">CAPITAL SHIELD · FILTERED PAIRS ONLY</div>
                </div>
              </div>
            </div>
          </div>

          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; padding-top: 14px; border-top: 1px solid #1e2b37;">
            <span class="muted" style="font-size: 12.5px;">
              💡 Todos los activos evaluados de Trend Pullback y su estado operativo están sincronizados en tiempo real con <a href="/instruments" style="color: #f4c84f; text-decoration: underline; font-weight: 600;">/instruments</a>.
            </span>
            <a href="/instruments" class="btn" style="border-color: #765719; color: #f4c84f;">Ver Catálogo de Instrumentos Sincronizado →</a>
          </div>
        </div>
      </div>'''

new_content = content[:match.start()] + new_tp_panel + content[match.end():]

with open("dashboard/strategy_bases_page.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("trendPullbackAuditPanel rediseñado con éxito.")
