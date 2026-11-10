"""A régi Picasa-szűrők katalógusa (#571, #6443): újraexport.

A katalógus (névsor + felületi feliratok) tiszta adat, ezért az `ini`
rétegben él (`picasapy.ini.legacy_effects`, #6688): a szerkesztő vezérlője
az indulás kritikus útján olvassa, és a `picasapy.render` csomag importja
ott nem fér bele. Ez a modul a régi importútvonalat tartja.
"""

from __future__ import annotations

from picasapy.ini.legacy_effects import (
    LEGACY_EFFECT_KEYS,
    LEGACY_EFFECTS,
    LegacyEffect,
)

__all__ = ["LEGACY_EFFECTS", "LEGACY_EFFECT_KEYS", "LegacyEffect"]
