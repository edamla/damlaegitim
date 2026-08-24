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

# Site veri senkronu (docs/data → _data / assets/data)
if [ -f "scripts/sync_site_data.py" ]; then
  echo ">>> Site veri senkronu (docs/data → _data / assets/data)"
  python3 scripts/sync_site_data.py 2>/dev/null || python scripts/sync_site_data.py 2>/dev/null || \
    echo "Uyarı: sync_site_data atlandı (Python veya docs/data eksik)."
  echo ""
fi

# Jekyll öncesi: sync sırasında IDE/paralel işlem _data kalıntısını geri yazabilir
if [ -f "scripts/sync_site_data.py" ]; then
  python3 scripts/sync_site_data.py --cleanup-only 2>/dev/null || \
    python scripts/sync_site_data.py --cleanup-only 2>/dev/null || true
fi

bundle exec jekyll serve
