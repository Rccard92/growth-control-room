#!/bin/sh
# Release step: apply database migrations once, before the new version starts.
# Running this inside the container CMD makes replicas race on the same database.
set -eu
cd "$(dirname "$0")/.."
exec uv run --directory apps/api alembic upgrade head
