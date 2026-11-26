// The Data page's tabs: show one panel at a time, chosen by the address's
// #fragment (#search when there is none), so a tab can be linked to and the
// back button moves between tabs. Without JavaScript every panel is shown and
// the tab links jump to them.
(() => {
  const nav = document.querySelector("[data-tabs]");
  const panels = [...document.querySelectorAll("[data-panel]")];
  if (!nav || !panels.length) return;
  const links = [...nav.querySelectorAll("a")];
  const ids = new Set(panels.map(p => p.id));

  function show(id) {
    for (const p of panels) p.hidden = p.id !== id;
    for (const a of links) {
      if (a.hash === "#" + id) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    }
  }

  // The tabs stay in view when a panel is chosen from further down the page.
  function keepTabsInView() {
    if (nav.getBoundingClientRect().top < 0) nav.scrollIntoView({ block: "start" });
  }

  function fromAddress() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (ids.has(id)) { show(id); return true; }
    if (!location.hash) show(panels[0].id);
    return false;
  }

  document.documentElement.classList.add("has-tabs");
  // The browser jumps to the #fragment's panel once the page has loaded, past the tabs; bring them back.
  if (fromAddress()) addEventListener("load", () => requestAnimationFrame(keepTabsInView), { once: true });
  window.addEventListener("hashchange", () => { if (fromAddress()) keepTabsInView(); });
})();
