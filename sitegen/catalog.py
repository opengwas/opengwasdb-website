"""Read-only access to the Analysis Catalog.

The catalogue root holds one directory per version and a `current` link:

    <root>/current -> versions/<version>
    <root>/versions/<version>/catalog.sqlite
    <root>/versions/<version>/changes.tsv   (absent for the first version)

Only listed Analyses and the Store Releases that hold them are exposed.
"""
import sqlite3
from pathlib import Path


def _open(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


class Catalog:
    def __init__(self, root: Path):
        self.root = Path(root)
        current = self.root / "current"
        if not current.exists():
            raise FileNotFoundError(f"no Analysis Catalog at {self.root} (expected {current})")
        self.dir = current.resolve()
        self.db = _open(self.dir / "catalog.sqlite")

    def _rows(self, sql: str, *args) -> list[dict]:
        return [dict(r) for r in self.db.execute(sql, args)]

    def meta(self) -> dict:
        m = {r["key"]: r["value"] for r in self._rows("select key, value from catalog_meta")}
        return {"version": m["version"], "built_at": m["built_at"]}

    def stores(self) -> list[dict]:
        """Listed Store Releases, with their Analysis counts taken from the listing itself."""
        return self._rows(
            """select s.store_id as id, s.label, s.layout, s.completion_state, s.association_coverage,
                      s.reference_assembly, s.n_variants, s.n_associations, s.store_bytes,
                      s.format_version, s.source_snapshot_id, s.validated_at, count(a.id) as n_analyses
               from stores s join listed_analyses a using (store_id)
               group by s.store_id order by s.store_id""")

    def totals(self) -> dict:
        r = self._rows(
            """select count(*) as analyses,
                      count(distinct a.store_id) as stores,
                      sum(s.association_coverage = 'gwas') as genome_wide,
                      sum(s.association_coverage = 'gwas' and s.completion_state = 'reference_completed') as imputed
               from listed_analyses a join stores s using (store_id)""")[0]
        return {k: r[k] or 0 for k in r}

    def ancestry(self, store_id: str | None = None) -> list[dict]:
        where, args = ("where store_id = ?", (store_id,)) if store_id else ("", ())
        return self._rows(
            f"""select coalesce(ancestry_category, 'unassigned') as code, count(*) as n
                from listed_analyses {where} group by 1 order by n desc""", *args)

    def licences(self, store_id: str) -> list[dict]:
        return self._rows(
            """select license as licence, count(*) as n from listed_analyses
               where store_id = ? group by 1 order by n desc""", store_id)

    def analyses(self, store_id: str | None = None, limit: int | None = None) -> list[dict]:
        where, args = ("where store_id = ?", [store_id]) if store_id else ("", [])
        order = "order by analysis_label collate nocase, id" if store_id else "order by id"
        lim = f"limit {int(limit)}" if limit else ""
        return self._rows(f"select * from listed_analyses {where} {order} {lim}", *args)

    def versions(self) -> list[dict]:
        """Every catalogue version, newest first, with what it added, changed and removed per Store."""
        out = []
        for vdir in sorted((self.root / "versions").iterdir()):
            if not (vdir / "catalog.sqlite").exists():
                continue
            vdb = _open(vdir / "catalog.sqlite")
            meta = dict(vdb.execute("select key, value from catalog_meta").fetchall())
            changes = {"added": {}, "changed": {}, "removed": {}}
            first = not (vdir / "changes.tsv").exists()
            if first:
                for sid, n in vdb.execute("select store_id, count(*) from listed_analyses group by 1"):
                    changes["added"][sid] = n
            else:
                for line in (vdir / "changes.tsv").read_text().splitlines()[1:]:
                    analysis, kind = line.split("\t")[:2]
                    bucket = changes[kind]
                    sid = analysis.split(":")[0]
                    bucket[sid] = bucket.get(sid, 0) + 1
            vdb.close()
            out.append({"version": meta["version"], "built_at": meta["built_at"], "first": first, **changes})
        return sorted(out, key=lambda v: v["built_at"], reverse=True)
