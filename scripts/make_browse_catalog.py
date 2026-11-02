"""Interim: make a copy of the Analysis Catalog built for browsing, for the hosted site.

Until the catalogue build adds them itself (opengwas/opengwasdb-stores#424), this
writes a copy of the catalogue root whose current version's SQLite has:
- the covering indexes in scripts/catalogue_browse_indexes.sql;
- 32 KB pages;
- an optimised FTS5 index (decision 13).

Older versions are linked, not copied. The real catalogue is only read.

    python scripts/make_browse_catalog.py SOURCE_ROOT DEST_ROOT

The copy's catalog.sqlite differs from the real one, so its checksum does too.
Use it for development hosting only. Remove this script once the real catalogue
is built this way.
"""
import shutil
import sqlite3
import sys
from pathlib import Path

INDEXES = Path(__file__).resolve().parent / "catalogue_browse_indexes.sql"


def main(src_root: Path, dest_root: Path) -> None:
    current = (src_root / "current").resolve()
    tmp = dest_root.with_name(dest_root.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "versions").mkdir(parents=True)
    for v in (src_root / "versions").iterdir():
        if v.name != current.name:
            (tmp / "versions" / v.name).symlink_to(v.resolve())
    dest = tmp / "versions" / current.name
    dest.mkdir()
    for f in current.iterdir():
        if f.name != "catalog.sqlite" and f.is_file():
            shutil.copy2(f, dest / f.name)
    (tmp / "current").symlink_to(Path("versions") / current.name)

    src = sqlite3.connect(f"file:{current / 'catalog.sqlite'}?mode=ro", uri=True)
    db = sqlite3.connect(dest / "catalog.sqlite")
    src.backup(db)
    src.close()
    db.execute("pragma page_size = 32768")
    db.executescript(INDEXES.read_text())
    db.execute("insert into analysis_search(analysis_search) values ('optimize')")
    db.commit()
    db.execute("vacuum")
    ok = db.execute("pragma quick_check").fetchone()[0]
    db.close()
    if ok != "ok":
        raise SystemExit(f"quick_check failed on the browse copy: {ok}")

    old = dest_root.with_name(dest_root.name + ".old")
    shutil.rmtree(old, ignore_errors=True)
    if dest_root.exists():
        dest_root.rename(old)
    tmp.rename(dest_root)
    shutil.rmtree(old, ignore_errors=True)
    print(f"wrote {dest_root} for catalogue version {current.name}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
