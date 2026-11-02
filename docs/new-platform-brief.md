# The new platform as a website visitor will meet it

A snapshot taken 2026-11-02 from `opengwasdb` and `opengwasdb-stores`
(`origin/main`), and from the built Analysis Catalog at
`/data/opengwasdb/stores/catalog/current`. That catalogue is version
`9df14f8dc3cceabf`, built 2026-11-01. Use it to decide what the redesigned site
can truthfully say. It complements
[`current-site/inventory.md`](current-site/inventory.md), which records what the
old site says.

## What OpenGWAS is becoming

The roadmap is `opengwasdb/docs/opengwas-roadmap.md`. OpenGWAS is moving from a
cloud-hosted archive behind one API to a family of **immutable, versioned Store
Releases**. Each release:

- is self-contained (SQLite metadata plus Zarr arrays);
- can be queried locally, on HPC, or behind a thin service;
- is built once and queried many times;
- has a declared reference panel, and is optionally **Reference-Completed**,
  with imputed associations kept distinguishable from observed ones;
- carries per-Analysis Attribution Metadata: licence, DOI or PMID, consortium
  and first author.

The roadmap gives the motivation plainly: ~20 TB of VCFs plus derived formats
made the old model "economically and operationally fragile". On cost recovery
it says only that the value proposition "needs to be refined" (`:183-186`).

## What exists versus what is planned

| Visitor-facing capability | State |
|---|---|
| Python library and CLI on a local Store: PheWAS, region PheWAS, lookup, top hits, full-analysis extraction | **Built.** Works on one Store at a time |
| Install | Git checkout plus Pixi, or `pip install -e`; Python ≥3.12. **No PyPI or conda release** |
| Analysis Catalog (SQLite, TSV, `analyses.tsv.gz`, a change log) | **Built**, on the host only. No public URL |
| Downloading or mirroring Stores | A principle only. No mechanism yet |
| Remote REST API, cross-store routing, auth, quotas, billing, audit logging | **Planned** (Horizon 4, the "Interface" workstream). Not started in these repos |
| ieugwasr, ieugwaspy, TwoSampleMR and gwasglue on the new backend | The "Tool integration" workstream. Not started |
| Developer status site | Live at `blog.opengwas.io/opengwasdb-stores/` (Quarto, published from `gh-pages`) |
| Publication | Nothing in either repo yet |
| Store format | Pre-release. `format_version` 0.2.0; "not yet stable" |

## Headline numbers available today

These come from `catalog.sqlite`, using the `listed_analyses` view and the
`stores` and `counts` tables.

| Measure | Value |
|---|---|
| Listed Store Releases | 10 (of 22 registered: 9 trials, 3 built but not yet validated) |
| Listed Analyses | **35,109** |
| By Assigned Ancestry | EUR 28,002 · META 1,691 · AFR 1,368 · AMR 850 · EAS 241 · unassigned 2,957 |
| Molecular / phenotype | 20,650 / 14,459 |
| Continuous / binary | 24,535 / 10,574 |
| Reference-Completed / Observed-Only Stores | 5 (11,159 Analyses) / 5 (23,950) |
| Analyses with a Trait Ontology term | 4,568 (2,180 distinct terms) |
| Associations | **Unknown.** Only 2 of 10 Stores report `n_associations`, totalling 185.2M |
| Store size on disk | **Unknown.** `store_bytes` is empty for every Store |
| Reference assembly | **Blank** for every Store in the catalogue |

Three cautions for the front page:

1. **35,109 is lower than the "more than 50,000" on today's site.** Several
   legacy batches are not yet rebuilt as Stores, including:
   - Pan-UKB (`ukb-e`);
   - the brain imaging batches (`ubm-a`, `ubm-b`);
   - the pQTL batches (`prot-a`, `prot-b`, `prot-c`);
   - the metabolite batches (`met-a` to `met-d`);
   - Biobank Japan (`bbj-a`);
   - the curated `ieu-a` and `ieu-b` sets.
   
   The site needs to explain why the number changed, or wait until the gap
   closes.
2. Every number the README wants on the front page (associations, stores,
   analyses) must exist as a stored value in the catalogue first. Today the
   association count and store sizes do not.
3. **Licence is blank for 25,272 of the 35,109 listed Analyses (72%).** These
   are all the MVP and eQTLGen rows. The licence filter, which would be the
   site's strongest commercial feature, does not work until this is filled.

## The listed Stores

| Store | Label | Source | Layout | Completion | Analyses |
|---|---|---|---|---|---:|
| OGS-00006 | 2023-chen-full-european | GWAS Catalog (Chen 2023 metabolome) | ragged, signals only | observed-only | 1,400 |
| OGS-00009 | ukb-b-full | Legacy OpenGWAS ukb-b | dense | completed | 2,514 |
| OGS-00011 | eur-hybrid-full | GWAS Catalog, EUR | hybrid | completed | 3,169 |
| OGS-00012 | mvp-phs002453-eur | MVP (dbGaP phs002453) | dense | completed | 1,669 |
| OGS-00013 | mvp-phs002453-afr | MVP | dense | observed-only | 1,368 |
| OGS-00014 | mvp-phs002453-amr | MVP | dense | completed | 1,053 |
| OGS-00015 | mvp-phs002453-eas | MVP | dense | observed-only | 241 |
| OGS-00016 | mvp-phs002453-meta-observed-only | MVP | dense | observed-only | 1,691 |
| OGS-00017 | r13-full | FinnGen R13 | dense | completed | 2,754 |
| OGS-00027 | eqtlgen-full | eQTLGen 2019 cis | ragged, cis | observed-only | 19,250 |

Built but not yet listed: OGS-00024, 00025 and 00026 (Chen AFR, EAS and SAS).

## Sources for a "news" feed

- Each catalogue version's `report.md` has a section "Change since the previous
  version": Analyses added, removed and changed. `changes.tsv` lists every id.
  This is the natural source for "data added" news items.
- Both repos tag every merge. The notes are the `changelog.d/` fragments,
  published as GitHub Releases. `opengwasdb-stores/docs/changelog.qmd` merges
  the two. This suits a developer changelog, not front-page news.

## Vocabulary the new site should adopt

These come from both repos' `CONTEXT.md`.

**Use:**

- Store Release
- the `OGS-xxxxx` Store id
- Analysis id `OGS-xxxxx:<analysis_id>`
- **Analysis** (one statistical analysis of a Trait) versus **Trait**
- Trait Ontology
- Analysis Catalog
- Observed-Only / Reference-Completed
- observed versus imputed association
- Dense / Ragged / Hybrid
- Association Coverage
- Assigned Ancestry
- Access Posture
- Source Provider

**Avoid:**

- "dataset", "study" or "phenotype" when you mean an Analysis. "Phenotype" is
  acceptable only as an explanatory synonym for Trait.
- "database" for a Store Release.
- "catalogue" for the registry. The catalogue code uses the US spelling
  "Analysis Catalog".
- "access control" when you mean Access Posture.
- "full GWAS" when you mean Association Coverage.

Website copy can soften these terms for a lay reader, but the identifiers and
the nouns on dataset pages should match the store schema.

## Implications for the website

- The README's "platform page" describes a service that does not yet exist.
  Decide what it says at launch:
  - (a) the legacy API, still running, plus "the new platform is coming"; or
  - (b) the local-first Stores and CLI only; or
  - (c) wait for the Horizon 4 service.
- The EULA forbids downloading or mirroring the Services (2.1) and bulk
  download (4.3). That conflicts directly with distributing Stores. The terms
  need rewriting before downloads go live, not after.
- Legacy users hold `ieu-a-2`-style IDs in scripts and papers. Only the
  `ukb-b` IDs survive, as Analysis IDs inside OGS-00009. The site needs a
  migration page that maps legacy IDs to new ones, or explains their absence.
