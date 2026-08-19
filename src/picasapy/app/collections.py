"""A bal hasáb gyűjtemény-szintje (#320).

Az eredeti Picasa bal hasábján a fa gyökerén nem mappák, hanem
**gyűjtemények** állnak — mindegyik saját, csukható fejléccel (zöld ▼ /
piros ▶ háromszög), és csak a „Mappák" gyűjtemény tagolt évszám-szakaszokra.

Ez a modul csak a gyűjtemények KATALÓGUSA és a csukott állapot beállítás-
kulcsa; a tartalom feltöltése gyűjteményenként külön modulban él:

* Albumok — `.picasa.ini` `[.album:token]` (`picasapy.index.albums`, #9);
* Emberek — `faces=` + `[Contacts2]` (`picasapy.index.people`, #26);
* **Projektek — `[Picasa]` `P2category=Projects (internal)`**
  (`picasapy.index.project_folders`, #1029) + az „Exportált képek"
  csomópont (`exported_folders.py`, #457);
* Mappák — az indexelt mappák (`models.FolderListModel`).

Az Egyebek gyűjtemény forrása (`P2category=Other Stuff`, a korpuszban 3
mappa) még nincs bekötve. A korábbi „a Projektek forrása kutatás alatt —
ld. #320" megjegyzés ELAVULT: a #320 lezárult anélkül, hogy megválaszolta
volna, a választ a #1029 mérte ki a valódi ini-korpuszból.
"""

from __future__ import annotations

#: A Picasa öt gyűjteménye, a hasábon látható sorrendben.
COLLECTIONS: tuple[str, ...] = (
    "albums",
    "people",
    "projects",
    "folders",
    "other",
)

#: Alapállapot: a napi munka helye (Mappák), a csillagozottat hordozó
#: Albumok és a Projektek nyitva; a még tartalom nélküli gyűjtemények
#: csukva, hogy ne foglalják a helyet a fától.
#:
#: #1029: a Projektek KINYITVA indul. Korábban csukva volt, mert nem volt
#: mit mutatnia — mostantól a `P2category=Projects (internal)` mappák
#: (Kollázsok, Filmek, …) benne állnak, és az eredeti Picasa is nyitva
#: mutatja őket. Csukott alapállapottal a felhasználó a javítás után is
#: ÜRESNEK látná a gyűjteményt, amíg rá nem kattint a fejlécre.
DEFAULT_COLLAPSED: dict[str, bool] = {
    "albums": False,
    "people": True,
    "projects": False,
    "folders": False,
    "other": True,
}


def collection_setting_key(name: str) -> str:
    """A gyűjtemény csukott állapotának QSettings-kulcsa."""
    return f"view/collection/{name}/collapsed"
