# Website decisions

These decisions answer the open questions in [`audit.md`](audit.md) §6. Each
entry gives the decision and then what it means for the site.

## 2026-11-02

### Platform and API

- **The platform page is on hold.** It is being built independently and waits
  on the API.
- **Architecture (for reference):**
  - A data-interface API serves queries.
  - It sits behind a middleware API that handles queueing, authentication,
    authorisation, tokens and logging.
  - The middleware is the user-facing entry point, at
    **`platform.opengwas.io`**. This hostname is assumed; the original note
    said "platform.opengwasio.io".
- *Means for this site:*
  - Navigation needs a slot for "Platform" that links out to
    `platform.opengwas.io`.
  - Until the platform launches, that slot reads "coming soon" or is hidden.
  - Nothing on this site documents tokens, quotas or endpoints. That belongs to
    the platform.

### Legal terms

- **The terms will be rewritten for the new model**, which actively encourages
  bulk download as well as API use.
- *Means for this site:*
  - The conflicts noted in the audit go away: EULA 2.1 and 4.3 (no
    downloading or mirroring), 4.1 (limits defined by a page that will
    disappear), and the "cloud-based… API" wording in the Service Description
    and Privacy Notice.
  - Until the new text exists, carry the current documents across from
    `current-site/snapshots/`, marked with their effective date.
  - Give every legal page a version and an effective date.

### Catalogue numbers

- **The catalogue is updated periodically and has no target size.** The site
  must reflect it faithfully.
- *Means for this site:*
  - Every number the site shows comes from the published catalogue at build or
    view time. No number is hand-typed.
  - The news feed comes from each catalogue version's "Change since the
    previous version" section and `changes.tsv`.

### 1. Platform page

Hold it (see "Platform and API" above).

### 2. Continuity with the legacy service

- **The legacy service and the new one run in parallel for a while.** The new
  site points to the new one and explains the differences.
- *Means for this site:*
  - Add a "What's changed" (transition) page. It covers:
    - data model: Analyses and Stores rather than datasets and batches;
    - IDs;
    - genome build;
    - access: download plus API, versus the legacy JWT API;
    - which tools work with which;
    - why numbers differ between the two.
  - Link it from the home page during the transition.
  - The legacy site's headline (~50k datasets) and the new catalogue's count
    (35,109 Analyses on 2026-11-01) will both be visible. The transition page
    must explain the difference.

### 3. Commercial licence

- **Current thinking:** the licence grants access to the resource for its
  duration. Commercial users may do what they want with the data they obtain,
  within the terms of the original data provider. This may be refined.
- *Means for this site:*
  - The pitch becomes "subscribe, download, keep, within source terms".
  - The commercial page explains this in plain language and links to the
    rewritten terms.
  - Because a user's rights to retained data depend on the **source**
    licence:
    - every Analysis shows its source licence;
    - the licence also appears in bulk-download metadata;
    - the site **links to the provider's terms rather than paraphrasing
      them**, so it avoids implying rights it cannot grant.
  - The licence field is blank for 72% of listed Analyses (MVP and eQTLGen).
    Filling it is a prerequisite for the commercial page, not polish.

### 4. Legacy ID mapping

- **The mapping lives in the analytical tools, not on this website.**
- *Means for this site:* the transition page says that the tools handle legacy
  IDs, and links to their docs.

### 5. News and the blog

- **Start fresh** with a news section on this site.
- The `opengwasdb-stores` project site
  (`blog.opengwas.io/opengwasdb-stores/`) stays as the development and
  transparency site, and the About page mentions it.
- *Means for this site:*
  - The two 2024 blog posts are not migrated.
  - What happens to `blog.opengwas.io` is settled in decision 10.

### 6. Catalogue fields for the front page

Agreed. The catalogue should **store** the values the front page needs:

- total associations (today only 2 of 10 Stores report it);
- Store sizes (empty today);
- reference assembly (blank today);
- licence for MVP and eQTLGen.

### 7. Datasets page reads the catalogue SQLite directly

- **SQLite was chosen so the website can use it directly**, for example
  DataTables with server-side-style pagination.
- *Feasibility, checked against the 2026-11-01 catalogue:*
  - **File:** 31 MB, 4 KB pages, journal mode `delete` (not WAL).
  - **Indexes:** on label, ancestry, outcome type, trait class, tissue, sample
    size, store, region and trait ontology label.
  - **Search:** an FTS5 index (`analysis_search`).
  - That layout suits **querying the file in the browser over HTTP range
    requests**: SQLite compiled to WASM, with a virtual file system that
    fetches only the 4 KB pages a query touches. Each query fetches tens to
    hundreds of KB rather than the whole file. Compare today's 9.1 MB JSON.
  - DataTables' server-side mode accepts a custom `ajax` function, so "server
    side" can be a SQL query run in a Web Worker. No server is needed, and the
    site stays static and independent of the platform API, which matters while
    the API is on hold.
- *Constraints this creates:*
  1. **The host must honour `Range` requests and serve the file
     uncompressed.** The current opengwas.io server (openresty) returns
     `206 Partial Content`. GitHub Pages and other hosts would need testing
     with a real SQLite file.
  2. **Publish each catalogue version at an immutable URL**, following the
     catalogue's own `versions/<hash>` layout, and add a small pointer to the
     current version. If the file is replaced mid-session, range reads mix
     pages from two versions and the results are corrupt.
  3. **Only sort on indexed columns.** Sorting or filtering an unindexed column
     (for example first author or DOI) scans the whole table, which means
     fetching nearly all 31 MB. Either limit which columns can be sorted or add
     indexes in the catalogue build.
  4. **The WASM SQLite build must include FTS5** for the search box to use
     `analysis_search`.
  5. **The home page should not load the SQL engine** just to show headline
     numbers. The catalogue build can also emit a small JSON file (counts,
     `catalog_meta`, the latest changes) for the home page and the news feed.
  6. **Analysis pages** (one page per Analysis, for search engines and
     citation) can be static HTML generated from the same SQLite at build
     time, or rendered client-side from it. Pre-rendering is what gets them
     indexed.
- **Open:** if range requests on the chosen host prove unreliable, the
  fallback is a small query endpoint. That makes the site depend on an API,
  which is better avoided.

## 2026-11-02 (follow-up)

### 8. Legacy URLs and shutdown

- **There will be a grace period, after which the old site is shut down.**
  Archived legacy data stays available for those who still need it, with
  documentation.
- **A 404 page specific to `/datasets/` points to that documentation.**
- *Means for this site:*
  - **New Analysis pages must not live where legacy IDs did**, or the
    datasets 404 cannot tell an old link from a broken new one. Either use a
    separate path (for example `/analyses/OGS-00009/ukb-b-10001`), or rely on
    new IDs always starting with `OGS-`.
  - **Static hosts serve one site-wide 404.** For a page specific to
    `/datasets/`, either add a per-path rule on the server (on nginx or
    openresty: `location /datasets/ { error_page 404 /datasets/404.html; }`),
    or have a single `404.html` check `location.pathname` and show the legacy
    message. The server rule keeps the real status code. After the old site is
    shut down, consider `410 Gone`, which tells search engines to drop the URL.
  - **The 404 can name the ID from the URL**, for example "`ieu-a-2` is a
    legacy OpenGWAS ID". It then links to the archive documentation and to the
    tools that map legacy IDs (decision 4).
  - **Optional:** some legacy IDs survive unchanged as Analysis IDs. Every
    `ukb-b-*` ID is in OGS-00009. The 404 could run one exact-match lookup
    against the catalogue and link to the new page if one is found. That is a
    lookup, not a mapping, so it stays within decision 4. Skip it if it blurs
    the line.

### 9. Hosting

- **Host the site on `opengwas.io`**, the current server (openresty).
- *Means for this site:*
  - Constraint 1 under decision 7 is met in principle. The server returned
    `206 Partial Content` for a ranged request on 2026-11-02.
  - Before launch, check two things with a real `.sqlite` file:
    - that ranged requests return 206;
    - that no gzip is applied to the file.
  - The server also allows the `/datasets/` 404 rule from decision 8.
  - While here, redirect `http://` to `https://`; today the server serves
    plain HTTP. The audit noted this.

### 10. blog.opengwas.io and the stores site

- **These will be handled separately.** The stores development site will
  likely move to a `github.io` address, and `blog.opengwas.io` will redirect to
  this site's news page.
- *Means for this site:*
  - The About page links to the stores site's new `github.io` address once it
    moves.
  - The two old post URLs redirect to news along with everything else. Nothing
    here needs to change.

### 11. Home page: variant D, "the architecture"

- **Approved.** Variant D of the prototype, which is kept unmerged on the
  branch `prototype/home-variants` (folder `prototype/home/`).
- **Why:** the home page should sell what the new architecture makes possible,
  not describe the catalogue:
  - stores are imputed, and imputed values are flagged;
  - they are about a tenth of the size of their source;
  - they are fast to query in every direction: PheWAS, top hits, HapMap3,
    region, lookup and whole analysis;
  - they are low-friction to use from a laptop, a cluster or analysis tools.
- **What came from the other variants:**
  - Variant A's commercial-use wording, kept verbatim: "Free for
    non-commercial research. Companies need a licence, and licence fees keep
    the resource running."
  - Variant C's catalogue overview moves to `/data/`, with a short version on
    `/about/`.
  - Variant B's four steps move to `/about/`.
- **Rules carried into the real build:**
  - Every number comes from data: the catalogue for counts, benchmark records
    for timings, and measured bytes for sizes. Nothing is hand-typed.
  - Timings shown are only those measured on the **published, imputed**
    release of a Store. A Store without one is left out of the demo, not
    approximated.
  - Size claims state their range and their exceptions. Sparse QTL stores do
    not shrink.
  - The query tour pauses on hover, has a Pause/Play control, stops when the
    visitor chooses a query, and does not start under reduced motion.
  - "Available now", "Coming soon" and "In progress" statuses must be true on
    launch day. "Available now" for local use needs a pip/conda release and a
    download route.

## Still open

Nothing blocks starting the design work.
