# The opengwas.io web server: nginx serving a built site from a read-only mount.
# The site is built outside the container (deploy/update.sh) into
# ${OPENGWAS_WEB_ROOT}/site, and the container serves it as /srv/www/site.
#
#   docker compose -f deploy/compose.yaml up -d --build
#
# The image runs nginx as an unprivileged user on port 8080. At start-up it fills
# ${WEB_ROOT} and ${LISTEN_PORT} into the template below.
FROM nginxinc/nginx-unprivileged:1.30.6-alpine

USER root
RUN rm -f /etc/nginx/conf.d/default.conf
USER 101

COPY site.conf.template /etc/nginx/templates/site.conf.template
ENV WEB_ROOT=/srv/www \
    LISTEN_PORT=8080
EXPOSE 8080
