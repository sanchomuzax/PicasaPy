#!/bin/bash
# PicasaPy SessionStart hook — Claude Code on the web.
# A teszt-/futtatókörnyezet függőségeit telepíti, hogy a `pytest` MINDIG
# fusson (ne kelljen sessionönként újra felfedezni a hiányzó csomagokat).
# A lista a .github/workflows/ci.yml-lel szinkronban tartandó.
set -euo pipefail

# Csak a távoli (web) környezetben fut — lokálisan a fejlesztő maga kezeli.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Qt (PySide6) futtató rendszer-libek — offscreen QML-teszthez is kellenek.
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -qq || apt-get update -qq || true
  (sudo apt-get install -y -q libegl1 libgl1 libxkbcommon0 \
    || apt-get install -y -q libegl1 libgl1 libxkbcommon0) || true
fi

# Python-függőségek (a CI-vel azonos halmaz). Idempotens: a pip a meglévőket
# kihagyja. A pip-frissítés nem végzetes (a rendszer-pip néha nem cserélhető).
python -m pip install --upgrade pip || true
python -m pip install \
  PySide6 opencv-python-headless pillow piexif watchdog pytest pytest-cov

# Az offscreen Qt-platform a fejléc/QML-teszteknek is kell.
echo 'export QT_QPA_PLATFORM=offscreen' >> "$CLAUDE_ENV_FILE"
