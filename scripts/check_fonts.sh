#!/bin/bash
# Font dosyalarını kontrol eder: eksik WOFF2, büyük kaynak dosyalar, CSS referansları.
# Dosyalara dokunmaz.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FONTS_DIR="$ROOT/assets/fonts"
SOURCE_THRESHOLD_KB=100
WARNINGS=()

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
  local dir base stem ext

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

add_warning() {
  WARNINGS+=("$1")
}

check_source_fonts() {
  while IFS= read -r -d '' file; do
    if should_skip_input "$file"; then
      continue
    fi

    local rel="${file#$ROOT/}"
    local woff2="${file%.*}.woff2"
    local bytes size_kb

    bytes=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file")
    size_kb=$((bytes / 1024))

    if [ ! -f "$woff2" ]; then
      add_warning "EKSİK WOFF2|$(human_size "$bytes")|$rel|WOFF2 yok — sh scripts/subset_font.sh çalıştırın"
      continue
    fi

    if [ "$file" -nt "$woff2" ]; then
      add_warning "GÜNCEL DEĞİL|$(human_size "$bytes")|$rel|Kaynak dosya WOFF2'den yeni — sh scripts/subset_font.sh çalıştırın"
    fi

    if [ "$size_kb" -gt "$SOURCE_THRESHOLD_KB" ]; then
      local woff2_bytes woff2_kb
      woff2_bytes=$(stat -c%s "$woff2" 2>/dev/null || stat -f%z "$woff2")
      woff2_kb=$((woff2_bytes / 1024))
      add_warning "BÜYÜK KAYNAK|$(human_size "$bytes") → $(human_size "$woff2_bytes")|$rel|Kaynak > ${SOURCE_THRESHOLD_KB} KB (WOFF2: ${woff2_kb} KB)"
    fi
  done < <(find "$FONTS_DIR" -type f \( -iname '*.otf' -o -iname '*.ttf' \) -print0 | sort -z)
}

check_css_references() {
  local theme="$ROOT/assets/css/theme.css"
  local ref path bytes rel

  [ -f "$theme" ] || return 0

  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    path="$ROOT/assets/css/$ref"
    path=$(printf '%s' "$path" | sed 's|^\.\./|../|' )
    path="$ROOT/assets/css/../${ref#../}"

    if [ ! -f "$path" ]; then
      add_warning "CSS EKSİK|—|${ref#../fonts/}|theme.css referansı bulunamadı"
      continue
    fi

    bytes=$(stat -c%s "$path" 2>/dev/null || stat -f%z "$path")
    rel="${path#$ROOT/}"

    if [ "$((bytes / 1024))" -gt 50 ]; then
      add_warning "CSS BÜYÜK|$(human_size "$bytes")|$rel|Servis edilen font > 50 KB"
    fi
  done < <(grep -oE 'url\("\.\./fonts/[^"]+"\)' "$theme" | sed 's/url("\(.*\)")/\1/')
}

check_source_fonts
check_css_references

if [ "${#WARNINGS[@]}" -eq 0 ]; then
  echo "✓ Font uyarısı yok."
  exit 0
fi

echo "⚠ Font uyarıları (${#WARNINGS[@]})"
echo ""
printf "  %-12s  %-10s  %s\n" "DURUM" "BOYUT" "DOSYA"
printf "  %-12s  %-10s  %s\n" "--------" "------" "-----"

IFS=$'\n'
for entry in "${WARNINGS[@]}"; do
  status=$(echo "$entry" | cut -d'|' -f1)
  size=$(echo "$entry" | cut -d'|' -f2)
  path=$(echo "$entry" | cut -d'|' -f3)
  note=$(echo "$entry" | cut -d'|' -f4)
  printf "  %-12s  %-10s  %s\n" "$status" "$size" "$path"
  if [ -n "$note" ]; then
    printf "              %s\n" "$note"
  fi
done

echo ""
echo "WOFF2 üretmek için: sh scripts/subset_font.sh"
