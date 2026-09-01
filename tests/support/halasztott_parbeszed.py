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
    # #1782: a nyomtatás-párbeszéd — a Fájl ▸ Nyomtatás… tétele
    "printDialog": "menuFilePrint",
    # #1719: a fájlműveleti párbeszédek — az „Új album…" menüpont
    # építi fel őket (üres kijelöléssel is, ld. a docstringet)
    "fileOpsDialogs": "menuFileNewAlbum",
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
    """A párbeszéd FELÉPÍTÉSE a menüpontján át, MELLÉKHATÁS NÉLKÜL.

    Sok teszt nem a megnyitást vizsgálja, hanem a párbeszéd belsejében ülő
    elemeket (`saveErrorMessage`, `exportQuality`, …) — azokhoz elég, hogy
    a fa álljon.

    ⚠️ A menüpont nem csak nyit: a `menuFileSave` MENT is. Üres kijelöléssel
    viszont minden belépő azonnal visszatér (`openSave([])`), a `Loader` mégis
    felépül — ezért a hívás idejére kiürítjük a kijelölést, utána
    visszaállítjuk. Enélkül a felépítés egy „lemezhiba" hibaüzenetet hagyott
    a párbeszédben, és a KÖVETKEZŐ teszt állítása bukott el rajta.

    A felépítés útja itt is a valódi menüpont, nem a `Loader.active`."""
    if window.findChild(QObject, parbeszed_neve) is not None:
        return

    kijeloles = window.property("selectedIndexes")
    kijelolt = window.property("selectedIndex")
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    try:
        nyisd_meg(window, parbeszed_neve)
    finally:
        window.setProperty("selectedIndexes", kijeloles)
        window.setProperty("selectedIndex", kijelolt)

    parbeszed = window.findChild(QObject, parbeszed_neve)
    if parbeszed is not None and parbeszed.property("visible"):
        QMetaObject.invokeMethod(
            parbeszed, "close", Qt.ConnectionType.DirectConnection
        )
