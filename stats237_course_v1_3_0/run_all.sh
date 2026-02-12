#!/usr/bin/env bash
set -euo pipefail

python scripts/build_all.py

echo

echo "Outputs:"
if [ -d build/site ]; then
  echo "- HTML site: build/site/index.html"
fi
if [ -f build/Stats237_Reader.pdf ]; then
  echo "- PDF reader: build/Stats237_Reader.pdf"
fi
if [ -d build/reading_edition ]; then
  if ls build/reading_edition/*.pdf >/dev/null 2>&1; then
    echo "- Reading Edition PDFs: build/reading_edition/*.pdf"
  fi
fi
