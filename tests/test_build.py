"""Build the whole site from the small test catalogue and check what comes out."""
import re
import sqlite3
from pathlib import Path

import pytest

from sitegen import content
from sitegen.build import build
from sitegen.check import check

FIXTURE = Path(__file__).parent / "fixtures" / "catalog"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("build") / "_site"
    result = build(FIXTURE, out)
    return out, result


def listed(sql):
    db = sqlite3.connect(f"file:{(FIXTURE / 'current' / 'catalog.sqlite').resolve()}?mode=ro", uri=True)
    return db.execute(sql).fetchall()


def test_every_internal_link_resolves(site):
    out, _ = site
    assert check(out) == []


def test_one_page_per_listed_analysis_and_store(site):
    out, result = site
    analyses = listed("select store_id, analysis_id from listed_analyses")
    assert result["analyses"] == len(analyses)
    for store_id, analysis_id in analyses:
        assert (out / "data/analyses" / store_id / analysis_id / "index.html").is_file()
    for (store_id,) in listed("select distinct store_id from listed_analyses"):
        assert (out / "data/stores" / store_id / "index.html").is_file()


def test_main_pages_exist(site):
    out, _ = site
    for path in ["index.html", "data/index.html", "data/stores/index.html", "tools/index.html",
                 "news/index.html", "news/feed.xml", "about/index.html", "licensing/index.html",
                 "transition/index.html", "legal/terms/index.html", "legal/privacy/index.html",
                 "404.html", "datasets/404.html", "sitemap.xml", "robots.txt", "favicon.ico"]:
        assert (out / path).is_file(), path


def test_home_page_numbers_come_from_the_catalogue(site):
    out, _ = site
    (n,) = listed("select count(*) from listed_analyses")[0]
    html = (out / "index.html").read_text()
    assert f"The catalogue holds {n:,} analyses" in html


def catalogue_versions():
    """Each test catalogue version, and whether it changed any listed analysis.

    A first version has no changes.tsv and lists every analysis it holds; a
    later one's changes.tsv has a row per analysis added, changed or removed.
    """
    changed = {}
    for p in (FIXTURE / "versions").iterdir():
        changes = p / "changes.tsv"
        changed[p.name] = not changes.exists() or len(changes.read_text().splitlines()) > 1
    return changed


def test_every_catalogue_version_that_changed_something_gets_a_news_item(site):
    out, _ = site
    news = (out / "news/index.html").read_text()
    feed = (out / "news/feed.xml").read_text()
    for v, changed in catalogue_versions().items():
        if changed:
            assert f"/news/catalogue-{v}/" in news
            assert f"/news/catalogue-{v}/" in feed


def test_a_catalogue_version_that_changed_nothing_gets_no_news_item(site):
    out, _ = site
    unchanged = [v for v, changed in catalogue_versions().items() if not changed]
    assert unchanged, "expected a test catalogue version that changed no listed analysis"
    news = (out / "news/index.html").read_text()
    feed = (out / "news/feed.xml").read_text()
    for v in unchanged:
        assert f"/news/catalogue-{v}/" not in news
        assert f"/news/catalogue-{v}/" not in feed
        assert not (out / f"news/catalogue-{v}").exists()
    assert "No changes to listed analyses" not in news


def test_draft_posts_are_left_out_unless_asked_for(site, tmp_path):
    out, _ = site
    drafts = [p for p in (Path(__file__).parent.parent / "content/news").glob("*.md")
              if "draft: true" in p.read_text()]
    assert drafts, "expected the example draft post in content/news/"
    slug = drafts[0].stem
    assert not (out / "news" / slug).exists()
    with_drafts = tmp_path / "_site"
    build(FIXTURE, with_drafts, drafts=True)
    assert (with_drafts / "news" / slug / "index.html").is_file()


def test_sitemap_lists_pages_but_not_error_pages(site):
    out, result = site
    urls = re.findall(r"<loc>([^<]+)</loc>", (out / "sitemap-1.xml").read_text())
    assert len(urls) == result["pages"]
    assert not any("404" in u for u in urls)


def test_link_checker_finds_broken_links(site, tmp_path):
    out, _ = site
    page = tmp_path / "about" / "index.html"
    page.parent.mkdir()
    page.write_text('<a href="/nowhere/">x</a> <a href="/about/#missing">y</a> <a href="about/">z</a>'
                    '<p id="here"></p><a href="#here">ok</a>')
    problems = check(tmp_path)
    assert len(problems) == 3, problems


def test_markdown_keeps_legal_clause_markers():
    html = content.markdown("See clause (c) and (r).")
    assert "(c)" in html and "©" not in html and "®" not in html


def test_pages_need_a_title(tmp_path):
    (tmp_path / "untitled.md").write_text("---\nlede: no title\n---\nBody\n")
    with pytest.raises(ValueError, match="needs a title"):
        content.load(tmp_path)


def test_catalogue_versions_are_published_with_checksums(site):
    import hashlib, json
    out, _ = site
    current = json.loads((out / "data/catalog/current.json").read_text())
    assert current["version"] == (FIXTURE / "current").resolve().name
    for name, f in current["files"].items():
        local = out / f["url"].split("://", 1)[1].split("/", 1)[1]
        assert hashlib.sha256(local.read_bytes()).hexdigest() == f["sha256"], name
    for v in (FIXTURE / "versions").iterdir():
        assert (out / "data/catalog" / v.name / "catalog.sqlite").is_file()
        assert (out / "data/catalog" / v.name / "SHA256SUMS").is_file()
