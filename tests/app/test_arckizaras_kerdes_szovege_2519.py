"""A kizárás megerősítő kérdése az EREDETI magyar szövegét kapja (#2519).

A Picasa saját honosításából (`stringres`, `CFolderMgrDialog::confirmfrexclude`)
mérve:

| | szöveg |
|---|---|
| angol | „Are you sure you want to remove all faces and name tags from excluded folders?" |
| magyar | **„Biztosan eltávolítja az összes arcot és névcímkét a kihagyott mappákból?"** |

Nálunk korábban a saját fordításunk állt („eltávolítod… a kizárt mappákból"),
ami két ponton tért el: tegezés magázás helyett, és „kizárt" a „kihagyott"
helyett. Az eredeti Picasa-szövegeknél az eredeti honosítás a mérce — az
újonnan írt, saját szövegeinknél marad a projekt tegező hangja.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_I18N_DIR = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"

#: A QML `qsTranslate` első argumentuma a `FolderManagerDialog.qml`-ben.
KONTEXTUS = "FolderStatePanel"

FORRAS = (
    "Are you sure you want to remove all faces "
    "and name tags from excluded folders?"
)

#: `referencia/stringres-en-hu.tsv:315` — a Picasa saját magyar szövege.
VART = "Biztosan eltávolítja az összes arcot és névcímkét a kihagyott mappákból?"


@pytest.fixture(scope="module")
def forditas():
    from PySide6.QtCore import QCoreApplication, QTranslator

    QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N_DIR)), (
        "a picasapy_hu.qm nem tölthető be — lefuttattad a pyside6-lrelease-t?"
    )
    return translator


def test_a_kerdes_az_eredeti_magyar_szoveget_kapja(forditas):
    kapott = forditas.translate(KONTEXTUS, FORRAS)
    assert kapott == VART, (
        f"a megerősítő kérdés magyar szövege nem az eredetié:\n"
        f"  kapott: {kapott!r}\n  várt:   {VART!r}"
    )


def test_a_qml_ugyanezt_a_forrasszoveget_kerdezi():
    """A honosítás csak akkor ér valamit, ha a QML PONTOSAN ezt a
    forrásszöveget adja a `qsTranslate`-nek (a #1138 mintája: a fordítás
    megléte önmagában nem bizonyíték)."""
    qml = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/FolderManagerDialog.qml"
    ).read_text(encoding="utf-8")
    assert f'"{KONTEXTUS}"' in qml
    # a QML-ben a szöveg két literálból van összefűzve — a szóközök miatt a
    # két darabot külön keressük
    assert "Are you sure you want to remove all faces" in qml
    assert "and name tags from excluded folders?" in qml
