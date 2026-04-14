/**
 * Clockly — refined interaction layer
 * Premium feel, minimal DOM work, preserves current functionality.
 */

(() => {
  "use strict";

  const doc = document;
  const win = window;
  const prefersReducedMotion = win.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const qs = (selector, root = doc) => root.querySelector(selector);
  const qsa = (selector, root = doc) => Array.from(root.querySelectorAll(selector));

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
      win.requestAnimationFrame(() => {
        fn(...args);
        ticking = false;
      });
    };
  }

  function setMotionMode() {
    if (prefersReducedMotion) {
      doc.documentElement.setAttribute("data-motion", "reduced");
    }
  }

  /* ── 1. Motion mode ─────────────────────────────────────── */
  setMotionMode();

  /* ── 2. Live clocks ─────────────────────────────────────── */
  (function initLiveClock() {
    const clocks = qsa("#live-clock, .kiosk-clock");
    if (!clocks.length) return;

    function tick() {
      const now = new Date();
      const date = now.toLocaleDateString("es-ES", {
        weekday: "short",
        day: "2-digit",
        month: "short"
      });

      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const ss = String(now.getSeconds()).padStart(2, "0");
      const value = `${date}  ${hh}:${mm}:${ss}`;

      for (let i = 0; i < clocks.length; i += 1) {
        clocks[i].textContent = value;
      }
    }

    tick();
    win.setInterval(tick, 1000);
  })();

  /* ── 3. Duration counters ───────────────────────────────── */
  (function initDurationCounters() {
    const elements = qsa(".duration-live");
    if (!elements.length) return;

    const items = elements.map((el) => ({
      el,
      since: parseDate(el.dataset.since),
      state: ""
    }));

    function update() {
      const now = Date.now();

      for (let i = 0; i < items.length; i += 1) {
        const item = items[i];

        if (!item.since) {
          item.el.textContent = "—";
          continue;
        }

        const elapsed = Math.max(0, Math.floor((now - item.since.getTime()) / 1000));
        item.el.textContent = formatElapsed(elapsed);

        let nextState = "";
        if (elapsed > 36000) nextState = "danger";
        else if (elapsed > 28800) nextState = "warning";

        if (nextState !== item.state) {
          item.state = nextState;

          if (nextState === "danger") {
            item.el.style.color = "var(--color-danger)";
            item.el.style.fontWeight = "700";
          } else if (nextState === "warning") {
            item.el.style.color = "var(--color-warning)";
            item.el.style.fontWeight = "700";
          } else {
            item.el.style.color = "";
            item.el.style.fontWeight = "";
          }
        }
      }
    }

    update();
    win.setInterval(update, 1000);
  })();

  /* ── 4. Flash + kiosk message dismiss ───────────────────── */
  (function initFlashDismiss() {
    const flashes = qsa(".flash, .flash-message");
    if (!flashes.length) return;

    for (let i = 0; i < flashes.length; i += 1) {
      const flash = flashes[i];
      let timeout = 0;

      if (flash.classList.contains("flash--success")) timeout = 3600;
      else if (flash.classList.contains("flash--info")) timeout = 5200;

      const closeButton = qs(".flash__close, .flash-close", flash);
      if (closeButton) {
        closeButton.addEventListener("click", () => fadeOut(flash), { passive: true });
      }

      if (timeout > 0) {
        win.setTimeout(() => fadeOut(flash), timeout);
      }
    }
  })();

  /* ── 5. Forms: confirm + double submit + loading ───────── */
  (function initFormHandling() {
    doc.addEventListener("submit", (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;

      const confirmMessage = form.dataset.confirm;
      if (confirmMessage && !win.confirm(confirmMessage)) {
        event.preventDefault();
        return;
      }

      if (form.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }

      form.dataset.submitting = "true";

      const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
      if (!submitButton) return;

      submitButton.disabled = true;
      submitButton.classList.add("is-loading");

      if (submitButton.tagName === "BUTTON" && !submitButton.dataset.originalText) {
        submitButton.dataset.originalText = submitButton.textContent.trim();
        submitButton.textContent = "Procesando";
      }
    });

    /* restore states on bfcache navigation */
    win.addEventListener("pageshow", () => {
      const buttons = qsa(".is-loading");
      for (let i = 0; i < buttons.length; i += 1) {
        const button = buttons[i];
        button.classList.remove("is-loading");
        button.disabled = false;
        if (button.dataset.originalText) {
          button.textContent = button.dataset.originalText;
        }
      }

      const forms = qsa("form[data-submitting='true']");
      for (let i = 0; i < forms.length; i += 1) {
        forms[i].dataset.submitting = "false";
      }
    });
  })();

  /* ── 6. Confirm clicks outside forms ───────────────────── */
  (function initConfirmClicks() {
    doc.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-confirm-click]");
      if (!trigger) return;

      const message = trigger.getAttribute("data-confirm-click");
      if (!win.confirm(message)) {
        event.preventDefault();
      }
    });
  })();

  /* ── 7. Modal helpers ───────────────────────────────────── */
  (function initModalHelpers() {
    const modals = qsa(".modal");
    if (!modals.length) return;

    let lastFocused = null;

    function getFocusable(modal) {
      return qsa(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        modal
      ).filter((el) => !el.hidden);
    }

    function open(modal) {
      if (!modal) return;
      lastFocused = doc.activeElement;
      modal.hidden = false;
      doc.body.style.overflow = "hidden";

      const focusable = getFocusable(modal);
      if (focusable.length) {
        win.setTimeout(() => focusable[0].focus(), 24);
      }
    }

    function close(modal) {
      if (!modal) return;
      modal.hidden = true;
      doc.body.style.overflow = "";

      const passwordField = modal.querySelector('input[type="password"]');
      if (passwordField) passwordField.value = "";

      if (lastFocused && typeof lastFocused.focus === "function") {
        lastFocused.focus();
      }
    }

    win.ClocklyModal = { open, close };

    for (let i = 0; i < modals.length; i += 1) {
      const modal = modals[i];

      modal.addEventListener("click", (event) => {
        if (event.target.classList.contains("modal__overlay")) {
          close(modal);
        }
      });
    }

    doc.addEventListener("keydown", (event) => {
      if (event.key !== "Escape") return;

      for (let i = 0; i < modals.length; i += 1) {
        const modal = modals[i];
        if (!modal.hidden) {
          close(modal);
          break;
        }
      }
    });
  })();

  /* ── 8. Reveal-on-load polish ───────────────────────────── */
  (function initRevealOnLoad() {
    if (prefersReducedMotion) return;

    const targets = qsa(
      ".card, .stat-card, .kiosk-card, .login-card, .employee-card, .colleague-card, .status-section, .colleague-section, .welcome-card"
    );
    if (!targets.length) return;

    for (let i = 0; i < targets.length; i += 1) {
      const el = targets[i];
      el.style.opacity = "0";
      el.style.transform = "translateY(8px)";

      win.setTimeout(() => {
        el.style.transition =
          "opacity 280ms cubic-bezier(.22,1,.36,1), transform 280ms cubic-bezier(.22,1,.36,1)";
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
      }, 24 + i * 20);
    }
  })();

  /* ── 9. Refined card pointer response ───────────────────── */
  (function initInteractiveCards() {
    if (prefersReducedMotion) return;

    const cards = qsa(".stat-card, .kiosk-card, .employee-card, .colleague-card");
    if (!cards.length) return;

    const handleMove = rafThrottle((card, event) => {
      const rect = card.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width;
      const py = (event.clientY - rect.top) / rect.height;

      const x = (px - 0.5) * 4;
      const y = (py - 0.5) * 4;

      card.style.transform = `translateY(-2px) rotateX(${-y * 0.22}deg) rotateY(${x * 0.22}deg)`;
    });

    for (let i = 0; i < cards.length; i += 1) {
      const card = cards[i];

      card.addEventListener("mousemove", (event) => handleMove(card, event), { passive: true });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
      }, { passive: true });
    }
  })();

  /* ── 10. Button sheen polish ────────────────────────────── */
  (function initButtonMicroPolish() {
    if (prefersReducedMotion) return;

    const buttons = qsa(".btn, .button-login, .button-large, .button-submit, .button-punch, .button-small");
    if (!buttons.length) return;

    const update = rafThrottle((button, event) => {
      const rect = button.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 100;
      const y = ((event.clientY - rect.top) / rect.height) * 100;
      button.style.backgroundImage = `
        radial-gradient(circle at ${x}% ${y}%, rgba(255,255,255,0.18), transparent 38%),
        ${button.dataset.baseGradient || ""}
      `;
    });

    for (let i = 0; i < buttons.length; i += 1) {
      const button = buttons[i];
      const computed = getComputedStyle(button).backgroundImage;
      button.dataset.baseGradient = computed === "none" ? "" : computed;

      button.addEventListener("mousemove", (event) => update(button, event), { passive: true });
      button.addEventListener("mouseleave", () => {
        button.style.backgroundImage = button.dataset.baseGradient || "";
      }, { passive: true });
    }
  })();
})();