#!/bin/sh
# Railway no tiene el mecanismo de volumen local (./keys:/app/keys:ro) que usa
# docker-compose en desarrollo — las llaves JWT llegan como variables de
# entorno en base64 (JWT_PRIVATE_KEY_B64 / JWT_PUBLIC_KEY_B64) y este script
# las materializa en disco antes de arrancar uvicorn. Base64 evita cualquier
# problema de saltos de línea al pegar el PEM en la UI de secretos de Railway.
set -e

mkdir -p /app/keys

if [ -n "${JWT_PRIVATE_KEY_B64:-}" ]; then
  echo "$JWT_PRIVATE_KEY_B64" | base64 -d > /app/keys/private.pem
fi

if [ -n "${JWT_PUBLIC_KEY_B64:-}" ]; then
  echo "$JWT_PUBLIC_KEY_B64" | base64 -d > /app/keys/public.pem
fi

exec "$@"
