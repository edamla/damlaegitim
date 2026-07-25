#!/bin/bash
# assets/fonts altındaki tüm OTF/TTF dosyalarından WOFF2 subset üretir.
# Orijinal dosyalara dokunmaz. fontawesome/ atlanır (zaten WOFF2 içerir).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FONTS_DIR="$ROOT/assets/fonts"

UNICODES="\
U+0020-007E,\
U+00A0-00FF,\
U+0100-017F,\
U+0130,U+0131,\
U+015E,U+015F,\
U+011E,U+011F,\
U+00C7,U+00E7,\
U+00D6,U+00F6,\
U+00DC,U+00FC"

if ! python -c "import fontTools" 2>/dev/null; then
  echo "fonttools kurulu değil. Çalıştırın: pip install fonttools brotli"
  exit 1
fi

human_size() {
  local bytes="$1"
  if [ "$bytes" -ge 1048576 ]; then
    awk -v b="$bytes" 'BEGIN { printf "%.1f MB", b / 1048576 }'
  elif [ "$bytes" -ge 1024 ]; then
    awk -v b="$bytes" 'BEGIN { printf "%.0f KB", b / 1024 }'
  else
    printf "%d B" "$bytes"
  fi
}

should_skip_input() {
  local file="$1"
  local dir base ext stem

  case "$file" in
    */fontawesome/*) return 0 ;;
  esac

  ext="${file##*.}"
  ext=$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')

  case "$ext" in
    otf|ttf) ;;
    *) return 0 ;;
  esac

  if [ "$ext" = "ttf" ]; then
    dir="$(dirname "$file")"
    base="$(basename "$file")"
    stem="${base%.ttf}"
    if [ -f "$dir/$stem.otf" ]; then
      return 0
    fi
  fi

  return 1
}

subset_one() {
  local input="$1"
  local output="${input%.*}.woff2"
  local rel="${input#$ROOT/}"

  if [ -f "$output" ] && [ "$output" -nt "$input" ]; then
    SKIPPED=$((SKIPPED + 1))
    return 0
  fi

  python -m fontTools.subset "$input" \
    --output-file="$output" \
    --flavor=woff2 \
    --layout-features='*' \
    --glyph-names \
    --symbol-cmap \
    --legacy-cmap \
    --notdef-glyph \
    --notdef-outline \
    --recommended-glyphs \
    --unicodes="$UNICODES" \
    2>/dev/null

  local in_size out_size
  in_size=$(stat -c%s "$input" 2>/dev/null || stat -f%z "$input")
  out_size=$(stat -c%s "$output" 2>/dev/null || stat -f%z "$output")

  printf "  ✓ %s\n" "$rel"
  printf "    %s → %s (%s)\n" "$(human_size "$in_size")" "$(basename "$output")" "$(human_size "$out_size")"
  TOTAL_IN=$((TOTAL_IN + in_size))
  TOTAL_OUT=$((TOTAL_OUT + out_size))
  COUNT=$((COUNT + 1))
}

TOTAL_IN=0
TOTAL_OUT=0
COUNT=0
SKIPPED=0

echo "WOFF2 subset üretimi başlıyor..."
echo ""

while IFS= read -r -d '' file; do
  if should_skip_input "$file"; then
    continue
  fi
  subset_one "$file"
done < <(find "$FONTS_DIR" -type f \( -iname '*.otf' -o -iname '*.ttf' \) -print0 | sort -z)

echo ""
if [ "$COUNT" -eq 0 ] && [ "$SKIPPED" -gt 0 ]; then
  echo "Tüm WOFF2 dosyaları güncel ($SKIPPED dosya atlandı)."
  exit 0
fi

if [ "$COUNT" -eq 0 ]; then
  echo "İşlenecek font dosyası bulunamadı."
  exit 0
fi

echo "Toplam: $COUNT dosya üretildi"
if [ "$SKIPPED" -gt 0 ]; then
  echo "Atlandı: $SKIPPED dosya (woff2 zaten güncel)"
fi
echo "Girdi:  $(human_size "$TOTAL_IN")"
echo "Çıktı:  $(human_size "$TOTAL_OUT")"
echo "Tasarruf: $(human_size "$((TOTAL_IN - TOTAL_OUT))")"
