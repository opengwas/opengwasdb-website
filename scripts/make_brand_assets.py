"""Make the site's logo, favicon and link-preview image from the designer's logo files.

    pixi run -e browser make-brand PATH/TO/opengwas-logo-v2

PATH holds the designer's SVGs: logo-text-colour.svg (the mark and the
wordmark), logo-colour.svg (the mark) and logo-1-colour.svg (one disc).

The SVGs were traced from a raster, and the tracing left thin slivers of the
wrong colour along the edges of the shapes. This keeps only the shapes at least
MIN_SIZE units across in both directions (6 half-discs and 8 letters in the
full logo) and writes each with a plain fill, so the output holds nothing but
shapes. It stops if a file doesn't have the shapes it should.

Writes, in static/img/:
  logo.svg              the header logo
  favicon.ico           one disc at 16 px, where the whole mark is a blur; the whole mark at 32 and 48 px
  apple-touch-icon.png  the mark on white, 180 px (iOS shows transparency as black)
  og.png                the logo on white, 1200 x 630, for link previews
"""
import base64
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "img"
SVG = "http://www.w3.org/2000/svg"
MIN_SIZE = 4  # viewBox units; the full logo is 192 high, and every real shape is over 40 across
# file: (shapes it must have, output name or None)
SOURCES = {"logo-text-colour.svg": (14, "logo.svg"), "logo-colour.svg": (6, None), "logo-1-colour.svg": (2, None)}


def clean(src: Path, expect: int) -> str:
    """The SVG with only its real shapes, each filled with its colour."""
    root = ET.parse(src).getroot()
    fills = dict(re.findall(r"\.([\w-]+)\s*\{\s*fill:\s*(#[0-9a-fA-F]{3,6})\s*;?\s*\}", "".join(root.itertext())))
    shapes = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag not in ("path", "polygon"):
            continue
        geom = el.get("d") if tag == "path" else el.get("points")
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+(?:[eE]-?\d+)?", geom)]
        xs, ys = nums[0::2], nums[1::2]
        if min(max(xs) - min(xs), max(ys) - min(ys)) < MIN_SIZE:
            continue
        fill = el.get("fill") or fills.get(el.get("class", ""))
        if not fill:
            sys.exit(f"{src.name}: a shape has no fill colour")
        # A tenth of a unit is a fiftieth of a pixel in the header, and halves the file.
        geom = re.sub(r"-?\d*\.\d+", lambda m: f"{float(m.group()):.1f}".removesuffix(".0"), geom)
        shapes.append((tag, "d" if tag == "path" else "points", geom, fill))
    if len(shapes) != expect:
        sys.exit(f"{src.name}: expected {expect} shapes at least {MIN_SIZE} units across, found {len(shapes)}")
    out = [f'<svg xmlns="{SVG}" viewBox="{root.get("viewBox")}"><title>OpenGWAS</title>']
    out += [f'<{tag} fill="{fill}" {attr}="{geom}"/>' for tag, attr, geom, fill in shapes]
    out.append("</svg>\n")
    return "\n".join(out)


def render(page, svg: str, width: int, height: int, fit: float, background: str | None) -> bytes:
    """A PNG of the SVG, scaled to fit `fit` of the canvas and centred."""
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    page.set_viewport_size({"width": width, "height": height})
    page.set_content(
        f'<body style="margin:0;width:{width}px;height:{height}px;display:grid;place-items:center;'
        f'background:{background or "transparent"}"><img src="{uri}" '
        f'style="max-width:{fit * width}px;max-height:{fit * height}px"></body>')
    page.wait_for_function("document.images[0].complete")
    return page.screenshot(omit_background=background is None)


def write_ico(path: Path, images: list[tuple[int, bytes]]) -> None:
    """An .ico of PNG images, one per size."""
    head = struct.pack("<HHH", 0, 1, len(images))
    offset, entries, data = 6 + 16 * len(images), b"", b""
    for size, png in images:
        entries += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    path.write_bytes(head + entries + data)


def main(src_dir: Path) -> None:
    svgs = {}
    for name, (expect, out) in SOURCES.items():
        svgs[name] = clean(src_dir / name, expect)
        if out:
            (OUT / out).write_text(svgs[name])
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        write_ico(OUT / "favicon.ico", [
            (16, render(page, svgs["logo-1-colour.svg"], 16, 16, 1, None)),
            (32, render(page, svgs["logo-colour.svg"], 32, 32, 1, None)),
            (48, render(page, svgs["logo-colour.svg"], 48, 48, 1, None)),
        ])
        (OUT / "apple-touch-icon.png").write_bytes(render(page, svgs["logo-colour.svg"], 180, 180, 0.76, "#fff"))
        (OUT / "og.png").write_bytes(render(page, svgs["logo-text-colour.svg"], 1200, 630, 0.7, "#fff"))
        browser.close()
    for f in ("logo.svg", "favicon.ico", "apple-touch-icon.png", "og.png"):
        print(f"wrote static/img/{f} ({(OUT / f).stat().st_size:,} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
