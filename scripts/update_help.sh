#!/usr/bin/env bash
# PicasaPy — napi felhasználói súgófrissítés headless Claude Code-dal (#2051).
#
# A súgó a megszűnt Picasa 3 online súgóját váltja ki, ezért NET NÉLKÜL is
# olvashatónak kell lennie: a `docs/help/` alatti markdown maga a termék, nem
# egy weboldal forrása.
#
# FONTOS — miért saját munkafa: ebből a repóból több Claude-session dolgozik
# egyszerre, és a fő checkout bármelyik pillanatban egy másik session ágán
# állhat. Egy éjszakai `git checkout main` ott elvinné a munkájukat, ezért ez
# a szkript SOHA nem a közös checkoutban dolgozik, hanem a sajátjában.
set -euo pipefail

FO_CHECKOUT="${FO_CHECKOUT:-$HOME/Documents/PicasaPy}"
MUNKAFA="${MUNKAFA:-$HOME/picasapy-sugo}"
AG="${AG:-sugo/auto}"
ZAR="${ZAR:-/tmp/picasapy-update-help.lock}"
KOLTSEGKERET="${KOLTSEGKERET:-8}"

# Egyszerre egy futás. A cron és egy kézi indítás könnyen egymásra csúszna, és
# két agent ugyanazt a fát írná.
exec 9>"$ZAR"
if ! flock -n 9; then
  echo "$(date -Is) mar fut egy masik peldany, kilepek" >&2
  exit 0
fi

# A munkafa a fő checkout git-adatbázisát használja, de külön dolgozó fát kap.
if [ ! -d "$MUNKAFA/.git" ] && [ ! -f "$MUNKAFA/.git" ]; then
  git -C "$FO_CHECKOUT" worktree add -B "$AG" "$MUNKAFA" origin/main
fi

cd "$MUNKAFA"
ALLAPOT="$MUNKAFA/docs/help/.last_documented_commit"
NAPLO="$MUNKAFA/docs/help/.update.log"
PROMPT="$MUNKAFA/.claude/prompts/update-help.md"
ENGEDELYEK="$MUNKAFA/.claude/help-agent-settings.json"

git fetch -q origin
git reset -q --hard origin/main
mkdir -p "$(dirname "$NAPLO")"

naplo() { echo "$(date -Is) $*" >> "$NAPLO"; }

fej=$(git rev-parse HEAD)
utolso=$(cat "$ALLAPOT" 2>/dev/null || git rev-list --max-parents=0 HEAD | tail -1)

if [ "$fej" = "$utolso" ]; then
  naplo "nincs uj commit $utolso ota"
  exit 0
fi

# Csak az számít, amit a FELHASZNÁLÓ lát. A kizárás a repó tényleges
# mappáihoz igazodik: a research/, tools/, scripts/, tests/ és packaging/
# fejlesztői terep, a docs/ pedig a saját dokumentációnk (a súgót is beleértve).
valtozott=$(git diff --name-only "$utolso" "$fej" -- . \
  ':!docs' ':!tests' ':!research' ':!tools' ':!scripts' ':!packaging' \
  ':!.github' ':!.claude' ':!temp_*' || true)

if [ -z "$valtozott" ]; then
  echo "$fej" > "$ALLAPOT"
  naplo "csak nem-felhasznaloi valtozas, kihagyva ($utolso -> ${fej:0:7})"
  exit 0
fi

osszefoglalo=$(git log --oneline "$utolso".."$fej")
reszletek=$(git diff "$utolso" "$fej" -- . \
  ':!docs' ':!tests' ':!research' ':!tools' ':!packaging' | head -c 200000)

feladat=$(cat "$PROMPT")
feladat="$feladat

## Commitok a legutóbbi súgófrissítés óta
$osszefoglalo

## Diff (200 KB-nál csonkolva)
\`\`\`diff
$reszletek
\`\`\`"

naplo "agent indul ($utolso -> ${fej:0:7}), ${valtozott//$'\n'/, }"

# A `--max-turns` NEM létezik ebben a Claude Code-ban (v2.1.252) — a futást a
# költségkeret határolja. A tool-engedélyek fájlból jönnek, nem a parancssorból.
if ! claude -p "$feladat" \
      --settings "$ENGEDELYEK" \
      --output-format text \
      --max-budget-usd "$KOLTSEGKERET" >> "$NAPLO" 2>&1; then
  naplo "az agent hibaval vagy keretkimeritessel allt le — a sugot NEM commitolom"
  exit 1
fi

if git diff --quiet -- docs/help; then
  naplo "az agent nem valtoztatott a sugon ($utolso -> ${fej:0:7})"
else
  git add docs/help
  git -c user.name="PicasaPy súgó-frissítő" -c user.email="noreply@anthropic.com" \
      commit -q -m "docs(help): napi automata súgófrissítés (${utolso:0:7} -> ${fej:0:7})"
  git push -q origin HEAD:main
  naplo "sugo frissitve es feltoltve"
fi

echo "$fej" > "$ALLAPOT"
