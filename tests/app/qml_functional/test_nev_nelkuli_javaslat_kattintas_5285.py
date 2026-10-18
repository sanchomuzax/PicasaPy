"""A Név nélküliek ajánlólistájának tétele: kattintás = névadás (#5285).

Az eredeti Picasa súgója szerint a névmezőbe gépelt részlet után a lista
„press Enter or click on an autocompleted name”. A teszt a TELJES
programablakban fut, ugyanúgy, mint a #5183 tesztjei: a Név nélküliek nézet
a bal oldali sávról nyílik, az üdvözlő párbeszédet bezárjuk, a csempe
névmezőjébe gépelve megjelenik a javaslat-lista, és a tételre VALÓDI
egérkattintással ugyanaz történik, mint Enterre: a mező kiürül, a lista
záródik, az Emberek-kezelő pedig a KATTINTOTT személy nevével nyílik meg.
A névadás a „Choose” gombbal történik: az arc a kattintott személyhez kerül.

Rontás-kontroll: a tétel MouseArea-ja nélkül a kattintás nem nevez el, és a
teszt piros.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import all_photos, open_index
from picasapy.ini import contacts_of, load_document, parse_faces
from tests.app.qml_functional._utolso_maradek_5150_helpers import gepel
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (
    _click,
    _find_item,
    _find_object,
    _save_window,
    _seed_six_faces,
)
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (  # noqa: F401
    qml_app_5183,
)
from tests.support.varakozas import var_feltetelre

_CEL_ARC = 5
_ELSO_SZEMELY = "Anna Kovács"
_MASODIK_SZEMELY = "Annabella Nagy"
_SZEMELYEK = (_ELSO_SZEMELY, _MASODIK_SZEMELY)
#: a gépelt részlet mindkét személyre illik; a kattintott a MÁSODIK, hogy a
#: teszt megkülönböztesse a kattintott nevet a gépelt részlettől
_GEPELT = "Ann"
#: a négy névtelen arc közül az 5-ös kikerül (a kattintott személyhez kerül),
#: a többi három névtelen marad
_NEVTELEN_UTANA = {3, 4, 6}
_GEOMETRIA_FAJL = "geometria_5285.json"


def _ter_lathato(elem) -> bool:
    """A felmenőkön át is látszik-e: a zárt Popup gyermekei a saját
    `visible` jelzőjüket tartják, a felmenőjük viszont már rejtett."""
    while elem is not None:
        if not elem.isVisible():
            return False
        elem = elem.parentItem()
    return True


def _javaslat_tetele(window, arc: int, nev: str):
    """A javaslat-lista azon tétele, amelynek személye `nev`; ha nincs, None."""
    for index in range(len(_SZEMELYEK)):
        tetel = _find_item(window, f"unnamedFaceSuggestion_{arc}_{index}")
        if tetel is not None and tetel.property("personName") == nev:
            return tetel
    return None


def _nevtelen_arcok(face_scan) -> set[int]:
    return {
        arc["faceId"]
        for csoport in face_scan.unnamedGroups(True, False)
        for arc in csoport["faces"]
    }


def _arcok_szama_nevhez(db_path: Path, nev: str) -> int:
    """Hány arc van `nev` személyhez rendelve a `.picasa.ini`-kben (ahogy a
    #5192 teszt méri)."""
    with open_index(db_path) as conn:
        photos = all_photos(conn)
    dokumentumok = [
        load_document(path)
        for path in {Path(photo.folder_path) / ".picasa.ini" for photo in photos}
    ]
    azonosito = next(
        (
            kontakt.person_id
            for dokumentum in dokumentumok
            for kontakt in contacts_of(dokumentum)
            if kontakt.name == nev
        ),
        None,
    )
    assert azonosito is not None, f"nincs ilyen névjegy: {nev}"
    return sum(
        arc.contact_id == azonosito
        for dokumentum in dokumentumok
        for szakasz in dokumentum.sections
        for arc in parse_faces(szakasz.get("faces") or "")
    )


def test_a_javaslat_tetelere_valodi_kattintas_ugyanazt_nevezi_meg_mint_az_enter(
    qml_app_5183, qt_app  # noqa: F811
):
    window, controller, engine = qml_app_5183
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    db_path = Path(controller._db_path)
    _seed_six_faces(db_path)
    # két ismert személy: a gépelt „Ann” mindkettőre illik
    assert face_scan.assignNameToFaces([1], _ELSO_SZEMELY)
    assert face_scan.assignNameToFaces([2], _MASODIK_SZEMELY)
    controller.refreshCollections()
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 4)
    arcok_elotte = _arcok_szama_nevhez(db_path, _MASODIK_SZEMELY)

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _find_item(window, "unnamedFacesItem")
    assert var_feltetelre(
        qt_app, lambda: unnamed_row is not None and unnamed_row.width() > 0
    )
    _click(qt_app, unnamed_row)
    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app, lambda: view is not None and view.property("visible") is True
    )
    welcome = _find_object(window, "unnamedWelcomeDialog")
    assert var_feltetelre(
        qt_app,
        lambda: welcome is not None and welcome.property("visible") is True,
    )
    _click(qt_app, _find_item(window, "unnamedWelcomeCloseButton"))
    assert var_feltetelre(qt_app, lambda: welcome.property("visible") is False)

    nev_mezo = _find_item(window, f"unnamedFaceNameField_{_CEL_ARC}")
    assert var_feltetelre(
        qt_app, lambda: nev_mezo is not None and nev_mezo.width() > 0
    )
    _click(qt_app, nev_mezo)
    gepel(window, qt_app, _GEPELT)
    assert nev_mezo.property("text") == _GEPELT

    assert var_feltetelre(
        qt_app,
        lambda: _javaslat_tetele(window, _CEL_ARC, _MASODIK_SZEMELY) is not None,
    ), "a javaslat-lista nem jelent meg a gépelés után"
    lista = _find_item(window, f"unnamedNameSuggestions_{_CEL_ARC}")
    assert lista is not None and lista.property("visible") is True
    assert _javaslat_tetele(window, _CEL_ARC, _ELSO_SZEMELY) is not None
    tetel = _javaslat_tetele(window, _CEL_ARC, _MASODIK_SZEMELY)
    assert tetel is not None and _ter_lathato(tetel)

    # a kattintás előtti ellenőrzés: a pont az ablakon belül legyen, és a
    # tétel a névmező alatt
    pont = tetel.mapToScene(QPointF(tetel.width() / 2, tetel.height() / 2))
    tetel_teteje = tetel.mapToScene(QPointF(0, 0)).y()
    mezo_also = nev_mezo.mapToScene(QPointF(0, nev_mezo.height())).y()
    assert tetel.width() > 0 and tetel.height() > 0
    assert 0 <= pont.x() < window.width(), (pont.x(), window.width())
    assert 0 <= pont.y() < window.height(), (pont.y(), window.height())
    assert tetel_teteje >= mezo_also, (tetel_teteje, mezo_also)

    kep = _save_window(window, "kep_5285.png")
    geometria = {
        "window": {"width": window.width(), "height": window.height()},
        "click": {"x": round(pont.x()), "y": round(pont.y())},
        "suggestion": {
            "y": tetel_teteje,
            "width": tetel.width(),
            "height": tetel.height(),
        },
        "field_bottom_y": mezo_also,
    }
    kep.with_name(_GEOMETRIA_FAJL).write_text(
        json.dumps(geometria, indent=2), encoding="utf-8"
    )

    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()

    assert var_feltetelre(
        qt_app, lambda: nev_mezo.property("text") == ""
    ), f"a névmező nem ürült: {nev_mezo.property('text')!r}"
    assert var_feltetelre(qt_app, lambda: not _ter_lathato(lista)), (
        "a javaslat-lista a kattintás után is nyitva maradt"
    )

    # az Enter útja: az Emberek-kezelő a KATTINTOTT névvel nyílik meg, nem a
    # gépelt részlettel, és a névadás a „Choose” gombbal történik
    kezelo = _find_object(window, "peopleManagerDialog")
    assert var_feltetelre(
        qt_app,
        lambda: kezelo is not None and kezelo.property("visible") is True,
    ), "a kattintás nem nyitotta meg az Emberek-kezelőt"
    kereso = _find_item(window, "peopleManagerSearchField")
    assert kereso is not None
    assert kereso.property("text") == _MASODIK_SZEMELY, kereso.property("text")
    kivalasztott = _find_item(window, f"peopleManagerContact_{_MASODIK_SZEMELY}")
    assert kivalasztott is not None and kivalasztott.property("highlighted") is True
    valaszt = _find_item(window, "peopleManagerOkButton")
    assert valaszt is not None and valaszt.property("text") == "Choose"
    _click(qt_app, valaszt)

    assert var_feltetelre(
        qt_app,
        lambda: kezelo.property("visible") is False
        and _nevtelen_arcok(face_scan) == _NEVTELEN_UTANA,
    ), f"a Choose után a névtelen arcok: {_nevtelen_arcok(face_scan)}"
    assert _arcok_szama_nevhez(db_path, _MASODIK_SZEMELY) == arcok_elotte + 1
