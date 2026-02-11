#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

python -m pip install -r requirements.txt
uvicorn api.app:app --host "${HOST}" --port "${PORT}"
