"""Mappa-dátum kézi felülírása a `.picasa.ini` `[Picasa]` szekciójában (#320).

**A kulcs a valódi Picasában IS létezik (#2304, 2026-09-04).** Korábban
PicasaPy-kiterjesztésnek hittük, mert a Buchinger-visszafejtés és az exe
string-tábla sem sorolta fel mappa-szinten (csak az albumoknál —
`[.album:token]` — van `date=ISO8601`). A tulajdonos gépén a Picasa 3 által
írt ini viszont ezt tartalmazza:

```ini
[Picasa]
P2category=Exported Pictures
date=46269.390486
```

⇒ **A Picasa OLE Variant-időt ír** (napok 1899-12-30 óta):
1899-12-30 + 46269,390486 nap = 2026-09-04 09:22:17, és a mappa pontosan
akkor jött létre.

Az olvasó ezért MINDKÉT alakot érti. **Írni** egyelőre ISO-ban írunk — de
⚠️ **nincs mérve, hogy a Picasa az ISO-alakot elfogadja-e**: csak azt
tudjuk, mit ír, nem azt, mit olvas. Amíg ez nem dőlt el, a mi ISO-nk
kockázat egy kétirányú munkamenetben (Picasa ↔ PicasaPy ugyanazon a
mappán). A kérdés a #2304 jegyben nyitva van.

Alapból a mappa dátuma a legrégebbi kép felvételi ideje (`index/sync.py`,
`_sync_folder`); ez a modul a felhasználó KÉZI felülírását olvassa/írja —
ha jelen van, a szinkron ezt veszi át a számított érték helyett.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from .document import IniDocument

_FOLDER_DATE_KEY = "date"
_FOLDER_SECTION = "Picasa"

# ISO 8601 dátum (év-hónap-nap), órarész nélkül — a mappa-szintű dátum-
# felülírásnak nincs értelme óra/perc pontossággal.
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# --- OLE Variant-idő (#2304) ------------------------------------------
#
# A VALÓDI Picasa a mappa dátumát NEM ISO-ban írja, hanem OLE Variant
# időként: napok az 1899-12-30-i alapponttól, tizedesként a napon belüli
# idő. Bizonyíték a tulajdonos gépéről (2026-09-04):
#
#     [Picasa]
#     P2category=Exported Pictures
#     date=46269.390486
#
# 1899-12-30 + 46269,390486 nap = 2026-09-04 09:22:17 — pontosan akkor
# jött létre a mappa. A modul eddig csak ISO-t fogadott, tehát a valódi
# Picasa-mappák dátumát NÉMÁN eldobta.
_VARIANT_ALAPPONT = datetime(1899, 12, 30)
_VARIANT_SZAM = re.compile(r"^\d+(\.\d+)?$")
#: Ésszerű tartomány: 1900-tól nagyjából 2100-ig. Az ezen kívüli szám nem
#: dátum, hanem valami más — nem találgatunk.
_VARIANT_MIN = 1.0
_VARIANT_MAX = 73_500.0


def _variant_datum(ertek: str) -> str | None:
    """OLE Variant-idő -> ISO nap, vagy `None`, ha nem az."""
    if not _VARIANT_SZAM.match(ertek):
        return None
    napok = float(ertek)
    if not (_VARIANT_MIN <= napok <= _VARIANT_MAX):
        return None
    return (_VARIANT_ALAPPONT + timedelta(days=napok)).date().isoformat()


def _ervenyes_iso(ertek: str) -> bool:
    """ISO-alakú ÉS létező nap — a `2019-13-45` alakilag illeszkedne."""
    if not _ISO_DATE.match(ertek):
        return False
    try:
        datetime.strptime(ertek, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def is_valid_folder_date(date_iso: str) -> bool:
    """Érvényes-e a `date_iso` ISO 8601 (év-hónap-nap) alakban — a hívó
    (controller-slot, QML-dialógus) ezzel véd a hibás formátum ellen.

    ⚠️ Ez az ÍRÁS kapuja: a BEMENET ISO. A kiírt alak viszont **OLE
    Variant** (#2353) — a Picasa `atof`-fal olvas, és az ISO-ból
    1905-öt csinálna. Az OLVASÁS mindkét alakot érti.
    """
    return _ervenyes_iso(date_iso.strip())


def read_folder_date_override(document: IniDocument) -> str | None:
    """A `[Picasa]` szekció kézi `date=` felülírása, ha érvényes ISO-dátum.

    Érvénytelen (nem ISO-formátumú) vagy hiányzó kulcsnál `None` — a hívó
    ilyenkor a számított (legrégebbi kép) dátumra esik vissza."""
    section = document.section(_FOLDER_SECTION)
    if section is None:
        return None
    value = section.get(_FOLDER_DATE_KEY)
    if value is None:
        return None
    nyers = value.strip()
    if _ervenyes_iso(nyers):
        return nyers
    # #2304: a valódi Picasa Variant-időt ír — ezt is értenünk kell.
    return _variant_datum(nyers)


#: A `%f` alapértelmezése hat tizedes — a Picasa-írta sor pontosan ilyen
#: (`date=46269.390486`), és az írója is `"%f"`-fel formáz (`0x00710332`).
_VARIANT_TIZEDES = 6


def variant_ertek(date_iso: str) -> str:
    """ISO nap -> a `.picasa.ini`-be írandó OLE Variant-alak (#2353).

    ⚠️ **ISO-t nem szabad kiírni.** A Picasa a `[Picasa] date=` értékét
    `atof`-fal olvassa (`0x0044248d` → a `0x00c080d7` CRT-hívás),
    hibajelzés NÉLKÜL: a `date=2019-07-04` sorból nála **`2019.0`** lesz,
    ami Variant-napként **1905-07-08**. A mappa 1905-be kerülne a bal
    hasáb évcsoportjában — és mivel a felhasználó ugyanazt a mappát nyitja
    meg mindkét programban (#2304), ez néma adatromlás.

    A nap egész, tehát a törtrész (a napon belüli idő) nulla; a hat
    tizedes a `%f` alakját tartja.
    """
    nap = datetime.strptime(date_iso, "%Y-%m-%d")
    return f"{(nap - _VARIANT_ALAPPONT).days:.{_VARIANT_TIZEDES}f}"


def with_folder_date_override(document: IniDocument, date_iso: str) -> IniDocument:
    """Új dokumentum a mappa-dátum felülírásával (`[Picasa]` `date=`).

    A kiírt alak **OLE Variant** (ld. `variant_ertek`), nem ISO — a
    bemenet viszont továbbra is ISO, mert a hívók (controller-slot,
    QML-dialógus) azzal dolgoznak.

    Üres vagy érvénytelen bemenetnél a kulcs **kimarad**: az eredeti író
    is kihagyja a sort, ha az érték `0.0` (`0x0071031e`–`0x0071032a`).
    """
    tisztitott = date_iso.strip()
    if not _ervenyes_iso(tisztitott):
        return document.with_removed(_FOLDER_SECTION, _FOLDER_DATE_KEY)
    return document.with_value(
        _FOLDER_SECTION, _FOLDER_DATE_KEY, variant_ertek(tisztitott)
    )


def without_folder_date_override(document: IniDocument) -> IniDocument:
    """Új dokumentum a kézi felülírás nélkül — a mappa a legrégebbi kép
    dátumára áll vissza a következő szinkronnál."""
    return document.with_removed(_FOLDER_SECTION, _FOLDER_DATE_KEY)
