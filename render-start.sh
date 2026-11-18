#!/bin/sh
set -eu

: "${DATABASE_URL:?Missing Render DATABASE_URL}"
: "${WHATOMATE_DATABASE__USER:?Missing Render database user}"
: "${WHATOMATE_DATABASE__PASSWORD:?Missing Render database password}"
: "${WHATOMATE_DEFAULT_ADMIN__PASSWORD:?Missing initial admin password}"
: "${WHATOMATE_APP__ENCRYPTION_KEY:?Missing encryption key}"
: "${WHATOMATE_JWT__SECRET:?Missing JWT secret}"
: "${RENDER_EXTERNAL_URL:?Missing Render public URL}"

# Render private URLs often omit the default port; credentials are injected separately.
db_url=${DATABASE_URL#*://}
db_location=${db_url#*@}
db_hostport=${db_location%%/*}
db_path=${db_location#*/}
export WHATOMATE_DATABASE__HOST=${db_hostport%%:*}
if [ "$db_hostport" = "${db_hostport%%:*}" ]; then
  export WHATOMATE_DATABASE__PORT=5432
else
  export WHATOMATE_DATABASE__PORT=${db_hostport##*:}
fi
ORIGINAL_RENDER_DB_NAME=${db_path%%\?*}
CLIENT_DB_NAME=wingerx_gajanand_wa
export WHATOMATE_DATABASE__NAME=$CLIENT_DB_NAME
export WHATOMATE_DATABASE__SSL_MODE=require
# Create the client's own logical database in the existing PostgreSQL instance.
# Never run migrations against the old default database.
# This requires the existing Render database role to have CREATEDB privileges.
# CREATE DATABASE runs only if the client database is absent.
export PGSSLMODE=require
export PGHOST="$WHATOMATE_DATABASE__HOST"
export PGPORT="$WHATOMATE_DATABASE__PORT"
export PGUSER="$WHATOMATE_DATABASE__USER"
export PGPASSWORD="$WHATOMATE_DATABASE__PASSWORD"
EXISTS=$(psql -X -v ON_ERROR_STOP=1 -d "$ORIGINAL_RENDER_DB_NAME" -tAc "SELECT 1 FROM pg_database WHERE datname = '$CLIENT_DB_NAME'")
if [ "$EXISTS" != "1" ]; then
  echo "Creating dedicated SGJ logical PostgreSQL database"
  psql -X -v ON_ERROR_STOP=1 -d "$ORIGINAL_RENDER_DB_NAME" -c "CREATE DATABASE \"$CLIENT_DB_NAME\""
fi
unset PGPASSWORD
# Temporary read-only credential diagnostic. Reports only counts and matching status.
# Remove after checking the first deployment log. No secrets go to stdout.
export PGPASSWORD="$WHATOMATE_DATABASE__PASSWORD"
diagnostic=$(psql -X -q -A -t -v ON_ERROR_STOP=1 -d "$CLIENT_DB_NAME" \
    -v "verify_email=$WHATOMATE_DEFAULT_ADMIN__EMAIL" \
    -v "verify_password=$WHATOMATE_DEFAULT_ADMIN__PASSWORD" <<'SGJ_AUTH_DIAGNOSTIC_SQL'
SELECT
  COUNT(*) FILTER (WHERE email = :'verify_email') AS email_count,
  COUNT(*) FILTER (WHERE email = :'verify_email' AND is_active = true) AS active_count,
  COUNT(*) FILTER (WHERE email = :'verify_email' AND password_hash = crypt(:'verify_password', password_hash)) AS bcrypt_match_count,
  COUNT(*) FILTER (WHERE is_super_admin = true AND deleted_at IS NULL) AS superadmin_count
FROM users WHERE deleted_at IS NULL;
SGJ_AUTH_DIAGNOSTIC_SQL
)
unset PGPASSWORD
echo "SGJ auth diagnostic (email_matches|active_matches|hash_matches|superadmin_count): $diagnostic"

echo "SGJ logical database is ready; starting the WingerX application"

# Run an isolated, in-container Valkey (Redis-compatible) service for this TEST tenant.
# On free Render, the filesystem and queue are ephemeral: do not rely on scheduled
# campaigns surviving sleep/restarts. No Redis is shared with the original account.
valkey-server --bind 127.0.0.1 --port 6379 --save "" --appendonly no --daemonize yes --maxmemory 96mb --maxmemory-policy noeviction
export WHATOMATE_REDIS__HOST=127.0.0.1
export WHATOMATE_REDIS__PORT=6379
export WHATOMATE_REDIS__TLS=false
export WHATOMATE_REDIS__DB=0
# Whatomate validates the Redis/Valkey connection with its built-in PING on startup.
# Alpine valkey package supplies valkey-server but not necessarily valkey-cli.

export WHATOMATE_SERVER__HOST=0.0.0.0
export WHATOMATE_SERVER__PORT=${PORT:-8080}
export WHATOMATE_SERVER__ALLOWED_ORIGINS=${RENDER_EXTERNAL_URL}

# One-time internal login smoke test. Runs only once on boot, prints HTTP status only.
# Credentials are constructed as escaped JSON inside PostgreSQL and are never logged.
(
  export PGPASSWORD="$WHATOMATE_DATABASE__PASSWORD"
  retries=0
  until curl -fsS -o /dev/null http://127.0.0.1:8080/health; do
    retries=$((retries+1))
    if [ "$retries" -ge 25 ]; then
      echo "SGJ internal login smoke test: health unavailable"
      exit 0
    fi
    sleep 1
  done
  auth_json=$(psql -X -qAt -v ON_ERROR_STOP=1 -d "$CLIENT_DB_NAME" \
    -v "verify_email=$WHATOMATE_DEFAULT_ADMIN__EMAIL" \
    -v "verify_password=$WHATOMATE_DEFAULT_ADMIN__PASSWORD" <<'SGJ_AUTH_SMOKE_JSON'
SELECT json_build_object('email', :'verify_email', 'password', :'verify_password')::text;
SGJ_AUTH_SMOKE_JSON
  )
  unset PGPASSWORD
  status=$(printf '%s' "$auth_json" | curl -sS --max-time 10 -o /dev/null \
    -w '%{http_code}' -H 'Content-Type: application/json' \
    --data-binary @- http://127.0.0.1:8080/api/auth/login || true)
  unset auth_json
  echo "SGJ internal login smoke test HTTP status: $status"
) &

exec /app/whatomate server -config /app/config.toml -migrate
