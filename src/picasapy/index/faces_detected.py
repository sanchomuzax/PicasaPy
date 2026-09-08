"""#26 (1. lépcső): a SAJÁT (YuNet) arc-detektálás tárolása az indexben, és
a „Névtelenek" album lekérdezése — csoportosítás/névfeloldás NÉLKÜL (ez a
terv 2–3. lépcsője).

Külön tábla (`face`, `schema.py`), a `photo_hashes`/`hashes.py` mintáját
követve: tisztán származtatott adat, fotónkénti töröl-és-újraír frissítéssel
(`replace_faces`) — egy fotó ismételt szkennelése nem halmoz duplikátumot.

A `.picasa.ini` `faces=`/`[Contacts2]` adatait ez a réteg NEM olvassa és
NEM írja — az a `ini/faces.py`/`index/people.py` már meglévő rétege,
változatlanul. A két réteg összefonása (pl. „ez a Picasa-arc egyezik ezzel
a saját találattal") a terv KÉSŐBBI lépcsője."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from picasapy.faces.detector import FaceDetection, FaceLandmarks

from .queries import _SELECT, PhotoRecord, _records


def replace_faces(
    conn: sqlite3.Connection, photo_id: int, faces: Iterable[FaceDetection]
) -> None:
    """A `photo_id` fotóhoz tárolt SAJÁT arc-találatok cseréje.

    Törli a fotó korábbi sorait, majd beszúrja az újakat — idempotens
    (egy fotó ismételt szkennelése nem duplikál). A hívó felelős a
    commitért (a scan-worker kötegelve commitol, a dedup/hash-scan
    mintája szerint, ld. `app/dedup_controller.py`)."""
    conn.execute("DELETE FROM face WHERE photo_id = ?", (photo_id,))
    rows = [
        (
            photo_id,
            face.left,
            face.top,
            face.right,
            face.bottom,
            face.score,
            face.landmarks.right_eye[0],
            face.landmarks.right_eye[1],
            face.landmarks.left_eye[0],
            face.landmarks.left_eye[1],
            face.landmarks.nose[0],
            face.landmarks.nose[1],
            face.landmarks.mouth_right[0],
            face.landmarks.mouth_right[1],
            face.landmarks.mouth_left[0],
            face.landmarks.mouth_left[1],
        )
        for face in faces
    ]
    if not rows:
        return
    conn.executemany(
        "INSERT INTO face ("
        "photo_id, rect_left, rect_top, rect_right, rect_bottom, det_conf, "
        "right_eye_x, right_eye_y, left_eye_x, left_eye_y, nose_x, nose_y, "
        "mouth_right_x, mouth_right_y, mouth_left_x, mouth_left_y"
        ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )


def clear_faces(conn: sqlite3.Connection, photo_id: int) -> None:
    """A fotó SAJÁT arc-találatainak törlése (pl. ha a Picasa időközben
    névcímkét kapott a fotón — ld. `FaceScanController`: onnantól a mi
    detektorunk kihagyja, a régi találat pedig félrevezető lenne)."""
    conn.execute("DELETE FROM face WHERE photo_id = ?", (photo_id,))


def reset_all_faces(conn: sqlite3.Connection) -> int:
    """A SAJÁT arc-találatok alaphelyzetbe állítása — az eredeti „Arcok
    alaphelyzetbe állítása" INDEX-oldali fele (#422).

    Az eredeti figyelmeztetése (`CThumbUI::ResetAllFaces`) szerint ez
    „törli az összes személyi albumot, és a Név nélküliek albumba helyezi
    át az arcokat". Nálunk pontosan ennyi történik: minden arc `'unnamed'`
    állapotba kerül, a névhez kötés és a javaslat törlődik, a csoportok
    pedig eltűnnek (a következő csoportosítás újraépíti őket).

    **Amit NEM csinál:** nem nyúl a `.picasa.ini` `faces=`/`[Contacts2]`
    tartalmához. Az eredeti ezt KÜLÖN kérdésként tette fel
    (`CThumbUI::ResetAll`: „Szeretné eltávolítani az arcokkal kapcsolatos
    összes adatot az INI fájlokból?") — az ember által adott névcímke a
    projekt alapszabálya szerint szent, azt csak külön, kifejezett kérésre
    szabad bántani.

    A visszatérési érték az érintett arcok száma.
    """
    row = conn.execute("SELECT COUNT(*) AS n FROM face").fetchone()
    affected = int(row["n"]) if row is not None else 0
    conn.execute(
        "UPDATE face SET state = 'unnamed', person_name = NULL, "
        "suggested_name = NULL, group_id = NULL"
    )
    conn.execute("DELETE FROM face_group")
    return affected


def detected_face_count(conn: sqlite3.Connection, photo_id: int) -> int:
    """Hány SAJÁT arc-találat tartozik a fotóhoz (a néző overlay-jének
    később hasznos lekérdezés — 1. lépcsőben csak a teszteké)."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM face WHERE photo_id = ?", (photo_id,)
    ).fetchone()
    return int(row["n"]) if row is not None else 0


@dataclass(frozen=True)
class PendingEmbeddingFace:
    """Egy DETEKTÁLT, de MÉG LENYOMAT NÉLKÜLI arc — pontosan annyi adattal,
    amennyi a `FaceEmbedder.compute()`-hoz kell (kép + `FaceDetection`).
    A `faces_missing_embedding` adja vissza, a lenyomat-számítás (issue
    #26, 2. lépcső, a detektálásnál alacsonyabb prioritású sor) ezen megy
    végig."""

    id: int
    photo_path: Path
    detection: FaceDetection


def faces_missing_embedding(conn: sqlite3.Connection) -> tuple[PendingEmbeddingFace, ...]:
    """A még lenyomat nélküli arcok — a fotó útvonalával és a tárolt
    kerettel/5 ponttal együtt, hogy a lenyomat-számítás ne kelljen újra
    detektáljon. `id` szerint rendezve (determinisztikus feldolgozási
    sorrend a csoportosításhoz, ld. `index.face_groups`)."""
    rows = conn.execute(
        "SELECT f.id, f.rect_left, f.rect_top, f.rect_right, f.rect_bottom, "
        "f.det_conf, f.right_eye_x, f.right_eye_y, f.left_eye_x, f.left_eye_y, "
        "f.nose_x, f.nose_y, f.mouth_right_x, f.mouth_right_y, "
        "f.mouth_left_x, f.mouth_left_y, fo.path AS folder_path, p.name AS name "
        "FROM face f "
        "JOIN photos p ON p.id = f.photo_id "
        "JOIN folders fo ON fo.id = p.folder_id "
        "WHERE f.embedding IS NULL "
        "ORDER BY f.id"
    )
    result = []
    for row in rows:
        detection = FaceDetection(
            left=row["rect_left"],
            top=row["rect_top"],
            right=row["rect_right"],
            bottom=row["rect_bottom"],
            score=row["det_conf"],
            landmarks=FaceLandmarks(
                right_eye=(row["right_eye_x"], row["right_eye_y"]),
                left_eye=(row["left_eye_x"], row["left_eye_y"]),
                nose=(row["nose_x"], row["nose_y"]),
                mouth_right=(row["mouth_right_x"], row["mouth_right_y"]),
                mouth_left=(row["mouth_left_x"], row["mouth_left_y"]),
            ),
        )
        result.append(
            PendingEmbeddingFace(
                id=row["id"],
                photo_path=Path(row["folder_path"]) / row["name"],
                detection=detection,
            )
        )
    return tuple(result)


def store_embedding(
    conn: sqlite3.Connection, face_id: int, embedding: np.ndarray | None
) -> None:
    """A `face_id` sor lenyomatának mentése — `None` esetén NULL marad
    (modell nélküli/sikertelen számítás, ld. `FaceEmbedder.compute`), nem
    hiba. `float32` bájtsorként tárolva (`numpy.frombuffer` olvassa
    vissza, ld. `face_embedding`)."""
    blob = np.asarray(embedding, dtype=np.float32).tobytes() if embedding is not None else None
    conn.execute("UPDATE face SET embedding = ? WHERE id = ?", (blob, face_id))


def face_embedding(conn: sqlite3.Connection, face_id: int) -> np.ndarray | None:
    """A `face_id` sor lenyomata, vagy `None`, ha még nincs kiszámolva."""
    row = conn.execute("SELECT embedding FROM face WHERE id = ?", (face_id,)).fetchone()
    if row is None or row["embedding"] is None:
        return None
    return np.frombuffer(row["embedding"], dtype=np.float32)


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


def unnamed_faces(conn: sqlite3.Connection) -> tuple[UnnamedFace, ...]:
    """Minden `state = 'unnamed'` arc — csoport szerint rendezve (a
    csoportosítatlanok, `group_id IS NULL`, a végén), majd `id` szerint
    (determinisztikus). A már névvel ellátott (`state != 'unnamed'`) arcokat
    ez a lekérdezés SOSEM adja vissza — az alapszabály (a Picasa döntései
    szentek) itt is szerkezeti kizárás, a `group_unnamed_faces` mintájára."""
    return _faces_in_state(conn, "unnamed")


def _faces_in_state(conn: sqlite3.Connection, state: str) -> tuple[UnnamedFace, ...]:
    """A közös test: egy adott állapotú arcok kiolvasása. A `state`
    ÉRTÉKKÉNT (paraméterként) megy be, nem szövegbe fűzve."""
    rows = conn.execute(
        "SELECT f.id, f.photo_id, f.rect_left, f.rect_top, f.rect_right, "
        "f.rect_bottom, f.group_id, f.suggested_name, "
        "fo.path AS folder_path, p.name AS name, "
        "p.width AS width, p.height AS height "
        "FROM face f "
        "JOIN photos p ON p.id = f.photo_id "
        "JOIN folders fo ON fo.id = p.folder_id "
        "WHERE f.state = ? "
        "ORDER BY (f.group_id IS NULL), f.group_id, f.id",
        (state,),
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


def unnamed_album_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    """A „Névtelenek" album (issue #26, javasolt 1. lépcső): minden fotó,
    amelyen a SAJÁT detektorunk legalább egy arcot talált — csoportosítás
    és névfeloldás NÉLKÜL (azok a terv 2–3. lépcsője). A `state` oszlop itt
    mindig 'unnamed', mert ez a lépcső még nem ír más állapotot."""
    rows = conn.execute(
        f"{_SELECT} WHERE p.id IN ("
        "SELECT DISTINCT photo_id FROM face WHERE state = 'unnamed'"
        ") ORDER BY f.path, p.name"
    )
    return _records(rows)


#: A `face_scan.ok` értékei — a jelölés OKA (#2519).
#:
#: `detektalva`: lefutott a detektálás (találattal vagy anélkül). A fájl
#: megváltozása feloldja: az új tartalmat újra meg kell nézni.
#:
#: `kizarva`: a Mappakezelő arcfelismerés-kizárása tette ki. **ERŐSEBB** — a
#: fájl változása sem oldja fel, csak a szándékos visszaengedés
#: (`forget_face_scan`). Ez az eredeti Picasa `facerect = 1` jelzőjének
#: megfelelője (`docs/specs/picasa-imagedata-rekord.md`, #2515): a téglalap
#: írója csak nulla értékre ír, tehát az 1 megvédi a képet.
OK_DETEKTALVA = "detektalva"
OK_KIZARVA = "kizarva"

#: A mappa ÉS az alfái — a kizárás az egész fára vonatkozik (`#449`: „a
#: mappára és az alfáira"). A `LIKE`-minta ESCAPE-elve megy, mert egy valódi
#: mappanévben is állhat `%` vagy `_` (mindkettő joker a `LIKE`-ban).
_MAPPAFA_FELTETEL = "(f.path = ? OR f.path LIKE ? ESCAPE '\\')"

#: #2761: az elválasztó a PLATFORMÉ, nem fixen `/`. Az index natív alakot
#: tárol (`index/paths.py`: `str(Path(...).resolve())`), tehát Windowson a
#: `C:\kepek\alfa` sosem illeszkedett a korábbi, fixen `/`-t fűző mintára —
#: a kizárt mappa ALFÁI nem kapták meg a jelölést. Modul-szintű konstans,
#: hogy a teszt MINDKÉT alakot mérni tudja a fejlesztői gépen is.
_ELVALASZTO = os.sep


def _like_vedett(szoveg: str) -> str:
    """A `LIKE`-minta escape-elése (`ESCAPE '\'`): a backslash ÖNMAGÁT is
    escape-eli, a `%` és a `_` pedig joker."""
    return szoveg.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _mappafa_parameterek(
    folder_path: str, *, elvalaszto: str | None = None
) -> tuple[str, str]:
    """A `_MAPPAFA_FELTETEL` két paramétere: a pontos út és az alfa-minta.

    Az `elvalaszto` alapértéke a platformé; a teszt adja meg kifejezetten,
    hogy MINDKÉT alak mérhető legyen ott is, ahol csak az egyik natív."""
    sep = _ELVALASZTO if elvalaszto is None else elvalaszto
    # a záró elválasztót le kell vágni — MINDKÉT alakot, mert a `folders.path`
    # jöhet másik platformról is (átvett adatbázis, `.picasa.ini`-korpusz)
    torzs = folder_path.rstrip("/\\")
    return (folder_path, _like_vedett(torzs) + _like_vedett(sep) + "%")


def mark_face_scan(
    conn: sqlite3.Connection,
    photo_id: int,
    *,
    mtime_ns: int,
    size: int,
    ok: str = OK_DETEKTALVA,
) -> None:
    """Nyom hagyása arról, hogy a fotón LEFUTOTT az arc-detektálás.

    A `face` tábla csak a megtalált arcokat tárolja, ezért nyom nélkül egy
    arc nélküli fotó megkülönböztethetetlen a még sosem vizsgálttól — a
    detektálás minden szkennelésnél újrafutna rajta (#2519).

    Fotónként EGY sor (a `photo_id` az elsődleges kulcs), tehát az ismételt
    jelölés felülír, nem duplikál. A hívó felelős a commitért."""
    conn.execute(
        "INSERT INTO face_scan(photo_id, mtime_ns, size, ok) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(photo_id) DO UPDATE SET"
        " mtime_ns = excluded.mtime_ns, size = excluded.size, ok = excluded.ok",
        (photo_id, int(mtime_ns), int(size), ok),
    )


def face_scan_done(
    conn: sqlite3.Connection, photo_id: int, *, mtime_ns: int, size: int
) -> bool:
    """Lefutott-e már a detektálás EZEN a fájlállapoton?

    `True`, ha van jelölés, ÉS vagy a fájl azonossága (`mtime_ns`, `size`)
    egyezik, vagy a jelölés oka `kizarva` — az utóbbit a fájl változása sem
    oldja fel (ld. `OK_KIZARVA`)."""
    sor = conn.execute(
        "SELECT mtime_ns, size, ok FROM face_scan WHERE photo_id = ?", (photo_id,)
    ).fetchone()
    if sor is None:
        return False
    if sor[2] == OK_KIZARVA:
        return True
    return int(sor[0]) == int(mtime_ns) and int(sor[1]) == int(size)


def mark_folder_excluded(conn: sqlite3.Connection, folder_path: str) -> int:
    """A mappa MINDEN fotójának megjelölése `kizarva` okkal; a megjelöltek
    száma.

    Az eredeti Picasa a Mappakezelő arcfelismerés-kizárásakor teszi ki a
    saját jelzőjét a képekre (`CFolderMgrDialog` → `FUN_005cef20` →
    `FUN_00491210` → `FUN_00446960`, `0x00491627`) — enélkül a mappa
    visszaengedése azonnal, kérdés nélkül újraindítaná a detektálást.

    A hívó felelős a commitért."""
    kurzor = conn.execute(
        "INSERT INTO face_scan(photo_id, mtime_ns, size, ok)"
        " SELECT p.id, p.mtime_ns, p.size, ?"
        " FROM photos p JOIN folders f ON f.id = p.folder_id"
        f" WHERE {_MAPPAFA_FELTETEL}"
        " ON CONFLICT(photo_id) DO UPDATE SET"
        " mtime_ns = excluded.mtime_ns, size = excluded.size, ok = excluded.ok",
        (OK_KIZARVA, *_mappafa_parameterek(folder_path)),
    )
    return int(kurzor.rowcount)


def forget_face_scan(
    conn: sqlite3.Connection, *, folder_path: str | None = None, photo_id: int | None = None
) -> int:
    """A jelölés törlése — ettől a következő szkennelés újra megnézi a
    fotókat. A törölt sorok száma.

    Egy mappa visszaengedésekor a hívó a felhasználó megerősítő válasza UTÁN
    hívja: a jelölés eldobása szándékos döntés, nem automatizmus."""
    if photo_id is not None:
        kurzor = conn.execute("DELETE FROM face_scan WHERE photo_id = ?", (photo_id,))
    elif folder_path is not None:
        kurzor = conn.execute(
            "DELETE FROM face_scan WHERE photo_id IN ("
            " SELECT p.id FROM photos p JOIN folders f ON f.id = p.folder_id"
            f" WHERE {_MAPPAFA_FELTETEL})",
            _mappafa_parameterek(folder_path),
        )
    else:
        raise ValueError("a `folder_path` és a `photo_id` közül az egyik kötelező")
    return int(kurzor.rowcount)


def delete_faces_in_folder(conn: sqlite3.Connection, folder_path: str) -> int:
    """A mappa (és alfái) fotóihoz tárolt SAJÁT arc-találatok törlése; a
    törölt sorok száma.

    A `.picasa.ini` `faces=` / `[Contacts2]` adatát ez NEM érinti — az a
    felhasználó saját, Picasában felvett adata. Itt csak a származtatott
    (bármikor újraszámolható) találataink tűnnek el, a kizárás megerősítő
    kérdése után (#2519). A hívó felelős a commitért."""
    kurzor = conn.execute(
        "DELETE FROM face WHERE photo_id IN ("
        " SELECT p.id FROM photos p JOIN folders f ON f.id = p.folder_id"
        f" WHERE {_MAPPAFA_FELTETEL})",
        _mappafa_parameterek(folder_path),
    )
    return int(kurzor.rowcount)
