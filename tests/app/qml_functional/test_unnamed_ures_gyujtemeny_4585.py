"""QML-funkcionális teszt: üres „Név nélküliek" gyűjtemény útmutatója — #4585.

Az eredeti Picasa üres Név nélküliek gyűjteményénél az Emberek-panel
útmutatója a `peoplepanel_text.tre` Text1/Text2 szövege (a `0x00431290`
döntése, spec `picasa-arcfelismeres.md` 9/b: „+2ae — a gyűjtemény listája
üres ⇒ üres fejléc és instructions 0/1”). Nálunk eddig ilyenkor a Text3
(„A program még nem talált személyeket…”) állt, pedig a Text3 csak akkor
jár, ha a gyűjtemény nem üres, és nincs kijelölt kép.

A teszt VALÓDI kattintással nyitja meg a Névtelenek albumot, és a panel
szövegét a látható `peoplePanelEmptyText`-ről olvassa le.

Megjegyzés: a „Névtelenek" sor nulla arcnál rejtve van (`FolderPane.qml`),
ezért a tesztben a beolvasás haladását jelző `faceScanPercent` tulajdonságot
állítjuk be, hogy a sor látszódjon — ugyanaz a mód, mint a #449 tesztjeiben.
"""

from __future__ import annotations

import pytest

from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from support.jpeg_factory import make_jpeg

_ANNA_ID = "1111111111111111"
# a.jpg: Anna · b.jpg, c.jpg, d.jpg: senki megnevezett
_INI = (
    "[Contacts2]\n"
    f"{_ANNA_ID}=Anna;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID};\n"
)

# Text1 és Text2 (`peoplepanel_text.tre`): az eredeti angol forrásszöveg
TEXT1_ELEJE = "As Picasa scans your photos, the faces it finds are automatically grouped"
# Text3: a nem üres gyűjteményben, kijelölés nélkül megmaradó szöveg
TEXT3 = "No people have been found yet"

_FACE_LANDMARKS = FaceLandmarks(
    right_eye=(40.0, 30.0), left_eye=(70.0, 30.0), nose=(55.0, 45.0),
    mouth_right=(45.0, 60.0), mouth_left=(65.0, 60.0),
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _settle(qt_app, rounds: int = 5):
    for _ in range(rounds):
        qt_app.processEvents()


def _library(window, controller, qt_app, tmp_path):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    lib = tmp_path / "kepek"
    make_jpeg(lib / "b.jpg", size=(120, 90))
    make_jpeg(lib / "c.jpg", size=(120, 90))
    make_jpeg(lib / "d.jpg", size=(120, 90))
    (lib / ".picasa.ini").write_text(_INI, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    _settle(qt_app)
    QMetaObject.invokeMethod(
        _child(window, "menuViewPeople"), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    _settle(qt_app)
    return lib


def _seed_unnamed_face(tmp_path, photo_name: str) -> None:
    """Egy VALÓDI, névtelen arc a gyűjteménybe — a szkennelés útján, detektor
    nélkül (`replace_faces`)."""
    face = FaceDetection(
        left=20.0, top=10.0, right=90.0, bottom=80.0, score=0.9,
        landmarks=_FACE_LANDMARKS,
    )
    with open_index(tmp_path / "index.db") as conn:
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = ?", (photo_name,)
        ).fetchone()["id"]
        replace_faces(conn, photo_id, [face])
        conn.commit()


def _open_unnamed_album_by_click(window, qt_app):
    """A „Névtelenek" sor VALÓDI kattintása a bal hasábon.

    Nulla arcnál a sor rejtett, ezért a beolvasás haladását jelző
    tulajdonságot állítjuk be, hogy a sor megjelenjen."""
    pane = _child(window, "folderPane")
    pane.setProperty("peopleCollapsed", False)
    pane.setProperty("faceScanPercent", 7)
    _settle(qt_app)
    row = _child(window, "unnamedFacesItem")
    assert row.property("visible") is True
    center = row.mapToScene(row.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    _settle(qt_app)


def _header(window) -> str | None:
    label = _child(window, "peoplePanelHeader")
    return label.property("text") if label.property("visible") else None


def _empty_text(window) -> str | None:
    empty = _child(window, "peoplePanelEmptyText")
    return empty.property("text") if empty.property("visible") else None


class TestEmptyUnnamedCollection:
    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_empty_collection_shows_text1_not_text3(
        self, qml_app, qt_app, tmp_path, height_delta
    ):
        """Üres gyűjtemény, nincs kijelölés: az eredeti Text1 áll, fejléc nélkül."""
        window, controller, _engine = qml_app
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        _library(window, controller, qt_app, tmp_path)

        _open_unnamed_album_by_click(window, qt_app)
        # a vizsgált állapot: NINCS kijelölés — a CI-n a betöltés egy kijelölést
        # hagyhat hátra, akkor a panel jogosan a Text5-öt mutatja
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        for _ in range(60):
            qt_app.processEvents()
            if (_empty_text(window) or "").startswith(TEXT1_ELEJE):
                break
            QTest.qWait(50)

        assert _header(window) is None
        text = _empty_text(window)
        assert text is not None, "az útmutató nem látszik"
        assert text.startswith(TEXT1_ELEJE)
        assert TEXT3 not in text
        # a renderelt ablak képe a futtatás tmp_path-jában marad meg —
        # ezt nézzük meg vizuálisan a Text1 elrendezéséhez
        QTest.qWait(600)  # a fiók nyitó animációja lefusson a képen
        assert window.grabWindow().save(str(tmp_path / "ures_gyujtemeny.png"))

    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_nonempty_collection_nothing_selected_keeps_text3(
        self, qml_app, qt_app, tmp_path, height_delta
    ):
        """Van névtelen arc, de nincs kijelölés: a Text3 marad (regressziógát)."""
        window, controller, _engine = qml_app
        window.setHeight(window.height() + height_delta)
        qt_app.processEvents()
        _library(window, controller, qt_app, tmp_path)
        _seed_unnamed_face(tmp_path, "c.jpg")

        _open_unnamed_album_by_click(window, qt_app)

        assert _header(window) is None
        assert TEXT3 in _empty_text(window)
