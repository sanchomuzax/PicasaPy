#!/bin/bash
# PicasaPy SessionStart hook — CODEX.
#
# Vékony belépő: a tényleges munkát a `scripts/bootstrap_env.sh` végzi, közösen
# a Claude-hookkal (`.claude/hooks/session-start.sh`). Korábban a két hook a
# teljes logikát — a telepítendő csomagok listájával együtt — külön-külön
# hordozta; a másolatok elcsúsztak egymástól és a CI-től is.
#
# A skillek célmappája agentfüggő, ez az egyetlen különbség a két hook között.
set -euo pipefail

exec "$(dirname "${BASH_SOURCE[0]}")/../../scripts/bootstrap_env.sh" .agents/skills
