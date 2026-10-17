"""#5195: a fotó helyi menüjének feliratai és a „Társítás ▸" almenü VALÓDI kattintással.

Lefedve:
- `contextMenuUndoAllEdits`: „Undo all Edits" (kis `a`, az eredeti
  `AlbumPhoto::ID_PICTURE_REVERT` szerint);
- `contextMenuBlockUpload`: „Block from Uploading" (`AlbumPhoto::ID_SUPPRESS`);
- `contextMenuOpenWith`: az almenü a társított alkalmazásokkal, a választó az
  utolsó tétel, és az alkalmazás-tételre kattintva a kép megnyílik.

A fotó menüjét valódi jobbkattintás nyitja a bélyegképen. A társított
alkalmazások listáját és az indítást helyettesítjük; ezt a teszt kimondja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF

import picasapy.fileops.open_with as open_with_module
from picasapy.fileops.open_with import OpenWithApp
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    egyezik,
    elokeszit_str,
    foto_utja,
    gyerek,
    jobbklikk_fotón,
    keres_vizualis_mindenablakban,
    kattints,
    varj,
)

_ALKALMAZASOK = [
    OpenWithApp("gimp.desktop", "GNU Image Manipulation Program", "gimp %U"),
    OpenWithApp("eog.desktop", "Image Viewer", "eog --new-instance %F"),
]


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.fixture
def tarsitott_alkalmazasok(monkeypatch):
    """A lista és az indítás helyettesítése; a hívásokat rögzíti.

    A `_platform` Linuxra van kényszerítve: Windowson a tétel a héj
    párbeszédét hívja, almenü nélkül (ezt a régi Open With-teszt fedi)."""
    inditasok = []
    monkeypatch.setattr(open_with_module, "_platform", lambda: "linux")
    monkeypatch.setattr(
        open_with_module, "apps_for_file", lambda path: list(_ALKALMAZASOK)
    )
    monkeypatch.setattr(
        open_with_module,
        "launch_app",
        lambda app, path: inditasok.append((app.app_id, Path(path))),
    )
    return inditasok


def _latszo_tetel(window, nev: str):
    tetel = keres_vizualis_mindenablakban(window, nev)
    assert tetel is not None, f"{nev} nem látszik a fotó helyi menüjében"
    return tetel


class TestFeliratok:
    def test_a_visszavonas_es_a_feltoltes_tiltasa_az_eredeti_feliratot_mutatja(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)

        jobbklikk_fotón(window, qt_app, 0)

        assert _latszo_tetel(window, "contextMenuUndoAllEdits") is not None
        assert gyerek(window, "contextMenuUndoAllEdits").property("text") == (
            "Undo all Edits"
        ), "a visszavonás tétel felirata nem az eredeti"
        assert _latszo_tetel(window, "contextMenuBlockUpload") is not None
        assert gyerek(window, "contextMenuBlockUpload").property("text") == (
            "Block from Uploading"
        ), "a feltöltés-tiltás tétel felirata nem az eredeti"


class TestTarsitasAlmenu:
    def test_az_almenu_valodi_kattintassal_listazza_az_alkalmazasokat_es_a_valasztot_utolsonak(
        self, mappa_app, qt_app, tarsitott_alkalmazasok
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        jobbklikk_fotón(window, qt_app, 0)

        kattints(window, qt_app, _latszo_tetel(window, "contextMenuOpenWith"))
        almenu = gyerek(window, "contextMenuOpenWithMenu")
        assert varj(qt_app, lambda: almenu.property("visible") is True), (
            "a Társítás almenü nem nyílt meg a valódi kattintásra"
        )

        tetelek = [
            _latszo_tetel(window, nev)
            for nev in (
                "contextMenuOpenWithApp_gimp.desktop",
                "contextMenuOpenWithApp_eog.desktop",
                "contextMenuOpenWithChoose",
            )
        ]
        magassagok = [tetel.mapToScene(QPointF(0, 0)).y() for tetel in tetelek]
        assert magassagok == sorted(magassagok), (
            "a választó nem az alkalmazások után áll"
        )
        assert keres_vizualis_mindenablakban(window, "contextMenuOpenWithNative") is None, (
            "Linuxon a héj-tétel nem lehet látható"
        )

        kattints(window, qt_app, tetelek[1])

        assert varj(qt_app, lambda: len(tarsitott_alkalmazasok) == 1), (
            "az alkalmazás-tétel nem indította el a programot"
        )
        app_id, megnyitott = tarsitott_alkalmazasok[0]
        assert app_id == "eog.desktop"
        assert egyezik(megnyitott, foto_utja(controller, 0))
