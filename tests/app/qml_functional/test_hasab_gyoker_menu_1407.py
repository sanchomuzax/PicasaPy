"""#1407 (5–6. pont) — a négy gyökér-tétel a menüben, és a hasáb fejléce.

A gyökér-váltás MECHANIZMUSÁT a `tests/app/test_hasab_gyokerek_1407.py`
méri (a vezérlőn, mérésre cserélhető rendszermappa-feloldóval). Ez a lap a
FELÜLET oldala:

- ott van-e mind a négy tétel (spec 2.2), a mért sorrendben,
- a rádiógomb-pipa a választott gyökéren áll-e (`0x00574b70`),
- a Mappák fejléce a mért feliratot mutatja-e (spec 4.2).

⚠️ A `mypics`/`mydocs`/`desktop` tételek elsülését itt SZÁNDÉKOSAN nem
kattintjuk: a valódi rendszermappákra oldódnának fel, és a próba a futtató
gép XDG-beállításait mérné. Azt az ágat a vezérlő próbái fedik, cserélt
feloldóval.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt

#: A négy tétel a spec 2.2 sorrendjében: Sajátgép · Képek · Dokumentumok · Asztal
GYOKER_TETELEK = [
    ("menuViewRootMyComputer", "My &Computer"),
    ("menuViewRootMyPictures", "My &Pictures"),
    ("menuViewRootMyDocuments", "My Do&cuments"),
    ("menuViewRootDesktop", "&Desktop"),
]


def _trigger(root, nev):
    elem = root.findChild(QObject, nev)
    assert elem is not None, f"nincs meg a menütétel: {nev}"
    if elem.property("checkable"):
        QMetaObject.invokeMethod(elem, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(elem, "triggered", Qt.ConnectionType.DirectConnection)
    return elem


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


class TestANegyTetelOttVan:
    def test_mind_a_negy_megvan_a_mert_felirattal(self, qml_app):
        window, _controller, _e = qml_app
        for nev, felirat in GYOKER_TETELEK:
            tetel = window.findChild(QObject, nev)
            assert tetel is not None, f"hiányzik a gyökér-tétel: {nev}"
            assert tetel.property("text") == felirat
            assert tetel.property("checkable") is True, (
                "a gyökér-tételek rádiógomb-pipát kapnak (spec 4.5/b)"
            )

    def test_a_sorrend_a_spec_2_2_szerinti(self, qml_app):
        """A menü tételei a felfedezés sorrendjében jönnek létre, ezért az
        objektumfa bejárása a MENÜ sorrendjét adja."""
        window, _controller, _e = qml_app
        keresett = [nev for nev, _ in GYOKER_TETELEK]
        latott = []

        def bejar(elem):
            for gyermek in elem.children():
                nev = gyermek.objectName() or ""
                if nev in keresett and nev not in latott:
                    latott.append(nev)
                bejar(gyermek)

        bejar(window)
        assert latott == keresett, f"a menü sorrendje eltér: {latott}"


class TestAPipaAValasztottGyokeren:
    def test_a_sajatgep_tetel_a_fara_valt_es_pipat_kap(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        sajatgep = window.findChild(QObject, "menuViewRootMyComputer")
        assert sajatgep.property("checked") is False, (
            "a lapos nézetben nem lehet a Sajátgépen a pipa"
        )

        _trigger(window, "menuViewRootMyComputer")

        assert _var(qt_app, lambda: sajatgep.property("checked") is True), (
            "a Sajátgép-tételen nem jelent meg a pipa"
        )
        fanezet = window.findChild(QObject, "menuViewTreeView")
        assert fanezet.property("checked") is True, "nem váltott fanézetre"

    def test_a_lapos_nezet_leveszi_a_pipat(self, qml_app, qt_app):
        """MÉRT buktató (#1454): a pipa-visszakötés hiányában a Sajátgép
        pipája ottmaradna, pedig már a lapos nézetben vagyunk."""
        window, _controller, _e = qml_app
        sajatgep = window.findChild(QObject, "menuViewRootMyComputer")
        _trigger(window, "menuViewRootMyComputer")
        assert _var(qt_app, lambda: sajatgep.property("checked") is True)

        _trigger(window, "menuViewFlatFolderView")

        assert _var(qt_app, lambda: sajatgep.property("checked") is False), (
            "a Sajátgép pipája ottmaradt a lapos nézetben"
        )


class TestAHasabFejlece:
    """Spec 4.2: pontosan KÉT rögzített felirat van."""

    def test_lapos_nezetben_az_alapertelmezett_nezet(self, qml_app):
        window, _controller, _e = qml_app
        fejlec = window.findChild(QObject, "folderPaneHeader")
        assert fejlec is not None
        #: a fejléc a darabszámot is hordozza („Default View (1)")
        assert fejlec.property("text").startswith("Default View")

    def test_fanezetben_a_sajatgep(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        fejlec = window.findChild(QObject, "folderPaneHeader")
        _trigger(window, "menuViewTreeView")
        assert _var(qt_app, lambda: fejlec.property("text").startswith("My Computer")), (
            f"a fejléc nem a mért feliratot mutatja: {fejlec.property('text')!r}"
        )

    def test_az_egyszerusitett_fanezet_is_a_sajatgep(self, qml_app, qt_app):
        """`watched` és `all` UGYANAZT a feliratot kapja (`ViewRoot::All`)."""
        window, _controller, _e = qml_app
        fejlec = window.findChild(QObject, "folderPaneHeader")
        _trigger(window, "menuViewTreeView")
        _trigger(window, "menuViewSimplifiedTreeView")
        assert _var(qt_app, lambda: fejlec.property("text").startswith("My Computer"))

    def test_a_keresesi_fejlec_TOVABBRA_is_felulirja(self, qml_app, qt_app):
        """Kontroll: a keresés kiírása (#7) nem eshetett ki a felirat
        cserélésével."""
        window, controller, _e = qml_app
        fejlec = window.findChild(QObject, "folderPaneHeader")
        controller.search("a")
        assert _var(
            qt_app,
            lambda: fejlec.property("text").startswith("Search results for"),
        ), f"a keresési fejléc elveszett: {fejlec.property('text')!r}"
