#!/bin/sh
# PicasaPy — Windows-zip összeállítása (#4).
#
# Pragmatikus MVP-megoldás: NEM önálló .exe-t vagy embeddable Python-
# csomagot épít (az bonyolultabb, Windowson tesztelendő build-lépéseket
# igényelne) — hanem a .whl-t egy telepítő útmutatóval (README-WINDOWS.txt)
# és egy egykattintásos install.bat-tal zip-eli össze. A felhasználó a
# saját gépén már meglévő (vagy python.org-ról telepített) Python mellé
# telepíti a `pip install`-lal, ahogy a Linux-oldalon is.
#
# Ez a szkript Linuxon fut (a wheel-t és a zip-et itt állítja össze) —
# magának a zip TARTALMÁNAK Windows alatti kipróbálása felhasználói kézi
# próba (ld. packaging/README.md).
#
# Használat:
#   ./packaging/build_windows_zip.sh
#
# Kimenet: packaging/dist/picasapy-windows-<verzió>.zip
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

# 1. Wheel build — saját, eldobható venv-ben (ld. build_deb.sh indoklása)
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
STAGE_NAME="picasapy-windows-${VERSION}"
STAGE_DIR="$BUILD_DIR/$STAGE_NAME"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

cp "$WHEEL_FILE" "$STAGE_DIR/"
sed "s/__VERSION__/$VERSION/g" "$SCRIPT_DIR/windows/README-WINDOWS.template.txt" \
    > "$STAGE_DIR/README-WINDOWS.txt"
sed "s/__VERSION__/$VERSION/g" "$SCRIPT_DIR/windows/install.bat.template" \
    > "$STAGE_DIR/install.bat"

# 3. zip
mkdir -p "$DIST_DIR"
ZIP_FILE="$DIST_DIR/${STAGE_NAME}.zip"
rm -f "$ZIP_FILE"
( cd "$BUILD_DIR" && zip -q -r "$ZIP_FILE" "$STAGE_NAME" )

echo "--- Kész ---"
echo "$ZIP_FILE"
unzip -l "$ZIP_FILE"
