"""#3352 — az ékezetes, szóközös (OneDrive-os) mappaút épen ér a borító-szolgáltatóhoz.

A windowsos napló `image://foldercover/…%5CK?pek%5Cteszt` sort mutatott, és
felmerült, hogy az „é" a program útján romlik el. Nem: a `?` a konzol
kódlapjáé, a QML az utat betű szerint adja át. Ez a próba VALÓDI QML
`Image`-en át kéri a borítót — nem közvetlen `requestImage`-hívással —,
tehát a Qt URL-kezelését is lefedi.

A figyelmeztetés tehát csak fotó nélküli mappánál jelenik meg, ahol a
null kép szándékos (#2215: a sor a mappaikonra esik vissza).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.folder_cover_provider import FolderCoverProvider, borito_fajljai
from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

_WINDOWS_UT = "C:\\Users\\X\\OneDrive - Cég Kft\\Képek\\teszt"
_READY = 1


def _statusz(qt_app, tmp_path: Path, lekerdezo, ut: str) -> int:
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine

    engine = QQmlApplicationEngine()
    engine.addImageProvider("foldercover", FolderCoverProvider(lekerdezo))
    engine.rootContext().setContextProperty("mappaUt", ut)
    qml = tmp_path / "borito.qml"
    qml.write_text(
        "import QtQuick\n"
        "Image { property int allapot: status; asynchronous: false;"
        ' source: "image://foldercover/" + mappaUt }\n',
        encoding="utf-8",
    )
    engine.load(QUrl.fromLocalFile(str(qml)))
    gyoker = engine.rootObjects()[0]
    statusz = gyoker.property("allapot")
    gyoker.deleteLater()
    return statusz


@pytest.fixture
def ekezetes_mappa(tmp_path: Path):
    mappa = tmp_path / "OneDrive - Cég Kft" / "Képek" / "teszt"
    mappa.mkdir(parents=True)
    make_jpeg(mappa / "a.jpg", size=(120, 90))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, tmp_path / "OneDrive - Cég Kft")
    return db, mappa


def test_az_ekezetes_indexelt_mappa_boritoja_BETOLTODIK(qt_app, tmp_path, ekezetes_mappa):
    db, mappa = ekezetes_mappa
    assert _statusz(qt_app, tmp_path, lambda m: borito_fajljai(db, m), str(mappa)) == _READY


def test_a_windowsos_ut_BETU_SZERINT_er_a_szolgaltatohoz(qt_app, tmp_path, ekezetes_mappa):
    _db, mappa = ekezetes_mappa
    kapott: list[str] = []

    def lekerdezo(m: str):
        kapott.append(m)
        return [mappa / "a.jpg"] if m == _WINDOWS_UT else []

    assert _statusz(qt_app, tmp_path, lekerdezo, _WINDOWS_UT) == _READY
    assert kapott == [_WINDOWS_UT]
