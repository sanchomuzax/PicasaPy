"""A bal hasáb gyűjtemény-szintje (#320).

Az eredeti Picasa bal hasábján a fa gyökerén nem mappák, hanem
**gyűjtemények** állnak — mindegyik saját, csukható fejléccel (zöld ▼ /
piros ▶ háromszög), és csak a „Mappák" gyűjtemény tagolt évszám-szakaszokra.

Ez a modul csak a gyűjtemények KATALÓGUSA és a csukott állapot beállítás-
kulcsa; a tartalom feltöltése gyűjteményenként külön munka (az Emberek a 3.
fázisé, a Projektek/Egyebek forrása még kutatás alatt — ld. #320).
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

#: Alapállapot: a napi munka helye (Mappák) és a csillagozottat hordozó
#: Albumok nyitva; a még tartalom nélküli gyűjtemények csukva, hogy ne
#: foglalják a helyet a fától.
DEFAULT_COLLAPSED: dict[str, bool] = {
    "albums": False,
    "people": True,
    "projects": True,
    "folders": False,
    "other": True,
}


def collection_setting_key(name: str) -> str:
    """A gyűjtemény csukott állapotának QSettings-kulcsa."""
    return f"view/collection/{name}/collapsed"
