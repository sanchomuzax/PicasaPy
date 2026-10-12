"""#4598 — az albummenü törlési útja tényleges kattintással."""

from __future__ import annotations

import time

from PySide6.QtCore import QPoint, QPointF, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini.albums import parse_album_refs
from picasapy.ini.document import parse_document
from support.jpeg_factory import make_jpeg

_TOKEN = "4598" * 8
_OTHER = "d" * 32


def _child(root, name):
    child = root.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _visual_item(root, name):
    """A Repeater albumsorát a QQuickItem vizuális fájában keresi meg."""
    pending = [root.contentItem()]
    while pending:
        item = pending.pop()
        if item.objectName() == name:
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{name} nem található a vizuális fában")


def _varj(feltetel, qt_app, nev):
    hatarido = time.monotonic() + 3
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(f"határidőn belül nem teljesült: {nev}")


def _katt(window, elem, gomb=Qt.LeftButton):
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        gomb,
        Qt.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def _torles_megerositot_nyit(window, qt_app):
    sor = _visual_item(window, f"albumItem_{_TOKEN}")
    _katt(window, sor, Qt.RightButton)
    menu = _child(window, "albumContextMenu")
    _varj(lambda: menu.property("visible"), qt_app, "album helyi menü")

    tetel = _child(window, "albumMenuDelete")
    assert tetel.property("enabled") is True
    _katt(window, tetel)

    dialog = _child(window, "deleteAlbumDialog")
    _varj(lambda: dialog.property("visible"), qt_app, "album törlésének megerősítője")
    assert dialog.property("title") == "Delete Album"
    assert dialog.property("message") == (
        'Are you sure you want to delete the album "Nyaralás"?'
    )
    assert dialog.property("yesText") == "Delete Album"
    return dialog


def test_kattintas_utan_megerositve_torol_es_mas_adatot_meghagy(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    masodik = root / "masodik"
    idegen = root / "idegen"
    masodik.mkdir()
    idegen.mkdir()
    make_jpeg(masodik / "masodik.jpg")
    make_jpeg(idegen / "idegen.jpg")

    (root / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Nyaralás\n"
        f"[.album:{_OTHER}]\ntoken={_OTHER}\nname=Másik album\n"
        f"[a.jpg]\nalbums={_TOKEN},{_OTHER}\ncaption=maradjon\n"
        f"[b.jpg]\nalbums={_TOKEN}\nstar=yes\n",
        encoding="utf-8",
    )
    (masodik / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Nyaralás\n"
        f"[.album:{_OTHER}]\ntoken={_OTHER}\nname=Másik album\n"
        f"[masodik.jpg]\nalbums={_TOKEN},{_OTHER}\n",
        encoding="utf-8",
    )
    (idegen / ".picasa.ini").write_text(
        "[idegen.jpg]\ncaption=ehhez ne nyúljon\n", encoding="utf-8"
    )
    erintetlen_ini = (idegen / ".picasa.ini").read_bytes()
    fajlok = [root / "a.jpg", root / "b.jpg", masodik / "masodik.jpg"]
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    qt_app.processEvents()

    eredeti_inek = {
        path: path.read_bytes()
        for path in (root / ".picasa.ini", masodik / ".picasa.ini")
    }
    alapmagassag = int(window.height())
    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        assert int(window.height()) == alapmagassag + eltolás
        dialog = _torles_megerositot_nyit(window, qt_app)
        if eltolás < 5:
            _katt(window, _child(dialog, "deleteAlbumCancelButton"))
            _varj(
                lambda dialog=dialog: not dialog.property("visible"),
                qt_app,
                "megerősítő bezárása",
            )
            assert {path: path.read_bytes() for path in eredeti_inek} == eredeti_inek
        else:
            _katt(window, _child(dialog, "deleteAlbumYesButton"))

    _varj(
        lambda: all(album["token"] != _TOKEN for album in controller.albums),
        qt_app,
        "album eltűnése a modellből",
    )
    for ini_path in (root / ".picasa.ini", masodik / ".picasa.ini"):
        document = parse_document(ini_path.read_text(encoding="utf-8"))
        assert document.section(f".album:{_TOKEN}") is None
        assert document.section(f".album:{_OTHER}") is not None
        for section in document.file_sections():
            assert _TOKEN not in parse_album_refs(section.get("albums") or "")
    assert all(path.is_file() for path in fajlok)
    assert "caption=maradjon" in (root / ".picasa.ini").read_text(encoding="utf-8")
    assert "star=yes" in (root / ".picasa.ini").read_text(encoding="utf-8")
    assert (idegen / ".picasa.ini").read_bytes() == erintetlen_ini
