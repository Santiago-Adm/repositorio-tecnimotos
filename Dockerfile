# syntax=docker/dockerfile:1

# ── Stage 1: builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
COPY src/ src/
COPY api/ api/
COPY scripts/ scripts/

RUN pip install --no-cache-dir .

# ── Stage 2: producción ───────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system --gid 1001 app && \
    useradd --system --uid 1001 --gid 1001 --no-create-home app

# Paquetes instalados (src, api, scripts ya están en site-packages)
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/alembic /usr/local/bin/alembic

# Migraciones Alembic — no son paquete Python, se necesitan en runtime
COPY --chown=app:app alembic/ alembic/
COPY --chown=app:app alembic.ini alembic.ini

# Materializa las llaves JWT desde variables de entorno en Railway (sin
# volumen local como en docker-compose) — ver docker-entrypoint.sh.
COPY --chown=app:app docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
# mkdir aquí (como root, antes de USER app) — el directorio debe ser escribible
# por el usuario "app" para que el entrypoint pueda escribir las llaves.
RUN mkdir -p /app/keys && chown app:app /app/keys

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')" || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Railway: Release Command = alembic upgrade head
# Docker Compose: command sobrescribe con alembic upgrade head && uvicorn ...
#
# --proxy-headers --forwarded-allow-ips="*": Railway termina TLS en su propio
# edge y reenvía al contenedor a través de su red interna — sin esto, Uvicorn
# reporta la IP interna del proxy de Railway como request.client.host para
# TODAS las peticiones, no la IP real del cliente. Esto rompe tanto el
# candado de red de SUPERADMIN (07 §Pieza 6-bis) como el conteo por IP del
# bloqueo de fuerza bruta (07 §2.5) — con este flag, Uvicorn lee la IP real
# desde X-Forwarded-For, que Railway sí añade correctamente.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
