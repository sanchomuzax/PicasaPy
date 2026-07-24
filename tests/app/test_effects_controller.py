"""`_write_session` (effects_controller) — a Paste All Effects (#152) ini-
beírásának hibatűrése (#301).

A `pasteEffects` egy MÁSOLT, idegen effektláncon hívja a `session.crop()`-ot
(nem a hívó saját, ellenőrzött láncán) — hibás rect64-nél a kivétel korábban
a QML-slotból szökött volna ki. A modul-szintű `_write_session` tiszta
függvény, nem igényel Qt-alkalmazást, ezért `qt_app` fixture nélkül tesztelhető.
"""

from __future__ import annotations

from picasapy.app.effects_controller import _write_session
from picasapy.edit.session import EditSession
from picasapy.ini.document import parse_document
from picasapy.ini.filters import FilterOp


def test_write_session_hibas_crop64_nem_dob():
    """Hibás rect64-es crop64-et tartalmazó (pl. beillesztett, idegen) lánc
    ne dobjon — a filters= beíródik, a crop= tükör-kulcs elmarad."""
    document = parse_document("[IMG_0001.jpg]\n")
    pasted = EditSession(ops=(FilterOp("crop64", ("1", "zzz")),))

    result = _write_session(document, "IMG_0001.jpg", pasted)

    section = result.section("IMG_0001.jpg")
    assert section is not None
    assert section.get("filters") == "crop64=1,zzz;"
    assert section.get("crop") is None


def test_write_session_ervenyes_crop64_beirja_a_crop_kulcsot():
    """Ellenpélda: érvényes crop64-nél a `crop=` tükör-kulcs is bekerül."""
    document = parse_document("[IMG_0001.jpg]\n")
    pasted = EditSession(ops=(FilterOp("crop64", ("1", "10001000e000e000")),))

    result = _write_session(document, "IMG_0001.jpg", pasted)

    section = result.section("IMG_0001.jpg")
    assert section is not None
    assert section.get("crop") == "rect64(10001000e000e000)"


def test_write_session_ures_session_eltavolitja_a_kulcsokat():
    """Üres (beillesztett) lánc a meglévő filters=/crop= kulcsokat törli."""
    document = parse_document(
        "[IMG_0001.jpg]\nfilters=enhance=1;\ncrop=rect64(10001000e000e000)\n"
    )
    result = _write_session(document, "IMG_0001.jpg", EditSession())

    # mindkét kulcs törlésével a szekció is elfogy (nincs megőrzendő sor)
    section = result.section("IMG_0001.jpg")
    assert section is None or (
        section.get("filters") is None and section.get("crop") is None
    )
