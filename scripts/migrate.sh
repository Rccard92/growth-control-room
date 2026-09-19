#!/bin/sh
# Release step: apply database migrations once, before the new version starts.
# Running this from the container CMD makes replicas race on the same database.
#
#   local:     ./scripts/migrate.sh
#   container: docker run --rm <image> ./scripts/migrate.sh
set -eu

cd "$(dirname "$0")/../apps/api"

if command -v uv >/dev/null 2>&1; then
    exec uv run alembic upgrade head
fi

# Runtime image: no uv, but the virtualenv is already on PATH.
exec alembic upgrade head
