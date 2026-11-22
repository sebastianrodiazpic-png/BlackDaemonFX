# -*- coding: utf-8 -*-
with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Actualizar CSS del top/title/sub/badge en el dashboard principal
old_css = """.top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 6px;
      }



      .title {



        font-size: 22px;



        font-weight: 800;



      }



      .sub {



        color: var(--muted);



      }



      .badge {



        padding: 7px 10px;



        border: 1px solid var(--line);



        border-radius: 999px;



        background: var(--panel);



      }"""

new_css = """.top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(91, 69, 20, 0.4);
      }

      .title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.02em;
        color: #ffffff;
      }

      .title strong, .title span {
        color: #f6cb57;
      }

      .sub {
        color: #94a3b8;
        font-size: 12px;
        letter-spacing: 0.03em;
        margin-top: 4px;
      }

      .badge {
        padding: 6px 14px;
        border: 1px solid #725116;
        border-radius: 999px;
        background: #0d1214;
        font-size: 11px;
        font-weight: 700;
        color: #ffd465;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 0 12px rgba(215, 155, 25, 0.12);
      }"""

if old_css not in content:
    print("ERROR: old_css no encontrado")
    exit(1)

content = content.replace(old_css, new_css, 1)

# 2. Actualizar HTML del header en el dashboard
old_html = """          <div>



            <div class="title">BLACKDAEMON<strong>FX</strong> · Control operativo</div>



            <div class="sub">ESTRATEGIA · DISCIPLINA · RESULTADOS · Dashboard en tiempo real</div>



          </div>



          <div class="actions">
            <div class="badge" id="status">Conectando...</div>
          </div>"""

new_html = """          <div>
            <div class="title">BLACKDAEMON<strong>FX</strong> · Control operativo</div>
            <div class="sub">ESTRATEGIA · DISCIPLINA · RESULTADOS · Control operativo en tiempo real · Conectado al motor</div>
          </div>
          <div class="actions">
            <div class="badge" id="status">DATOS EN VIVO</div>
          </div>"""

if old_html not in content:
    print("ERROR: old_html no encontrado")
    exit(1)

content = content.replace(old_html, new_html, 1)

# 3. Actualizar JS de actualización del badge para que mantenga el formato píldora compacto
old_js = """            $('status').textContent =



              (s.status || '—') +



              ' · ' +



              (s.daemon_version || 'version ?') +



              ' · ' +



              (s.connection_mode === 'LIVE' ? 'DATOS EN VIVO' : 'ÚLTIMO ESTADO CONOCIDO') +



              ' · ' +



              new Date(s.updated_at).toLocaleTimeString();"""

new_js = """            const liveLabel = s.connection_mode === 'LIVE' ? 'DATOS EN VIVO' : (s.status || 'CONECTADO');
            $('status').textContent = liveLabel;
            $('status').title = (s.status || 'ONLINE') + ' · ' + (s.daemon_version || '') + ' · ' + new Date(s.updated_at).toLocaleTimeString();
            $('status').style.borderColor = '#725116';
            $('status').style.color = '#ffd465';"""

if old_js not in content:
    print("ERROR: old_js no encontrado")
    exit(1)

content = content.replace(old_js, new_js, 1)

# 4. Actualizar JS catch en caso de error
old_catch = """            } catch (e) {



              $('status').textContent = 'Dashboard sin conexión: ' + e.message;



              pageLoading.fail('No se pudieron cargar los datos. Intenta nuevamente.');"""

new_catch = """            } catch (e) {
              $('status').textContent = 'SIN CONEXIÓN';
              $('status').title = 'Dashboard sin conexión: ' + e.message;
              $('status').style.borderColor = 'rgba(239, 68, 68, 0.5)';
              $('status').style.color = '#f87171';
              pageLoading.fail('No se pudieron cargar los datos. Intenta nuevamente.');"""

if old_catch not in content:
    print("ERROR: old_catch no encontrado")
    exit(1)

content = content.replace(old_catch, new_catch, 1)

with open("dashboard/realtime_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("dashboard/realtime_dashboard.py actualizado con éxito.")
