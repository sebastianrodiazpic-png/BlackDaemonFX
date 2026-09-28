"""Shared initial-data and navigation feedback for the dashboard pages."""

LOADING_UI = r'''
<style>
  #pageLoading {
    position: fixed;
    inset: 0;
    z-index: 10000;
    display: grid;
    place-items: center;
    background: rgba(7, 16, 24, 0.88);
    color: #e9f1f7;
    font: 15px system-ui;
  }
  #pageLoading[hidden] {
    display: none;
  }
  #pageLoading .loadingCard {
    text-align: center;
    padding: 28px;
    border: 1px solid #233647;
    border-radius: 16px;
    background: #0d1822;
    max-width: 90vw;
  }
  .pageSpinner {
    display: block;
    width: 36px;
    height: 36px;
    margin: 0 auto 16px;
    border: 3px solid #233647;
    border-top-color: #53a7ff;
    border-radius: 50%;
    animation: pageSpin 0.8s linear infinite;
  }
  .pageSpinner[hidden] {
    display: none;
  }
  @keyframes pageSpin {
    to {
      transform: rotate(360deg);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .pageSpinner {
      animation: none;
    }
  }
  #pageLoading button {
    margin: 14px 5px 0;
    padding: 8px 14px;
    background: #122231;
    color: #e9f1f7;
    border: 1px solid #536879;
    border-radius: 8px;
    cursor: pointer;
  }
</style>
<div id="pageLoading" role="status" aria-live="polite">
  <div class="loadingCard">
    <span class="pageSpinner" aria-hidden="true"></span
    ><span id="pageLoadingText">Cargando datos…</span>
    <div id="pageLoadingActions" hidden>
      <button type="button" onclick="location.reload()">Reintentar</button
      ><button type="button" onclick="pageLoading.dismiss()">Cerrar</button>
    </div>
  </div>
</div>
<script>
  const pageLoading = (() => {
    const box = document.getElementById('pageLoading'),
      label = document.getElementById('pageLoadingText'),
      actions = document.getElementById('pageLoadingActions');
    let initial = true,
      timer;
    function dismiss() {
      box.hidden = true;
      clearTimeout(timer);
    }
    function fail(message) {
      if (!initial) return;
      clearTimeout(timer);
      box.hidden = false;
      label.textContent = message;
      actions.hidden = false;
      box.querySelector('.pageSpinner').hidden = true;
    }
    function show(message) {
      box.hidden = false;
      label.textContent = message;
      actions.hidden = true;
      box.querySelector('.pageSpinner').hidden = false;
      clearTimeout(timer);
      timer = setTimeout(() => {
        label.textContent = 'La carga está tardando más de lo habitual…';
        actions.hidden = false;
      }, 15000);
    }
    show(
      'Cargando ' +
        ({
          '/': 'Dashboard',
          '/index.html': 'Dashboard',
          '/instruments': 'Instrumentos',
          '/account': 'Cuenta activa',
        }[location.pathname.replace(/\/$/, '') || '/'] || 'página') +
        '…',
    );
    document.addEventListener('click', (event) => {
      const a = event.target.closest('a[href]');
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey ||
        event.altKey ||
        !a ||
        a.hasAttribute('download') ||
        (a.target && a.target !== '_self')
      )
        return;
      const url = new URL(a.href, location.href);
      if (
        url.origin !== location.origin ||
        url.hash ||
        !['/', '/index.html', '/instruments', '/account'].includes(
          url.pathname.replace(/\/$/, '') || '/',
        )
      )
        return;
      show('Cargando página…');
    });
    window.addEventListener('pageshow', (event) => {
      if (event.persisted) dismiss();
    });
    return {
      dismiss,
      fail,
      done() {
        initial = false;
        dismiss();
      },
    };
  })();
</script>
'''


def with_page_loading(html):
    return html.replace('<body>', '<body>' + LOADING_UI, 1)
