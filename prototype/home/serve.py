"""PROTOTYPE: rebuild summary.json from the catalogue, then serve this folder.

    python3 prototype/home/serve.py [port]      # default 8765

Open http://localhost:8765/ (variant D; ?variant=A, B or C for the others).
Arrow keys switch variants. Off the OpenGWAS server the catalogue is not
reachable, so it serves the committed summary.json snapshot instead.
"""
import functools
import http.server
import sys
from pathlib import Path

import build_summary

HERE = Path(__file__).parent
try:
    build_summary.main()
except Exception as e:  # noqa: BLE001 (prototype: any failure means "use the snapshot")
    print(f"catalogue not reachable ({e}); serving the committed summary.json")
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
print(f"serving http://localhost:{port}/")
http.server.ThreadingHTTPServer(("", port), handler).serve_forever()
