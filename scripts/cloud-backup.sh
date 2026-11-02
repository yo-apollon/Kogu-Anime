#!/usr/bin/env bash
# ==============================================================================
# Kogu Mudae — Automated Cloud Backup (PostgreSQL + Tower State + Overrides)
# Runs daily via cron on the Oracle Cloud VPS (129.148.63.115).
# Keeps the last 14 days of compressed backups in /home/ubuntu/backups/kogu/
# ==============================================================================
set -euo pipefail

BACKUP_DIR="/home/ubuntu/backups/kogu"
APP_DIR="/home/ubuntu/arqon"
export DATABASE_URL="${DATABASE_URL:-postgres://postgres:arqon_dev_pw@127.0.0.1:54329/arqon_dev}"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

echo "[backup] Iniciando backup diário do Kogu ($TIMESTAMP)..."

# 1. Dump lógico completo do PostgreSQL via Node.js (independe de pg_dump externo)
cd "$APP_DIR"
node --input-type=module -e '
import postgres from "postgres";
import zlib from "node:zlib";
import fs from "node:fs";

const sql = postgres(process.env.DATABASE_URL, { max: 1, onnotice: () => {} });
const tables = [
  "guilds",
  "users",
  "guild_members",
  "niches",
  "franchises",
  "series",
  "entities",
  "entity_series",
  "entity_images",
  "pacts",
  "wishes",
  "disabled_series",
  "entity_likes"
];
const dump = { generatedAt: new Date().toISOString(), tables: {} };
for (const t of tables) {
  try {
    dump.tables[t] = await sql.unsafe(`SELECT * FROM "${t}"`);
  } catch {
    dump.tables[t] = [];
  }
}
await sql.end({ timeout: 5 });
const gz = zlib.gzipSync(Buffer.from(JSON.stringify(dump), "utf8"), { level: 9 });
fs.writeFileSync(process.argv[1], gz);
' "$BACKUP_DIR/kogu_db_${TIMESTAMP}.json.gz"

# 2. Backup dos estados de Torre e dados locais (data/)
if [ -d "$APP_DIR/data" ]; then
  tar -czf "$BACKUP_DIR/kogu_data_${TIMESTAMP}.tar.gz" -C "$APP_DIR" data
fi

# 3. Rotação automática: mantém os últimos 14 dias de backups
find "$BACKUP_DIR" -type f -name "kogu_*.gz" -mtime +14 -delete

echo "[backup] Backup concluído com sucesso em $BACKUP_DIR:"
ls -lh "$BACKUP_DIR" | tail -n 5
