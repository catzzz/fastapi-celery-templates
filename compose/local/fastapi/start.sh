#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Start the FastAPI application with uvicorn
# uvicorn main:app --reload --reload-dir app --workers 1 --host 0.0.0.0 --port 8000
uvicorn main:app --reload --workers 1 --host 0.0.0.0 --port 8000
