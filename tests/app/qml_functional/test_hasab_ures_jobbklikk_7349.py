"""#7349: a bal hasáb üres részén a jobbklikk nem nyit menüt, mint az eredetiben.

Az eredeti Picasában az `AlbumList` menü egyetlen belépése a ▾ gomb
(`0x005e2000`, hívója `0x005d9cc0`); a hasáb üres részére egyik menü sem ad
(Colab job-801, 05-06. és 09-10. kép; `docs/specs/paritas-folyamat-7326.md`,
8. szakasz, J6).

A próbák valódi `QTest.mouseClick`-kel kattintanak a főablakon. A nyitást és a
hasáb képkockáját mérik; az eredeti képével való vizuális egyezést NEM.

Rontás-kontroll (futás közben): a `FolderPane.qml`-be visszatett
`TapHandler { acceptedButtons: Qt.RightButton ... }` és a menüpéldány mellett
mindhárom próba pirosra vált (a menü megnyílik, a kezelő létezik).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF
from PySide6.QtTest import QTest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    elokeszit_str,
    gyerek,
    jobbklikk_mappan,
    kattints,
    varj,
    zar,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import jobbklikk_a_ponton

#: A hasáb és a fejléc minden jobbklikk-menüje, valamint a ▾ gomb legördülője:
#: az üres részen egyik sem nyílhat meg.
_MENUK = (
    "folderListContextMenu",
    "toolbarFolderListMenu",
    "folderContextMenu",
    "hierFolderContextMenu",
    "albumContextMenu",
    "peopleAlbumContextMenu",
    "collectionContextMenu",
    "recentlyUpdatedContextMenu",
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nyitott_menuk(window) -> list[str]:
    nyitott = []
    for nev in _MENUK:
        menu = window.findChild(QObject, nev)
        if menu is not None and (
            menu.property("visible") is True or menu.property("opened") is True
        ):
            nyitott.append(nev)
    return nyitott


def _negativ_ablak(qt_app) -> None:
    """Rögzített várakozás a „nem történik semmi" állításhoz (feltétel nincs,
    amire várni lehetne)."""
    QTest.qWait(300)
    qt_app.processEvents()


def _ures_pont(pane) -> QPointF:
    """A hasáb alsó, sorok alatti pontja (ablak-koordinátában)."""
    assert pane.width() > 0 and pane.height() > 0
    return pane.mapToScene(QPointF(pane.width() / 2, pane.height() - 8))


def _pane_kep(window, pane):
    """A hasáb képkockája a renderelt ablakból."""
    teljes = window.grabWindow()
    assert not teljes.isNull(), "az ablak nem rajzolódott ki"
    dpr = teljes.devicePixelRatio()
    bal_felso = pane.mapToScene(QPointF(0, 0))
    return teljes.copy(
        round(bal_felso.x() * dpr),
        round(bal_felso.y() * dpr),
        round(pane.width() * dpr),
        round(pane.height() * dpr),
    )


def _mukodo_belepes_meg_van(window, qt_app, controller) -> None:
    """A szomszéd: a mappasor jobbklikk-menüje (a hasáb egy másik belépése)."""
    cel = elokeszit_str(window, qt_app, controller)
    menu = jobbklikk_mappan(window, qt_app, cel)
    assert menu.property("visible") is True
    zar(qt_app, menu)


@pytest.mark.parametrize("fanezet", (False, True), ids=("lapos", "fanezet"))
class TestAzUresHasabJobbklikkje:
    def _beallit(self, window, qt_app, controller, fanezet: bool):
        elokeszit_str(window, qt_app, controller)
        pane = gyerek(window, "folderPane")
        fa = pane.property("hierarchyController")
        fa.setTreeView(fanezet)
        assert varj(qt_app, lambda: fa.property("treeView") is fanezet), (
            "a hasáb nézetmódja nem állt be"
        )
        qt_app.processEvents()
        return pane

    def test_nem_nyit_menut(self, mappa_app, qt_app, fanezet):
        window, controller, _motor = mappa_app
        pane = self._beallit(window, qt_app, controller, fanezet)

        jobbklikk_a_ponton(window, qt_app, _ures_pont(pane))

        # negatív ablak: a menü nyitása a gombfelengedésre azonnal megtörténne,
        # ezért rögzített idő után mérjük, hogy MAR SEM nyílt meg
        _negativ_ablak(qt_app)
        assert _nyitott_menuk(window) == [], (
            "a hasáb üres részének jobbklikkje menüt nyitott, az eredetiben "
            f"nincs ilyen belépés: {_nyitott_menuk(window)}"
        )

    def test_a_hasab_kepkockaja_valtozatlan(self, mappa_app, qt_app, fanezet):
        window, controller, _motor = mappa_app
        pane = self._beallit(window, qt_app, controller, fanezet)
        elotte = _pane_kep(window, pane)

        jobbklikk_a_ponton(window, qt_app, _ures_pont(pane))
        _negativ_ablak(qt_app)
        utana = _pane_kep(window, pane)

        assert elotte == utana, (
            "a jobbklikk megváltoztatta a hasáb képkockáját (menü vagy kijelölés)"
        )


class TestAHasabBelepeseiMegvannak:
    def test_nincs_ures_reszi_jobbklikk_kezelo_es_belepo_fuggveny(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        pane = gyerek(window, "folderPane")

        assert window.findChild(QObject, "folderPaneContextMenuHandler") is None, (
            "a hasáb üres részén még van jobbklikk-kezelő"
        )
        assert window.findChild(QObject, "folderListContextMenu") is None, (
            "a hasáb még tartja a ▾ gombon kívüli FolderListContextMenu példányt"
        )
        meta = pane.metaObject()
        metodusok = {
            bytes(meta.method(i).name()).decode() for i in range(meta.methodCount())
        }
        assert "openFolderListContextMenu" not in metodusok

    def test_a_mappasor_jobbklikk_menuje_valtozatlan(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        _mukodo_belepes_meg_van(window, qt_app, controller)

    def test_a_nezetbeallito_nyil_tovabbra_is_nyitja_a_sajat_legordulojet(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        menu = gyerek(window, "toolbarFolderListMenu")
        assert menu.property("visible") is False

        kattints(window, qt_app, gyerek(window, "toolbarFolderViewPopupButton"))

        assert varj(qt_app, lambda: menu.property("visible") is True), (
            "a ▾ gomb nem nyitotta meg a saját legördülőjét"
        )
        zar(qt_app, menu)


def test_a_vizsgalt_pont_tenyleg_ures(mappa_app, qt_app):
    """Őr a próbáknak: a kattintási pont nem esik mappasorra, tehát a hiányzó
    menü az üres hasáb belépésének hiányát méri, nem egy sor eltakarását."""
    window, controller, _motor = mappa_app
    elokeszit_str(window, qt_app, controller)
    pane = gyerek(window, "folderPane")
    pont = _ures_pont(pane)
    for item in _vizualis(window.contentItem()):
        nev = item.objectName()
        if nev.startswith(("folderRowMouse", "hierRowMouse:")) and item.isVisible():
            bal_felso = item.mapToScene(QPointF(0, 0))
            assert not (
                bal_felso.x() <= pont.x() <= bal_felso.x() + item.width()
                and bal_felso.y() <= pont.y() <= bal_felso.y() + item.height()
            ), f"a kattintási pont a(z) {nev} soron van"


def _vizualis(item):
    for gyerek_elem in item.childItems():
        yield gyerek_elem
        yield from _vizualis(gyerek_elem)

