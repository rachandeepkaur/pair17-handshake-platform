# syntax=docker/dockerfile:1
# Pair 17 frontend: React build served by nginx, which also proxies /api/* to the services.

FROM node:20-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# Same-origin API base; nginx strips /api and routes by path (docker/nginx.conf).
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1
