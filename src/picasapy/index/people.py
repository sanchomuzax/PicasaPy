"""#26: az „Emberek" gyűjtemény — a `faces=` + `[Contacts2]` összesítése.

Nincs önálló SQL-tábla ehhez (a `schema.py` forró fájl — séma-bővítést csak
az integrátor oszthat ki, ld. CONTRIBUTING.md): a névvel ellátott arcok
DIREKT ini-olvasással kerülnek elő, a `queries._album_suggestions` mintáját
követve — a `folders` tábla `has_ini=1` sorain megyünk végig, minden
`.picasa.ini` `[Contacts2]`-jét és a fájlbejegyzések `faces=` kulcsát
feldolgozzuk. Ez minden híváskor újraolvassa az ini-ket (NAS-on drágább,
mint egy indexelt tábla lenne) — nagy könyvtárnál ez a réteg később
séma-bővítéssel (`people`/`photo_people` tábla, az `albums`/`photo_albums`
mintájára) válthatja a mostani, olvasáskor összesítő változatot.

Az összesítés NÉV szerint történik, nem `person_id` szerint: a `[Contacts2]`
„csak lokális" (docs/specs/picasa-ini-format.md) — ugyanaz a személy
különböző mappák ini-jeiben eltérő id-t kaphat, de a nevet a Picasa
egyformán írja ki. Azonosítatlan arc (`ffffffffffffffff` contact_id) nem
számít bele.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini import (
    IniDocument,
    contacts_of,
    load_document,
    parse_faces,
    update_document,
)
from picasapy.ini.faces import Face
from picasapy.ini.person_album_thumbnail import (
    clear_person_album_thumbnail as _clear_thumbnail,
    person_album_thumbnails,
    set_person_album_thumbnail as _set_thumbnail,
)
from picasapy.scanner import PICASA_INI_NAME

from .folder_ini import sweep_folder_inis
from .queries import _SELECT, PhotoRecord, _records


@dataclass(frozen=True)
class PersonRecord:
    """Egy személy a bal hasábnak: név, fotószám és opcionális borítókép."""

    name: str
    photo_count: int
    thumbnail_path: str | None = None


#: Egy mappa arc-adata: (mappa, {person_id.casefold(): név}, {fájlnév: arcok}).
FaceData = tuple[str, dict[str, str], dict[str, tuple[Face, ...]]]


#: A Személyek lista három rendezési módja (#1767). A sorrend az eredeti
#: `Preferences\peoplesort` értékeit követi: 0 = név, 1 = darabszám,
#: 2 = Top 10.
PEOPLE_SORT_MODES = ("name", "count", "top")

#: A „Top 10" mód felső korlátja. Az eredeti FELIRATA mondja ki a tízet
#: (`Sort People by Top &10`); a holtverseny és a „továbbiak" tétel
#: viselkedése NINCS mérve — nálunk a darabszám-sorrend első tíz eleme
#: áll, holtversenynél a névsor dönt (ugyanaz a kulcs, mint a
#: `people_with`-nél). Ez TUDATOS egyszerűsítés, nem mérés.
TOP_LIST_LIMIT = 10


def rendezd_szemelyeket(
    records: "tuple[PersonRecord, ...]", mode: str
) -> "tuple[PersonRecord, ...]":
    """A Személyek lista rendezése (és a `top` módban SZŰRÉSE) — #1767.

    Tiszta függvény: nem nyúl adatbázishoz, nem függ Qt-tól. Ismeretlen
    módra a NÉV szerinti sorrendet adja, ami az eredeti alapértéke is
    (`peoplesort=0`) — hibás beállításból ne legyen üres lista."""
    if mode == "count":
        return _darabszam_szerint(records)
    if mode == "top":
        return _darabszam_szerint(records)[:TOP_LIST_LIMIT]
    return tuple(sorted(records, key=lambda r: r.name.casefold()))


def _darabszam_szerint(
    records: "tuple[PersonRecord, ...]",
) -> "tuple[PersonRecord, ...]":
    """Legtöbb fotó elöl, azonos darabszámnál névsor — ugyanaz a kulcs,
    amit a `people_with` is használ."""
    return tuple(
        sorted(records, key=lambda r: (-r.photo_count, r.name.casefold()))
    )


def people_in_index(
    conn: sqlite3.Connection,
    face_data: tuple[FaceData, ...] | None = None,
    thumbnail_paths: dict[str, str] | None = None,
) -> tuple[PersonRecord, ...]:
    """A könyvtárban előforduló, NÉVVEL ellátott személyek — NÉV szerint
    rendezve (kis-nagybetű-tűrően), a Picasa-hasáb mintájára.

    Egy fotón belül ugyanaz a név csak egyszer számít (két arc-régió is
    tartozhatna rá, de a darabszám fotókat számol, nem arc-régiókat).

    #1601: a `face_data` a MÁR BEGYŰJTÖTT arc-adat — a hívó így megoszthatja
    az ini-söprést a Projektek gyűjteménnyel (`index/side_pane.py`), és a
    `.picasa.ini`-ket nem kell kétszer végigolvasni. `None` esetén a
    viselkedés változatlan: maga söpör."""
    if face_data is None:
        collector = FaceDataCollector()
        sweep_folder_inis(conn, (collector,))
        face_data = tuple(collector.rows)
        if thumbnail_paths is None:
            thumbnail_paths = collector.thumbnail_paths
    counts: dict[str, int] = {}
    for _folder_path, names, faces_by_file in face_data:
        for faces in faces_by_file.values():
            seen: set[str] = set()
            for face in faces:
                name = _resolve_name(face, names)
                if name is None or name in seen:
                    continue
                seen.add(name)
                counts[name] = counts.get(name, 0) + 1
    return tuple(
        PersonRecord(
            name=name,
            photo_count=count,
            thumbnail_path=(thumbnail_paths or {}).get(name.casefold()),
        )
        for name, count in sorted(counts.items(), key=lambda kv: kv[0].casefold())
    )


def set_person_album_thumbnail(
    conn: sqlite3.Connection,
    person_name: str,
    photo_path: str,
    previous_photo_path: str | None,
) -> None:
    """A személy borítóját a kiválasztott fotó mappájában tárolja.

    A korábban megjelenített borítót a hívó adja át; így a régi bejegyzés
    törléséhez legfeljebb egy másik ini-t kell megnyitni, nem kell az egész
    könyvtárat újra végigsöpörni. Minden módosítás az `update_document`
    konfliktusvédett ini-API-ján megy át.
    """
    if not isinstance(person_name, str) or not person_name.strip():
        raise ValueError("A személy neve nem lehet üres.")
    if not isinstance(photo_path, str) or not photo_path:
        raise ValueError("A borítókép útvonala nem lehet üres.")
    selected = Path(photo_path)
    if not selected.is_absolute() or not selected.name or not selected.is_file():
        raise ValueError("A borítóképnek létező, indexelt fotónak kell lennie.")

    photo = conn.execute(
        """SELECT f.path AS folder_path, p.name
           FROM photos p JOIN folders f ON f.id = p.folder_id
           WHERE f.path = ? COLLATE NOCASE AND p.name = ? COLLATE NOCASE
           LIMIT 1""",
        (str(selected.parent), selected.name),
    ).fetchone()
    if photo is None:
        raise ValueError("A borítókép nincs a könyvtár indexében.")

    target_ini = Path(photo["folder_path"]) / PICASA_INI_NAME
    if previous_photo_path:
        previous_ini = Path(previous_photo_path).parent / PICASA_INI_NAME
        if previous_ini != target_ini and previous_ini.is_file():
            document = load_document(previous_ini)
            if person_name.casefold() in person_album_thumbnails(document):
                update_document(
                    previous_ini,
                    lambda current: _clear_thumbnail(current, person_name),
                    backup=True,
                )

    update_document(
        target_ini,
        lambda current: _set_thumbnail(current, person_name, photo["name"]),
        backup=True,
    )


def people_with(conn: sqlite3.Connection, name: str) -> tuple[PersonRecord, ...]:
    """Akik EGYÜTT szerepelnek a megadott személlyel — közös fotók száma
    szerint csökkenően, azonos darabszámnál név szerint.

    Az eredeti Picasa Emberek-panelének negyedik állapota: *„Named People
    who appear WITH the currently selected person will be listed here."*
    Ez a családi/baráti gyűjtemények természetes navigációja — „ki van még
    rajta ezeken a képeken?" —, és onnan egy kattintással át a másik
    személy albumába.

    A keresett személy MAGA nincs benne a listában. Üres/ismeretlen névre
    üres eredmény (nem hiba), a `person_photos` mintáját követve.
    """
    if not name:
        return ()
    counts: dict[str, int] = {}
    for _folder_path, names, faces_by_file in _iter_face_data(conn):
        for faces in faces_by_file.values():
            on_photo = {
                resolved
                for resolved in (_resolve_name(face, names) for face in faces)
                if resolved is not None
            }
            if name not in on_photo:
                continue
            for other in on_photo - {name}:
                counts[other] = counts.get(other, 0) + 1
    return tuple(
        PersonRecord(name=other, photo_count=count)
        for other, count in sorted(
            counts.items(), key=lambda kv: (-kv[1], kv[0].casefold())
        )
    )


def person_photos(conn: sqlite3.Connection, name: str) -> tuple[PhotoRecord, ...]:
    """Egy megnevezett személyre kitaggelt fotók — a `album_photos` mintáját
    követő szűrt nézet. Ismeretlen/üres név esetén üres eredmény (nem hiba)."""
    if not name:
        return ()
    pairs: list[tuple[str, str]] = []
    for folder_path, names, faces_by_file in _iter_face_data(conn):
        for filename, faces in faces_by_file.items():
            if any(_resolve_name(face, names) == name for face in faces):
                pairs.append((folder_path, filename))
    if not pairs:
        return ()
    clause = " OR ".join(["(f.path = ? AND p.name = ? COLLATE NOCASE)"] * len(pairs))
    params = [value for pair in pairs for value in pair]
    rows = conn.execute(
        f"{_SELECT} WHERE {clause} ORDER BY f.path, p.name", params
    )
    return _records(rows)


def person_movie_photos(
    conn: sqlite3.Connection,
    albums: Sequence[PersonRecord | str],
) -> tuple[PhotoRecord, ...]:
    """A személyalbum-lista nem üres képeit fűzi össze, sorrendtartóan.

    Az albumok sorrendje a hívó által átadott lista; itt nem rendezünk. Egy
    üres alsó kép-lista kimarad, a képek sorrendjét ugyanaz az index-lekérdezés
    adja, amit a `person_photos` is használ.
    """
    album_names = tuple(
        album.name if isinstance(album, PersonRecord) else str(album)
        for album in albums
    )
    if not album_names:
        return ()

    wanted = set(album_names)
    pairs_by_person: dict[str, list[tuple[str, str]]] = {
        name: [] for name in wanted
    }
    for folder_path, names, faces_by_file in _iter_face_data(conn):
        for filename, faces in faces_by_file.items():
            on_photo: set[str] = set()
            for face in faces:
                name = _resolve_name(face, names)
                if name in wanted:
                    on_photo.add(name)
            for name in on_photo:
                pairs_by_person[name].append((folder_path, filename))

    result: list[PhotoRecord] = []
    for name in album_names:
        pairs = pairs_by_person.get(name, [])
        if not pairs:
            continue
        clause = " OR ".join(
            ["(f.path = ? AND p.name = ? COLLATE NOCASE)"] * len(pairs)
        )
        params = [value for pair in pairs for value in pair]
        rows = conn.execute(
            f"{_SELECT} WHERE {clause} ORDER BY f.path, p.name", params
        )
        result.extend(_records(rows))
    return tuple(result)


def photos_with_faces(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """Minden fotó, amin VAN bejelölt arc (#1830) — az eredeti `facesearch`
    szűrője.

    ⚠️ A **megnevezetlen** arc is arc: ez a szűrő nem arra válaszol, hogy
    kit ismerünk fel, hanem arra, hogy van-e a képen bejelölt arc. Ebben
    tér el a `person_photos`-tól, ami nevet egyeztet.

    A MEGLÉVŐ `.picasa.ini` `faces=` adatára épül — ugyanazon a söprésen,
    amiből az „Emberek" gyűjtemény is él —, tehát **nem igényel
    arcfelismerést** (a `face` tábla az `index/faces_detected.py` motorjáé,
    az üres lehet). Rendezés: mappa, majd név — mint a csillag- és a
    film-szűrőnél."""
    parok: list[tuple[str, str]] = []
    for folder_path, _names, faces_by_file in _iter_face_data(conn):
        for filename, faces in faces_by_file.items():
            if faces:
                parok.append((folder_path, filename))
    if not parok:
        return ()
    clause = " OR ".join(["(f.path = ? AND p.name = ? COLLATE NOCASE)"] * len(parok))
    params = [value for pair in parok for value in pair]
    rows = conn.execute(
        f"{_SELECT} WHERE {clause} ORDER BY f.path, p.name", params
    )
    return _records(rows)


def _resolve_name(face: Face, names: dict[str, str]) -> str | None:
    if not face.is_identified:
        return None
    return names.get(face.contact_id.casefold())


class FaceDataCollector:
    """#1601: a `sweep_folder_inis` fogyasztója az Emberek-gyűjteményhez.

    Külön osztály, mert a söprést MEGOSZTJUK a Projektek gyűjteménnyel
    (`index/side_pane.py`): a `.picasa.ini`-t így mappánként egyszer
    olvassuk, nem kétszer. A törzse változatlanul a korábbi
    `_iter_face_data` ciklusmagja."""

    def __init__(self) -> None:
        self.rows: list[FaceData] = []
        self.thumbnail_paths: dict[str, str] = {}

    def __call__(self, folder_path: str, document: IniDocument) -> None:
        for person_name, photo_name in person_album_thumbnails(document).items():
            photo_path = Path(folder_path) / photo_name
            if not photo_path.is_file():
                continue
            key = person_name.casefold()
            candidate = str(photo_path)
            previous = self.thumbnail_paths.get(key)
            if previous is None or candidate.casefold() < previous.casefold():
                self.thumbnail_paths[key] = candidate

        names = {
            contact.person_id.casefold(): contact.name
            for contact in contacts_of(document)
            if contact.name
        }
        if not names:
            return
        faces_by_file: dict[str, tuple[Face, ...]] = {}
        for section in document.file_sections():
            raw_faces = section.get("faces")
            if not raw_faces:
                continue
            try:
                faces = parse_faces(raw_faces)
            except ValueError:
                continue
            faces_by_file[section.name] = faces
        if faces_by_file:
            self.rows.append((folder_path, names, faces_by_file))


def _iter_face_data(
    conn: sqlite3.Connection,
) -> tuple[FaceData, ...]:
    """(mappa, {person_id.casefold(): név}, {fájlnév: arcok}) hármasok a
    `has_ini=1` mappákra — olvashatatlan/hibás ini-t csendben kihagy (a
    könyvtár másik folyamat általi éppen-írása ne omlassza össze a listát)."""
    collector = FaceDataCollector()
    sweep_folder_inis(conn, (collector,))
    return tuple(collector.rows)
