with open('dashboard/decisions_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        <div class="note">
          <b>Cómo leer esta página.</b> Cada señal pasa por tres pilares antes de operar: la <b>Estrategia</b> (trae SL y TP),
          el <b>Criterio Humano</b> (puntaje 0–100, tendencia H1, régimen, vela clímax, spike, racha, spread) y el <b>filtro de IA</b>
          (meta-etiquetado; hoy en modo sombra). La <b>Tripartita</b> junta los tres veredictos. Cada decisión se guarda con su
          <code>execution_key</code>: en el evento de auditoría (aprobadas y vetadas) y dentro del trade (<code>details.metadata.entry_decision</code>),
          que es lo que permite medir después si un veto evitó una pérdida o recortó una ganancia.
        </div>"""

replacement = """        <div class="note">
          <b>Cómo leer esta página.</b> Cada señal pasa por tres pilares antes de operar: la <b>Estrategia</b> (trae SL y TP),
          el <b>Criterio Humano</b> (puntaje 0–100, tendencia H1, régimen, vela clímax, spike, racha, spread) y el <b>filtro de IA</b>
          (meta-etiquetado; hoy en modo sombra). La <b>Tripartita</b> junta los tres veredictos. Cada decisión se guarda con su
          <code>execution_key</code>: en el evento de auditoría (aprobadas y vetadas) y dentro del trade (<code>details.metadata.entry_decision</code>),
          que es lo que permite medir después si un veto evitó una pérdida o recortó una ganancia.
        </div>
        <div class="note" style="border-left-color: var(--g); background: rgba(0, 219, 121, 0.05); margin-top: 10px;">
          <b>⚡ MultiStrategia Activa en Familia Step:</b> En los índices <code>Step Index</code>, <code>Step Index 200</code>, <code>Step Index 300</code>, <code>Step Index 400</code> y <code>Step Index 500</code> (Worker STEP · Magic 26082104), el motor evalúa concurrentemente <b>Malaysian SNR</b> (con gatillo M5 y pinbar &ge; 55%) e <b>ICT Sabri Malle</b>. Cada trade y análisis queda etiquetado con su estrategia de origen y confluencia AAA para auditoría transparente.
        </div>"""

norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

if target_norm in norm:
    norm = norm.replace(target_norm, replacement_norm, 1)
    with open('dashboard/decisions_page.py', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(norm)
    print("SUCCESS: decisions_page.py updated")
else:
    print("ERROR: target not found in decisions_page.py")
