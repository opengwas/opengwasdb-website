"""The LD resources list at /data/ld/ and one page per OGL id, from the catalogue's ld_resources table."""
import re
import shutil
import sqlite3
from pathlib import Path

import pytest

from sitegen.build import build
from sitegen.catalog import Catalog
from sitegen.check import check

FIXTURE = Path(__file__).parent / "fixtures" / "catalog"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("ld") / "_site"
    build(FIXTURE, out)
    return out


@pytest.fixture(scope="module")
def without_table(tmp_path_factory):
    """The test catalogue with ld_resources dropped, as a catalogue built before #537 has it."""
    root = tmp_path_factory.mktemp("old")
    catalog = root / "catalog"
    shutil.copytree(FIXTURE, catalog, symlinks=True)
    for db in catalog.glob("versions/*/catalog.sqlite"):
        with sqlite3.connect(db) as d:
            d.execute("drop table ld_resources")
    out = root / "_site"
    build(catalog, out)
    return catalog, out


# 1. The reader

def test_the_reader_returns_every_row():
    rows = Catalog(FIXTURE).ld_resources()
    assert len(rows) == 18
    assert {r["kind"] for r in rows} == {"ld_store", "genotype_store", "ld_panel"}
    ukb = next(r for r in rows if r["ld_id"] == "OGL-00013")
    assert ukb["n_variants"] is None and ukb["store_bytes"] is None


def test_a_catalogue_without_the_table_is_unavailable_not_an_error(without_table):
    catalog, _ = without_table
    assert Catalog(catalog).ld_resources() is None


# 2. The build

def test_the_list_and_a_page_per_row_exist(site):
    assert (site / "data/ld/index.html").is_file()
    for r in Catalog(FIXTURE).ld_resources():
        assert (site / "data/ld" / r["ld_id"] / "index.html").is_file(), r["ld_id"]
    assert check(site) == []


def test_the_list_is_grouped_by_kind_and_linked_from_data(site):
    html = (site / "data/ld/index.html").read_text()
    main = html[html.index("<main"):html.index("</main>")]
    headings = re.findall(r"<h2>([^<]+)</h2>", main)
    assert headings == ["LD Stores", "Genotype Stores", "LD panels"]
    assert 'href="/data/ld/OGL-00001/"' in html
    assert 'href="/data/ld/"' in (site / "data/index.html").read_text()
    assert "/data/ld/" in (site / "sitemap-1.xml").read_text()


def test_a_genotype_store_row_shows_both_sizes(site):
    nb = "\u00a0"
    html = (site / "data/ld/index.html").read_text()
    row = html[html.index("OGL-00007"):]
    row = row[:row.index("</tr>")]
    assert f"1.5{nb}GB" in row and f"4.1{nb}GB" in row
    assert f"4.1{nb}GB" in (site / "data/ld/OGL-00007/index.html").read_text()


def test_a_page_has_provenance_and_a_link_to_its_record(site):
    html = (site / "data/ld/OGL-00001/index.html").read_text()
    for text in ("3,000,000", "10,000,000", "GRCh38", "ogld 0.0.1.dev292", "13 November 2026"):
        assert text in html, text
    assert 'href="https://github.com/opengwas/opengwasdb-stores/blob/main/stores/ld/OGL-00001/record.yaml"' in html


VIGNETTE = "https://github.com/opengwas/opengwasr/blob/main/vignettes/ld.Rmd"


def test_served_and_retiring_rows_say_how_to_use_them_and_others_do_not(site):
    for ld_id, label in (("OGL-00001", "hgdp1kgp-v2-EUR-k10"), ("OGL-00002", "hgdp1kgp-v2-AFR-k10")):
        html = (site / "data/ld" / ld_id / "index.html").read_text()
        assert "Using it" in html and VIGNETTE in html, ld_id
        assert f"<code>{label}</code>" in html and f"<code>{ld_id}</code>" in html, ld_id
        # No endpoints (decisions.md), and no ancestry to pass: that picks the ancestry's default store.
        assert "/api/" not in html and "og_ld_stores" not in html and "ld = " not in html, ld_id
    for ld_id in ("OGL-00006", "OGL-00007", "OGL-00013"):
        assert "Using it" not in (site / "data/ld" / ld_id / "index.html").read_text(), ld_id


def test_ancestry_is_named_as_elsewhere_on_the_site(site):
    page = (site / "data/ld/OGL-00001/index.html").read_text()
    assert "European" in page and "European ancestry" in page
    assert "EUR ancestry" not in page
    html = (site / "data/ld/index.html").read_text()
    assert "<td>European</td>" in html and "<td>EUR</td>" not in html


def test_t_far_keeps_every_digit_the_catalogue_holds(site):
    assert "0.03186544342507645" in (site / "data/ld/OGL-00001/index.html").read_text()


# 3. NULL

def test_a_null_value_is_shown_as_not_recorded(site):
    page = (site / "data/ld/OGL-00013/index.html").read_text()
    assert "Not recorded" in page
    assert "<dd>0</dd>" not in page and "<dd></dd>" not in page
    html = (site / "data/ld/index.html").read_text()
    row = html[html.index("OGL-00013"):]
    row = row[:row.index("</tr>")]
    assert row.count("Not recorded") >= 2  # variant count and size
    assert "<td></td>" not in html and '<td class="num"></td>' not in html


# 4. Degradation

def test_a_catalogue_without_the_table_still_builds_and_says_so(without_table):
    _, out = without_table
    assert not (out / "data/ld").exists()
    data = (out / "data/index.html").read_text()
    assert "LD resources are unavailable" in data
    assert 'href="/data/ld/"' not in data
    assert check(out) == []


# 5. NULLs everywhere, and kinds the site doesn't know


def edited(tmp_path_factory, sql):
    root = tmp_path_factory.mktemp("edited")
    catalog = root / "catalog"
    shutil.copytree(FIXTURE, catalog, symlinks=True)
    for db in catalog.glob("versions/*/catalog.sqlite"):
        with sqlite3.connect(db) as d:
            d.execute(sql)
    return catalog, root / "_site"


def test_a_row_with_nothing_but_its_id_renders_not_recorded_everywhere(tmp_path_factory):
    nulls = ", ".join(f'"{c}" = NULL' for c in ("label", "ancestry", "source_panel", "n", "licence",
                                              "used_for", "created_at", "record", "t_far", "near_bp", "built_with"))
    catalog, out = edited(tmp_path_factory, f"update ld_resources set {nulls} where ld_id = 'OGL-00001'")
    build(catalog, out)
    page = (out / "data/ld/OGL-00001/index.html").read_text()
    assert "None" not in page and "<dd></dd>" not in page and "<dd>0</dd>" not in page
    assert "Using it" in page and "Not recorded" in page
    assert "<code>OGL-00001</code>" in page and "pass its id" in page
    assert check(out) == []


def test_a_kind_the_site_does_not_know_fails_the_build_naming_it(tmp_path_factory):
    catalog, out = edited(tmp_path_factory, "update ld_resources set kind = 'ld_tensor' where ld_id = 'OGL-00001'")
    with pytest.raises(ValueError, match="ld_tensor.*OGL-00001|OGL-00001.*ld_tensor"):
        build(catalog, out)
