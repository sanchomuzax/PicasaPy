"""#4573: az Emberek-panel névtelen arca javaslatot is fogad vagy vet el."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from picasapy.index.faces_detected import set_suggested_name
from support.qt_wait import varj_feltetelre
from test_people_panel_new_person_4522 import (
    _named_item,
    _prepare_panel,
)


def _click(window, item):
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _walk_items(item):
    for child in item.childItems():
        yield child
        yield from _walk_items(child)


def _dialog_button(window, qt_app, text):
    def find_button():
        return next(
            (
                item
                for item in _walk_items(window.contentItem())
                if item.property("text") == text
                and item.isVisible()
                and item.width() > 0
                and item.metaObject().indexOfSignal("clicked()") >= 0
            ),
            None,
        )

    assert varj_feltetelre(qt_app, lambda: find_button() is not None, 3.0)
    return find_button()


def test_unnamed_face_suggestion_can_be_accepted_or_rejected_in_people_panel(
    qml_app_valodi_belyegkep, qt_app, tmp_path
):
    window, controller, panel, _library, _photo, _row, face_ids = _prepare_panel(
        qml_app_valodi_belyegkep, qt_app, tmp_path
    )
    assert len(face_ids) == 2
    rejected_id, accepted_id = face_ids
    with open_index(controller._db_path) as conn:
        set_suggested_name(conn, rejected_id, "Ada Lovelace")
        set_suggested_name(conn, accepted_id, "Grace Hopper")
        conn.commit()

    face_scan = window.property("_faceScanController")
    assert face_scan is not None
    face_scan.unnamedCountChanged.emit()
    window.setHeight(1024)
    assert varj_feltetelre(qt_app, lambda: int(window.height()) == 1024, 3.0)
    original_height = int(window.height())

    shot_dir = tmp_path / "4573-shots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    for delta in (-5, 0, 5):
        window.setHeight(original_height + delta)
        assert varj_feltetelre(
            qt_app,
            lambda target=original_height + delta:
                int(window.height()) == target,
            3.0,
        )
        row = _named_item(panel, f"peoplePanelFaceRow_{rejected_id}")
        face_image = _named_item(
            panel, f"peoplePanelFaceImage_{rejected_id}"
        )
        yes = _named_item(panel, f"peoplePanelSuggestionYes_{rejected_id}")
        no = _named_item(panel, f"peoplePanelSuggestionNo_{rejected_id}")
        suggestion = _named_item(
            panel, f"peoplePanelSuggestionName_{rejected_id}"
        )
        assert row is not None and row.isVisible()
        assert face_image is not None and face_image.isVisible()
        assert yes is not None and yes.isVisible()
        assert no is not None and no.isVisible()
        assert suggestion is not None and suggestion.property("text") == "Ada Lovelace?"
        assert (round(yes.width()), round(yes.height())) == (27, 22)
        assert (round(no.width()), round(no.height())) == (27, 22)
        yes_pos = yes.mapToItem(panel, QPointF(0, 0))
        no_pos = no.mapToItem(panel, QPointF(0, 0))
        face_right = face_image.mapToItem(
            panel, QPointF(face_image.width(), 0)
        )
        assert abs(yes_pos.x() - face_right.x()) <= 3
        assert abs((no_pos.x() - yes_pos.x()) - 32) <= 3

        if delta == 0:
            rendered = window.grabWindow()
            assert not rendered.isNull()
            rendered.save(str(shot_dir / "unnamed-row-window.png"))
            origin = row.mapToScene(QPointF(0, 0))
            crop = rendered.copy(
                round(origin.x()),
                round(origin.y()),
                round(row.width()),
                round(row.height()),
            )
            assert not crop.isNull()
            crop.save(str(shot_dir / "unnamed-row.png"))

    window.setHeight(original_height)
    assert varj_feltetelre(
        qt_app, lambda: int(window.height()) == original_height, 3.0
    )

    no = _named_item(panel, f"peoplePanelSuggestionNo_{rejected_id}")
    assert no is not None and no.isVisible()
    _click(window, no)
    assert varj_feltetelre(
        qt_app,
        lambda: (
            (item := _named_item(
                panel, f"peoplePanelSuggestionNo_{rejected_id}"
            )) is None
            or not item.isVisible()
        ),
        3.0,
    )
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT state, suggested_name FROM face WHERE id = ?",
            (rejected_id,),
        ).fetchone()
    assert row["state"] != "named"
    assert row["suggested_name"] is None

    ignore = _named_item(panel, f"peoplePanelIgnoreX_{rejected_id}")
    assert ignore is not None and ignore.isVisible()
    _click(window, ignore)
    _click(window, _dialog_button(window, qt_app, "Ignore Person"))
    assert varj_feltetelre(
        qt_app,
        lambda: _named_item(panel, f"peoplePanelFaceRow_{rejected_id}") is None,
        3.0,
    )
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT state, suggested_name FROM face WHERE id = ?",
            (rejected_id,),
        ).fetchone()
    assert row["state"] == "ignored"
    assert row["suggested_name"] is None

    yes = _named_item(panel, f"peoplePanelSuggestionYes_{accepted_id}")
    assert yes is not None and yes.isVisible()
    _click(window, yes)
    assert varj_feltetelre(
        qt_app,
        lambda: _named_item(panel, f"peoplePanelFaceRow_{accepted_id}") is None,
        3.0,
    )
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT state, person_name, suggested_name FROM face WHERE id = ?",
            (accepted_id,),
        ).fetchone()
    assert row["state"] == "named"
    assert row["person_name"] == "Grace Hopper"
    assert row["suggested_name"] is None
