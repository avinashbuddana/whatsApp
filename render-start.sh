#!/bin/sh
set -eu

: "${DATABASE_URL:?Missing Render DATABASE_URL}"
: "${REDIS_URL:?Missing Render REDIS_URL}"
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
echo "SGJ logical database is ready; starting the WingerX application"

redis_scheme=${REDIS_URL%%://*}
redis_url=${REDIS_URL#*://}
redis_location=${redis_url#*@}
redis_hostport=${redis_location%%/*}
export WHATOMATE_REDIS__HOST=${redis_hostport%%:*}
if [ "$redis_hostport" = "${redis_hostport%%:*}" ]; then
  export WHATOMATE_REDIS__PORT=6379
else
  export WHATOMATE_REDIS__PORT=${redis_hostport##*:}
fi
if [ "$redis_scheme" = "rediss" ]; then
  export WHATOMATE_REDIS__TLS=true
else
  export WHATOMATE_REDIS__TLS=false
fi
if [ "$redis_url" != "$redis_location" ]; then
  redis_auth=${redis_url%%@*}
  if [ "$redis_auth" != "${redis_auth#*:}" ]; then
    export WHATOMATE_REDIS__USERNAME=${redis_auth%%:*}
    export WHATOMATE_REDIS__PASSWORD=${redis_auth#*:}
  else
    export WHATOMATE_REDIS__PASSWORD=$redis_auth
  fi
fi
export WHATOMATE_SERVER__HOST=0.0.0.0
export WHATOMATE_SERVER__PORT=${PORT:-8080}
export WHATOMATE_SERVER__ALLOWED_ORIGINS=${RENDER_EXTERNAL_URL}

exec /app/whatomate server -config /app/config.toml -migrate
