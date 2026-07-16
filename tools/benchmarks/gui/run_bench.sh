#!/bin/bash
# GUI toolkit benchmark futtató — a 3 demót egymás után indítja.
# Minden demóból Esc-kel lépsz ki, és jön a következő.
# Wayland-fix a Raspberry Connect-hez (ld. rpi5-wayland-app-fix skill).
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
THUMBS="${1:-$DIR/../../../research/benchmarks/thumbs}"
COUNT="${2:-5000}"
VENV="$DIR/../../../research/benchmarks/.venv/bin/python"

export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

echo "=========================================="
echo " 1/3: PySide6 / QML GridView"
echo "=========================================="
QT_QPA_PLATFORM=wayland "$VENV" "$DIR/qml_grid.py" "$THUMBS" "$COUNT"

echo "=========================================="
echo " 2/3: GTK4 GridView"
echo "=========================================="
GDK_BACKEND=wayland python3 "$DIR/gtk_grid.py" "$THUMBS" "$COUNT"

echo "=========================================="
echo " 3/3: Dear PyGui"
echo "=========================================="
# A DPG (GLFW) X11-et akar: dummy xauth cookie a lazy Xwayland :0-hoz
if ! xauth list :0 2>/dev/null | grep -q "unix:0"; then
    xauth add :0 . "$(mcookie)"
fi
DISPLAY=:0 "$VENV" "$DIR/dpg_grid.py" "$THUMBS" "$COUNT"

echo "=== KÉSZ mind a 3 demó ==="
