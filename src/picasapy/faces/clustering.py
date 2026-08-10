"""Inkrementális arc-csoportosítás — tiszta matematika, klaszterező könyvtár
NÉLKÜL (issue #26, 2. lépcső, méréssel ellenőrzött terv).

A modul a lenyomatokat (numpy tömbként) PARAMÉTERKÉNT várja — nem ismeri
sem az SQLite-indexet, sem az OpenCV-t, ezért modell nélkül is teljesen
tesztelhető (a #26 kötelező-teszt szabálya). A DB-perzisztenciát (a
`face_group` tábla olvasása/írása, a `face.group_id` frissítése) az
`picasapy.index.face_groups` réteg végzi, erre a modulra építve.

ALGORITMUS (a terv szerint, „nincs éjszakai újraszámolás”):

    minden ÚJ (névtelen) archoz:
        ha van elnevezett személy, akihez a hasonlóság >= SUGGEST_THRESHOLD
            → JAVASLAT (a személy-hozzárendelést a jelenlegi lépcső NEM
              írja — a javaslat elfogadása a terv 4. lépcsője)
        különben: a „Névtelenek” meglévő csoportjaihoz mérve
            >= CLUSTER_THRESHOLD → a legjobban illeszkedő csoportba kerül,
              a centroid frissül (súlyozott átlag a csoport méretével)
            egyébként → új csoport (az arc lesz az első tagja/centroidja)

A hasonlóság koszinusz-hasonlóság (`cosine_similarity`), [-1, 1] tartományban
(gyakorlatban SFace-lenyomatokra jellemzően [0, ~0.7]).

KÜSZÖBÖK — miért ennyi (a Picasa mintáját követve, de a saját skálánkhoz
hangolva, ld. issue #26 2026-08-07-i kommentje):

A Picasa `facethresh0`/`facethresh1` beállítása a 10 lépcsős
50/55/60/65/70/75/80/85/90/95 listából választott (`runtime/options.fen`,
ld. issue #26) — ezt a LÉPCSŐZÉST vesszük át (`PICASA_STEPS`), de a
mögöttes hasonlósági skálát a saját motorunkhoz (SFace) hangoljuk, mert a
Picasa `conf`-ja motorspecifikus (Neven Vision), nem összemérhető a
miénkkel.

Az SFace hivatalos mintakódja (OpenCV Zoo, `face_recognition_sface`
demo) 0.363 koszinusz-hasonlóságot ajánl „ugyanaz a személy” döntési
határként (1e-3 hamis-elfogadási arány mellett) — ez egy PUBLIKUS,
mért referenciaérték, nem saját becslés. Erre a pontra hangoljuk a skála
közepét: a [MIN_SIMILARITY, MAX_SIMILARITY] = [0.20, 0.55] tartomány úgy
lett választva, hogy a Picasa-lépcsőzés KÖZEPÉHEZ közeli lépcső (70) essen
egybe az SFace 0.363-as referenciájával — ez indokolja a CSOPORTOSÍTÁS
alapértelmezett lépcsőjét (70 → kb. 0.356). A JAVASLAT — mivel egy
MEGLÉVŐ, elnevezett személyhez társít, tehát tévedése látványosabb, mint
egy névtelen csoport téves összevonása — szigorúbb, magasabb lépcsőt kap
(85 → kb. 0.472)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

#: A Picasa `facethresh0`/`facethresh1` beállításának 10 lépcsője
#: (`runtime/options.fen`, issue #26) — a LÉPCSŐZÉST vesszük át.
PICASA_STEPS: tuple[int, ...] = (50, 55, 60, 65, 70, 75, 80, 85, 90, 95)

#: A saját (SFace) koszinusz-hasonlósági skálánk alsó/felső határa — a
#: modul-docstring indoklása szerint hangolva.
MIN_SIMILARITY = 0.20
MAX_SIMILARITY = 0.55

#: Alapértelmezett lépcsők (a modul-docstring indoklása szerint).
DEFAULT_CLUSTER_STEP = 70
DEFAULT_SUGGEST_STEP = 85


def step_to_threshold(step: int) -> float:
    """Egy Picasa-lépcső (50–95) átváltása a saját hasonlósági skálánkra,
    lineáris interpolációval a `[MIN_SIMILARITY, MAX_SIMILARITY]` sávban."""
    lo, hi = PICASA_STEPS[0], PICASA_STEPS[-1]
    fraction = (step - lo) / (hi - lo)
    return MIN_SIMILARITY + fraction * (MAX_SIMILARITY - MIN_SIMILARITY)


DEFAULT_CLUSTER_THRESHOLD = step_to_threshold(DEFAULT_CLUSTER_STEP)
DEFAULT_SUGGEST_THRESHOLD = step_to_threshold(DEFAULT_SUGGEST_STEP)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Koszinusz-hasonlóság — 0.0, ha bármelyik vektor nulla (nem hiba)."""
    vec_a = np.asarray(a, dtype=np.float64)
    vec_b = np.asarray(b, dtype=np.float64)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


@dataclass(frozen=True)
class FaceGroupCentroid:
    """Egy „Névtelenek”-csoport a csoportosító algoritmus szemével — csak
    az, ami a döntéshez kell (DB-azonosító + centroid + taglétszám)."""

    group_id: int
    centroid: np.ndarray
    face_count: int


@dataclass(frozen=True)
class AssignmentResult:
    """Egy arc lenyomatának elbírálása — pontosan egy a három kimenet közül
    (`kind`): `"suggestion"` (elnevezett személyhez javasolva, a
    hozzárendelést a jelenlegi lépcső NEM írja), `"grouped"` (meglévő
    névtelen csoportba került, `new_centroid` a frissített centroid) vagy
    `"new_group"` (önálló, első tagú csoport, `new_centroid` az arc saját
    lenyomata)."""

    kind: str
    group_id: int | None = None
    new_centroid: np.ndarray | None = None
    suggested_name: str | None = None
    similarity: float = 0.0


def _weighted_centroid(
    centroid: np.ndarray, face_count: int, embedding: np.ndarray
) -> np.ndarray:
    """A csoport centroidjának frissítése egy új taggal — súlyozott átlag,
    hogy egy nagy csoport centroidját ne mozgassa el aránytalanul egyetlen
    új arc."""
    old = np.asarray(centroid, dtype=np.float64)
    new = np.asarray(embedding, dtype=np.float64)
    updated = (old * face_count + new) / (face_count + 1)
    return updated.astype(np.float32)


def assign_face(
    embedding: np.ndarray,
    named_centroids: Mapping[str, np.ndarray],
    groups: Sequence[FaceGroupCentroid],
    suggest_threshold: float = DEFAULT_SUGGEST_THRESHOLD,
    cluster_threshold: float = DEFAULT_CLUSTER_THRESHOLD,
) -> AssignmentResult:
    """Egy ÚJ (névtelen) arc lenyomatának besorolása a modul-docstring
    algoritmusa szerint.

    FONTOS: ez a függvény csak NÉVTELEN arcokra hívható — a hívó
    (`picasapy.index.face_groups.group_unnamed_faces`) felel azért, hogy
    már elnevezett/ismert arc lenyomata SOHA ne kerüljön ide (issue #26
    alapszabálya: a meglévő `faces=` hozzárendeléseket a csoportosítás nem
    értékeli újra)."""
    best_name: str | None = None
    best_name_similarity = -1.0
    for name, centroid in named_centroids.items():
        similarity = cosine_similarity(embedding, centroid)
        if similarity > best_name_similarity:
            best_name_similarity = similarity
            best_name = name
    if best_name is not None and best_name_similarity >= suggest_threshold:
        return AssignmentResult(
            kind="suggestion",
            suggested_name=best_name,
            similarity=best_name_similarity,
        )

    best_group: FaceGroupCentroid | None = None
    best_group_similarity = -1.0
    for group in groups:
        similarity = cosine_similarity(embedding, group.centroid)
        if similarity > best_group_similarity:
            best_group_similarity = similarity
            best_group = group
    if best_group is not None and best_group_similarity >= cluster_threshold:
        updated_centroid = _weighted_centroid(
            best_group.centroid, best_group.face_count, embedding
        )
        return AssignmentResult(
            kind="grouped",
            group_id=best_group.group_id,
            new_centroid=updated_centroid,
            similarity=best_group_similarity,
        )

    return AssignmentResult(
        kind="new_group", new_centroid=np.asarray(embedding, dtype=np.float32)
    )
