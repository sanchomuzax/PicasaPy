"""A Crop Apply lánckezelése: a lánc végi `crop64` helyben frissül (#7367).

Az eredeti Picasa (`0x006b4300`) a lista utolsó elemének nevét a `crop64`
literálhoz hasonlítja. Egyezéskor a meglévő rekord koordinátáit írja át (a
lánc nem nő, a Visszavonás-lépések száma sem), más végrekordnál új `crop64`
elemet fűz a végére. Az `EditSession.append_crop` feltétlen hozzáfűzés
marad: a #1553 őrei és a több-vágásos láncok olvasása rá épülnek.
"""

from __future__ import annotations

from picasapy.ini.rect64 import Rect64, encode_rect64

from .session import EditSession
from .session_core import _new_op

_CROP_NEV = "crop64"


def vegi_crop_frissitheto(session: EditSession) -> bool:
    """Igaz, ha a lánc UTOLSÓ eleme `crop64`: az újravágás azt írja át."""
    return session.last_is(_CROP_NEV)


def recrop(session: EditSession, rect: Rect64 | None) -> EditSession:
    """A Crop Apply hatása a láncra; `rect=None` az üres téglalap.

    - `crop64` végű lánc: az utolsó rekord koordinátái cserélődnek, az üres
      téglalap viszont törli az utolsó rekordot.
    - Üres lánc vagy más végrekord: érvényes téglalapnál új `crop64` kerül a
      végére, üres téglalapnál a lánc nem változik.

    A korábbi és közbeeső elemek mindig érintetlenek maradnak.
    """
    if not vegi_crop_frissitheto(session):
        return session if rect is None else session.append_crop(rect)
    if rect is None:
        return EditSession(ops=session.ops[:-1])
    uj_elem = _new_op(_CROP_NEV, ("1", encode_rect64(rect)))
    return EditSession(ops=session.ops[:-1] + (uj_elem,))
