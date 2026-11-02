# PROTOTYPE: home page variants (throwaway)

**Question:** what should the new opengwas.io home page look like?

Four variants share one header, transition notice and footer. D is the
current direction and the default.

| Variant | Leads with | Bets that visitors mostly want to… |
|---|---|---|
| `D` The architecture | "An engine for GWAS summary data": a store drawn as a variants × analyses table that tours six query shapes (including HapMap3) with timings measured on the published imputed releases; then imputation, size against source, and ways to use it | understand why the new stores are better |
| `A` Search first | A catalogue search box, with the counts in its placeholder | look something up |
| `B` How it works | The four real steps: collect, harmonise, complete, release | understand what OpenGWAS is |
| `C` Catalogue ledger | A bar of every Store Release, sized by Analyses and coloured by source, plus the change log | see what is in it, faithfully |

Every number comes from the live Analysis Catalog or from the `opengwasdb` benchmark reports (D's timings and sizes). `build_summary.py` reads it
read-only and writes `summary.json`, standing in for the small summary file the
catalogue build should one day emit (see `docs/site-structure.md`). Source names
and Store titles are hand-mapped in `build_summary.py`, because the catalogue
does not carry them yet.

## Run

```sh
python3 prototype/home/serve.py          # http://localhost:8765/ (variant D)
```

Switch variants with the bar at the bottom or the ← and → keys. On a remote
host, forward the port: `ssh -L 8765:localhost:8765 <host>`.

## Verdict (2026-11-02)

**Variant D won.** The home page sells what the new stores make possible
(imputed with flags, about a tenth of the source size, fast in every query
direction, usable from many tools) rather than describing the catalogue. A's
commercial-use wording is kept; C's overview moves to `/data/` and `/about/`;
B's four steps move to `/about/`. The reasons and the rules the real build must
follow are decision 11 in `docs/decisions.md`.

This branch (`prototype/home-variants`) keeps the prototype for reference. It
is not merged: rebuild D properly in the real site; don't promote this code.
`summary.json` is committed as the snapshot the prototype showed, because
`build_summary.py` reads paths that exist only on the OpenGWAS server.
