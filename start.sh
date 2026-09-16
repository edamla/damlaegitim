#!/bin/bash
# Damla Okul — yerel geliştirme (kurulum sonrası).
# Hook'lar: görsel kontrol, WebP, koşullu site veri import, Jekyll serve.

set -uo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# shellcheck source=scripts/refresh_image_paths.sh
. "$ROOT/scripts/refresh_image_paths.sh"
refresh_image_tool_paths

echo "=== Damla Okul — Geliştirme ==="

if ! command -v bundle >/dev/null 2>&1 || [ ! -f "Gemfile.lock" ]; then
  echo "Kurulum eksik görünüyor. Önce çalıştırın: sh install.sh"
  exit 1
fi

if [ -f "scripts/check_images.sh" ]; then
  sh scripts/check_images.sh
  echo ""
fi

if [ -f "scripts/generate_webp.sh" ]; then
  sh scripts/generate_webp.sh
  echo ""
fi

DAMLA_DATA_IMPORT="${DAMLA_DATA_IMPORT:-auto}"
run_import=false
case "$DAMLA_DATA_IMPORT" in
  always) run_import=true ;;
  never) run_import=false ;;
  auto)
    if [ ! -f "assets/data/okullar.json" ] && [ -f "${DAMLA_SITE_ZIP:-$ROOT/../data/data/zip/damla_site.zip}" ]; then
      run_import=true
    fi
    ;;
  *)
    echo "Uyarı: DAMLA_DATA_IMPORT geçersiz ($DAMLA_DATA_IMPORT); auto kullanılıyor." >&2
    ;;
esac

if [ "$run_import" = true ] && [ -f "scripts/import_site_data.sh" ]; then
  sh scripts/import_site_data.sh
  echo ""
elif [ ! -f "assets/data/okullar.json" ] && [ "$DAMLA_DATA_IMPORT" != "never" ]; then
  echo "Uyarı: /ogretmen ve /okullar için site verisi yok. DAMLA_SITE_ZIP=... sh scripts/import_site_data.sh" >&2
  echo ""
fi

bundle exec jekyll serve
