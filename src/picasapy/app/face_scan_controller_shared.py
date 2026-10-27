# ruff: noqa: F401 -- module namespace is shared by themed mixins and the legacy façade.
"""Közös függőségek és segédfüggvények az arcfelismerés-vezérlő mixinjeihez."""


from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QSettings, Property, QLocale, QObject, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from picasapy.cvimage import dekodolj_forrast, scale_down
from picasapy.faces import detector as detector_module
from picasapy.faces import embedder as embedder_module
from picasapy.faces import model_download
from picasapy.faces.detector import FaceDetector, rescale_face_detection
from picasapy.faces.embedder import FaceEmbedder
from picasapy.faces.clustering import (
    CLUSTER_CALIBRATION_STEP,
    DEFAULT_CLUSTER_STEP,
    DEFAULT_SUGGEST_STEP,
    PICASA_STEPS,
    cluster_step_to_threshold,
    step_to_threshold,
    threshold_to_cluster_step,
)
from picasapy.export import export_sidecar_for_photo
from picasapy.index import (
    PhotoRecord,
    album_photos,
    all_photos,
    clear_faces,
    faces_for_photo,
    faces_missing_embedding,
    ignored_faces,
    group_unnamed_faces,
    ignored_ini_faces,
    javaslatokat_ujraszamol,
    lazitott_lepcso,
    mark_faces_ignored,
    set_suggested_name,
    suggested_faces_for,
    unignore_faces,
    mark_faces_named,
    open_index,
    photos_in_folder,
    face_scan_done,
    forget_face_scan,
    mark_face_scan,
    replace_faces,
    reset_all_faces as reset_all_faces_in_index,
    store_embedding,
    sync_tree,
    unnamed_album_photos,
    unnamed_faces,
)
from picasapy.index.faces_detected import UnnamedFace
from picasapy.index.hidden_scope import hidden_folders_visible
from picasapy.index.ignored_ini_faces import IniIgnoredFace
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

from .face_ignore_ini import (
    best_region,
    ignored_regions,
    ini_face_key,
    ini_faces_of,
    match_named_regions,
    match_regions,
    parse_ini_face_key,
    quantize_rect,
)
from .arc_nagyitas_url import arc_cimke
from .filetype_preferences import enabled_filetypes as load_enabled_filetypes
from .faces_helper import FacesHelper
from .worker_thread import BackgroundWorkerMixin
from .display_mode_paint import current_display_mode_suffix

_log = logging.getLogger(__name__)

# A detektálás bemenetének célmérete — a thumbs-cache alapértelmezett
# méreténél (256) nagyobb, hogy a kisebb arcok is megtalálhatók legyenek,
# de nem a teljes felbontás (nagy fotóknál ez percekre lassítaná a
# szkennelést). A YuNet kis felbontáson is jól teljesít (issue #26).
_DETECT_MAX_DIMENSION = detector_module.MAX_DETECTION_DIMENSION

# #26 (3. lépcső): egy csoportban ennyi arcot mutatunk „Expand groups"
# kikapcsolt állapotban — a teljes csoport a bekapcsolt állapotban látszik
# (ld. `unnamedGroups()`). Csak megjelenítési korlát, a kijelölés/névadás
# a NEM mutatott arcokat is eléri (a hívó a mutatott faceId-kat kapja meg,
# tehát ez a korlát a gyakorlatban a kijelölhető halmazt is szűkíti —
# szándékosan: „Expand groups" nélkül a felhasználó a reprezentatív
# részhalmazt nevezi el, ami a Picasa csoport-előnézetének felel meg).
_COLLAPSED_GROUP_PREVIEW = 12


def _path_key(path: str | Path) -> str:
    """A fájlútvonal platformhelyes összehasonlító alakja."""
    return os.path.normcase(os.path.normpath(str(path)))




def _group_payload(faces, label: str) -> dict:
    """Egy `unnamedGroups()`-csoport QML-alakja — a bélyegkép ugyanazt a
    `image://thumbs/<photo_id>` szolgáltatót használja, mint a fő rács
    (ld. `app/models.py:_thumb_url`), forgatás-/szűrő-érzékeny cache-
    buster NÉLKÜL (a Névtelenek albumban ez nem kritikus)."""
    return {
        "label": label,
        "faces": [_face_tile_payload(face) for face in faces],
    }


def _face_tile_payload(face) -> dict:
    """Egy névtelen csempe URL-je arc-kivágással, a közös thumb-provideren."""
    thumb_url = f"image://thumbs/{face.photo_id}"
    if face.rect is not None:
        # A `?&fz=` mellett a provider a PhotoRecordból veszi az elforgatást;
        # nem írunk rá mesterséges `r=0` értéket. A megjelenítési mód marad
        # a szokásos URL-rész, ahogy a teljes képes csempén is volt.
        thumb_url += f"?{arc_cimke(face.rect)}"
    thumb_url += current_display_mode_suffix()
    return {
        "faceId": face.id,
        "thumbUrl": thumb_url,
        # #26 (4. lépcső): a MÉG EL NEM DÖNTÖTT név-javaslat. Az eredeti
        # kérdésként vetette fel (`PeoplePanel::SuggestionFmt` = „%s?"),
        # pipa/x gombbal.
        "suggestedName": face.suggested_name or "",
    }


def _mark_previously_ignored(conn, photo_id: int, ini_faces) -> None:
    """#3670, „kész, ha" 4. pont: a `.picasa.ini`-ben MÁR mellőzöttként
    (`faces=…,ffffffffffffffff`) jelölt régiók saját találatai `'ignored'`
    állapotba kerülnek — egy újraindexelés ne dobja vissza őket a
    „Névtelenek" közé.

    Átfedés alapú, páronkénti egyeztetés (`face_ignore_ini`): a Picasa
    kerete a miénknél mérten nagyobb, bitre sosem egyezik. Egy régió
    legfeljebb egy találatot visz, és csak a még névtelent fordítja át —
    a fotó többi arca névtelen marad."""
    regions = ignored_regions(ini_faces)
    if not regions:
        return
    faces = [face for face in faces_for_photo(conn, photo_id) if face.rect is not None]
    matched = match_regions([(face.id, face.rect) for face in faces], regions)
    unnamed_ids = [face.id for face in faces if face.id in matched and face.state == "unnamed"]
    if unnamed_ids:
        mark_faces_ignored(conn, unnamed_ids)


def _ini_only(
    own: tuple[UnnamedFace, ...] | list[UnnamedFace],
    ini_faces: tuple[IniIgnoredFace, ...],
) -> list[IniIgnoredFace]:
    """Az ini-ben mellőzött arcok közül azok, amelyeket egyetlen saját,
    mellőzött találat sem fed át (#3670, B2) — a többit a saját sor
    képviseli az albumban, így egy arc nem jelenik meg kétszer."""
    own_by_photo: dict[int, list[UnnamedFace]] = {}
    for face in own:
        if face.rect is not None:
            own_by_photo.setdefault(face.photo_id, []).append(face)
    ini_by_photo: dict[int, list[IniIgnoredFace]] = {}
    for item in ini_faces:
        ini_by_photo.setdefault(item.photo_id, []).append(item)
    result: list[IniIgnoredFace] = []
    for photo_id, items in ini_by_photo.items():
        mine = own_by_photo.get(photo_id, [])
        used = set(
            match_regions([(face.id, face.rect) for face in mine], [i.rect for i in items]).values()
        )
        result.extend(item for item in items if item.rect not in used)
    return result


def _ini_face_payload(item: IniIgnoredFace) -> dict:
    """Egy csak az ini-ben mellőzött arc az album QML-alakjában."""
    return {
        "faceId": ini_face_key(item.photo_id, item.rect),
        "thumbUrl": f"image://thumbs/{item.photo_id}{current_display_mode_suffix()}",
        "suggestedName": "",
    }


def _photo_paths(conn, photo_ids: set[int]) -> dict[int, Path]:
    """Fotó-azonosító → teljes útvonal, a megadott azonosítókra."""
    if not photo_ids:
        return {}
    ids = sorted(photo_ids)
    rows = conn.execute(
        "SELECT p.id, fo.path AS folder_path, p.name FROM photos p "
        "JOIN folders fo ON fo.id = p.folder_id "
        f"WHERE p.id IN ({','.join('?' * len(ids))})",
        ids,
    )
    return {int(row["id"]): Path(row["folder_path"]) / row["name"] for row in rows}
