"""Check that every internal link and asset in a built site resolves.

A link resolves if the file it points at exists in the build, and, when it
has a #fragment, that page has an element with that id.
"""
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit

REF = re.compile(r'''\b(?:href|src)="([^"]*)"''')
ID = re.compile(r'''\bid="([^"]+)"''')


def check(site: Path) -> list[str]:
    site = Path(site)

    def target(path: str) -> Path:
        p = site / unquote(path).lstrip("/")
        return p / "index.html" if path.endswith("/") else p

    @lru_cache(maxsize=4096)
    def ids(page: Path) -> frozenset:
        return frozenset(ID.findall(page.read_text(encoding="utf-8")))

    problems = []
    for page in sorted(site.rglob("*.html")):
        here = "/" + page.relative_to(site).as_posix()
        for ref in REF.findall(page.read_text(encoding="utf-8")):
            ref = ref.replace("&amp;", "&")
            parts = urlsplit(ref)
            if parts.scheme or parts.netloc or ref.startswith(("mailto:", "tel:", "data:")):
                continue
            if parts.path and not parts.path.startswith("/"):
                problems.append(f"{here}: relative link {ref!r} (use a path from the site root)")
                continue
            dest = target(parts.path) if parts.path else page
            if not dest.is_file():
                problems.append(f"{here}: {ref} does not exist")
            elif parts.fragment and dest.suffix == ".html" and parts.fragment not in ids(dest):
                problems.append(f"{here}: {ref} has no element with id {parts.fragment!r}")
    return problems
