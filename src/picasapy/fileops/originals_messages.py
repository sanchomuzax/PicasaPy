"""A megőrzött eredetik költözésének FIGYELMEZTETŐ szövegei.

A `picasapy.fileops.originals` szétbontott része: az „útban van egy fájl"
üzenet és a visszagörgetés-utáni megnyugtató, illetve figyelmeztető
mondatok. A szövegek változatlanok; a döntésük (mit mondhatunk ki, és
mikor) a `originals_move` és a `originals_plan` dolga.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from picasapy.fileops.originals_names import _snapshot_dir_name

if TYPE_CHECKING:  # csak típushoz, a körkörös futásidejű importot elkerüljük
    from picasapy.fileops.original_ini import IniSectionMove
    from picasapy.fileops.originals_plan import OriginalMove


def _occupied_message(move: OriginalMove) -> str:
    """Az „útban van egy fájl" üzenet - a tanács attól függ, KIÉ az a fájl.

    Az eredeti-mappában lévő fájl lehet egy MÁSIK, élő kép saját megőrzött
    eredetije (a `<név>.<N>` névminta kétértelműsége miatt ez valódi eset).
    Annak a törlését tanácsolni pont azt a kárt okozná, amit ez a modul
    megelőzni hivatott - ezért előbb megnézzük, van-e a képmappában ilyen
    nevű, élő kép.

    MELYIK ÚTON hangzik el: az F2-es átnevezésén, a másolásén és az
    egyfájlos mozgatásén - ahol a nevet a felhasználó adta meg, tehát ő is
    tudja megváltoztatni. A kötegelt áthelyezés az „átnevezés" házirenddel
    pótnevet keres helyette (ld. a modul docstringjét); ott ez az üzenet
    csak akkor szólal meg, ha a hely a pótnév-keresés ÓTA lett foglalt."""
    fej = (
        f"A képhez megőrzött eredeti változatot nem lehet a helyére tenni, mert "
        f"ott "
        f"már van egy azonos nevű fájl: {move.target}. Semmi nem változott: "
        f"a kép és a megőrzött változatai is a régi helyükön maradtak. "
    )
    # #2512: a `.picasapy-snapshots` alkönyvtárba rajtunk kívül SENKI nem ír,
    # tehát az útban lévő fájl ott nem lehet egy másik kép „szent"
    # eredetije - csak egy korábbi költöztetés árva pillanatképe. A
    # gazda-ág tanácsa („ez a(z) X képhez tartozik, NE törölje") itt
    # félrevezető lenne: a szomszédos, azonos nevű kép ehhez a fájlhoz
    # semmilyen viszonyban nincs.
    if move.target.parent.name == _snapshot_dir_name():
        return fej + (
            f"Ez egy korábbi költöztetés árván maradt pillanatképe: a(z) "
            f"„{move.target.parent.name}” mappa kizárólag a PicasaPy saját, "
            f"mentésenkénti másolatait tartalmazza, más kép megőrzött "
            f"eredetije nem kerülhet bele. Ha nincs rá szüksége, törölje "
            f"vagy nevezze át, és próbálja újra."
        )
    kep_mappa = move.target.parent.parent
    gazda = kep_mappa / move.target.name
    if gazda.exists():
        return fej + (
            f"Ez a fájl a(z) {gazda.name} nevű képhez tartozik, annak az "
            f"eredeti változata - NE törölje, mert azzal annak a képnek a "
            f"visszaútját semmisítené meg. Adjon inkább a képnek másik "
            f"nevet, vagy válasszon másik célmappát."
        )
    return fej + (
        f"Ez valószínűleg egy korábbi költöztetés árván maradt fájlja: nincs "
        f"a(z) {kep_mappa} mappában {move.target.name} nevű kép, amihez "
        f"tartozhatna. Ha nincs rá szüksége, törölje vagy nevezze át a(z) "
        f"„{move.target.parent.name}” mappában, és próbálja újra."
    )


def _reassurance() -> str:
    """A megnyugtató zárómondat - KIZÁRÓLAG akkor mondható ki, ha minden
    megőrzött változat a kép mellett maradt."""
    return (
        " A kép nem mozdult el, és a megőrzött változatai is a helyükön "
        "vannak: a „Vissza az eredetihez” továbbra is működik."
    )


def _stranded_warning(stranded: Sequence[OriginalMove]) -> str:
    """A figyelmeztetés, ha a visszatétel IS elbukott. Üres sztring, ha
    minden visszakerült.

    Itt a megnyugtatás HAZUGSÁG lenne, és a kár nem kozmetikai: a
    `find_original_backup` a kép mellett ilyenkor nem talál eredetit, az
    `edit/save.py` pedig `existing_backup is None` mellett a MÁR
    SZERKESZTETT bájtokat írja be új „eredetiként". A megnyugtatott
    felhasználó egyetlen mentéssel véglegesen elveszítené az érintetlen
    változatot - ezért a legfontosabb mondanivaló az, hogy MIT NE tegyen."""
    if not stranded:
        return ""
    helyek = ", ".join(str(move.target) for move in stranded)
    honnan = ", ".join(str(move.source) for move in stranded)
    return (
        f" FIGYELEM: a kép megőrzött változatát nem sikerült a helyére "
        f"visszatenni, itt maradt: {helyek}. Amíg nincs a kép mellett, a "
        f"„Vissza az eredetihez” nem talál semmit, és ha ÚJRA MENTI a képet, "
        f"a program a mostani, szerkesztett állapotot fogja eredetinek "
        f"tekinteni - az érintetlen változat véglegesen elveszne. Ne mentse "
        f"újra a képet, amíg ezt a fájlt kézzel vissza nem másolta ide: "
        f"{honnan}."
    )


def _ini_stranded_warning(stranded: Sequence["IniSectionMove"]) -> str:
    """A figyelmeztetés, ha a MEGŐRZÖTT EREDETI BEÁLLÍTÁSAIT nem sikerült
    visszatenni a régi helyükre. Üres sztring, ha minden visszakerült.

    A fájlokénál enyhébb kár, de ki kell mondani: a beállítások (`filters`,
    `crop`, `rotate`, `moddate`) a célmappa inijében ragadtak, ahol egy
    későbbi, azonos nevű eredeti örökölné őket - és a párhuzamosan futó
    windowsos Picasa is onnan olvasná. A megnyugtató mondat ilyenkor
    HAZUGSÁG lenne (#1448 2. átnézés, 3. lelet)."""
    if not stranded:
        return ""
    helyek = ", ".join(
        f"{move.target_ini} [{move.target_name}]" for move in stranded
    )
    return (
        f" FIGYELEM: a megőrzött eredeti beállításait nem sikerült a régi "
        f"helyükre visszatenni, itt maradtak: {helyek}. A képhez tartozó "
        f"fájlok a helyükön vannak, de ezt a bejegyzést érdemes kézzel "
        f"eltávolítani, mert egy későbbi, azonos nevű megőrzött eredeti "
        f"örökölné a beállításait."
    )
