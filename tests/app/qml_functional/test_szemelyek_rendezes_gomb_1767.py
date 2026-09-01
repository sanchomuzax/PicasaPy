"""#1767 — a Személyek rendezésének három menütétele a felületről.

A három tétel eddig `placeholder: true` volt: **látszott, kattintható
volt, és nem csinált semmit**. A rendezés magját a
`tests/index/test_szemelyek_rendezes_1767.py` méri; ez a fájl a
bekötést és a rádió-viselkedést.

⚠️ RÁDIÓ-CSAPDA (#1464/#1468): a valódi kattintás előbb IMPERATÍVAN
átbillenti a `checked`-et, és a `setPeopleSort` azonos értéknél nem
változtat állapotot — a kötés magától soha nem értékelődne újra, tehát a
menü újranyitásakor egyik tételen sem állna pipa. A tételek ezért a
jelzés után VISSZAKÖTIK a `checked`-et; a teszt ezt is méri.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

_MENU = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/FolderListContextMenu.qml"
)
_PANE = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/FolderPane.qml"
)

_TETELEK = {
    "folderListMenuSortPeopleByName": "name",
    "folderListMenuSortPeopleByCount": "count",
    "folderListMenuSortPeopleByTopList": "top",
}


class TestATetelekELOK:
    def test_egyik_sem_helyfoglalo(self):
        forras = _MENU.read_text(encoding="utf-8")
        for nev in _TETELEK:
            kezdet = forras.index(f'objectName: "{nev}"')
            blokk = forras[kezdet : kezdet + 400]
            assert "placeholder: true" not in blokk, (
                f"{nev} még mindig néma helyfoglaló (#1767)"
            )
            assert "onTriggered:" in blokk, f"{nev}: nincs kezelője"

    def test_a_jelzest_a_hasab_elkapja(self):
        assert "onPeopleSortRequested" in _PANE.read_text(encoding="utf-8")

    def test_mindharom_VISSZAKOTI_a_pipat(self):
        """A rádió-csapda ellen — enélkül a menü újranyitásakor egyik
        tételen sem állna pipa."""
        forras = _MENU.read_text(encoding="utf-8")
        for nev in _TETELEK:
            kezdet = forras.index(f'objectName: "{nev}"')
            blokk = forras[kezdet : kezdet + 400]
            assert "Qt.binding(" in blokk, (
                f"{nev}: a `checked` nincs visszakötve a jelzés után"
            )


class TestAzEloFaban:
    def test_a_harom_tetel_letezik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        for nev in _TETELEK:
            assert window.findChild(QObject, nev) is not None, nev

    def test_egyszerre_pontosan_egy_pipa(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        eredeti = controller.peopleSort
        try:
            for nev, mod in _TETELEK.items():
                controller.setPeopleSort(mod)
                qt_app.processEvents()
                pipak = [
                    n
                    for n in _TETELEK
                    if window.findChild(QObject, n).property("checked")
                ]
                assert pipak == [nev], (
                    f"{mod!r} módban a pipák: {pipak}"
                )
        finally:
            controller.setPeopleSort(eredeti)


class TestAVezerlo:
    def test_alapbol_nev_szerint(self, qml_app, qt_app):
        _window, controller, _engine = qml_app
        assert controller.peopleSort == "name"

    def test_a_valasztas_ELTEVODIK(self, qml_app, qt_app):
        _window, controller, _engine = qml_app
        try:
            controller.setPeopleSort("count")
            assert controller.peopleSort == "count"
        finally:
            controller.setPeopleSort("name")

    def test_ismeretlen_modot_NEM_tarol_el(self, qml_app, qt_app):
        """Egy elgépelt érték némán elrontaná a következő indulást."""
        _window, controller, _engine = qml_app
        controller.setPeopleSort("nincs-ilyen")
        assert controller.peopleSort == "name"
