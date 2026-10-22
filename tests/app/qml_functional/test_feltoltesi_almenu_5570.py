"""#5570 — az Eszközök ▸ Feltöltés menü szürke tételei."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickWindow

from tests.app.qml_functional._fomenu_4420_akciok import _kattints
from tests.app.qml_functional._fomenu_4420_menu import (
    _almenu,
    _megnyit,
    _menupont,
    _varj,
)

_FELTOLTESI_TETELEK = (
    "Upload to Google &Photos",
    "Upload to a Collaborative Web Album",
    "Upload to &YouTube",
)


def _feltoltes_almenu(menu_bar, tools_menu):
    for index in range(int(tools_menu.property("count") or 0)):
        sor = _menupont(tools_menu, index)
        almenu = _almenu(menu_bar, tools_menu, sor)
        if almenu is not None and almenu.property("title") == "U&pload":
            return sor, almenu
    raise AssertionError("az Eszközök menüben nincs Feltöltés almenü")


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_a_feltoltes_almenu_valodi_kattintassal_nyilik(
    qml_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = qml_app
    celmagassag = window.height() + magassag_eltolas
    window.setHeight(celmagassag)
    assert _varj(qt_app, lambda: window.height() == celmagassag), (
        "a főablak magassága nem állt be a kért értékre"
    )

    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    tools_menu = _megnyit(menu_bar, qt_app, "Tools")
    feltoltes_sor, feltoltes_menu = _feltoltes_almenu(menu_bar, tools_menu)

    _kattints(qt_app, feltoltes_sor)
    assert _varj(qt_app, lambda: feltoltes_menu.property("opened") is True), (
        "a Feltöltés almenü nem nyílt meg kattintásra"
    )


def test_a_feltoltesi_tetelek_szovege_sorrendje_es_letiltasa(qml_app, qt_app):
    window, _controller, _engine = qml_app
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    tools_menu = _megnyit(menu_bar, qt_app, "Tools")
    feltoltes_sor, feltoltes_menu = _feltoltes_almenu(menu_bar, tools_menu)
    _kattints(qt_app, feltoltes_sor)
    assert _varj(qt_app, lambda: feltoltes_menu.property("opened") is True), (
        "a Feltöltés almenü nem nyílt meg kattintásra"
    )

    darab = int(feltoltes_menu.property("count") or 0)
    assert darab == len(_FELTOLTESI_TETELEK), (
        f"a Feltöltés almenüben {darab} tétel van a várt három helyett"
    )
    tetelek = [_menupont(feltoltes_menu, index) for index in range(darab)]
    assert [tetel.property("text") for tetel in tetelek] == list(
        _FELTOLTESI_TETELEK
    )

    retired_szinu = next(
        (
            obj.property("contentItem").property("color")
            for obj in window.findChildren(QObject)
            if obj.property("retired") is True
            and obj.property("contentItem") is not None
            and obj.property("text") != _FELTOLTESI_TETELEK[0]
        ),
        None,
    )
    assert retired_szinu is not None, "nincs meglévő szürke nyugdíjazott minta"
    for tetel in tetelek:
        assert tetel.property("retired") is True, (
            f"{tetel.property('text')!r} nincs nyugdíjazottként jelölve"
        )
        assert tetel.property("enabled") is False, (
            f"{tetel.property('text')!r} kattintható maradt"
        )
        assert tetel.property("visible") is True, (
            f"{tetel.property('text')!r} nem látszik a megnyitott almenüben"
        )
        assert tetel.property("contentItem").property("color") == retired_szinu, (
            f"{tetel.property('text')!r} nem a szürke nyugdíjazott stílust kapta"
        )

    assert tetelek[0].window() is not None
    assert isinstance(tetelek[0].window(), QQuickWindow)
    ablak = tetelek[0].window()
    kep = ablak.grabWindow()
    assert not kep.isNull(), "a megnyitott Feltöltés menü üres képet adott"
    kepfajl = Path(__file__).resolve().parents[3] / ".bt" / "kep5570_feltoltes.png"
    kepfajl.parent.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(kepfajl), "PNG"), (
        "a megnyitott Feltöltés menüképe nem menthető"
    )

    import_google_photos = window.findChild(
        QObject, "menuFileImportFromGooglePhotos"
    )
    assert import_google_photos is not None
    assert import_google_photos.property("text") == "Import from Google Photos..."
    assert import_google_photos.property("retired") is True
    assert import_google_photos.property("enabled") is False
