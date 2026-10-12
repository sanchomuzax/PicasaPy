"""#4599 — az album „Sort Album By" almenüje TÉNYLEGES kattintással.

A tételre kattint (nem a metódust hívja; a Shift-es változatnál a Shift-et
lenyomva), majd nézi (1) a rácsot, (2) a lemezen lévő `.picasa.ini`-k
`albumorder=` sorait és (3) egy újraépített index sorrendjét — köztük egy két
mappára szóró albumon. A szomszéd album és a szakaszok többi sora bájtra
változatlan.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QPoint, QPointF, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.index import album_photos, open_index, sync_tree
from picasapy.ini.album_order import places_of
from picasapy.ini.document import parse_document
from support.jpeg_factory import make_jpeg

_TOKEN = "4599" * 8
_OTHER = "e" * 32

# (mappa, név, kép mérete, felvétel ideje)
_KEPEK = (
    ("", "b10.jpg", (200, 200), "2020:03:01 10:00:00"),
    ("", "b2.jpg", (40, 40), "2020:01:01 10:00:00"),
    ("", "a.jpg", (120, 120), "2020:02:01 10:00:00"),
    ("masodik", "c.jpg", (80, 80), "2020:04:01 10:00:00"),
)


def _child(root, name):
    child = root.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _visual_item(root, name):
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


def _katt(window, elem, gomb=Qt.LeftButton, modositok=Qt.NoModifier):
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window, gomb, modositok, QPoint(round(pont.x()), round(pont.y()))
    )


def _almenu_delegat(menu, almenu):
    """A szülőmenü sora, amely az almenüt nyitja (a felirata az almenü címe)."""
    cim = almenu.property("title")
    pending = [menu.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == cim
            and not item.objectName()
        ):
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{cim!r} almenü-sora nem található")


def _konyvtar(root, tmp_path):
    (root / "masodik").mkdir()
    for mappa, nev, meret, ido in _KEPEK:
        make_jpeg((root / mappa / nev) if mappa else (root / nev), size=meret, taken_at=ido)
    # CRLF sorvégek: a Picasa Windowson ír, a kiírásnak meg kell őriznie
    (root / ".picasa.ini").write_bytes(
        (
            f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Nyaralás\n"
            f"[.album:{_OTHER}]\ntoken={_OTHER}\nname=Másik\n"
            f"[b10.jpg]\nalbums={_TOKEN},{_OTHER}\npriority=7.0\ncaption=marad\n"
            f"[b2.jpg]\nalbums={_TOKEN}\nstar=yes\n"
            f"[a.jpg]\nalbums={_TOKEN},{_OTHER}\nalbumorder={_OTHER}:4.5\n"
        ).replace("\n", "\r\n").encode("utf-8")
    )
    (root / "masodik" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Nyaralás\n"
        f"[c.jpg]\nalbums={_TOKEN}\n",
        encoding="utf-8",
    )


def _rendez_kattintassal(window, qt_app, tetel, modositok=Qt.NoModifier):
    sor = _visual_item(window, f"albumItem_{_TOKEN}")
    _katt(window, sor, Qt.RightButton)
    menu = _child(window, "albumContextMenu")
    _varj(lambda: menu.property("visible"), qt_app, "album helyi menü")

    almenu = _child(window, "albumMenuSortAlbumBy")
    _katt(window, _almenu_delegat(menu, almenu))
    _varj(lambda: almenu.property("visible"), qt_app, "Sort Album By almenü")

    elem = _child(window, tetel)
    assert elem.property("enabled") is True
    shift = bool(modositok & Qt.ShiftModifier)
    if shift:
        # a felhasználó LENYOMVA tartja a Shiftet, miközben kattint
        QTest.keyPress(window, Qt.Key_Shift)
    try:
        _katt(window, elem, modositok=modositok)
    finally:
        if shift:
            QTest.keyRelease(window, Qt.Key_Shift)
    _varj(lambda: not menu.property("visible"), qt_app, "menü bezárása")


def _albumorder_nelkul(ini):
    """A fájl bájtjai az `albumorder=` sorok nélkül (sorvégek megőrizve)."""
    return b"".join(
        sor
        for sor in ini.read_bytes().splitlines(keepends=True)
        if not sor.startswith(b"albumorder=")
    )


def _racs(controller):
    return [(p.folder_path.rsplit("/", 1)[-1], p.name) for p in controller._photos.photos]


def _lemez(root):
    return {
        "fo": parse_document((root / ".picasa.ini").read_text(encoding="utf-8")),
        "masodik": parse_document(
            (root / "masodik" / ".picasa.ini").read_text(encoding="utf-8")
        ),
    }


def _ujranyitott_index(tmp_path, root):
    with open_index(tmp_path / "ujra.db") as conn:
        sync_tree(conn, root)
        return [(r.folder_path.rsplit("/", 1)[-1], r.name) for r in album_photos(conn, _TOKEN)]


def test_kattintasra_nev_szerint_rendez_es_a_sorrend_tartos(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    _konyvtar(root, tmp_path)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()
    # rendezés előtt: a mai rend (mappa útvonala, név)
    assert _racs(controller) == [
        ("kepek", "a.jpg"), ("kepek", "b10.jpg"), ("kepek", "b2.jpg"),
        ("masodik", "c.jpg"),
    ]
    szomszed_elotte = _albumorder_nelkul(root / ".picasa.ini")

    _rendez_kattintassal(window, qt_app, "albumMenuSortByName")

    varhato = [
        ("kepek", "a.jpg"), ("kepek", "b2.jpg"), ("kepek", "b10.jpg"),
        ("masodik", "c.jpg"),
    ]
    _varj(lambda: _racs(controller) == varhato, qt_app, "a rács átrendeződése")
    lemez = _lemez(root)
    assert places_of(lemez["fo"])["a.jpg"][_TOKEN] == 1.0
    assert places_of(lemez["fo"])["b2.jpg"][_TOKEN] == 2.0
    assert places_of(lemez["fo"])["b10.jpg"][_TOKEN] == 3.0
    assert places_of(lemez["masodik"])["c.jpg"][_TOKEN] == 4.0
    # a szomszéd album helye és minden más sor bájtra azonos
    assert places_of(lemez["fo"])["a.jpg"][_OTHER] == 4.5
    # minden más sor (sorvégekkel együtt) BÁJTRA azonos: az `albumorder=`
    # sorok kivételével a fájl nem változott
    assert _albumorder_nelkul(root / ".picasa.ini") == szomszed_elotte
    assert b"\r\n" in (root / ".picasa.ini").read_bytes()
    # újraindítás (új index) után is ez a sorrend
    assert _ujranyitott_index(tmp_path, root) == varhato


def test_shift_csokkeno_meret_es_fordított(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    _konyvtar(root, tmp_path)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()

    # méret szerint növekvő: b2 (40) < c (80) < a (120) < b10 (200)
    _rendez_kattintassal(window, qt_app, "albumMenuSortBySize")
    novekvo = [("kepek", "b2.jpg"), ("masodik", "c.jpg"), ("kepek", "a.jpg"),
               ("kepek", "b10.jpg")]
    _varj(lambda: _racs(controller) == novekvo, qt_app, "méret szerint növekvő")

    # Shifttel csökkenő
    _rendez_kattintassal(
        window, qt_app, "albumMenuSortBySize", Qt.ShiftModifier
    )
    csokkeno = novekvo[::-1]
    _varj(lambda: _racs(controller) == csokkeno, qt_app, "Shifttel csökkenő")
    assert _ujranyitott_index(tmp_path, root) == csokkeno

    # Fordított: a tárolt (csökkenő) sorrendet megfordítja
    _rendez_kattintassal(window, qt_app, "albumMenuSortReverse")
    _varj(lambda: _racs(controller) == novekvo, qt_app, "fordított sorrend")
    assert _ujranyitott_index(tmp_path, root) == novekvo


def test_datum_szerint_a_felvetel_ideje_dont(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    _konyvtar(root, tmp_path)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()

    _rendez_kattintassal(window, qt_app, "albumMenuSortByDate")

    # b2 (jan) < a (feb) < b10 (márc) < c (ápr)
    varhato = [("kepek", "b2.jpg"), ("kepek", "a.jpg"), ("kepek", "b10.jpg"),
               ("masodik", "c.jpg")]
    _varj(lambda: _racs(controller) == varhato, qt_app, "dátum szerint")
    assert _ujranyitott_index(tmp_path, root) == varhato


def test_bukott_mappairas_hangos_megnevezi_a_mappat_es_megismetelheto(
    qml_app, qt_app, tmp_path, monkeypatch
):
    import picasapy.ini.album_order as modul

    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    _konyvtar(root, tmp_path)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()
    uzenetek = []
    controller.albumWriteFailed.connect(uzenetek.append)
    eredeti = modul.update_document

    def hibas(path, mutate, **kwargs):
        if "masodik" in str(path):
            raise OSError("nem írható")
        return eredeti(path, mutate, **kwargs)

    monkeypatch.setattr(modul, "update_document", hibas)

    assert controller.sortAlbumBy(_TOKEN, "name") is False

    assert len(uzenetek) == 1
    assert "masodik" in uzenetek[0]
    # a másik mappa kiíródott, a bukotté a régi hely (nincs) maradt
    lemez = _lemez(root)
    assert places_of(lemez["fo"])["a.jpg"][_TOKEN] == 1.0
    assert _TOKEN not in places_of(lemez["masodik"]).get("c.jpg", {})

    # a művelet megismételhető
    monkeypatch.setattr(modul, "update_document", eredeti)
    assert controller.sortAlbumBy(_TOKEN, "name") is True
    assert places_of(_lemez(root)["masodik"])["c.jpg"][_TOKEN] == 4.0


def test_ismeretlen_mod_es_ismeretlen_album_nem_ir(qml_app, qt_app, tmp_path):
    _window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    _konyvtar(root, tmp_path)
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    controller._reload_after_sync()
    elotte = {
        p: p.read_bytes() for p in (root / ".picasa.ini", root / "masodik" / ".picasa.ini")
    }

    assert controller.sortAlbumBy(_TOKEN, "szin") is False
    assert controller.sortAlbumBy("nincs-ilyen", "name") is False

    assert {p: p.read_bytes() for p in elotte} == elotte
