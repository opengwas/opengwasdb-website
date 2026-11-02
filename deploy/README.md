# Hosting the site

The site and its catalogue files are served by nginx, built for a container and
for now run natively (decision 14). The development host is the OpenGWAS build
server in Bristol, reachable inside the University network and over VPN:

```text
http://app-dc3-ogws-p0.services.bris.ac.uk:8080/
```

## How it fits together

```text
cron, every 5 min ──▶ deploy/update.sh (in /data/opengwasdb/website/repo, a checkout used only for hosting)
                        1. make sure nginx is running
                        2. if the branch or the catalogue's `current` changed:
                             make the catalogue copy built for browsing  (interim: scripts/make_browse_catalog.py)
                             build the site into staging/, check every link
                             move it to www/releases/<time>-<commit>, switch www/site to it in one rename
nginx ──▶ serves www/site, including /data/catalog/<version>/catalog.sqlite (range requests, no gzip)
```

Everything lives in `/data/opengwasdb/website/`:

| Path | What |
|---|---|
| `repo/` | The hosting checkout. Never edit it; push to the branch instead. |
| `catalog/` | The browsing copy of the Analysis Catalog. Only its current version is a copy; the rest link to the real catalogue. |
| `www/site` | A link to the release being served |
| `www/releases/` | The current release and the one before it |
| `run/` | The native nginx's config, pid, logs (`access.log`, `error.log`) |
| `logs/update.log` | What each rebuild did |

## Commands

From the hosting checkout:

```sh
pixi run -e web web-status     # is it up?
pixi run -e web web-reload     # after changing deploy/site.conf.template
pixi run -e web web-stop
deploy/update.sh               # rebuild now, if anything changed
```

- **Roll back:** point the link at the previous release with
  `ln -sfn releases/<previous> www/site.next && mv -T www/site.next www/site`.
- **Force a rebuild:** delete `/data/opengwasdb/website/.built`.

## Moving to the container

Once someone with Docker access is available:

```sh
pixi run -e web web-stop
docker compose -f deploy/compose.yaml up -d --build
```

Then change the crontab line to set `OPENGWAS_WEB_SERVER=container`, so the job
stops starting the native nginx. Both read the same `deploy/site.conf.template`
and serve the same `www/` folder, so nothing else changes.

For production, the same container can either:
- run on the opengwas.io VM, with each release copied there from Bristol; or
- stay here behind a public proxy.

That's decided at launch (opengwas/opengwasdb-website#5).

## What the server must do

The site's needs from its server are listed in `CONTRIBUTING.md` under
"Publishing". `site.conf.template` covers all of them except HTTPS and HTTP/2,
which belong to whatever faces the public.
