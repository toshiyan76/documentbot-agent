ARG IMG_VER="22.12.0-slim"

### base ####
FROM node:${IMG_VER} AS base
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    libvips42 \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g npm@latest
RUN corepack disable

FROM base AS init
WORKDIR /app/src

FROM base AS dev
WORKDIR /app/src

FROM base AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY src/package*.json ./
RUN npm ci
ENV NODE_ENV=production
COPY src/ ./
COPY src/public ./public
RUN mkdir -p public
RUN npm run build

FROM node:${IMG_VER}-slim AS runner
WORKDIR /app

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    openssl \
    && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/.next/standalone ./

EXPOSE 3000

CMD ["node", "server.js"]