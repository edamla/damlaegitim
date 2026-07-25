#!/bin/bash
# Damla Okul — yerel geliştirme (kurulum sonrası).
# Hook'lar yalnızca burada: görsel kontrol, WebP üretimi, Jekyll serve.

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

# Görsel boyut kontrolü (uyarı raporu, dosyaya dokunmaz)
if [ -f "scripts/check_images.sh" ]; then
  sh scripts/check_images.sh
  echo ""
fi

# Eksik WebP üretimi + manifest güncelleme
if [ -f "scripts/generate_webp.sh" ]; then
  sh scripts/generate_webp.sh
  echo ""
fi

bundle exec jekyll serve
