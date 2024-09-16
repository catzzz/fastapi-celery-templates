#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Start the alembic migrations
alembic -c /app/alembic.ini upgrade head

uvicorn main:app --reload --reload-dir apis --workers 1 --host 0.0.0.0
