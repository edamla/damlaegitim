#!/bin/bash
# Prebuilt damla_site.zip -> _data/ + assets/data/ (edamla/data export çıktısı).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DAMLA_SITE_ZIP="${DAMLA_SITE_ZIP:-$ROOT/../data/data/zip/damla_site.zip}"

STALE=(
  "_data/okullar.json"
  "_data/okullar_detay.json"
  "_data/turkiye_adres.json"
  "_data/turkiye_geodata.json"
)

cleanup_stale() {
  for rel in "${STALE[@]}"; do
    if [ -f "$rel" ]; then
      rm -f "$rel"
      echo "Silindi (eski kalıntı): $rel"
    fi
  done
}

fail_no_zip() {
  echo "Hata: damla_site.zip bulunamadı: $DAMLA_SITE_ZIP" >&2
  echo "  edamla/data: python scripts/export_damla_site.py  (veya: python scripts/main.py export damla-site)" >&2
  exit 1
}

cleanup_stale

if [ ! -f "$DAMLA_SITE_ZIP" ]; then
  fail_no_zip
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "Hata: unzip gerekli (Git Bash / Linux)." >&2
  exit 1
fi

echo ">>> Site veri import: $DAMLA_SITE_ZIP"
unzip -o -q "$DAMLA_SITE_ZIP" -d "$ROOT"

cleanup_stale
echo "Import tamamlandı (_data/turkiye_adres_il_ilce.json, _data/tymm.json, assets/data/)."
