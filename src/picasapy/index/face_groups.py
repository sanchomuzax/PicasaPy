"""A „Névtelenek” arcainak inkrementális csoportosítása — DB-perzisztencia
a `picasapy.faces.clustering` tiszta algoritmusára építve (issue #26, 2.
lépcső).

ALAPSZABÁLY (issue #26 terve, „a Picasa döntései szentek”): a `face`
tábla `state = 'unnamed'` sorai a KIZÁRÓLAGOS bemenete a csoportosításnak.
Már névvel ellátott/javasolt/ignorált arc (bármely `state != 'unnamed'`)
SOHA nem kerül ide — a meglévő `faces=` hozzárendeléseket ez a réteg nem
értékeli újra, és nem is látja őket (a `state` oszlop maga a védelem: az
1. lépcső `FaceScanController`-je ma egyáltalán nem hoz létre `face` sort
névcímkés fotóhoz, egy jövőbeli lépcső pedig a `state='named'` értékkel
zárná ki ugyanígy)."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping

import numpy as np

from picasapy.faces.clustering import (
    DEFAULT_CLUSTER_THRESHOLD,
    DEFAULT_SUGGEST_THRESHOLD,
    PICASA_STEPS,
    FaceGroupCentroid,
    assign_face,
    cosine_similarity,
)

from .faces_detected import named_centroids as _named_centroids
from .faces_detected import set_suggested_name


#: #3237: a „További javaslatok keresése" ennyivel csökkenti a LÉPCSŐT.
#:
#: Az eredeti `moresug` (kezelő `0x00602890`) a `FRSuggestionThreshold`-ot
#: `/100 − 0,1`-del használja, visszaírás nélkül. ⛔ A `0,75`-ös SZÁMOT nem
#: vesszük át: nálunk a küszöb a `step_to_threshold` skáláján él (a Picasa
#: 50–95-ös lépcsője a `[MIN_SIMILARITY … MAX_SIMILARITY]` sávba). A hű
#: megfelelő a **lépcső** csökkentése tízzel — a vezérlőt vesszük át, nem a
#: számot (#2187 mértékegység-csapdája).
LAZITAS_LEPCSO = 10


def lazitott_lepcso(lepcso: int) -> int:
    """A lazított lépcső — a saját skálánk alját nem lépi túl.

    Az alja alatt a `step_to_threshold` már extrapolálna (a sávon kívülre),
    és a „javaslat" mindenre eltalálna; ott tehát megállunk.
    """
    return max(PICASA_STEPS[0], int(lepcso) - LAZITAS_LEPCSO)


def javaslatokat_ujraszamol(
    conn: sqlite3.Connection,
    suggest_threshold: float,
    named_centroids: Mapping[str, np.ndarray] | None = None,
) -> int:
    """A MEGADOTT küszöbbel javaslatot keres a még javaslat nélküli arcokra.

    A `group_unnamed_faces`-től két dologban tér el, és mindkettő szándékos:

    1. **a már csoportba sorolt arcokat is megvizsgálja** — a lazítás épp
       azokra hasznos, amelyek korábban javaslat helyett csoportba kerültek;
    2. **csak `suggested_name`-et ír**: a csoportokhoz hozzá sem nyúl, és a
       kézzel beírt javaslatot sem írja felül.

    A névvel ellátott (`state='named'`) arcokat nem bántja.

    Visszatérési érték: hány arcra írtunk ÚJ javaslatot.
    """
    if named_centroids is None:
        named_centroids = _named_centroids(conn)
    if not named_centroids:
        return 0  # nincs mihez hasonlítani
    rows = conn.execute(
        "SELECT id, embedding FROM face "
        "WHERE state = 'unnamed' AND suggested_name IS NULL "
        "AND embedding IS NOT NULL ORDER BY id"
    ).fetchall()
    irt = 0
    for row in rows:
        embedding = np.frombuffer(row["embedding"], dtype=np.float32)
        nev, hasonlosag = _legkozelebbi_nev(embedding, named_centroids)
        if nev is None or hasonlosag < suggest_threshold:
            continue
        set_suggested_name(conn, row["id"], nev)
        irt += 1
    return irt


def _legkozelebbi_nev(
    embedding: np.ndarray, named_centroids: Mapping[str, np.ndarray]
) -> tuple[str | None, float]:
    """A legjobban illeszkedő NEVESÍTETT centroid és a hasonlósága.

    Ugyanaz a mérték, amit az `assign_face` használ (`cosine_similarity`) —
    egy helyen, hogy a két út ne sodródjon el egymástól.
    """
    legjobb_nev: str | None = None
    legjobb = -1.0
    for nev, centroid in named_centroids.items():
        hasonlosag = cosine_similarity(embedding, centroid)
        if hasonlosag > legjobb:
            legjobb_nev, legjobb = nev, hasonlosag
    return legjobb_nev, legjobb


def group_unnamed_faces(
    conn: sqlite3.Connection,
    suggest_threshold: float = DEFAULT_SUGGEST_THRESHOLD,
    cluster_threshold: float = DEFAULT_CLUSTER_THRESHOLD,
    named_centroids: Mapping[str, np.ndarray] | None = None,
) -> int:
    """A még csoportosítatlan NÉVTELEN arcok besorolása — egy híváson
    belül `id` sorrendben (determinisztikus, ismételt futásnál idempotens:
    a már besorolt arcokat a `group_id IS NULL` szűrő kihagyja).

    `named_centroids`: {személynév: centroid-lenyomat} — a JAVASLAT-ághoz
    (issue #26 terve). Egyelőre NINCS forrás, amiből ez automatikusan
    összeállna (a `.picasa.ini` `faces=`/`[Contacts2]` neveit a saját
    lenyomatainkhoz kötni külön, dokumentálatlan illesztést igényelne —
    ld. a jegy 2. lépcsőjének jelentése), ezért alapból üres: a
    javaslat-ág ma soha nem talál el, minden névtelen arc csoportba
    kerül/új csoportot nyit. A paraméter a jövőbeli (3–4. lépcső)
    bekötésre való, hívóként HASZNÁLHATÓ, de nem kötelező.

    Visszatérési érték: hány arcot soroltunk be (csoportba VAGY új
    csoportba) — a javaslatok NEM számítanak bele, mert azokhoz a
    jelenlegi lépcső nem ír semmit (a javaslat elfogadása/DB-perzisztenciája
    a terv 4. lépcsője)."""
    # #26 (4. lépcső): ha a hívó nem ad névhez kötött centroidokat, MOST
    # MÁR magunk össze tudjuk állítani őket (`face.person_name`) — a
    # korábbi „nincs forrás, amiből ez automatikusan összeállna" megszűnt.
    if named_centroids is None:
        named_centroids = _named_centroids(conn)
    groups = _load_groups(conn)
    rows = conn.execute(
        "SELECT id, embedding FROM face "
        "WHERE state = 'unnamed' AND group_id IS NULL AND embedding IS NOT NULL "
        "ORDER BY id"
    ).fetchall()
    assigned = 0
    for row in rows:
        embedding = np.frombuffer(row["embedding"], dtype=np.float32)
        result = assign_face(embedding, named_centroids, groups, suggest_threshold, cluster_threshold)
        if result.kind == "suggestion":
            # A javaslat NEM döntés: rögzítjük az arcon, az állapot
            # 'unnamed' marad, és a felhasználó erősíti meg vagy veti el
            # (pipa/x). Így nem "vész el", és nem is dönt helyette senki.
            set_suggested_name(conn, row["id"], result.suggested_name)
            # A javaslat-munkafolyamat (megerősítés/elutasítás öt gombbal)
            # a terv 4. lépcsője — itt csak a döntést hoztuk meg, DB-írás
            # nélkül. A face sor `state`-je 'unnamed' marad, tehát a
            # következő futás újra megvizsgálja (nem "elveszett" javaslat).
            continue
        if result.kind == "grouped":
            assert result.group_id is not None
            assert result.new_centroid is not None
            _assign_to_group(conn, row["id"], result.group_id, result.new_centroid)
            groups = [
                group
                if group.group_id != result.group_id
                else FaceGroupCentroid(
                    group.group_id, result.new_centroid, group.face_count + 1
                )
                for group in groups
            ]
            assigned += 1
        else:  # "new_group"
            assert result.new_centroid is not None
            group_id = _create_group(conn, result.new_centroid)
            conn.execute("UPDATE face SET group_id = ? WHERE id = ?", (group_id, row["id"]))
            groups.append(FaceGroupCentroid(group_id, result.new_centroid, 1))
            assigned += 1
    return assigned


def _load_groups(conn: sqlite3.Connection) -> list[FaceGroupCentroid]:
    rows = conn.execute("SELECT id, centroid, face_count FROM face_group")
    return [
        FaceGroupCentroid(
            group_id=row["id"],
            centroid=np.frombuffer(row["centroid"], dtype=np.float32),
            face_count=row["face_count"],
        )
        for row in rows
    ]


def _create_group(conn: sqlite3.Connection, centroid: np.ndarray) -> int:
    cursor = conn.execute(
        "INSERT INTO face_group (centroid, face_count) VALUES (?, 1)",
        (np.asarray(centroid, dtype=np.float32).tobytes(),),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def _assign_to_group(
    conn: sqlite3.Connection, face_id: int, group_id: int, new_centroid: np.ndarray
) -> None:
    conn.execute("UPDATE face SET group_id = ? WHERE id = ?", (group_id, face_id))
    conn.execute(
        "UPDATE face_group SET centroid = ?, face_count = face_count + 1 WHERE id = ?",
        (np.asarray(new_centroid, dtype=np.float32).tobytes(), group_id),
    )


def face_groups(conn: sqlite3.Connection) -> tuple[FaceGroupCentroid, ...]:
    """A jelenleg létező „Névtelenek”-csoportok — teszteknek/jövőbeli
    UI-lekérdezésnek hasznos áttekintés."""
    return tuple(_load_groups(conn))
