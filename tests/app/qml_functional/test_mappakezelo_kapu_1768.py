"""A Mappakezelő két belépési pontja SZÜRKE szerkesztés közben — #1768.

Az eredeti Picasa a `0x9caa` parancsot (a Mappakezelő MINDKÉT menütételét)
a menü megnyitásakor szürkíti, amíg a szerkesztő-előnézet él
(`editpanel/preview`, `FUN_0056e1c0`; az engedélyezés `0x0056f562`–
`0x0056f56c`). Nálunk mindkettő mindig kattintható volt.

## A leképezés, kimondva

Nálunk a szerkesztőpanel a NÉZŐBEN lakik (`PhotoViewer.qml` →
`EditorPanel`), külön láthatóság-kapcsoló nélkül. A „szerkesztő-előnézet
él" feltétel megfelelője tehát a NYITOTT NÉZŐ — ez a `photoActionsEnabled`
már meglévő mintája is (`!window.viewerOpen`).

## Miért szürkítés, nem hibaüzenet

A jegy külön kiköti: az eredeti sem üzen. A szürke tétel maga az üzenet.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest

_MENU = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")

#: A két belépési pont — az eredetiben UGYANAZ a parancsazonosító.
KET_BELEPES = ("menuFileAddFolder", "menuToolsFolderManager")


def _blokk(nev: str, hossz: int = 700) -> str:
    kezd = _MENU.index(f'objectName: "{nev}"')
    return _MENU[kezd : kezd + hossz]


class TestAKapu:
    @pytest.mark.parametrize("nev", KET_BELEPES)
    def test_a_tetel_a_szerkeszto_allapotahoz_kotodik(self, nev):
        assert "enabled: !bar.editorActive" in _blokk(nev)

    @pytest.mark.parametrize("nev", KET_BELEPES)
    def test_ugyanazt_a_parancsot_inditja(self, nev):
        """Ha a két tétel más jelet adna, a kapu is elválhatna."""
        assert "bar.folderManagerRequested()" in _blokk(nev)

    def test_van_ilyen_allapot_a_menusavon(self):
        assert "property bool editorActive: false" in _MENU

    def test_a_gazdaablak_BEKOTI(self):
        """A #1153 osztálya: az állapot ott van, de senki nem tölti fel —
        akkor a kapu sosem zárna."""
        assert "editorActive: window.viewerOpen" in _MAIN


class TestNincsHibauzenet:
    @pytest.mark.parametrize("nev", KET_BELEPES)
    def test_a_tetel_NEM_uzen(self, nev):
        """A jegy kiköti: a kattinthatatlanság szürkítéssel valósul meg,
        nem hibaüzenettel — az eredeti sem üzen."""
        blokk = _blokk(nev)
        for tiltott in ("Dialog", "showMessage", "errorRequested", "warning"):
            assert tiltott not in blokk, f"{nev}: üzenet-ág a menütételben"


class TestAKirajzoltMenu:
    """A forrás-állítás a deklarációt méri; ez azt, hogy a kötés
    futásidőben tényleg VÁLT.

    ⚠️ A kaput a menüsáv `editorActive` állapotán át hajtjuk meg, nem a
    `window.viewerOpen`-en keresztül. Ennek MÉRT oka van: ebben a
    próbapadban a `window.setProperty("viewerOpen", …)` beállítja ugyan az
    értéket, de a menüsáv rá épülő kötése nem értékelődik újra — ugyanez
    igaz a régóta meglévő `photoActionsEnabled: !window.viewerOpen`
    kötésre is, tehát a próbapad korlátja, nem ezé a jegyé. A `viewerOpen`
    → `editorActive` szálat ezért a `TestAKapu` állítja a forrásból; itt
    az `editorActive` → `enabled` szálat mérjük, kirajzolva.
    """

    @staticmethod
    def _menusav(tetel):
        """A menüsáv példánya a tétel ŐSEI közt — az `editorActive`
        tulajdonság azonosítja."""
        while tetel is not None and tetel.property("editorActive") is None:
            tetel = tetel.parent()
        return tetel

    def test_a_ket_tetel_koveti_az_editorActive_allapotot(
        self, qml_app, qt_app
    ):
        from PySide6.QtCore import QObject

        window, _controller, _engine = qml_app[:3]
        tetelek = {
            nev: window.findChild(QObject, nev) for nev in KET_BELEPES
        }
        for nev, tetel in tetelek.items():
            assert tetel is not None, f"{nev} nincs a kirajzolt ablakban"

        bar = self._menusav(tetelek[KET_BELEPES[0]])
        assert bar is not None, "a menüsáv példánya nem található"

        bar.setProperty("editorActive", False)
        qt_app.processEvents()
        for nev, tetel in tetelek.items():
            assert tetel.property("enabled") is True, (
                f"{nev}: zárva maradt, pedig a szerkesztő nincs nyitva"
            )

        bar.setProperty("editorActive", True)
        qt_app.processEvents()
        for nev, tetel in tetelek.items():
            assert tetel.property("enabled") is False, (
                f"{nev}: nyitva maradt, pedig a szerkesztő él"
            )

        bar.setProperty("editorActive", False)
