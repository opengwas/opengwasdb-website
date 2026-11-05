"""Render the whole site into an output directory.

Inputs, all read at build time:
    the Analysis Catalog          counts, Stores, Analyses, version history
    data/*.yaml, data/*.json      settings, display names, tools, home page words, benchmarks
    content/**/*.md               pages and news posts
    static/                       CSS, JavaScript, fonts, images (served under /assets/)
    templates/                    Jinja layouts

The site is built into `<out>.tmp` and then swapped into place, so a server
never sees a half-written site.
"""
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import jinja2
import yaml
from markupsafe import Markup

from . import content, fmt
from .catalog import Catalog

ROOT = Path(__file__).resolve().parent.parent
SITEMAP_CHUNK = 40_000          # the sitemap protocol allows 50,000 URLs per file
SEARCH_PAGE = 25                # results per page on the Data page
NUMBER_WORDS = "zero one two three four five six seven eight nine ten".split()
# Files from each catalogue version that are published for download, and what they are.
PUBLISHED = {
    "catalog.sqlite": "The whole catalogue as one SQLite file. The Data page searches this file.",
    "analyses.tsv.gz": "Every listed analysis, one per row, as tab-separated text.",
    "stores.tsv": "Every store release, one per row.",
    "changes.tsv": "What this version added, changed or removed.",
}

# The query demo's grid: rows are variants, columns are analyses.
COLS, ROWS = 36, 20


def demo_cells(shape: str) -> dict:
    """The cells each query reads, in the order it reads them."""
    k = lambda r, c: r * COLS + c  # noqa: E731
    col, hit, near = 11, [], []
    if shape == "phewas":
        hit = [k(8, c) for c in range(COLS)]
    elif shape == "regional":
        hit = [k(r, c) for c in range(COLS) for r in (11, 12, 13)]
    elif shape == "bulk":
        hit = [k(r, col) for r in range(ROWS)]
    elif shape == "tophits":
        near = [k(r, col) for r in range(ROWS)]
        hit = [k(r, col) for r in (3, 4, 9, 15)]
    elif shape == "hm3":
        sub = {1, 3, 6, 8, 10, 13, 15, 18}
        hit = [k(r, col) for r in range(ROWS) if r in sub]
        near = [k(r, col) for r in range(ROWS) if r not in sub]
    elif shape == "random_lookup_10_variants_100_analyses":
        hit = [k(r, c) for r in (2, 7, 16) for c in (4, 9, 17, 23, 30)]
    else:
        raise ValueError(f"no demo drawing for query shape {shape!r}")
    return {"hit": hit, "near": [c for c in near if c not in hit]}


# One analysis, as published and as stored: o = observed, - = missing.
# Two of the missing variants stay missing after imputation.
IMPUTED_PATTERN = "ooo-oo--oooo-o-ooo--o-ooo-o--o"
STILL_MISSING = {7, 20}


class Site:
    def __init__(self, catalog_root: Path, out: Path, drafts: bool = False, root: Path = ROOT):
        self.root, self.out, self.drafts = Path(root), Path(out), drafts
        self.catalog = Catalog(catalog_root)
        self.data = {name: yaml.safe_load((self.root / "data" / f"{name}.yaml").read_text())
                     for name in ("site", "home", "stores", "tools")}
        self.bench = json.loads((self.root / "data" / "benchmarks.json").read_text())
        self.urls: list[str] = []
        self.text_env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        self.env = self._env()

    # ---- helpers -------------------------------------------------------

    def _env(self) -> jinja2.Environment:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.root / "templates"),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True)
        env.filters.update(
            nf=fmt.nf, fdate=fmt.fdate, isodate=fmt.isodate, fms=fmt.fms, fbytes=fmt.fbytes, fsize=fmt.fsize,
            label=lambda code, kind: fmt.label(kind, code), ancestry=fmt.ancestry,
            md=lambda s: Markup(content.markdown(s)), md_inline=lambda s: Markup(content.markdown_inline(s)))
        hashes = {p.relative_to(self.root / "static").as_posix(): hashlib.md5(p.read_bytes()).hexdigest()[:8]
                  for p in (self.root / "static").rglob("*") if p.is_file()}
        env.globals.update(
            site=self.data["site"],
            asset=lambda path: f"/assets/{path}?v={hashes[path]}",
            absolute=lambda url: self.data["site"]["base_url"].rstrip("/") + url,
            now=datetime.now(timezone.utc))
        return env

    def fill(self, text: str, **values) -> str:
        """Fill the {{ placeholders }} in a piece of editable text."""
        return self.text_env.from_string(text).render(**values)

    def write(self, url: str, template, listed: bool = True, **ctx):
        """Render a template to the file a URL is served from."""
        path = self.tmp / (url.lstrip("/") + "index.html" if url.endswith("/") else url.lstrip("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        tpl = template if isinstance(template, jinja2.Template) else self.env.get_template(template)
        path.write_text(tpl.render(url=url, **ctx), encoding="utf-8")
        if listed and url.endswith("/"):
            self.urls.append(url)

    def store_names(self, stores: list[dict]) -> None:
        names, colours = self.data["stores"]["stores"], self.data["stores"]["sources"]
        for s in stores:
            n = names.get(s["id"])
            if n is None:
                print(f"warning: {s['id']} is not in data/stores.yaml; using its catalogue label", file=sys.stderr)
                n = {"title": s["label"], "short": s["label"], "source": "Other"}
            s.update(title=n["title"], short=n["short"], source=n["source"],
                     colour=colours.get(n["source"], "sand"))

    # ---- page groups ---------------------------------------------------

    def catalogue_news(self, versions: list[dict], stores: dict) -> list[dict]:
        """One news item per catalogue version, worded from what it changed."""
        def title(sid):
            return stores[sid]["title"] if sid in stores else sid

        def source(sid):
            return stores[sid]["source"] if sid in stores else sid

        items = []
        for v in versions:
            parts, added = [], v["added"]
            if added:
                n = fmt.nf(sum(added.values()))
                if v["first"]:
                    parts.append(f"Catalogue published with {n} analyses from {fmt.join_and(title(s) for s in added)}.")
                elif len(added) == 1:
                    (sid,) = added
                    parts.append(f"{n} analyses added: {title(sid)} (`{sid}`).")
                else:
                    srcs = list(dict.fromkeys(source(s) for s in added))
                    parts.append(f"{n} analyses added in {len(added)} store releases, from {fmt.join_and(srcs)}.")
            if v["changed"]:
                parts.append(f"Metadata updated for {fmt.nf(sum(v['changed'].values()))} analyses in "
                             f"{fmt.join_and(title(s) for s in v['changed'])}.")
            if v["removed"]:
                parts.append(f"{fmt.nf(sum(v['removed'].values()))} analyses withdrawn.")
            items.append({
                "kind": "catalogue", "url": f"/news/catalogue-{v['version']}/",
                "title": "Catalogue published" if v["first"] else "Catalogue updated",
                "date": v["built_at"], "summary": " ".join(parts) or "No changes to listed analyses.",
                "version": v,
            })
        return items

    def home(self, totals: dict, stores: dict, meta: dict) -> dict:
        copy, b = self.data["home"], self.bench
        demo = []
        for rec in b["demo"]:
            sid = rec["store"]
            per_store = {
                "analyses": fmt.nf(rec["n_analyses"]), "variants": fmt.nf(rec["n_variants"]),
                "variant": rec["variant"], "locus": rec["locus"], "id": sid, "measured": fmt.fdate(rec["measured_at"]),
                "hm3_millions": f"{rec['timings']['hm3']['subset'] / 1e6:.1f}",
            }
            shapes = {}
            for key, words in copy["demo"]["shapes"].items():
                t = rec["timings"][key]
                shapes[key] = {
                    "what": words["what"], "sub": content.markdown_inline(self.fill(words["sub"], **per_store)),
                    "time": fmt.fms(t["ms"]),
                    "result": self.fill(copy["demo"]["result"], count=fmt.nf(t["n"]), time=fmt.fms(t["ms"])),
                }
            demo.append({
                "id": sid, "name": stores[sid]["short"] if sid in stores else sid,
                "axis_x": self.fill(copy["demo"]["axis_x"], **per_store),
                "axis_y": self.fill(copy["demo"]["axis_y"], **per_store),
                "fine": content.markdown_inline(self.fill(copy["demo"]["fine"], **per_store)), "shapes": shapes,
            })
        first_shape = next(iter(copy["demo"]["shapes"]))

        size = b["size"]
        ratios = [r["source_bytes"] / r["store_bytes"] for r in size]
        biggest = max(r["source_bytes"] for r in size)
        rows = [{
            "name": stores[r["store"]]["short"] if r["store"] in stores else r["store"],
            "source_pct": 100 * r["source_bytes"] / biggest, "store_pct": 100 * r["store_bytes"] / biggest,
            "label": self.fill(copy["size"]["row"], source=fmt.fbytes(r["source_bytes"]),
                               store=fmt.fbytes(r["store_bytes"]), ratio=f"{r['source_bytes'] / r['store_bytes']:.1f}"),
        } for r in size]
        sp = b["sparse_example"]
        numbers = {"analyses": fmt.nf(totals["analyses"]), "stores": fmt.nf(totals["stores"]),
                   "genome_wide": fmt.nf(totals["genome_wide"]), "imputed": fmt.nf(totals["imputed"]),
                   "built": fmt.fdate(meta["built_at"])}
        return {
            "words": copy, "numbers": numbers, "demo": demo, "first_shape": first_shape,
            "demo_json": json.dumps({
                "stores": demo, "cells": {k: demo_cells(k) for k in copy["demo"]["shapes"]},
                "first": first_shape, "dwell": 3400}).replace("</", "<\\/"),  # safe inside <script>
            "cells": demo_cells(first_shape), "cols": COLS, "rows": ROWS,
            "imputed": {
                "body": self.fill(copy["imputed"]["body"], **numbers),
                "before": ["o" if c == "o" else "" for c in IMPUTED_PATTERN],
                "after": ["o" if c == "o" else "" if i in STILL_MISSING else "m" for i, c in enumerate(IMPUTED_PATTERN)],
            },
            "size": {
                "body": self.fill(copy["size"]["body"], min_ratio=round(min(ratios)), max_ratio=round(max(ratios)),
                                  count_word=NUMBER_WORDS[len(size)] if len(size) < len(NUMBER_WORDS) else len(size),
                                  source_total=fmt.fbytes(sum(r["source_bytes"] for r in size)),
                                  store_total=fmt.fbytes(sum(r["store_bytes"] for r in size))),
                "rows": rows,
                "note": self.fill(copy["size"]["note"], name=stores[sp["store"]]["source"] if sp["store"] in stores else sp["store"],
                                  source=fmt.fbytes(sp["source_bytes"]), store=fmt.fbytes(sp["store_bytes"])),
            },
            "routes": [{**r, "text": self.fill(r["text"], **numbers)} for r in copy["routes"]],
            "updates_intro": self.fill(copy["updates"]["intro"], **numbers),
        }

    def publish_catalogue(self) -> dict:
        """Publish every catalogue version's files at /data/catalog/<version>/.

        A version's files never change, so a page that is reading one version keeps
        working while a newer one is published (decision 7). /data/catalog/current.json
        names the current version and its files, for scripts.
        """
        current = self.catalog.dir.name
        published = {}
        for vdir in sorted((self.catalog.root / "versions").iterdir()):
            files = {}
            for name, what in PUBLISHED.items():
                src = vdir / name
                if not src.is_file():
                    continue
                url = f"/data/catalog/{vdir.name}/{name}"
                dest = self.tmp / url.lstrip("/")
                dest.parent.mkdir(parents=True, exist_ok=True)
                # Always a copy, never a hard link: nothing done to the site's files
                # can then reach the catalogue's own.
                shutil.copyfile(src, dest)
                files[name] = {"url": url, "bytes": src.stat().st_size, "what": what,
                               "sha256": hashlib.sha256(src.read_bytes()).hexdigest()}
            if files:
                (self.tmp / "data/catalog" / vdir.name / "SHA256SUMS").write_text(
                    "".join(f"{f['sha256']}  {n}\n" for n, f in files.items()))
                published[vdir.name] = files
        meta = self.catalog.meta()
        absolute = self.env.globals["absolute"]
        (self.tmp / "data/catalog/current.json").write_text(json.dumps({
            "version": meta["version"], "built_at": meta["built_at"],
            "files": {n: {"url": absolute(f["url"]), "bytes": f["bytes"], "sha256": f["sha256"]}
                      for n, f in published[current].items()},
        }, indent=1) + "\n")
        return {"version": current, "files": published[current]}

    def search(self, stores: dict, download: dict) -> dict:
        """What the Data page's search needs: its filters, the first page of results
        (so the page shows something before, or without, JavaScript), and the
        settings for static/js/catalogue-search.js."""
        cat, asset = self.catalog, self.env.globals["asset"]
        facets = [[("none" if v is None else v) for v in row[:-1]] + [row[-1]] for row in cat.facets()]
        dims = []
        for i, (key, col, name, kind) in enumerate([
                ("ancestry", "ancestry_category", "Ancestry", None),
                ("trait", "trait_class", "Trait", "trait_class"),
                ("outcome", "outcome_type", "Outcome", "outcome_type"),
                ("tissue", "tissue", "Tissue", "tissue"),
                ("store", "store_id", "Store release", None)]):
            assert cat.FACETS[i] == col
            counts = {}
            for row in facets:
                counts[row[i]] = counts.get(row[i], 0) + row[-1]
            values = []
            for v, n in counts.items():
                if key == "ancestry":
                    text = fmt.ancestry(None if v == "none" else v)
                elif key == "store":
                    text = stores[v]["short"] if v in stores else v
                elif v == "none":
                    text = "None"
                else:
                    text = fmt.label(kind, v)
                values.append({"v": v, "label": text, "n": n})
            if key in ("ancestry", "tissue"):
                values.sort(key=lambda x: (x["v"] == "none", -x["n"]))
            else:
                values.sort(key=lambda x: x["v"])
            dims.append({"key": key, "col": col, "label": name, "index": f"analyses_by_{col}", "values": values})
        config = {
            "catalog": download["files"]["catalog.sqlite"]["url"],
            "worker": asset("vendor/sql.js-httpvfs/sqlite.worker.js"),
            "wasm": asset("vendor/sql.js-httpvfs/sql-wasm.wasm"),
            # Results per page, and the catalogue's SQLite page size: each range request
            # fetches whole pages.
            "perPage": SEARCH_PAGE, "dbPageSize": cat.page_size(),
            "facets": facets, "total": sum(r[-1] for r in facets),
            "dims": [{k: d[k] for k in ("key", "col", "label", "index")} | {"values": [{"v": v["v"], "label": v["label"]} for v in d["values"]]} for d in dims],
            "stores": {sid: {"short": s["short"], "colour": s["colour"]} for sid, s in stores.items()},
            "ancestry": {k: fmt.ancestry(k) for k in fmt.ANCESTRY},
            "labels": {k: fmt.LABELS[k] for k in ("trait_class", "outcome_type", "tissue")},
            # Covering indexes, if the catalogue has them (decision 13); otherwise
            # the single-column indexes every catalogue has.
            "browseIndexes": {"name": "analyses_browse_by_label", "size": "analyses_browse_by_sample_size"},
            "plainIndexes": {"name": "analyses_by_analysis_label", "size": "analyses_by_sample_size"},
        }
        return {"dims": dims, "rows": cat.browse(SEARCH_PAGE),
                "config": json.dumps(config, separators=(",", ":")).replace("</", "<\\/")}

    # ---- the build -----------------------------------------------------

    def build(self) -> dict:
        t0 = time.monotonic()
        # One working folder per build, so two builds at once can't mix their files.
        self.tmp = self.out.with_name(f"{self.out.name}.tmp-{os.getpid()}")
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.copytree(self.root / "static", self.tmp / "assets")
        shutil.copy(self.root / "static/img/favicon.ico", self.tmp / "favicon.ico")

        cat = self.catalog
        meta, totals = cat.meta(), cat.totals()
        stores = cat.stores()
        self.store_names(stores)
        by_id = {s["id"]: s for s in stores}
        self.env.globals.update(catalog=meta, totals=totals)

        pages = content.load(self.root / "content", drafts=self.drafts)
        posts = [p for p in pages if p.section == "news"]
        news = self.catalogue_news(cat.versions(), by_id) + [{
            "kind": "post", "url": p.url, "title": p.title, "date": p.meta["date"],
            "summary": p.meta.get("summary", ""), "draft": p.meta.get("draft", False),
        } for p in posts]
        news.sort(key=lambda n: fmt.isodate(n["date"]) + str(n["date"])[10:], reverse=True)

        # Home
        self.write("/", "home.html", section="home", home=self.home(totals, by_id, meta),
                   updates=[n for n in news if n["kind"] == "catalogue"][:3])

        # Data: the catalogue, each Store Release and each Analysis
        download = self.publish_catalogue()
        self.write("/data/", "data.html", section="data", stores=stores, ancestry=cat.ancestry(), download=download,
                   search=self.search(by_id, download))
        self.write("/data/stores/", "stores.html", section="data", stores=stores)
        for s in stores:
            self.write(f"/data/stores/{s['id']}/", "store.html", section="data", store=s,
                       licences=cat.licences(s["id"]), ancestry=cat.ancestry(s["id"]),
                       analyses=cat.analyses(s["id"], limit=25))
        analysis_tpl = self.env.get_template("analysis.html")
        n_analyses = 0
        for a in cat.analyses():
            self.write(f"/data/analyses/{a['store_id']}/{a['analysis_id']}/", analysis_tpl,
                       section="data", a=a, store=by_id[a["store_id"]])
            n_analyses += 1

        # Tools
        tools = []
        for t in self.data["tools"]:
            t = dict(t)
            for k in ("new", "legacy"):
                v = {True: "yes", False: "no"}.get(t[k], t[k])
                if v not in ("yes", "in progress", "no", "unknown"):
                    raise ValueError(f"data/tools.yaml: {t['name']}: {k} is {v!r}")
                t[k] = v
            tools.append(t)
        self.write("/tools/", "tools.html", section="tools", tools=tools)

        # Markdown pages and news
        for p in pages:
            layout = p.meta.get("layout") or ("post.html" if p.section == "news" else "page.html")
            self.write(p.url, layout, section=p.section, page=p, body=Markup(content.markdown(p.body)))
        for n in news:
            if n["kind"] == "catalogue":
                v = n["version"]
                rows = sorted({*v["added"], *v["changed"], *v["removed"]})
                self.write(n["url"], "catalogue_update.html", section="news", item=n, stores=by_id,
                           rows=[{"id": sid, "added": v["added"].get(sid, 0), "changed": v["changed"].get(sid, 0),
                                  "removed": v["removed"].get(sid, 0)} for sid in rows])
        self.write("/news/", "news.html", section="news", items=news)
        self.write("/news/feed.xml", "feed.xml", listed=False, items=[n for n in news if not n.get("draft")][:20])

        # Error pages, sitemap, robots
        self.write("/404.html", "404.html", listed=False, section="")
        self.write("/datasets/404.html", "datasets_404.html", listed=False, section="")
        chunks = [self.urls[i:i + SITEMAP_CHUNK] for i in range(0, len(self.urls), SITEMAP_CHUNK)]
        for i, chunk in enumerate(chunks, 1):
            self.write(f"/sitemap-{i}.xml", "sitemap.xml", listed=False, urls=chunk)
        self.write("/sitemap.xml", "sitemap_index.xml", listed=False, files=[f"/sitemap-{i}.xml" for i in range(1, len(chunks) + 1)])
        (self.tmp / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {self.env.globals['absolute']('/sitemap.xml')}\n")

        # Swap the new site into place
        old = self.out.with_name(f"{self.out.name}.old-{os.getpid()}")
        shutil.rmtree(old, ignore_errors=True)
        if self.out.exists():
            self.out.rename(old)
        self.tmp.rename(self.out)
        shutil.rmtree(old, ignore_errors=True)
        return {"pages": len(self.urls), "analyses": n_analyses, "stores": len(stores),
                "catalogue": meta["version"], "seconds": round(time.monotonic() - t0, 1)}


def build(catalog_root: Path, out: Path, drafts: bool = False, root: Path = ROOT) -> dict:
    return Site(catalog_root, out, drafts=drafts, root=root).build()
