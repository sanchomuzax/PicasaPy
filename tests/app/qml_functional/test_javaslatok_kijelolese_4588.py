"""#4588: a személy-album fejlécéből kijelölhetők a javaslatok."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.index import open_index, replace_faces, sync_tree
from picasapy.index.faces_detected import set_suggested_name
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre


_LANDMARKS = FaceLandmarks(
    right_eye=(2.0, 2.0),
    left_eye=(4.0, 2.0),
    nose=(3.0, 3.0),
    mouth_right=(2.0, 3.5),
    mouth_left=(4.0, 3.5),
)


def _face(offset: float) -> FaceDetection:
    return FaceDetection(
        left=1.0 + offset,
        top=1.0,
        right=5.0 + offset,
        bottom=4.0,
        score=0.9,
        landmarks=_LANDMARKS,
    )


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _visual_item(root, name):
    return next(
        (item for item in _walk(root.contentItem())
         if item.objectName() == name),
        None,
    )


def _lathato_gomb(root, name):
    item = _visual_item(root, name)
    return (
        item is not None
        and item.isVisible()
        and item.width() > 0
        and item.height() > 0
    )


def _lista_property(root, name):
    value = root.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click(window, item):
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _photo_rows(controller, paths):
    return sorted(controller.photos.rowOfPath(path) for path in paths)


def test_a_szemely_album_gombja_kijeloli_es_a_muveletek_ezt_hasznaljak(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    root = tmp_path / "kepek"
    for name in ("c.jpg", "d.jpg", "e.jpg", "f.jpg", "g.jpg"):
        make_jpeg(root / name)

    db = tmp_path / "index.db"
    names = {
        "Anna": ("a.jpg", "b.jpg"),
        "Béla": ("c.jpg", "d.jpg"),
        "Cora": ("e.jpg", "f.jpg"),
    }
    face_ids = {}
    with open_index(db) as conn:
        sync_tree(conn, root)
        photo_ids = {
            row["name"]: row["id"]
            for row in conn.execute("SELECT id, name FROM photos")
        }
        for person, photos in names.items():
            for offset, photo_name in enumerate(photos):
                arcok = (
                    [_face(0.0), _face(10.0)]
                    if person == "Anna" and photo_name == "a.jpg"
                    else [_face(float(offset * 10))]
                )
                replace_faces(
                    conn,
                    photo_ids[photo_name],
                    arcok,
                )
        replace_faces(conn, photo_ids["g.jpg"], [_face(0.0)])
        conn.commit()
        photo_id_to_name = {photo_id: name for name, photo_id in photo_ids.items()}
        megerositett_arc = None
        for row in conn.execute("SELECT id, photo_id FROM face"):
            photo_name = photo_id_to_name[row["photo_id"]]
            if photo_name == "g.jpg":
                megerositett_arc = row["id"]
                continue
            person = next(
                person for person, photos in names.items()
                if photo_name in photos
            )
            set_suggested_name(conn, row["id"], person)
            face_ids.setdefault(person, []).append(row["id"])
        conn.commit()

    face_scan = window.property("_faceScanController")
    assert face_scan is not None
    assert megerositett_arc is not None
    face_scan.setPersistFaceToFile(False)
    assert face_scan.assignNameToFaces([megerositett_arc], "Anna")
    controller._reload_after_sync()

    eredeti_magassag = int(window.height())
    muveletek = (
        (-5, "Anna", "headerConfirmSuggestionsButton"),
        (0, "Béla", "headerRemoveSuggestionsButton"),
        (5, "Cora", None),
    )
    javaslat_darabszam = {"Anna": 3, "Béla": 2, "Cora": 2}
    for eltol, person, muvelet_gomb in muveletek:
        cel_magassag = eredeti_magassag + eltol
        window.setHeight(cel_magassag)
        assert varj_feltetelre(
            qt_app, lambda cel=cel_magassag: int(window.height()) == cel, 3.0
        )

        controller.showPerson(person)
        assert varj_feltetelre(
            qt_app,
            lambda nev=person: str(controller.currentPersonName) == nev
            and int(window.property("personSuggestionCount"))
            == javaslat_darabszam[nev],
            3.0,
        )

        assert varj_feltetelre(
            qt_app,
            lambda: _lathato_gomb(window, "headerSelectSuggestionsButton"),
            3.0,
        )
        kijelolo = _visual_item(window, "headerSelectSuggestionsButton")
        assert kijelolo is not None and kijelolo.isVisible()
        assert kijelolo.width() > 0 and kijelolo.height() > 0
        _click(window, kijelolo)

        vart_sorok = _photo_rows(
            controller, [str(root / photo) for photo in names[person]]
        )
        assert varj_feltetelre(
            qt_app,
            lambda vart=vart_sorok:
                _lista_property(window, "selectedIndexes") == vart,
            3.0,
        )
        assert set(_lista_property(window, "personSelectedSuggestionIds")) == set(
            face_ids[person]
        )

        if muvelet_gomb is None:
            continue
        muvelet = _visual_item(window, muvelet_gomb)
        assert muvelet is not None and muvelet.isVisible()
        _click(window, muvelet)
        assert varj_feltetelre(
            qt_app,
            lambda nev=person: face_scan.personSuggestionCount(nev) == 0,
            3.0,
        )
