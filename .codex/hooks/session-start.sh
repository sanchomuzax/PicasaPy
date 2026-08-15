#!/bin/bash
# PicasaPy SessionStart hook — Claude Code on the web.
# A teszt-/futtatókörnyezet függőségeit telepíti, hogy a `pytest` MINDIG
# fusson (ne kelljen sessionönként újra felfedezni a hiányzó csomagokat).
# A lista a .github/workflows/ci.yml-lel szinkronban tartandó.
#
# Ezen felül szinkronban tartja a privát agent-kontextus repót
# (sanchomuzax/picasapy-agent): a CLAUDE.md onnan importálja a fejlesztői
# szabálykönyvet, a skilleket pedig ide másoljuk a checkoutba.
set -euo pipefail

# --- Privát agent-kontextus (mindkét környezetben fut) ---------------------
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  AGENT_DIR=/workspace/picasapy-agent
else
  AGENT_DIR="$HOME/picasapy-agent"
fi

if [ -d "$AGENT_DIR/.git" ]; then
  timeout 60 git -C "$AGENT_DIR" pull --quiet --rebase || true
else
  mkdir -p "$(dirname "$AGENT_DIR")" || true
  timeout 60 git clone --quiet \
    https://github.com/sanchomuzax/picasapy-agent.git "$AGENT_DIR" || true
fi

if [ -d "$AGENT_DIR/skills" ]; then
  mkdir -p "$CLAUDE_PROJECT_DIR/.claude/skills"
  cp -r "$AGENT_DIR"/skills/. "$CLAUDE_PROJECT_DIR/.claude/skills/" || true
else
  echo "FIGYELEM: a privát agent-kontextus ($AGENT_DIR) nincs meg." \
       "A munka megkezdése ELŐTT: add_repo sanchomuzax/picasapy-agent," \
       "majd git clone a fenti útvonalra — ld. CLAUDE.md."
fi

# --- Innentől csak a távoli (web) környezet: futtatókörnyezet -------------
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
