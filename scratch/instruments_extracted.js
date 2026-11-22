



          const $ = (id) => document.getElementById(id);



          const esc = (v) =>



            String(v ?? '—').replace(



              /[&<>"']/g,



              (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],



            );



          function pct(v) {



            return v == null ? '—' : Number(v).toFixed(1) + '%';



          }



          function n(v, d = 1) {



            return v == null ? '—' : Number(v).toFixed(d);



          }



          function scoreClass(v) {



            return v >= 75 ? 'good' : v >= 60 ? 'warn' : 'bad';



          }



          function renderList(el, items, cls) {



            el.innerHTML =



              items && items.length



                ? items



                    .map((x) => `<div class="${cls}">${cls === 'ok' ? '✓' : '•'} ${esc(x)}</div>`)



                    .join('')



                : '<div class="empty">Ninguna</div>';



          }



          let selectionDirty = false;



          let lastSelectionVersion = null;



          function renderCatalog(s) {



            const summary = $('selectionSummary');



            if (summary) {



              const selected = s.selected_symbols || [];



              summary.textContent = `${selected.length} instrumentos habilitados para nuevas entradas · cambios disponibles en /instruments`;



              return;



            }



            const grid = $('instrumentGrid');



            if (!grid) return;



          }



          function currentSelection() {



            const grid = $('instrumentGrid');



            if (!grid) return [];



            return [...grid.querySelectorAll('input[data-symbol]:checked')]



              .map((x) => x.dataset.symbol)



              .sort((a, b) => a.localeCompare(b, 'es'));



          }



          async function saveSelection() {



            const selected = currentSelection();



            if (!selected.length) {



              $('selectionMsg').textContent =



                'Debes mantener al menos un instrumento seleccionado.';



              return;



            }



            $('saveSelection').disabled = true;



            try {



              const r = await fetch('/api/instruments/selection', {



                method: 'POST',



                headers: { 'Content-Type': 'application/json' },



                body: JSON.stringify({ selected_symbols: selected }),



              });



              const data = await r.json();



              if (!r.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar');



              selectionDirty = false;



              lastSelectionVersion = data.selection_version;



              $('selectionMsg').textContent = data.message || 'Selección guardada';



            } catch (e) {



              $('selectionMsg').textContent = 'Error: ' + e.message;



            } finally {



              $('saveSelection').disabled = false;



            }



          }



          let latestState = null;



          let selectedTradeId = null;



          // /api/state ya no trae los gráficos de cada posición (charts_lazy): se piden solo para la seleccionada.



          const positionChartCache = {};



          let positionChartInFlight = null;



          function hydratePositionCharts(rows) {



            (rows || []).forEach((p) => {



              const cached = p && p.charts_lazy ? positionChartCache[String(p.id)] : null;



              if (cached) {



                p.chart = cached.chart || {};



                p.entry_chart = cached.entry_chart || {};



              }



            });



          }



          async function loadPositionCharts(id) {



            const key = String(id);



            if (!key || positionChartInFlight === key) return;



            positionChartInFlight = key;



            try {



              const r = await fetch('/api/open-positions/' + encodeURIComponent(key) + '/charts?ts=' + Date.now(),



                                    { cache: 'no-store' });



              if (!r.ok) return;



              const data = await r.json();



              positionChartCache[key] = { chart: data.chart || {}, entry_chart: data.entry_chart || {} };



              const t = (latestState?.open_positions || []).find((x) => String(x.id) === key);



              if (t) {



                t.chart = positionChartCache[key].chart;



                t.entry_chart = positionChartCache[key].entry_chart;



                if (String(selectedTradeId) === key) {



                  renderPositionChart(t);



                  renderOpenRows(latestState?.open_positions || []);



                }



              }



            } catch (e) {



              /* el gráfico se reintenta en el siguiente refresco */



            } finally {



              if (positionChartInFlight === key) positionChartInFlight = null;



            }



          }



          let selectedCandidateBot = 'TODOS';



          function priceFmt(v) {



            if (v == null || !Number.isFinite(Number(v))) return '—';



            const x = Number(v);



            return Math.abs(x) >= 10000



              ? x.toFixed(2)



              : Math.abs(x) >= 100



                ? x.toFixed(3)



                : x.toFixed(5);



          }



          function svgEl(tag, attrs, text = '') {



            const a = Object.entries(attrs || {})



              .map(([k, v]) => `${k}="${esc(v)}"`)



              .join(' ');



            return `<${tag} ${a}>${text}</${tag}>`;



          }



          let chartRenderContext = null;



          const chartLayerState = {



            trade: true,



            swings: true,



            structure: true,



            liquidity: true,



            orderblock: true,



            fvg: true,



            premiumdiscount: true,



            confluence: true,



            rsi: true,



            cleanZones: true,



          };



          const chartViewState = {



            timeframe: 'M5',



            auditMode: 'ENTRY',



            zoom: 1,



            offset: 0,



            priceZoom: 1,



            pricePan: 0,



            dragging: false,



            dragStartX: 0,



            dragStartY: 0,



            dragStartOffset: 0,



            dragStartPricePan: 0,



            maxZoom: 12,



            maxPriceZoom: 20,



            minVisible: 8,



          };



          function chartCard() {



            return $('chartViewportShell');



          }



          function isChartFullscreen() {



            const el = chartCard();



            return document.fullscreenElement === el || document.webkitFullscreenElement === el;



          }



          function updateChartViewerButtons() {



            const full = isChartFullscreen(),



              shell = chartCard(),



              btn = $('chartFullscreenBtn'),



              txt = $('chartFullscreenText');



            if (txt) txt.textContent = full ? 'Salir' : 'Pantalla completa';



            if (btn) btn.setAttribute('aria-pressed', full ? 'true' : 'false');



            const min = $('chartMinimizeBtn');



            if (min)



              min.setAttribute(



                'aria-expanded',



                shell && !shell.classList.contains('chartPlotCollapsed') ? 'true' : 'false',



              );



          }



          async function toggleChartFullscreen() {



            const el = chartCard();



            if (!el) return;



            try {



              if (isChartFullscreen()) {



                if (document.exitFullscreen) await document.exitFullscreen();



                else if (document.webkitExitFullscreen) document.webkitExitFullscreen();



              } else {



                el.classList.remove('chartPlotCollapsed');



                if (el.requestFullscreen) await el.requestFullscreen();



                else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();



              }



            } catch (e) {



              console.warn('No se pudo ampliar el gráfico', e);



            } finally {



              updateChartViewerButtons();



            }



          }



          function toggleChartMinimized() {



            const el = chartCard();



            if (!el) return;



            if (isChartFullscreen()) {



              const exit = document.exitFullscreen || document.webkitExitFullscreen;



              if (exit) {



                try {



                  exit.call(document);



                } catch (e) {}



              }



            }



            el.classList.toggle('chartPlotCollapsed');



            updateChartViewerButtons();



            if (!el.classList.contains('chartPlotCollapsed')) rerenderSelectedChart();



          }



          function rerenderSelectedChart() {



            if (!selectedTradeId) return;



            const t = (latestState?.open_positions || []).find(



              (x) => String(x.id) === String(selectedTradeId),



            );



            if (t) requestAnimationFrame(() => renderPositionChart(t));



          }



          function setAuditMode(mode) {



            mode = String(mode || 'ENTRY').toUpperCase();



            if (!['ENTRY', 'CURRENT'].includes(mode)) return;



            chartViewState.auditMode = mode;



            chartViewState.zoom = 1;



            chartViewState.offset = 0;



            chartViewState.priceZoom = 1;



            chartViewState.pricePan = 0;



            document



              .querySelectorAll('.auditModeBtn[data-audit-mode]')



              .forEach((b) => b.classList.toggle('active', b.dataset.auditMode === mode));



            rerenderSelectedChart();



          }



          function setChartTimeframe(tf) {



            tf = String(tf || 'M5').toUpperCase();



            if (!['M1', 'M5', 'M15', 'H1'].includes(tf)) return;



            chartViewState.timeframe = tf;



            chartViewState.zoom = 1;



            chartViewState.offset = 0;



            chartViewState.priceZoom = 1;



            chartViewState.pricePan = 0;



            updateChartZoomBadge();



            document



              .querySelectorAll('.tfBtn[data-tf]')



              .forEach((b) => b.classList.toggle('active', b.dataset.tf === tf));



            rerenderSelectedChart();



          }



          function updateChartZoomBadge() {



            const b = $('chartZoomBadge');



            if (b)



              b.textContent =



                'Y ' +



                chartViewState.priceZoom.toFixed(1) +



                '× · X ' +



                chartViewState.zoom.toFixed(1) +



                '×';



            const w = $('chartWrap');



            if (w)



              w.dataset.zoomed =



                chartViewState.zoom > 1.01 ||



                chartViewState.priceZoom > 1.01 ||



                Math.abs(chartViewState.pricePan) > 0.001



                  ? 'true'



                  : 'false';



          }



          function changeChartZoom(multiplier, anchorRatio = null) {



            const t = (latestState?.open_positions || []).find(



              (x) => String(x.id) === String(selectedTradeId),



            );



            const ec = t?.entry_chart || {},



              c =



                chartViewState.auditMode === 'ENTRY' && Object.keys(ec).length



                  ? ec



                  : t?.chart || {},



              tf = (c.timeframes || {})[chartViewState.timeframe] || c,



              all = tf.candles || [],



              total = all.length;



            if (!total) return;



            const oldZoom = chartViewState.zoom,



              oldVisible = Math.max(



                chartViewState.minVisible,



                Math.min(total, Math.round(Math.min(total, 80) / oldZoom)),



              ),



              oldMax = Math.max(0, total - oldVisible),



              oldOffset = Math.max(0, Math.min(oldMax, chartViewState.offset));



            const ratio = anchorRatio == null ? 0.5 : Math.max(0, Math.min(1, anchorRatio));



            const oldEnd = total - oldOffset,



              oldStart = Math.max(0, oldEnd - oldVisible),



              anchorIndex = oldStart + ratio * Math.max(0, oldVisible - 1);



            chartViewState.zoom = Math.max(



              1,



              Math.min(chartViewState.maxZoom, oldZoom * multiplier),



            );



            const newVisible = Math.max(



              chartViewState.minVisible,



              Math.min(total, Math.round(Math.min(total, 80) / chartViewState.zoom)),



            );



            let newStart = anchorIndex - ratio * Math.max(0, newVisible - 1);



            newStart = Math.max(0, Math.min(Math.max(0, total - newVisible), newStart));



            chartViewState.offset = Math.max(0, total - (newStart + newVisible));



            updateChartZoomBadge();



            rerenderSelectedChart();



          }



          function changePriceZoom(multiplier, anchorRatioY = 0.5) {



            const oldZoom = chartViewState.priceZoom,



              oldSpan = 1 / oldZoom,



              ratio = Math.max(0, Math.min(1, anchorRatioY == null ? 0.5 : anchorRatioY)),



              anchor = chartViewState.pricePan + (0.5 - ratio) * oldSpan;



            chartViewState.priceZoom = Math.max(



              1,



              Math.min(chartViewState.maxPriceZoom, oldZoom * multiplier),



            );



            const newSpan = 1 / chartViewState.priceZoom;



            chartViewState.pricePan = anchor - (0.5 - ratio) * newSpan;



            chartViewState.pricePan = Math.max(-3, Math.min(3, chartViewState.pricePan));



            updateChartZoomBadge();



            rerenderSelectedChart();



          }



          function resetChartView() {



            chartViewState.zoom = 1;



            chartViewState.offset = 0;



            chartViewState.priceZoom = 1;



            chartViewState.pricePan = 0;



            updateChartZoomBadge();



            rerenderSelectedChart();



          }



          function chartWindow(allCandles) {



            const total = allCandles.length;



            if (!total) return { candles: [], start: 0, end: 0 };



            const base = Math.min(total, 80);



            const visible = Math.max(



              chartViewState.minVisible,



              Math.min(total, Math.round(base / chartViewState.zoom)),



            );



            const maxOffset = Math.max(0, total - visible);



            chartViewState.offset = Math.max(



              0,



              Math.min(maxOffset, Math.round(chartViewState.offset)),



            );



            const end = total - chartViewState.offset;



            const start = Math.max(0, end - visible);



            return { candles: allCandles.slice(start, end), start, end };



          }



          function bindChartManipulation() {



            const wrap = $('chartWrap');



            if (!wrap || wrap.dataset.navBound === '1') return;



            wrap.dataset.navBound = '1';



            wrap.addEventListener(



              'wheel',



              (e) => {



                if (!selectedTradeId) return;



                e.preventDefault();



                const rect = wrap.getBoundingClientRect();



                if (e.ctrlKey) {



                  const anchorX = rect.width > 0 ? (e.clientX - rect.left) / rect.width : 0.5;



                  changeChartZoom(e.deltaY < 0 ? 1.18 : 1 / 1.18, anchorX);



                  return;



                }



                const anchorY = rect.height > 0 ? (e.clientY - rect.top) / rect.height : 0.5;



                changePriceZoom(e.deltaY < 0 ? 1.16 : 1 / 1.16, anchorY);



              },



              { passive: false },



            );



            wrap.addEventListener('dblclick', (e) => {



              if (!selectedTradeId) return;



              e.preventDefault();



              resetChartView();



            });



            wrap.addEventListener('pointerdown', (e) => {



              if (!selectedTradeId || e.button !== 0) return;



              chartViewState.dragging = true;



              chartViewState.dragStartX = e.clientX;



              chartViewState.dragStartY = e.clientY;



              chartViewState.dragStartOffset = chartViewState.offset;



              chartViewState.dragStartPricePan = chartViewState.pricePan;



              wrap.classList.add('dragging');



              try {



                wrap.setPointerCapture(e.pointerId);



              } catch (_) {}



            });



            wrap.addEventListener('pointermove', (e) => {



              if (chartViewState.dragging) {



                const dx = e.clientX - chartViewState.dragStartX,



                  dy = e.clientY - chartViewState.dragStartY,



                  width = Math.max(1, wrap.clientWidth),



                  height = Math.max(1, wrap.clientHeight);



                const t = (latestState?.open_positions || []).find(



                  (x) => String(x.id) === String(selectedTradeId),



                );



                const ec = t?.entry_chart || {},



                  c =



                    chartViewState.auditMode === 'ENTRY' && Object.keys(ec).length



                      ? ec



                      : t?.chart || {},



                  tf = (c.timeframes || {})[chartViewState.timeframe] || c,



                  all = tf.candles || [],



                  total = all.length,



                  baseVisible = Math.min(total, 80);



                const visible = Math.max(



                  chartViewState.minVisible,



                  Math.min(total, Math.round(baseVisible / Math.max(1, chartViewState.zoom))),



                );



                const pxPerCandle = width / Math.max(1, visible);



                const maxOffset = Math.max(0, total - visible);



                chartViewState.offset = Math.max(



                  0,



                  Math.min(maxOffset, chartViewState.dragStartOffset + dx / Math.max(1, pxPerCandle)),



                );



                chartViewState.pricePan =



                  chartViewState.dragStartPricePan +



                  dy / height / Math.max(1, chartViewState.priceZoom);



                chartViewState.pricePan = Math.max(-3, Math.min(3, chartViewState.pricePan));



                updateChartZoomBadge();



                rerenderSelectedChart();



              } else if (chartRenderContext && chartRenderContext.candles && chartRenderContext.candles.length) {



                updateChartCrosshair(e, wrap, chartRenderContext);



              }



            });



            wrap.addEventListener('pointerleave', () => {



              hideChartCrosshair(chartRenderContext);



            });



            const stop = (e) => {



              if (!chartViewState.dragging) return;



              chartViewState.dragging = false;



              wrap.classList.remove('dragging');



              if (e && e.pointerId != null) {



                try {



                  wrap.releasePointerCapture(e.pointerId);



                } catch (_) {}



              }



            };



            wrap.addEventListener('pointerup', stop);



            wrap.addEventListener('pointercancel', stop);



            updateChartZoomBadge();



          }



          function updateChartHud(q, symbol, tf) {



            const symEl = $('hudSymbol'),



              tfEl = $('hudTf'),



              oEl = $('hudOpen'),



              hEl = $('hudHigh'),



              lEl = $('hudLow'),



              cEl = $('hudClose'),



              chEl = $('hudChange'),



              rsiEl = $('hudRsi');



            if (symEl) symEl.textContent = symbol || '—';



            if (tfEl) tfEl.textContent = tf || '—';



            if (!q) {



              if (oEl) oEl.textContent = '—';



              if (hEl) hEl.textContent = '—';



              if (lEl) lEl.textContent = '—';



              if (cEl) cEl.textContent = '—';



              if (chEl) {



                chEl.textContent = '—';



                chEl.className = 'hudChange';



              }



              if (rsiEl) rsiEl.textContent = '—';



              return;



            }



            if (oEl) oEl.textContent = priceFmt(q.open);



            if (hEl) hEl.textContent = priceFmt(q.high);



            if (lEl) lEl.textContent = priceFmt(q.low);



            if (cEl) cEl.textContent = priceFmt(q.close);



            const diff = Number(q.close) - Number(q.open);



            const pctVal = Number(q.open) ? (diff / Number(q.open)) * 100 : 0;



            if (chEl) {



              chEl.textContent = `${diff >= 0 ? '+' : ''}${priceFmt(diff)} (${pctVal >= 0 ? '+' : ''}${pctVal.toFixed(2)}%)`;



              chEl.className = 'hudChange ' + (diff >= 0 ? 'good' : 'bad');



            }



            if (rsiEl) rsiEl.textContent = q.rsi14 != null ? n(q.rsi14, 1) : '—';



          }



          function updateChartCrosshair(e, wrap, ctx) {



            const ch = $('chartCrosshair');



            if (!ch || !ctx) return;



            const rect = wrap.getBoundingClientRect();



            if (rect.width <= 0 || rect.height <= 0) return;



            const svgX = (e.clientX - rect.left) * (ctx.W / rect.width);



            const svgY = (e.clientY - rect.top) * (ctx.H / rect.height);



            if (



              svgX < ctx.pad.l ||



              svgX > ctx.W - ctx.pad.r ||



              svgY < ctx.pad.t ||



              svgY > ctx.H - ctx.pad.b



            ) {



              ch.style.display = 'none';



              return;



            }



            ch.style.display = '';



            const plotW = ctx.W - ctx.pad.l - ctx.pad.r;



            const candleIdx = Math.max(



              0,



              Math.min(



                ctx.candles.length - 1,



                Math.floor(((svgX - ctx.pad.l) / plotW) * ctx.candles.length),



              ),



            );



            const q = ctx.candles[candleIdx];



            if (q) {



              updateChartHud(q, ctx.symbol, ctx.activeTf);



            }



            const cX = ctx.pad.l + ((candleIdx + 0.5) * plotW) / ctx.candles.length;



            const vLine = $('crossV');



            if (vLine) {



              vLine.setAttribute('x1', cX);



              vLine.setAttribute('x2', cX);



            }



            const hLine = $('crossH');



            if (hLine) {



              hLine.setAttribute('y1', svgY);



              hLine.setAttribute('y2', svgY);



            }



            const priceBadge = $('crossPriceBadge');



            if (priceBadge) {



              if (svgY <= ctx.priceBottom) {



                priceBadge.style.display = '';



                const p = ctx.max - ((svgY - ctx.pad.t) / ctx.priceH) * (ctx.max - ctx.min);



                const prRect = $('crossPriceRect'),



                  prText = $('crossPriceText');



                if (prRect) prRect.setAttribute('y', svgY - 8.5);



                if (prText) {



                  prText.setAttribute('y', svgY + 3.5);



                  prText.textContent = priceFmt(p);



                }



              } else if (svgY >= ctx.rsiTop && svgY <= ctx.rsiTop + ctx.rsiH) {



                priceBadge.style.display = '';



                const r = 100 - ((svgY - ctx.rsiTop) / ctx.rsiH) * 100;



                const prRect = $('crossPriceRect'),



                  prText = $('crossPriceText');



                if (prRect) prRect.setAttribute('y', svgY - 8.5);



                if (prText) {



                  prText.setAttribute('y', svgY + 3.5);



                  prText.textContent = 'RSI ' + n(r, 1);



                }



              } else {



                priceBadge.style.display = 'none';



              }



            }



            const timeBadge = $('crossTimeBadge');



            if (timeBadge && q) {



              const tmRect = $('crossTimeRect'),



                tmText = $('crossTimeText');



              const tmW = 86;



              const badgeX = Math.max(



                ctx.pad.l,



                Math.min(ctx.W - ctx.pad.r - tmW, cX - tmW / 2),



              );



              if (tmRect) tmRect.setAttribute('x', badgeX);



              if (tmText) {



                tmText.setAttribute('x', badgeX + tmW / 2);



                const d = new Date(q.time);



                tmText.textContent = !isNaN(d.getTime())



                  ? d.toLocaleTimeString([], {



                      hour: '2-digit',



                      minute: '2-digit',



                      second: '2-digit',



                    })



                  : String(q.time).slice(11, 19);



              }



            }



          }



          function hideChartCrosshair(ctx) {



            const ch = $('chartCrosshair');



            if (ch) ch.style.display = 'none';



            if (ctx && ctx.candles && ctx.candles.length) {



              updateChartHud(ctx.candles[ctx.candles.length - 1], ctx.symbol, ctx.activeTf);



            }



          }



          function eventLayer(ev) {



            if (ev && ev.layer) return String(ev.layer);



            const t = String(ev?.type || ev || '');



            if (t.includes('swing')) return 'swings';



            if (t.includes('choch') || t.includes('bos')) return 'structure';



            if (t.includes('liquidity') || t.includes('sweep')) return 'liquidity';



            if (t.includes('order_block')) return 'orderblock';



            if (t.includes('fvg')) return 'fvg';



            return 'confluence';



          }



          function nearestCandleIndex(candles, time, clamp = false) {



            if (!time || !candles.length) return null;



            const target = new Date(time).getTime();



            if (!Number.isFinite(target)) return null;



            const first = new Date(candles[0].time).getTime(),



              last = new Date(candles[candles.length - 1].time).getTime();



            if (



              !clamp &&



              Number.isFinite(first) &&



              Number.isFinite(last) &&



              (target < first || target > last)



            )



              return null;



            let best = null,



              dist = Infinity;



            candles.forEach((q, i) => {



              const d = Math.abs(new Date(q.time).getTime() - target);



              if (d < dist) {



                dist = d;



                best = i;



              }



            });



            return best;



          }



          function chartObjectX(allCandles, win, time, plotW, padLeft) {



            const gi = nearestCandleIndex(allCandles, time, true);



            if (gi == null) return null;



            return padLeft + ((gi - win.start + 0.5) * plotW) / Math.max(1, win.end - win.start);



          }



          function viewBoxHtml(title, v) {



            const passed = (v.passed || []).slice(0, 10),



              missing = [



                ...(v.missing || []),



                ...(v.critical_failures || []).map((x) => 'CRÍTICA: ' + x),



              ].slice(0, 7),



              stamp = v.evaluated_at



                ? `<div class="sub" style="font-size:10px; margin-bottom:4px;">Actualizado ${new Date(v.evaluated_at).toLocaleTimeString('es-CL')}</div>`



                : '';



            const cf = [];



            if (v.divergence_confirmed)



              cf.push('Divergencia: ' + (v.divergence_type || 'confirmada'));



            if (v.h1_doji_confirmed)



              cf.push(



                'Doji H1: ' +



                  (v.h1_doji_type || 'confirmado') +



                  (v.h1_doji_zone ? ' · ' + v.h1_doji_zone : ''),



              );



            if (v.harmonic_confirmed) cf.push('Armónico: ' + (v.harmonic_pattern || 'confirmado'));



            if (v.chart_pattern_confirmed)



              cf.push(



                'Chartista: ' +



                  (v.chart_pattern_name || 'confirmado') +



                  ' · fuerza ' +



                  (v.chart_pattern_strength == null



                    ? '—'



                    : n(Number(v.chart_pattern_strength) * 100, 0) + '%'),



              );



            if (v.chart_pattern_conflict) {



              const sp = v.chart_pattern_supporting_pattern,



                sd = v.chart_pattern_supporting_direction,



                ss = v.chart_pattern_supporting_strength,



                cp = v.chart_pattern_conflicting_pattern,



                cd = v.chart_pattern_conflicting_direction,



                cs = v.chart_pattern_conflicting_strength;



              cf.push(



                'Conflicto chartista: ' +



                  (v.chart_pattern_conflict_reason || 'patrones opuestos detectados'),



              );



              if (sp)



                cf.push(



                  'A favor: ' +



                    String(sp).replaceAll('_', ' ') +



                    ' · ' +



                    (sd || '—') +



                    ' · ' +



                    (ss == null ? '—' : n(Number(ss) * 100, 0) + '%'),



                );



              if (cp)



                cf.push(



                  'En contra: ' +



                    String(cp).replaceAll('_', ' ') +



                    ' · ' +



                    (cd || '—') +



                    ' · ' +



                    (cs == null ? '—' : n(Number(cs) * 100, 0) + '%'),



                );



              if (v.chart_pattern_conflict_level)



                cf.push(



                  'Nivel conflicto: ' + String(v.chart_pattern_conflict_level).replaceAll('_', ' '),



                );



            }







            const stratPill = v.strategy_name



              ? `<span class="pill" style="font-size:10px; font-weight:700; background:rgba(41,98,255,0.18); color:#59a5ff; border:1px solid rgba(41,98,255,0.35); text-transform:uppercase;">${esc(v.strategy_name)}</span>`



              : '';







            const rawDec = String(v.decision || v.state || v.status || 'Sin registro');



            const isGood = rawDec.includes('BENEFICIO') || rawDec.includes('CONFIRMAD') || rawDec.includes('VIGENTE') || rawDec.includes('PROGRESO');



            const isWarn = rawDec.includes('RETROCESO') || rawDec.includes('VIGILAR') || rawDec.includes('CRÍTICA');



            const decPillClass = isGood ? 'good' : isWarn ? 'warn' : 'neutral';







            let paramsHtml = '';



            if (v.strategy_name === 'MALAYSIAN_SNR' || v.scenario || v.break_level != null || v.ref_level != null) {



              const pList = [];



              if (v.scenario_desc || v.scenario) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Escenario:</span> <span class="setupParamsVal">${esc(v.scenario_desc || v.scenario)}</span></div>`);



              if (v.break_level != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Nivel Break:</span> <span class="setupParamsVal">${priceFmt(v.break_level)}</span></div>`);



              if (v.ref_level != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Nivel Ref:</span> <span class="setupParamsVal">${priceFmt(v.ref_level)}</span></div>`);



              if (v.momentum_adx != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">ADX:</span> <span class="setupParamsVal">${n(v.momentum_adx, 1)}</span></div>`);



              if (v.body_ratio != null) {



                const brPct = Number(v.body_ratio) <= 1.0 ? Number(v.body_ratio) * 100 : Number(v.body_ratio);



                pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Cuerpo:</span> <span class="setupParamsVal">${n(brPct, 0)}%</span></div>`);



              }



              if (v.runner_target_name || v.runner_rr) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Corredora:</span> <span class="setupParamsVal">${esc(v.runner_target_name || 'TP2')} (1:${n(v.runner_rr || 2.0, 1)}R)</span></div>`);



              if (pList.length) paramsHtml = `<div class="setupParamsGrid">${pList.join('')}</div>`;



            } else if (v.strategy_name === 'ORB_NEW_YORK' || v.opening_range_high != null) {



              const pList = [];



              if (v.opening_range_high != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">OR High:</span> <span class="setupParamsVal">${priceFmt(v.opening_range_high)}</span></div>`);



              if (v.opening_range_low != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">OR Low:</span> <span class="setupParamsVal">${priceFmt(v.opening_range_low)}</span></div>`);



              if (v.opening_range_midpoint != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Midpoint:</span> <span class="setupParamsVal">${priceFmt(v.opening_range_midpoint)}</span></div>`);



              if (v.session_vwap != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">VWAP:</span> <span class="setupParamsVal">${priceFmt(v.session_vwap)}</span></div>`);



              if (pList.length) paramsHtml = `<div class="setupParamsGrid">${pList.join('')}</div>`;



            } else if (v.strategy_name === 'GOLD_QUARTERS' || v.major_quarter != null) {



              const pList = [];



              if (v.major_quarter != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Cuadrante:</span> <span class="setupParamsVal">${priceFmt(v.major_quarter)}</span></div>`);



              if (v.quarters_level != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Reacción:</span> <span class="setupParamsVal">${priceFmt(v.quarters_level)}</span></div>`);



              if (v.target_quarter != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Target:</span> <span class="setupParamsVal">${priceFmt(v.target_quarter)}</span></div>`);



              if (pList.length) paramsHtml = `<div class="setupParamsGrid">${pList.join('')}</div>`;



            }







            const scoreParts = [];



            if (v.direction) scoreParts.push(`<span class="pill ${v.direction === 'BUY' ? 'good' : 'bad'}" style="font-size:10px; padding:2px 6px;">${esc(v.direction)}</span>`);



            if (v.score != null) scoreParts.push(`<span class="pill neutral" style="font-size:10px; padding:2px 6px;">Score ${n(v.score, 0)}</span>`);



            if (v.grade) scoreParts.push(`<span class="pill good" style="font-size:10px; padding:2px 6px;">Grado ${esc(v.grade)}</span>`);



            if (v.confirmation_percentage != null) scoreParts.push(`<span class="pill" style="font-size:10px; padding:2px 6px;">${pct(v.confirmation_percentage)}</span>`);



            const scoreHtml = scoreParts.length ? `<div style="display:flex; gap:5px; flex-wrap:wrap; margin:6px 0 4px 0;">${scoreParts.join('')}</div>` : '';







            const passedHtml = passed.length



              ? `<div class="good" style="margin-top:6px; font-size:11px; line-height:1.5;">${passed.map((p) => `<div style="display:flex; align-items:flex-start; gap:5px;"><span style="color:#089981; font-weight:700;">✓</span><span>${esc(p)}</span></div>`).join('')}</div>`



              : '';



            const missingHtml = missing.length



              ? `<div class="warn" style="margin-top:5px; font-size:11px; line-height:1.4;">${missing.map((m) => `<div style="display:flex; align-items:flex-start; gap:5px;"><span style="color:#f23645;">•</span><span>${esc(m)}</span></div>`).join('')}</div>`



              : '';







            const smcTrendHtml = v.h1_trend ? `<div style="font-size:11px; color:var(--muted); margin-top:4px;">H1 ${esc(v.h1_trend)} · ${esc(v.structure_break || '—')} · ${esc(v.zone || '—')}</div>` : '';



            const reasonHtml = v.reason ? `<div class="sub" style="margin-top:6px; font-size:11px; line-height:1.4;">${esc(v.reason)}</div>` : '';



            const obsHtml = (v.observations || []).length ? `<div class="sub" style="margin-top:4px; font-size:11px; line-height:1.4;">${v.observations.map(esc).join('<br>')}</div>` : '';







            return `<section class="compareBox"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;"><h5>${esc(title)}</h5>${stratPill}</div>${stamp}<div style="margin:4px 0 6px 0;"><span class="pill ${decPillClass}" style="font-size:11px; font-weight:700; padding:3px 8px;">${esc(rawDec)}</span></div>${scoreHtml}${paramsHtml}${smcTrendHtml}${reasonHtml}${obsHtml}${cf.length ? `<div class="warn" style="margin-top:5px; font-size:11px;">${cf.map(esc).join('<br>')}</div>` : ''}${passedHtml}${missingHtml}</section>`;



          }



          function mtfAuditHtml(mtf) {



            const order = ['H1', 'M15', 'M5', 'M1'];



            return `<div style="margin-top:10px"><b>Contexto SMC multi-timeframe:</b>${order



              .map((tf) => {



                const q = mtf?.[tf] || {},



                  c = q.context || {},



                  ev = (q.recent_events || []).slice(-4);



                return `<div class="compareBox" style="margin-top:6px"><h5>${tf}</h5><div>Zona: <b>${esc(c.zone || '—')}</b> · EQ: ${priceFmt(c.equilibrium)}</div><div>Rango: ${priceFmt(c.range_low)} → ${priceFmt(c.range_high)}</div>${ev.length ? `<div style="margin-top:4px">${ev.map((x) => `<span class="pill">${esc(x.label)}</span>`).join(' ')}</div>` : '<div class="sub">Sin eventos recientes publicados.</div>'}</div>`;



              })



              .join('')}</div>`;



          }



          function renderPositionChart(t) {



            if (!t) {



              $('chartTitle').textContent = 'Selecciona una posición';



              $('chartSubtitle').textContent =



                'Navega M1 / M5 / M15 / H1; el gráfico usa todo el ancho y la comparación Entrada vs. Ahora queda debajo.';



              $('chartMeta').innerHTML = '';



              $('chartWrap').innerHTML =



                '<div class="empty">Selecciona “Ver gráfico” en una posición abierta.</div>';



              $('chartAudit').innerHTML = 'Sin posición seleccionada.';



              return;



            }



            const requestedEntry = chartViewState.auditMode === 'ENTRY',



              entryChart = t.entry_chart || {},



              hasEntry = Object.keys(entryChart).length > 0,



              c = requestedEntry && hasEntry ? entryChart : t.chart || {},



              tfMap = c.timeframes || {},



              tf = tfMap[chartViewState.timeframe] || c,



              allCandles = tf.candles || [],



              win = chartWindow(allCandles),



              candles = win.candles,



              events = tf.events || [],



              zones = tf.zones || [],



              liqLevels = tf.levels || [],



              smc = tf.smc_context || {},



              mtf = c.multi_timeframe || {},



              sv = t.latest_strategy_view || {},



              entryView = t.entry_strategy_view || {};



            const activeTf = tf.timeframe || chartViewState.timeframe || 'M5',



              mode = tf.context_mode || (activeTf === 'M1' ? 'AUXILIAR' : 'ESTRATEGIA');



            document



              .querySelectorAll('.tfBtn[data-tf]')



              .forEach((b) =>



                b.classList.toggle('active', b.dataset.tf === chartViewState.timeframe),



              );



            const modeEl = $('chartTfMode');



            if (modeEl) {



              modeEl.textContent = mode;



              modeEl.className = 'pill chartTfMode ' + (mode === 'AUXILIAR' ? 'aux' : 'strategy');



            }



            $('chartTitle').textContent =



              `${t.symbol} · ${t.direction} · ${t.leg || 'POSICIÓN'} · ${t.owner_profile || 'OWNER ?'}`;



            const auditLabel =



              requestedEntry && hasEntry ? 'EVIDENCIA DE ENTRADA PERSISTIDA' : 'ESTADO ACTUAL';



            const auditTime =



              requestedEntry && hasEntry ? t.entry_chart_captured_at : t.visual_audit_updated_at;



            $('chartSubtitle').textContent =



              `${auditLabel} · ${activeTf} · ${mode === 'AUXILIAR' ? 'contexto visual auxiliar' : 'capas SMC de estrategia'} · auditoría ${auditTime ? new Date(auditTime).toLocaleTimeString() : 'pendiente'} · owner ${t.chart_owner_profile || t.owner_profile || '—'} · recomendación ${t.recommendation || '—'}`;



            $('chartMeta').innerHTML =



              `<span class="pill ${t.health_score == null ? 'neutral' : scoreClass(t.health_score)}">Salud ${t.health_score == null ? 'N/D' : n(t.health_score, 0) + '/100'}</span><span class="pill">${esc(t.managed_by_daemon ? 'GESTIONADA' : 'SOLO VISUAL')}</span><span class="pill">Magic ${esc(t.owner_magic || '—')}</span><span class="pill">${esc(t.current_rr == null ? 'R —' : n(t.current_rr, 2) + 'R')}</span><span class="pill">Entrada ${priceFmt(t.entry_price)}</span><span class="pill">Actual ${priceFmt(t.current_price)}</span><span class="pill">${activeTf} · ${candles.length}/${allCandles.length} velas</span>`;



            const audit = [];



            audit.push(



              `<div class="compareGrid">${viewBoxHtml('Tesis al abrir', entryView)}${viewBoxHtml('Lo que ve ahora', sv)}</div>`,



            );



            audit.push(



              `<div><b>Recomendación:</b> <span class="${t.recommendation === 'MANTENER' ? 'good' : t.recommendation === 'VIGILAR' ? 'warn' : 'bad'}">${esc(t.recommendation || '—')}</span></div>`,



            );



            audit.push(



              `<div style="margin-top:7px"><b>Mapa SMC ${esc(activeTf)}:</b> ${events.length} eventos · ${liqLevels.length} niveles de liquidez · ${zones.filter((z) => z.layer === 'orderblock').length} OB · ${zones.filter((z) => z.layer === 'fvg').length} FVG</div>`,



            );



            audit.push(mtfAuditHtml(mtf));



            audit.push(



              `<div style="margin-top:7px"><b>Razones de salud:</b><ul class="auditList">${(t.reasons || []).map((x) => `<li>${esc(x)}</li>`).join('') || '<li>Sin razones suficientes.</li>'}</ul></div>`,



            );



            audit.push(



              `<div class="sub" style="margin-top:8px">M1 es navegación auxiliar y no modifica las condiciones de entrada. M5/M15/H1 muestran las capas SMC publicadas por el pipeline cuando están disponibles.</div>`,



            );



            $('chartAudit').innerHTML = audit.join('');



            if (!candles.length) {



              chartRenderContext = null;



              updateChartHud(null, t?.symbol, activeTf);



              $('chartWrap').innerHTML =



                `<div class="empty">Auditoría visual pendiente para ${esc(t.symbol)} · owner ${esc(t.owner_profile || 'no identificado')}. El worker debe publicar un snapshot persistente ${esc(activeTf)}.${tf.error ? ' · ' + esc(tf.error) : ''}</div>`;



              return;



            }



            const W = 1000,



              H = 540,



              pad = { l: 20, r: 94, t: 20, b: 26 },



              rsiH = 92,



              rsiGap = 20;



            const priceBottom = H - pad.b - rsiH - rsiGap,



              priceH = priceBottom - pad.t;



            const lows = candles.map((x) => Number(x.low)),



              highs = candles.map((x) => Number(x.high));



            const levelVals = [



              t.entry_price,



              t.stop_loss,



              t.take_profit,



              t.current_stop_loss,



              t.current_price,



              smc.range_high,



              smc.range_low,



              smc.equilibrium,



            ]



              .map(Number)



              .filter(Number.isFinite);



            let min = Math.min(...lows, ...levelVals),



              max = Math.max(...highs, ...levelVals);



            let span = max - min;



            if (!(span > 0)) span = Math.max(1, Math.abs(max) * 0.01);



            min -= span * 0.08;



            max += span * 0.08;



            const autoCenter = (min + max) / 2,



              autoSpan = Math.max(1e-12, max - min),



              visibleSpan = autoSpan / Math.max(1, chartViewState.priceZoom),



              visibleCenter = autoCenter + chartViewState.pricePan * autoSpan;



            min = visibleCenter - visibleSpan / 2;



            max = visibleCenter + visibleSpan / 2;



            const plotW = W - pad.l - pad.r;



            const x = (i) => pad.l + ((i + 0.5) * plotW) / candles.length;



            const y = (v) => pad.t + ((max - Number(v)) / (max - min)) * priceH;



            const cw = Math.max(3, (plotW / candles.length) * 0.65);



            const rsiTop = priceBottom + rsiGap,



              rsiY = (v) => rsiTop + ((100 - Number(v)) / 100) * rsiH;



            let out = `<svg class="chartSvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Auditoría SMC ${esc(activeTf)} de ${esc(t.symbol)}"><defs><clipPath id="chartPriceClip"><rect x="${pad.l}" y="${pad.t}" width="${plotW}" height="${priceH}"/></clipPath><clipPath id="chartRsiClip"><rect x="${pad.l}" y="${rsiTop}" width="${plotW}" height="${rsiH}"/></clipPath></defs><rect width="${W}" height="${H}" fill="#131722"/><rect x="${pad.l}" y="${pad.t}" width="${plotW}" height="${priceH}" fill="#131722"/><rect x="${pad.l}" y="${rsiTop}" width="${plotW}" height="${rsiH}" fill="#0e121b"/><rect x="${W - pad.r}" y="0" width="${pad.r}" height="${H}" fill="#131722"/><rect x="0" y="${H - pad.b}" width="${W}" height="${pad.b}" fill="#131722"/><line x1="${W - pad.r}" y1="0" x2="${W - pad.r}" y2="${H - pad.b}" stroke="#1e222d" stroke-width="1"/><line x1="0" y1="${H - pad.b}" x2="${W}" y2="${H - pad.b}" stroke="#1e222d" stroke-width="1"/><line x1="0" y1="${priceBottom + rsiGap / 2}" x2="${W}" y2="${priceBottom + rsiGap / 2}" stroke="#1e222d" stroke-width="1"/>`;



            for (let i = 0; i <= 5; i++) {



              const yy = pad.t + (i * priceH) / 5,



                val = max - (i * (max - min)) / 5;



              out += `<line x1="${pad.l}" y1="${yy}" x2="${W - pad.r}" y2="${yy}" stroke="#1e222d" stroke-width="1" stroke-dasharray="3 3"/><line x1="${W - pad.r}" y1="${yy}" x2="${W - pad.r + 4}" y2="${yy}" stroke="#2a2e39"/><text x="${W - pad.r + 8}" y="${yy + 3.5}" fill="#787b86" font-size="9.5" font-family="monospace, sans-serif">${priceFmt(val)}</text>`;



            }



            const vGridCount = Math.min(6, candles.length);



            for (let k = 0; k < vGridCount; k++) {



              const cIdx = Math.floor((k * (candles.length - 1)) / Math.max(1, vGridCount - 1));



              const gx = x(cIdx);



              out += `<line x1="${gx}" y1="${pad.t}" x2="${gx}" y2="${H - pad.b}" stroke="#181c27" stroke-width="1" stroke-dasharray="2 4"/>`;



            }



            if (chartLayerState.premiumdiscount && smc.premium_discount_available) {



              const eq = Number(smc.equilibrium),



                rh = Number(smc.range_high),



                rl = Number(smc.range_low);



              if ([eq, rh, rl].every(Number.isFinite)) {



                const top = y(Math.min(rh, max)),



                  mid = y(eq),



                  bot = y(Math.max(rl, min));



                out += `<g clip-path="url(#chartPriceClip)"><rect x="${pad.l}" y="${top}" width="${plotW}" height="${Math.max(0, mid - top)}" fill="rgba(242, 54, 69, 0.04)"/><rect x="${pad.l}" y="${mid}" width="${plotW}" height="${Math.max(0, bot - mid)}" fill="rgba(8, 153, 129, 0.04)"/><line x1="${pad.l}" y1="${mid}" x2="${W - pad.r}" y2="${mid}" stroke="#eab308" stroke-width="1.2" stroke-dasharray="4 4" opacity="0.85"/><text x="${W - pad.r - 8}" y="${Math.max(pad.t + 13, top + 13)}" text-anchor="end" fill="#f87171" opacity="0.38" font-size="9" font-weight="700" letter-spacing="1">PREMIUM</text><text x="${W - pad.r - 8}" y="${Math.min(priceBottom - 6, bot - 6)}" text-anchor="end" fill="#34d399" opacity="0.38" font-size="9" font-weight="700" letter-spacing="1">DISCOUNT</text></g><rect x="${W - pad.r + 3}" y="${mid - 8}" width="${pad.r - 6}" height="16" rx="2" fill="#ca8a04"/><text x="${W - pad.r + pad.r / 2}" y="${mid + 3.5}" text-anchor="middle" fill="#000" font-size="9" font-weight="800">EQ 50%</text>`;



              }



            }



            zones



              .filter((z) => chartLayerState[z.layer])



              .forEach((z) => {



                const xx = chartObjectX(allCandles, win, z.time, plotW, pad.l);



                if (xx == null) return;



                const lo = Number(z.low),



                  hi = Number(z.high);



                if (!Number.isFinite(lo) || !Number.isFinite(hi)) return;



                const yy1 = y(hi),



                  yy2 = y(lo),



                  zoneTop = Math.min(yy1, yy2),



                  zoneHeight = Math.max(2, Math.abs(yy2 - yy1)),



                  zoneRight = W - pad.r,



                  w = zoneRight - xx;



                if (w <= 0) return;



                const isMitigated =



                  z.status === 'INVALIDADA' ||



                  z.status === 'RELLENADA' ||



                  z.status === 'MITIGADA' ||



                  z.status === 'SWEPT';



                if (chartLayerState.cleanZones && isMitigated) return;



                const bullish = z.direction === 'BUY';



                let col = '',



                  badgeBg = '',



                  badgeTextCol = '',



                  zoneLabel = '';



                if (z.layer === 'fvg') {



                  col = bullish ? '#818cf8' : '#a855f7';



                  badgeBg = bullish ? 'rgba(49, 46, 129, 0.88)' : 'rgba(88, 28, 135, 0.88)';



                  badgeTextCol = bullish ? '#c7d2fe' : '#e9d5ff';



                  zoneLabel = `FVG ${bullish ? 'BULL' : 'BEAR'}${isMitigated ? ' (MIT)' : ''}`;



                } else {



                  col = bullish ? '#089981' : '#f23645';



                  badgeBg = bullish ? 'rgba(6, 78, 59, 0.88)' : 'rgba(136, 19, 55, 0.88)';



                  badgeTextCol = bullish ? '#34d399' : '#fb7185';



                  zoneLabel = `OB ${bullish ? 'BULL' : 'BEAR'}${isMitigated ? ' (MIT)' : ''}`;



                }



                const opacity = isMitigated ? '0.04' : '0.12';



                const badgeW = isMitigated ? 68 : 48;



                out += `<g clip-path="url(#chartPriceClip)"><rect x="${xx}" y="${zoneTop}" width="${w}" height="${zoneHeight}" rx="3" ry="3" fill="${col}" opacity="${opacity}" stroke="${col}" stroke-width="1" stroke-dasharray="${z.layer === 'fvg' ? '4 3' : '3 3'}"><title>${esc(z.label)} · ${esc(z.status || '')} [${priceFmt(lo)} - ${priceFmt(hi)}]</title></rect><rect x="${xx + 4}" y="${zoneTop + 2}" width="${badgeW}" height="14" rx="2" fill="${badgeBg}"/><text class="zoneChartLabel" x="${xx + 6}" y="${zoneTop + 12}" fill="${badgeTextCol}" font-size="8.5" font-weight="700">${esc(zoneLabel)}</text></g>`;



              });



            liqLevels



              .filter(() => chartLayerState.liquidity)



              .forEach((l) => {



                const xx = chartObjectX(allCandles, win, l.time, plotW, pad.l),



                  pv = Number(l.price);



                if (xx == null || !Number.isFinite(pv) || xx >= W - pad.r) return;



                const yy = y(pv),



                  isBsl = l.type === 'buy_side_liquidity',



                  col = isBsl ? '#f59e0b' : '#38bdf8';



                out += `<g clip-path="url(#chartPriceClip)"><line x1="${xx}" y1="${yy}" x2="${W - pad.r}" y2="${yy}" stroke="${col}" stroke-width="1" stroke-dasharray="2 4" opacity="0.65"><title>${esc(l.label)}</title></line><rect x="${xx + 4}" y="${yy - 11}" width="26" height="11" rx="2" fill="${col}" opacity="0.25"/><text x="${xx + 17}" y="${yy - 3}" text-anchor="middle" fill="${col}" font-size="8" font-weight="800">${isBsl ? 'BSL' : 'SSL'}</text></g>`;



              });



            candles.forEach((q, i) => {



              const xx = x(i),



                yo = y(q.open),



                yc = y(q.close),



                yh = y(q.high),



                yl = y(q.low),



                up = Number(q.close) >= Number(q.open),



                col = up ? '#089981' : '#f23645';



              out += `<g clip-path="url(#chartPriceClip)"><line x1="${xx}" y1="${yh}" x2="${xx}" y2="${yl}" stroke="${col}" stroke-width="1.2"/><rect x="${xx - cw / 2}" y="${Math.min(yo, yc)}" width="${cw}" height="${Math.max(1, Math.abs(yc - yo))}" rx="1" ry="1" fill="${col}" opacity="0.95"/></g>`;



            });



            if (chartLayerState.trade) {



              const tradeLevels = [



                { id: 'TP', label: 'TP', val: t.take_profit, bg: '#089981', fg: '#ffffff', dash: '4 4' },



                { id: 'SL', label: 'SL', val: t.stop_loss, bg: '#f23645', fg: '#ffffff', dash: '4 4' },



                { id: 'ENT', label: 'ENT', val: t.entry_price, bg: '#2962ff', fg: '#ffffff', dash: '6 4' },



                { id: 'BE', label: 'BE', val: t.current_stop_loss, bg: '#d97706', fg: '#ffffff', dash: '4 3' },



                { id: 'ACT', label: 'ACT', val: t.current_price, bg: '#475569', fg: '#ffffff', dash: '2 2' },



              ];



              const validLevels = tradeLevels



                .filter((x) => Number.isFinite(Number(x.val)))



                .map((lvl) => ({



                  ...lvl,



                  val: Number(lvl.val),



                  y: y(Number(lvl.val)),



                }))



                .sort((a, b) => a.y - b.y);







              validLevels.forEach((l) => {



                l.badgeY = l.y;



              });



              for (let k = 1; k < validLevels.length; k++) {



                if (validLevels[k].badgeY - validLevels[k - 1].badgeY < 18) {



                  validLevels[k].badgeY = validLevels[k - 1].badgeY + 18;



                }



              }



              if (



                validLevels.length &&



                validLevels[validLevels.length - 1].badgeY > priceBottom



              ) {



                const shift = validLevels[validLevels.length - 1].badgeY - priceBottom;



                validLevels.forEach((l) => {



                  l.badgeY -= shift;



                });



              }







              validLevels.forEach((lvl) => {



                out += `<line x1="${pad.l}" y1="${lvl.y}" x2="${W - pad.r}" y2="${lvl.y}" stroke="${lvl.bg}" stroke-width="1.4" stroke-dasharray="${lvl.dash}" opacity="0.85"/>`;



                if (Math.abs(lvl.badgeY - lvl.y) > 1) {



                  out += `<line x1="${W - pad.r}" y1="${lvl.y}" x2="${W - pad.r + 3}" y2="${lvl.badgeY}" stroke="${lvl.bg}" stroke-width="1.2"/>`;



                }



                out += `<rect x="${W - pad.r + 3}" y="${lvl.badgeY - 8.5}" width="${pad.r - 6}" height="17" rx="3" fill="${lvl.bg}"/><text class="priceLabel" x="${W - pad.r + (pad.r - 6) / 2 + 3}" y="${lvl.badgeY + 3.5}" text-anchor="middle" fill="${lvl.fg}" font-size="9.5" font-family="monospace, sans-serif" font-weight="700">${lvl.label} ${priceFmt(lvl.val)}</text>`;



              });







              const ei = nearestCandleIndex(candles, t.entry_time);



              if (ei != null) {



                const ex = x(ei);



                out += `<line x1="${ex}" y1="${pad.t}" x2="${ex}" y2="${priceBottom}" stroke="#2962ff" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.85"/><rect x="${Math.min(ex - 2, W - pad.r - 180)}" y="${pad.t + 2}" width="176" height="18" rx="3" fill="#1e3a8a" opacity="0.9"/><text class="entryTag" x="${Math.min(ex + 4, W - pad.r - 174)}" y="${pad.t + 14}" fill="#93c5fd" font-size="9" font-weight="700">ENTRADA · ${entryView.score == null ? 'score —' : 'score ' + n(entryView.score, 0)} · ${pct(entryView.confirmation_percentage)}</text>`;



              }



            }



            const timeIndex = new Map(candles.map((q, i) => [String(q.time).slice(0, 16), i]));



            events



              .filter((e) => chartLayerState[eventLayer(e)])



              .forEach((e) => {



                let i = timeIndex.get(String(e.time).slice(0, 16));



                if (i == null) return;



                const xx = x(i),



                  py = y(



                    e.price != null



                      ? e.price



                      : e.direction === 'BUY'



                        ? candles[i].low



                        : candles[i].high,



                  ),



                  bull = e.direction === 'BUY';



                if (e.layer === 'swings') {



                  const col = bull ? '#38bdf8' : '#fbbf24',



                    dy = bull ? 14 : -8,



                    circleDy = bull ? 5 : -5;



                  out += `<g clip-path="url(#chartPriceClip)"><circle cx="${xx}" cy="${py + circleDy}" r="2" fill="${col}"/><text x="${xx}" y="${py + dy}" text-anchor="middle" fill="${col}" font-size="8" font-weight="800"><title>${esc(e.label)}</title>${esc(e.label)}</text></g>`;



                  return;



                }



                const col = bull ? '#38bdf8' : '#fbbf24',



                  pts = bull



                    ? `${xx},${py - 12} ${xx - 5},${py - 3} ${xx + 5},${py - 3}`



                    : `${xx},${py + 12} ${xx - 5},${py + 3} ${xx + 6},${py + 3}`;



                out += `<g clip-path="url(#chartPriceClip)"><polygon points="${pts}" fill="${col}"><title>${esc(e.label)}</title></polygon></g>`;



              });



            if (chartLayerState.confluence) {



              const ei = nearestCandleIndex(candles, t.entry_time);



              if (ei != null) {



                let ty = pad.t + 36;



                const con = [];



                if (entryView.divergence_confirmed) con.push('DIV RSI (' + (entryView.divergence_type || 'confirmada') + ')');



                if (entryView.h1_doji_confirmed) con.push('DOJI H1 (' + (entryView.h1_doji_type || 'confirmado') + ')');



                if (entryView.harmonic_confirmed) con.push('ARMÓNICO');



                if (entryView.chart_pattern_confirmed)



                  con.push(



                    'PATRÓN ' +



                      String(entryView.chart_pattern_name || 'CHARTISTA').replaceAll('_', ' '),



                  );



                con.forEach((label) => {



                  const chipW = Math.min(220, label.length * 6.5 + 24);



                  out += `<g opacity="0.92"><rect x="${pad.l + 8}" y="${ty - 11}" width="${chipW}" height="16" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="#f59e0b" stroke-width="0.8"/><text x="${pad.l + 14}" y="${ty + 1}" fill="#fbbf24" font-size="8.5" font-weight="700">✦ ${esc(label)}</text></g>`;



                  ty += 19;



                });



              }



              if (entryView.h1_doji_confirmed && entryView.h1_doji_time) {



                const di = nearestCandleIndex(candles, entryView.h1_doji_time);



                if (di != null) {



                  const xx = x(di),



                    py = y(candles[di].low);



                  out += `<circle cx="${xx}" cy="${py + 9}" r="4" fill="none" stroke="#fbbf24" stroke-width="2"><title>${esc(entryView.h1_doji_type || 'Doji H1 en extremo')}</title></circle>`;



                }



              }



            }



            if (chartLayerState.confluence && entryView.chart_pattern_confirmed) {



              const pe = entryView.chart_pattern_evidence || {},



                anchors = pe.anchors || [],



                pts = [];



              anchors.forEach((a) => {



                const ai = nearestCandleIndex(candles, a.time),



                  pv = Number(a.price);



                if (ai == null || !Number.isFinite(pv)) return;



                pts.push([x(ai), y(pv)]);



                out += `<circle cx="${x(ai)}" cy="${y(pv)}" r="4" fill="none" stroke="#fbbf24" stroke-width="2"><title>${esc(pe.pattern || entryView.chart_pattern_name || 'Patrón chartista')}</title></circle>`;



              });



              if (pts.length > 1)



                out += `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.9"/>`;



              if (pts.length)



                out += `<text x="${Math.min(pts[pts.length - 1][0] + 7, W - pad.r - 220)}" y="${Math.max(pad.t + 15, pts[pts.length - 1][1] - 8)}" fill="#fbbf24" font-size="9" font-weight="800">${esc(String(pe.pattern || entryView.chart_pattern_name || 'PATRÓN').replaceAll('_', ' '))}</text>`;



            }



            if (chartLayerState.rsi) {



              out += `<g clip-path="url(#chartRsiClip)"><rect x="${pad.l}" y="${rsiY(100)}" width="${plotW}" height="${Math.max(0, rsiY(70) - rsiY(100))}" fill="rgba(242, 54, 69, 0.05)"/><rect x="${pad.l}" y="${rsiY(70)}" width="${plotW}" height="${Math.max(0, rsiY(30) - rsiY(70))}" fill="rgba(129, 140, 248, 0.04)"/><rect x="${pad.l}" y="${rsiY(30)}" width="${plotW}" height="${Math.max(0, rsiY(0) - rsiY(30))}" fill="rgba(8, 153, 129, 0.05)"/></g>`;



              [70, 50, 30].forEach((v) => {



                const yy = rsiY(v);



                const col = v === 70 ? 'rgba(242, 54, 69, 0.45)' : v === 30 ? 'rgba(8, 153, 129, 0.45)' : '#334155';



                out += `<line x1="${pad.l}" y1="${yy}" x2="${W - pad.r}" y2="${yy}" stroke="${col}" stroke-width="1" stroke-dasharray="3 3"/><line x1="${W - pad.r}" y1="${yy}" x2="${W - pad.r + 4}" y2="${yy}" stroke="#2a2e39"/><text class="rsiLabel" x="${W - pad.r + 8}" y="${yy + 3.5}" fill="${v === 70 ? '#ef4444' : v === 30 ? '#22c55e' : '#64748b'}" font-size="9.5" font-family="monospace, sans-serif">${v}</text>`;



              });



              let pts = [];



              let lastRsi = null;



              candles.forEach((q, i) => {



                const rv = Number(q.rsi14);



                if (Number.isFinite(rv)) {



                  pts.push(`${x(i)},${rsiY(rv)}`);



                  lastRsi = rv;



                }



              });



              if (pts.length > 1) {



                out += `<g clip-path="url(#chartRsiClip)"><polyline points="${pts.join(' ')}" fill="none" stroke="#818cf8" stroke-width="1.8" stroke-linejoin="round"/></g>`;



              }



              out += `<text x="${pad.l + 8}" y="${rsiTop + 14}" fill="#787b86" font-size="9.5" font-family="monospace, sans-serif" font-weight="700">RSI (14, Close)</text>`;



              if (lastRsi != null) {



                const rY = rsiY(lastRsi);



                out += `<rect x="${W - pad.r + 3}" y="${rY - 7.5}" width="${pad.r - 6}" height="15" rx="2" fill="#6366f1"/><text x="${W - pad.r + pad.r / 2}" y="${rY + 3.5}" text-anchor="middle" fill="#ffffff" font-size="9" font-family="monospace, sans-serif" font-weight="700">${n(lastRsi, 1)}</text>`;



              }



            }



            const tickCount = Math.min(6, candles.length);



            for (let tIdx = 0; tIdx < tickCount; tIdx++) {



              const i = Math.floor((tIdx * (candles.length - 1)) / Math.max(1, tickCount - 1));



              const d = new Date(candles[i].time);



              const timeStr = !isNaN(d.getTime())



                ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })



                : String(candles[i].time).slice(11, 16);



              out += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle" fill="#787b86" font-size="10" font-family="monospace, sans-serif">${timeStr}</text>`;



            }



            out += `<g id="chartCrosshair" style="display:none; pointer-events:none;"><line id="crossV" x1="0" y1="${pad.t}" x2="0" y2="${H - pad.b}" stroke="#787b86" stroke-width="1" stroke-dasharray="3 3"/><line id="crossH" x1="${pad.l}" y1="0" x2="${W - pad.r}" y2="0" stroke="#787b86" stroke-width="1" stroke-dasharray="3 3"/><g id="crossPriceBadge" style="display:none;"><rect id="crossPriceRect" x="${W - pad.r + 2}" y="0" width="${pad.r - 4}" height="17" rx="2" fill="#2a2e39"/><text id="crossPriceText" x="${W - pad.r + pad.r / 2}" y="0" text-anchor="middle" fill="#ffffff" font-size="9.5" font-family="monospace, sans-serif" font-weight="700"></text></g><g id="crossTimeBadge"><rect id="crossTimeRect" x="0" y="${H - pad.b + 2}" width="86" height="17" rx="2" fill="#2a2e39"/><text id="crossTimeText" x="0" y="${H - pad.b + 14}" text-anchor="middle" fill="#ffffff" font-size="9.5" font-family="monospace, sans-serif" font-weight="700"></text></g></g>`;



            out += '</svg>';



            $('chartWrap').innerHTML = out;



            chartRenderContext = {



              W,



              H,



              pad,



              priceBottom,



              priceH,



              rsiTop,



              rsiH,



              min,



              max,



              candles,



              symbol: t.symbol,



              activeTf,



            };



            if (candles.length) {



              updateChartHud(candles[candles.length - 1], t.symbol, activeTf);



            }



          }



          function selectTrade(id) {



            selectedTradeId = String(id);



            const t = (latestState?.open_positions || []).find(



              (x) => String(x.id) === selectedTradeId,



            );



            renderPositionChart(t);



            renderOpenRows(latestState?.open_positions || []);



            if (t && t.charts_lazy) loadPositionCharts(selectedTradeId);



          }



          function renderOpenRows(rows) {



            $('openBody').innerHTML =



              (rows || [])



                .map((t) => {



                  const rec = t.recommendation || 'SIN DATOS';



                  const cls =



                    rec === 'MANTENER'



                      ? 'good'



                      : rec === 'VIGILAR'



                        ? 'warn'



                        : rec === 'SIN VALIDACIÓN EN VIVO' ||



                            rec === 'SIN TELEMETRÍA DEL WORKER' ||



                            rec === 'WORKER SIN ACTIVIDAD'



                          ? 'neutral'



                          : 'bad';



                  const rs = (t.reasons || [])



                    .slice(0, 5)



                    .map((x) => `• ${esc(x)}`)



                    .join('<br>');



                  const sel = String(t.id) === String(selectedTradeId) ? 'selectedRow' : '';



                  const persisted =



                    t.persistence_status === 'PERSISTED'



                      ? '<span class="statusPill warn">PERSISTIDA · SIN CONEXIÓN</span>'



                      : '<span class="statusPill good">EN VIVO</span>';



                  const health = t.health_score == null ? '—' : n(t.health_score, 0) + '/100';



                  const owner = t.owner_profile || 'NO IDENTIFICADO';



                  const ownerStatus = t.ownership_status || '—';



                  const ownerCls = t.managed_by_daemon ? 'good' : 'warn';



                  const chartAvailable = (t.chart && Object.keys(t.chart).length) || t.chart_available;



                  const durationPill = t.duration_str && t.duration_str !== '—'



                    ? `<span class="pill neutral" style="font-size:10px; padding:1px 6px; margin-left:4px; font-weight:600;" title="Tiempo transcurrido en posición">⏱ ${esc(t.duration_str)}</span>`



                    : '';



                  const scorePill = t.quality_score != null



                    ? `<span class="pill neutral" style="font-size:11px; font-weight:700; padding:2px 7px;">${n(t.quality_score, 0)}</span>`



                    : '—';



                  const confPill = t.confirmation_percentage != null



                    ? `<span class="pill ${t.confirmation_percentage >= 80 ? 'good' : 'neutral'}" style="font-size:11px; font-weight:700; padding:2px 7px;">${pct(t.confirmation_percentage)}</span>`



                    : '—';



                  return `<tr class="${sel}">



    <td><b>${esc(t.symbol)}</b> ${durationPill}<br><span class="sub">${esc(t.execution_mode)} · ${esc(t.leg)}</span><br>${persisted}<span class="technical">${esc(t.broker_verification)}</span></td>



    <td><b class="${ownerCls}">${esc(owner)}</b><br><span class="technical">Magic ${esc(t.owner_magic || '—')} · ${esc(ownerStatus)}</span><br><span class="technical">Worker ${esc(t.worker_status || '—')}${t.worker_pid ? ' · PID ' + esc(t.worker_pid) : ''}</span></td>



    <td>${esc(t.direction)}</td>



    <td class="score ${t.health_score == null ? 'neutral' : scoreClass(t.health_score)}">${health}<br><span class="pill">${esc(t.health_grade || '—')}</span></td>



    <td class="${cls}"><b>${esc(rec)}</b></td>



    <td>${t.current_rr == null ? '—' : n(t.current_rr, 2) + 'R'}</td>



    <td class="${t.break_even_confirmed ? 'good' : 'warn'}">${t.break_even_confirmed ? 'ACTIVO' : 'Pendiente'}</td>



    <td>${scorePill}</td>



    <td>${confPill}</td>



    <td>${esc(t.current_price)}</td>



    <td class="sub">${rs || 'Sin razones suficientes todavía'}</td>



    <td><button type="button" class="btn viewBtn" data-trade-id="${esc(t.id)}">${chartAvailable ? 'Ver gráfico' : 'Esperando gráfico'}</button></td>



   </tr>`;



                })



                .join('') ||



              '<tr><td colspan="12" class="empty">No hay operaciones abiertas registradas</td></tr>';



            $('openBody')



              .querySelectorAll('button[data-trade-id]')



              .forEach((b) => b.addEventListener('click', () => selectTrade(b.dataset.tradeId)));



          }



          function candidateFromWorker(worker) {



            if (!worker) return {};



            const details = worker.details || {},



              result = details.result && typeof details.result === 'object' ? details.result : {};



            return {



              ...result,



              symbol: worker.current_symbol || result.symbol,



              _worker_profile: worker.bot_profile,



              _worker_magic: worker.daemon_magic,



              _worker_cycle: worker.cycle_number,



              _worker_time: worker.last_event_time,



              _worker_action: worker.last_action,



            };



          }



          function renderCandidateTabs(s) {



            const workers = visibleWorkers(s),



              profiles = [



                'TODOS',



                ...workers.map((w) => String(w.bot_profile || '').toUpperCase()).filter(Boolean),



              ];



            const unique = [...new Set(profiles)];



            if (!unique.includes(selectedCandidateBot)) selectedCandidateBot = 'TODOS';



            const box = $('candidateBotTabs');



            if (!box) return;



            box.innerHTML = unique



              .map(



                (p) =>



                  `<button type="button" class="botTab ${p === selectedCandidateBot ? 'active' : ''}" data-bot="${esc(p)}">${esc(p)}</button>`,



              )



              .join('');



            box.querySelectorAll('button[data-bot]').forEach((b) =>



              b.addEventListener('click', () => {



                selectedCandidateBot = b.dataset.bot;



                render(latestState);



              }),



            );



          }



          function selectedCandidate(s) {



            const workers = visibleWorkers(s);



            if (!workers.length) return {};



            let worker = null;



            if (selectedCandidateBot === 'TODOS') {



              worker = [...workers].sort(



                (a, b) => new Date(b.last_event_time || 0) - new Date(a.last_event_time || 0),



              )[0];



            } else {



              worker = workers.find(



                (w) => String(w.bot_profile || '').toUpperCase() === selectedCandidateBot,



              );



            }



            return candidateFromWorker(worker);



          }



          function renderCandidateContext(last) {



            const box = $('candidateContext');



            if (!box) return;



            if (!last || !last._worker_profile) {



              box.innerHTML = '<span class="pill">Sin worker seleccionado</span>';



              return;



            }



            box.innerHTML = `<span class="pill good">BOT ${esc(last._worker_profile)}</span><span class="pill">Magic ${esc(last._worker_magic || '—')}</span><span class="pill">Ciclo ${esc(last._worker_cycle || 0)}</span><span class="pill">${esc(last._worker_action || 'En espera')}</span><span class="pill">${last._worker_time ? 'Actualizado ' + new Date(last._worker_time).toLocaleTimeString() : 'Sin timestamp'}</span>`;



          }



          const RETIRED_WORKER_PROFILES = new Set([



            'FLIP', 'IDX_OPEN', 'CARRY', 'DRIFT', 'GOLD', 'GOLD_QUARTERS', 'MSNR', 'NIGHT', 'RSI2', 'V53_PROBE', 'COMMODITIES', 'INDICES'



          ]);



          function visibleWorkers(s) {



            return (s.worker_states || []).filter(



              (w) => !RETIRED_WORKER_PROFILES.has(String(w.bot_profile || '').toUpperCase()),



            );



          }



          function renderLearningAudit(s) {



            const box = $('learningAuditPanel');



            if (!box) return;



            box.innerHTML =



              '<h3>Auditoría MT5 y aprendizaje candidato</h3><p>Captura de entrada, resultado cerrado y validación temporal. No activa modelos ni modifica SL/TP. MT5_OBSERVATION aprende variación de precio desde la primera observación hasta el cierre; no representa el PnL neto ni la señal original.</p>' +



              ((s.learning_audit || [])



                .map(



                  (r) =>



                    `<details><summary>${esc(r.worker)} · ${esc(r.source || '')} · ${esc(r.updated_at || r.error || '')} · ${r.stale ? 'INFORME ANTIGUO' : 'ACTUALIZADO'} · ${r.schema_current ? 'ESQUEMA VIGENTE' : 'ESQUEMA ANTERIOR'}</summary><p>Historial de la cuenta: ${Number(r.account_trades) || 0} registros · Con captura: ${Number(r.with_entry_snapshot) || 0} · Sin captura: ${Number(r.without_entry_snapshot) || 0} · Con primera observación: ${Number(r.with_observation) || 0}</p>${Object.entries(r.scopes || {}).map(([scope, v]) => `



                      <p><b>Ámbito ${esc(scope)}</b>: ${Number(v.execution_rows) || 0} ejecuciones ·



                      ${Number(v.logical_setups) || 0} setups únicos · ${Number(v.closed_setups) || 0} cerrados ·



                      ${Number(v.entry_captures) || 0} capturas de entrada</p>



                      <details><summary>Elegibilidad por ejecución</summary>



                      ${Object.entries(v.eligibility_reasons_by_execution || {}).map(([reason, count]) =>



                        `<p>${esc(reason)}: ${Number(count)}</p>`).join('')}</details>`).join('')}



                      <p>Entrenamiento por familia: ${Number(r.training_funnel?.eligible_closed_setups_family) || 0}



                      setups cerrados elegibles. Promoción automática deshabilitada.



                      Los esquemas antiguos requieren evidencia original; no se rellenan variables inventadas.</p>${



                      Object.entries(r.strategies || {})



                        .map(



                          ([k, v]) =>



                            `<p>${esc(k)} · Setups cerrados elegibles de la familia: ${Number(v.eligible_closed_setups) || 0} / mínimo ${Number(v.minimum) || 0} · ${esc(v.reason)} · Candidato entrenado: ${v.trained ? 'sí' : 'no'}<br>Validación: ${esc(v.temporal_validation?.reason || 'pendiente')} · Muestras evaluadas: ${Number(v.temporal_validation?.samples_evaluated) || 0} · Brier: ${esc(v.temporal_validation?.brier_score ?? '—')}</p>`,



                        )



                        .join('') || '<p>Sin capturas de entrada disponibles para entrenar.</p>'



                    }<details><summary>Elegibilidad de la familia (últimas 100 ejecuciones)</summary>${(r.trade_eligibility || []).map((t) => `<p>Trade ${esc(t.trade_id)} · ${esc(t.symbol)} · ${esc(t.evidence_type)} · ${esc(t.reason)}</p>`).join('')}</details><details><summary>Comparación por setup cerrado de la familia</summary><p>${esc(r.closed_comparison?.counterfactual_status || 'Sin comparación')} · ${Number(r.closed_comparison?.pending_setups) || 0} pendientes · ${Number(r.closed_comparison?.missing_variant_capture) || 0} sin captura de variante · ${Number(r.closed_comparison?.target_review_pending) || 0} pendientes de reconciliación SL/TP · ${Number(r.closed_comparison?.manual_exit_setups) || 0} setups con cierre manual (separados de la comparación autónoma)</p><details><summary>Resultados por versión de estrategia</summary>${Object.entries(r.closed_comparison?.by_version || {}).map(([k,v]) => `<p>${esc(k)} · ${Number(v.closed_setups)} setups · R neto total ${Number(v.sum_net_r).toFixed(3)}</p>`).join('')}</details>${Object.entries(



                      r.closed_comparison?.cohorts || {},



                    )



                      .map(



                        ([k, v]) =>



                          `<p>${esc(k)} · ${Number(v.closed_setups)} setups · R neto medio ${Number(v.mean_net_r).toFixed(3)} · ${esc(v.note)}</p>`,



                      )



                      .join(



                        '',



                      )}</details><p>Resultados de cuenta por instrumento (setups cerrados):</p>${Object.entries(



                      r.instruments || {},



                    )



                      .map(



                        ([k, v]) =>



                          `<p>${esc(k)} · ${Number(v.closed_setups)} cerrados · ${Number(v.wins)} positivos / ${Number(v.losses)} negativos · PnL neto ${Number(v.net_pnl).toFixed(2)}</p>`,



                      )



                      .join('')}</details>`,



                )



                .join('') ||



                '<p>Pendiente de la primera actualización del worker con esta versión.</p>');



          }



          function renderPersistenceHealth(s) {



            const rows = s.forex_spread_audit || [];



            return rows.filter(x => x.persistence?.status === 'DEGRADED').map(x =>



              `<p class="bad">Persistencia de spread degradada: ${esc(x.worker)} · ${esc(x.symbol)} ·



              ${esc(x.persistence.at)} · ${esc(x.persistence.error)}</p>`).join('');



          }



          function renderSmcTrial(s) {



            const box = $('smcTrialPanel');



            if (!box) return;



            const report = s.smc_trial || {},



              workers = report.workers || [];



            box.innerHTML =



              workers



                .map(



                  (w) =>



                    `<details><summary>${esc(w.profile)} · ${esc(w.policy)} · ${esc(w.retest)} · ${Number(w.evaluations) || 0} evaluaciones</summary><div class="sub">Desde ${esc(w.since)} · Actualizado ${esc(w.updated_at)} · ${w.stale_signals_count ?? (w.stale_signals || []).length} señales caducadas únicas</div><div><p>Bloques M15 únicos del día: ${w.m15_blocks_count ?? Object.keys(w.m15_blocks || {}).length} ·



                    Señales observadas: ${w.signal_observations_count ?? Object.keys(w.signal_observations || {}).length} ·



                    Primeras observaciones ya antiguas: ${w.signal_observations_stale_count ?? Object.values(w.signal_observations || {}).filter(x => x.stale_at_first_seen).length}.



                    Estos conteos no equivalen a operaciones.</p>



                    <details><summary>Últimos 30 bloques registrados y motivos</summary>



                    ${Object.entries(w.m15_blocks || {}).slice(-30).map(([id, block]) => `



                      <p>${esc(block.symbol)} · ${esc(id)} · ${block.state?.accepted ? 'Aceptado como setup' : 'Descartado'}<br>



                      ${esc((block.state?.reasons || []).join(', ') || 'Sin rechazos M15')} ·



                      ${Number(block.evaluations) || 0} evaluaciones · ${Number(block.timeline?.length) || 0} cambios conservados</p>`).join('')}



                    </details>



                    <details><summary>Última señal observada por instrumento</summary>



                    ${Object.entries(w.latest || {}).map(([symbol, item]) => `<p>${esc(symbol)} ·



                    ${esc(item.signal_age?.observation_class || 'Sin señal')} ·



                    Primera observación: ${esc(item.signal_age?.first_seen || '—')} ·



                    Retraso desde cierre M5: ${esc(item.signal_age?.first_detection_delay_seconds ?? '—')} s</p>`).join('')}



                    </details></div><div>${Object.entries(



                      w.counts || {},



                    )



                      .map(([k, v]) => esc(k) + ': ' + Number(v))



                      .join(' · ')}</div>${Object.values(w.latest || {})



                      .map(



                        (r) =>



                          `<p><b>${esc(r.symbol)}</b> · ${esc(r.action)} · ${esc(r.reason || '')}<br><span class="sub">${esc(r.updated_at)} · Confirmación favorable: ${r.favorable_confirmation?.confirmed ? (r.favorable_confirmation.chart_pattern ? 'patrón chartista' : 'agotamiento confirmado') : 'sin confirmación registrada'} · Obstáculos M15 (informativo): ${esc(



                            Object.entries(r.target_path_audit || {})



                              .map(



                                ([leg, a]) =>



                                  leg +



                                  ': ' +



                                  (a.obstacles || [])



                                    .map(



                                      (o) =>



                                        o.type +



                                        ' ' +



                                        Number(o.low).toFixed(3) +



                                        '–' +



                                        Number(o.high).toFixed(3) +



                                        ' / ' +



                                        Number(o.distance_r).toFixed(2) +



                                        'R',



                                    )



                                    .join(', '),



                              )



                              .join(' | ') || 'sin evaluación registrada',



                          )} · Edad M5: ${esc((r.signal_age || {}).age_candles ?? '—')} velas · Críticas: ${esc((r.critical_confirmation_failures || []).join(', ') || '—')} · Zona H1: ${r.entry_location_comparison?.H1_PRIMARY?.valid === true ? 'apta' : r.entry_location_comparison?.H1_PRIMARY?.valid === false ? 'bloqueada' : 'sin evaluar'} · Zona tres marcos: ${r.entry_location_comparison?.ALL_TIMEFRAMES?.valid === true ? 'apta' : r.entry_location_comparison?.ALL_TIMEFRAMES?.valid === false ? 'bloqueada' : 'sin evaluar'}</span></p>`,



                      )



                      .join('')}</details>`,



                )



                .join('') || 'Sin registros: reiniciar los workers para cargar la prueba.';



            const orb = s.orb_audit || {};



            box.innerHTML += `<details open><summary>ORB · resultados por activo y modalidad</summary><p>Esperanza = PnL neto cerrado / ejecuciones cerradas. Cada pierna cuenta por separado.</p>${(s.orb_execution_metrics || []).map(m => `<p><b>${esc(m.symbol)} · ${esc(m.strategy)}</b> · ${esc(m.source)} / ${esc(m.broker)} · Cerradas ${esc(m.closed)} · Ganadas ${esc(m.wins)} · Perdidas ${esc(m.losses)} · PnL ${esc(m.net_pnl)} · Esperanza ${esc(m.expectancy_net_pnl ?? '—')}</p>`).join('') || 'Sin ejecuciones ORB etiquetadas.'}${s.orb_metrics_error ? '<p>Métricas temporalmente no disponibles.</p>' : ''}</details>`;



            box.innerHTML += `<details open><summary>ORB · rango y rechazos · ${esc(orb.day || 'sin registros')}</summary><p>Actualizado ${esc(orb.updated_at || '—')} · Comparaciones solo en sombra; no autorizan entradas.</p>${Object.values(



              orb.latest || {},



            )



              .map(



                (a) =>



                  `<p><b>${esc(a.symbol)}</b> · ${esc(a.reason)}<br>Perfil ${esc(a.asset_profile || "—")} · Modos ${esc((a.allowed_modes || []).join(", "))} · Rango/ATR ${esc(a.range_amplitude?.ratio ?? "—")} · Calidad retest ${esc(a.retest?.quality || "—")}${a.session_cancellation ? " · Cancelado por ratio " + esc(a.session_cancellation.ratio) + " > " + esc(a.session_cancellation.critical_ratio) : ""}<br>ORH ${esc(a.orh)} / ORL ${esc(a.orl)} · ${esc(a.range_start)} → ${esc(a.range_end)} · ${esc(a.source)}<br>Cuerpo ${a.momentum?.body_ratio == null ? '—' : (100 * a.momentum.body_ratio).toFixed(1) + '%'} · Extensión ${a.momentum?.extension_atr == null ? '—' : Number(a.momentum.extension_atr).toFixed(2) + ' ATR'} · Volumen ${esc((a.volume_evidence || a.momentum)?.volume_status || 'no evaluado')} · Fuente ${esc((a.volume_evidence || a.momentum)?.volume_source || 'sin datos')} · Ruptura ${esc((a.volume_evidence || a.momentum)?.volume ?? '—')} / Media ${esc((a.volume_evidence || a.momentum)?.average_volume ?? '—')} · Ratio ${esc((a.volume_evidence || a.momentum)?.volume_ratio ?? '—')} / Umbral ${esc((a.volume_evidence || a.momentum)?.volume_threshold ?? '—')}</p><details><summary>Velas que forman el rango</summary>${(a.opening_candles || []).map((c) => `<p>${esc(c.time)} · O ${esc(c.open)} H ${esc(c.high)} L ${esc(c.low)} C ${esc(c.close)}</p>`).join('')}</details>`,



              )



              .join(



                '',



              )}<details><summary>${Object.keys(orb.candidates || {}).length} rupturas únicas: sensibilidad de momentum</summary>${Object.values(



              orb.candidates || {},



            )



              .map(



                (a) =>



                  `<p>${esc(a.symbol)} · ${esc(a.momentum?.confirmation_time)}<br>${Object.entries(



                    a.momentum?.variants || {},



                  )



                    .map(



                      ([k, v]) =>



                        esc(k) +



                        ': ' +



                        esc(



                          v.remaining_failures.join(', ') ||



                            'cumple momentum; faltan otros controles',



                        ),



                    )



                    .join('<br>')}</p>`,



              )



              .join('')}</details></details>`;



            workers.forEach((w) => {



              const setups = Object.values(w.unique_setups || {});



              const spreads = (s.forex_spread_audit || []).filter((x) => x.worker === w.profile);



              if (spreads.length)



                box.innerHTML += `<details><summary>${esc(w.profile)} · Spread de ejecución MT5</summary>${spreads.map((x) => `<p>${esc(x.symbol)} · ${esc(x.reason)} · ${x.spread_pips == null ? 'desconocido' : Number(x.spread_pips).toFixed(2) + ' pips'} · muestras ${Number(x.samples_count)} · estables ${Number(x.stable_count)}<br>Actualizado ${esc(x.observed_at)}</p>`).join('')}</details>`;



              const uniqueDiag = w.unique_setup_diagnostics || {};



              box.innerHTML += `<p>${esc(w.profile)} · Setups con captura incompleta: ${Number(uniqueDiag.capture_failure_setups || 0)}</p>`;



              box.innerHTML += setups.filter(x => Object.keys(x.variant_capture_failures || {}).length).map(x => `<p>${esc(x.symbol)} · ${Object.entries(x.variant_capture_failures).map(([name, failure]) => esc(name) + ': ' + esc(failure.reason)).join(' · ')}</p>`).join('');







              const replay = w.variant_outcomes || {};



              box.innerHTML += `<p><b>${esc(w.profile)} · Comparación con resultados cerrados (sombra)</b><br>${esc(replay.updated_at || 'Pendiente de actualización')} · ${esc(replay.limitations || 'Sin planes causales cerrados disponibles')}</p>`;



              box.innerHTML += Object.entries(replay.variants || {})



                .map(



                  ([k, v]) =>



                    `<p>${esc(k)}: ${Number(v.unique_setups)} setups únicos · ${Number(v.closed_replays)} replays cerrados · TP ${Number(v.tp)} / SL ${Number(v.sl)} · R bruto ${Number(v.gross_r_sum).toFixed(2)} · pendientes/excluidos ${Number(v.excluded_or_pending)}</p>`,



                )



                .join('');







              box.innerHTML += `<p><b>${esc(w.profile)} · Fallos pendientes por setup único</b><br>${



                Object.entries(uniqueDiag.remaining_failure_counts || {})



                  .map(([k, v]) => esc(k) + ': ' + Number(v))



                  .join(' · ') || 'Sin comparación disponible'



              }</p>`;



              box.innerHTML += `<details><summary>${esc(w.profile)} · ${setups.length} setups únicos observados · variantes solo en sombra</summary>${setups



                .map(



                  (x) =>



                    `<p>${esc(x.symbol)} · ${Number(x.evaluations)} evaluaciones · ${esc(x.action)}<br>Formación ${esc(x.setup_formed_at || '—')} · primera detección ${esc(x.first_seen)} · última ${esc(x.last_seen)} · primera caducidad ${esc(x.first_expired_at || '—')}<br>${Object.entries(



                      x.comparison?.variants || {},



                    )



                      .map(



                        ([k, v]) =>



                          esc(k) +



                          ': resuelve ' +



                          esc((v.resolved_failures || []).join(', ') || 'ninguno') +



                          '; persisten ' +



                          esc(



                            (v.remaining_critical_failures || []).join(', ') ||



                              'sin críticos; faltan otros controles',



                          ),



                      )



                      .join('<br>')}</p>`,



                )



                .join('')}</details>`;



              const groups = Object.entries(w.groups || {});



              if (groups.length)



                box.innerHTML += `<p><b>${esc(w.profile)} · por mercado</b><br>${groups



                  .map(



                    ([g, c]) =>



                      esc(g) +



                      ': ' +



                      Object.entries(c)



                        .map(([k, v]) => esc(k) + ' ' + Number(v))



                        .join(' · '),



                  )



                  .join('<br>')}</p>`;



              const candidates = Object.values(w.candidates || {});



              if (candidates.length)



                box.innerHTML += `<details><summary>${esc(w.profile)} · ${candidates.length} candidatas únicas (no operaciones)</summary>${candidates.map((c) => `<p>${esc(c.symbol)} · ${c.expired ? 'CADUCADA' : 'ÚLTIMO ESTADO REGISTRADO'} · ${esc(c.action)}<br>Señal ${esc(c.signal_time)} · Primera detección ${esc(c.first_seen)} · Última ${esc(c.last_seen)}<br>${esc(c.reason || '')}</p>`).join('')}</details>`;



            });



            box.innerHTML += `<details open><summary>Reglas actualizadas y flexibilidades pendientes</summary><ul><li>Activo al reiniciar: H1 sólo ubicación; dirección confirmada por setup M15 y CHOCH/BOS M5.</li><li>Activo al reiniciar: recuperación del OB al cierre como alternativa al rechazo por mecha; conserva desplazamiento y confirmación favorable.</li><li>Pendiente, NO ACTIVADO: desplazamiento, calibrar umbral relativo a volatilidad por instrumento, sin reducirlo globalmente.</li><li>Pendiente, NO ACTIVADO: secuencia, comprobar vigencia de setups anteriores antes de recuperarlos.</li><li>Forex: ventana diaria NY y cierre preventivo configurados; GOLD: pausa por cotizaciones no disponibles.</li></ul><p>Promover cambios sólo tras replay fuera de muestra con costes, expectativa y drawdown. RR, spread y riesgo siguen vigentes. H1_PRIMARY y ATR_BOUNDED ya son la prueba activa según el worker.</p></details>`;



            if ((report.errors || []).length)



              box.innerHTML += '<p>' + esc(report.errors.join(' · ')) + '</p>';



          }



          function renderQuarantine(s) {



            const box = $('quarantinePanel');



            if (!box) return;



            const q = s.risk_quarantine || {},



              items = q.items || [];



            const num = (v) =>



              v == null ? '—' : Number(v).toLocaleString('es-CL', { maximumFractionDigits: 4 });



            if (q.status === 'ERROR') {



              box.textContent = 'No se pudo leer la cuarentena. ' + (q.error || '');



              return;



            }



            box.innerHTML = items.length



              ? items



                  .map(



                    (x) =>



                      `<section class="workerCard" style="margin-top:10px"><div class="workerHead"><b>${esc(x.symbol)}</b><span class="statusPill warn">${esc(x.status)}</span></div><p>${esc(x.reason)} · ${esc(x.direction || '')} · ${esc(x.trade_leg || '')}</p><div class="workerMeta"><div><span>Riesgo objetivo</span><b>${num(x.target_risk)}</b></div><div><span>Riesgo ejecutado</span><b>${num(x.actual_risk)}</b></div><div><span>Límite máximo</span><b>${num(x.hard_cap)}</b></div><div><span>Exceso sobre objetivo</span><b>${x.excess_ratio == null ? '—' : num(x.excess_ratio * 100) + '%'}</b></div></div><p class="sub">Desde ${esc(x.since ? new Date(x.since).toLocaleString() : 'sin fecha')} · ${x.expires_at ? 'Reevaluación desde ' + esc(new Date(x.expires_at).toLocaleString()) : 'Requiere revisión manual'}</p><details><summary>Acciones para investigar y prevenir</summary><ul>${(x.actions || []).map((a) => '<li>' + esc(a) + '</li>').join('')}</ul></details></section>`,



                  )



                  .join('')



              : 'Sin instrumentos registrados en cuarentena.';



          }



          function renderWorkers(s) {



            const rows = visibleWorkers(s),



              grid = $('workerGrid');



            if (!grid) return;



            const order = [



              'BOOM', 'CRASH', 'STEP', 'JUMP',



              'VOLATILITY', 'VOLATILITY_1', 'VOLATILITY_2', 'VOLATILITY_3', 'VOLATILITY_4',



              'FOREX', 'FOREX_1', 'FOREX_2', 'FOREX_3', 'FOREX_4',



              'ICT', 'MALAYSIAN_SNR', 'COMMODITIES_SNR', 'INDICESB_SNR', 'ORB', 'TREND_PULLBACK'

            ];

            const workerLabels = {

              COMMODITIES_SNR: 'COMMODITIES_SNR · Materias Primas',

              INDICESB_SNR: 'INDICESB_SNR · Índices Bursátiles',

              IDX_OPEN: 'Apertura Bursátiles',



              ORB: 'ORB · Apertura New York',



              MALAYSIAN_SNR: 'Malaysian SNR (M15 Fresh/Break)',



              ICT: 'ICT (Metales, Cripto & Índices)',



              VOLATILITY_1: 'VOLATILITY (1)',



              VOLATILITY_2: 'VOLATILITY (2)',



              VOLATILITY_3: 'VOLATILITY (3)',



              VOLATILITY_4: 'VOLATILITY (4)',



              FOREX_1: 'FOREX (1)',



              FOREX_2: 'FOREX (2)',



              FOREX_3: 'FOREX (3)',



              FOREX_4: 'FOREX (4)',



            };



            const now = Date.now();



            const sorted = [...rows].sort((a, b) => {



              const ai = order.indexOf(String(a.bot_profile || '').toUpperCase()),



                bi = order.indexOf(String(b.bot_profile || '').toUpperCase());



              return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);



            });



            grid.innerHTML =



              sorted



                .map((w) => {



                  const prof = String(w.bot_profile || '').toUpperCase();



                  const isGold = prof === 'GOLD';



                  const isOrb = prof === 'ORB';



                  const total = Number(w.symbols_total || 0),



                    done = Number(w.symbols_processed || 0),



                    activeCnt = Number(w.active_symbols_count ?? total),



                    prunedCnt = Number(w.pruned_symbols_count ?? 0),



                    pctv = total ? Math.min(100, (done / total) * 100) : 0;



                  const age = w.last_event_time



                    ? Math.max(0, (now - new Date(w.last_event_time).getTime()) / 1000)



                    : 999999;



                  const disabled = String(w.status || '').toUpperCase() === 'DISABLED';



                  const paused = ['OUTSIDE_SESSION', 'SESSION_WARMUP'].includes(



                    String(w.status || '').toUpperCase(),



                  );



                  const stale = !disabled && !paused && age > 120,



                    status = disabled



                      ? 'DESACTIVADO MANUALMENTE'



                      : paused



                        ? w.status === 'SESSION_WARMUP'



                          ? 'PREPARANDO SESIÓN'



                          : isOrb



                            ? 'ACTIVO · ESPERANDO SESIÓN NY (09:30 EST)'



                            : 'PAUSADO · SESIÓN / MERCADO'



                        : stale



                          ? 'SIN ACTIVIDAD'



                          : isGold && (w.status === 'RUNNING' || !w.status)



                            ? 'ACTIVO · ESTRATEGIA CUARTOS'



                            : isOrb && w.status === 'RUNNING'



                              ? 'ACTIVO · SESIÓN NY VIGENTE'



                              : w.status || 'RUNNING';



                  const cls =



                    disabled



                      ? 'bad'



                      : paused && !isOrb



                        ? ''



                        : (isOrb && paused) || status.startsWith('ACTIVO') || status === 'RUNNING'



                          ? 'good'



                          : status === 'STARTING'



                            ? 'warn'



                            : 'bad';



                  const displayName =



                    workerLabels[prof] ||



                    w.worker_label ||



                    w.bot_profile ||



                    'WORKER';



                  const stratLabel = isGold



                    ? 'Cuartos ($25) · M5/H1'



                    : isOrb



                      ? 'ORB New York M5 (SWEEP)'



                      : (prof === 'MALAYSIAN_SNR' || prof === 'COMMODITIES_SNR' || prof === 'INDICESB_SNR')

                        ? 'Malaysian SNR (M15 Fresh/Break · C2)'



                          : prof === 'NIGHT'



                          ? 'Sesgo nocturno (cierre → apertura NY)'



                          : prof === 'DRIFT'



                          ? 'Ruptura tras compresión (Drift Switch)'



                          : prof === 'RSI2'



                          ? 'RSI(2) diario de Connors (índices US)'



                          : prof === 'CARRY'



                          ? 'Carry Forex G10 (swap real, mensual)'



                          : 'Estrategia ICT';



                  return `<section class="workerCard ${paused && !isOrb ? 'workerPaused' : disabled ? 'workerPaused' : stale ? 'workerStale' : ''}">



    <div class="workerHead"><div class="workerName">${esc(displayName)}</div><span class="statusPill ${cls}">${esc(status)}</span></div>



    <div class="workerMeta">



      <div><span>Estrategia</span><b style="color:#d79b19;">${esc(stratLabel)}</b></div>



      <div><span>PID</span><b>${esc(w.pid || '—')}</b></div>



      <div><span>Magic</span><b>${esc(w.daemon_magic || '—')}</b></div>



      <div><span>Ciclo</span><b>${esc(w.cycle_number || 0)}</b></div>



      <div><span>Progreso (/Instruments)</span><b>${done} / ${total} (${activeCnt} act · ${prunedCnt} poda OFF)</b></div>



      <div><span>Instrumento</span><b>${esc(w.current_symbol || 'En espera')}</b></div>



      <div><span>Última acción</span><b>${esc(w.last_action_es || '—')}</b><span class="technical">${esc(w.last_action || '')}</span></div>



    </div>



    <div class="workerProgress"><div style="width:${pctv}%"></div></div>



    <div class="workerReason">${esc(w.last_reason_es || 'Sin motivo adicional')}<span class="technical">${esc(w.last_reason || '')}${w.last_event_time ? ' · Actualizado ' + new Date(w.last_event_time).toLocaleTimeString() : ' · Sin timestamp'}</span></div>



    <button class="btn workerControl ${disabled ? 'primary' : ''}" data-worker-profile="${esc(w.bot_profile || '')}" data-worker-enabled="${disabled ? 'true' : 'false'}">${disabled ? 'Reactivar worker' : paused ? 'Desactivar también la reactivación automática' : 'Desactivar worker'}</button>



   </section>`;



                })



                .join('') ||



              '<div class="empty">Aún no hay workers registrados en SQLAlchemy.</div>';



            grid.querySelectorAll('[data-worker-profile]').forEach((button) =>



              button.addEventListener('click', async () => {



                const profile = button.dataset.workerProfile,



                  enabled = button.dataset.workerEnabled === 'true';



                if (



                  !enabled &&



                  !confirm(



                    `¿Desactivar ${profile}? No se puede desactivar si mantiene posiciones abiertas.`,



                  )



                )



                  return;



                button.disabled = true;



                try {



                  const response = await fetch(



                    `/api/workers/${encodeURIComponent(profile)}/enabled`,



                    {



                      method: 'POST',



                      headers: { 'Content-Type': 'application/json' },



                      body: JSON.stringify({ enabled }),



                    },



                  );



                  const result = await response.json();



                  if (!response.ok || !result.ok)



                    throw new Error(result.error || 'No se pudo actualizar el worker');



                  await refresh();



                } catch (error) {



                  alert(error.message);



                  button.disabled = false;



                }



              }),



            );



          }



          function renderDashboardNews(s) {



            const n = s.financial_news || {},



              items = n.items || [],



              calendar = n.calendar || {},



              events = calendar.events || [],



              agenda = $('economicCalendar'),



              target = $('dashboardNews');



            if (agenda) {



              agenda.innerHTML = events.length



                ? events



                    .slice(0, 10)



                    .map((x) => {



                      const when = x.event_at



                        ? new Intl.DateTimeFormat('es-CL', {



                            dateStyle: 'short',



                            timeStyle: 'short',



                            timeZone: 'America/Santiago',



                          }).format(new Date(x.event_at))



                        : 'Hora por confirmar';



                      const values = [



                        x.forecast ? 'Pronóstico: ' + x.forecast : '',



                        x.previous ? 'Anterior: ' + x.previous : '',



                      ]



                        .filter(Boolean)



                        .join(' · ');



                      return `<div style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact || 'MEDIO')}</span> <span class="pill">${esc(x.country || 'GLOBAL')}</span> <b>${esc(when)} CLT/CLST</b> · ${esc(x.title)}${values ? `<div class="sub">${esc(values)}</div>` : ''}</div>`;



                    })



                    .join('')



                : `Sin eventos próximos (${esc(calendar.status || n.status || 'SIN DATOS')}).`;



            }



            if (!target) return;



            target.innerHTML = items.length



              ? items



                  .slice(0, 6)



                  .map(



                    (x) =>



                      `<div style="padding:6px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact || 'MEDIO')}</span> <a href="${esc(x.link)}" target="_blank" rel="noopener" style="color:var(--text)">${esc(x.title)}</a></div>`,



                  )



                  .join('')



              : `Sin noticias disponibles (${esc(n.status || 'SIN DATOS')}).`;



          }



                    let currentMatrixFilter = 'ALL';
          let matrixSearchQuery = '';
          let matrixPage = 1;
          let matrixPageSize = 10;

          window.setMatrixFilter = function(filter) {
            currentMatrixFilter = filter;
            matrixPage = 1;
            document.querySelectorAll('#confluenceFilters .matrixTabBtn').forEach(btn => {
              btn.classList.toggle('active', btn.getAttribute('data-filter') === filter);
            });
            if (latestState) renderConfluenceMatrix(latestState);
          };

          window.setMatrixSearch = function(val) {
            matrixSearchQuery = (val || '').trim().toLowerCase();
            matrixPage = 1;
            if (latestState) renderConfluenceMatrix(latestState);
          };

          window.setMatrixPageSize = function(val) {
            matrixPageSize = val === 'ALL' ? 9999 : parseInt(val, 10);
            matrixPage = 1;
            if (latestState) renderConfluenceMatrix(latestState);
          };

          window.changeMatrixPage = function(delta) {
            matrixPage += delta;
            if (latestState) renderConfluenceMatrix(latestState);
          };

          function renderConfluenceMatrix(s) {
            const tbody = $('confluenceMatrixBody');
            if (!tbody) return;
            const fullMatrix = s.confluence_matrix || [];
            if (!fullMatrix.length) {
              tbody.innerHTML = '<tr><td colspan="5" class="empty">Esperando datos centinela de las estrategias…</td></tr>';
              return;
            }

            // Actualizar contadores dinámicos en los botones de filtro
            const cntAll = fullMatrix.length;
            const cntIct = fullMatrix.filter(m => (m.strategy_key || '').toUpperCase() === 'ICT').length;
            const cntMsnr = fullMatrix.filter(m => (m.strategy_key || '').toUpperCase() === 'MALAYSIAN_SNR').length;
            const cntOrb = fullMatrix.filter(m => (m.strategy_key || '').toUpperCase() === 'ORB').length;
            const cntTpb = fullMatrix.filter(m => (m.strategy_key || '').toUpperCase() === 'TREND_PULLBACK').length;
            const cntActive = fullMatrix.filter(m => (m.final_state || '').includes('ACTIVA') || m.badge_class === 'active').length;

            if ($('cntAll')) $('cntAll').textContent = `(${cntAll})`;
            if ($('cntIct')) $('cntIct').textContent = `(${cntIct})`;
            if ($('cntMsnr')) $('cntMsnr').textContent = `(${cntMsnr})`;
            if ($('cntOrb')) $('cntOrb').textContent = `(${cntOrb})`;
            if ($('cntTpb')) $('cntTpb').textContent = `(${cntTpb})`;
            if ($('cntActive')) $('cntActive').textContent = `(${cntActive})`;

            // Actualizar chips de resumen superiores
            const summaryDiv = $('confluenceSummaryChips');
            if (summaryDiv) {
              const readyCount = fullMatrix.filter(m => (m.final_state || '').includes('LISTA')).length;
              const monitorCount = fullMatrix.filter(m => (m.final_state || '').includes('MONITOREANDO') || (m.final_state || '').includes('ESPERANDO')).length;
              summaryDiv.innerHTML = `
                <span class="statusPill active" style="font-size:10px;">${cntActive} Posición${cntActive === 1 ? '' : 'es'} Activa${cntActive === 1 ? '' : 's'}</span>
                <span class="statusPill good" style="font-size:10px;">${readyCount} Señal${readyCount === 1 ? '' : 'es'} Lista${readyCount === 1 ? '' : 's'}</span>
                <span class="statusPill warn" style="font-size:10px;">${monitorCount} En Seguimiento</span>
              `;
            }

            // Aplicar filtros por estrategia y búsqueda
            let filtered = fullMatrix;
            if (currentMatrixFilter === 'ACTIVE') {
              filtered = fullMatrix.filter(m => (m.final_state || '').includes('ACTIVA') || m.badge_class === 'active');
            } else if (currentMatrixFilter !== 'ALL') {
              filtered = fullMatrix.filter(m => (m.strategy_key || '').toUpperCase() === currentMatrixFilter);
            }

            if (matrixSearchQuery) {
              filtered = filtered.filter(m =>
                (m.symbol || '').toLowerCase().includes(matrixSearchQuery) ||
                (m.strategy || '').toLowerCase().includes(matrixSearchQuery) ||
                (m.final_state || '').toLowerCase().includes(matrixSearchQuery)
              );
            }

            if (!filtered.length) {
              tbody.innerHTML = `<tr><td colspan="5" class="empty">No hay activos para el filtro seleccionado (${esc(currentMatrixFilter)}).</td></tr>`;
              if ($('confluencePageInfo')) $('confluencePageInfo').textContent = '0 activos';
              if ($('matrixPageNumber')) $('matrixPageNumber').textContent = '0 / 0';
              return;
            }

            // Paginación
            const totalItems = filtered.length;
            const totalPages = Math.ceil(totalItems / matrixPageSize) || 1;
            if (matrixPage < 1) matrixPage = 1;
            if (matrixPage > totalPages) matrixPage = totalPages;

            const startIndex = (matrixPage - 1) * matrixPageSize;
            const pageItems = filtered.slice(startIndex, startIndex + matrixPageSize);

            if ($('confluencePageInfo')) {
              const endIndex = Math.min(startIndex + pageItems.length, totalItems);
              $('confluencePageInfo').textContent = `Mostrando ${startIndex + 1}–${endIndex} de ${totalItems} activos`;
            }
            if ($('matrixPageNumber')) $('matrixPageNumber').textContent = `${matrixPage} / ${totalPages}`;
            if ($('matrixPrevBtn')) $('matrixPrevBtn').disabled = (matrixPage <= 1);
            if ($('matrixNextBtn')) $('matrixNextBtn').disabled = (matrixPage >= totalPages);

            tbody.innerHTML = pageItems.map(m => `
              <tr style="border-bottom: 1px solid var(--line); height: 44px;">
                <td style="padding: 6px 10px;">
                  <b style="font-size:12px;color:var(--text);">${esc(m.symbol)}</b>
                  <div style="margin-top: 2px;"><span class="stratBadge ${esc(m.strat_badge || 'strat-smc')}" style="font-size:9.5px;padding:1px 5px;">${esc(m.strategy || 'SMC')}</span></div>
                </td>
                <td style="padding: 6px 10px;">
                  <div style="font-weight:600;color:var(--text);">${esc(m.macro_context || m.h1_context || '—')}</div>
                  <div class="technical" style="color:var(--muted);">${esc(m.structure_level || m.m15_structure || '—')}</div>
                </td>
                <td style="padding: 6px 10px;">
                  <div style="color:var(--text);">${esc(m.trigger_confirmation || m.m5_confirmation || '—')}</div>
                  <div class="technical" style="color:var(--muted);">${esc(m.metrics_freshness || m.m5_freshness || '—')}</div>
                </td>
                <td style="padding: 6px 10px; text-align: center;">
                  <b style="color:var(--gold2);font-size:12px;">${esc(m.ai_score || '—')}</b>
                </td>
                <td style="padding: 6px 10px; text-align: center;">
                  <span class="statusPill ${esc(m.badge_class || 'neutral')}" style="font-size:10px;">${esc(m.final_state || '—')}</span>
                </td>
              </tr>
            `).join('');
          }

          function showDptNotification(msg, isError) {



            let toast = $('dptToast');



            if (!toast) {



              toast = document.createElement('div');



              toast.id = 'dptToast';



              toast.style.cssText = 'position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;font-weight:700;font-size:13px;z-index:99999;box-shadow:0 6px 18px rgba(0,0,0,0.5);transition:all 0.3s ease;pointer-events:none;';



              document.body.appendChild(toast);



            }



            toast.textContent = msg;



            toast.style.background = isError ? '#ff453a' : '#00db79';



            toast.style.color = '#000000';



            toast.style.opacity = '1';



            toast.style.transform = 'translateY(0)';



            setTimeout(() => {



              if (toast) {



                toast.style.opacity = '0';



                toast.style.transform = 'translateY(10px)';



              }



            }, 3500);



          }







          function renderDailyProfitTarget(s) {



            const d = (s && s.daily_profit_target) ? s.daily_profit_target : (s || {});



            const card = $('dailyProfitTargetCard');



            if (!card) return;



            const enabled = Boolean(d.enabled);



            const isLocked = Boolean(d.is_locked);



            const overrideUnlocked = Boolean(d.override_unlocked);



            const targetPct = Number(d.target_percent != null ? d.target_percent : 2.0).toFixed(2);



            const extraBuffer = Number(d.extra_target_buffer_percent != null ? d.extra_target_buffer_percent : 1.0).toFixed(2);



            const effectiveTarget = Number(d.effective_target_percent != null ? d.effective_target_percent : targetPct).toFixed(2);



            const dailyReturn = Number(d.daily_return_pct || 0.0);



            const todayPnl = Number(d.today_net_pnl || 0.0);



            const tradesCount = Number(d.today_trades_count || 0);



            const wins = Number(d.today_winning_trades || 0);



            const losses = Number(d.today_losing_trades || 0);







            const badge = $('dptStatusBadge');



            if (badge) {



              if (!enabled) {



                badge.className = 'statusPill neutral';



                badge.textContent = '⚪ Desactivado';



              } else if (isLocked) {



                badge.className = 'statusPill bad';



                badge.textContent = '🔒 Meta Alcanzada · Entradas Bloqueadas';



              } else if (overrideUnlocked) {



                badge.className = 'statusPill warn';



                badge.textContent = `⚡ Desbloqueo Activo (+${extraBuffer}% extra)`;



              } else {



                badge.className = 'statusPill good';



                badge.textContent = '🟢 Operando Normal';



              }



            }







            const chk = $('dptEnabledCheckbox');



            if (chk && document.activeElement !== chk) chk.checked = enabled;



            const inp = $('dptTargetPercentInput');



            if (inp && document.activeElement !== inp) inp.value = targetPct;







            if ($('dptReturnDisplay')) {



              $('dptReturnDisplay').textContent = (dailyReturn >= 0 ? '+' : '') + dailyReturn.toFixed(2) + '%';



              $('dptReturnDisplay').style.color = dailyReturn > 0 ? '#00db79' : dailyReturn < 0 ? '#ff453a' : 'inherit';



            }



            if ($('dptTodayPnlDisplay')) {



              $('dptTodayPnlDisplay').textContent = (todayPnl >= 0 ? '+$' : '-$') + Math.abs(todayPnl).toFixed(2) + ' hoy';



              $('dptTodayPnlDisplay').style.color = todayPnl > 0 ? '#00db79' : todayPnl < 0 ? '#ff453a' : '#94a3b8';



            }



            if ($('dptTargetDisplay')) {



              $('dptTargetDisplay').textContent = effectiveTarget + '%' + (overrideUnlocked ? ` (base ${targetPct}% + ${extraBuffer}% buffer)` : '');



            }



            if ($('dptTradesSummary')) {



              $('dptTradesSummary').textContent = `${tradesCount} cerrados · ${wins} ganados / ${losses} perdidos`;



            }







            const prog = $('dptProgressBar');



            if (prog) {



              const eff = parseFloat(effectiveTarget) || 2.0;



              const ratio = eff > 0 ? Math.min(100, Math.max(0, (dailyReturn / eff) * 100)) : 0;



              prog.style.width = ratio.toFixed(1) + '%';



              prog.style.background = isLocked ? '#00db79' : dailyReturn < 0 ? '#ff453a' : '#d79b19';



            }







            const banner = $('dptLockedBanner');



            if (banner) {



              banner.style.display = isLocked ? 'block' : 'none';



              if (isLocked && $('dptBannerText')) {



                $('dptBannerText').innerHTML = `<b>🎯 ¡META DIARIA CUMPLIDA!</b> Se ha alcanzado un retorno de <b>+${dailyReturn.toFixed(2)}%</b> (meta: ${effectiveTarget}%). Las nuevas entradas se encuentran bloqueadas en todos los workers para proteger tus ganancias.<br><span style="font-size:11px; color:#cbd5e1;">🛡️ Las posiciones abiertas continúan activas con gestión de riesgo (SL, TP, BE con protección de swap y spread).<br>🌏 Reactivación automática de todos los workers en la próxima <b>sesión de Asia (00:00 UTC / 09:00 JST)</b>.</span>`;



              }



            }



          }







          window.saveDailyTargetSettings = async function() {



            const chk = $('dptEnabledCheckbox');



            const inp = $('dptTargetPercentInput');



            const btn = $('dptSaveSettingsBtn');



            if (!inp) return;



            const enabled = chk ? chk.checked : true;



            const target_percent = parseFloat(inp.value) || 2.0;



            if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }



            try {



              const res = await fetch('/api/daily-target/settings', {



                method: 'POST',



                headers: { 'Content-Type': 'application/json' },



                body: JSON.stringify({ enabled, target_percent })



              });



              const data = await res.json();



              if (!res.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar la meta');



              if (data.daily_profit_target) {



                renderDailyProfitTarget(data.daily_profit_target);



              }



              showDptNotification(`✓ Meta diaria (${enabled ? target_percent.toFixed(2) + '%' : 'Desactivada'}) guardada exitosamente y persistida.`);



              if (typeof refresh === 'function') await refresh();



              else if (typeof window.refresh === 'function') await window.refresh();



            } catch (err) {



              showDptNotification('❌ Error al guardar meta diaria: ' + err.message, true);



            } finally {



              if (btn) { btn.disabled = false; btn.textContent = 'Guardar Meta'; }



            }



          };







          window.openDptOverrideModal = function() {



            const modal = $('dptRiskModal');



            if (modal) modal.style.display = 'flex';



          };







          window.closeDptOverrideModal = function() {



            const modal = $('dptRiskModal');



            if (modal) modal.style.display = 'none';



          };







          window.confirmDptOverride = async function() {



            const btn = $('dptConfirmOverrideBtn');



            if (btn) btn.disabled = true;



            try {



              const res = await fetch('/api/daily-target/override', {



                method: 'POST',



                headers: { 'Content-Type': 'application/json' },



                body: JSON.stringify({ confirm: true, extra_percent: 1.0 })



              });



              const data = await res.json();



              if (!res.ok || !data.ok) throw new Error(data.error || 'No se pudo desbloquear');



              closeDptOverrideModal();



              if (data.daily_profit_target) {



                renderDailyProfitTarget(data.daily_profit_target);



              }



              showDptNotification('⚡ Nuevas entradas desbloqueadas con buffer adicional asumido.');



              if (typeof refresh === 'function') await refresh();



              else if (typeof window.refresh === 'function') await window.refresh();



            } catch (err) {



              showDptNotification('❌ Error al desbloquear: ' + err.message, true);



            } finally {



              if (btn) btn.disabled = false;



            }



          };







          function render(s) {



            hydratePositionCharts(s && s.open_positions);



            latestState = s;



            if (selectedTradeId && (s?.open_positions || []).some((x) => String(x.id) === String(selectedTradeId) && x.charts_lazy)) {



              loadPositionCharts(selectedTradeId);  // mantiene vivo solo el gráfico seleccionado



            }



            renderDailyProfitTarget(s);



            renderConfluenceMatrix(s);



            renderDashboardNews(s);



            renderCatalog(s);



            renderWorkers(s);



            renderLearningAudit(s);



            if ($('learningAuditPanel')) $('learningAuditPanel').innerHTML += renderPersistenceHealth(s);



            renderSmcTrial(s);



            renderQuarantine(s);



            renderCandidateTabs(s);



            const ax = (s.account || {}).snapshot || {};







            const money = (v) =>



              v == null



                ? '—'



                : Number(v).toLocaleString('es-CL', {



                    minimumFractionDigits: 2,



                    maximumFractionDigits: 2,



                  });



            $('accountBalance').textContent = money(ax.balance);



            $('accountEquity').textContent = money(ax.equity);



            $('accountProfit').textContent = money(ax.profit);



            $('accountProfit').className =



              'value ' +



              (Number(ax.profit || 0) > 0 ? 'good' : Number(ax.profit || 0) < 0 ? 'bad' : '');



            $('accountFreeMargin').textContent = money(ax.free_margin);



            const liveLabel = s.connection_mode === 'LIVE' ? 'DATOS EN VIVO' : (s.status || 'CONECTADO');
            $('status').textContent = liveLabel;
            $('status').title = (s.status || 'ONLINE') + ' · ' + (s.daemon_version || '') + ' · ' + new Date(s.updated_at).toLocaleTimeString();
            $('status').style.borderColor = '#725116';
            $('status').style.color = '#ffd465';



            const workers = visibleWorkers(s);



            const activeWorkers = workers.filter(



              (w) => String(w.status || '').toUpperCase() !== 'STOPPED',



            );



            $('cycle').textContent = activeWorkers.length;



            const total = workers.reduce((a, w) => a + Number(w.symbols_total || 0), 0),



              done = workers.reduce((a, w) => a + Number(w.symbols_processed || 0), 0);



            $('progressText').textContent = done + ' / ' + total;



            $('progressBar').style.width = (total ? Math.min(100, (done / total) * 100) : 0) + '%';



            const latestWorker = [...workers].sort(



              (a, b) => new Date(b.last_event_time || 0) - new Date(a.last_event_time || 0),



            )[0];



            $('current').textContent = latestWorker



              ? (latestWorker.bot_profile || '') +



                ' · ' +



                (latestWorker.current_symbol || 'En espera')



              : 'En espera';



            $('openCount').textContent = (s.open_positions || []).length;



            let last = selectedCandidate(s);



            renderCandidateContext(last);



            const sc = last.score;



            $('score').textContent = sc == null ? '—' : Math.round(sc);



            $('ring').style.setProperty('--p', Math.max(0, Math.min(100, sc || 0)));



            $('lastSymbol').textContent = last.symbol || 'Sin datos';



            $('lastMeta').innerHTML =



              `<span class="pill ${scoreClass(sc)}">${esc(last.grade || 'SIN SCORE')}</span><span class="pill">Confirmaciones ${pct(last.confirmation_percentage)}</span><span class="pill">${esc(last.direction || 'SIN DIRECCIÓN')}</span>`;



            $('decision').innerHTML =



              `<b>${esc(last.decision_es || 'No confirmada')}</b>${last.reason_es ? ` · ${esc(last.reason_es)}` : ''}${last.reason ? `<span class="technical">${esc(last.reason)}</span>` : ''}`;



            $('divergence').textContent = last.divergence_confirmed



              ? last.divergence_type || 'Sí'



              : 'No';



            $('harmonic').textContent = last.harmonic_confirmed



              ? last.harmonic_pattern || 'Sí'



              : 'No';



            $('h1doji').textContent = last.h1_doji_confirmed



              ? (last.h1_doji_type || 'Sí') + (last.h1_doji_zone ? ' · ' + last.h1_doji_zone : '')



              : 'No';



            $('structure').textContent = last.structure_break || '—';



            $('zone').textContent = last.zone || '—';



            renderList($('passed'), last.passed, 'ok');



            const critical = (last.critical_failures || []).map((x) => 'CRÍTICA: ' + x);



            renderList(



              $('missing'),



              [...(last.missing || []), ...critical],



              critical.length ? 'critical' : 'miss',



            );



            const hs = s.position_health_summary || {};



            $('healthSummary').textContent =



              `Mantener ${hs.mantener || 0} · Vigilar ${hs.vigilar || 0} · Proteger ${hs.proteger || 0} · Salida ${hs.salida || 0} · Sin datos ${hs.sin_datos || 0} · Visual ${hs.solo_visual || 0}`;



            renderOpenRows(s.open_positions || []);



            if (selectedTradeId) {



              const selected = (s.open_positions || []).find(



                (x) => String(x.id) === String(selectedTradeId),



              );



              if (selected) renderPositionChart(selected);



              else {



                selectedTradeId = null;



                renderPositionChart(null);



              }



            }



            $('recentBody').innerHTML =



              (s.recent || [])



                .map((r) => {



                  const st = r.operational_state || {};



                  return `<tr><td><span class="pill">${esc(r._bot_profile || '—')}</span></td><td><b>${esc(r.symbol)}</b></td><td><span class="statusPill ${esc(st.severity || 'neutral')}">${esc(st.label || 'INFORMATIVO')}</span></td><td><b>${esc(r.action_es || r.action || 'Sin acción')}</b><span class="technical">${esc(r.action || '')}</span></td><td class="score ${scoreClass(r.score)}">${r.score == null ? '—' : n(r.score, 0)}</td><td>${pct(r.confirmation_percentage)}</td><td>${esc(r.grade)}</td><td>${esc(r.direction)}</td><td>${r.divergence_confirmed ? 'Sí' : 'No'}</td><td>${r.harmonic_confirmed ? 'Sí' : 'No'}</td><td>${n(r.elapsed_seconds, 2)}s</td><td>${esc(r.reason_es || 'Sin motivo adicional informado.')} ${r.decision_es ? `<span class="technical">Decisión: ${esc(r.decision_es)}</span>` : ''}${r.reason ? `<span class="technical">Código: ${esc(r.reason)}</span>` : ''}</td></tr>`;



                })



                .join('') ||



              '<tr><td colspan="12" class="empty">Esperando el primer análisis…</td></tr>';



          }



          let refreshBusy = false;



          async function refresh() {



            if(document.hidden||refreshBusy)return;



            refreshBusy = true;



            const controller = new AbortController(),



              timeout = setTimeout(() => controller.abort(), 30000);



            try {



              const r = await fetch('/api/state?ts='+Date.now(), {



                cache: 'no-store',



                signal: controller.signal,



              });



              if (!r.ok) throw new Error('HTTP ' + r.status);



              render(await r.json());



              pageLoading.done();



            } catch (e) {
              $('status').textContent = 'SIN CONEXIÓN';
              $('status').title = 'Dashboard sin conexión: ' + e.message;
              $('status').style.borderColor = 'rgba(239, 68, 68, 0.5)';
              $('status').style.color = '#f87171';
              pageLoading.fail('No se pudieron cargar los datos. Intenta nuevamente.');



            } finally {



              clearTimeout(timeout);



              refreshBusy = false;



            }



          }



          window.refresh = refresh;



          const selectAllBtn = $('selectAll'),



            clearAllBtn = $('clearAll'),



            saveSelectionBtn = $('saveSelection');



          if (selectAllBtn) selectAllBtn.addEventListener('click', () => {});



          if (clearAllBtn) clearAllBtn.addEventListener('click', () => {});



          if (saveSelectionBtn) saveSelectionBtn.addEventListener('click', saveSelection);



          document.querySelectorAll('#chartLayers input[data-layer]').forEach((cb) =>



            cb.addEventListener('change', () => {



              chartLayerState[cb.dataset.layer] = cb.checked;



              rerenderSelectedChart();



            }),



          );



          document



            .querySelectorAll('.auditModeBtn[data-audit-mode]')



            .forEach((b) => b.addEventListener('click', () => setAuditMode(b.dataset.auditMode)));



          document



            .querySelectorAll('.tfBtn[data-tf]')



            .forEach((b) => b.addEventListener('click', () => setChartTimeframe(b.dataset.tf)));



          const chartFullscreenBtn = $('chartFullscreenBtn'),



            chartMinimizeBtn = $('chartMinimizeBtn'),



            chartZoomInBtn = $('chartZoomInBtn'),



            chartZoomOutBtn = $('chartZoomOutBtn'),



            chartResetViewBtn = $('chartResetViewBtn');



          if (chartFullscreenBtn)



            chartFullscreenBtn.addEventListener('click', toggleChartFullscreen);



          if (chartMinimizeBtn) chartMinimizeBtn.addEventListener('click', toggleChartMinimized);



          if (chartZoomInBtn)



            chartZoomInBtn.addEventListener('click', () => changePriceZoom(1.25, 0.5));



          if (chartZoomOutBtn)



            chartZoomOutBtn.addEventListener('click', () => changePriceZoom(1 / 1.25, 0.5));



          if (chartResetViewBtn) chartResetViewBtn.addEventListener('click', resetChartView);



          document.addEventListener('fullscreenchange', () => {



            updateChartViewerButtons();



            rerenderSelectedChart();



          });



          document.addEventListener('webkitfullscreenchange', () => {



            updateChartViewerButtons();



            rerenderSelectedChart();



          });



          bindChartManipulation();



          updateChartViewerButtons();



          refresh();



          setInterval(refresh,6000);



          document.addEventListener('visibilitychange', () => {



            if (!document.hidden) refresh();



          });



        