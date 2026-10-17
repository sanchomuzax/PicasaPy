"""#5180: a deferredface ismeretlen régiói a Név nélküliek indexébe kerülnek."""

from __future__ import annotations

import pytest

from picasapy.app.picasa_import_controller import PicasaImportController
from picasapy.index import (
    faces_missing_embedding,
    open_index,
    sync_tree,
    unnamed_faces,
)
from support.jpeg_factory import make_jpeg
from support.pmp_factory import build_pmp_column, build_thumb_index


def test_ffff_deferredface_a_nevtelenek_indexebe_kerul(tmp_path, qt_app):
    library = tmp_path / "kepek"
    library.mkdir()
    make_jpeg(library / "a.jpg")

    db3 = tmp_path / "db3"
    db3.mkdir()
    (db3 / "thumbindex.db").write_bytes(
        build_thumb_index(
            [("C:\\Pictures", None), ("a.jpg", 0)],
        )
    )
    rect = "5000600070008000"
    (db3 / "imagedata_deferredface.pmp").write_bytes(
        build_pmp_column(0x0, ["", f"rect64({rect}),ffffffffffffffff;"])
    )
    (db3 / "imagedata_deferredregion.pmp").write_bytes(
        build_pmp_column(0x0, ["", f"rect64({rect}),Régi pillanatképnév;"])
    )

    index_path = tmp_path / "index.db"
    with open_index(index_path) as conn:
        sync_tree(conn, library)
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()[0]

    controller = PicasaImportController(index_path=index_path)
    controller.startManualImport(str(db3), "C:\\Pictures", str(library))
    assert controller.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()

    with open_index(index_path) as conn:
        imported = [face for face in unnamed_faces(conn) if face.photo_id == photo_id]
        pending = faces_missing_embedding(conn)
    assert len(imported) == 1
    assert imported[0].rect is not None
    assert imported[0].state == "unnamed"
    assert imported[0].rect == pytest.approx((0.3125, 0.375, 0.4375, 0.5))
    assert pending == ()
