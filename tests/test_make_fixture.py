"""scripts/make_fixture_catalog.py: the ld_resources copy fails loudly rather than leaving the fixture without it."""
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "make_fixture_catalog.py"
spec = importlib.util.spec_from_file_location("make_fixture_catalog", SCRIPT)
script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script)


def database(path, ddl=None, rows=()):
    with sqlite3.connect(path) as d:
        if ddl:
            d.execute(ddl)
            d.executemany("insert into ld_resources values (?)", rows)
    return path


def test_a_source_without_the_table_is_an_error(tmp_path):
    src, dest = database(tmp_path / "src.sqlite"), database(tmp_path / "dest.sqlite")
    with pytest.raises(SystemExit, match="no ld_resources"):
        script.copy_ld_resources(src, dest)


def test_an_empty_table_is_an_error(tmp_path):
    src = database(tmp_path / "src.sqlite", "create table ld_resources (ld_id text)")
    with pytest.raises(SystemExit, match="no rows"):
        script.copy_ld_resources(src, database(tmp_path / "dest.sqlite"))


def test_the_rows_are_copied(tmp_path):
    src = database(tmp_path / "src.sqlite", "create table ld_resources (ld_id text)", [("OGL-1",), ("OGL-2",)])
    dest = database(tmp_path / "dest.sqlite")
    script.copy_ld_resources(src, dest)
    assert sqlite3.connect(dest).execute("select count(*) from ld_resources").fetchone() == (2,)


@pytest.mark.parametrize("flag", [["--catalog", "x"], ["--per-store", "2"]])
def test_ld_only_refuses_options_it_would_ignore(flag, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["make_fixture_catalog", "--ld-only", "--ld-catalog", "y", *flag])
    with pytest.raises(SystemExit) as e:
        script.main()
    assert e.value.code == 2
