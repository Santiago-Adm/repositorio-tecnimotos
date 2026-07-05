#!/bin/bash
# Copia 3 del respaldo 3-2-1 (08-plan-operacion-ejecutable.md §5.2/5.3) —
# volcado semanal comprimido al equipo local de Sant. Pensado para correr
# cada domingo vía cron, tanto en desarrollo como apuntando a la base real
# de Railway una vez desplegada (solo cambiar BACKUP_DATABASE_URL).
#
# Uso manual:
#   BACKUP_DATABASE_URL="postgresql://usuario:pass@host:puerto/db" ./scripts/backup_semanal.sh
#
# Cron sugerido (domingos 3:00 am, hora de Perú):
#   0 3 * * 0 BACKUP_DATABASE_URL="..." /home/san/Proyectos/repositorio-tecnimotos/scripts/backup_semanal.sh >> ~/backups/tecnimotos/backup.log 2>&1
set -euo pipefail

DESTINO="${BACKUP_DESTINO:-$HOME/backups/tecnimotos}"
RETENCION_DIAS=90  # 08 §5.3 — Copia 3 (local), retención 90 días
FECHA=$(date +%Y-%m-%d_%H%M%S)
ARCHIVO="$DESTINO/tecnimotos_$FECHA.sql.gz"

if [ -z "${BACKUP_DATABASE_URL:-}" ]; then
  echo "ERROR: falta BACKUP_DATABASE_URL (cadena de conexión postgresql://...)." >&2
  exit 1
fi

mkdir -p "$DESTINO"

echo "[$FECHA] Iniciando respaldo → $ARCHIVO"
# pg_dump vía contenedor descartable — evita instalar postgresql-client en el
# sistema; usa la misma imagen que ya corre el proyecto (postgres:16-alpine).
# --network host: necesario para alcanzar "localhost" cuando se respalda la
# base de desarrollo; no estorba al respaldar la base remota de Railway.
if docker run --rm --network host postgres:16-alpine pg_dump "$BACKUP_DATABASE_URL" | gzip > "$ARCHIVO"; then
  TAMANO=$(du -h "$ARCHIVO" | cut -f1)
  echo "[$FECHA] Respaldo completado — $TAMANO"
else
  echo "[$FECHA] ERROR: pg_dump falló — revisar la conexión." >&2
  rm -f "$ARCHIVO"
  exit 1
fi

# Retención — borra respaldos con más de 90 días (08 §5.3)
BORRADOS=$(find "$DESTINO" -name "tecnimotos_*.sql.gz" -mtime +"$RETENCION_DIAS" -print -delete | wc -l)
if [ "$BORRADOS" -gt 0 ]; then
  echo "[$FECHA] Limpieza de retención: $BORRADOS respaldo(s) con más de $RETENCION_DIAS días eliminados."
fi

echo "[$FECHA] Respaldos actuales en $DESTINO:"
ls -lh "$DESTINO"/tecnimotos_*.sql.gz 2>/dev/null || echo "  (ninguno todavía)"
