/**
 * Clockly — main.js
 * Minimal vanilla JS. No framework dependencies.
 *
 * Features:
 *  - Live clock in the kiosk topbar
 *  - Live elapsed-time counters for active sessions ("duration-live")
 *  - Auto-dismiss flash messages after a timeout
 */

/* ── Live clock ────────────────────────────────────────────── */
(function initLiveClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;

  function tick() {
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    const date = now.toLocaleDateString('es-ES', {
      weekday: 'short', day: '2-digit', month: 'short'
    });
    el.textContent = `${date}  ${hh}:${mm}:${ss}`;
  }
  tick();
  setInterval(tick, 1000);
})();


/* ── Live elapsed time counters ────────────────────────────── */
/**
 * Any element with class "duration-live" and attribute data-since="YYYY-MM-DD HH:MM:SS"
 * will be updated every second showing the elapsed time as "Xh Ym Zs".
 */
(function initDurationCounters() {
  const elements = document.querySelectorAll('.duration-live');
  if (!elements.length) return;

  function parseSince(isoString) {
    // SQLite stores "YYYY-MM-DD HH:MM:SS" — convert space to T for ISO compatibility
    return new Date(isoString.replace(' ', 'T'));
  }

  function formatElapsed(totalSeconds) {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`;
    if (m > 0) return `${m}m ${String(s).padStart(2, '0')}s`;
    return `${s}s`;
  }

  function update() {
    const now = Date.now();
    elements.forEach(el => {
      const since = parseSince(el.dataset.since);
      if (isNaN(since.getTime())) {
        el.textContent = '—';
        return;
      }
      const elapsed = Math.max(0, Math.floor((now - since.getTime()) / 1000));
      el.textContent = formatElapsed(elapsed);

      // Visual warning for very long sessions (>10h)
      if (elapsed > 36000) {
        el.style.color = 'var(--color-danger)';
        el.style.fontWeight = '600';
      } else if (elapsed > 28800) {
        el.style.color = 'var(--color-warning)';
      }
    });
  }

  update();
  setInterval(update, 1000);
})();


/* ── Auto-dismiss flash messages ───────────────────────────── */
(function initFlashDismiss() {
  const SUCCESS_TIMEOUT = 4000;   // ms — success messages disappear quickly
  const INFO_TIMEOUT    = 6000;
  const WARN_TIMEOUT    = 0;      // 0 = don't auto-dismiss (require manual close)
  const ERROR_TIMEOUT   = 0;

  document.querySelectorAll('.flash').forEach(flash => {
    let timeout = 0;
    if (flash.classList.contains('flash--success')) timeout = SUCCESS_TIMEOUT;
    else if (flash.classList.contains('flash--info')) timeout = INFO_TIMEOUT;
    else if (flash.classList.contains('flash--warning')) timeout = WARN_TIMEOUT;
    else if (flash.classList.contains('flash--error')) timeout = ERROR_TIMEOUT;

    if (timeout > 0) {
      setTimeout(() => {
        flash.style.transition = 'opacity 0.3s';
        flash.style.opacity = '0';
        setTimeout(() => flash.remove(), 300);
      }, timeout);
    }
  });
})();


/* ── Confirm before form submit (data-confirm attribute) ────── */
/**
 * Add data-confirm="Are you sure?" to any button or form to show a native
 * confirmation dialog before submitting.
 * Used as a lightweight alternative to inline onclick="return confirm(...)".
 */
document.addEventListener('submit', function(event) {
  const form = event.target;
  const message = form.dataset.confirm;
  if (message && !confirm(message)) {
    event.preventDefault();
  }
});
