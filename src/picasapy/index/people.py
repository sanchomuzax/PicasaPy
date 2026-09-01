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
from dataclasses import dataclass

from picasapy.ini import IniDocument, contacts_of, parse_faces
from picasapy.ini.faces import Face

from .folder_ini import sweep_folder_inis
from .queries import _SELECT, PhotoRecord, _records


@dataclass(frozen=True)
class PersonRecord:
    """Egy személy a bal hasábnak: név + a rá kitaggelt fotók száma."""

    name: str
    photo_count: int


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
) -> tuple[PersonRecord, ...]:
    """A könyvtárban előforduló, NÉVVEL ellátott személyek — NÉV szerint
    rendezve (kis-nagybetű-tűrően), a Picasa-hasáb mintájára.

    Egy fotón belül ugyanaz a név csak egyszer számít (két arc-régió is
    tartozhatna rá, de a darabszám fotókat számol, nem arc-régiókat).

    #1601: a `face_data` a MÁR BEGYŰJTÖTT arc-adat — a hívó így megoszthatja
    az ini-söprést a Projektek gyűjteménnyel (`index/side_pane.py`), és a
    `.picasa.ini`-ket nem kell kétszer végigolvasni. `None` esetén a
    viselkedés változatlan: maga söpör."""
    counts: dict[str, int] = {}
    for _folder_path, names, faces_by_file in (
        _iter_face_data(conn) if face_data is None else face_data
    ):
        for faces in faces_by_file.values():
            seen: set[str] = set()
            for face in faces:
                name = _resolve_name(face, names)
                if name is None or name in seen:
                    continue
                seen.add(name)
                counts[name] = counts.get(name, 0) + 1
    return tuple(
        PersonRecord(name=name, photo_count=count)
        for name, count in sorted(counts.items(), key=lambda kv: kv[0].casefold())
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

    def __call__(self, folder_path: str, document: IniDocument) -> None:
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
