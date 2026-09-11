"""#798: a Shift LENYOMÁSÁRA váltanak a csempék, nem csak fülváltáskor.

## Amit a tulajdonos lát

> „Az effekt csempéken a Shift funkció még mindig nem működik."

A #2146 megépítette a Shift-ágat, de az állapotot pontosan KÉTSZER
olvastuk: a panel felépülésekor és fülváltáskor. Aki az effekt-fülön áll
és megnyomja a Shiftet, semmit nem lát.

## A mérés, ami a „csak egyszer olvas" olvasatot cáfolja

A `VK_SHIFT` lekérdezése a `FUN_005d7c20`-ban van
(`0x005d7c91`: `push 0x10` → `call [0xc406f8]` → `shr eax,0xf` →
`mov [ecx+0x33a8], al`). Ugyanez a függvény **`LoadCursorA`-t és
`SetCursor`-t is hív** (`imports.csv`) — az egérmutató beállítása
mutató-eseményhez tartozik, nem egyszeri felépítéshez. A két ismert
hívója közül az egyik (`FUN_005e6710`) a nevesített parancsok kezelője
(`searchcontainer/searchbutton`, `thumbui/startoggle`,
`editpanel/edithelpbutton`).

⚠️ A bináris nem mondja ki szó szerint, hogy „képkockánként olvas"; azt
viszont igen, hogy a lekérdezés **interakciós útvonalon** ül. A
felhasználó által LÁTOTT viselkedés pedig egyértelmű: a Shift lenyomása
azonnal átváltja a csempéket.

## Miért nem fogta meg egyetlen őr sem

A #2146 őrei a QML FORRÁSÁT olvassák: azt állítják, hogy a Shift-ág
létezik és helyes nevet ad. Egyik sem nyom le billentyűt. Ez a fájl
igen — valódi `QKeyEvent`-et küld az alkalmazásnak.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent


def _shift(tipus) -> QKeyEvent:
    return QKeyEvent(tipus, Qt.Key.Key_Shift, Qt.KeyboardModifier.ShiftModifier)


def _kuldd(esemeny: QKeyEvent) -> None:
    """A billentyű-esemény az ALKALMAZÁSNAK — ahogy az ablakból érkezne."""
    QGuiApplication.sendEvent(QGuiApplication.instance(), esemeny)


@pytest.fixture
def edit_controller(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    vezerlo = EditController(EditPreviewProvider())
    yield vezerlo
    vezerlo.shutdown() if hasattr(vezerlo, "shutdown") else None


class TestAzEloAllapot:
    def test_alapbol_NINCS_lenyomva(self, edit_controller):
        assert edit_controller.shiftAktiv is False

    def test_a_LENYOMAS_atbillenti(self, edit_controller):
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        assert edit_controller.shiftAktiv is True, (
            "a Shift lenyomására nem változott az állapot — a csempék "
            "a felhasználónál sem váltanak"
        )

    def test_az_ELENGEDES_visszabillenti(self, edit_controller):
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        _kuldd(_shift(QKeyEvent.Type.KeyRelease))
        assert edit_controller.shiftAktiv is False

    def test_a_JELZES_eldordul(self, edit_controller):
        valtozasok = []
        edit_controller.shiftAktivChanged.connect(
            lambda: valtozasok.append(edit_controller.shiftAktiv)
        )
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        _kuldd(_shift(QKeyEvent.Type.KeyRelease))
        assert valtozasok == [True, False], (
            "a kötés nem értékelődik újra — QML-ben a csempe felirata "
            f"változatlan maradna (jelzések: {valtozasok})"
        )

    def test_az_ISMETELT_lenyomas_nem_ad_uj_jelzest(self, edit_controller):
        """A nyomva tartás automatikus ismétlése ne pörgesse a kötéseket."""
        valtozasok = []
        edit_controller.shiftAktivChanged.connect(
            lambda: valtozasok.append(edit_controller.shiftAktiv)
        )
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        assert len(valtozasok) == 1, f"{len(valtozasok)} jelzés egy váltásra"

    def test_MAS_billentyu_nem_hat_ra(self, edit_controller):
        masik = QKeyEvent(
            QKeyEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier,
        )
        _kuldd(masik)
        assert edit_controller.shiftAktiv is False

    def test_a_REGI_lekerdezes_is_megmarad(self, edit_controller):
        """A `shiftLenyomva()` a pillanatnyi állapotot adja — a #2146
        hívóit nem törjük el."""
        assert edit_controller.shiftLenyomva() in (True, False)


@pytest.fixture
def editor_panel(qt_app, edit_controller):
    """Az EditorPanel valódi QML-motorban, az ÉLES vezérlővel.

    A motor és a komponens a fixture kerete miatt marad életben — ha a
    hívó frame eltűnik, a QML-motor elviszi a példányt (mérve: „Internal
    C++ object already deleted")."""
    from pathlib import Path as Ut

    import picasapy.app
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    qml = Ut(picasapy.app.__file__).parent / "qml"
    motor = QQmlEngine()
    motor.addImportPath(str(qml))
    motor.rootContext().setContextProperty("editController", edit_controller)
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(qml / "PicasaPy" / "EditorPanel.qml"))
    )
    panel = komponens.create()
    assert panel is not None, komponens.errorString()
    yield panel
    panel.deleteLater()


class TestACsempeFelirata:
    """A csempe feliratának a BILLENTYŰRE kell változnia (#798).

    A #2146 őrei a QML forrását olvassák; ez a próba valódi QML-motort
    futtat, lenyomja a Shiftet, és a panel állapotát nézi utána — a
    kilenc csempe felirata és szűrője erre a tulajdonságra van kötve
    (`EditorEffectsTab1.qml`), tehát ez a felirat útja.
    """

    def test_a_panel_kotese_KOVETI_a_billentyut(self, editor_panel):
        assert editor_panel.property("shiftMasodlagos") is False
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        assert editor_panel.property("shiftMasodlagos") is True, (
            "a panel nem követi a Shift lenyomását — a kilenc csempe "
            "felirata változatlan marad"
        )
        _kuldd(_shift(QKeyEvent.Type.KeyRelease))
        assert editor_panel.property("shiftMasodlagos") is False
