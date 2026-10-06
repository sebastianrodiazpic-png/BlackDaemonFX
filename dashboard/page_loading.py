"""Shared non-blocking initial-data and navigation feedback for the dashboard pages."""

LOADING_UI = r'''
<style>
  #pageLoadingBar {
    position: fixed;
    top: 0;
    left: 0;
    height: 3px;
    width: 0%;
    background: linear-gradient(90deg, #53a7ff, #f5bd36);
    z-index: 10001;
    transition: width 0.25s ease-out, opacity 0.3s ease;
    box-shadow: 0 0 10px rgba(83, 167, 255, 0.7);
    pointer-events: none;
  }
  #pageLoadingBar.active {
    width: 75%;
    animation: barPulse 1.2s ease-in-out infinite alternate;
  }
  #pageLoadingBar.finished {
    width: 100%;
    opacity: 0;
  }
  @keyframes barPulse {
    0% { width: 50%; opacity: 0.9; }
    100% { width: 85%; opacity: 1; }
  }
  #pageLoading {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 10000;
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(13, 24, 34, 0.95);
    border: 1px solid #233647;
    border-radius: 12px;
    padding: 10px 16px;
    color: #e9f1f7;
    font: 13px system-ui;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    transition: opacity 0.2s ease, transform 0.2s ease;
    pointer-events: auto;
  }
  #pageLoading[hidden] {
    display: none;
  }
  .pageSpinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid #233647;
    border-top-color: #53a7ff;
    border-radius: 50%;
    animation: pageSpin 0.8s linear infinite;
    flex-shrink: 0;
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
    .pageSpinner, #pageLoadingBar.active {
      animation: none;
    }
  }
  #pageLoading button {
    margin-left: 6px;
    padding: 4px 10px;
    background: #122231;
    color: #e9f1f7;
    border: 1px solid #536879;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
  }
  #pageLoading button:hover {
    background: #1d354d;
  }
</style>
<div id="pageLoadingBar"></div>
<div id="pageLoading" role="status" aria-live="polite" hidden>
  <span class="pageSpinner" aria-hidden="true"></span>
  <span id="pageLoadingText">Cargando datos…</span>
  <div id="pageLoadingActions" hidden>
    <button type="button" onclick="location.reload()">Reintentar</button>
    <button type="button" onclick="pageLoading.dismiss()">Cerrar</button>
  </div>
</div>
<script>
  const pageLoading = (() => {
    const box = document.getElementById('pageLoading'),
      bar = document.getElementById('pageLoadingBar'),
      label = document.getElementById('pageLoadingText'),
      actions = document.getElementById('pageLoadingActions'),
      spinner = box ? box.querySelector('.pageSpinner') : null;
    let initial = true,
      timer,
      toastTimer;

    function dismiss() {
      if (box) box.hidden = true;
      clearTimeout(timer);
      clearTimeout(toastTimer);
    }

    function fail(message) {
      if (!initial) return;
      clearTimeout(timer);
      clearTimeout(toastTimer);
      if (bar) {
        bar.classList.remove('active');
        bar.classList.remove('finished');
      }
      if (box) {
        box.hidden = false;
        label.textContent = message;
        if (actions) actions.hidden = false;
        if (spinner) spinner.hidden = true;
      }
    }

    function show(message) {
      clearTimeout(timer);
      clearTimeout(toastTimer);
      if (bar) {
        bar.classList.remove('finished');
        bar.classList.add('active');
      }
      // Mostrar toast discreto solo si la carga toma mas de 400ms para evitar parpadeos
      toastTimer = setTimeout(() => {
        if (box) {
          box.hidden = false;
          label.textContent = message;
          if (actions) actions.hidden = true;
          if (spinner) spinner.hidden = false;
        }
      }, 400);

      timer = setTimeout(() => {
        if (box) {
          label.textContent = 'La carga está tardando más de lo habitual…';
          if (actions) actions.hidden = false;
        }
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
        if (bar) {
          bar.classList.remove('active');
          bar.classList.add('finished');
        }
        dismiss();
      },
    };
  })();
</script>
'''


def with_page_loading(html):
    return html.replace('<body>', '<body>' + LOADING_UI, 1)
