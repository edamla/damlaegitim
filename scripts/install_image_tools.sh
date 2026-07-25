#!/bin/bash
# WebP üretimi ve görsel boyut raporu için cwebp / ImageMagick kurulumu.
# install.sh tarafından çağrılır; başarısızlıkta kurulum durmaz.

set -uo pipefail

has_webp_tool() {
  if command -v cwebp >/dev/null 2>&1; then
    return 0
  fi
  if command -v magick >/dev/null 2>&1; then
    return 0
  fi
  if command -v convert >/dev/null 2>&1 && convert -version 2>/dev/null | grep -qi 'ImageMagick'; then
    return 0
  fi
  return 1
}

has_identify_tool() {
  command -v identify >/dev/null 2>&1 || command -v magick >/dev/null 2>&1
}

is_windows() {
  case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) return 0 ;;
  esac
  [ "${OS:-}" = "Windows_NT" ] && return 0
  return 1
}

refresh_windows_image_paths() {
  # shellcheck source=refresh_image_paths.sh
  . "$(cd "$(dirname "$0")" && pwd)/refresh_image_paths.sh"
  refresh_image_tool_paths
}

winget_install() {
  local id="$1"
  if ! command -v winget >/dev/null 2>&1; then
    return 1
  fi
  echo "  winget install $id"
  winget install --id "$id" -e \
    --accept-source-agreements --accept-package-agreements \
    --disable-interactivity
}

choco_install() {
  local pkg="$1"
  if ! command -v choco >/dev/null 2>&1; then
    return 1
  fi
  echo "  choco install $pkg"
  choco install "$pkg" -y
}

brew_install() {
  local pkg="$1"
  if ! command -v brew >/dev/null 2>&1; then
    return 1
  fi
  echo "  brew install $pkg"
  brew install "$pkg"
}

apt_install() {
  if ! command -v apt-get >/dev/null 2>&1; then
    return 1
  fi
  if command -v sudo >/dev/null 2>&1; then
    echo "  apt-get install (sudo)"
    sudo apt-get update -qq && sudo apt-get install -y imagemagick webp
  else
    echo "  Uyarı: sudo yok; apt ile kurulum atlandı."
    return 1
  fi
}

install_on_windows() {
  local ok=0

  if ! has_webp_tool || ! has_identify_tool; then
    if winget_install "ImageMagick.ImageMagick"; then
      ok=1
    elif choco_install "imagemagick"; then
      ok=1
    fi
    refresh_windows_image_paths
  fi

  if ! has_webp_tool; then
    if winget_install "Google.Libwebp"; then
      ok=1
    elif choco_install "webp"; then
      ok=1
    fi
    refresh_windows_image_paths
  fi

  return $(( ok == 0 && ! has_webp_tool ))
}

install_on_macos() {
  if brew_install "imagemagick"; then
    return 0
  fi
  brew_install "webp" || return 1
}

install_on_linux() {
  apt_install || return 1
}

echo ">>> Görsel araçları (WebP / ImageMagick)"

if has_webp_tool && has_identify_tool; then
  echo "  Zaten kurulu."
  if has_webp_tool; then echo "  WebP üretimi: evet"; fi
  if has_identify_tool; then echo "  Boyut raporu (identify): evet"; fi
  exit 0
fi

INSTALLED=0
if is_windows; then
  if install_on_windows; then
    INSTALLED=1
  fi
elif [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
  if install_on_macos; then
    INSTALLED=1
  fi
else
  if install_on_linux; then
    INSTALLED=1
  fi
fi

if is_windows; then
  refresh_windows_image_paths
fi

echo ""
if has_webp_tool; then
  echo "  WebP üretimi: hazır ($(command -v cwebp || command -v magick))"
else
  echo "  WebP üretimi: yok — start.sh jpg/png ile devam eder"
fi

if has_identify_tool; then
  echo "  Boyut raporu: hazır ($(command -v identify || command -v magick))"
else
  echo "  Boyut raporu: yok — check_images.sh boyutları '?' gösterebilir"
fi

if [ "$INSTALLED" -eq 1 ] || has_webp_tool || has_identify_tool; then
  exit 0
fi

echo "  Uyarı: Otomatik kurulum tamamlanamadı."
if is_windows; then
  echo "  Manuel: winget install ImageMagick.ImageMagick"
  echo "         winget install Google.Libwebp"
fi
exit 0
