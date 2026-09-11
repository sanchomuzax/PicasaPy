"""A kártyatörlés ÖSSZEÁLLÍTOTT figyelmeztetése (#860).

Az eredeti Picasa nem egyetlen mondatot ad a „minden fájl törlése a
forrásról" választásra, hanem **darabokból fűzi össze** a szöveget, aszerint,
hogy mit tud a kártyáról. A darabok a `CAcquireUI::WipeCard*` erőforrások
(`docs/specs/picasa-importalas.md`), és ez a modul ugyanazokat, ugyanabban a
sorrendben állítja össze:

1. bevezető (FIGYELMEZTETÉS + mit választott a felhasználó),
2. hány fájlt törlünk — vagy hogy a szám még nem ismert,
3. amit nem importálunk (másodpéldányok),
4. amit a program nem ismer fel,
5. záró kérdés + „A MŰVELET NEM VONHATÓ VISSZA."

⚠️ **A magyar szövegek MÉRTEK** (a Picasa magyar erőforrás-készletéből, szó
szerint, a `.ts`-ben). Az angol forrás-alak viszont a MI szövegünk: az angol
erőforrás-készlet nincs kinyerve, tehát azt nem állítjuk mérésnek. A
felhasználó a magyart látja.

⚠️ A fordítás **kimondott kontextussal** megy
(`QCoreApplication.translate("ImportSourceController", …)`, az
`edit_action_names.py` mintája): a szöveget nem a hívó osztálya adja, tehát a
`self.tr()` statikus elemzése nem tudná levezetni a futásidejű kontextust. A
kontextus és a szöveg **minden hívásban literál** — burkolón keresztül a
`lupdate` nem látná, és a fordítás-őr joggal hiányolná a fordítást.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QCoreApplication


@dataclass(frozen=True)
class WipeCardFacts:
    """Amit a kártyáról tudunk a figyelmeztetés megírásakor.

    `scan_done`: lefutott-e a pásztázás. Ha nem, a darabszámot NEM
    találgatjuk — az eredetinek külön erőforrása van erre az esetre
    (`WipeCardScanNotDone`), és ez a helyes: a hamis szám rosszabb, mint a
    bevallott bizonytalanság."""

    scan_done: bool = False
    #: ennyi fájl kerül törlésre (a teljes forrás-tartalom)
    total: int = 0
    #: ebből ennyi NEM lesz importálva, mert már másodpéldány
    duplicates: int = 0
    #: ebből ennyit nem ismer fel a program (nem kép és nem film)
    unrecognized: int = 0


def wipe_card_warning(facts: WipeCardFacts) -> str:
    """A teljes, összeállított figyelmeztetés-szöveg.

    Fordítás nélküli környezetben (próbák) az angol forrás-alak jön vissza."""
    reszek: list[str] = [
        QCoreApplication.translate(
            "ImportSourceController",
            "WARNING\n\nYou have chosen to delete ALL FILES from the source "
            "media.\n\n",
        )
    ]

    if facts.scan_done:
        reszek.append(
            QCoreApplication.translate(
                "ImportSourceController",
                "After importing, %1 file(s) will be deleted.\n",
            ).replace("%1", str(max(0, int(facts.total))))
        )
    else:
        #: `WipeCardScanNotDone` — a szám még nem ismert
        reszek.append(
            QCoreApplication.translate(
                "ImportSourceController",
                "An unknown number of files will be deleted after importing.\n",
            )
        )

    if facts.duplicates == 1:
        #: `WipeCardSingleDupe`
        reszek.append(
            QCoreApplication.translate(
                "ImportSourceController",
                "1 file will not be imported because it is already a "
                "duplicate in Picasa.\n",
            )
        )
    elif facts.duplicates > 1:
        #: `WipeCardMultiDupes`
        reszek.append(
            QCoreApplication.translate(
                "ImportSourceController",
                "%1 files will not be imported because they are already "
                "duplicates in Picasa.\n",
            ).replace("%1", str(int(facts.duplicates)))
        )

    if facts.unrecognized == 1:
        #: `WipeCard1OtherFile`
        reszek.append(
            QCoreApplication.translate(
                "ImportSourceController",
                "\nPicasa does not recognize 1 of the files to be deleted.\n",
            )
        )
    elif facts.unrecognized > 1:
        #: `WipeCardOtherFiles`
        reszek.append(
            QCoreApplication.translate(
                "ImportSourceController",
                "\nPicasa does not recognize %1 of the files to be deleted.\n",
            ).replace("%1", str(int(facts.unrecognized)))
        )

    #: `WipeCardFinalWarning` — a ZÁRÓ mondat MINDIG kimegy
    reszek.append(
        QCoreApplication.translate(
            "ImportSourceController",
            "\nAre you sure you want to remove ALL FILES?\n\nTHIS CANNOT BE "
            "UNDONE.\n",
        )
    )
    return "".join(reszek)
