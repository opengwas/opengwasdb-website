"""The Data page's search, in headless Chromium, against the test catalogue.

Each check compares what the page shows with the same question asked of the
catalogue directly, through Python's SQLite.

    pixi run -e browser install-browser   (once)
    pixi run -e browser test-browser
"""
import functools
import http.server
import re
import shutil
import sqlite3
import threading
from pathlib import Path

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from sitegen.build import build  # noqa: E402
from sitegen.serve import Handler  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "catalog"
BUSY = ("!document.getElementById('search').hasAttribute('aria-busy') && "
        "!/Counting|Searching|Opening/.test(document.querySelector('[data-status]').textContent)")


def ask(sql, *args):
    db = sqlite3.connect(f"file:{(FIXTURE / 'current' / 'catalog.sqlite').resolve()}?mode=ro", uri=True)
    return db.execute(sql, args).fetchall()


def with_browse_indexes(tmp):
    """A copy of the test catalogue as decision 13 proposes it: 32 KB pages,
    the covering indexes, and an optimised search index."""
    root = tmp / "catalog"
    shutil.copytree(FIXTURE, root, symlinks=True)
    db = sqlite3.connect((root / "current" / "catalog.sqlite").resolve())
    db.execute("pragma page_size = 32768")
    db.executescript((ROOT / "scripts" / "catalogue_browse_indexes.sql").read_text())
    db.execute("insert into analysis_search(analysis_search) values ('optimize')")
    db.commit()
    db.execute("vacuum")
    db.close()
    return root


# Every test runs against the catalogue as published and as decision 13 proposes.
@pytest.fixture(scope="module", params=["as published", "with browse indexes"])
def base(request, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("browser")
    catalog = FIXTURE if request.param == "as published" else with_browse_indexes(tmp)
    out = tmp / "_site"
    build(catalog, out)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(out)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser, base):
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.base = base
    yield pg
    assert pg.errors == []
    ctx.close()


def shown_ids(pg):
    pg.wait_for_function(BUSY, timeout=30000)
    hrefs = pg.locator("[data-rows] td.an a").evaluate_all("as => as.map(a => a.getAttribute('href'))")
    return [":".join(re.match(r"/data/analyses/([^/]+)/([^/]+)/", h).groups()) for h in hrefs]


def status(pg):
    return pg.inner_text("[data-status]")


def test_first_page_is_in_the_html_and_the_controls_come_alive(page):
    page.goto(page.base + "/data/")
    expected = [r[0] for r in ask("select id from listed_analyses order by sample_size desc, id desc limit 25")]
    assert shown_ids(page) == expected
    assert page.is_enabled("#q")
    (total,) = ask("select count(*) from listed_analyses")[0]
    assert f"{total:,} analyses" in status(page)


def test_next_page_continues_the_listing(page):
    page.goto(page.base + "/data/")
    page.click("[data-next]")
    expected = [r[0] for r in ask("select id from listed_analyses order by sample_size desc, id desc limit 25 offset 25")]
    assert shown_ids(page) == expected
    assert "page=2" in page.url


def test_search_matches_the_full_text_index(page):
    (label,) = ask("select analysis_label from listed_analyses where analysis_label glob '[A-Z][a-z][a-z][a-z]*' limit 1")[0]
    word = re.match(r"[A-Za-z]+", label).group(0)
    page.goto(page.base + "/data/")
    page.fill("#q", word)
    page.press("#q", "Enter")
    expected = {r[0] for r in ask(
        "select a.id from analysis_search s join analyses a on a.rowid = s.rowid "
        "where analysis_search match ? and a.listed = 1", f'"{word}"*')}
    assert expected and set(shown_ids(page)) == expected
    assert f"matching “{word}”" in status(page)


def test_filters_sort_and_counts_agree_with_the_catalogue(page):
    (store,) = ask("select store_id from listed_analyses group by store_id order by store_id limit 1")[0]
    page.goto(page.base + f"/data/?store={store}&sort=name")
    expected = [r[0] for r in ask(
        "select id from listed_analyses where store_id = ? order by analysis_label, id", store)]
    assert shown_ids(page) == expected
    assert f"{len(expected):,} analys" in status(page)
    # The other filters' options count only within this Store.
    (n_eur,) = ask("select count(*) from listed_analyses where store_id = ? and ancestry_category = 'EUR'", store)[0]
    option = page.locator("select[name=ancestry] option[value=EUR]").inner_text()
    assert option.endswith(f"({n_eur:,})")


def test_impossible_combinations_say_so_without_a_query(page):
    page.goto(page.base + "/data/?tissue=whole_blood&outcome=binary")
    page.wait_for_function(BUSY)
    assert status(page) == "No analyses match these filters."
    assert shown_ids(page) == []


def test_the_back_button_restores_the_previous_results(page):
    page.goto(page.base + "/data/")
    first = shown_ids(page)
    page.select_option("select[name=sort]", "name")
    shown_ids(page)
    page.go_back()
    assert shown_ids(page) == first


def test_without_javascript_the_first_page_still_shows(browser, base):
    ctx = browser.new_context(java_script_enabled=False)
    pg = ctx.new_page()
    pg.goto(base + "/data/")
    assert pg.locator("[data-rows] tr").count() == 25
    assert pg.locator("noscript").count() == 1
    assert not pg.is_enabled("#q")
    ctx.close()
