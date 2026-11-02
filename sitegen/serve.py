"""Preview the site locally: build, serve, and rebuild whenever a source file changes.

Missing pages get the site's 404 page, and missing pages under /datasets/ get
the legacy-ID page, as the live server is set up to do (decision 8).
"""
import functools
import http.server
import threading
import time
import traceback
from pathlib import Path

from .build import ROOT, build

WATCH = ["content", "data", "static", "templates", "sitegen"]


def snapshot(root: Path) -> dict:
    return {p: p.stat().st_mtime for d in WATCH for p in (root / d).rglob("*") if p.is_file()}


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_error(self, code, message=None, explain=None):
        if code == 404:
            root = Path(self.directory)
            page = root / ("datasets/404.html" if self.path.startswith("/datasets/") else "404.html")
            if page.exists():
                body = page.read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        super().send_error(code, message, explain)

    def log_message(self, *args):
        pass


def rebuild(catalog: Path, out: Path, drafts: bool) -> None:
    try:
        r = build(catalog, out, drafts=drafts)
        print(f"built {r['pages']:,} pages in {r['seconds']} s (catalogue {r['catalogue']})", flush=True)
    except Exception:
        traceback.print_exc()
        print("build failed; still serving the last good build", flush=True)


def serve(catalog: Path, out: Path, port: int, drafts: bool = True) -> None:
    rebuild(catalog, out, drafts)
    handler = functools.partial(Handler, directory=str(out))
    server = http.server.ThreadingHTTPServer(("", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"serving http://localhost:{port}/ (drafts {'shown' if drafts else 'hidden'}); Ctrl-C to stop", flush=True)
    seen = snapshot(ROOT)
    try:
        while True:
            time.sleep(1)
            now = snapshot(ROOT)
            if now != seen:
                seen = now
                print("change detected, rebuilding…", flush=True)
                rebuild(catalog, out, drafts)
    except KeyboardInterrupt:
        server.shutdown()
