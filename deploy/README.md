# Hosting the site

The site and its catalogue files are served by nginx in a container
(decision 14). The development host is the OpenGWAS build server in Bristol:

```text
http://app-dc3-ogws-p0.services.bris.ac.uk:8080/
```

If the server's firewall blocks port 8080 from where you are, forward it over
SSH and open <http://localhost:8080/>:

```sh
ssh -N -L 8080:localhost:8080 app-dc3-ogws-p0.services.bris.ac.uk
```

## How it fits together

```text
cron, every 5 min ──▶ deploy/update.sh (in /data/opengwasdb/website/repo, a checkout used only for hosting)
                        if the branch or the catalogue's `current` changed:
                             build the site into staging/ from the Analysis Catalog, check every link
                             move it to www/releases/<time>-<commit>, switch www/site to it in one rename
nginx ──▶ serves www/site, including /data/catalog/<version>/catalog.sqlite (range requests, no gzip)
```

Everything lives in `/data/opengwasdb/website/`:

| Path | What |
|---|---|
| `repo/` | The hosting checkout. Never edit it; push to the branch instead. |
| `www/site` | A link to the release being served |
| `www/releases/` | The current release and the one before it |
| `run/` | The native nginx's config, pid and logs, when it runs without Docker |
| `logs/update.log` | What each rebuild did |

## Commands

From the hosting checkout:

```sh
docker compose -f deploy/compose.yaml up -d --build   # start, or apply a change to deploy/
docker compose -f deploy/compose.yaml logs web        # requests and errors
docker compose -f deploy/compose.yaml down
deploy/update.sh                                      # rebuild now, if anything changed
```

The crontab line, which publishes `main`:

```text
*/5 * * * * /data/opengwasdb/website/repo/deploy/update.sh >> /data/opengwasdb/website/logs/update.log 2>&1
```

A rebuild needs nothing from the container: the site link changes under its
read-only mount, and the next request sees the new release.

- **Roll back:** point the link at the previous release with
  `ln -sfn releases/<previous> www/site.next && mv -T www/site.next www/site`.
- **Force a rebuild:** delete `/data/opengwasdb/website/.built`.

## Without Docker

The same server block runs natively through pixi, from the same `www/` folder:

```sh
docker compose -f deploy/compose.yaml down
pixi run -e web web-start      # also web-status, web-reload, web-stop
```

Then set `OPENGWAS_WEB_SERVER=native` at the start of the crontab line, so each
run restarts nginx if it has stopped.

## Production

For production, the same container can either:
- run on the opengwas.io VM, with each release copied there from Bristol; or
- stay here behind a public proxy.

That's decided at launch (opengwas/opengwasdb-website#5).

## What the server must do

The site's needs from its server are listed in `CONTRIBUTING.md` under
"Publishing". `site.conf.template` covers all of them except HTTPS and HTTP/2,
which belong to whatever faces the public.
