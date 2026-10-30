"""Az észlelt arcok albumaihoz és állapotaihoz tartozó lekérdezések."""


from __future__ import annotations


import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .hidden_scope import visible_folder_sql
from .queries import PhotoRecord, _records, _select


@dataclass(frozen=True)
class UnnamedFace:
    """Egy MÉG NÉVTELEN, detektált arc — a „Névtelenek" album csoportosított
    megjelenítéséhez (issue #26, 3. lépcső: bekötés). `rect` a relatív
    (rect64-stílusú, [0..1]) keret — a meglévő `FacesHelper.addFace()` úton
    íráshoz kell EBBEN a formátumban, ld. `app/faces_helper.py`. `None`, ha a
    fotó szélessége/magassága ismeretlen az indexben (ritka, hiányos
    indexelés) — ilyenkor a hívó a nevet nem tudja megírni, ezért ezeket a
    csoportosított listákból kihagyjuk (ld. `FaceScanController`)."""

    id: int
    photo_id: int
    photo_path: Path
    group_id: int | None
    rect: tuple[float, float, float, float] | None
    #: #26 (4. lépcső): a MÉG EL NEM DÖNTÖTT név-javaslat, ha van. Az
    #: eredeti kérdésként vetette fel („Anna?"), pipa/x gombbal — a
    #: javaslat nem döntés, az arc állapota `'unnamed'` marad.
    suggested_name: str | None = None
    #: #3670: az arc állapota (`'unnamed'`/`'named'`/`'ignored'`) — a
    #: `faces_for_photo` állapottól függetlenül ad vissza, és a mellőzés
    #: átvétele csak a még névtelen arcot fordíthatja át
    state: str | None = None


def unnamed_faces(conn: sqlite3.Connection) -> tuple[UnnamedFace, ...]:
    """Minden `state = 'unnamed'` arc — csoport szerint rendezve (a
    csoportosítatlanok, `group_id IS NULL`, a végén), majd `id` szerint
    (determinisztikus). A már névvel ellátott (`state != 'unnamed'`) arcokat
    ez a lekérdezés SOSEM adja vissza — az alapszabály (a Picasa döntései
    szentek) itt is szerkezeti kizárás, a `group_unnamed_faces` mintájára."""
    return _faces_where(conn, "WHERE f.state = ?", ("unnamed",))


def unnamed_faces_for_photos(
    conn: sqlite3.Connection, photo_ids: Iterable[int]
) -> tuple[UnnamedFace, ...]:
    """A kiválasztott fotók még névtelen arcai egy kötegben.

    A panel kijelölésenként hívja; az `IN`-lista több kisebb részre oszlik,
    hogy nagy kijelölésnél se lépje át az SQLite paraméterkorlátját.
    `rect is None` maradhat a hiányos képméretű rekordnál — a felület ezt
    kihagyja, mert kivágott bélyegképet nem lehet hozzá készíteni.
    """
    ids = tuple(dict.fromkeys(int(photo_id) for photo_id in photo_ids))
    if not ids:
        return ()

    faces: list[UnnamedFace] = []
    # Az SQLite régebbi buildjeinek 999 kötött változója is elég legyen.
    for start in range(0, len(ids), 900):
        chunk = ids[start : start + 900]
        placeholders = ",".join("?" for _ in chunk)
        faces.extend(
            _faces_where(
                conn,
                f"WHERE f.state = ? AND f.photo_id IN ({placeholders})",
                ("unnamed", *chunk),
            )
        )
    return tuple(faces)


def _faces_in_state(conn: sqlite3.Connection, state: str) -> tuple[UnnamedFace, ...]:
    """A közös test: egy adott állapotú arcok kiolvasása. A `state`
    ÉRTÉKKÉNT (paraméterként) megy be, nem szövegbe fűzve."""
    return _faces_where(conn, "WHERE f.state = ?", (state,))


def faces_for_photo(conn: sqlite3.Connection, photo_id: int) -> tuple[UnnamedFace, ...]:
    """A `photo_id` fotóhoz tartozó ÖSSZES saját arc-találat, ÁLLAPOTTÓL
    FÜGGETLENÜL (#3670) — a `_run_scan` ezzel dönti el egy friss detektálás
    UTÁN, melyik ÚJ találat esik egybe egy már a `.picasa.ini`-ben
    mellőzöttként (`faces=…,ffffffffffffffff`) jelölt régióval, hogy azt ne
    dobja vissza javaslatként."""
    # #4887: belső szkennelési út (nem megjelenítés) — a rejtett mappa
    # képén is dolgozik
    return _faces_where(
        conn, "WHERE f.photo_id = ?", (photo_id,), include_hidden_folders=True
    )


def _faces_where(
    conn: sqlite3.Connection,
    where_sql: str,
    params: tuple,
    *,
    include_hidden_folders: bool | None = None,
) -> tuple[UnnamedFace, ...]:
    """A közös lekérdezés-test: a `WHERE`-ág és a paraméterei jönnek
    kívülről, ÉRTÉKKÉNT (nem szövegbe fűzve).

    #4887: a rejtett mappák arcai a közös kapu szerint maradnak ki
    (Névtelenek, Mellőzöttek, javaslatok)."""
    lathato = visible_folder_sql(conn, "fo", include_hidden_folders)
    rows = conn.execute(
        "SELECT f.id, f.photo_id, f.rect_left, f.rect_top, f.rect_right, "
        "f.rect_bottom, f.group_id, f.suggested_name, f.state, "
        "fo.path AS folder_path, p.name AS name, "
        "p.width AS width, p.height AS height "
        "FROM face f "
        "JOIN photos p ON p.id = f.photo_id "
        f"JOIN folders fo ON fo.id = p.folder_id AND {lathato} "
        f"{where_sql} "
        "ORDER BY (f.group_id IS NULL), f.group_id, f.id",
        params,
    )
    result = []
    for row in rows:
        width, height = row["width"], row["height"]
        rect = None
        if width and height:
            rect = (
                row["rect_left"] / width,
                row["rect_top"] / height,
                row["rect_right"] / width,
                row["rect_bottom"] / height,
            )
        result.append(
            UnnamedFace(
                id=row["id"],
                photo_id=row["photo_id"],
                photo_path=Path(row["folder_path"]) / row["name"],
                group_id=row["group_id"],
                rect=rect,
                suggested_name=row["suggested_name"],
                state=row["state"],
            )
        )
    return tuple(result)


def mark_faces_named(
    conn: sqlite3.Connection, face_ids: Iterable[int], name: str | None = None
) -> None:
    """A megadott arcok `state`-jét `'named'`-re állítja — a tömeges
    névadás (issue #26, 3. lépcső) sikeres `faces_helper.addFace()` írása
    UTÁN hívandó. Innentől ezek az arcok SEM a „Névtelenek" albumban
    (`unnamed_faces`), SEM a jövőbeli csoportosításban (`group_unnamed_
    faces`, amely csak `state = 'unnamed'`-et néz) nem jelennek meg újra —
    a friss emberi döntés éppúgy szent, mint az importált."""
    ids = list(face_ids)
    if not ids:
        return
    # #26 (4. lépcső): a NEVET is eltesszük. Enélkül a lenyomatot semmi nem
    # kötné névhez, és a javaslat-ág (`named_centroids`) sosem működhetne —
    # ez volt a `face_groups.group_unnamed_faces` dokumentált hiánya.
    # A javaslat ilyenkor tárgytalan, ezért törlődik.
    conn.executemany(
        "UPDATE face SET state = 'named', person_name = ?, "
        "suggested_name = NULL WHERE id = ?",
        [(name, i) for i in ids],
    )


def mark_faces_ignored(conn: sqlite3.Connection, face_ids: Iterable[int]) -> None:
    """A megadott arcok `state`-jét `'ignored'`-ra állítja — a „Mellőzött
    emberek" album (#26).

    Az eredeti Picasában a mellőzés NEM törlés: a személy a *Mellőzött
    emberek* albumba került (`CAlbumLabel::Ignored`, `CThumbDB::
    ignorefacealbum`), és a program külön rákérdezett rá
    (`DeleteMessage::RemoveSingleUnknown`). Ugyanez itt: az arc-sor
    megmarad, csak az állapota változik — így sem a „Névtelenek" albumban,
    sem a csoportosításban nem bukkan fel újra, de vissza is vehető.

    A `state` oszlop ezt az értéket a séma óta várja (ld. `schema.py`: a
    javaslat/elnevezés/ignorálás hármasa)."""
    ids = list(face_ids)
    if not ids:
        return
    conn.executemany(
        "UPDATE face SET state = 'ignored' WHERE id = ?", [(i,) for i in ids]
    )


def unignore_faces(conn: sqlite3.Connection, face_ids: Iterable[int]) -> None:
    """A mellőzés visszavonása — az arc újra a „Névtelenek" albumba kerül.

    A mellőzés az eredetiben sem volt végleges (az album ott van, tehát
    vissza lehet nyúlni) — nálunk sem az."""
    ids = list(face_ids)
    if not ids:
        return
    conn.executemany(
        "UPDATE face SET state = 'unnamed' WHERE id = ? AND state = 'ignored'",
        [(i,) for i in ids],
    )


def ignored_faces(conn: sqlite3.Connection) -> tuple[UnnamedFace, ...]:
    """A mellőzött arcok — a „Mellőzött emberek" album tartalma."""
    return _faces_in_state(conn, "ignored")


def named_centroids(conn: sqlite3.Connection) -> dict[str, "np.ndarray"]:
    """Személynév → a hozzá tartozó arcok ÁTLAGOS lenyomata.

    Ez a javaslat-ág bemenete (`faces.clustering.assign_face`): egy új,
    névtelen archoz ehhez mérjük a hasonlóságot. Csak azok a nevek
    szerepelnek, amelyeknél van legalább egy lenyomatolt, névvel ellátott
    arc — modell/lenyomat nélkül üres, tehát a javaslat-ág egyszerűen nem
    talál el (nem hibázik).
    """
    import numpy as np

    sums: dict[str, tuple[np.ndarray, int]] = {}
    rows = conn.execute(
        "SELECT person_name, embedding FROM face "
        "WHERE state = 'named' AND person_name IS NOT NULL "
        "AND embedding IS NOT NULL"
    )
    for row in rows:
        vector = np.frombuffer(row["embedding"], dtype=np.float32)
        name = row["person_name"]
        if name in sums:
            total, count = sums[name]
            sums[name] = (total + vector, count + 1)
        else:
            sums[name] = (vector.astype(np.float32), 1)
    return {
        name: (total / count).astype(np.float32) for name, (total, count) in sums.items()
    }


def set_suggested_name(
    conn: sqlite3.Connection, face_id: int, name: str | None
) -> None:
    """Javaslat rögzítése (vagy törlése) egy arcra.

    A javaslat NEM döntés: az arc állapota `'unnamed'` marad, csak kap egy
    kérdőjeles nevet — az eredeti is kérdésként vetette fel
    (`PeoplePanel::SuggestionFmt` = „%s?"), pipa/x gombbal."""
    conn.execute(
        "UPDATE face SET suggested_name = ? WHERE id = ?", (name, face_id)
    )


def suggested_faces(conn: sqlite3.Connection) -> tuple[UnnamedFace, ...]:
    """Azok a névtelen arcok, amelyekre van még el nem döntött javaslat."""
    return tuple(
        face
        for face in _faces_in_state(conn, "unnamed")
        if face.suggested_name
    )


def suggested_faces_for(
    conn: sqlite3.Connection, name: str
) -> tuple[UnnamedFace, ...]:
    """Egy megnevezett személy MÉG EL NEM DÖNTÖTT javaslatai (#2187).

    A `suggested_faces()` minden függő javaslatot ad; a személy-album
    javaslat-munkafolyamatának viszont az kell, ami ehhez az EGY névhez
    tartozik — ebből lesz a fejléc darabszáma, és ezen hat az „Az összes
    jóváhagyása".

    A névösszevetés kis-nagybetűre érzéketlen, ahogy a `.picasa.ini`
    `[Contacts2]` neveinél is szokás. Üres névre üres eredmény (nem hiba):
    a felület akkor is meghívhatja, amikor nincs nyitott személy-album."""
    if not name:
        return ()
    kulcs = name.casefold()
    return tuple(
        face
        for face in suggested_faces(conn)
        if face.suggested_name and face.suggested_name.casefold() == kulcs
    )


def suggested_album_photos(
    conn: sqlite3.Connection, name: str
) -> tuple[PhotoRecord, ...]:
    """Azok a fotók, amelyeken ehhez a névhez FÜGGŐ javaslat tartozik (#2187).

    A személy-album rácsa ebből kapja a javaslatokat: a névvel ELLÁTOTT
    arcok a `.picasa.ini`-ből jönnek (`people.person_photos`), a még el nem
    döntött javaslatok viszont a saját `face` táblánkból. A kettő külön
    halmaz, és a metszetük sem feltétlenül üres.

    A névösszevetés kis-nagybetűre érzéketlen — ugyanaz a szokás, mint a
    `suggested_faces_for`-nál. Üres névre üres eredmény (nem hiba): a
    felület akkor is hívja, amikor nem személy-album van nyitva.

    Egy fotó egyszer szerepel akkor is, ha több arca hordozza ugyanazt a
    javaslatot — a rács SORA a fotó, nem az arc.
    """
    if not name:
        return ()
    rows = conn.execute(
        f"{_select(conn)} WHERE p.id IN ("
        "SELECT DISTINCT photo_id FROM face "
        "WHERE state = 'unnamed' AND suggested_name IS NOT NULL "
        "AND suggested_name = ? COLLATE NOCASE"
        ") ORDER BY f.path, p.name",
        (name,),
    )
    return _records(rows)


def unnamed_photo_count(conn: sqlite3.Connection) -> int:
    """Hány LÁTHATÓ fotón van még névtelen saját találat — a „Névtelenek"
    album hasáb-darabszáma (#4887: a rejtett mappák képei nem számítanak)."""
    row = conn.execute(
        "SELECT COUNT(DISTINCT fa.photo_id) AS n FROM face fa "
        "JOIN photos p ON p.id = fa.photo_id "
        f"JOIN folders f ON f.id = p.folder_id AND {visible_folder_sql(conn)} "
        "WHERE fa.state = 'unnamed'"
    ).fetchone()
    return int(row["n"]) if row is not None else 0


def unnamed_face_count(conn: sqlite3.Connection) -> int:
    """Hány látható, még névtelen arc van a „Névtelenek” albumban."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM face fa "
        "JOIN photos p ON p.id = fa.photo_id "
        f"JOIN folders f ON f.id = p.folder_id AND {visible_folder_sql(conn)} "
        "WHERE fa.state = 'unnamed'"
    ).fetchone()
    return int(row["n"]) if row is not None else 0


def unnamed_album_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """A „Névtelenek" album (issue #26, javasolt 1. lépcső): minden fotó,
    amelyen a SAJÁT detektorunk legalább egy arcot talált — csoportosítás
    és névfeloldás NÉLKÜL (azok a terv 2–3. lépcsője). A `state` oszlop itt
    mindig 'unnamed', mert ez a lépcső még nem ír más állapotot."""
    rows = conn.execute(
        f"{_select(conn)} WHERE p.id IN ("
        "SELECT DISTINCT photo_id FROM face WHERE state = 'unnamed'"
        ") ORDER BY f.path, p.name"
    )
    return _records(rows)
