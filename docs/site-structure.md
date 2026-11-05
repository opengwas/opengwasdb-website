# Site structure (draft)

A proposed sitemap, navigation and per-page content for the new `opengwas.io`.
It follows [`decisions.md`](decisions.md). The home page was explored as a
throwaway prototype, kept unmerged on the branch `prototype/home-variants`
(folder `prototype/home/`). How the site is built and edited is in
[`../CONTRIBUTING.md`](../CONTRIBUTING.md) (decision 12).

## Who the site is for

| Visitor | What they came to do |
|---|---|
| Researcher | Find Analyses for a trait or gene, get them into R or Python, and cite them |
| Legacy user | Understand what changed, and where their old workflow and IDs went |
| Commercial evaluator | Decide whether they need a licence, what it covers, and how to buy one |
| Funder or collaborator | Understand what OpenGWAS is, who runs it, and whether it is used |

## Sitemap and URLs

```text
/                                   Home
/data/                              Browse the Analysis Catalog: search plus table
/data/stores/                       All Store Releases
/data/stores/OGS-00009/             One Store Release: summary, provenance, licence, download
/data/analyses/OGS-00009/ukb-b-10001/   One Analysis (pre-rendered for search engines and citation)
/tools/                             Tools that work with OpenGWAS data
/news/                              Data updates (generated) and written posts
/news/<yyyy-mm-dd>-<slug>/          One post
/licensing/                         Free versus commercial use; what a licence covers; how to buy
/transition/                        What's changed from legacy OpenGWAS; grace period; archive docs
/about/                             What OpenGWAS is, team, funders, how to cite, development site
/legal/terms/                       EULA (versioned, dated)
/legal/service-description/         Service Description (versioned, dated)
/legal/privacy/                     Privacy Notice (versioned, dated)
/legal/accessibility/               Accessibility statement
/datasets/*                         Legacy-ID 404, pointing to /transition/ (decision 8)
platform.opengwas.io                External: middleware and API (on hold, decision 1)
blog.opengwas.io/*                  Redirects to /news/ (decision 10)
```

New Analysis pages live under `/data/analyses/`, never under `/datasets/`, so
the legacy 404 can never shadow a real page.

## Navigation

```text
[logo]          Data   Tools   News   Licensing   About   Platform (soon)
```

- "Data" is the noun visitors expect. Inside, the page and its headings use the
  store vocabulary: Analysis, Store Release, OGS id.
- "Platform" is a placeholder until `platform.opengwas.io` exists, and then
  becomes an external link.
- During the grace period, a one-line notice sits under the header on every
  page and links to `/transition/`.

The footer contains:

- the catalogue version and its date;
- the legal links;
- the shared contact mailbox (not a personal one);
- links to the status page and GitHub;
- the funders and supporters;
- how to cite.

## Pages

Each page lists its blocks in order, with where the content comes from.
Content comes from three kinds of source:

- **the catalogue**, read from `catalog.sqlite` in the browser or at build time;
- **numbers worked out from the catalogue at build time** and written into the
  pages, so no page needs the SQL engine just to show a count;
- **hand-written** Markdown or YAML.

### Home `/`

Approved: prototype variant D, "the architecture" (decision 11, 2026-11-02).
The page leads with what the new stores make possible.

1. **The hero:** the headline "An engine for GWAS summary data", one sentence
   saying OpenGWAS harmonises, *imputes* and stores, and four value points:
   - imputed, with every imputed value flagged;
   - about a tenth of the size of the source files;
   - milliseconds for a PheWAS, seconds for a whole region;
   - usable from a laptop, a cluster or your analysis tools.
2. **Query demo:** the store drawn as a variants × analyses table.
   - The six query shapes are PheWAS, top hits, HapMap3 extraction, region,
     random lookup and whole analysis.
   - It cycles through the shapes on its own. Each slice fills in the order
     the query reads it. A Pause control is provided, and hovering pauses it.
   - Choosing a query stops the tour. With reduced motion set, it doesn't
     start.
   - It shows timings **only from benchmarks measured on the published,
     imputed release.**
3. **Imputed, and marked as imputed:**
   - what completion does, and that imputed values are flagged and can be
     excluded;
   - the live count of imputed versus genome-wide Analyses, from the
     catalogue;
   - a one-analysis before-and-after graphic.
4. **Size:** source files versus the published imputed store, per genome-wide
   Store, stated honestly. Sparse QTL data does not shrink.
5. **Ways to use it**, each with its true status: local (CLI or Python), the
   platform (on hold), and analysis tools (in progress).
6. **Browse the catalogue** and **Commercial use**, using the variant A
   wording.
7. **Data updates:** the last three, plus one line of current catalogue
   counts, from the catalogue.
8. **Transition notice** during the grace period.

The catalogue-composition view (prototype variant C: a bar of Stores by source,
a Store table, an ancestry breakdown, the change log) moves to the top of
`/data/`, with a short version on `/about/`. Variant B's four-step "how it
works" goes to `/about/`.

### Data `/data/`

Built (decision 13).

- **Search and table:**
  - The page is full width, up to 1,800 px, so the table has room for a
    column per filter.
  - One search box above the table: full-text search (FTS5
    `analysis_search`).
  - A filter under each column's name: Store release, ancestry, trait,
    outcome and tissue. Each filter option shows how many analyses it would
    leave.
  - Sorted by best match, sample size (the default) or name. Clicking the
    Analysis or Sample size heading sorts by it, one way only: the way its
    index reads. 25 per page, with the request kept in the address so it can
    be shared.
  - Runs over `catalog.sqlite` in the browser through HTTP range requests
    (decision 7), with plain JavaScript rather than DataTables.
  - The first page is in the HTML, so the page shows results before, or
    without, JavaScript.
  - On a phone or an upright tablet the table becomes result cards, and its
    header becomes sort buttons and a grid of filters.
- **Then:** the Store table, downloads, and the ancestry breakdown.
- **Download:**
  - Every catalogue version's `catalog.sqlite`, `analyses.tsv.gz`,
    `stores.tsv` and `changes.tsv`, at `/data/catalog/<version>/`, with
    SHA-256 checksums.
  - `/data/catalog/current.json` names the current version, for scripts.
- **Not yet:**
  - the licence filter, which waits for the licence fields to be filled in;
  - the variant C bar of Stores by source.

### Store Release `/data/stores/<OGS-id>/`

Identity, source, layout, completion state, Analysis count, validation date,
source snapshot, licence(s), how to download, and how to cite. This page is
the "receipt" that provenance-minded users want. Source: the catalogue
`stores` table plus the release metadata.

### Analysis `/data/analyses/<OGS-id>/<analysis_id>/`

The trait label and ontology, ancestry, sample size and cases, effect scale,
licence (linking to the provider's terms, not a paraphrase), DOI or PMID,
consortium, first author, and which Store holds it. Pre-rendered at build time
from `catalog.sqlite`, about 35k pages.

### Tools `/tools/`

One entry per tool: what it does, a link, and its status on the new data and
the legacy service. Candidates are TwoSampleMR, ieugwasr, ieugwaspy,
gwasglue2, GPMap and the `opengwasdb` CLI. Source: a hand-written
`tools.yaml`.

### News `/news/`

Two streams in one list:

- generated data updates, one per catalogue version, from `changes.tsv` and
  the report;
- written posts (Markdown), for releases, papers and terms changes.

Provides an RSS or Atom feed.

### Licensing `/licensing/`

1. "Do I need a licence?": a decision box.
2. Free non-commercial use.
3. The commercial licence: access for the licence's duration; keep what you
   obtained, within the source providers' terms (decision 3).
4. What a licence includes, and prices or price bands if published.
5. The procurement pack: terms, a security and logging summary, invoicing
   details.
6. A contact form to the shared mailbox.

### Transition `/transition/`

Legacy versus new, covering data model, IDs, genome build, access, tools, why
the numbers differ, the grace-period dates, and where the archived data and its
documentation live. Legacy ID mapping is the tools' job (decision 4), so this
page links to them.

### About `/about/`

What OpenGWAS is and why; the team; funders and supporters (the commercial
supporters explained); how to cite (the forthcoming paper, plus BibTeX); and a
link to the development and transparency site, which is moving to `github.io`
(decision 10).

### Legal `/legal/*`

Carried over from `docs/current-site/snapshots/` until rewritten. Each page
has a version, an effective date and links to its previous versions.

## Data the build consumes

| Input | Producer | Used by |
|---|---|---|
| `catalog.sqlite`, at an immutable versioned URL | `opengwasdb-stores` `pixi run catalog` | Data search (browser); Analysis and Store pages (build) |
| `current` pointer: version id plus URL | The catalogue publish step | Every page that reads the catalogue |
| Benchmark record per Store: source and store bytes, median query times per shape, date, commit, the build it was measured on | `opengwasdb` benchmark reports (today ad hoc, in `docs/benchmark-output/`), collected into `data/benchmarks.json` on the server | Home query demo and size comparison; Store pages |
| Markdown posts and pages; `tools.yaml` | Hand-written in this repo | News, about, licensing, transition, tools |

## Catalogue gaps found while sketching

These are in addition to decision 6's list (associations, Store sizes,
assembly, MVP and eQTLGen licences).

- **Source provider display name per Store.** No column exists, and
  `consortium` is blank for 7 of 10 Stores. The prototype hand-maps it.
- **A human-readable title per Store.** `description` is written for
  developers, for example "the frozen 1669-Analysis input manifest accepted
  for ow…". The prototype hand-maps titles.
- **The first catalogue version has no `changes.tsv`.** The news generator has
  to read that version's listing instead.
- **Benchmarks are not consistently tied to the published releases.** The home
  demo uses only published-release benchmarks:
  - OGS-00009-completed, measured 2026-10-24
    (`opengwasdb_ogs00009_vs_ogs00010_queries.json`).
  - OGS-00011-completed, measured 2026-11-01.
  - **FinnGen (OGS-00017-completed) has none.** Its only benchmark is the
    earlier observed-only build, made before its id moved from OGS-00016, so it
    is left out of the demo.
  
  The site needs one benchmark record per published Store Release, including
  the HapMap3 extraction, re-run whenever a Store is rebuilt.
- **Earlier size figures were from builds that were not imputed.** The
  published imputed stores, measured on disk on 2026-11-02:

  | Store | Source files | Imputed store | Times smaller |
  |---|---:|---:|---:|
  | FinnGen | 2,160.7 GB | 139.1 GB | 15.5 |
  | GWAS Catalog EUR | 1,511.7 GB | 166.6 GB | 9.1 |
  | UK Biobank | 425.4 GB (2,514 VCFs, from the source inventory) | 61.9 GB | 6.9 |
  | **Total** | **4.1 TB** | **368 GB** | **about 11** |

  The observed-only eQTLGen store is *larger* than its source: 2.6 GB against
  2.4 GB.
- **Source size per Store** (bytes of the source files) belongs in the
  catalogue next to `store_bytes`, so the size comparison can cover every
  Store. Today it is assembled from benchmark JSON and, for UK Biobank, the
  source inventory.
- **No rsid on benchmark variants.** The prototype hand-maps the GRCh38 ALIDs:
  `10:112998590:C:T` is rs7903146 (TCF7L2), and `19:44908822:C:T` is rs7412
  (APOE).

## Before launch

Found while building the skeleton. Each is something the site says, or needs,
that isn't true or available yet.

- **The catalogue should be built for browsing** (decision 13). That means two
  covering indexes, 32 KB pages and an optimised search index. Filtered and
  sorted views then fetch kilobytes rather than about 10 MB, and every action
  takes about half the time. This is a change to the catalogue build in
  `opengwasdb-stores`; the statements are in
  `scripts/catalogue_browse_indexes.sql`. The site already uses them when
  they are there.
- **The server must serve the catalogue files for range requests** (decision
  13). That means `Accept-Ranges: bytes`, no gzip on `.sqlite`, and
  `application/wasm` for the `.wasm` file. Check with a real request after
  deployment.
- **"Available now" for local use** needs a pip or conda release of
  `opengwasdb` and a way to download a store (decision 11).
- **The benchmark reports have no public address**, so the demo's fine print
  can't link to them.
- **Every FinnGen Analysis is "Not yet assigned" an ancestry** in the
  catalogue, so the FinnGen Store page says so.
- **Tool statuses marked "To be confirmed"** in `data/tools.yaml`: ieugwaspy
  with the new stores, and gwasglue2 and the Genotype-Phenotype Map with the
  legacy API.

## Not decided

- **Dark mode.** The logo PNG has black text on a transparent background, so
  dark mode needs a light-text variant of the logo.
