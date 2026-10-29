"""Az infósáv fényképadatait összerakó formázók."""

from __future__ import annotations

from PySide6.QtCore import QLocale

from .formatting_dates import _info_datum
from .formatting_sizes import format_size

def _dimensions_text(photo, tr) -> str:
    """`SZxM képpont` szöveg a felbontáshoz."""
    return (
        tr("%1x%2 pixels")
        .replace("%1", str(photo.width))
        .replace("%2", str(photo.height))
    )


def _info_cimkek(photo, tr) -> str:
    """`Címkék: …` a sáv végén (#2565).

    Az előtag MÉRT szöveg: `CThumbUI::GetTagInfo::format`
    (`referencia/stringres-en-hu.tsv:691`) — `Tags: ` → `Címkék: `. A
    `keywords` az indexben VESSZŐVEL tagolt sztring, nem lista.
    """
    nyers = photo.keywords or ""
    cimkek = [k.strip() for k in nyers.split(",") if k.strip()]
    if not cimkek:
        return ""
    return tr("Tags: %1").replace("%1", ", ".join(cimkek))


def photo_info_text(photo, locale: QLocale, tr, szamlalo: str = "") -> str:
    """A kék infó-sáv tartalma, Picasa-stílusban:
    `név   dátum   SZxM képpont   méret   (összes / aktuális)   Címkék: …`.

    A sorrend a tulajdonos TELJES SZÉLESSÉGŰ felvételéről való
    (`research/felirat-ki-bekapcsolva/picasa3-felirat-bekapcsolva. 223224.jpg`,
    1920 × 1080)::

        AI > JonasBen_…png   2023. 05. 10. 16:30:05   896x1344 képpont
        807 KB   (82 / 3)   Címkék: AI image

    ⚠️ **A `szamlalo` helye MÉRT, és egyszer már elrontottuk.** A #2565
    körében a számláló tévesen KIKERÜLT a sávból: az akkori bizonyíték
    (`141421.jpg`) FÉL SZÉLESSÉGŰ Picasa-ablakot mutatott, ahol a sáv
    szövege le volt vágva — és a levágást olvastuk hiánynak. A fenti,
    teljes szélességű felvétel megcáfolta. A számláló a fájlméret UTÁN és a
    címkék ELŐTT áll; üres sztringnél kimarad (rács-kijelölés, ahol nincs
    „hányadik").
    """
    parts = [photo.name]
    datum = _info_datum(photo, locale)
    if datum:
        parts.append(datum)
    if photo.width and photo.height:
        parts.append(_dimensions_text(photo, tr))
    parts.append(format_size(photo.size, locale, tr))
    if szamlalo:
        parts.append(szamlalo)
    cimkek = _info_cimkek(photo, tr)
    if cimkek:
        parts.append(cimkek)
    return "   ".join(parts)

