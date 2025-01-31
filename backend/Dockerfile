# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# uvのインストール
RUN pip install uv

# 依存関係ファイルのコピーと依存関係のインストール
COPY pyproject.toml uv.lock ./
RUN uv pip install . --system

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# 依存関係のコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY . .

ENV PORT=8080
ENV HOST=0.0.0.0

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]