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

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NODE_OPTIONS="--max-old-space-size=512"

# Install healthcheck dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir waitress==2.1.2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/.next/standalone ./

# Create healthcheck endpoint
RUN echo 'from http.server import HTTPServer, BaseHTTPRequestHandler\n\
class HealthCheck(BaseHTTPRequestHandler):\n\
    def do_GET(self):\n\
        self.send_response(200)\n\
        self.end_headers()\n\
        self.wfile.write(b"OK")\n\
server = HTTPServer(("", 8080), HealthCheck)\n\
server.serve_forever()' > health_check.py \
    && chmod +x health_check.py

EXPOSE 3000 8080

# Create startup script
RUN echo '#!/bin/sh\npython3 health_check.py & \nexec node server.js' > start.sh \
    && chmod +x start.sh

CMD ["/bin/sh", "-c", "./start.sh"]