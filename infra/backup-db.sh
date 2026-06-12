#!/usr/bin/env bash
# Backup diario de la base de Vigía a S3 (runbook: infra/DEPLOY.md § Backups).
#
# Corre por cron en el host del EC2 como ec2-user; streamea
# pg_dump -> gzip -> S3 sin tocar el disco local (~80 MB comprimido).
# Credenciales: instance profile `vigia-ec2` (solo s3:PutObject — la caja
# puede subir backups pero no leerlos ni borrarlos; el restore usa
# credenciales admin desde afuera). Retención: lifecycle de 30 días en el bucket.
set -euo pipefail
PATH=/usr/local/bin:/usr/bin:/bin

BUCKET="${VIGIA_BACKUP_BUCKET:-vigia-backups}"
COMPOSE_FILE="${VIGIA_COMPOSE_FILE:-/home/ec2-user/vigia/docker-compose.prod.yml}"
DEST="s3://${BUCKET}/vigia-$(date -u +%F).sql.gz"

echo "[$(date -u +%FT%TZ)] backup -> ${DEST}"
docker compose -f "${COMPOSE_FILE}" exec -T db \
  pg_dump -U vigia --no-owner vigia | gzip | aws s3 cp - "${DEST}"
echo "[$(date -u +%FT%TZ)] backup OK"
