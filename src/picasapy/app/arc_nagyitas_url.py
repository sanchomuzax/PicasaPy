"""Az arc-nagyítás cimkéje a thumb-URL-ben (#2187, `face_zoom`).

Az eredeti személy-album fejlécén a `face_zoom` ↔ `picture_zoom` pár
(`faceheaderpanel/zoom_container`, 2 × 35 × 21) váltja a csempék tartalmát
a személy arcára közelített és a teljes kép között. Nálunk a váltás a
bélyegkép-URL `&fz=<bal>,<fent>,<jobb>,<lent>` cimkéje (relatív, [0..1]
keret), és a szolgáltató ezt a keretet vágja ki.

A kivágás ÉLES kell legyen: a négyzet oldala legalább a kért cella
(`&sz=`, cimke nélkül a felső szint). A cellához választott kész bélyegkép
ehhez kis arcnál kevés — egy 144-es kép 10 %-os arcából ~29 képpontos
négyzet lenne, ötszörösen felnagyítva. Ilyenkor a szolgáltató nagyobb
szintből, végső soron az eredeti fájlból vág (`szukseges_hosszabb_el`).

A keret ugyanazért az URL része, amiért a szint (`&sz=`) és a
megjelenítési mód (`&d=`): a Qt URL szerint gyorstárazza a kész képet,
tehát ha a vágás a szolgáltató állapotából jönne, a váltás után a régi
képpontok maradnának. A lemez-gyorstárat a vágás NEM érinti — a vágott
kép a teljesből készül, kérésenként.

A keret értelmezése a `FacesOverlay` szokása: a relatív koordináta a
MEGJELENÍTETT (forgatott) képre vonatkozik.
"""

from __future__ import annotations

import math

from PySide6.QtGui import QImage

#: A lekérdezés kulcsa a thumb-URL-ben.
ARC_KULCS = "fz"

#: A kivágott négyzet oldala az arc hosszabbik oldalának ennyiszerese — a
#: fej és egy kis környezet is beleférjen, ne csak az arcfelület.
KORNYEZET_SZORZO = 2.0


def arc_cimke(teglalap: tuple[float, float, float, float]) -> str:
    """A `&fz=` cimke egy relatív kerethez (négy tizedes elég: a
    legnagyobb bélyegképen is képpont alatti)."""
    return f"&{ARC_KULCS}=" + ",".join(f"{ertek:.4f}" for ertek in teglalap)


def arc_from_thumb_id(
    photo_id: str,
) -> tuple[float, float, float, float] | None:
    """A `?…&fz=` kiolvasása; cimke nélkül (a rendes eset) `None`.

    Hibás cimkét `None`-ként olvasunk: a teljes kép a helyes tartalék, így
    rossz cimkéből sosem lesz rossz vágás."""
    if not photo_id:
        return None
    _, _, query = str(photo_id).partition("?")
    if f"{ARC_KULCS}=" not in query:
        return None
    for parameter in query.split("&"):
        key, separator, value = parameter.partition("=")
        if not separator or key != ARC_KULCS:
            continue
        try:
            ertekek = tuple(float(resz) for resz in value.split(","))
        except ValueError:
            return None
        if len(ertekek) != 4 or not all(math.isfinite(e) for e in ertekek):
            return None
        bal, fent, jobb, lent = ertekek
        if jobb <= bal or lent <= fent:
            return None
        return ertekek
    return None


def _vagas_oldal(
    szel: int, mag: int, teglalap: tuple[float, float, float, float]
) -> float:
    """A kivágott négyzet oldala képpontban, kerekítés előtt: az arc
    hosszabbik oldalának `KORNYEZET_SZORZO`-szorosa, de legfeljebb a kép
    rövidebbik oldala. Mindkét tag a kép méretével arányos."""
    bal, fent, jobb, lent = teglalap
    arc_oldal = max((jobb - bal) * szel, (lent - fent) * mag)
    return min(max(arc_oldal * KORNYEZET_SZORZO, 1.0), szel, mag)


def arc_vagas_oldala(
    szel: int, mag: int, teglalap: tuple[float, float, float, float]
) -> int:
    """A `szel` × `mag` képből kivágott négyzet oldala (képpont)."""
    return int(round(_vagas_oldal(szel, mag, teglalap)))


def szukseges_hosszabb_el(
    szel: int,
    mag: int,
    teglalap: tuple[float, float, float, float],
    cella: int,
) -> int | None:
    """Mekkora (hosszabb élű) forráskép kell, hogy a kivágás oldala elérje
    a `cella`-t? `None`, ha a `szel` × `mag` kép már elég.

    A kivágás oldala a képmérettel arányos, tehát a szükséges méret egy
    arányosítás; a +1 a kerekítés ellen biztosít."""
    oldal = _vagas_oldal(szel, mag, teglalap)
    if szel <= 0 or mag <= 0 or round(oldal) >= cella:
        return None
    return math.ceil(max(szel, mag) * cella / oldal) + 1


def arcra_vag(
    kep: QImage, teglalap: tuple[float, float, float, float]
) -> QImage:
    """Négyzetes kivágás az arc középpontja körül.

    Az oldal az `arc_vagas_oldala`; a négyzetet a kép határain belülre
    toljuk (a kép szélén ülő arc sem kap üres sávot)."""
    if kep.isNull():
        return kep
    szel, mag = kep.width(), kep.height()
    bal, fent, jobb, lent = teglalap
    kozep_x = (bal + jobb) / 2 * szel
    kozep_y = (fent + lent) / 2 * mag
    oldal = arc_vagas_oldala(szel, mag, teglalap)
    x = int(round(min(max(kozep_x - oldal / 2, 0), szel - oldal)))
    y = int(round(min(max(kozep_y - oldal / 2, 0), mag - oldal)))
    return kep.copy(x, y, oldal, oldal)


__all__ = [
    "ARC_KULCS",
    "KORNYEZET_SZORZO",
    "arc_cimke",
    "arc_from_thumb_id",
    "arc_vagas_oldala",
    "arcra_vag",
    "szukseges_hosszabb_el",
]
