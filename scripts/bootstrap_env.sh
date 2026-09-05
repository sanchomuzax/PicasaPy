#!/bin/bash
# PicasaPy session-bootstrap — a Claude- és a Codex-hook KÖZÖS magja.
#
# Két dolgot csinál:
#  1. szinkronban tartja a privát agent-kontextus repót (picasapy-agent), és
#     bemásolja a skilleket a hívó által megadott mappába;
#  2. a távoli (felhős) környezetben felépíti a futtatókörnyezetet, hogy a
#     teljes tesztkészlet és a lint MINDIG futtatható legyen.
#
# Korábban ez a logika két, majdnem azonos szkriptben élt (`.claude/hooks/` és
# `.codex/hooks/`), a telepítendő csomagok listájával együtt bemásolva. A
# másolatok elcsúsztak egymástól és a CI-től is; a csomaglisták azóta egyetlen
# helyen élnek (`pyproject.toml`, `packaging/qt-runtime-deps.txt`), ez a
# szkript pedig csak lekérdezi őket. Őr: `tests/test_kornyezet_szinkron.py`.
#
# Használat:  scripts/bootstrap_env.sh <skill-célmappa a projekten belül>
# Például:    scripts/bootstrap_env.sh .claude/skills
set -euo pipefail

SKILLS_ALKONYVTAR="${1:-.claude/skills}"

# A projekt gyökerét a szkript a SAJÁT helyéből számolja, nem környezeti
# változóból — így nem függ attól, melyik agent milyen néven exportálja azt.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- 1. Privát agent-kontextus (mindkét környezetben fut) -----------------
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
  mkdir -p "$PROJECT_DIR/$SKILLS_ALKONYVTAR"
  cp -r "$AGENT_DIR"/skills/. "$PROJECT_DIR/$SKILLS_ALKONYVTAR/" || true
else
  echo "FIGYELEM: a privát agent-kontextus ($AGENT_DIR) nincs meg." \
       "A munka megkezdése ELŐTT: add_repo sanchomuzax/picasapy-agent," \
       "majd git clone a fenti útvonalra — ld. CLAUDE.md / AGENTS.md."
fi

# --- 2. Innentől csak a távoli (web) környezet ----------------------------
# Helyi gépen a függőségek már megvannak; ott ne nyúljunk a rendszerhez.
# A `PICASAPY_BOOTSTRAP_REMOTE` kézi felülbírálás — ezzel futtatja a CI is,
# ami így ugyanazt az utat járja be, mint egy valódi felhős session.
if [ "${PICASAPY_BOOTSTRAP_REMOTE:-}" != "1" ] \
   && [ "${CLAUDE_CODE_REMOTE:-}" != "true" ] \
   && [ ! -d /workspace ]; then
  exit 0
fi

# Qt (PySide6) rendszer-libek — offscreen QML-teszthez is kellenek. A lista
# a `packaging/qt-runtime-deps.txt`; az idézőjel-nélküli behelyettesítés
# szándékos, a csomagnevek külön argumentumként kellenek.
if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  APT_CSOMAGOK="$(python3 "$PROJECT_DIR/scripts/print_dependencies.py" --apt)"
  sudo apt-get update -qq || apt-get update -qq || true
  # shellcheck disable=SC2086
  (sudo apt-get install -y -q $APT_CSOMAGOK \
    || apt-get install -y -q $APT_CSOMAGOK) || true
fi

# Python-függőségek: futásidejű + fejlesztői, a `pyproject.toml`-ból.
# Idempotens: a pip a meglévőket kihagyja. A pip-frissítés nem végzetes (a
# rendszer-pip néha nem cserélhető).
PIP_CSOMAGOK="$(python3 "$PROJECT_DIR/scripts/print_dependencies.py" --all)"
python3 -m pip install --upgrade pip || true
# shellcheck disable=SC2086
python3 -m pip install $PIP_CSOMAGOK

# Megszakadt teszt-körök maradékának takarítása (#1358). Eddig ez csak
# tesztfuttatáskor futott le, és csak a 3 óránál régebbi könyvtárakra — így
# 2026-08-24-én négy fiatal, de halott maradék ~1,5 GB-ot foglalt a /tmp-en,
# és a tulajdonosnak kellett szólnia. Élő futás könyvtárához nem nyúl.
python3 "$PROJECT_DIR/scripts/run_tests.py" --csak-takaritas || true

# #1867: a fenti sor CSAK a saját basetempjeinket takarítja. A munkamásolatok
# és a halott munkamenetek scratchpadjei külön osztály — egyetlen éjszaka
# 4,6 GB-ot és 17 fölösleges munkamásolatot hagyott, és a /tmp 82%-on
# riasztott a tulajdonosnál.
#
# Itt SZÁNDÉKOSAN csak JELENTÜNK, nem törlünk: a session-start hook minden
# indulásnál fut, felügyelet nélkül is, és egy téves törlés
# visszafordíthatatlan. A `--torol` az emberi (vagy kör-végi) döntés.
python3 "$PROJECT_DIR/scripts/takarito.py" || true

# Az offscreen Qt-platform a fejléc/QML-teszteknek is kell. A környezetfájl
# neve agentfüggő; ha egyik sem ismert, a beállítás kimarad (nem hiba).
ENV_FILE="${CLAUDE_ENV_FILE:-${CODEX_ENV_FILE:-}}"
if [ -n "$ENV_FILE" ]; then
  echo 'export QT_QPA_PLATFORM=offscreen' >> "$ENV_FILE"
fi

# A szabálykönyvből CSAK a két CLAUDE.md töltődik be magától; a PROTOKOLL.md és
# a docs/lapok.md nem. A 2026-09-02/03-i kör bizonyította, hogy a puszta
# hivatkozás kevés: a repó-szétválasztás szabálya BE VOLT töltve, és aznap
# kétszer sérült. Ezért a néhány teherhordó szabályt minden induláskor
# kiírjuk — a szöveg a privát repóban él, mert a munkavégzés módja.
EMLEKEZTETO="$HOME/picasapy-agent/eszkozok/session_emlekezteto.md"
if [ -r "$EMLEKEZTETO" ]; then
  echo
  cat "$EMLEKEZTETO"
  echo
fi
