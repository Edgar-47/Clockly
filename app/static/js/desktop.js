/**
 * Clockly — desktop.js
 * Desktop-shell exclusive interactions.
 * Assumes core.js has already run and ClocklyCore is available.
 */

(() => {
  "use strict";

  const doc = document;
  const win = window;
  const { rafThrottle, prefersReducedMotion, isTouchDevice } = win.ClocklyCore || {};

  const qs = (sel, root = doc) => root.querySelector(sel);
  const qsa = (sel, root = doc) => Array.from(root.querySelectorAll(sel));

  /* ── 1. Interactive card tilt (desktop hover only) ──────────────── */
  (function initInteractiveCards() {
    if (prefersReducedMotion || isTouchDevice) return;

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
      card.addEventListener("mouseleave", () => { card.style.transform = ""; }, { passive: true });
    }
  })();

  /* ── 2. Button sheen on hover ───────────────────────────────────── */
  (function initButtonMicroPolish() {
    if (prefersReducedMotion || isTouchDevice) return;

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
      button.addEventListener("mouseleave", () => { button.style.backgroundImage = button.dataset.baseGradient || ""; }, { passive: true });
    }
  })();

  /* ── 3. Sidebar drawer (responsive fallback on desktop) ─────────── */
  (function initSidebarDrawer() {
    const toggle = qs("#sidebar-toggle");
    const sidebar = qs("#sidebar");
    const backdrop = qs("#sidebar-backdrop");
    if (!toggle || !sidebar || !backdrop) return;

    const drawerQuery = win.matchMedia("(max-width: 900px)");

    function openSidebar() {
      sidebar.classList.add("sidebar--open");
      backdrop.classList.add("sidebar-backdrop--visible");
      toggle.setAttribute("aria-expanded", "true");
      doc.body.style.overflow = "hidden";
    }

    function closeSidebar() {
      sidebar.classList.remove("sidebar--open");
      backdrop.classList.remove("sidebar-backdrop--visible");
      toggle.setAttribute("aria-expanded", "false");
      doc.body.style.overflow = "";
    }

    toggle.addEventListener("click", () => {
      sidebar.classList.contains("sidebar--open") ? closeSidebar() : openSidebar();
    });

    backdrop.addEventListener("click", closeSidebar);

    doc.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sidebar.classList.contains("sidebar--open")) closeSidebar();
    });

    sidebar.querySelectorAll(".sidebar__link, .sidebar__logout").forEach(link => {
      link.addEventListener("click", () => { if (drawerQuery.matches) closeSidebar(); });
    });

    win.addEventListener("resize", rafThrottle(() => {
      if (!drawerQuery.matches) closeSidebar();
    }), { passive: true });
  })();

  /* ── 4. Topbar action menu (collapses at narrow widths) ─────────── */
  (function initTopbarActions() {
    const topbar = qs(".topbar");
    const toggle = qs("#topbar-actions-toggle");
    const actions = qs("#topbar-actions");
    if (!topbar || !toggle || !actions) return;

    const actionables = qsa("a, button, form, .btn-group", actions);
    if (!actionables.length) { toggle.hidden = true; return; }

    topbar.classList.add("topbar--has-actions");
    toggle.hidden = false;

    function closeActions() {
      topbar.classList.remove("topbar--actions-open");
      toggle.setAttribute("aria-expanded", "false");
    }

    function openActions() {
      topbar.classList.add("topbar--actions-open");
      toggle.setAttribute("aria-expanded", "true");
    }

    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      topbar.classList.contains("topbar--actions-open") ? closeActions() : openActions();
    });

    doc.addEventListener("click", (event) => {
      if (!topbar.classList.contains("topbar--actions-open")) return;
      if (topbar.contains(event.target)) return;
      closeActions();
    });

    doc.addEventListener("keydown", (event) => { if (event.key === "Escape") closeActions(); });

    win.addEventListener("resize", rafThrottle(() => {
      if (win.innerWidth > 720) closeActions();
    }), { passive: true });
  })();

})();
