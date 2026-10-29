"""Az alkalmazás-indító forrásszövege a forrás-szintű őröknek (#6155).

Az `application.py` 2026-10-29 óta több modulra bomlik (`application_*.py`,
`_application_constants.py`); a vezérlők létrehozása és a QML-regisztráció
már nem egyetlen fájlban áll. Az őrök ezért az egész családot olvassák.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app


def indito_fajlok() -> list[Path]:
    gyoker = Path(picasapy.app.__file__).parent
    return sorted({*gyoker.glob("application*.py"), *gyoker.glob("_application*.py")})


def indito_forras() -> str:
    return "\n".join(ut.read_text(encoding="utf-8") for ut in indito_fajlok())
