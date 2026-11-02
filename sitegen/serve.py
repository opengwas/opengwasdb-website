"""Preview the site locally: build, serve, and rebuild whenever a source file changes.

Behaves like the live server where the site depends on it:
- missing pages get the site's 404 page, and missing pages under /datasets/
  get the legacy-ID page (decision 8);
- byte-range requests are answered with 206 Partial Content, which the Data
  page needs to read the catalogue in the browser (decision 7).
"""
import functools
import http.server
import io
import os
import re
import threading
import time
import traceback
from pathlib import Path

from .build import ROOT, build

WATCH = ["content", "data", "static", "templates", "sitegen"]


def snapshot(root: Path) -> dict:
    return {p: p.stat().st_mtime for d in WATCH for p in (root / d).rglob("*") if p.is_file()}


RANGE = re.compile(r"bytes=(\d*)-(\d*)$")


class Handler(http.server.SimpleHTTPRequestHandler):
    # Keep connections open between requests, as a real server does: the Data page
    # makes many small range requests. Without TCP_NODELAY, each response would
    # stall about 40 ms on delayed acknowledgements.
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        """Answer a single byte range with 206; anything else as normal."""
        m = RANGE.match(self.headers.get("Range", "").strip())
        path = self.translate_path(self.path)
        if not m or not os.path.isfile(path):
            return super().send_head()
        with open(path, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            first, last = m.groups()
            if first == "":
                start, end = max(0, size - int(last or 0)), size - 1
            else:
                start, end = int(first), min(int(last), size - 1) if last else size - 1
            if start >= size or start > end:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            f.seek(start)
            body = f.read(end - start + 1)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return io.BytesIO(body)

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
