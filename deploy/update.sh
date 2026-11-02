#!/usr/bin/env bash
# Rebuild the hosted site when its branch or the Analysis Catalog changes, and
# make sure the web server is running (decisions 12 and 14). Run from cron in a
# checkout used only for hosting, never a working copy:
#
#   */5 * * * * /data/opengwasdb/website/repo/deploy/update.sh >> /data/opengwasdb/website/logs/update.log 2>&1
#
# Settings, from the environment:
#   OPENGWAS_WEB_BASE    everything the hosted site uses     (/data/opengwasdb/website)
#   OPENGWAS_WEB_BRANCH  the branch to publish               (main)
#   OPENGWAS_WEB_SERVER  native: keep deploy/web.py's nginx running; container: leave it to Docker
#   OPENGWAS_CATALOG     the Analysis Catalog root           (/data/opengwasdb/stores/catalog)
#
# Layout of OPENGWAS_WEB_BASE:
#   repo/      this checkout
#   catalog/   the catalogue copy built for browsing (scripts/make_browse_catalog.py, interim)
#   www/site   a link to the release being served, in www/releases/ (the previous one is kept)
#   staging/   the next release, until it passes its checks
#   run/       the native nginx's config, pid and logs
set -euo pipefail

BASE=${OPENGWAS_WEB_BASE:-/data/opengwasdb/website}
BRANCH=${OPENGWAS_WEB_BRANCH:-main}
SERVER=${OPENGWAS_WEB_SERVER:-native}
CATALOG=${OPENGWAS_CATALOG:-/data/opengwasdb/stores/catalog}
REPO="$BASE/repo"
export PATH="$HOME/.pixi/bin:$PATH" OPENGWAS_WEB_ROOT="$BASE/www" OPENGWAS_WEB_RUN="$BASE/run"

exec 9>"$BASE/update.lock"
flock -n 9 || exit 0  # a rebuild is already running
cd "$REPO"
say() { echo "$(date -Is) $*"; }

if [ "$SERVER" = native ]; then
  pixi run -q -e web python deploy/web.py ensure
fi

git fetch -q origin "$BRANCH"
want=$(git rev-parse "origin/$BRANCH")
catalogue=$(readlink -f "$CATALOG/current")
built=$(cat "$BASE/.built" 2>/dev/null || true)
[ "$built" = "$want $catalogue" ] && [ -d "$BASE/www/site" ] && exit 0

say "building $BRANCH at ${want:0:7}, catalogue $(basename "$catalogue")"
git checkout -q --detach "$want"
if [ "$(cat "$BASE/.catalog-browse" 2>/dev/null || true)" != "$catalogue" ]; then
  pixi run -q python scripts/make_browse_catalog.py "$CATALOG" "$BASE/catalog"
  echo "$catalogue" > "$BASE/.catalog-browse"
fi
rm -rf "$BASE/staging"
pixi run -q python -m sitegen build --catalog "$BASE/catalog" --out "$BASE/staging/site"
pixi run -q python -m sitegen check --out "$BASE/staging/site"

# Publish: move the checked site into releases/ and point the site link at it in
# one rename, so no request ever finds a half-swapped site. Keep the previous
# release for rollback (point the link back at it); delete older ones.
release="$(date +%Y%m%dT%H%M%S)-${want:0:7}"
mkdir -p "$BASE/www/releases"
mv "$BASE/staging/site" "$BASE/www/releases/$release"
ln -sfn "releases/$release" "$BASE/www/site.next"
mv -T "$BASE/www/site.next" "$BASE/www/site"
rm -rf "$BASE/staging"
ls -1dt "$BASE/www/releases"/*/ | tail -n +3 | xargs -r rm -rf --
[ "$SERVER" = native ] && pixi run -q -e web python deploy/web.py reload
echo "$want $catalogue" > "$BASE/.built"
say "published"
