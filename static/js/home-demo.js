// The home page query demo. The page works without this script: it shows the
// first Store and query. This adds the tour through the query shapes, which
// pauses on hover, stops when the visitor picks a query, and doesn't start
// when reduced motion is set (decision 11).
(() => {
  const demo = document.getElementById("demo");
  const source = document.getElementById("demo-data");
  if (!demo || !source) return;
  const data = JSON.parse(source.textContent);
  const keys = Object.keys(data.cells);
  const rects = demo.querySelectorAll(".matrix rect");
  const btn = document.getElementById("dPlay");
  const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  let store = 0, shape = data.first, autoplay = false, timer = null, hovering = false;

  function draw() {
    const s = data.stores[store];
    document.getElementById("axisX").textContent = s.axis_x;
    document.getElementById("axisY").textContent = s.axis_y;
    for (const k of keys) {
      demo.querySelector(`[data-t="${k}"]`).textContent = s.shapes[k].time;
      demo.querySelector(`[data-sub="${k}"]`).innerHTML = s.shapes[k].sub;
    }
    demo.querySelector(`input[name="dshape"][value="${shape}"]`).checked = true;
    const { hit, near } = data.cells[shape];
    const order = new Map(hit.map((c, i) => [c, i]));
    const nearSet = new Set(near);
    const step = reduced() ? 0 : Math.min(28, 700 / hit.length);  // each slice fills in reading order
    rects.forEach((r, i) => {
      r.setAttribute("class", order.has(i) ? "hit" : nearSet.has(i) ? "near" : "");
      r.style.transitionDelay = order.has(i) ? `${Math.round(order.get(i) * step)}ms` : "0ms";
    });
    document.getElementById("dResult").textContent = s.shapes[shape].result;
    document.getElementById("dFine").innerHTML = s.fine;
    markPlaying();
  }

  function markPlaying() {
    demo.querySelectorAll(".shape").forEach(l => l.classList.remove("playing"));
    if (autoplay && !hovering) {
      const l = demo.querySelector(`.shape[data-shape="${shape}"]`);
      void l.offsetWidth;  // restart the dwell bar
      l.style.setProperty("--dwell", `${data.dwell}ms`);
      l.classList.add("playing");
    }
  }

  function tick() {
    if (!autoplay || hovering) return;
    shape = keys[(keys.indexOf(shape) + 1) % keys.length];
    draw();
  }

  function setAutoplay(on) {
    autoplay = on;
    clearInterval(timer);
    timer = on ? setInterval(tick, data.dwell) : null;
    btn.textContent = on ? "Pause" : "Play";
    btn.setAttribute("aria-pressed", String(on));
    markPlaying();
  }

  demo.querySelectorAll('input[name="dstore"]').forEach(i => i.addEventListener("change", () => { store = +i.value; draw(); }));
  // Choosing a query yourself stops the tour.
  demo.querySelectorAll('input[name="dshape"]').forEach(i => i.addEventListener("change", () => { shape = i.value; setAutoplay(false); draw(); }));
  btn.addEventListener("click", () => setAutoplay(!autoplay));
  demo.addEventListener("mouseenter", () => { hovering = true; markPlaying(); });
  demo.addEventListener("mouseleave", () => { hovering = false; if (autoplay) setAutoplay(true); });
  btn.hidden = false;
  draw();
  setAutoplay(!reduced());
})();
