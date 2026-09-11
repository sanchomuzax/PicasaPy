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
    # #798: a figyelés az effekt-füleken kapcsolódik be (a panel teszi);
    # itt kézzel, mert a vezérlőt panel nélkül próbáljuk.
    vezerlo.figyeldAShiftet(True)
    yield vezerlo
    vezerlo.figyeldAShiftet(False)
    vezerlo.shutdown() if hasattr(vezerlo, "shutdown") else None


class TestAFigyelesKapcsoloja:
    """A szűrő CSAK az effekt-füleken van fent (#798).

    ⚠️ Mérve: az alkalmazás-szintű eseményszűrő MINDEN eseményre átlép
    Pythonba. Állandóra téve a `tests/app/qml_functional/test_people_panel_26.py`
    futásideje 13 s-ról **25 s-ra** nőtt, és két időzítésre épülő próba el
    is bukott — a felhasználó ugyanezt a lassulást kapná az egész
    felületen, egy olyan funkcióért, ami csak az effekt-fülön él.
    """

    def test_alapbol_NEM_figyel(self, qt_app):
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider

        vezerlo = EditController(EditPreviewProvider())
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        try:
            assert vezerlo.shiftAktiv is False, (
                "a vezérlő figyel, pedig senki nem kérte — ez az egész "
                "felületet lassítja"
            )
        finally:
            _kuldd(_shift(QKeyEvent.Type.KeyRelease))

    def test_a_KIKAPCSOLAS_visszaallitja_az_allapotot(self, edit_controller):
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        assert edit_controller.shiftAktiv is True
        edit_controller.figyeldAShiftet(False)
        assert edit_controller.shiftAktiv is False, (
            "a fülről lelépve a csempék Shift-es állapotban ragadnának"
        )
        _kuldd(_shift(QKeyEvent.Type.KeyRelease))
        edit_controller.figyeldAShiftet(True)

    def test_a_BEKAPCSOLAS_beolvassa_a_pillanatnyi_allapotot(self, qt_app):
        """A felhasználó már a fül megnyitása előtt is nyomhatja."""
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider

        vezerlo = EditController(EditPreviewProvider())
        vezerlo.figyeldAShiftet(True)
        try:
            assert vezerlo.shiftAktiv == vezerlo.shiftLenyomva()
        finally:
            vezerlo.figyeldAShiftet(False)


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
        # az effekt-fülre lépve kapcsol be a figyelés (a panel teszi)
        editor_panel.setProperty("activeTab", 2)
        assert editor_panel.property("shiftMasodlagos") is False
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        assert editor_panel.property("shiftMasodlagos") is True, (
            "a panel nem követi a Shift lenyomását — a kilenc csempe "
            "felirata változatlan marad"
        )
        _kuldd(_shift(QKeyEvent.Type.KeyRelease))
        assert editor_panel.property("shiftMasodlagos") is False


class TestVezerloNelkul:
    """A panel vezérlő NÉLKÜL is felépül (#798).

    A CI ezt fogta meg: a csupasz `editController` név a kötésben
    `ReferenceError`-t dobott azoknál a próbáknál, amelyek kontextus-
    tulajdonság nélkül építik fel a panelt — három QML-tesztfájl bukott
    el rá. A `qml_undefined_or.py` átengedte, mert a `!== undefined`
    záradékot őrzésnek látta; a `typeof` viszont hiányzott.
    """

    def test_felepul_kontextus_tulajdonsag_nelkul(self, qt_app):
        from pathlib import Path as Ut

        import picasapy.app
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        qml = Ut(picasapy.app.__file__).parent / "qml"
        motor = QQmlEngine()
        motor.addImportPath(str(qml))
        komponens = QQmlComponent(
            motor, QUrl.fromLocalFile(str(qml / "PicasaPy" / "EditorPanel.qml"))
        )
        panel = komponens.create()
        assert panel is not None, komponens.errorString()
        assert panel.property("shiftMasodlagos") is False
        panel.deleteLater()


class TestAFulValtas:
    """A figyelés a FÜLLEL jár (#798)."""

    def test_a_NEM_effekt_fulon_nem_hat_a_shift(self, editor_panel):
        editor_panel.setProperty("activeTab", 0)
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        try:
            assert editor_panel.property("shiftMasodlagos") is False, (
                "a Finomhangolás fülön is figyelünk — felesleges teher"
            )
        finally:
            _kuldd(_shift(QKeyEvent.Type.KeyRelease))

    def test_MIND_A_NEGY_effekt_fulon_hat(self, editor_panel):
        for ful in (2, 3, 4, 5):
            editor_panel.setProperty("activeTab", ful)
            _kuldd(_shift(QKeyEvent.Type.KeyPress))
            allapot = editor_panel.property("shiftMasodlagos")
            _kuldd(_shift(QKeyEvent.Type.KeyRelease))
            assert allapot is True, f"a(z) {ful}. fülön nem hat a Shift"

    def test_a_fulrol_LELEPVE_visszaall(self, editor_panel):
        editor_panel.setProperty("activeTab", 2)
        _kuldd(_shift(QKeyEvent.Type.KeyPress))
        assert editor_panel.property("shiftMasodlagos") is True
        editor_panel.setProperty("activeTab", 0)
        assert editor_panel.property("shiftMasodlagos") is False, (
            "a csempék Shift-es állapotban ragadtak a fülváltás után"
        )
        _kuldd(_shift(QKeyEvent.Type.KeyRelease))
