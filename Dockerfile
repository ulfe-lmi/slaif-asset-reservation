# Base image pinned by digest (re-verified 2026-09-14 via `docker manifest inspect python:3.13-slim`, linux/amd64).
# Tag kept as comment: python:3.13-slim
FROM python:3.13-slim@sha256:cc9dffa47c8294ba9bb795a8dfaeb7b76f2b30acade2c52a461a2999d127eb00 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN groupadd --system --gid 10001 slaif \
    && useradd --system --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin slaif

COPY --from=ghcr.io/astral-sh/uv:0.11.23 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

COPY manage.py ./
COPY src ./src
COPY data/bootstrap ./data/bootstrap

RUN DJANGO_SETTINGS_MODULE=slaif_reservation.config.settings.local \
    SLAIF_DEBUG=false \
    python manage.py collectstatic --noinput --clear \
    && test -f /app/staticfiles/admin/css/base.css \
    && test -f /app/staticfiles/drf_spectacular_sidecar/swagger-ui-dist/swagger-ui-bundle.js \
    && test -f /app/data/bootstrap/assets.yaml \
    && test -f /app/data/bootstrap/assets.schema.json \
    && chown -R slaif:slaif /app

USER 10001:10001

EXPOSE 8000

CMD ["gunicorn", "slaif_reservation.config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "8", "--keep-alive", "5", "--timeout", "30", "--forwarded-allow-ips", "127.0.0.1,::1", "--header-map", "drop", "--logger-class", "slaif_reservation.config.gunicorn.SlaifGunicornLogger"]
