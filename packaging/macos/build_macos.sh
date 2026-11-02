#!/usr/bin/env bash
# ==============================================================================
# PicasaPy macOS Bundle & DMG Builder
#
# Usage:
#   ./packaging/macos/build_macos.sh [m1|arm64|x86_64|universal]
#
# Examples:
#   ./packaging/macos/build_macos.sh arm64      # Native Apple Silicon (M1/M2/M3)
#   ./packaging/macos/build_macos.sh universal  # Universal 2 (Intel + Apple Silicon)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# Auto-activate local .venv if available and not already in PATH
if [ -d "$REPO_ROOT/.venv/bin" ]; then
  export PATH="$REPO_ROOT/.venv/bin:$PATH"
fi

TARGET="${1:-auto}"
if [ "$TARGET" = "auto" ] || [ "$TARGET" = "m1" ]; then
  ARCH="$(uname -m)"
  if [ "$ARCH" = "arm64" ]; then
    TARGET="arm64"
  else
    TARGET="x86_64"
  fi
fi

echo "==> Building PicasaPy for macOS (target: $TARGET)"

# 1. Check prerequisites
command -v pyinstaller >/dev/null 2>&1 || {
  echo "Error: pyinstaller is not installed in the active environment." >&2
  exit 1
}
command -v hdiutil >/dev/null 2>&1 || {
  echo "Error: hdiutil is required (must run on macOS)." >&2
  exit 1
}
command -v codesign >/dev/null 2>&1 || {
  echo "Error: codesign is required (must run on macOS)." >&2
  exit 1
}

# 2. Ensure icon.icns exists
ICON_ICNS="src/picasapy/app/assets/icon.icns"
ICON_PNG="src/picasapy/app/assets/icon.png"
if [ ! -f "$ICON_ICNS" ] && [ -f "$ICON_PNG" ]; then
  echo "==> Generating $ICON_ICNS from $ICON_PNG..."
  ICONSET="$(mktemp -d)/icon.iconset"
  mkdir -p "$ICONSET"
  sips -z 16 16     "$ICON_PNG" --out "$ICONSET/icon_16x16.png" >/dev/null
  sips -z 32 32     "$ICON_PNG" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
  sips -z 32 32     "$ICON_PNG" --out "$ICONSET/icon_32x32.png" >/dev/null
  sips -z 64 64     "$ICON_PNG" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
  sips -z 128 128   "$ICON_PNG" --out "$ICONSET/icon_128x128.png" >/dev/null
  sips -z 256 256   "$ICON_PNG" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
  sips -z 256 256   "$ICON_PNG" --out "$ICONSET/icon_256x256.png" >/dev/null
  sips -z 512 512   "$ICON_PNG" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
  sips -z 512 512   "$ICON_PNG" --out "$ICONSET/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "$ICON_PNG" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$ICONSET" -o "$ICON_ICNS"
  rm -rf "$(dirname "$ICONSET")"
fi

# 3. Build translations
if [ -f scripts/build_qm.py ]; then
  echo "==> Compiling translations (.qm)..."
  python scripts/build_qm.py
fi

# Read project version
VERSION="$(grep -m1 '^version = ' pyproject.toml | sed -E 's/version = "(.*)"/\1/')"
mkdir -p packaging/dist dist

# Use a temporary staging directory outside of iCloud/FileProvider (e.g. /tmp)
# to prevent macOS from attaching 'com.apple.FinderInfo' which breaks codesign.
STAGE_DIR="$(mktemp -d -t picasapy_macos_XXXXXX)"
cleanup() {
  rm -rf "$STAGE_DIR"
}
trap cleanup EXIT

build_single_arch() {
  local arch="$1"
  local stage_app="$STAGE_DIR/dist/PicasaPy.app"
  local dest_app="dist/PicasaPy-${arch}.app"
  echo "==> Building standalone bundle for ${arch}..."

  rm -rf "$STAGE_DIR"
  mkdir -p "$STAGE_DIR"

  pyinstaller --noconfirm --clean \
    --workpath "$STAGE_DIR/build" \
    --distpath "$STAGE_DIR/dist" \
    packaging/macos/picasapy.spec

  # Strip Apple quarantine and Finder extended attributes before code signing
  xattr -cr "$stage_app" 2>/dev/null || true

  echo "==> Applying ad-hoc codesign to bundle..."
  codesign --force --deep -s - "$stage_app"
  codesign -v "$stage_app"

  rm -rf "$dest_app"
  cp -R "$stage_app" "$dest_app"
}

create_dmg() {
  local src_app="$1"
  local dmg_name="$2"
  local dmg_path="packaging/dist/${dmg_name}"

  # Create a clean folder containing only PicasaPy.app for the DMG root
  local dmg_root="$STAGE_DIR/dmg_root"
  rm -rf "$dmg_root"
  mkdir -p "$dmg_root"
  cp -R "$src_app" "$dmg_root/PicasaPy.app"

  echo "==> Packaging into $dmg_path..."
  rm -f "$dmg_path"
  hdiutil create \
    -volname "PicasaPy" \
    -srcfolder "$dmg_root" \
    -ov \
    -format UDZO \
    "$dmg_path"
  echo "==> Created $dmg_path"
}

if [ "$TARGET" = "arm64" ]; then
  build_single_arch "arm64"
  # Also keep/symlink as dist/PicasaPy.app
  rm -rf dist/PicasaPy.app
  cp -R dist/PicasaPy-arm64.app dist/PicasaPy.app
  create_dmg "dist/PicasaPy.app" "PicasaPy-${VERSION}-macOS-arm64.dmg"

elif [ "$TARGET" = "x86_64" ]; then
  build_single_arch "x86_64"
  rm -rf dist/PicasaPy.app
  cp -R dist/PicasaPy-x86_64.app dist/PicasaPy.app
  create_dmg "dist/PicasaPy.app" "PicasaPy-${VERSION}-macOS-x86_64.dmg"

elif [ "$TARGET" = "universal" ]; then
  # If arm64 and x86_64 apps are not built yet, build them if possible
  if [ ! -d "dist/PicasaPy-arm64.app" ]; then
    echo "dist/PicasaPy-arm64.app not found. Building arm64..."
    build_single_arch "arm64"
  fi

  if [ ! -d "dist/PicasaPy-x86_64.app" ]; then
    if [ "$(uname -m)" = "arm64" ]; then
      echo "Apple Silicon host detected: Building x86_64 under Rosetta 2..."
      rm -rf "$STAGE_DIR"
      mkdir -p "$STAGE_DIR"
      arch -x86_64 pyinstaller --noconfirm --clean \
        --workpath "$STAGE_DIR/build" \
        --distpath "$STAGE_DIR/dist" \
        packaging/macos/picasapy.spec
      xattr -cr "$STAGE_DIR/dist/PicasaPy.app" 2>/dev/null || true
      codesign --force --deep -s - "$STAGE_DIR/dist/PicasaPy.app"
      rm -rf dist/PicasaPy-x86_64.app
      cp -R "$STAGE_DIR/dist/PicasaPy.app" dist/PicasaPy-x86_64.app
    else
      echo "Error: dist/PicasaPy-x86_64.app is missing." >&2
      exit 1
    fi
  fi

  echo "==> Merging arm64 and x86_64 bundles into Universal bundle..."
  local stage_uni="$STAGE_DIR/PicasaPy.app"
  python packaging/macos/merge_universal.py \
    dist/PicasaPy-arm64.app \
    dist/PicasaPy-x86_64.app \
    "$stage_uni"

  create_dmg "$stage_uni" "PicasaPy-${VERSION}-macOS-universal.dmg"
  rm -rf dist/PicasaPy.app
  cp -R "$stage_uni" dist/PicasaPy.app
else
  echo "Unknown target: $TARGET. Expected: arm64, x86_64, or universal." >&2
  exit 1
fi

echo "==> Done! Output artifacts in packaging/dist/:"
ls -lh packaging/dist/*.dmg 2>/dev/null || true
