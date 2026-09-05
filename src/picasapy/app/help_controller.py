"""A felhasználói súgó felületi vezérlője (#2054).

A tartalmat a `picasapy.help_content` adja (csomagfa alól, net nélkül);
ez a szelet csak **kiteszi a QML-nek**. Formázni nem formáz: a nyers
Markdown megy át, a megjelenítés a felület dolga.

## Miért mixin

Ugyanaz a felállás, mint a többi szeleté (`CreateMixin`, `ExportMixin`,
…): az `AppController`-be keverve egyetlen `controller` objektumon át
érhető el a QML-ből. A `tr()` futásidejű kontextusa emiatt az
`AppController` — új hibaszövegnél ezt a
`tests/app/test_i18n_completeness.py` átfordító táblájába is fel kell
venni.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from ..help_content import (
    FOOLDAL,
    fejezet_szovege,
    fejezetek,
    hivatkozas_celja,
    kereses,
)


class HelpMixin(QObject):
    """A súgó fejezetei, egy fejezet szövege és a keresés."""

    #: A #1743 őre miatt kell: jelzés nélküli `Property` a QML-ben nem
    #: köthető. A súgó tartalma futás közben nem változik, de a
    #: tulajdonságnak akkor is kell értesítője.
    helpChanged = Signal()

    @Property(str, constant=True)
    def helpHomeTopic(self) -> str:
        """A főoldal fejezetneve — az F1 ezt nyitja meg."""
        return FOOLDAL

    @Property("QVariantList", notify=helpChanged)
    def helpTopics(self) -> list[dict[str, str]]:
        """A fejezetek listája: `{nev, cim}`, a főoldallal elöl.

        A `cim` a fejezet első címsora — a fájlnév (`features/kollazs.md`)
        önmagában nem olvasható a felhasználónak.
        """
        tetelek = []
        for nev in fejezetek():
            szoveg = fejezet_szovege(nev) or ""
            cim = next(
                (s[2:].strip() for s in szoveg.splitlines() if s.startswith("# ")),
                nev,
            )
            tetelek.append({"nev": nev, "cim": cim})
        return tetelek

    @Slot(str, result=str)
    def helpTopicText(self, nev: str) -> str:
        """Egy fejezet nyers Markdown-szövege; ismeretlen névre üres.

        Üres szöveget adunk vissza, nem hibát: a súgó megnyitása sosem
        buktathatja el a programot, és a néző a főoldalra tud esni.
        """
        return fejezet_szovege(nev) or ""

    @Slot(str, str, result=str)
    def helpResolveLink(self, honnan: str, cel: str) -> str:
        """Egy Markdown-hivatkozás célja fejezetnévként; üres, ha nem az.

        A nyitólap a súgó tartalomjegyzéke — csupa relatív hivatkozás —,
        ezért a feloldás a HIVATKOZÓ fejezethez képest történik. Üres
        választ adunk vissza (nem hibát) minden olyan célra, ami külső,
        nem létezik, vagy kilépne a súgó mappájából: a felület ilyenkor
        egyszerűen nem lép sehova (#2212).
        """
        return hivatkozas_celja(honnan, cel) or ""

    @Slot(str, result="QVariantList")
    def helpSearch(self, kifejezes: str) -> list[dict[str, str]]:
        """Szöveges keresés; találatonként `{fejezet, cim, reszlet}`."""
        return kereses(kifejezes)


__all__ = ["HelpMixin"]
