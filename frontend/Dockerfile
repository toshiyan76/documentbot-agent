# syntax=docker.io/docker/dockerfile:1
FROM node:20.11.0-slim AS base
WORKDIR /app

# デフォルトではproductionですが、build引数で上書き可能にする
ARG BUILD_ENV=production
ENV NODE_ENV=${BUILD_ENV}

# Next.jsのテレメトリを無効化（プライバシーとセキュリティのため）
ENV NEXT_TELEMETRY_DISABLED 1

## 開発用ステージ
FROM base AS dev
WORKDIR /app
# 依存関係のインストール
COPY src/package.json src/package-lock.json* ./
RUN npm install
# ソースコードをコピー（volumeマウントがある場合は上書きされるので、最低限のファイルだけでもOK）
COPY src/ ./
EXPOSE 3000
CMD ["npm", "run", "dev"]

## 以下はプロダクション用のステージ（既存の内容）
FROM base AS deps
WORKDIR /app
COPY src/package.json src/package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY src/ .
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

RUN groupadd -r nodejs && useradd -r -g nodejs nextjs

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]