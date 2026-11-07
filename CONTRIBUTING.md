# Working on the website

The site is plain HTML built by a small Python program (`sitegen/`) from
Markdown, a few YAML files and the Analysis Catalog. Most changes are to
Markdown or YAML and need no code.

```text
content/          Markdown pages: about, licensing, transition, legal/, news/
data/
  site.yaml       menu, transition notice, footer
  home.yaml       every word on the home page
  stores.yaml     display names for each Store Release
  tools.yaml      the tools page, and whether each tool works with the new stores
  benchmarks.json query timings and sizes for the home page (generated, see below)
templates/        page layouts (Jinja)
static/           CSS, JavaScript, fonts and images, served under /assets/
  vendor/         third-party code, unchanged, with its licence and source
sitegen/          the build
tests/            tests, and a small copy of the catalogue for them
```

## Common changes

You can make any of these in GitHub's web editor: open the file, edit it,
and choose **Create a new branch and start a pull request**. The *Build*
check on the pull request builds the whole site and fails if anything
breaks.

**Add a news post.** Create `content/news/YYYY-MM-DD-short-title.md`:

```markdown
---
title: FinnGen release 13 is in the catalogue
date: 2026-11-10
summary: One sentence, shown in the news list and the feed.
---

The post, in Markdown.
```

Add `draft: true` to the top section to keep a post off the live site while
you work on it. Catalogue updates don't need a post: the site writes one for
every new catalogue version by itself.

**Change a page's text.** Edit its Markdown file in `content/`. The section
at the top can set:

| Field | What it does |
|---|---|
| `title` | The page heading (required) |
| `lede` | The larger sentence under the heading |
| `description` | The summary search engines show |
| `notice` | A highlighted note at the top, such as "Draft" |
| `updated` | Adds "Last updated" with this date at the end |

A new Markdown file becomes a new page at the address its path gives:
`content/legal/cookies.md` is published at `/legal/cookies/`.

**Change the home page's words.** Edit `data/home.yaml`. Text in
`{{ double braces }}` is filled in from the catalogue and the benchmarks when
the site is built. Reword around it, but keep the braces. Never type a
number in by hand (decision 11).

**Change the menu, the transition notice or the footer.** Edit
`data/site.yaml`. To remove the transition notice, delete the `notice:` text.
When the platform launches, follow the comment on the Platform menu item.

**Update a tool's status.** Edit `data/tools.yaml`. Statuses must be true on
the day they go live.

## Preview the site on your own machine

Install [pixi](https://pixi.sh), then:

```sh
pixi run serve                                    # on the OpenGWAS server
pixi run serve --catalog tests/fixtures/catalog   # anywhere else
```

Open <http://localhost:8000/>. The site rebuilds whenever you save a file.
The preview shows draft posts; the live site doesn't. Away from the server,
the preview has only the test catalogue: a few Analyses from each Store.

Before opening a pull request that changes code or templates, run:

```sh
pixi run test
pixi run build --catalog tests/fixtures/catalog && pixi run check
```

Changes to the Data page's search (`static/js/catalogue-search.js`) also have
browser tests, which check what the page shows against the catalogue:

```sh
pixi run -e browser install-browser   # once
pixi run -e browser test-browser
```

## Data that comes from elsewhere

- **The Analysis Catalog** is read when the site is built, so every count,
  Store and Analysis page follows the published catalogue.
- **`data/benchmarks.json`** holds the home page's query timings and sizes.
  When a Store in the demo or the size comparison is rebuilt, run
  `pixi run collect-benchmarks` on the OpenGWAS server and commit the result.
  Only benchmarks measured on a published, imputed release are allowed.
- **`tests/fixtures/catalog/`** is a small copy of the catalogue for tests and
  previews. Refresh it on the server with `pixi run make-fixture` when the
  catalogue's format changes.

## Publishing

For development, the site is hosted on the OpenGWAS build server in Bristol,
reachable over the University network and VPN at
<http://app-dc3-ogws-p0.services.bris.ac.uk:8080/> (decision 14). Every five
minutes it checks for a new commit or catalogue version, rebuilds, checks the
links and switches to the new build. How that works, and how to run its
container, is in [`deploy/README.md`](deploy/README.md).

Whatever serves the site must provide (`deploy/site.conf.template` does all of
this except HTTPS):

- the site's 404 page for missing pages, and `/datasets/404.html` for missing
  pages under `/datasets/` (decision 8);
- `http://` redirected to `https://` (decision 9);
- the catalogue files under `/data/catalog/` served for range requests:
  keep-alive or HTTP/2, `Accept-Ranges: bytes`, no gzip on `.sqlite`, and
  `application/wasm` for `.wasm` (decision 13).
