



      const $ = (id) => document.getElementById(id),



        esc = (v) =>



          String(v ?? '').replace(



            /[&<>"']/g,



            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[c],



          );



      let state = null,



        dirty = false,



        activeProfile = 'SYNTHETICS';



      const PROFILE_STRATEGY_INFO = {



        SYNTHETICS: {



          badge: 'ESTRATEGIA ICT (SABRI MALLE · 24/7)',



          color: '#38bdf8',



          workersText: 'CRASH · BOOM · STEP · JUMP · VOLATILITY (1-4)',



          desc: 'Esta pestaña opera bajo la Estrategia ICT Sabri Malle (Judas Swing + FVG + OTE + GBDT >= 0.55) y controla en paralelo los workers CRASH, BOOM, STEP, JUMP y VOLATILITY (1-4). Los instrumentos rentables permanecen activos y los podados desactivados.',



        },



        FOREX: {



          badge: 'ESTRATEGIA ICT (SABRI MALLE · KILLZONES)',



          color: '#38bdf8',



          workersText: 'FOREX (1-4): FOREX_1 · FOREX_2 · FOREX_3 · FOREX_4',



          desc: 'Esta pestaña opera bajo la Estrategia ICT Sabri Malle con filtro de Killzones Institucionales (Londres/NY) y controla los workers FOREX (1-4) por familia de divisa.',



        },



        ICT: {



          badge: 'ESTRATEGIA ICT (SABRI MALLE · METALES, CRIPTO & ÍNDICES)',



          color: '#38bdf8',



          workersText: 'ICT (Metales, Cripto & Índices)',



          desc: 'Esta pestaña opera bajo la Estrategia ICT Sabri Malle dedicada a Metales (XAUUSD, XAGUSD), Cripto (BTCUSD) e Índices/Energía (US Oil, Wall Street 30, US Tech 100, US SP 500) y controla el worker ICT.',



        },



        MALAYSIAN_SNR: {



          badge: 'ESTRATEGIA MALAYSIAN SNR (M15 FRESH/BREAK · C2)',



          color: '#fbbf24',



          workersText: 'Malaysian SNR (M15 Fresh/Break)',



          desc: 'Controla el worker Malaysian SNR (M15 Fresh/Break) con configuración C2 (ADX >= 30, ATR <= 1.2 en Forex/Metales, ATR <= 1.5 en Sintéticos y Wall Street 30, Cap=1). Muestra en paralelo los 23 activos rentables activos y mantiene los 37 podados desactivados.',



        },



        ORB: {



          badge: 'ESTRATEGIA ORB NEW YORK (M5 SWEEP / HTF_SWEEP)',



          color: '#34d399',



          workersText: 'ORB · Apertura New York',



          desc: 'Controla el worker ORB New York enfocado en los 4 activos rentables en modo SWEEP / HTF_SWEEP (XAUUSD, BTCUSD, XAGUSD, US Oil -> 231 trades, 56.7%-59.1% WR, +31.54R) manteniendo podados los índices perdedores.',



        },



        TREND_PULLBACK: {



          badge: 'ESTRATEGIA TREND PULLBACK (H1+M15 · SINTÉTICOS >51% WR)',



          color: '#c084fc',



          workersText: 'Trend Pullback [H1+M15]',



          desc: 'Esta pestaña opera bajo la Estrategia Cuantitativa Trend Pullback H1+M15 (EMA50/200 + ADX>=20 en H1, pullback EMA21 + RSI en M15, 2 patas TP1/TP2 con BE automático). Controla el worker dedicado TREND_PULLBACK con los 21 activos que superan el 51% de Win Rate y R neto > 0 en el replay multianual 5Y.',



        },



      };



      function visibleInstrumentGroups(s) {



        return (s.instrument_catalog || [])



          .filter(



            (g) =>



              String(g.category || '').toLowerCase() !== 'flip' &&



              String(g.selection_profile || '').toUpperCase() !== 'IDX_OPEN',



          )



          .map((g) => ({



            ...g,



            symbols: (g.symbols || []).filter((sym) => {



              if (String(g.selection_profile || '').toUpperCase() === 'MALAYSIAN_SNR') return true;



              return !(/boom/i.test(sym) && /crash/i.test(sym));



            }),



          }))



          .filter((g) => g.symbols.length);



      }



            function groups(s) {
        const rawList = visibleInstrumentGroups(s).filter(
          (g) => String(g.selection_profile || 'SYNTHETICS').toUpperCase() === activeProfile,
        );

        if (activeProfile === 'FOREX') {
          const allForex = rawList.flatMap((g) => g.symbols || []);
          const majorsSet = new Set(['EURUSD', 'EURUSDmicro', 'GBPUSD', 'GBPUSDmicro', 'USDJPY', 'USDJPYmicro', 'USDCAD', 'USDCADmicro', 'USDCHF', 'USDCHFmicro', 'AUDUSD', 'AUDUSDmicro', 'NZDUSD', 'NZDUSDmicro']);
          const eurGbpSet = new Set([
            'EURJPY', 'EURJPYmicro', 'EURCHF', 'EURCHFmicro', 'EURGBP', 'EURGBPmicro', 'EURAUD', 'EURAUDmicro', 'EURCAD', 'EURCADmicro', 'EURNZD', 'EURNZDmicro',
            'GBPJPY', 'GBPJPYmicro', 'GBPCHF', 'GBPCHFmicro', 'GBPAUD', 'GBPAUDmicro', 'GBPCAD', 'GBPCADmicro', 'GBPNZD', 'GBPNZDmicro'
          ]);
          
          const majors = allForex.filter(x => majorsSet.has(x));
          const eurGbp = allForex.filter(x => eurGbpSet.has(x));
          const crossOther = allForex.filter(x => !majorsSet.has(x) && !eurGbpSet.has(x));

          return [
            { category: 'forex_majors', selection_profile: 'FOREX', label: 'Forex · Pares Mayores (USD)', symbols: majors },
            { category: 'forex_eurgbp', selection_profile: 'FOREX', label: 'Forex · Cruces EUR & GBP', symbols: eurGbp },
            { category: 'forex_crosses', selection_profile: 'FOREX', label: 'Forex · Cruces Menores (AUD/NZD/CAD/CHF/JPY)', symbols: crossOther }
          ].filter(g => g.symbols.length);
        }

        if (activeProfile === 'TREND_PULLBACK') {
          const allTpb = rawList.flatMap((g) => g.symbols || []);
          const crashBoom = allTpb.filter(x => /crash|boom/i.test(x));
          const stepJump = allTpb.filter(x => /step|jump/i.test(x));
          const volSpec = allTpb.filter(x => /high frequency|volswitch|vol over/i.test(x));
          const volStd = allTpb.filter(x => /volatility/i.test(x) && !volSpec.includes(x));

          return [
            { category: 'tpb_crash_boom', selection_profile: 'TREND_PULLBACK', label: 'Trend Pullback · Crash & Boom', symbols: crashBoom },
            { category: 'tpb_vol_std', selection_profile: 'TREND_PULLBACK', label: 'Trend Pullback · Volatility Index', symbols: volStd },
            { category: 'tpb_step_jump', selection_profile: 'TREND_PULLBACK', label: 'Trend Pullback · Step & Jump', symbols: stepJump },
            { category: 'tpb_vol_spec', selection_profile: 'TREND_PULLBACK', label: 'Trend Pullback · Especiales & HF', symbols: volSpec }
          ].filter(g => g.symbols.length);
        }

        if (activeProfile === 'SYNTHETICS') {
          const res = [];
          for (const g of rawList) {
            if (g.category === 'volatility') {
              const allVol = g.symbols || [];
              const vol1s = allVol.filter(x => /\(1s\)/i.test(x));
              const volSpec = allVol.filter(x => /high frequency|volswitch|vol over/i.test(x));
              const volStd = allVol.filter(x => !vol1s.includes(x) && !volSpec.includes(x));

              if (volStd.length) res.push({ category: 'vol_std', selection_profile: 'SYNTHETICS', label: 'Volatility Index (Estándar)', symbols: volStd });
              if (vol1s.length) res.push({ category: 'vol_1s', selection_profile: 'SYNTHETICS', label: 'Volatility Index (1s)', symbols: vol1s });
              if (volSpec.length) res.push({ category: 'vol_spec', selection_profile: 'SYNTHETICS', label: 'Volatility Especiales & HF', symbols: volSpec });
            } else {
              res.push(g);
            }
          }
          return res;
        }

        if (activeProfile === 'ORB') {
          const orbOrder = {
            'orb_ny_xauusd': 1,
            'orb_ny_xagusd': 2,
            'orb_ny_us_oil': 3,
            'orb_ny_btcusd': 4,
            'orb_ny_ethusd': 5,
            'orb_ny_eurusd': 6,
            'orb_ny_gbpusd': 7,
            'orb_ny_audusd': 8,
            'orb_ny_usdcad': 9,
            'orb_ny_usdchf': 10,
            'orb_ny_usdjpy': 11,
            'orb_ny_wall_street_30': 12,
            'orb_ny_us_tech_100': 13,
            'orb_ny_us_500': 14,
          };
          return rawList.sort((a, b) => (orbOrder[a.category] || 99) - (orbOrder[b.category] || 99));
        }

        return rawList;
      }



      function selectionSummary(s) {



        return (



          ['SYNTHETICS', 'FOREX', 'ORB', 'MALAYSIAN_SNR', 'ICT', 'TREND_PULLBACK']



            .map((p, i) => {



              const allowed = new Set(



                visibleInstrumentGroups(s)



                  .filter((g) => String(g.selection_profile || 'SYNTHETICS').toUpperCase() === p)



                  .flatMap((g) => g.symbols),



              );



              return (



                ['Sintéticos [ICT]', 'Forex [ICT]', 'ORB', 'Malaysian SNR', 'ICT (Metales, Cripto & Índices)', 'Trend Pullback (>51% WR)'][i] +



                ': ' +



                ((s.selection_profiles || {})[p] || []).filter((x) => allowed.has(x)).length



              );



            })



            .join(' · ') + ' · selecciones independientes'



        );



      }



      function ictFamilyLabel(sym) {



        const l = String(sym || '').toLowerCase();



        if (activeProfile === 'FOREX') return 'Worker Forex';



        if (l.includes('boom')) return 'Worker Boom';



        if (l.includes('crash')) return 'Worker Crash';



        if (l.includes('step')) return 'Worker Step';



        if (l.includes('jump')) return 'Worker Jump';



        if (l.includes('vol')) return 'Worker Volatility';



        if (l.includes('xau')) return 'Worker ICT · Oro';



        if (l.includes('oil')) return 'Worker ICT · Petróleo';



        if (l.includes('wall street') || l.includes('tech 100') || l.includes('sp 500')) return 'Worker ICT · Índices';



        return 'Worker ICT';



      }



      function msnrFamilyLabel(sym) {
        const l = String(sym || '').toLowerCase();
        if (l.startsWith('dex ')) return 'DEX';
        if (l.includes('vol over boom') || l.includes('vol over crash')) return 'Volatility';
        if (l.includes('boom')) return 'Boom (BUY)';
        if (l.includes('crash')) return 'Crash (SELL)';
        if (l.includes('step')) return 'Step';
        if (l.includes('jump')) return 'Jump';
        if (l.includes('volatility') || l.includes('vol ') || l.includes('volswitch')) return 'Volatility';
        // Mercados Reales
        if (/^xa[ug]|^xpt/.test(l)) return 'Metal';
        if (/^[a-z]{6}(?:micro)?$/.test(l)) return 'Forex';
        if (l.includes('oil') || l.includes('brent')) return 'Energía';
        if (l.includes('btc') || l.includes('eth')) return 'Cripto';
        return 'Índice';
      }



      function selected() {



        return [...document.querySelectorAll('input[data-symbol]:checked')]



          .map((x) => x.dataset.symbol)



          .sort((a, b) => a.localeCompare(b, 'es'));



      }



      function updateCount() {



        const allInputs = [...document.querySelectorAll('input[data-symbol]')];



        const checkedCnt = allInputs.filter((x) => x.checked).length;



        const prunedOffCnt = allInputs.filter((x) => !x.checked && x.dataset.pruned === 'true').length;



        $('selectedCount').textContent = checkedCnt;



        if ($('prunedOffCount')) $('prunedOffCount').textContent = prunedOffCnt;



      }



      async function toggleWorkerFromInstruments(workerProfile, enableFlag) {



        if (!enableFlag && !confirm(`¿Desactivar el worker ${workerProfile}? No se puede desactivar si mantiene posiciones abiertas.`)) {



          return;



        }



        try {



          const r = await fetch(`/api/workers/${encodeURIComponent(workerProfile)}/enabled`, {



            method: 'POST',



            headers: { 'Content-Type': 'application/json' },



            body: JSON.stringify({ enabled: Boolean(enableFlag) }),



          });



          const data = await r.json();



          if (!r.ok || !data.ok) throw new Error(data.error || 'No se pudo cambiar el estado del worker');



          $('msg').textContent = `Worker ${workerProfile}: ${enableFlag ? 'REACTIVADO' : 'DESACTIVADO'}`;



          await load();



        } catch (e) {



          $('msg').textContent = 'Error controlando worker: ' + e.message;



        }



      }



      function renderTabWorkers(s) {
        const banner = $('strategyHighlightBanner');
        if (banner) {
          banner.style.display = 'none';
          banner.innerHTML = '';
        }
        const panel = $('tabWorkerPanel');
        if (panel) {
          panel.style.display = 'none';
          panel.innerHTML = '';
        }
      }

      function renderNews(s) {



        const n = s.financial_news || {},



          items = n.items || [];



        $('newsStatus').textContent =



          `${n.status || 'SIN DATOS'} · ${n.updated_at ? new Date(n.updated_at).toLocaleTimeString() : 'sin actualización'}`;



        $('newsList').innerHTML = items.length



          ? items



              .slice(0, 8)



              .map(



                (x) =>



                  `<div style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact || 'MEDIO')}</span> <a href="${esc(x.link)}" target="_blank" rel="noopener" style="color:var(--text)">${esc(x.title)}</a><div class="sub">${x.published_at ? new Date(x.published_at).toLocaleString('es-ES') : ''}</div></div>`,



              )



              .join('')



          : 'No hay noticias disponibles; se conserva el último estado conocido.';



      }



      function render(s) {



        state = s;



        renderNews(s);



        const chosen = new Set((s.selection_profiles || {})[activeProfile] || []),



          prunedByProfile = s.pruned_instruments_by_profile || {},



          prunedInfo = prunedByProfile[activeProfile] || s.pruned_instruments || {},



          prioritized = new Set((s.prioritized_symbols || {})[activeProfile] || []),



          policyProfiles = new Set(s.ict_policy_profiles || []),



          q = $('search').value.trim().toLocaleLowerCase('es'),



          gs = groups(s);



        $('grid').innerHTML =



          gs



            .map((g) => {



              const items = (g.symbols || []).filter((x) => x.toLocaleLowerCase('es').includes(q));



              let displayLabel = g.label;
              if (activeProfile === 'MALAYSIAN_SNR' && displayLabel.startsWith('Malaysian SNR · ')) {
                displayLabel = displayLabel.replace('Malaysian SNR · ', '');
              } else if (activeProfile === 'TREND_PULLBACK' && displayLabel.startsWith('Trend Pullback · ')) {
                displayLabel = displayLabel.replace('Trend Pullback · ', '');
              }

              const isIctTab = ['SYNTHETICS', 'FOREX', 'ICT'].includes(activeProfile);
              const stratTag = isIctTab
                ? `<span class="cardTag tagIct">ICT Sabri Malle</span>`
                : activeProfile === 'MALAYSIAN_SNR'
                  ? `<span class="cardTag tagMsnr">M15 Fresh/Break</span>`
                  : activeProfile === 'ORB'
                    ? `<span class="cardTag tagOrb">ORB SWEEP</span>`
                    : activeProfile === 'TREND_PULLBACK'
                      ? `<span class="cardTag tagTp">H1+M15 &gt;51% WR</span>`
                      : '';

              return items.length
                ? `<section class="group">
                    <div class="groupHeader">
                      <h3><span>${esc(displayLabel)}</span> <span class="groupCount">(${items.length})</span></h3>
                      ${stratTag}
                    </div>
                    <div class="groupItems">
                      ${items.map((sym) => {
                        const isChecked = chosen.has(sym);
                        const isPrioritized = prioritized.has(sym);
                        const isPruned = !isPrioritized && (Boolean(prunedInfo[sym]) || (prioritized.size > 0 && !isPrioritized));
                        const warning = prunedInfo[sym] || (isPruned ? 'Poda preventiva: Descartado en el análisis multi-anual por baja expectativa matemática.' : '');
                        const isPolicyTab = policyProfiles.has(activeProfile);
                        let badge = isPruned
                          ? `<span class="badge pruneBadge" title="${esc(warning)}">⛔ PODADO</span>`
                          : `<span class="badge activeBadge" title="Instrumento operable con ventaja matemática confirmada">✓ ACTIVO</span>`;
                        const selectiveAllowed = Boolean(s.allow_selective_activation ?? true) && ['FOREX', 'SYNTHETICS', 'ICT'].includes(activeProfile);
                        const locked = isPolicyTab && isPruned && !selectiveAllowed;
                        return `<label class="item ${isPruned ? 'prunedItem' : ''}" ${locked || isPruned ? `title="${esc(warning)}"` : ''}><input type="checkbox" data-symbol="${esc(sym)}" ${isChecked && !locked ? 'checked' : ''} ${locked ? 'disabled data-locked="true"' : ''} ${isPruned ? `data-pruned="true" data-warning="${esc(warning)}"` : ''}><span class="symName">${esc(sym)}</span>${badge}</label>`;
                      }).join('')}
                    </div>
                  </section>`
                : '';



            })



            .join('') || '<div class="sub">No se encontraron instrumentos para este perfil.</div>';



        $('totalCount').textContent = gs.reduce((n, g) => n + (g.symbols || []).length, 0);



        $('msg').textContent = selectionSummary(s);



        const profBtn = $('selectProfitable');
        if (profBtn) {
          profBtn.textContent = '✓ Seleccionar solo ACTIVOS (excluir PODADOS)';
        }
        $('profileNote').innerHTML =
          (new Set(s.ict_policy_profiles || []).has(activeProfile)
            ? `<b>${activeProfile}:</b> esta pestaña controla ${activeProfile === 'TREND_PULLBACK' ? 'el worker Trend Pullback (sintéticos >51% WR)' : activeProfile === 'MALAYSIAN_SNR' ? 'el worker Malaysian SNR (sintéticos y mercados reales validados >50% WR)' : `los workers ICT (${activeProfile === 'SYNTHETICS' ? 'Step, Jump, Volatility 1 (Activos) + Volatility 2 (Podados OFF), Boom y Crash' : activeProfile === 'FOREX' ? 'Forex 1 (Activos) + Forex 2 (Podados OFF)' : 'ICT: metales, índices y commodities'})`}. Marcado = el worker lo escanea en el próximo ciclo; PODA PREVENTIVA = desactivado por defecto (activable de manera selectiva con confirmación). La selección se guarda en la base y persiste tras reiniciar.`
            : `<b>${activeProfile}:</b> selección persistente independiente sincronizada con Modo Centinela, Análisis Recientes y progreso de Workers en paralelo. Los instrumentos rentables están activos y los podados desactivados.`);



        document



          .querySelectorAll('.profileTab')



          .forEach((b) => b.classList.toggle('active', b.dataset.profile === activeProfile));



        document.querySelectorAll('input[data-symbol]').forEach((cb) =>



          cb.addEventListener('change', () => {



            const sym = cb.dataset.symbol;



            const isPruned = cb.dataset.pruned === 'true';



            const warning = cb.dataset.warning || '';



            if (cb.checked && isPruned) {



              const proceed = window.confirm(



                `⚠️ ADVERTENCIA DE PODA:\n\nEl instrumento "${sym}" fue descartado de la activación inicial:\n\n${warning}\n\n¿Deseas activarlo de todas formas bajo tu propio criterio de riesgo?`



              );



              if (!proceed) {



                cb.checked = false;



                return;



              }



            }



            dirty = true;



            updateCount();



            renderTabWorkers(state);



            $('msg').textContent = `Cambios pendientes para ${activeProfile}. Haz clic en Aplicar selección para persistir en los workers.`;



          }),



        );



        updateCount();



        renderTabWorkers(s);



      }



      let loadBusy = false;



      async function load() {



        if (document.hidden || loadBusy) return;



        loadBusy = true;



        const controller = new AbortController(),



          timeout = setTimeout(() => controller.abort(), 30000);



        try {



          const r = await fetch('/api/instruments?ts='+Date.now(), {



            cache: 'no-store',



            signal: controller.signal,



          });



          if (!r.ok) throw new Error('HTTP ' + r.status);



          const s = await r.json();



          if (!dirty) render(s);



          pageLoading.done();



        } catch (e) {



          $('msg').textContent = 'Sin conexión con el daemon: ' + e.message;



          pageLoading.fail('No se pudieron cargar los datos. Intenta nuevamente.');



        } finally {



          clearTimeout(timeout);



          loadBusy = false;



        }



      }



      async function save() {



        const values = selected();



        const selectiveCount = [...document.querySelectorAll('input[data-symbol]:checked')].filter((x) => x.dataset.pruned === 'true').length;



        $('save').disabled = true;



        try {



          const r = await fetch('/api/instruments/selection', {



            method: 'POST',



            headers: { 'Content-Type': 'application/json' },



            body: JSON.stringify({ selection_profile:activeProfile, selected_symbols: values, allow_selective: selectiveCount > 0 }),



          });



          const data = await r.json();



          if (!r.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar');



          dirty = false;



          $('msg').textContent = data.message || `${activeProfile} guardado`;



          await load();



        } catch (e) {



          $('msg').textContent = 'Error: ' + e.message;



        } finally {



          $('save').disabled = false;



        }



      }



      $('search').addEventListener('input', () => {



        if (state) render(state);



      });



      document.querySelectorAll('.profileTab').forEach((b) =>



        b.addEventListener('click', () => {



          if (dirty && !confirm('Hay cambios sin guardar. ¿Descartarlos?')) return;



          dirty = false;



          activeProfile = b.dataset.profile;



          if (state) render(state);



        }),



      );



      if ($('selectProfitable')) {



        $('selectProfitable').addEventListener('click', () => {



          document.querySelectorAll('input[data-symbol]').forEach((x) => {



            x.checked = x.dataset.pruned !== 'true';



          });



          dirty = true;



          updateCount();



          if (state) renderTabWorkers(state);



          $('msg').textContent = `Seleccionados únicamente los instrumentos rentables de ${activeProfile} (Podados OFF). Haz clic en Aplicar selección.`;



        });



      }



      $('selectAll').addEventListener('click', () => {



        document.querySelectorAll('input[data-symbol]').forEach((x) => (x.checked = x.dataset.locked !== 'true' && x.dataset.pruned !== 'true'));



        dirty = true;



        updateCount();



        if (state) renderTabWorkers(state);



      });



      $('clearAll').addEventListener('click', () => {



        document.querySelectorAll('input[data-symbol]').forEach((x) => (x.checked = false));



        dirty = true;



        updateCount();



        if (state) renderTabWorkers(state);



      });



      $('save').addEventListener('click', save);



      load();



      setInterval(load,6000);



      document.addEventListener('visibilitychange', () => {



        if (!document.hidden) load();



      });



    