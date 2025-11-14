# ==========================
# Build stage
# ==========================
FROM python:3.11.6-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel \
 && pip wheel --no-deps --wheel-dir /wheels -r requirements.txt

COPY . .

# ==========================
# Runtime stage
# ==========================
FROM python:3.11.6-slim AS runtime

ENV PYTHONUNBUFFERED=1

ARG APP_USER=app
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} ${APP_USER} \
 && useradd -u ${APP_UID} -g ${APP_GID} -m ${APP_USER}

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt


COPY --chown=app:app . .

ENV PORT=8000
EXPOSE 8000

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

VOLUME ["/tmp"]

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
