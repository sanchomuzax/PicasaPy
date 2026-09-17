"""Az adatbázis-költözés CÉLJÁNAK alkalmassága (#1402, #3214).

Két helyen kell ugyanaz az ítélet, ezért él külön modulban:

* a párbeszéd a szándék rögzítése előtt kérdez (`relocate_controller`) —
  a mért eredeti is a művelet ELŐTT ellenőriz, és elutasításnál semmihez
  nem nyúl („No changes will be made");
* az indulás a költözés előtt ÚJRA kérdez (`startup_relocate`) — a
  szándék rögzítése óta eltelhetett idő, és a cél időközben megtelhetett
  vagy lecsatolódhatott.

A modul SZÁNDÉKOSAN nem fogalmaz üzenetet: a felületi szöveg a
párbeszédben fordítható (`self.tr`), az indulásnál viszont még nincs
felület. Ezért jelképes okot ad vissza, a szöveget a hívó adja hozzá.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

#: a megadott út létezik, de nem mappa
AKADALY_NEM_MAPPA = "nem_mappa"
#: létező, de NEM ÜRES mappa — az eredeti is ezt kéri számon
AKADALY_NEM_URES = "nem_ures"
#: pozitívan hálózatiként felismert tároló
AKADALY_HALOZATI = "halozati"
#: a cél a JELENLEGI adatok mappáján belül van — a mag sem engedi
AKADALY_FORRASON_BELUL = "forrason_belul"


def cel_akadalya(
    new_root: Path, forrasok: Iterable[Path] = ()
) -> str | None:
    """Mi teszi alkalmatlanná a célt — `None`, ha alkalmas.

    A NEM létező mappa rendben van: azt a költöztető mag hozza létre.

    ⚠️ A modul SEMMIT nem hoz létre és nem próbál ki írással. A mag
    `validate_destination`-je viszont **létrehozza** a célt (írás-próbához)
    — ezért NEM hívjuk a szándék rögzítése előtt: a felhasználó
    visszavonhatja az előjegyzést, és nem maradhat utána üres mappa.
    `forrasok`: a jelenlegi adatok mappái, amelyeken belülre nem lehet
    költözni.

    ⚠️ SZŰKÍTVE, szándékosan: az eredeti „írható HELYI merevlemez"-t kér,
    mi viszont csak azt utasítjuk el, amit POZITÍVAN hálózati meghajtóként
    ismerünk fel. Ok: a `tarolo_tipusa` bármilyen hibára „ismeretlen"-t ad,
    és egy téves elutasítás rosszabb, mint egy átengedett cserélhető lemez
    — a felhasználó a saját gépén nem tud megkerülni egy magabiztosan
    hibás tiltást.
    """
    from picasapy.perf.tesztuzem import TAROLO_HALOZATI, tarolo_tipusa

    new_root = Path(new_root)
    feloldott = new_root.resolve()
    for forras in forrasok:
        feloldott_forras = Path(forras).resolve()
        if feloldott == feloldott_forras or feloldott.is_relative_to(
            feloldott_forras
        ):
            return AKADALY_FORRASON_BELUL
    if new_root.exists() and not new_root.is_dir():
        return AKADALY_NEM_MAPPA
    if new_root.is_dir() and any(new_root.iterdir()):
        return AKADALY_NEM_URES
    # A típust a LÉTEZŐ legközelebbi szülőre kérdezzük: egy még létre nem
    # hozott mappának nincs mountja.
    letezo = new_root
    while not letezo.exists() and letezo.parent != letezo:
        letezo = letezo.parent
    if tarolo_tipusa(letezo) == TAROLO_HALOZATI:
        return AKADALY_HALOZATI
    return None
