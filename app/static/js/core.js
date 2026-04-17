/**
 * Clockly — core.js
 * Shared interaction layer loaded by both desktop and mobile shells.
 * No layout or platform assumptions here — pure behaviour.
 */

(() => {
  "use strict";

  const doc = document;
  const win = window;
  const prefersReducedMotion = win.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Exported surface for platform-specific scripts
  win.ClocklyCore = {};

  /* ── Utilities ──────────────────────────────────────────────────── */

  function parseDate(value) {
    if (!value) return null;
    const normalized = value.includes("T") ? value : value.replace(" ", "T");
    const date = new Date(normalized);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function formatElapsed(totalSeconds) {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    if (h > 0) return `${h}h ${String(m).padStart(2, "0")}m`;
    if (m > 0) return `${m}m ${String(s).padStart(2, "0")}s`;
    return `${s}s`;
  }

  function fadeOut(el, duration = 180) {
    if (!el) return;
    el.style.transition = `opacity ${duration}ms ease, transform ${duration}ms ease`;
    el.style.opacity = "0";
    el.style.transform = "translateY(-4px)";
    win.setTimeout(() => el.remove(), duration);
  }

  function rafThrottle(fn) {
    let ticking = false;
    return (...args) => {
      if (ticking) return;
      ticking = true;
      win.requestAnimationFrame(() => { fn(...args); ticking = false; });
    };
  }

  const qs = (sel, root = doc) => root.querySelector(sel);
  const qsa = (sel, root = doc) => Array.from(root.querySelectorAll(sel));

  // Export utils so desktop.js / mobile.js can reuse them
  win.ClocklyCore.rafThrottle = rafThrottle;
  win.ClocklyCore.prefersReducedMotion = prefersReducedMotion;
  win.ClocklyCore.isTouchDevice = win.matchMedia("(hover: none) and (pointer: coarse)").matches;

  /* ── 1. Motion mode ─────────────────────────────────────────────── */
  if (prefersReducedMotion) {
    doc.documentElement.setAttribute("data-motion", "reduced");
  }

  /* ── 2. Live clocks ─────────────────────────────────────────────── */
  (function initLiveClock() {
    const clocks = qsa("#live-clock, .kiosk-clock");
    if (!clocks.length) return;

    function tick() {
      if (doc.hidden) return;
      const now = new Date();
      const date = now.toLocaleDateString("es-ES", { weekday: "short", day: "2-digit", month: "short" });
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const ss = String(now.getSeconds()).padStart(2, "0");
      const value = `${date}  ${hh}:${mm}:${ss}`;
      for (let i = 0; i < clocks.length; i += 1) clocks[i].textContent = value;
    }

    tick();
    win.setInterval(tick, 1000);
  })();

  /* ── 3. Duration counters ───────────────────────────────────────── */
  (function initDurationCounters() {
    const elements = qsa(".duration-live");
    if (!elements.length) return;

    const items = elements.map(el => ({ el, since: parseDate(el.dataset.since), state: "" }));

    function update() {
      if (doc.hidden) return;
      const now = Date.now();
      for (let i = 0; i < items.length; i += 1) {
        const item = items[i];
        if (!item.since) { item.el.textContent = "—"; continue; }
        const elapsed = Math.max(0, Math.floor((now - item.since.getTime()) / 1000));
        item.el.textContent = formatElapsed(elapsed);
        let nextState = "";
        if (elapsed > 36000) nextState = "danger";
        else if (elapsed > 28800) nextState = "warning";
        if (nextState !== item.state) {
          item.state = nextState;
          if (nextState === "danger") { item.el.style.color = "var(--color-danger)"; item.el.style.fontWeight = "700"; }
          else if (nextState === "warning") { item.el.style.color = "var(--color-warning)"; item.el.style.fontWeight = "700"; }
          else { item.el.style.color = ""; item.el.style.fontWeight = ""; }
        }
      }
    }

    update();
    win.setInterval(update, 1000);
  })();

  /* ── 4. Flash dismiss ───────────────────────────────────────────── */
  (function initFlashDismiss() {
    const flashes = qsa(".flash, .flash-message");
    if (!flashes.length) return;

    for (let i = 0; i < flashes.length; i += 1) {
      const flash = flashes[i];
      let timeout = 0;
      if (flash.classList.contains("flash--success")) timeout = 3600;
      else if (flash.classList.contains("flash--info")) timeout = 5200;

      const closeBtn = qs(".flash__close, .flash-close", flash);
      if (closeBtn) closeBtn.addEventListener("click", () => fadeOut(flash), { passive: true });
      if (timeout > 0) win.setTimeout(() => fadeOut(flash), timeout);
    }
  })();

  /* ── 5. Forms: confirm + double-submit protection ───────────────── */
  (function initFormHandling() {
    doc.addEventListener("submit", (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;

      const confirmMessage = form.dataset.confirm;
      if (confirmMessage && !win.confirm(confirmMessage)) { event.preventDefault(); return; }

      if (form.dataset.submitting === "true") { event.preventDefault(); return; }
      form.dataset.submitting = "true";

      const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
      if (!submitBtn) return;
      submitBtn.disabled = true;
      submitBtn.classList.add("is-loading");
      if (submitBtn.tagName === "BUTTON" && !submitBtn.dataset.originalText) {
        submitBtn.dataset.originalText = submitBtn.textContent.trim();
        submitBtn.textContent = "Procesando";
      }
    });

    // Restore on bfcache navigation
    win.addEventListener("pageshow", () => {
      qsa(".is-loading").forEach(btn => {
        btn.classList.remove("is-loading");
        btn.disabled = false;
        if (btn.dataset.originalText) btn.textContent = btn.dataset.originalText;
      });
      qsa("form[data-submitting='true']").forEach(f => { f.dataset.submitting = "false"; });
    });
  })();

  /* ── 6. Confirm clicks ──────────────────────────────────────────── */
  (function initConfirmClicks() {
    doc.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-confirm-click]");
      if (!trigger) return;
      if (!win.confirm(trigger.getAttribute("data-confirm-click"))) event.preventDefault();
    });
  })();

  /* ── 7. Modal helpers ───────────────────────────────────────────── */
  (function initModalHelpers() {
    const modals = qsa(".modal");
    if (!modals.length) return;

    let lastFocused = null;

    function getFocusable(modal) {
      return qsa('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])', modal).filter(el => !el.hidden);
    }

    function open(modal) {
      if (!modal) return;
      lastFocused = doc.activeElement;
      modal.hidden = false;
      doc.body.style.overflow = "hidden";
      const focusable = getFocusable(modal);
      if (focusable.length) win.requestAnimationFrame(() => focusable[0].focus());
    }

    function close(modal) {
      if (!modal) return;
      modal.hidden = true;
      doc.body.style.overflow = "";
      const pwd = modal.querySelector('input[type="password"]');
      if (pwd) pwd.value = "";
      if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
    }

    win.ClocklyModal = { open, close };

    for (let i = 0; i < modals.length; i += 1) {
      const modal = modals[i];
      modal.addEventListener("click", (event) => {
        if (event.target.classList.contains("modal__overlay")) close(modal);
      });
    }

    doc.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;
      for (let i = 0; i < modals.length; i += 1) {
        if (!modals[i].hidden) { close(modals[i]); break; }
      }
    });
  })();

  /* ── 8. Reveal-on-load ──────────────────────────────────────────── */
  (function initRevealOnLoad() {
    if (prefersReducedMotion) return;

    const targets = qsa(".card, .stat-card, .kiosk-card, .login-card, .employee-card, .colleague-card, .status-section, .colleague-section, .welcome-card");
    if (!targets.length) return;

    for (let i = 0; i < targets.length; i += 1) {
      const el = targets[i];
      el.style.opacity = "0";
      el.style.transform = "translateY(8px)";
      win.setTimeout(() => {
        el.style.transition = "opacity 280ms cubic-bezier(.22,1,.36,1), transform 280ms cubic-bezier(.22,1,.36,1)";
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
      }, 24 + i * 20);
    }
  })();

  /* ── 9. Responsive filter disclosures (both platforms) ──────────── */
  (function initResponsiveDisclosures() {
    const disclosures = qsa("details[data-mobile-collapsed]");
    if (!disclosures.length) return;

    const mobileQuery = win.matchMedia("(max-width: 640px)");
    const isMobileShell = doc.documentElement.dataset.platform === "mobile";

    function syncDisclosure(details) {
      if (details.dataset.userToggled === "true") return;
      // Mobile shell: always use collapsed behaviour; desktop: open on wide viewports
      if (!isMobileShell && !mobileQuery.matches) { details.open = true; return; }
      details.open = details.dataset.hasFilters === "true";
    }

    for (let i = 0; i < disclosures.length; i += 1) {
      const details = disclosures[i];
      const summary = qs("summary", details);
      if (summary) summary.addEventListener("click", () => { details.dataset.userToggled = "true"; });
      syncDisclosure(details);
    }

    if (!isMobileShell) {
      win.addEventListener("resize", rafThrottle(() => {
        for (let i = 0; i < disclosures.length; i += 1) syncDisclosure(disclosures[i]);
      }), { passive: true });
    }
  })();

})();
