"""python -m sitegen build | serve | check

The catalogue defaults to $OPENGWAS_CATALOG, or else the OpenGWAS server's
copy at /data/opengwasdb/stores/catalog. Elsewhere, point it at the small
test catalogue: --catalog tests/fixtures/catalog
"""
import argparse
import os
import sys
from pathlib import Path

from .build import ROOT, build
from .check import check
from .serve import serve

DEFAULT_CATALOG = os.environ.get("OPENGWAS_CATALOG", "/data/opengwasdb/stores/catalog")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sitegen", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_ in [("build", "build the site"), ("serve", "build, serve and rebuild on change"),
                        ("check", "check internal links in a built site")]:
        p = sub.add_parser(name, help=help_)
        p.add_argument("--out", type=Path, default=ROOT / "_site", help="output directory (default: _site)")
        if name != "check":
            p.add_argument("--catalog", type=Path, default=Path(DEFAULT_CATALOG),
                           help=f"Analysis Catalog root (default: {DEFAULT_CATALOG})")
        if name == "build":
            p.add_argument("--drafts", action="store_true", help="include news posts marked draft: true")
        if name == "serve":
            p.add_argument("--port", type=int, default=8000)
            p.add_argument("--no-drafts", action="store_true", help="hide news posts marked draft: true")
    args = ap.parse_args(argv)

    if args.cmd == "build":
        r = build(args.catalog, args.out, drafts=args.drafts)
        print(f"built {r['pages']:,} pages ({r['analyses']:,} Analyses, {r['stores']} Stores) "
              f"from catalogue {r['catalogue']} in {r['seconds']} s -> {args.out}")
    elif args.cmd == "serve":
        serve(args.catalog, args.out, args.port, drafts=not args.no_drafts)
    elif args.cmd == "check":
        problems = check(args.out)
        for p in problems[:200]:
            print(p)
        if problems:
            sys.exit(f"{len(problems)} broken internal links")
        print(f"all internal links in {args.out} resolve")


if __name__ == "__main__":
    main()
