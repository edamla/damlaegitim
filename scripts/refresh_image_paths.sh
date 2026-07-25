#!/bin/bash
# Windows'ta winget ile kurulan ImageMagick / libwebp yollarını PATH'e ekler.
# install_image_tools.sh, start.sh, generate_webp.sh ve check_images.sh tarafından kullanılır.

refresh_image_tool_paths() {
  local dir base

  case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*) ;;
    *)
      [ "${OS:-}" = "Windows_NT" ] || return 0
      ;;
  esac

  for dir in "/c/Program Files/ImageMagick"*; do
    if [ -d "$dir" ]; then
      export PATH="$dir:$PATH"
    fi
  done

  if [ -n "${PROGRAMFILES:-}" ]; then
    base="${PROGRAMFILES//\\//}"
    for dir in "$base/ImageMagick"*; do
      if [ -d "$dir" ]; then
        export PATH="$dir:$PATH"
      fi
    done
  fi

  if [ -n "${LOCALAPPDATA:-}" ]; then
    base="${LOCALAPPDATA//\\//}"
    if [ -d "$base/Microsoft/WinGet/Packages" ]; then
      while IFS= read -r -d '' bin; do
        dir="$(dirname "$bin")"
        export PATH="$dir:$PATH"
      done < <(find "$base/Microsoft/WinGet/Packages" -name 'cwebp.exe' -print0 2>/dev/null)
    fi
    if [ -d "$base/Microsoft/WinGet/Links" ]; then
      while IFS= read -r -d '' bin; do
        dir="$(dirname "$bin")"
        export PATH="$dir:$PATH"
      done < <(find "$base/Microsoft/WinGet/Links" -name 'cwebp.exe' -print0 2>/dev/null)
    fi
  fi

  hash -r 2>/dev/null || true
}
