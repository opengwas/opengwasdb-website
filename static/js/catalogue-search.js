// The Data page's catalogue search.
//
// Queries the catalogue's SQLite file in the browser, fetching only the parts
// each query needs over HTTP range requests (decision 7). Each request is a
// round trip, so every query is planned to make as few as possible
// (decision 13):
//   - Counts for any combination of filters come from the build (`facets`),
//     so no query is needed to count, and a combination with no analyses is
//     never queried.
//   - A selective filter (at most SMALL analyses) reads its own rows through
//     its index, then sorts them; they sit together in the file.
//   - Otherwise the query walks the index for the chosen sort. With the
//     catalogue's covering indexes, filters are checked inside the index and
//     results come straight from it, without fetching rows.
// Without JavaScript the page shows the first 25 analyses by sample size.
(() => {
  const root = document.getElementById("search");
  const cfgEl = document.getElementById("search-config");
  if (!root || !cfgEl || typeof createDbWorker !== "function") return;
  const C = JSON.parse(cfgEl.textContent);
  const form = root.querySelector("[data-form]");
  const status = root.querySelector("[data-status]");
  const rowsEl = root.querySelector("[data-rows]");
  const pager = root.querySelector("[data-pager]");
  const clearBtn = root.querySelector("[data-clear]");
  const PAGE = C.perPage;
  const SMALL = 2000;
  const COLS = "a.id, a.store_id, a.analysis_label, a.ancestry_category, a.sample_size, a.trait_class, a.outcome_type, a.tissue";
  const ORDER = { name: "a.analysis_label, a.id", size: "a.sample_size desc, a.id desc" };
  const SORT_TEXT = { relevance: "best match first", size: "largest sample size first", name: "by name" };
  const nf = n => Number(n).toLocaleString("en-GB");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const plural = (n, one, many) => `${nf(n)} ${n === 1 ? one : many}`;

  // ---- what the visitor asked for, kept in the address so it can be shared
  function readState() {
    const p = new URLSearchParams(location.search);
    const s = { q: (p.get("q") || "").trim(), f: {}, sort: p.get("sort") || "", page: Math.max(1, parseInt(p.get("page"), 10) || 1) };
    for (const d of C.dims) {
      const v = p.get(d.key);
      if (v !== null && d.values.some(x => x.v === v)) s.f[d.key] = v;
    }
    if (!(s.sort in SORT_TEXT) || (s.sort === "relevance" && !s.q)) s.sort = s.q ? "relevance" : "size";
    return s;
  }
  function toUrl(s) {
    const p = new URLSearchParams();
    if (s.q) p.set("q", s.q);
    for (const d of C.dims) if (s.f[d.key] !== undefined) p.set(d.key, s.f[d.key]);
    if (s.sort !== (s.q ? "relevance" : "size")) p.set("sort", s.sort);
    if (s.page > 1) p.set("page", s.page);
    const qs = p.toString();
    return location.pathname + (qs ? "?" + qs : "");
  }
  const isDefault = s => !s.q && !Object.keys(s.f).length && s.sort === "size" && s.page === 1;

  // ---- counts from the build, for any combination of filters
  function count(f, except) {
    let n = 0;
    for (const row of C.facets) {
      if (C.dims.every((d, i) => d.key === except || f[d.key] === undefined || row[i] === f[d.key])) n += row[row.length - 1];
    }
    return n;
  }
  function optionCounts(f, key) {
    const i = C.dims.findIndex(d => d.key === key), out = {};
    for (const row of C.facets) {
      if (C.dims.every((d, j) => d.key === key || f[d.key] === undefined || row[j] === f[d.key])) out[row[i]] = (out[row[i]] || 0) + row[row.length - 1];
    }
    return out;
  }

  // ---- the catalogue, opened on first use
  let dbPromise = null, covering = false;
  function db() {
    dbPromise ??= createDbWorker(
      [{ from: "inline", config: { serverMode: "full", url: C.catalog, requestChunkSize: C.dbPageSize } }], C.worker, C.wasm,
    ).then(async w => {
      const [{ n }] = await w.db.query("select count(*) as n from sqlite_master where type = 'index' and name in (?, ?)",
        [C.browseIndexes.name, C.browseIndexes.size]);
      covering = n === 2;
      return w.db;
    });
    return dbPromise;
  }
  // Read the top of each tree a search walks (the full-text index, the table and
  // the sort indexes) while the page is idle, so the first real search starts
  // with them in memory. Each lookup below finds nothing or almost nothing.
  async function warm() {
    const d = await db();
    const q = [
      ["select count(*) as n from analysis_search where analysis_search match ?", ['"opengwaswarm"']],
      ["select id from analyses where rowid = (select max(rowid) / 2 from analyses)", []],
      [`select id from analyses a indexed by ${sortIndex("size")} where a.listed = 1 order by ${ORDER.size} limit 1`, []],
      [`select id from analyses a indexed by ${sortIndex("name")} where a.listed = 1 order by ${ORDER.name} limit 1`, []],
    ];
    for (const [sql, params] of q) {
      if (seq) return;  // the visitor has started; don't get in the way
      await d.query(sql, params);
    }
  }

  // ---- turning the request into SQL
  function filterSql(f) {
    const conds = [], params = [];
    for (const d of C.dims) {
      const v = f[d.key];
      if (v === undefined) continue;
      if (v === "none") conds.push(`a.${d.col} is null`);
      else { conds.push(`a.${d.col} = ?`); params.push(v); }
    }
    return { sql: conds.map(c => ` and ${c}`).join(""), params };
  }
  // Words become an FTS5 query: every word must match, and the last may be the start of a word.
  function match(q) {
    const words = q.match(/[\p{L}\p{N}]+/gu) || [];
    return words.map((w, i) => `"${w}"${i === words.length - 1 ? "*" : ""}`).join(" ");
  }
  const sortIndex = sort => (covering ? C.browseIndexes : C.plainIndexes)[sort];
  function bestFilter(f) {
    let best = null;
    for (const d of C.dims) {
      if (f[d.key] === undefined) continue;
      const n = count({ [d.key]: f[d.key] });
      if (!best || n < best.n) best = { d, n };
    }
    return best;
  }
  function plan(s) {
    const w = filterSql(s.f), limit = PAGE + 1, offset = (s.page - 1) * PAGE;
    if (s.q) {
      const m = match(s.q);
      if (s.sort === "relevance" || !covering) {
        const order = s.sort === "relevance" ? "s.rank" : ORDER[s.sort];
        return { sql: `select ${COLS} from analysis_search s join analyses a on a.rowid = s.rowid
                       where analysis_search match ? and a.listed = 1${w.sql} order by ${order} limit ? offset ?`,
                 params: [m, ...w.params, limit, offset], match: m, w };
      }
      return { sql: `select ${COLS} from analyses a indexed by ${sortIndex(s.sort)} where a.listed = 1${w.sql}
                     and a.rowid in (select rowid from analysis_search where analysis_search match ?)
                     order by ${ORDER[s.sort]} limit ? offset ?`,
               params: [...w.params, m, limit, offset], match: m, w };
    }
    const best = bestFilter(s.f);
    // Without the covering indexes, walking a sort index fetches a row per step, so a
    // filter's own index is always better: its rows sit together and are read in bulk.
    const index = best && (best.n <= SMALL || !covering) ? best.d.index : sortIndex(s.sort);
    return { sql: `select ${COLS} from analyses a indexed by ${index} where a.listed = 1${w.sql}
                   order by ${ORDER[s.sort]} limit ? offset ?`,
             params: [...w.params, limit, offset] };
  }
  // How many analyses a search matches. Counting the words alone reads only the
  // search index. With filters, a few hundred matches are cheapest to check one
  // by one; more than that, by walking a covering index once.
  async function countMatches(d, p) {
    const [{ n }] = await d.query("select count(*) as n from analysis_search where analysis_search match ?", [p.match]);
    if (!p.w.sql || n === 0) return n;
    const viaMatches = n <= 500 || !covering;
    const sql = viaMatches
      ? `select count(*) as n from analysis_search s join analyses a on a.rowid = s.rowid
         where analysis_search match ? and a.listed = 1${p.w.sql}`
      : `select count(*) as n from analyses a indexed by ${C.browseIndexes.name}
         where a.listed = 1${p.w.sql} and a.rowid in (select rowid from analysis_search where analysis_search match ?)`;
    const [{ n: m }] = await d.query(sql, viaMatches ? [p.match, ...p.w.params] : [...p.w.params, p.match]);
    return m;
  }

  // ---- showing the results
  function kind(r) {
    const t = C.labels.trait_class[r.trait_class] || r.trait_class || "";
    const second = r.tissue ? (C.labels.tissue[r.tissue] || r.tissue) : (C.labels.outcome_type[r.outcome_type] || r.outcome_type || "").toLowerCase();
    return second ? `${t}, ${second}` : t;
  }
  function rowHtml(r) {
    const aid = r.id.slice(r.store_id.length + 1), st = C.stores[r.store_id] || { short: r.store_id, colour: "taupe" };
    return `<tr><td class="an"><a href="/data/analyses/${esc(r.store_id)}/${esc(aid)}/">${esc(r.analysis_label || aid)}</a> <code>${esc(aid)}</code></td>`
      + `<td class="st"><span class="bean" style="background:var(--${esc(st.colour)})" aria-hidden="true"></span>${esc(st.short)}</td>`
      + `<td class="anc-c">${esc(C.ancestry[r.ancestry_category ?? "unassigned"] || r.ancestry_category)}</td>`
      + `<td class="num">${r.sample_size ? nf(r.sample_size) : ""}</td><td class="kind">${esc(kind(r))}</td></tr>`;
  }
  function describe(s, total, shown) {
    const from = (s.page - 1) * PAGE + 1, to = from + shown - 1;
    const what = s.q ? ` matching “${esc(s.q)}”` : "";
    if (total === 0 || (shown === 0 && s.page === 1)) return `No analyses${what || " match these filters"}.`;
    if (shown === 0) return `No more analyses${what}.`;
    if (total === null) return `Analyses ${nf(from)}–${nf(to)}${what}, ${SORT_TEXT[s.sort]}. Counting the rest…`;
    const range = total <= PAGE && s.page === 1 ? "" : `${nf(from)}–${nf(to)} of `;
    return `${range}${nf(total)} ${total === 1 ? "analysis" : "analyses"}${what}, ${SORT_TEXT[s.sort]}.`;
  }

  // ---- keeping the form in step with the request
  function syncForm(s) {
    if (document.activeElement !== form.elements.q) form.elements.q.value = s.q;  // never rewrite what's being typed
    for (const d of C.dims) {
      const sel = form.elements[d.key], counts = optionCounts(s.f, d.key);
      sel.value = s.f[d.key] ?? "";
      for (const opt of sel.options) {
        if (!opt.value) continue;
        const v = d.values.find(x => x.v === opt.value), n = counts[opt.value] || 0;
        opt.textContent = `${v.label} (${nf(n)})`;
        opt.disabled = n === 0 && sel.value !== opt.value;
      }
    }
    const sort = form.elements.sort;
    sort.querySelector('option[value="relevance"]').disabled = !s.q;
    sort.value = s.sort;
    clearBtn.hidden = !s.q && !Object.keys(s.f).length;
  }

  // ---- running a request; only the latest one is shown
  let seq = 0, state = readState();
  async function run(s, { push = false, replace = false } = {}) {
    if (s.q && !match(s.q)) s = { ...s, q: "", sort: s.sort === "relevance" ? "size" : s.sort };  // nothing searchable typed
    state = s;
    const mine = ++seq;
    if (push) history.pushState(null, "", toUrl(s));
    else if (replace) history.replaceState(null, "", toUrl(s));
    syncForm(s);
    let total = s.q ? null : count(s.f);
    if (total === 0) return show(s, mine, [], 0);
    root.setAttribute("aria-busy", "true");
    status.textContent = dbPromise ? "Searching…" : "Opening the catalogue…";
    try {
      const d = await db();
      if (mine !== seq) return;  // a newer request has already started
      const p = plan(s);
      const rows = await d.query(p.sql, p.params);
      if (mine !== seq) return;
      if (s.q && s.page === 1 && rows.length <= PAGE) total = rows.length;  // it all fits on this page
      show(s, mine, rows, total);
      if (s.q && total === null && mine === seq) {
        const n = await countMatches(d, p);
        if (mine === seq) show(s, mine, rows, n);
      }
    } catch (e) {
      if (mine !== seq) return;
      root.removeAttribute("aria-busy");
      status.textContent = `The search failed (${e.message || e}). Try again, or download the catalogue below.`;
    }
  }
  function show(s, mine, rows, total) {
    if (mine !== seq) return;
    root.removeAttribute("aria-busy");
    const shown = Math.min(rows.length, PAGE);
    rowsEl.innerHTML = rows.slice(0, PAGE).map(rowHtml).join("");
    status.innerHTML = describe(s, total, shown);
    const more = rows.length > PAGE;
    pager.hidden = s.page === 1 && !more;
    pager.querySelector("[data-prev]").disabled = s.page === 1;
    pager.querySelector("[data-next]").disabled = !more;
    pager.querySelector("[data-page]").textContent = total ? `Page ${nf(s.page)} of ${nf(Math.ceil(total / PAGE))}` : `Page ${nf(s.page)}`;
  }

  // ---- wiring up the controls
  const fromForm = () => {
    const s = { q: form.elements.q.value.trim(), f: {}, sort: form.elements.sort.value, page: 1 };
    for (const d of C.dims) if (form.elements[d.key].value) s.f[d.key] = form.elements[d.key].value;
    if (s.q && !state.q) s.sort = "relevance";
    if (!s.q && s.sort === "relevance") s.sort = "size";
    return s;
  };
  let typing = null;
  form.elements.q.addEventListener("input", () => {
    clearTimeout(typing);
    typing = setTimeout(() => run(fromForm(), { replace: true }), 350);
  });
  // Most visitors to this page search, so open the catalogue as soon as the page is idle.
  (window.requestIdleCallback || (f => setTimeout(f, 500)))(() => warm().catch(() => {}), { timeout: 2000 });
  form.addEventListener("submit", e => { e.preventDefault(); clearTimeout(typing); run(fromForm(), { push: true }); });
  for (const name of [...C.dims.map(d => d.key), "sort"]) {
    form.elements[name].addEventListener("change", () => run(fromForm(), { push: true }));
  }
  clearBtn.addEventListener("click", () => run({ q: "", f: {}, sort: "size", page: 1 }, { push: true }));
  const turn = step => {
    run({ ...state, page: state.page + step }, { push: true });
    root.scrollIntoView({ block: "start" });
  };
  pager.querySelector("[data-prev]").addEventListener("click", () => turn(-1));
  pager.querySelector("[data-next]").addEventListener("click", () => turn(1));
  addEventListener("popstate", () => run(readState()));

  for (const el of form.elements) el.disabled = false;
  syncForm(state);
  if (isDefault(state)) {
    pager.hidden = C.total <= PAGE;
    pager.querySelector("[data-prev]").disabled = true;
    pager.querySelector("[data-page]").textContent = `Page 1 of ${nf(Math.ceil(C.total / PAGE))}`;
  } else {
    run(state);
  }
})();
