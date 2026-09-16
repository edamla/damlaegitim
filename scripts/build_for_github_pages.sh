#!/bin/bash
# Yerel: GitHub Pages ile aynı Jekyll build (github-pages gem).
# GitHub uzaktan import çalıştırmaz — push öncesi import + bu script, sonra veri dosyalarını commit edin.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v bundle >/dev/null 2>&1 || [ ! -f "Gemfile.lock" ]; then
  echo "Hata: bundle / Gemfile.lock eksik. Önce: sh install.sh" >&2
  exit 1
fi

DAMLA_DATA_IMPORT="${DAMLA_DATA_IMPORT:-always}"
if [ "$DAMLA_DATA_IMPORT" != "never" ] && [ -f "scripts/import_site_data.sh" ]; then
  sh scripts/import_site_data.sh
  echo ""
fi

echo ">>> Jekyll build (GitHub Pages ile uyumlu)"
bundle exec jekyll build

echo ""
echo "Push öncesi (veri güncellediyseniz commit edin):"
echo "  _data/tymm.json _data/turkiye_adres_il_ilce.json assets/data/"
echo "Sonra: git push origin main  →  GitHub Pages Jekyll build"
