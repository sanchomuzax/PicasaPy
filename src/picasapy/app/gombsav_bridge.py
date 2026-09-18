"""#1792: vékony QML-híd a `gombsav_beallitas.py` fölött.

Az album-fejléc (`LightboxHeader.qml`) ezen a `gombsav` context
property-n olvassa ki, mely gombok látszanak és milyen sorrendben; a
„Gombok konfigurálása…" párbeszéd pedig ezen át ment.

A tényleges logika a `gombsav_beallitas.py`-ban él (tesztelhető,
`QSettings`-injektálható); ez a modul csak QML-ből hívható metódusokká
csomagolja — a `ConfirmSettingsBridge` (#367) mintájára.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

from picasapy.app import gombsav_beallitas as logika


class GombsavBridge(QObject):
    """A fejléc gombsorának összeállítása QML felé.

    `settings=None` esetén a valós alkalmazás közös
    `QSettings("PicasaPy", "PicasaPy")`-jét használja (lusta
    létrehozással); tesztekhez injektálható elszigetelt `QSettings`.
    """

    #: A sor megváltozott — a fejléc kötése erre értékelődik újra.
    sorrendChanged = Signal()

    def __init__(self, settings: QSettings | None = None, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._sorrend: list[str] | None = None

    def _get_settings(self) -> QSettings:
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    @Property("QVariantList", notify=sorrendChanged)
    def sorrend(self):
        """A LÁTHATÓ gombok, megjelenítési sorrendben."""
        if self._sorrend is None:
            self._sorrend = logika.betoltsd(self._get_settings())
        return list(self._sorrend)

    @Slot("QVariantList")
    def mentsd(self, sorrend) -> None:
        """A párbeszéd OK-ja. A Mégse egyszerűen nem hívja ezt — a
        szerkesztés a párbeszéd saját másolatán folyik."""
        tiszta = [str(nev) for nev in sorrend]
        logika.mentsd(self._get_settings(), tiszta)
        self._sorrend = logika.betoltsd(self._get_settings())
        self.sorrendChanged.emit()

    @Slot(result="QVariantList")
    def alapertelmezes(self):
        """A „Visszaállítás alapértelmezettre" gomb kimenete — a
        párbeszéd listájába megy, nem a tárolóba: a felhasználó még
        mindig lemondhat róla a Mégsével."""
        return logika.visszaall_alapra()

#: ⛔ Ami SZÁNDÉKOSAN nincs itt: „látszik-e ez a gomb", „hol áll a
#: sorban" és „mi a felirata". Mindhármat a QML számolja a `sorrend`-ből
#: (`LightboxHeader.gombLathato`/`gombX`, `ConfigureButtonsDialog.felirata`)
#: — a feliratot ott is kell, mert `qsTr`-rel fordul. Egy híd-metódus,
#: amit a felület nem hív, halott tag: a `kepesseg_or.py` jelzi is.
