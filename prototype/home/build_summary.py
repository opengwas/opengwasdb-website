"""PROTOTYPE: fake the `summary.json` the catalogue build should one day emit.

Reads the Analysis Catalog read-only and writes summary.json next to this file.
Throwaway; see prototype/home/README.md.
"""
import csv
import io
import json
import sqlite3
import subprocess
from pathlib import Path

CATALOG = Path("/data/opengwasdb/stores/catalog")
OUT = Path(__file__).with_name("summary.json")

# Catalogue gap: no source-provider or human-readable title per Store yet.
STORE_META = {
    "OGS-00006": ("GWAS Catalog", "Chen et al. 2023 plasma metabolome, European"),
    "OGS-00009": ("UK Biobank (MRC IEU)", "UK Biobank, MRC IEU analyses (ukb-b)"),
    "OGS-00011": ("GWAS Catalog", "GWAS Catalog harmonised studies, European"),
    "OGS-00012": ("Million Veteran Program", "Million Veteran Program, European"),
    "OGS-00013": ("Million Veteran Program", "Million Veteran Program, African"),
    "OGS-00014": ("Million Veteran Program", "Million Veteran Program, Admixed American"),
    "OGS-00015": ("Million Veteran Program", "Million Veteran Program, East Asian"),
    "OGS-00016": ("Million Veteran Program", "Million Veteran Program, multi-ancestry meta-analysis"),
    "OGS-00017": ("FinnGen", "FinnGen release 13"),
    "OGS-00027": ("eQTLGen", "eQTLGen 2019 cis-eQTL, whole blood"),
}


BENCH_DIR = Path("/home/gh13047/repo/opengwasdb/docs/benchmark-output")
STORES_REPO = Path("/home/gh13047/repo/opengwasdb-stores")
STORE_ROOT = Path("/data/opengwasdb/stores")
SHAPES = ["phewas", "tophits", "hm3", "regional", "random_lookup_10_variants_100_analyses", "bulk"]

# Query timings: only benchmarks measured on the *published, imputed* release.
# Variant labels are hand-mapped from the benchmark's GRCh38 ALID (gap: no rsid recorded).
DEMO = [
    # (store, name, file, how to find the store's record in that file, variant, locus)
    ("OGS-00009", "UK Biobank (ukb-b)", "opengwasdb_ogs00009_vs_ogs00010_queries.json", "stores[new]",
     "rs7412 (APOE)", "APOE"),
    ("OGS-00011", "GWAS Catalog, European", "opengwasdb_ogs00011_hybrid_benchmark.json", "top",
     "rs7903146 (TCF7L2)", "TCF7L2"),
]
# Size: source bytes per Store (gap: the catalogue should carry these), store bytes measured on disk.
SIZE = [
    ("OGS-00017", "FinnGen R13", ("bench", "opengwasdb_ogs00016_finngen_benchmark_0_2_0.json")),
    ("OGS-00011", "GWAS Catalog, European", ("bench", "opengwasdb_ogs00011_hybrid_benchmark.json")),
    ("OGS-00009", "UK Biobank (ukb-b)", ("inventory", "resources/inventories/ukb-b-restored-2026-10-11.tsv")),
]
SPARSE = ("OGS-00027", "eQTLGen cis-eQTL", "opengwasdb_eqtlgen_ragged_benchmark.json")


def du_bytes(path):
    return int(subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, check=True).stdout.split()[0])


def source_bytes(kind, ref):
    if kind == "bench":
        st = json.loads((BENCH_DIR / ref).read_text())["storage"]
        return st.get("source_bytes") or st.get("raw_vcf_bytes")
    tsv = subprocess.run(["git", "-C", str(STORES_REPO), "show", f"origin/main:{ref}"],
                         capture_output=True, text=True, check=True).stdout
    rows = list(csv.DictReader(io.StringIO(tsv), delimiter="\t"))
    return sum(int(r["data_bytes"]) for r in rows)


def benchmarks():
    demo = []
    for sid, name, fname, where, variant, locus in DEMO:
        b = json.loads((BENCH_DIR / fname).read_text())
        rec = b["stores"][0] if where == "stores[new]" else b
        assert rec.get("label", "new") == "new"
        ds = rec["dataset"]
        assert ds["completion_state"] == "reference_completed", sid
        timings = {t["query"]: {"ms": t["median_ms"], "n": t["result_count"]} for t in rec["timings"]}
        hm3 = rec["hm3_extract"]
        timings["hm3"] = {"ms": hm3["median_ms"], "n": hm3["result_count"], "subset": hm3["subset_n_variants"]}
        demo.append({
            "id": sid, "name": name, "variant": variant, "locus": locus,
            "n_variants": ds["n_variants"], "n_analyses": ds["n_analyses"],
            "layout": "hybrid" if "n_panel_variants" in ds else "dense",
            "measured_at": b["measured_at"][:10], "commit": b.get("commit"),
            "report": fname.replace("_queries", "").replace(".json", ".html"),
            "timings": {k: timings[k] for k in SHAPES},
        })
    size = []
    for sid, name, (kind, ref) in SIZE:
        src, st = source_bytes(kind, ref), du_bytes(STORE_ROOT / sid / "store.opengwasdb")
        size.append({"id": sid, "name": name, "source_bytes": src, "store_bytes": st, "ratio": round(src / st, 2)})
    sid, name, fname = SPARSE
    sparse = {"id": sid, "name": name,
              "source_bytes": json.loads((BENCH_DIR / fname).read_text())["storage"]["source_bytes"],
              "store_bytes": du_bytes(STORE_ROOT / sid / "store.opengwasdb")}
    return {"demo": demo, "size": size, "sparse_example": sparse}


def ro(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def main():
    current = (CATALOG / "current").resolve()
    db = ro(current / "catalog.sqlite")
    q = lambda sql: db.execute(sql).fetchall()  # noqa: E731
    meta = dict(q("select key, value from catalog_meta"))
    stores = [
        dict(zip(["id", "label", "layout", "completion", "coverage", "n", "validated_at"], r))
        for r in q(
            "select store_id, label, layout, completion_state, association_coverage, n_analyses, validated_at "
            "from stores order by store_id"
        )
    ]
    for s in stores:
        s["source"], s["title"] = STORE_META.get(s["id"], ("Unknown source", s["label"]))
    counts = {}
    for kind, key, n in q("select dimension, value, n_analyses from counts"):
        counts.setdefault(kind, {})[key or "unassigned"] = n
    total = q("select count(*) from listed_analyses")[0][0]
    mapped = q("select count(*), count(distinct trait_ontology_id) from listed_analyses where trait_ontology_id <> ''")[0]

    # News: one entry per catalogue version, from its changes.tsv (or listing, for the first).
    changes = []
    for vdir in (CATALOG / "versions").iterdir():
        report = (vdir / "report.md").read_text()
        built = next(line for line in report.splitlines() if line.startswith("Built "))[6:25]
        added, changed, removed = {}, {}, {}
        ct = vdir / "changes.tsv"
        first = not ct.exists()
        if first:
            vdb = ro(vdir / "catalog.sqlite")
            for sid, n in vdb.execute("select store_id, count(*) from listed_analyses group by 1"):
                added[sid] = n
        else:
            for line in ct.read_text().splitlines()[1:]:
                aid, kind = line.split("\t")[:2]
                bucket = {"added": added, "changed": changed, "removed": removed}[kind]
                sid = aid.split(":")[0]
                bucket[sid] = bucket.get(sid, 0) + 1
        changes.append({"version": vdir.name, "date": built, "first": first,
                        "added": added, "changed": changed, "removed": removed})
    changes.sort(key=lambda c: c["date"], reverse=True)

    out = {
        "catalog": {"version": meta["version"], "built_at": meta["built_at"][:10]},
        "totals": {
            "analyses": total,
            "stores": len(stores),
            "sources": len({s["source"] for s in stores}),
            "completed_stores": sum(s["completion"] == "reference_completed" for s in stores),
            "completed_analyses": sum(s["n"] for s in stores if s["completion"] == "reference_completed"),
            "ontology_mapped": mapped[0],
            "ontology_terms": mapped[1],
        },
        "counts": counts,
        "stores": stores,
        "changes": changes,
        "store_meta": {k: {"source": v[0], "title": v[1]} for k, v in STORE_META.items()},
        "benchmarks": benchmarks(),
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT} (catalogue {meta['version']}, {total} analyses)")


if __name__ == "__main__":
    main()
