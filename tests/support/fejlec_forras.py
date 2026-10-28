"""A fénytábla fejlécének forrásszövege, a részeivel együtt (#6104).

A `LightboxHeader.qml` szétbomlott: a címsor, a gombsor, a javaslat-sor és a
leírás-sor külön komponens. A forrás-szintű őrök a fejléc szövegét egyben
kapják meg, ezért a fájlok sorrendje ugyanaz, mint a komponensek egymásutánja
a fejlécben. A horgonyok (`objectName`) egyediek, így az egymásba fűzés nem
téveszti meg a keresést.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

FEJLEC_RESZEI: tuple[str, ...] = (
    "LightboxHeader.qml",
    "LightboxHeaderTitle.qml",
    "LightboxHeaderButtons.qml",
    "LightboxHeaderSuggestionRow.qml",
    "LightboxHeaderDescription.qml",
)


def fejlec_forras() -> str:
    """A fejléc összes részének forrása, fájlonként egymás után."""
    mappa = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
    return "\n".join(
        (mappa / nev).read_text(encoding="utf-8") for nev in FEJLEC_RESZEI
    )
