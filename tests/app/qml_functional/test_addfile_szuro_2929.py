"""#2929: a „Fájl hozzáadása…" szűrője a FELISMERT halmazzal egyezzen.

Két, egymástól független lista élt: a beolvasás halmaza
(`scanner/filetypes.py`) és a fájlválasztó `nameFilters`-e
(`AddFileDialog.qml`). Ami a szűrőből kimaradt, azt a felhasználó nem is
tudta kiválasztani — pedig beolvasnánk. Ez az őr a KETTŐT méri egymáshoz,
nem egy harmadik, kézzel írt listához: így a következő kiterjesztés-bővítés
nem csúszhat el a két hely között.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app
from picasapy.scanner.filetypes import (
    PHOTO_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

_QML = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "AddFileDialog.qml"
).read_text(encoding="utf-8")


def _szuro_kiterjesztesei() -> set[str]:
    """A „Picture and Movie Files" szűrő kiterjesztései a QML-forrásból."""
    return {m.lower() for m in re.findall(r"\*(\.[a-z0-9]+)", _QML)}


def test_a_szuro_a_felismert_halmazt_adja():
    """A nyers (RAW) fájlok szándékosan maradnak ki: azokból ma nem
    jelenik meg kép (#528), tehát felajánlani őket félrevezető volna."""
    assert _szuro_kiterjesztesei() == PHOTO_EXTENSIONS | VIDEO_EXTENSIONS


def test_a_2929_ot_kiterjesztese_is_benne_van():
    """A jegy konkrét leletei — hogy a halmaz-egyezés ne süllyedjen el."""
    szuro = _szuro_kiterjesztesei()
    for kiterjesztes in (".tp", ".ts", ".m2v", ".ogg", ".ogv"):
        assert kiterjesztes in szuro
