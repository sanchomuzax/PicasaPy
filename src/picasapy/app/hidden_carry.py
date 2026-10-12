"""#4597: a még az ini-be be nem írt rejtés (`folders.hidden = 2`) átvitele
egy áthelyezett mappa új útvonalára.

A 2-es jelölés csak az indexben él; a régi útvonal sora az áthelyezés után
eltűnik, és az új útvonal ini-jében nincs `Hidden Folders` — a rejtett
(privát) mappa láthatóvá válna. Ezért az áthelyezés előbb megpróbálja beírni
az ini-be az új helyen; ha az nem megy (nem írható, vagy a mappa még nem
érhető el), az új útvonalra 2-es jelölésű sor kerül, amit a szinkron pótol.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from picasapy.ini import set_folder_hidden_in_ini

_log = logging.getLogger(__name__)


def carry_pending_hidden(conn: sqlite3.Connection, old: str, new: str) -> None:
    """A `old` részfa 2-es jelölésű mappáinak rejtését az `new` részfára viszi."""
    rows = conn.execute(
        "SELECT path FROM folders WHERE hidden = 2 AND (path = ? OR path LIKE ? ESCAPE '\\')",
        (old, _like_prefix(old)),
    ).fetchall()
    for row in rows:
        target = new + row["path"][len(old):]
        try:
            if not Path(target).is_dir():
                raise FileNotFoundError(target)
            set_folder_hidden_in_ini(target, True)
        except (OSError, RuntimeError, ValueError):
            _log.warning("A rejtés nem írható az áthelyezett mappába: %s", target)
            conn.execute(
                "INSERT INTO folders(path, has_ini, hidden) VALUES (?, 0, 2) "
                "ON CONFLICT(path) DO UPDATE SET hidden = 2",
                (target,),
            )
    conn.commit()


def _like_prefix(path: str) -> str:
    escaped = path.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return escaped.rstrip("/\\") + "/%"
