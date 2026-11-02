#!/usr/bin/env bash
# ==============================================================================
# Kogu Mudae — Automated Cloud Backup (PostgreSQL + Tower State + Overrides)
# Runs daily via cron on the Oracle Cloud VPS (129.148.63.115).
# Keeps the last 14 days of compressed backups in /home/ubuntu/backups/kogu/
# ==============================================================================
set -euo pipefail

BACKUP_DIR="/home/ubuntu/backups/kogu"
APP_DIR="/home/ubuntu/arqon"
PG_BIN="/home/ubuntu/arqon/node_modules/@embedded-postgres/linux-arm64/native/bin"
PG_PORT="54329"
PG_DB="arqon_dev"
PG_USER="postgres"
export PGPASSWORD="arqon_dev_pw"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

echo "[backup] Iniciando backup diário do Kogu ($TIMESTAMP)..."

# 1. Dump do PostgreSQL (todas as cartas, pactos, saldos, relíquias, configurações)
if [ -x "$PG_BIN/pg_dump" ]; then
  "$PG_BIN/pg_dump" -h 127.0.0.1 -p "$PG_PORT" -U "$PG_USER" "$PG_DB" | gzip -9 > "$BACKUP_DIR/kogu_db_${TIMESTAMP}.sql.gz"
else
  pg_dump -h 127.0.0.1 -p "$PG_PORT" -U "$PG_USER" "$PG_DB" | gzip -9 > "$BACKUP_DIR/kogu_db_${TIMESTAMP}.sql.gz"
fi

# 2. Backup dos estados de Torre e dados locais (data/)
if [ -d "$APP_DIR/data" ]; then
  tar -czf "$BACKUP_DIR/kogu_data_${TIMESTAMP}.tar.gz" -C "$APP_DIR" data
fi

# 3. Rotação automática: mantém os últimos 14 dias de backups
find "$BACKUP_DIR" -type f -name "kogu_*.gz" -mtime +14 -delete

echo "[backup] Backup concluído com sucesso em $BACKUP_DIR:"
ls -lh "$BACKUP_DIR" | tail -n 5
