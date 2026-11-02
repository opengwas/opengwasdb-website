# Current opengwas.io — page inventory and key facts

Crawled 2026-11-02 with a headless browser (desktop 1366px and phone 390px).
Scope: `opengwas.io`, `api.opengwas.io`, `blog.opengwas.io`, plus the landing
pages of `gpmap.opengwas.io` and `status.opengwas.io`. There is no
`robots.txt` or `sitemap.xml`, so pages were found by following links.

Verbatim copies of the pages whose wording must carry across (EULA, Service
Description, Privacy Notice, About, API tutorial) are in
[`snapshots/`](snapshots/).

**Most of the technical description below is about to be wrong.** The current
site describes the legacy platform: GWAS-VCF files on hg19, a cloud REST API at
`api.opengwas.io` with JWT tokens and per-request "cost", and `ieu-a-*`-style
dataset IDs. The replacement is OpenGWASDB Store Releases (`OGS-xxxxx`), built
by `opengwasdb-stores` and queried locally, on HPC, or behind a thin service.
Each fact below is marked **[stale]** when the new infrastructure changes it,
**[keep]** when it should carry across, and **[decide]** when it is a policy
choice for the team.

## Site map

| URL | What it is | Notes |
|---|---|---|
| `/` | Landing page: tagline, four tiles (Datasets, API, Analysis integrations, Genotype-phenotype map), a "Coming in 2026" box | Only 1,096 characters of text |
| `/datasets/` | A DataTables browser over every dataset, with a batches panel and CSV export | Downloads a 9.1 MB `gwasinfo.json` on first visit and caches it in IndexedDB |
| `/datasets/<id>` | Detail page for one dataset: raw metadata fields, a download button, a GPMap note | Around 50k pages, with no sitemap |
| `/about` | Background, GWAS-VCF, citations, bulk downloads, credits, dependencies, contributing consortia | The consortia list ends in a literal "..." |
| `/policies/eula` | End-User Licence Agreement, 13 sections | No version or effective date |
| `/policies/service-description` | Service Description (commercial customers only) | No version or effective date |
| `/policies/privacy` | Privacy Notice | No version or effective date |
| `/phewas` | **404.** It is linked from the api.opengwas.io navigation | Dead link |
| `api.opengwas.io/` | Sign-in page: Microsoft (recommended), GitHub, email (academic only) | Shows a literal "..." placeholder under the title |
| `api.opengwas.io/api/` | API tutorial: overview, auth, allowance and cost, related tools | Dark theme, which differs from the main site |
| `api.opengwas.io/api/docs` | Swagger UI, API v4.0.0 (31 operations) | No viewport tag |
| `api.opengwas.io/api/status` | Raw JSON status | See numbers below |
| `api.opengwas.io/profile/` | Account page (needs a login, so not crawled) | |
| `blog.opengwas.io/` | Hugo blog with **2 posts**, the latest dated 2024-04-21; footer reads "2018 - 2024" | Hosted on GitHub Pages |
| `status.opengwas.io` | Uptime and maintenance page | |
| `gpmap.opengwas.io` | Genotype-Phenotype Map, a separate application | Out of scope for the redesign; link to it |

Main navigation is home · datasets · about · api, injected at runtime from
`/common/header.html` by JavaScript.

The footer has:

- funder and supporter logos: UoB, MRC IEU, Wellcome, Royal Society, GSK, NIHR Bristol BRC, BenevolentAI, CRUK, Biogen, Oracle Cloud Infrastructure;
- links to the EULA, Service Description and Privacy Notice;
- Contact, a `mailto:` to one person's university address.

## Headline numbers the current site shows (all legacy)

| Where | Number |
|---|---|
| Home page | "more than 50,000 GWAS summary datasets" |
| `/datasets` | "Listing 50,066 datasets" |
| Sum of `gwasinfo_batches.json` counts | 50,193 across 22 batches (3 of them marked "DO NOT USE") |
| `/api/status` | `N_DATASETS` 50,174; `N_PUBLIC_DATASETS` 50,055 |
| `/api/status` | `N_REQS_IN_PAST_HOUR` 5,715 (useful evidence of demand) |

The site therefore shows three different totals. **[stale]** The new front
page should take one set of numbers from one source, the stores catalogue.

The legacy batches, by size:

| Batch | Datasets | Description |
|---|---:|---|
| eqtl-a | 19,935 | eQTLGen 2019 |
| ebi-a | 6,328 | EBI GWAS Catalog full summary stats |
| ubm-b | 3,935 | UKB brain imaging (expanded) |
| ukb-e | 3,801 | Pan-UKB |
| prot-a | 3,282 | Sun 2018 pQTL |
| ubm-a | 3,143 | UKB brain imaging (Elliott 2018) |
| finn-b | 2,803 | FinnGen R5 |
| ukb-b | 2,514 | IEU UKB |
| prot-c | 1,124 | Suhre 2017 pQTL |
| ukb-d | 838 | Neale round 2 |
| ukb-a | 596 | Neale round 1 |
| met-a | 452 | Shin 2014 metabolites |
| ieu-a | 434 | Manually curated consortia |
| ieu-b | 277 | Manually curated consortia |
| met-d | 249 | Nightingale UKB |
| met-b | 150 | Roederer immune traits |
| met-c | 123 | Kettunen metabolites |
| bbj-a | 120 | Biobank Japan |
| prot-b | 83 | Folkersen pQTL |
| test-a, met-e, prot-d | 6 | Internal or work in progress, marked "DO NOT USE" |

## Usage, access and allowance (legacy API)

- **Account required for everything except `/status` and `/batches`.** This has
  been the case since 1 May 2024. Sign-in options:
  - Microsoft (recommended);
  - GitHub;
  - email, which accepts academic addresses only "unless you are an approved
    commercial user".
  
  **[stale]**: tied to the legacy API.
- **JWT token** valid for 14 days. A user holds one token at a time and sends it
  as `Authorization: Bearer <token>`. **[stale]**
- **Allowance tiers** are "No allowance", "Trial", "Standard" and "Commercial".
  All three paid or free tiers are listed at *100,000 per 10 minutes*, so the
  tier table tells users nothing. University of Bristol users get more.
  Exceeding the allowance repeatedly can block the account and IP address for
  up to a week. **[stale; the concept of fair-use limits is [decide]]**
- **Cost per request** comes from a formula per endpoint, for example:
  - `/associations` costs `max(Nid, Nvariant)`, or five times that with proxies;
  - `/phewas` costs `variants × 20 + Nresults`;
  - `/gwasinfo/files` costs `Nid × 1000` beyond 100 ids.
  
  **[stale]**
- **Downloads:** "You can only download VCF files of 20 datasets per 24 hours
  on this website." Bulk download costs allowance. "There is not currently a
  single file to download everything." **[stale]**: the new model publishes
  self-contained Store Releases to download.
- **Client packages named:** ieugwasr, ieugwaspy, TwoSampleMR, gwasglue,
  gwasglue2, the MRC IEU R-universe, gwasvcf and gwas2vcf. MR-Base is also
  named, even though `/about` says it is decommissioned. **[decide]**: which
  of these survive the migration, and with what install story.
- **"White label" ban:** "OpenGWAS must not be provided as 'white label'
  software or service by any means." A package that wraps the API must
  surface the JWT to its users. **[keep the principle]**
- **Status:** `api.opengwas.io/api/status` and `status.opengwas.io`.

## Terms and licensing (from `snapshots/eula.md` and `snapshots/service-description.md`)

- **The licensor is the University of Bristol.** It is a body incorporated by
  Royal Charter, RC000648. English law and the courts of England and Wales
  govern the licence. **[keep]**
- **Free use is limited to "private or non-commercial research purposes"** (EULA
  1.3). **[keep]**: this is the basis for cost recovery.
- **Commercial use needs an "organisation-level platform subscription
  agreement"** (EULA 3.1). Using the service commercially without one is a
  breach, and the University may charge "our current annual fees" (3.2).
  Purchase is by emailing `ieu-opengwas@bristol.ac.uk` (3.3). No price, tiers
  or process are published. **[decide]**
- **No licence is granted to the Datasets** (2.3). The University surfaces
  licence metadata and "Open Access" / "Restricted Access" flags but does not
  warrant them (2.4, 2.5). On dataset pages this appears as a raw `is_nc` field,
  for example "Unknown (commercial use might or might not be permitted - check
  with the author, not OpenGWAS)". **[keep the concept]**: the new stores carry
  per-Analysis Attribution Metadata (licence, DOI/PMID, consortium).
- **Restrictions** (2.1) include:
  - no automated access except through the documented APIs;
  - no circumventing rate limits;
  - no identifying living individuals;
  - no building a competing product;
  - no providing services to third parties;
  - "attempt to copy… mirror, republish, download… all or any portion of the
    Software, Services and/or Documents".
  
  **[stale/conflict]**: the new local-first, downloadable-store model needs
  this rewritten.
- **No bulk download through API queries** (4.3). **[stale/conflict]** for the
  same reason.
- **API limits are defined by reference to `https://api.opengwas.io/api/`**
  (4.1). **[stale]**: this is a hard link from the contract to a page that will
  disappear.
- **Citation obligations** are in EULA section 6 and `/about`. The text cites:
  - the 2020 bioRxiv preprint of the OpenGWAS infrastructure, which was never
    published in a journal;
  - MR-Base (eLife 2018);
  - GWAS-VCF, cited as a bioRxiv preprint, although it **was published in
    Genome Biology in 2021** (PMID 33441155, doi:10.1186/s13059-020-02248-0).
  
  **[stale]**: the forthcoming OpenGWASDB paper will replace these.
- **Liability** is capped at £100 for non-commercial users. Commercial
  liability is capped under the subscription agreement (8.5). **[keep]**
- **Funders are excluded from warranty:** CRUK and Cancer Research Horizons are
  named (8.8). **[keep]**
- **Service Description (commercial customers only):**
  - "reasonable endeavours" to provide 24/7 availability;
  - planned maintenance notified in advance;
  - no SLA, no response-time commitment, no guarantee of long-term
    preservation;
  - "Support is limited."
  - It describes OpenGWAS as "a cloud-based data aggregation and delivery
    service", and the commercial licence buys API access plus the cloud compute
    to deliver data.
  
  **[stale]**: the description assumes the cloud API.

## Privacy (from `snapshots/privacy.md`)

- **Personal data collected:** name, email, affiliation and role. Sources are
  the sign-in form and Microsoft or GitHub OAuth.
- **Lawful basis:** Art. 6(1)(b), contract.
- **Retention:** inactive accounts are deleted after 3 years. Pseudonymised
  logs may take up to 6 months to clear.
- **Processors named:** Oracle Cloud and Microsoft Forms.
- **Contacts:** a named individual's email, and the UoB DPO at
  `data-protection@bristol.ac.uk`.
- **Not mentioned:** Microsoft Clarity. Clarity's session-recording and
  analytics script (`clarity.ms`, tag `sq9z63te1u`) loads on every page of
  `opengwas.io` and `api.opengwas.io`. **No consent banner and no cookie notice
  appear anywhere.**

## "Coming in 2026" box on the home page (now stale)

- All datasets lifted over to GRCh38
- EBI datasets updated
- MVP (GIA) datasets imported

## Credits (from `/about`)

Credits are grouped as Methodology, Data administration and curation, Data
pipeline, Software (server), Software (client), Platform architecture and
Research IT. Active contributors are shown in bold: Gaunt, Hemani, Haycock,
Dai, Qiu, Palmer and Henry. Related
projects are EpiGraphDB and GPMap. The page also lists the open-source
dependencies (Flask, Kubernetes, Neo4j, Elasticsearch, Airflow and others) and
about 60 contributing consortia, which end with a literal "...".
**[decide]**: refresh the credits for the OpenGWASDB team.

## Blog

There are only two posts, both about the 2024 introduction of authentication:

- 2024-03-20, "Managing traffic to the OpenGWAS API"
- 2024-04-21, "User authentication is now live"

The first post quotes an older "Terms of use" wording, not the current EULA.
Nothing has been posted in roughly 2.5 years.

## Technical observations

- **Main-site pages (`opengwas.io/*`) and the Swagger UI have no
  `<meta name="viewport">`.** Phones lay them out at 980px and shrink them to
  fit, so body text renders at about 5–7 CSS px. Pages on `api.opengwas.io` and
  `blog.opengwas.io` do have one.
- The header and footer are fetched by JavaScript at runtime, so crawlers and
  no-JS clients see pages without navigation.
- Most pages have no `<h1>`. The home page has a mismatched `<h1>…</h3>`.
- No page has a meta description or Open Graph tags, except the blog, which
  has a description but no image. Shared links therefore unfurl blank in
  Slack, Teams and LinkedIn.
- `http://opengwas.io/` serves the page over plain HTTP without redirecting to
  HTTPS. `www.opengwas.io` does not resolve.
- The About and policy pages load their table of contents from
  `cdn.rawgit.com`. RawGit shut down in 2019.
- Microsoft Clarity loads on every `opengwas.io` and `api.opengwas.io` page.
- There are four visual identities: the main site (light Bootstrap), the API
  tutorial (dark, orange and green, Lato), Swagger UI, and the blog (a Hugo
  theme).
- The datasets table opens in **random order**. eQTLGen Ensembl-ID "traits"
  are 40% of all rows, so the first screen is mostly `ENSG000…` rows.
