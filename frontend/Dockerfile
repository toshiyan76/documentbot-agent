ARG IMG_VER="20.11.0"

### base ####
FROM node:${IMG_VER} AS base
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    libvips42 \
    && rm -rf /var/lib/apt/lists/*

# npmは20.11.0に付属のものを使用するため、追加インストール不要
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
RUN npm install --production
ENV NODE_ENV=production
COPY src/ ./
RUN npm run build

FROM node:${IMG_VER} AS runner
WORKDIR /app

# 環境変数の設定
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_OPTIONS="--max-old-space-size=512 --max-http-header-size=16384"

# タイムアウト設定
ENV SERVER_TIMEOUT=60000
ENV KEEP_ALIVE_TIMEOUT=65000

# Next.js固有の設定
ENV NEXT_TELEMETRY_DISABLED=1

# デバッグ用の環境変数
ENV DEBUG="*"

# Next.js固有の設定
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_SHARP_PATH=/usr/local/lib/node_modules/sharp

# スタンドアロンビルドの結果をコピー
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

# ヘルスチェック用の設定
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

CMD ["node", "server.js"]