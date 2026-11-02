"""Run the web server natively, with the same server block as the container.

    pixi run -e web web-start     # fill in the template, test the config, start nginx
    pixi run -e web web-reload    # after a config change; a site rebuild needs nothing
    pixi run -e web web-stop
    pixi run -e web web-status
    pixi run -e web python deploy/web.py ensure   # start it only if it isn't running

Settings, from the environment:
    OPENGWAS_WEB_ROOT   the folder holding the built site in site/  (/data/opengwasdb/website/www)
    OPENGWAS_WEB_RUN    nginx's own files: config, pid, logs, temp  (/data/opengwasdb/website/run)
    OPENGWAS_WEB_PORT   the port                                   (8080)
"""
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = Path(sys.prefix)  # the pixi "web" environment, which holds nginx
NGINX = PREFIX / "bin" / "nginx"
WEB_ROOT = Path(os.environ.get("OPENGWAS_WEB_ROOT", "/data/opengwasdb/website/www"))
RUN = Path(os.environ.get("OPENGWAS_WEB_RUN", "/data/opengwasdb/website/run"))
PORT = os.environ.get("OPENGWAS_WEB_PORT", "8080")
CONF = RUN / "nginx.conf"


def render() -> None:
    """Write nginx.conf and site.conf into RUN, filling in the template as the container does."""
    values = {"WEB_ROOT": str(WEB_ROOT), "LISTEN_PORT": PORT}
    site = re.sub(r"\$\{(\w+)\}", lambda m: values.get(m.group(1), m.group(0)),
                  (HERE / "site.conf.template").read_text())
    for d in ("tmp/client", "tmp/proxy", "tmp/fastcgi", "tmp/uwsgi", "tmp/scgi"):
        (RUN / d).mkdir(parents=True, exist_ok=True)
    (RUN / "site.conf").write_text(site)
    CONF.write_text(f"""# Written by deploy/web.py; edit deploy/site.conf.template instead.
worker_processes 4;
pid {RUN}/nginx.pid;
error_log {RUN}/error.log warn;
events {{ worker_connections 1024; }}
http {{
    include {PREFIX}/etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    access_log {RUN}/access.log;
    client_body_temp_path {RUN}/tmp/client;
    proxy_temp_path {RUN}/tmp/proxy;
    fastcgi_temp_path {RUN}/tmp/fastcgi;
    uwsgi_temp_path {RUN}/tmp/uwsgi;
    scgi_temp_path {RUN}/tmp/scgi;
    include {RUN}/site.conf;
}}
""")


def nginx(*args) -> int:
    # -e: nginx opens its error log before reading the config, so name it up front.
    return subprocess.run([str(NGINX), "-p", str(RUN), "-e", str(RUN / "error.log"), "-c", str(CONF), *args]).returncode


def running() -> bool:
    try:
        pid = int((RUN / "nginx.pid").read_text())
        os.kill(pid, 0)
        return True
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        return False


def main(cmd: str) -> int:
    if cmd in ("start", "ensure"):
        if running():
            print(f"already running on port {PORT}" if cmd == "start" else "", end="")
            return 0
        render()
        if nginx("-t", "-q"):
            return 1
        rc = nginx()
        if rc == 0:
            print(f"serving {WEB_ROOT}/site on port {PORT}")
        return rc
    if cmd == "reload":
        if not running():
            return main("start")
        render()
        return nginx("-t", "-q") or nginx("-s", "reload")
    if cmd == "stop":
        return nginx("-s", "quit") if running() else 0
    if cmd == "status":
        if not running():
            print("not running")
            return 1
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=5) as r:
                print(f"running on port {PORT}: / answers {r.status}")
        except Exception as e:  # noqa: BLE001
            print(f"running on port {PORT}, but / fails: {e}")
            return 1
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
