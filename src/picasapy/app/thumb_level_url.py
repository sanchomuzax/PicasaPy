"""A bélyegkép-SZINT cimkéje a thumb-URL-ben (#598).

A szint ugyanúgy az URL része, mint a megjelenítési mód (`&d=`): a Qt
URL szerint gyorstárazza a kész képet, tehát ha a szint a szolgáltató
állapotából jönne, egy szintváltás után a régi képpontok maradnának a
gyorstárban — más méretben.

A cimke **csak a nem-felső szinteken** kerül ki (`models._thumb_url`), így a
mai URL-ek bájtra változatlanok, és a meglévő lemez-gyorstár érvényes marad.
"""

from __future__ import annotations

#: A lekérdezés kulcsa a thumb-URL-ben.
SZINT_KULCS = "sz"


def szint_from_thumb_id(photo_id: str) -> int | None:
    """A `?…&sz=<px>` kiolvasása; cimke nélkül (a rendes eset) `None`.

    A gyors kizárás SZÁNDÉKOS: a rács minden bélyegképnél ide lép. Hibás
    számot `None`-ként olvasunk — a felső szint a helyes tartalék, mert az
    minden cellára elég (kicsinyítéssel), tehát rossz cimkéből sosem lesz
    homályos kép.
    """
    if not photo_id:
        return None
    _, _, query = str(photo_id).partition("?")
    marker = f"{SZINT_KULCS}="
    if marker not in query:
        return None
    for parameter in query.split("&"):
        key, separator, value = parameter.partition("=")
        if separator and key == SZINT_KULCS:
            try:
                px = int(value)
            except ValueError:
                return None
            return px if px > 0 else None
    return None


__all__ = ["SZINT_KULCS", "szint_from_thumb_id"]
