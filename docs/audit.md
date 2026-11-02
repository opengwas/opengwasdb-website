# opengwas.io audit, 2026-11-02

This audit is based on a headless crawl of every reachable page on
`opengwas.io`, `api.opengwas.io` and `blog.opengwas.io` (26 URLs), at desktop
(1366px) and phone (390px) widths. It is read against the new infrastructure in
`opengwasdb` and `opengwasdb-stores`.

Supporting notes:

- [`current-site/inventory.md`](current-site/inventory.md): page-by-page facts,
  usage and terms.
- [`current-site/snapshots/`](current-site/snapshots/): verbatim EULA, Service
  Description, Privacy Notice, About and API tutorial.
- [`new-platform-brief.md`](new-platform-brief.md): what the new platform can
  and cannot claim today.

## The short version

The current site is a thin shell around the legacy API.

- **Almost every explanatory sentence describes infrastructure being retired:**
  GWAS-VCF on hg19, JWT tokens, per-request "cost", and `ieu-a-*` IDs.
- **It is effectively unusable on a phone.** The main site has no viewport tag,
  so every page renders as a shrunken desktop page with 5–7px text.
- **A business can't work out whether it needs a licence, what one costs, or
  how to buy one** without emailing a person.

None of this is fatal. The site is small, about eight real pages. The harder
problems are not design problems:

1. The legal terms conflict with the new distribution model.
2. The new platform's headline number (35,109 Analyses) is lower than the old
   site's ("more than 50,000").
3. The "platform" the README wants a page for does not exist yet.

---

## 1. What looks dated

### Content that is now wrong or old

- **The "Coming in 2026" box on the home page.** It is November 2026. One item
  (MVP) is delivered, but in a different system. The other two (GRCh38 liftover,
  EBI refresh) are being delivered by a different architecture than the box
  implies.
- **The blog's last post is from April 2024.** There are two posts, both about
  introducing rate limits, so the "news" a visitor finds is about restrictions.
  The footer reads "2018 - 2024".
- **The main citation is a 2020 bioRxiv preprint.** The OpenGWAS
  infrastructure paper never reached a journal. The GWAS-VCF paper is still
  cited as a preprint, although it **was published in Genome Biology in 2021**
  (PMID 33441155). To a reviewer or a procurement team, a six-year-old preprint
  reads as "unmaintained".
- **MR-Base is presented as live in the API tutorial**, while `/about` says it
  is decommissioned.
- **"Dependencies" lists the old stack:** Flask, Kubernetes, Neo4j,
  Elasticsearch, Airflow, Redis, MySQL. None of it is the new
  SQLite/Zarr/Snakemake/Pixi stack.
- **The credits describe the MR-Base-era team**, using the old role split
  (bold marks active contributors). The OpenGWASDB and stores work is not
  credited anywhere.
- **The consortia list ends in a literal "...".**

### Visual and technical signals

- **It is a stock Bootstrap 5 template.** The page is a cornflower-blue icon
  grid with no imagery, data or product shot, so nothing shows what the
  resource does.
- **Four unrelated visual identities.** The main site is light Bootstrap, the
  API tutorial is a dark theme with orange buttons, green links and the Lato
  font, the docs are default Swagger UI, and the blog is a Hugo theme.
  Following "api" from the nav feels like leaving the site.
- **The header and footer are injected by JavaScript at runtime.** Search
  engines and no-JS clients see pages without navigation.
- **The table of contents on the About and policy pages loads from
  `cdn.rawgit.com`.** That service shut down in 2019.
- **Shared links unfurl blank.** No page has a meta description, Open Graph
  tags or a share image, so a link in Slack, Teams or LinkedIn shows nothing.
  Most pages have no `<h1>`, and the home page has a mismatched `<h1>…</h3>`.
- **`http://opengwas.io` is served without redirecting to HTTPS.**
  `www.opengwas.io` does not resolve.
- **There is no `robots.txt` and no `sitemap.xml`.** About 50,000 dataset pages
  are invisible to search engines, which is free inbound traffic you are not
  getting.

---

## 2. What is missing

Ordered roughly by how much each gap costs you.

1. **Any description of the new platform.** Stores, OGS ids, Reference
   Completion, multi-ancestry, immutable releases and local or HPC querying are
   all absent. The site sells the thing being switched off.
2. **A commercial-use page.** Today the only route is EULA clause 3.3: "get in
   touch via email". Section 5 covers what that page should contain.
3. **Licence information that is visible, filterable and complete.** The EULA
   promises to "surface" licence and Open/Restricted flags (2.4). On the site
   this appears as a raw field, `is_nc: Unknown (commercial use might or might
   not be permitted…)`, which cannot be filtered. In the new catalogue the
   licence field is **blank for 72% of listed Analyses**, all of MVP and
   eQTLGen.
4. **One source of truth for numbers.** The site shows 50,066, 50,174, 50,193
   and "more than 50,000" on different pages. The README's front-page counters
   need the catalogue to *store* associations and store sizes. Today only 2 of
   10 Stores report associations, and none report size.
5. **A quickstart.** No page shows an install command and a first query. This
   matters most for the new local-first model, where the user does the
   installing.
6. **A migration guide from legacy to new.** Thousands of papers and scripts
   cite `ieu-a-2`, `ebi-a-GCST…` and similar IDs. Only the `ukb-b` IDs survive,
   inside OGS-00009. The site needs to explain where a legacy ID went, and what
   happens to ieugwasr and TwoSampleMR users.
7. **A tools page.** The README asks for the suite of linked tools to be
   referenced. Today they get one sentence on the home page and a list in the
   API tutorial. The page should name each tool, say what it does, and give its
   status on the new backend. On disk the "Tool integration" workstream has not
   started.
8. **A news or "what's new in the data" feed.** The catalogue already writes a
   "Change since the previous version" section and a `changes.tsv` with every
   build, so this can be generated rather than written by hand.
9. **How to cite in one place.** Citations are duplicated, slightly differently,
   across `/about` and EULA section 6. There is no copy button or BibTeX, and
   nowhere to put the forthcoming paper.
10. **Dates and versions on the legal documents.** None of the three policies
    has an effective date or version, and there is no change history. EULA 10.3
    says notice is "deemed received… 24 hours after it is first posted on our
    website", which only works if the website shows when something was posted.
11. **An accessibility statement.** University websites almost certainly fall
    under the UK Public Sector Bodies Accessibility Regulations 2018. Check this
    with the UoB web team.
12. **Cookie and analytics consent.** Microsoft Clarity's session-recording
    script loads on every page of the main site and the API site. There is no
    consent banner, and the Privacy Notice does not mention Clarity, although it
    does name Oracle and Microsoft Forms. Clarity normally sets first-party
    cookies; under UK PECR that needs consent.
13. **A data contribution route.** The footer's "Data contributions or requests"
    link is commented out in the HTML. The About page says "contact us" and
    links to a personal email.
14. **Team, governance and sustainability.** The site never says who runs
    OpenGWAS now, how it is funded, or why industry pays. That story is the
    justification for cost recovery.
15. **A status link on the main site.** `status.opengwas.io` exists but is
    reachable only from the API tutorial.

---

## 3. What is confusing

- **What is it?** The header logo says "ieu open gwas project", the title says
  "OpenGWAS", the API site says "IEU OpenGWAS project" and "OpenGWAS API", and
  the tagline ("Empowering decision makers to maximise improvements to public
  health") says nothing about GWAS, data or tools. A first-time visitor can't
  tell whether this is a database, an API, a method or a research group.
- **The navigation changes under you.** The main nav is
  home · datasets · about · api. On `api.opengwas.io` it becomes
  home · datasets · api · account, with no about, and a "phewas" link
  elsewhere returns **404**. The API landing page also shows a literal "..."
  placeholder under its title.
- **The allowance tiers are identical.** Trial, Standard and Commercial are all
  "100000 per 10 minutes". Users are told to "upgrade to Standard" for no
  visible gain.
- **"Cost" and "allowance" sound like billing.** The API's per-request "cost"
  formulas make a free service look metered. Academics worry they are spending
  something, and businesses can't tell whether the commercial licence is priced
  per request.
- **Commercial users hit a wall before any explanation.** Email sign-in
  "accepts academic email address only, unless you are an approved commercial
  user", but nothing says how to become approved.
- **The site contradicts itself on downloads.**
  - `/about` tells you to download VCFs, and a dataset page offers a Download
    button limited to "20 datasets per 24 hours".
  - The EULA forbids attempts to "download… mirror, republish" the Services
    (2.1) and bulk downloading through the API (4.3), and says bulk download
    costs allowance.
  - The new model makes downloading Stores the main way to use the data.
- **"Commercial licence does not include a licence to the datasets."** This is
  correct and necessary, but it is the most prominent fact a business reads,
  and nothing tells them which data they *can* use.
- **Dataset pages show raw database fields** (`mr`, `priority`, `is_nc`, `nsnp`,
  `ncase`, `ncontrol`, `note: NA`) with no labels or explanation.
- **The datasets table opens in random order.** eQTLGen rows, whose trait is an
  Ensembl ID, make up 40% of the data, so the first screen is mostly
  `ENSG000…` rows. That is an off-putting first impression of a curated
  resource.
- **Terminology is inconsistent.** "Dataset", "study", "GWAS", "trait",
  "phenotype" and "batch" are used interchangeably. The new stores define
  Analysis, Trait, Store and Store Release precisely. The redesign is the
  moment to adopt that vocabulary (see `new-platform-brief.md`).
- **The blog is on its own subdomain with its own "About" page**, and that page
  just links back to the main site.

---

## 4. What breaks on a phone

All figures come from the 390px crawl, captured with an iPhone user agent.

| Page | Problem | Severity |
|---|---|---|
| **Every `opengwas.io` page** | **No `<meta name="viewport">`.** The browser lays out at 980px and shrinks to about 40%, so 16px body text renders at about 6px and 13px legal text at about 5px. Users must pinch-zoom and pan every page | Critical |
| Same | 14–84 tap targets per page are under 24px before scaling, and the nav links render with about 6px text after scaling | Critical |
| `/datasets` | Downloads a **9.1 MB JSON** on first visit before the table renders (it is cached in IndexedDB afterwards). On mobile data this is slow and costly | High |
| `/datasets` | A 10-column table, 1,389px wide, with filter inputs in the header row. The page itself warns "The table is horizontally scrollable" | High |
| `/datasets/<id>` | A two-column layout shrunk to fit; the Download panel and its code links are unreadable | High |
| `/policies/*` | 25,000-character legal text rendered at about 5px, beside a sidebar table of contents that takes a third of the width | High (you rely on people having read it) |
| Footer, every page | Ten partner logos in three rows dominate the screen on a short page | Medium |
| `api.opengwas.io/api/docs` (Swagger) | No viewport tag either | Medium (developers use desktops) |
| `api.opengwas.io/` | Responsive, but the logo disappears on mobile, leaving only a hamburger, and the "..." placeholder shows | Low |
| `blog.opengwas.io` | Fine. The Hugo theme is responsive | — |

The single biggest mobile fix costs one line of HTML. The real fix is a layout
designed for narrow screens first, especially for the catalogue. On a phone the
catalogue should be search-first with result cards, not a 10-column table.

---

## 5. Making it more attractive to businesses (cost recovery)

Be honest about what changes first. **The current commercial offer is "API
access plus the cloud compute to deliver data".** That is the Service
Description's own wording. The new architecture deliberately moves compute to
the user: local, HPC, or a thin router. Once Stores can be downloaded, a
business is no longer paying for compute. The offer has to be redefined around
what OpenGWAS uniquely adds:

- the *right to use* the harmonised resource commercially;
- curation, harmonisation and Reference Completion;
- a predictable stream of updated releases;
- provenance;
- support.

That needs deciding before the page is designed. The points below assume that
direction.

### Lead with the things pharma actually buys

1. **Queries that stay on their own network.** Pharma and biotech teams are
   cautious about sending target genes or variants to an external API, because
   the query itself reveals what they are working on. Self-contained Store
   Releases that run inside their own HPC or VPC are a genuine competitive
   advantage over every hosted GWAS API. Say so prominently. (The EULA must
   first permit it; see below.)
2. **Provenance and reproducibility.** Immutable, identified releases (OGS ids),
   validation records, recorded build commands, observed and imputed
   associations kept distinct, and per-Analysis Reference Completion quality.
   That is an audit story regulated industries value. Show a release's "receipt"
   on its page.
3. **Licence clarity per Analysis.** The new schema records licence, DOI, PMID
   and consortium for every Analysis. A catalogue filter for "commercially
   usable under source terms" is the most useful single feature you could offer
   a business, and nobody else does it well. **Today 72% of listed Analyses
   have a blank licence**, so filling that is a prerequisite, not polish.
4. **Breadth that is ready to use.** Multi-ancestry coverage (MVP AFR, AMR, EAS
   and META), FinnGen R13 and eQTLGen, harmonised to one contract with a
   declared reference panel. Show the ancestry breakdown, because it is a
   differentiator.

### Remove procurement friction

- **A "Do I need a commercial licence?" decision box**: for-profit employer,
  contract work for one, or commercial product, then yes. Most companies want
  to comply. Make it a two-second answer.
- **Published tiers, or at least starting prices** ("from £X per year"), banded
  by organisation size or use. Each tier states what's included:
  - support response time;
  - update cadence;
  - early access to new Stores;
  - private builds of the customer's own data into the store format;
  - a named contact.
  
  "Email us for a price" filters out the smaller biotech and AI companies that
  are probably your growth market.
- **A procurement pack to download**, containing:
  - the subscription terms (so legal can review before the first call);
  - a short security and data-protection summary: where data and logs live,
    and **what query logging you do**, which pharma infosec will ask about
    first;
  - the University of Bristol as the contracting entity, with invoicing, PO and
    VAT details.
- **A contact form that goes to the shared mailbox** (`ieu-opengwas@bristol.ac.uk`,
  already named in EULA 3.3). It should replace the personal email in the
  footer, with a stated response time. A named individual's inbox signals
  "hobby project" to a procurement team.
- **A self-serve route for commercial trials**, instead of email sign-in
  rejecting them.

### Build credibility

- **Explain the commercial logos you already have.** GSK, Biogen, BenevolentAI
  and Oracle sit in the footer with no explanation. With permission, turn them
  into "Supported by" or "Used by" and add a one-line case study each.
  Recognisable peers matter more than anything else on a business page.
- **Show demand.** The legacy API currently serves about 5,700 requests an hour
  (from `/api/status`). Add user counts and citation counts for TwoSampleMR and
  MR-Base. Academic adoption is the reason a company trusts the data.
- **Tell the sustainability story honestly:** "Free for non-commercial
  research, because commercial users fund it." Academics accept it and
  businesses respect it. It also pre-empts "why should we pay for public
  data?".
- **Show reliability signals:** the status page, a public data changelog and
  dated releases.
- **Replace Clarity with consented or cookieless analytics.** Corporate
  networks often block session-recording scripts, and infosec teams dislike
  them on a site where staff type target names into a search box.

### Terms that need changing before the business pitch works

- **EULA 2.1 and 4.3** forbid downloading, mirroring and bulk access, which are
  the main use of the new model. Rewrite them around Store distribution.
- **EULA 4.1, the Service Description, and the Privacy Notice** depend on
  `api.opengwas.io/api/` and on "cloud-based… API" wording. Rewrite all three
  for the new service shape.
- **Add version and effective dates to every legal document**, and keep the
  previous versions online.

---

## 6. Decisions needed before building

> **Answered 2026-11-02.** See [`decisions.md`](decisions.md) for each answer
> and what it implies. The list below is kept as originally written.

These are not design questions, but the design depends on each one.

1. **What "platform" means at launch.**
   - Keep the legacy API running alongside, and say so.
   - Ship the local Stores and CLI only, with no PyPI release yet.
   - Or hold the platform page until the Horizon 4 service exists.
2. **The headline number.** The new catalogue lists 35,109 Analyses. The old
   site claims more than 50,000. Either rebuild the missing legacy batches
   first (Pan-UKB, brain imaging, the pQTL and metabolite batches, BBJ, the
   curated `ieu-a` and `ieu-b` sets) or explain the change ("re-harmonised,
   multi-ancestry, reference-completed"). Don't quietly show a smaller number.
3. **The commercial offer.** What a licence buys once compute moves to the
   user, and whether prices are published.
4. **Legacy IDs.** Will the site redirect `opengwas.io/datasets/ieu-a-2` to
   something? Those URLs are in published papers.
5. **The blog.** Migrate the two 2024 posts (whose content is obsolete), or
   start fresh at `/news`. Also decide what happens to the developer status
   site at `blog.opengwas.io/opengwasdb-stores/`, which currently occupies the
   blog's domain.
6. **Catalogue fields the front page needs**, to be stored rather than
   computed: total associations, Store sizes, reference assembly (blank today),
   and licence for MVP and eQTLGen.
7. **Hosting the catalogue.** It exists only on the host today. The datasets
   page needs a public, versioned copy: SQLite for download, plus a static JSON
   or Parquet slice for the browser that is much smaller than today's 9 MB.
