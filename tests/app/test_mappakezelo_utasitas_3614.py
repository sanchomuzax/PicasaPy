"""A Mappakezelő jobb oldalán az EREDETI Picasa-utasítás áll (#3614).

Az eredetiben a „For the current folder:” csoport fölött, a `right_side`
bal felső sarkához igazítva egy rövid utasítás áll
(`foldermgr/instructions_text`, `docs/specs/picasa-mappakezelo.md` 1.3):

| | szöveg |
|---|---|
| angol | „For each folder, you can choose whether or not to have Picasa find pictures inside it.  You can also pick folders to watch for new pictures.” |
| magyar | „Minden mappa esetében megadhatja, hogy a Picasa keressen-e bennük képeket. Kijelölhet egyes mappákat is, és beállíthatja, hogy a program figyelje bennük az új képek megjelenését.” |

Nálunk a helyén saját, más tartalmú mondat állt („Válassza ki, mely mappákat
figyelje a PicasaPy…”). Eredeti Picasa-szövegnél az eredeti honosítás a
mérce (#2519 mintája).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_GYOKER = Path(__file__).resolve().parents[2]
_I18N_DIR = _GYOKER / "src" / "picasapy" / "app" / "i18n"
_QML = _GYOKER / "src/picasapy/app/qml/PicasaPy/FolderManagerDialog.qml"

KONTEXTUS = "FolderManagerDialog"

#: `foldermgr_text.tre` szó szerint — az „inside it.” után KÉT szóköz.
FORRAS = (
    "For each folder, you can choose whether or not to have Picasa find "
    "pictures inside it.  You can also pick folders to watch for new pictures."
)

#: `referencia/stringres-en-hu.tsv` — a Picasa saját magyar szövege.
VART = (
    "Minden mappa esetében megadhatja, hogy a Picasa keressen-e bennük "
    "képeket. Kijelölhet egyes mappákat is, és beállíthatja, hogy a program "
    "figyelje bennük az új képek megjelenését."
)


@pytest.fixture
def forditas(qt_app):
    # a `qt_app` (QGuiApplication) kell: egy saját QCoreApplication a
    # modul QML-tesztjét (`qml_app`) abortra vinné
    from PySide6.QtCore import QTranslator

    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N_DIR)), (
        "a picasapy_hu.qm nem tölthető be — lefuttattad a pyside6-lrelease-t?"
    )
    return translator


def _utasitas_blokk() -> str:
    qml = _QML.read_text(encoding="utf-8")
    m = re.search(
        r'objectName: "folderManagerInstructions"(.*?)\n\s*\}', qml, re.S
    )
    assert m, "nincs `folderManagerInstructions` elem a Mappakezelőben"
    return m.group(1)


def _qstr_osszefuzve(blokk: str) -> str:
    m = re.search(r"qsTr\((.*?)\)\s*\n", blokk, re.S)
    assert m, "az utasítás szövege nem qsTr()-ből jön"
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1)))


def test_a_qml_az_eredeti_angol_utasitast_forditja():
    assert _qstr_osszefuzve(_utasitas_blokk()) == FORRAS


def test_a_magyar_forditas_az_eredeti_honositase(forditas):
    kapott = forditas.translate(KONTEXTUS, FORRAS)
    assert kapott == VART, f"kapott: {kapott!r}\nvárt:   {VART!r}"


def _elem(window, nev):
    from PySide6.QtCore import QObject
    from support.halasztott_parbeszed import nyisd_meg

    nyisd_meg(window, "folderManagerDialog")
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


@pytest.mark.parametrize("szoveg", [FORRAS, VART], ids=["angol", "magyar"])
def test_a_helye_es_merete_az_eredetie(qml_app, qt_app, szoveg):
    """232 széles, legalább 73 magas, tördelt szövegdoboz a jobb oszlop
    tetején, az állapot-csoport („For the current folder:”) FÖLÖTT — és a
    hosszabb magyar szöveg sem lóg rá a csoportra."""
    window, _controller, _lib, _engine = qml_app
    utasitas = _elem(window, "folderManagerInstructions")
    panel = _elem(window, "folderManagerStatePanel")
    dialog = _elem(window, "folderManagerDialog")
    dialog.setProperty("visible", True)
    utasitas.setProperty("text", szoveg)
    qt_app.processEvents()

    assert utasitas.property("width") == 232
    assert utasitas.property("height") >= 73
    assert utasitas.property("lineCount") > 1, "a szöveg nincs tördelve"
    assert utasitas.property("height") >= utasitas.property("contentHeight"), (
        "a szöveg kifut a dobozából"
    )
    assert utasitas.property("y") == 0, "nem a jobb oszlop tetején áll"
    assert panel.property("y") >= utasitas.property("y") + utasitas.property("height"), (
        "az utasítás rálóg a „For the current folder:” csoportra"
    )
    dialog.setProperty("visible", False)


def test_a_sugo_ablak_tartalma_valtozatlan():
    qml = _QML.read_text(encoding="utf-8")
    assert "Scan Always keeps watching the folder: pictures you add" in qml
    assert "Face detection is separate: you can watch a folder and" in qml


def _folder_list_felirat_blokk() -> str:
    qml = _QML.read_text(encoding="utf-8")
    m = re.search(r'text: qsTr\("Folder List"\)(.*?)\n\s*\}', qml, re.S)
    assert m, "nincs „Folder List” felirat a Mappakezelőben"
    return m.group(1)


def _color(blokk: str) -> str:
    m = re.search(r"color:\s*(\S+)", blokk)
    assert m, "a blokknak nincs `color` tulajdonsága"
    return m.group(1)


def test_az_utasitas_szine_egyezik_a_folder_list_feliratteval():
    """A referencia-képen (Colab EN 10 - Folder Manager.png) az utasítás
    szövege ugyanolyan sötét, mint a „Folder List” felirat — nem
    Theme.textGray, hanem Theme.ink."""
    assert _color(_utasitas_blokk()) == _color(_folder_list_felirat_blokk()) == "Theme.ink"
