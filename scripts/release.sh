#!/usr/bin/env bash
set -euo pipefail

VERSION="1.0.0"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python scripts/build_all.py
python scripts/release_gate.py --strict

DIST="dist/stats237_course_v${VERSION}"
rm -rf "$DIST"
mkdir -p "$DIST"

# Core artifacts
cp -R build "$DIST/build" || true
cp -R docs "$DIST/docs" || true
cp -R golden "$DIST/golden" || true

# Generated artifacts (if inputs were present)
for d in registry problem_bank coverage reports; do
  if [ -d "$d" ]; then
    cp -R "$d" "$DIST/$d"
  fi
done

# Schema freeze snapshot
mkdir -p "$DIST/api"
cp api/openapi_snapshot.json "$DIST/api/openapi_snapshot.json"

# Build a wheel without fetching deps (offline-friendly)
mkdir -p "$DIST/wheels"
python -m pip wheel ./stats237_quantlib --no-deps -w "$DIST/wheels" >/dev/null

echo "Release dist written to: $DIST"
