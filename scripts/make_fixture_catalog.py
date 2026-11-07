"""Rebuild tests/fixtures/catalog: a small copy of the Analysis Catalog for tests and CI.

GitHub's machines can't see the real catalogue, which lives on the OpenGWAS
server, so the tests build the site from this copy instead. It keeps two
versions (a first one, which has no changes.tsv, and the current one), every
listed Store, and a few Analyses from each. The catalogue keeps only its last
five versions, so once its first version is gone, the oldest one it keeps
stands in for it, without its changes.tsv. Runs on the server only:

    pixi run make-fixture [--catalog /data/opengwasdb/stores/catalog] [--per-store 4]
"""
import argparse
import shutil
import sqlite3
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "catalog"


def trim(src: Path, dest: Path, keep: set[str]) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{src}?mode=ro", uri=True) as s, sqlite3.connect(dest) as d:
        s.backup(d)
    d = sqlite3.connect(dest)
    d.execute("create temp table keep (id text primary key)")
    d.executemany("insert into keep values (?)", [(k,) for k in keep])
    d.execute("delete from analyses where id not in (select id from keep)")
    d.execute("insert into analysis_search(analysis_search) values ('rebuild')")
    # As the catalogue build leaves it (opengwasdb-stores ADR 0041): one search segment.
    d.execute("insert into analysis_search(analysis_search) values ('optimize')")
    d.commit()
    d.execute("vacuum")
    d.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", type=Path, default=Path("/data/opengwasdb/stores/catalog"))
    ap.add_argument("--per-store", type=int, default=4)
    args = ap.parse_args()

    current = (args.catalog / "current").resolve()
    versions = sorted((args.catalog / "versions").iterdir(), key=lambda v: v.stat().st_mtime)
    first = next((v for v in versions if not (v / "changes.tsv").exists()), versions[0])
    with sqlite3.connect(f"file:{current / 'catalog.sqlite'}?mode=ro", uri=True) as db:
        keep = {r[0] for r in db.execute(
            """select id from (select id, row_number() over (partition by store_id order by id) as k
                               from listed_analyses) where k <= ?""", (args.per_store,))}

    shutil.rmtree(OUT, ignore_errors=True)
    for v in {first, current}:
        trim(v / "catalog.sqlite", OUT / "versions" / v.name / "catalog.sqlite", keep)
        if v != first and (v / "changes.tsv").exists():
            lines = (v / "changes.tsv").read_text().splitlines()
            kept = [lines[0]] + [ln for ln in lines[1:] if ln.split("\t")[0] in keep]
            (OUT / "versions" / v.name / "changes.tsv").write_text("\n".join(kept) + "\n")
    (OUT / "current").symlink_to(Path("versions") / current.name)
    print(f"wrote {OUT}: {len(keep)} analyses, versions {first.name} and {current.name}")


if __name__ == "__main__":
    main()
