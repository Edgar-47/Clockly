/**
 * Clockly — mobile.js
 * Mobile-shell exclusive interactions.
 * Assumes core.js has already run and ClocklyCore is available.
 */

(() => {
  "use strict";

  const doc = document;
  const win = window;
  const { rafThrottle } = win.ClocklyCore || {};

  const qs = (sel, root = doc) => root.querySelector(sel);
  const qsa = (sel, root = doc) => Array.from(root.querySelectorAll(sel));

  /* ── 1. Active nav highlight (client-side reinforcement) ────────── */
  (function initMobileNavHighlight() {
    const currentPath = win.location.pathname;
    const navItems = qsa(".mobile-nav__item");

    for (let i = 0; i < navItems.length; i += 1) {
      const item = navItems[i];
      const href = item.getAttribute("href");
      if (!href || href === "#") continue;

      // More precise matching than Jinja2 server-side: exact or prefix
      const isActive = href === "/" ?
        currentPath === "/" :
        currentPath === href || currentPath.startsWith(href + "/");

      if (isActive) {
        item.classList.add("mobile-nav__item--active");
      }
    }
  })();

  /* ── 2. Header actions overflow: show/hide based on content ─────── */
  (function initMobileHeaderActions() {
    const actionsEl = qs("#mobile-header-actions");
    if (!actionsEl) return;

    // If header actions contain only hidden elements, collapse the area
    const visible = qsa("a, button, [type='submit']", actionsEl).filter(el => !el.hidden && !el.closest("[hidden]"));
    if (!visible.length) {
      actionsEl.style.display = "none";
    }
  })();

  /* ── 3. Haptic-like nav tap feedback (visual bounce) ────────────── */
  (function initNavTapFeedback() {
    const navItems = qsa(".mobile-nav__item");

    for (let i = 0; i < navItems.length; i += 1) {
      const item = navItems[i];

      item.addEventListener("touchstart", () => {
        item.style.transform = "scale(0.88)";
      }, { passive: true });

      item.addEventListener("touchend", () => {
        win.setTimeout(() => { item.style.transform = ""; }, 120);
      }, { passive: true });

      item.addEventListener("touchcancel", () => {
        item.style.transform = "";
      }, { passive: true });
    }
  })();

  /* ── 4. Pull-to-refresh prevention (avoid accidental reloads) ───── */
  (function preventOverscroll() {
    // Only prevent on scrolled elements, not the whole body
    doc.addEventListener("touchmove", (e) => {
      const el = e.target.closest(".mobile-content, .card, .table-wrap");
      if (!el) return;
      // Allow scroll within elements but block if at boundary
    }, { passive: true });
  })();

  /* ── 5. Sticky header shadow on scroll ──────────────────────────── */
  (function initHeaderScrollShadow() {
    const header = qs(".mobile-header");
    if (!header) return;

    const mobileContent = qs(".mobile-content");
    const scrollRoot = mobileContent || win;

    function update() {
      const scrollY = mobileContent ? mobileContent.scrollTop : win.scrollY;
      if (scrollY > 4) {
        header.style.boxShadow = "0 2px 12px rgba(16,24,40,0.07)";
        header.style.borderBottomColor = "rgba(15,23,42,0.10)";
      } else {
        header.style.boxShadow = "";
        header.style.borderBottomColor = "";
      }
    }

    if (rafThrottle) {
      scrollRoot.addEventListener("scroll", rafThrottle(update), { passive: true });
    }
    update();
  })();

})();
