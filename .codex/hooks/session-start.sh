#!/bin/bash
# PicasaPy SessionStart hook — CODEX.
#
# A Claude-változat (.claude/hooks/session-start.sh) párja. Két dolgot csinál:
#  1. szinkronban tartja a privát agent-kontextus repót (picasapy-agent), és
#     bemásolja a skilleket a checkout `.agents/skills/` mappájába;
#  2. a távoli (web) környezetben telepíti a teszt-futtatáshoz kellő
#     függőségeket, hogy a `pytest` mindig fusson.
#
# A projekt gyökerét a szkript a SAJÁT helyéből számolja, nem környezeti
# változóból — így nem függ attól, melyik agent milyen néven exportálja azt.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# --- Privát agent-kontextus (mindkét környezetben fut) ---------------------
# Az a példány nyer, amelyik már klónozva van; ha egyik sincs, a /workspace
# léte dönt (felhős session), különben a home.
if [ -d "$HOME/picasapy-agent/.git" ]; then
  AGENT_DIR="$HOME/picasapy-agent"
elif [ -d /workspace/picasapy-agent/.git ]; then
  AGENT_DIR=/workspace/picasapy-agent
elif [ -d /workspace ]; then
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
  mkdir -p "$PROJECT_DIR/.agents/skills"
  cp -r "$AGENT_DIR"/skills/. "$PROJECT_DIR/.agents/skills/" || true
else
  echo "FIGYELEM: a privát agent-kontextus ($AGENT_DIR) nincs meg." \
       "A munka megkezdése ELŐTT: git clone" \
       "https://github.com/sanchomuzax/picasapy-agent — ld. AGENTS.md."
fi

# --- Innentől csak a távoli (web) környezet: futtatókörnyezet -------------
# Helyi gépen a függőségek már megvannak; ott ne nyúljunk a rendszerhez.
if [ ! -d /workspace ]; then
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

# Az offscreen Qt-platform a fejléc/QML-teszteknek is kell. A környezetfájl
# neve agentfüggő; ha egyik sem ismert, a beállítás kimarad (nem hiba).
ENV_FILE="${CODEX_ENV_FILE:-${CLAUDE_ENV_FILE:-}}"
if [ -n "$ENV_FILE" ]; then
  echo 'export QT_QPA_PLATFORM=offscreen' >> "$ENV_FILE"
fi
