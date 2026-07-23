#!/bin/sh
# PicasaPy — Debian-csomag (.deb) összeállítása RPi/Debian/Ubuntu célra (#4).
#
# Használat (a repó gyökeréből vagy bárhonnan):
#   ./packaging/build_deb.sh
#
# Kimenet: packaging/dist/picasapy_<verzió>_all.deb
#
# A csomag pip-fűggetlenül is telepíthető: `sudo dpkg -i picasapy_*_all.deb`
# — a postinst-szkript ekkor internetkapcsolatot használva (PyPI) építi fel
# a futtatáshoz szükséges dedikált virtuális környezetet. Részletek:
# packaging/README.md.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
BUILD_DIR="$SCRIPT_DIR/.build"
DIST_DIR="$SCRIPT_DIR/dist"

PYTHON_BIN=${PYTHON_BIN:-}
if [ -z "$PYTHON_BIN" ]; then
    if command -v python3.12 >/dev/null 2>&1; then
        PYTHON_BIN=python3.12
    else
        PYTHON_BIN=python3
    fi
fi

VERSION=$(grep -m1 '^version = ' "$REPO_ROOT/pyproject.toml" | sed -E 's/version = "(.*)"/\1/')
if [ -z "$VERSION" ]; then
    echo "HIBA: nem sikerült kiolvasni a verziót a pyproject.toml-ból." >&2
    exit 1
fi
echo "PicasaPy verzió: $VERSION (python: $PYTHON_BIN)"

# 1. Wheel build — saját, eldobható venv-ben (a rendszer Python sok
# Debian/Ubuntu-n "externally managed" — PEP 668 —, oda nem pip-elhetünk).
echo "--- Wheel build ---"
BUILD_VENV="$BUILD_DIR/build-venv"
if [ ! -x "$BUILD_VENV/bin/python3" ]; then
    "$PYTHON_BIN" -m venv "$BUILD_VENV"
fi
"$BUILD_VENV/bin/python3" -m pip install --quiet --upgrade pip build

cd "$REPO_ROOT"
"$BUILD_VENV/bin/python3" -m build --wheel --outdir "$REPO_ROOT/dist"

WHEEL_FILE=$(ls "$REPO_ROOT/dist"/picasapy-"$VERSION"-*.whl 2>/dev/null | head -n1)
if [ -z "$WHEEL_FILE" ]; then
    echo "HIBA: nem található a legyártott .whl a dist/ alatt." >&2
    exit 1
fi
echo "Wheel: $WHEEL_FILE"

# 2. Staging könyvtár összeállítása
STAGE_DIR="$BUILD_DIR/picasapy_${VERSION}_all"
rm -rf "$STAGE_DIR"
mkdir -p \
    "$STAGE_DIR/DEBIAN" \
    "$STAGE_DIR/opt/picasapy/dist" \
    "$STAGE_DIR/usr/share/applications" \
    "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps"

sed "s/__VERSION__/$VERSION/" "$SCRIPT_DIR/debian/control.template" \
    > "$STAGE_DIR/DEBIAN/control"
cp "$SCRIPT_DIR/debian/postinst" "$STAGE_DIR/DEBIAN/postinst"
cp "$SCRIPT_DIR/debian/postrm" "$STAGE_DIR/DEBIAN/postrm"
chmod 0755 "$STAGE_DIR/DEBIAN/postinst" "$STAGE_DIR/DEBIAN/postrm"

cp "$SCRIPT_DIR/debian/picasapy.desktop" \
    "$STAGE_DIR/usr/share/applications/picasapy.desktop"
cp "$REPO_ROOT/src/picasapy/app/assets/icon.png" \
    "$STAGE_DIR/usr/share/icons/hicolor/256x256/apps/picasapy.png"
cp "$WHEEL_FILE" "$STAGE_DIR/opt/picasapy/dist/"

# 3. .deb build
mkdir -p "$DIST_DIR"
DEB_FILE="$DIST_DIR/picasapy_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$STAGE_DIR" "$DEB_FILE"

echo "--- Kész ---"
echo "$DEB_FILE"
dpkg-deb --info "$DEB_FILE"
