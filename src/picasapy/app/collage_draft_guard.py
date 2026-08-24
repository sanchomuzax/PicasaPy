"""A PISZKOZAT megosztás- és nyomtatás-tilalma (#1072).

## Miért van, és miért NEM a mi döntésünk

A `projectutils::draft_collage` erőforrás-szöveg kimondja:

> „Ez a kollázs még nem készült el teljesen. A kollázs befejezéséhez (ami a
> megosztás és a nyomtatás feltétele) kattintson a »Létrehozás« gombra.
> Megjegyzendő, hogy később bármikor módosíthatja a kollázst, akár még a
> mentése után is."

A zárójeles közbevetés **feltételt** mond, nem tanácsot: a piszkozat nem
osztható meg és nem nyomtatható. A spec ezt normatívaként rögzíti
(`docs/specs/kollazs-eletciklus.md` 4.2).

## Miért külön, apró `QObject`

A szöveget KÉT hívó mutatja (`print_controller`, `email_controller`), és a
Qt fordítás-kontextusa az `self.tr()`-t hívó OSZTÁLY neve. Ha mindkét
vezérlőbe bemásolnánk a bekezdést, két külön `.ts`-bejegyzés keletkezne
ugyanarra a szövegre — és a következő javításnál az egyik némán
elmaradna. Így egyetlen kontextus (`CollageDraftGuard`) van, egyetlen
fordítással.

A felismerést a `picasapy.collage.draft_state` végzi (tiszta útvonal-
kérdés, Qt nélkül) — ez az osztály csak a SZÖVEGET és a kijelölésre
alkalmazást adja hozzá.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QObject

from picasapy.collage.draft_state import is_draft_image


class CollageDraftGuard(QObject):
    """A piszkozat-tilalom szövege és a kijelölésre alkalmazása."""

    def restriction_message(self) -> str:
        """A `projectutils::draft_collage` szövege, SZÓ SZERINT.

        Nem a mi fogalmazásunk és nem is rövidíthető: a felhasználónak
        pontosan azt kell látnia, amit az eredeti Picasa mutat, beleértve
        azt is, hogy a befejezés NEM végleges."""
        return self.tr(
            "This collage was not completed. To finalize this collage "
            '(required for sharing or printing), please select the "Create '
            'Now" button. Please note that you can always change your '
            "collage later, even after it has been saved."
        )

    def first_draft(self, paths: Iterable[Path | str]) -> Path | None:
        """Az ELSŐ piszkozat a felsorolásban, vagy `None`.

        A művelet egészét tiltjuk, nem szűrjük a listát: egy vegyes
        kijelölésből a piszkozatot csendben kihagyni azt jelentené, hogy a
        felhasználó nem tudja meg, miért maradt el egy kép."""
        for path in paths:
            if is_draft_image(path):
                return Path(str(path))
        return None


__all__ = ["CollageDraftGuard"]
