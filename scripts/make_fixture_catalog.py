"""Rebuild tests/fixtures/catalog: a small copy of the Analysis Catalog for tests and CI.

GitHub's machines can't see the real catalogue, which lives on the OpenGWAS
server, so the tests build the site from this copy instead. It keeps two
versions (a first one, which has no changes.tsv, and the current one), every
listed Store, and a few Analyses from each. The catalogue keeps only its last
five versions, so once its first version is gone, the oldest one it keeps
stands in for it, without its changes.tsv. Runs on the server only:

    pixi run make-fixture [--catalog /data/opengwasdb/stores/catalog] [--per-store 4]
                          [--ld-catalog PATH] [--ld-only]

The published catalogue may not have the `ld_resources` table yet. `--ld-catalog`
names a catalogue root that does (build one into a scratch root with
`OPENGWASDB_ARTIFACT_ROOT=<scratch> pixi run catalog` in opengwasdb-stores); its
current version's rows are copied, all of them, into every fixture version. The
table is copied from `--catalog` when that has it and `--ld-catalog` is not given.
`--ld-only` leaves the fixture's Analyses and versions as they are and only
replaces the `ld_resources` table in each of its versions.
"""
import argparse
import shutil
import sqlite3
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "catalog"


def copy_ld_resources(src: Path, dest: Path) -> None:
    """Give the database at `dest` the `ld_resources` table of the one at `src`, schema and rows."""
    with sqlite3.connect(f"file:{src}?mode=ro", uri=True) as s:
        schema = s.execute("select sql from sqlite_master where type = 'table' and name = 'ld_resources'").fetchone()
        if schema is None:
            raise SystemExit(f"no ld_resources table in {src}: point --ld-catalog at a catalogue that has one")
        rows = s.execute("select * from ld_resources").fetchall()
    if not rows:
        raise SystemExit(f"the ld_resources table in {src} has no rows")
    d = sqlite3.connect(dest)
    d.execute("drop table if exists ld_resources")
    d.execute(schema[0])
    d.executemany(f"insert into ld_resources values ({','.join('?' * len(rows[0]))})", rows)
    d.commit()
    d.close()


def trim(src: Path, dest: Path, keep: set[str], ld_source: Path) -> None:
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
    d.close()
    copy_ld_resources(ld_source, dest)
    d = sqlite3.connect(dest)
    d.execute("vacuum")
    d.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", type=Path, help="default /data/opengwasdb/stores/catalog")
    ap.add_argument("--per-store", type=int, help="default 4")
    ap.add_argument("--ld-only", action="store_true", help="only replace ld_resources in the existing fixture")
    ap.add_argument("--ld-catalog", type=Path, help="a catalogue root whose current version has ld_resources")
    args = ap.parse_args()
    if args.ld_only:
        if not args.ld_catalog:
            ap.error("--ld-only needs --ld-catalog")
        given = [f for f, v in (("--catalog", args.catalog), ("--per-store", args.per_store)) if v is not None]
        if given:
            ap.error(f"--ld-only keeps the fixture's Analyses and versions, so it does not take {' or '.join(given)}")

    if args.ld_only:
        source = (args.ld_catalog / "current").resolve() / "catalog.sqlite"
        for db in sorted(OUT.glob("versions/*/catalog.sqlite")):
            copy_ld_resources(source, db)
            with sqlite3.connect(db) as d:
                d.execute("vacuum")
            print(f"wrote ld_resources to {db}")
        return

    args.catalog = args.catalog or Path("/data/opengwasdb/stores/catalog")
    args.per_store = 4 if args.per_store is None else args.per_store
    current = (args.catalog / "current").resolve()
    versions = sorted((args.catalog / "versions").iterdir(), key=lambda v: v.stat().st_mtime)
    first = next((v for v in versions if not (v / "changes.tsv").exists()), versions[0])
    with sqlite3.connect(f"file:{current / 'catalog.sqlite'}?mode=ro", uri=True) as db:
        keep = {r[0] for r in db.execute(
            """select id from (select id, row_number() over (partition by store_id order by id) as k
                               from listed_analyses) where k <= ?""", (args.per_store,))}

    ld_source = (args.ld_catalog / "current").resolve() / "catalog.sqlite" if args.ld_catalog else None
    shutil.rmtree(OUT, ignore_errors=True)
    for v in {first, current}:
        trim(v / "catalog.sqlite", OUT / "versions" / v.name / "catalog.sqlite", keep,
             ld_source or (current / "catalog.sqlite"))
        if v != first and (v / "changes.tsv").exists():
            lines = (v / "changes.tsv").read_text().splitlines()
            kept = [lines[0]] + [ln for ln in lines[1:] if ln.split("\t")[0] in keep]
            (OUT / "versions" / v.name / "changes.tsv").write_text("\n".join(kept) + "\n")
    (OUT / "current").symlink_to(Path("versions") / current.name)
    print(f"wrote {OUT}: {len(keep)} analyses, versions {first.name} and {current.name}")


if __name__ == "__main__":
    main()
