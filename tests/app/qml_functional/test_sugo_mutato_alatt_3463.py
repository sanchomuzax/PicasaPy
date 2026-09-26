"""#3463: a Shift+F1 a mutató alatti panel súgófejezetét nyitja.

A #2054 gépezete kész volt (`Main.qml`: `helpTopicUnderCursor()`), de két
ok miatt MINDIG a főoldalra esett:

1. egyetlen QML-elem sem deklarált `helpTopic`-ot;
2. a keresés a `contentItem.childAt()`-tel CSAK a közvetlen gyermeket kapta
   meg — a panelek mélyén álló elemtől a szülőláncon felfelé sétálás így el
   sem indulhatott — ráadásul a legfelső gyermek gyakran egy üres,
   ablaknyi betöltő volt. A javított keresés mélységi: felülről lefelé
   próbálja a pontot tartalmazó elemeket, és a legmélyebb témát adja.

A főablak rétegében nyitott MODÁLIS párbeszéd alatt a Qt a főablak
Shift+F1-ét letiltja: ezért a témát deklaráló réteg-párbeszédek saját,
csak nyitott állapotban élő Shift+F1-et kapnak, a saját fejezetükkel.

A külön ablakos, alkalmazás-modális párbeszédek (Nyomtatás, Mappakezelő,
Beállítások, Importálás forrásból, Exportálás weboldalként) súgóját a #3544
kötötte be, saját súgóablakkal: `test_sugo_kulon_ablakbol_3544.py`.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.help_content import fejezetek

_QML = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _deklaralt_temak() -> dict[str, str]:
    temak = {}
    for fajl in _QML.rglob("*.qml"):
        for talalat in re.finditer(r'helpTopic:\s*"([^"]+)"', fajl.read_text(encoding="utf-8")):
            temak[f"{fajl.name}:{talalat.group(1)}"] = talalat.group(1)
    return temak


def test_minden_deklaralt_tema_letezo_fejezet():
    temak = _deklaralt_temak()
    assert temak, "egyetlen elem sem deklarál helpTopic-ot"
    letezok = set(fejezetek())
    rosszak = {hely: tema for hely, tema in temak.items() if tema not in letezok}
    assert not rosszak, f"nem létező fejezetre mutat: {rosszak}"


@pytest.mark.parametrize(
    "fajl,tema",
    [
        ("PicasaPy/FolderPane.qml", "features/konyvtar.md"),
        ("PicasaPy/LightboxFeed.qml", "features/konyvtar.md"),
        ("PicasaPy/PhotoViewer.qml", "features/nezegetes.md"),
        ("PicasaPy/EditorPanel.qml", "features/szerkeszto.md"),
        ("PicasaPy/CollagePanel.qml", "features/kollazs.md"),
        ("PicasaPy/ExportDialogs.qml", "features/exportalas.md"),
        ("PicasaPy/PicasaImportDialog.qml", "features/importalas.md"),
    ],
)
def test_a_panel_a_sajat_fejezetet_deklaralja(fajl, tema):
    assert f'helpTopic: "{tema}"' in (_QML / fajl).read_text(encoding="utf-8")


def _shift_f1_a_mutato_alatt(qml_app, qt_app, elem) -> str:
    window, _controller, _engine = qml_app
    # a gyorsbillentyű csak AKTÍV főablakban nyit súgót (külön ablakos
    # párbeszédből nem) — a felhasználó gépelő ablaka mindig aktív
    window.requestActivate()
    assert QTest.qWaitForWindowActive(window, 3000), "a főablak nem lett aktív"
    _var(qt_app, lambda: elem.width() > 0 and elem.height() > 0)
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(window, pont)
    qt_app.processEvents()
    QTest.keyClick(window, Qt.Key.Key_F1, Qt.KeyboardModifier.ShiftModifier)

    def _nyitott():
        p = window.findChild(QObject, "helpDialog")
        return p if p is not None and p.property("visible") else None

    assert _var(qt_app, lambda: _nyitott() is not None), "a súgó nem nyílt meg"
    return _nyitott().property("topic")


def test_a_mappalista_folott_a_konyvtar_fejezete_nyilik(qml_app, qt_app):
    window, _c, _e = qml_app
    pane = window.findChild(QObject, "folderPane")
    assert _shift_f1_a_mutato_alatt(qml_app, qt_app, pane) == "features/konyvtar.md"


def test_a_racs_folott_a_konyvtar_fejezete_nyilik(qml_app, qt_app):
    window, _c, _e = qml_app
    racs = window.findChild(QObject, "photoGrid")
    assert _shift_f1_a_mutato_alatt(qml_app, qt_app, racs) == "features/konyvtar.md"


def test_nyitott_retegbeli_parbeszed_folott_a_sajat_fejezete_nyilik(qml_app, qt_app):
    """A főablak rétegében (`overlay`) nyitott párbeszéd a `contentItem`
    fölött ül — a keresésnek előbb azt kell néznie."""
    window, _c, _e = qml_app
    parbeszed = window.findChild(QObject, "picasaImportDialog")
    parbeszed.metaObject().invokeMethod(parbeszed, "open")
    doboz = parbeszed.property("contentItem")
    assert _var(qt_app, lambda: parbeszed.property("opened") is True and doboz.width() > 0)
    assert _shift_f1_a_mutato_alatt(qml_app, qt_app, doboz) == "features/importalas.md"
