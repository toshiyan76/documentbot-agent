ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim AS base
RUN apt-get update && \
    apt-get install -y \
    git gcc musl-dev && \
    rm -rf /var/lib/apt/lists/*

FROM base AS init
WORKDIR /app

FROM base AS dev
WORKDIR /app
COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONPATH=/app/src
ENV FASTAPI_ENV="development"

FROM base AS builder
ARG API_PORT
WORKDIR /app

COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV FASTAPI_ENV="production"

FROM python:${PYTHON_VERSION}-slim AS runner
WORKDIR /app
ENV PYTHONPATH=/app/src
ENV FASTAPI_ENV="production"

COPY src/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app/src .
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

EXPOSE 8080
ENV PORT 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]