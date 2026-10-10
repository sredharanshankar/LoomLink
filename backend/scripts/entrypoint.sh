#!/usr/bin/env bash
set -e

echo "Waiting for database..."
until pg_isready -h db -U loomlink -q 2>/dev/null; do
    sleep 1
done
echo "Database ready."

alembic upgrade head
exec "$@"
