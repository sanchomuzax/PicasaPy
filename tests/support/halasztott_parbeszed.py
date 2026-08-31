"""#1720: halasztott párbeszédek megnyitása a VALÓDI menüponton át.

**Miért kell.** A #1720 óta a ritkán használt párbeszédek (Mappakezelő,
Duplikátum-kereső, Beállítások, …) `DeferredDialog`-ba (`Loader`,
`active: false`) kerültek: induláskor NEM épülnek fel, ezért a
`window.findChild(...)` sem találja meg őket, amíg meg nem nyíltak. Ez a
#1720 nyeresége, nem hiba.

**Miért menüponttal.** A `Loader.active = true` közvetlen beállítása
zölden hazudna: a párbeszéd létrejönne akkor is, ha a menüpont bekötése
elromlott. A projekt visszatérő kára pontosan ez volt (MEMORY: „a
vezérlőre KATTINTS, ne a metódust hívd"), ezért itt a menüpont
`triggered` jelzését váltjuk ki — ugyanazt az utat, amit a felhasználó
bejár.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt

#: párbeszéd `objectName` → az őt megnyitó menüpont `objectName`-je
MENUPONT = {
    "folderManagerDialog": "menuFileAddFolder",
    "dedupDialog": "menuToolsDedup",
    "importSourceDialog": "menuFileImportFrom",
    "saveDialogs": "menuFileSave",
    "exportDialog": "menuFileExport",
}


def nyisd_meg(window, parbeszed_neve: str) -> None:
    """A megnevezett halasztott párbeszéd megnyitása a menüpontjával.

    Ha a párbeszéd már létezik, nem csinál semmit."""
    if window.findChild(QObject, parbeszed_neve) is not None:
        return
    menupont_neve = MENUPONT[parbeszed_neve]
    menupont = window.findChild(QObject, menupont_neve)
    assert menupont is not None, f"{menupont_neve} nem található"
    QMetaObject.invokeMethod(
        menupont, "triggered", Qt.ConnectionType.DirectConnection
    )


def epitsd_fel(window, parbeszed_neve: str) -> None:
    """A párbeszéd FELÉPÍTÉSE a menüpontján át, majd azonnali bezárás.

    Sok teszt nem magát a megnyitást vizsgálja, hanem a párbeszéd
    belsejében ülő elemeket (`findChild`) — azokhoz elég, hogy a fa
    álljon. A `nyisd_meg` viszont MEG IS NYITJA a párbeszédet, ami
    átállítaná a kiinduló állapotot; ez a változat ezért utána becsukja.

    A felépítés útja itt is a valódi menüpont, nem a `Loader.active`."""
    if window.findChild(QObject, parbeszed_neve) is not None:
        return
    nyisd_meg(window, parbeszed_neve)
    parbeszed = window.findChild(QObject, parbeszed_neve)
    if parbeszed is not None and parbeszed.property("visible"):
        QMetaObject.invokeMethod(
            parbeszed, "close", Qt.ConnectionType.DirectConnection
        )
