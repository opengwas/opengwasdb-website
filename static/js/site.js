// The menu button on narrow screens. Without JavaScript the menu is always shown.
(() => {
  const btn = document.querySelector(".menu-btn");
  const nav = document.getElementById("mainnav");
  if (!btn || !nav) return;
  btn.hidden = false;
  btn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", String(open));
    btn.textContent = open ? "Close" : "Menu";
  });
})();
