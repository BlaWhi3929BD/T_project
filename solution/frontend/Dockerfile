FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.28-alpine-slim

COPY nginx.conf /etc/nginx/nginx.conf

# The nginx package is upgraded from the current Alpine security repository.
# hadolint ignore=DL3018
RUN touch /tmp/nginx.pid \
    && apk add --no-cache --upgrade musl-utils nginx \
    && rm -f /etc/nginx/conf.d/default.conf \
    && mkdir -p /var/cache/nginx/client_temp \
        /var/cache/nginx/proxy_temp \
        /var/cache/nginx/fastcgi_temp \
        /var/cache/nginx/uwsgi_temp \
        /var/cache/nginx/scgi_temp \
        /etc/nginx/conf.d \
    && chown -R nginx:nginx \
        /tmp/nginx.pid \
        /var/cache/nginx \
        /var/log/nginx \
        /etc/nginx/conf.d
COPY --from=build /app/dist /usr/share/nginx/html
RUN chown -R nginx:nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/ || exit 1
