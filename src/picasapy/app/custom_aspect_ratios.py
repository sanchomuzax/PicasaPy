"""Egyéni vágás-képarányok (#448): a "Fotó vágása" panel beépített
arány-listája (`EditorPanel.qml` `aspectPresets`) mellett a felhasználó
SAJÁT arányt is felvehet — szélesség × magasság + név (a jegy szerint a
listában "4 x 6   Small print" alakban jelenik meg), és törölhető is.

Tárolás: a `custom_collections.py` mintáját követve, ugyanabban a
QSettings-ben, egyetlen JSON-szerializált kulcs alatt — ez a modul csak
TISZTA függvényeket ad, a QSettings I/O a hívó (controller-mixin) dolga."""

from __future__ import annotations

import json
from dataclasses import dataclass

#: A felhasználói egyéni arányok listája ez alatt az EGY QSettings-kulcs
#: alatt él, JSON-szerializálva.
CUSTOM_ASPECT_RATIOS_SETTING_KEY = "crop/customAspectRatios"

#: A legutóbb használt arány kulcsa (#448 `lastCropRatio`) — a beépített
#: preset "key" mezője (pl. "4x6") vagy egyéni arány esetén
#: "custom:<név>:<szélesség>x<magasság>" (ld. EditorPanel.qml aspectList).
LAST_CROP_RATIO_SETTING_KEY = "crop/lastRatioKey"


@dataclass(frozen=True)
class CustomAspectRatio:
    """Egy felhasználói egyéni képarány: név + szélesség/magasság (bármilyen
    mértékegységben — csak az ARÁNYuk számít, a QML ebből képez `ratio`-t)."""

    name: str
    width: float
    height: float


def parse_custom_aspect_ratios(raw: str | None) -> tuple[CustomAspectRatio, ...]:
    """A QSettings-ből olvasott nyers JSON-string feldolgozása.

    Hiányzó/sérült/érvénytelen bemenetnél üres tuple — egy hibás beállítás-
    fájl NEM omlaszthatja el az alkalmazást, legfeljebb az egyéni arányok
    tűnnek el (amíg a felhasználó újra fel nem veszi őket)."""
    if not raw:
        return ()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return ()
    if not isinstance(data, list):
        return ()
    result: list[CustomAspectRatio] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        width = item.get("width")
        height = item.get("height")
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
            continue
        if width <= 0 or height <= 0:
            continue
        result.append(
            CustomAspectRatio(name=name, width=float(width), height=float(height))
        )
    return tuple(result)


def serialize_custom_aspect_ratios(ratios: tuple[CustomAspectRatio, ...]) -> str:
    """Az egyéni arány-lista JSON-szerializálása a QSettings-be íráshoz."""
    return json.dumps(
        [{"name": r.name, "width": r.width, "height": r.height} for r in ratios],
        ensure_ascii=False,
    )


def add_custom_aspect_ratio(
    ratios: tuple[CustomAspectRatio, ...], width: float, height: float, name: str
) -> tuple[CustomAspectRatio, ...]:
    """Új egyéni arány hozzáadása.

    Érvénytelen (nem-pozitív) méretet vagy üres/csak-szóköz nevet csendben
    elutasít (változatlan listát ad vissza) — a hívó UI a validációt már
    elvégzi (pl. az Ok gomb tiltásával), de a réteg saját magát is védi.
    Pontos duplikátumot (azonos név+méret) nem vesz fel kétszer."""
    stripped = name.strip() if isinstance(name, str) else ""
    if not stripped:
        return ratios
    try:
        width = float(width)
        height = float(height)
    except (TypeError, ValueError):
        return ratios
    if width <= 0 or height <= 0:
        return ratios
    for r in ratios:
        if r.name == stripped and r.width == width and r.height == height:
            return ratios
    return ratios + (CustomAspectRatio(name=stripped, width=width, height=height),)


def delete_custom_aspect_ratio(
    ratios: tuple[CustomAspectRatio, ...], name: str, width: float, height: float
) -> tuple[CustomAspectRatio, ...]:
    """Egyéni arány törlése — a név+méret hármas azonosítja (ld. #448 jegy:
    a lista törölhető tételei); nem-egyező bejegyzésnél nincs teendő."""
    try:
        width = float(width)
        height = float(height)
    except (TypeError, ValueError):
        return ratios
    return tuple(
        r
        for r in ratios
        if not (r.name == name and r.width == width and r.height == height)
    )
