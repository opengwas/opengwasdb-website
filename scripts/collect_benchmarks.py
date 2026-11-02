"""Write data/benchmarks.json: the query timings and sizes the home page shows.

Runs on the OpenGWAS server only, because it reads the opengwasdb benchmark
reports and measures each Store on disk. Re-run it whenever a Store in the
lists below is rebuilt, and commit the result, so the change shows up in
review.

Rules (decision 11 in docs/decisions.md):
- Timings come only from benchmarks measured on the *published, imputed*
  release of a Store. A Store without one is left out of the demo.
- Store bytes are measured on disk; source bytes come from the benchmark
  record or, for UK Biobank, the source inventory.

Catalogue gap: the catalogue should carry source and store bytes, and a
benchmark record per Store, so this script can go away.

    pixi run collect-benchmarks [--bench-dir DIR] [--store-root DIR] [--stores-repo DIR]
"""
import argparse
import csv
import io
import json
import subprocess
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "benchmarks.json"
SHAPES = ["phewas", "tophits", "hm3", "regional", "random_lookup_10_variants_100_analyses", "bulk"]

# Stores in the query demo: (Store, benchmark file, where its record is in that
# file, variant label, locus). Variant labels are hand-mapped from the
# benchmark's GRCh38 ALID, because the benchmark does not record an rsid.
DEMO = [
    ("OGS-00009", "opengwasdb_ogs00009_vs_ogs00010_queries.json", "stores[0]", "rs7412 (APOE)", "APOE"),
    ("OGS-00011", "opengwasdb_ogs00011_hybrid_benchmark.json", "top", "rs7903146 (TCF7L2)", "TCF7L2"),
]
# Stores in the size comparison, and where their source bytes come from.
SIZE = [
    ("OGS-00017", "bench", "opengwasdb_ogs00016_finngen_benchmark_0_2_0.json"),
    ("OGS-00011", "bench", "opengwasdb_ogs00011_hybrid_benchmark.json"),
    ("OGS-00009", "inventory", "resources/inventories/ukb-b-restored-2026-10-11.tsv"),
]
# A sparse Store, to show that already-compact data doesn't shrink.
SPARSE = ("OGS-00027", "opengwasdb_eqtlgen_ragged_benchmark.json")


def du_bytes(path: Path) -> int:
    out = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, check=True).stdout
    return int(out.split()[0])


def source_bytes(kind: str, ref: str, bench_dir: Path, stores_repo: Path) -> int:
    if kind == "bench":
        st = json.loads((bench_dir / ref).read_text())["storage"]
        return st.get("source_bytes") or st["raw_vcf_bytes"]
    tsv = subprocess.run(["git", "-C", str(stores_repo), "show", f"origin/main:{ref}"],
                         capture_output=True, text=True, check=True).stdout
    return sum(int(r["data_bytes"]) for r in csv.DictReader(io.StringIO(tsv), delimiter="\t"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench-dir", type=Path, default=Path.home() / "repo/opengwasdb/docs/benchmark-output")
    ap.add_argument("--store-root", type=Path, default=Path("/data/opengwasdb/stores"))
    ap.add_argument("--stores-repo", type=Path, default=Path.home() / "repo/opengwasdb-stores")
    args = ap.parse_args()

    demo = []
    for store, fname, where, variant, locus in DEMO:
        b = json.loads((args.bench_dir / fname).read_text())
        rec = b["stores"][0] if where == "stores[0]" else b
        ds = rec["dataset"]
        if ds["completion_state"] != "reference_completed":
            raise SystemExit(f"{store}: {fname} was not measured on an imputed release")
        timings = {t["query"]: {"ms": t["median_ms"], "n": t["result_count"]} for t in rec["timings"]}
        hm3 = rec["hm3_extract"]
        timings["hm3"] = {"ms": hm3["median_ms"], "n": hm3["result_count"], "subset": hm3["subset_n_variants"]}
        demo.append({
            "store": store, "variant": variant, "locus": locus,
            "n_variants": ds["n_variants"], "n_analyses": ds["n_analyses"],
            "measured_at": b["measured_at"][:10], "commit": b.get("commit"), "source_file": fname,
            "timings": {k: timings[k] for k in SHAPES},
        })

    today = date.today().isoformat()
    size = []
    for store, kind, ref in SIZE:
        size.append({
            "store": store,
            "source_bytes": source_bytes(kind, ref, args.bench_dir, args.stores_repo),
            "store_bytes": du_bytes(args.store_root / store / "store.opengwasdb"),
            "source_from": ref, "measured_at": today,
        })

    store, fname = SPARSE
    sparse = {
        "store": store,
        "source_bytes": json.loads((args.bench_dir / fname).read_text())["storage"]["source_bytes"],
        "store_bytes": du_bytes(args.store_root / store / "store.opengwasdb"),
        "source_from": fname, "measured_at": today,
    }

    OUT.write_text(json.dumps({"demo": demo, "size": size, "sparse_example": sparse}, indent=1) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
