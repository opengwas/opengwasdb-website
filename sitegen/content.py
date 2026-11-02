"""Markdown files with YAML front matter.

Every `.md` file under content/ becomes one page, at the URL its path gives:

    content/about.md                     -> /about/
    content/legal/terms.md               -> /legal/terms/
    content/news/2026-11-10-finngen.md   -> /news/2026-11-10-finngen/

Files and folders whose names start with `_` are skipped.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin

FRONT = re.compile(r"\A---\n(.*?)\n---\n?", re.S)

# CommonMark plus tables and curly quotes. The "replacements" rule is left off
# on purpose: it would turn legal clause markers such as "(c)" into "©".
_md = (MarkdownIt("commonmark", {"typographer": True})
       .enable(["table", "strikethrough", "smartquotes"])
       .use(anchors_plugin, min_level=2, max_level=3))


def markdown(text: str) -> str:
    return _md.render(text)


def markdown_inline(text: str) -> str:
    return _md.renderInline(text)


@dataclass
class Page:
    path: Path                 # relative to content/
    url: str
    meta: dict = field(default_factory=dict)
    body: str = ""             # Markdown

    @property
    def title(self) -> str:
        return self.meta["title"]

    @property
    def section(self) -> str:
        return self.url.strip("/").split("/")[0]


def read(path: Path, root: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    meta = yaml.safe_load(m.group(1)) if m else {}
    body = text[m.end():] if m else text
    rel = path.relative_to(root)
    if "title" not in meta:
        raise ValueError(f"{rel}: front matter needs a title")
    if rel.parts[0] == "news" and "date" not in meta:
        raise ValueError(f"{rel}: news posts need a date")
    url = "/" + "/".join(rel.with_suffix("").parts) + "/"
    return Page(path=rel, url=url, meta=meta, body=body)


def load(root: Path, drafts: bool = False) -> list[Page]:
    pages = []
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith("_") for part in path.relative_to(root).parts):
            continue
        page = read(path, root)
        if page.meta.get("draft") and not drafts:
            continue
        pages.append(page)
    return pages
