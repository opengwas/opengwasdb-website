"""Whole-store downloads: each Store Archive's facts on its store's page, from the catalogue's store_archives table."""
import shutil
import sqlite3
from pathlib import Path

import pytest
import yaml

from sitegen.build import build
from sitegen.catalog import Catalog
from sitegen.check import check

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "catalog"
SHA = "9f2c" * 16

ARCHIVES = [
    # id, release_id, file, bytes, sha256, created_at
    ("OGS-00009", "4b1e6f0a", "OGS-00009-4b1e6f0a.tar", 61_463_374_061, SHA, "2026-11-27T10:00:00+00:00"),
    ("OGL-00007", None, "OGL-00007.tar", 5_613_571_291, SHA, "2026-11-27T11:00:00+00:00"),
]


def with_archives(tmp_path_factory):
    """The test catalogue with a store_archives table holding ARCHIVES."""
    root = tmp_path_factory.mktemp("archives")
    catalog = root / "catalog"
    shutil.copytree(FIXTURE, catalog, symlinks=True)
    for db in catalog.glob("versions/*/catalog.sqlite"):
        with sqlite3.connect(db) as d:
            d.execute("create table store_archives (id text primary key, release_id text, file text not null,"
                      " bytes integer not null, sha256 text not null, created_at text not null)")
            d.executemany("insert into store_archives values (?, ?, ?, ?, ?, ?)", ARCHIVES)
    return catalog


def site_root(tmp_path_factory, live: bool) -> Path:
    """A copy of the site's sources with downloads switched on or off."""
    root = tmp_path_factory.mktemp("root")
    for name in ("templates", "static", "content"):
        (root / name).symlink_to(ROOT / name)
    shutil.copytree(ROOT / "data", root / "data")
    site = yaml.safe_load((root / "data/site.yaml").read_text())
    site["downloads"]["live"] = live
    (root / "data/site.yaml").write_text(yaml.safe_dump(site))
    return root


@pytest.fixture(scope="module")
def soon(tmp_path_factory):
    out = tmp_path_factory.mktemp("soon") / "_site"
    build(with_archives(tmp_path_factory), out, root=site_root(tmp_path_factory, live=False))
    return out


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    out = tmp_path_factory.mktemp("live") / "_site"
    build(with_archives(tmp_path_factory), out, root=site_root(tmp_path_factory, live=True))
    return out


def test_a_store_release_page_shows_its_archive(soon):
    html = (soon / "data/stores/OGS-00009/index.html").read_text()
    for text in ("OGS-00009-4b1e6f0a.tar", "61 GB", "<code>4b1e6f0a</code>", "27 November 2026", SHA):
        assert text in html, text
    assert 'href="/data/#download"' in html


def test_an_ld_resource_page_shows_its_archive_without_a_release(soon):
    html = (soon / "data/ld/OGL-00007/index.html").read_text()
    assert "OGL-00007.tar" in html and "5.6 GB" in html and SHA in html
    assert "<dt>Release</dt>" not in html[html.index('id="download"'):]


def test_a_store_without_an_archive_shows_no_download_block(soon):
    for page in ("data/stores/OGS-00006/index.html", "data/ld/OGL-00008/index.html"):
        assert 'id="download"' not in (soon / page).read_text(), page


def test_a_catalogue_without_the_table_has_no_archives():
    assert Catalog(FIXTURE).store_archives() == {}


def tab(site):
    html = (site / "data/index.html").read_text()
    start = html.index('id="download"')
    return html[start:html.index("</section>", start)]


def test_until_downloads_open_the_tab_says_coming_soon_and_links_no_tool(soon):
    t = tab(soon)
    assert "coming soon" in t and "OpenGWAS account" in t
    assert "opengwasr (R) or opengwaspy (Python)" in t
    assert 'href="https://github.com/opengwas/opengwasr"' not in t
    assert "coming soon" in (soon / "data/stores/OGS-00009/index.html").read_text()


def test_once_downloads_open_the_tab_links_the_tools(live):
    t = tab(live)
    assert "coming soon" not in t
    assert 'href="https://github.com/opengwas/opengwasr"' in t and 'href="https://github.com/opengwas/opengwaspy"' in t
    page = (live / "data/stores/OGS-00009/index.html").read_text()
    assert "coming soon" not in page and "How to download" in page


def test_the_site_names_no_endpoint_or_token(soon, live):
    for site in (soon, live):
        for page in ("data/index.html", "data/stores/OGS-00009/index.html", "data/ld/OGL-00007/index.html"):
            html = (site / page).read_text()
            assert "/api/" not in html and "token" not in html.lower() and "jwt" not in html.lower(), page


def test_links_resolve(soon, live):
    assert check(soon) == [] and check(live) == []
