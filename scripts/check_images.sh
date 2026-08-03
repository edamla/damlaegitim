#!/bin/bash
# Büyük görsel dosyalarını raporlar; dosyalara dokunmaz.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck source=refresh_image_paths.sh
. "$ROOT/scripts/refresh_image_paths.sh"
refresh_image_tool_paths

SLIDES_SIZE_KB=150
SLIDES_MOBILE_SIZE_KB=120
EAN_SIZE_KB=200
LOGO_SIZE_KB=50

SLIDES_WIDTH=1280
SLIDES_HEIGHT=560
SLIDES_MOBILE_WIDTH=500
SLIDES_MOBILE_HEIGHT=500
EAN_WIDTH=600
EAN_HEIGHT=600

TARGET="${1:-all}"
WARNINGS=()
TOTAL_BYTES=0

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

get_dimensions() {
  local file="$1"
  if command -v identify >/dev/null 2>&1; then
    identify -format '%wx%h' "$file" 2>/dev/null || echo "?"
  elif command -v magick >/dev/null 2>&1; then
    magick identify -format '%wx%h' "$file" 2>/dev/null || echo "?"
  else
    echo "?"
  fi
}

check_file() {
  local file="$1"
  local threshold_kb="$2"
  local max_width="${3:-0}"
  local max_height="${4:-0}"
  local skip_size_if_dims_ok="${5:-0}"

  [ -f "$file" ] || return 0

  # 2 = slide mobil: ~500x500 hedef ölçü, uyarı üretilmez
  if [ "$skip_size_if_dims_ok" -eq 2 ]; then
    return 0
  fi

  local bytes
  bytes=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file")
  local size_kb=$((bytes / 1024))
  local rel="${file#$ROOT/}"
  local dims
  dims=$(get_dimensions "$file")
  local reason=""
  local dims_ok=0

  if [ "$max_width" -gt 0 ] && [ "$dims" != "?" ]; then
    local width height
    width=${dims%x*}
    height=${dims#*x}
    if [ "$width" -le "$max_width" ] && [ "$height" -le "$max_height" ]; then
      dims_ok=1
    elif [ "$width" -gt "$max_width" ] || [ "$height" -gt "$max_height" ]; then
      reason="piksel > ${max_width}x${max_height}"
    fi
  fi

  if [ "$skip_size_if_dims_ok" -eq 1 ] && [ "$dims_ok" -eq 1 ]; then
    return 0
  fi

  if [ "$size_kb" -gt "$threshold_kb" ]; then
    if [ -n "$reason" ]; then
      reason="boyut > ${threshold_kb} KB, ${reason}"
    else
      reason="boyut > ${threshold_kb} KB"
    fi
  fi

  if [ -n "$reason" ]; then
    WARNINGS+=("$(human_size "$bytes")|${dims}|${rel}|${reason}")
    TOTAL_BYTES=$((TOTAL_BYTES + bytes))
  fi
}

scan_slides() {
  local slides_dir="$ROOT/assets/images/slides"
  [ -d "$slides_dir" ] || return 0

  for file in "$slides_dir"/*; do
    [ -f "$file" ] || continue
    case "$(basename "$file")" in
      *m.jpg|*m.jpeg|*m.png|*m.webp)
        check_file "$file" "$SLIDES_MOBILE_SIZE_KB" "$SLIDES_MOBILE_WIDTH" "$SLIDES_MOBILE_HEIGHT" 2
        ;;
      *)
        check_file "$file" "$SLIDES_SIZE_KB" "$SLIDES_WIDTH" "$SLIDES_HEIGHT" 1
        ;;
    esac
  done
}

scan_ean() {
  local ean_dir="$ROOT/assets/images/ean"
  [ -d "$ean_dir" ] || return 0

  while IFS= read -r -d '' file; do
    check_file "$file" "$EAN_SIZE_KB" "$EAN_WIDTH" "$EAN_HEIGHT"
  done < <(find "$ean_dir" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' \) -print0)
}

scan_logo() {
  check_file "$ROOT/assets/images/logo.png" "$LOGO_SIZE_KB"
}

print_thresholds() {
  echo "Eşikler: slides > ${SLIDES_SIZE_KB} KB, mobil slides > ${SLIDES_MOBILE_SIZE_KB} KB, ean > ${EAN_SIZE_KB} KB, logo > ${LOGO_SIZE_KB} KB"
  case "$TARGET" in
    slides)
      echo "Beklenen en büyük çözünürlük: slides ${SLIDES_WIDTH}x${SLIDES_HEIGHT}, mobil slides ${SLIDES_MOBILE_WIDTH}x${SLIDES_MOBILE_HEIGHT}"
      ;;
    ean)
      echo "Beklenen en büyük çözünürlük: ean ${EAN_WIDTH}x${EAN_HEIGHT}"
      ;;
    logo)
      echo "Beklenen en büyük çözünürlük: logo (piksel sınırı yok)"
      ;;
    all)
      echo "Beklenen en büyük çözünürlük: slides ${SLIDES_WIDTH}x${SLIDES_HEIGHT}, mobil slides ${SLIDES_MOBILE_WIDTH}x${SLIDES_MOBILE_HEIGHT}, ean ${EAN_WIDTH}x${EAN_HEIGHT}, logo (piksel sınırı yok)"
      ;;
  esac
}

case "$TARGET" in
  slides) scan_slides ;;
  ean) scan_ean ;;
  logo) scan_logo ;;
  all)
    scan_slides
    scan_ean
    scan_logo
    ;;
  *)
    echo "Kullanım: sh scripts/check_images.sh [all|slides|ean|logo]"
    exit 1
    ;;
esac

if [ "${#WARNINGS[@]}" -eq 0 ]; then
  echo "✓ Büyük görsel uyarısı yok."
  echo ""
  print_thresholds
  exit 0
fi

echo "⚠ Büyük görsel uyarıları (${#WARNINGS[@]} dosya)"
echo ""
printf "  %-8s  %-12s  %s\n" "BOYUT" "BOYUTLAR" "DOSYA"
printf "  %-8s  %-12s  %s\n" "------" "--------" "-----"

IFS=$'\n'
sorted=$(printf '%s\n' "${WARNINGS[@]}" | sort -t'|' -k1,1hr)
for entry in $sorted; do
  size=$(echo "$entry" | cut -d'|' -f1)
  dims=$(echo "$entry" | cut -d'|' -f2)
  path=$(echo "$entry" | cut -d'|' -f3)
  printf "  %-8s  %-12s  %s\n" "$size" "$dims" "$path"
done

echo ""
print_thresholds
echo "Toplam uyarı: ${#WARNINGS[@]} dosya / $(human_size "$TOTAL_BYTES") tasarruf potansiyeli"
echo "Photoshop ile optimize edip tekrar kontrol edin."
