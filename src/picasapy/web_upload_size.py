"""Webalbum feltöltési méret: a Beállítások ▸ Webalbumok fül legördülője (#5482).

Az eredeti sablon („Default upload size:”) öt tételt kínál, ebben a sorrendben:
Eredeti méret, 2048, 1600, 1024, 800 (a `CGeneralPrefsPage` sztringjei). A
kiválasztott méret pixelben a `Preferences/PWADefaultSize` kulcsba kerül. Az
„Eredeti méret” tétel értéke 0. A kulcs hiányában az alapérték az 1600 képpont,
vagyis a legördülő 2. indexe.

⚠️ A 0 jelentését a bináris nem igazolja: a spec az alapértéket (1600) és a
tételek sorrendjét rögzíti, az „eredeti” tétel tárolt értékét nem. A 0 itt a
PicasaPy saját jelölése.

A fül az éles appban továbbra is tiltott, ezért a legördülő csak a teszt
példányán kattintható.
"""

from __future__ import annotations

KULCS = "Preferences/PWADefaultSize"

#: a legördülő tételei, a sablon sorrendjében; 0 = eredeti méret
MERETEK = (0, 2048, 1600, 1024, 800)

ALAPERTELMEZETT_INDEX = MERETEK.index(1600)


def read_index(value: object) -> int:
    """A tárolt pixelméretből legördülő-index; hibás vagy hiányzó érték az alapérték."""
    if value is None or isinstance(value, bool):
        return ALAPERTELMEZETT_INDEX
    try:
        meret = int(str(value).strip())
    except ValueError:
        return ALAPERTELMEZETT_INDEX
    if meret not in MERETEK:
        return ALAPERTELMEZETT_INDEX
    return MERETEK.index(meret)


def size_at(index: int) -> int:
    """A legördülő indexéhez tartozó tárolt érték; a tartományon kívüli index az alapérték."""
    if 0 <= index < len(MERETEK):
        return MERETEK[index]
    return MERETEK[ALAPERTELMEZETT_INDEX]
