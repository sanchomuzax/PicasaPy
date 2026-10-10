"""#4564: a vágópanel Windows/macOS ága vezérlőhöz és exporthoz kapcsol."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

from picasapy.index import PhotoRecord


def _video(folder: Path) -> PhotoRecord:
    return PhotoRecord(
        id=7,
        folder_path=str(folder),
        name="forras.mp4",
        kind="video",
        size=1000,
        mtime_ns=5,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters="moviestart=4e20;movieend=13880;",
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
    )


class _Photos:
    _photos = (_video(Path("forras")),)

    @staticmethod
    def movieTrimAt(row):
        assert row == 0
        return {"start": 2000, "end": 8000}


class _BackgroundOwner:
    def _start_background(self, target, *, name=None, **_kwargs):
        self.worker_names.append(name)
        target()


def test_vezerlo_a_modelben_tarolt_vagast_exportalja(monkeypatch, tmp_path):
    from picasapy.app import movie_clip_export_controller as modul
    from picasapy.app.movie_clip_export_controller import MovieClipExportMixin

    calls = []
    exported = tmp_path / "forras.mp4"
    exported.touch()
    monkeypatch.setattr(modul, "exported_video_folder", lambda: tmp_path)

    def fake_export(source, folder, *, start_ms, end_ms):
        calls.append((source, folder, start_ms, end_ms))
        return exported

    monkeypatch.setattr(modul, "export_clip", fake_export)

    class Controller(MovieClipExportMixin, _BackgroundOwner, QObject):
        def __init__(self):
            QObject.__init__(self)
            self.photos = _Photos()
            self.worker_names = []

        def _vago_sor(self, row):
            assert row == 0
            return self.photos._photos[0]

    controller = Controller()
    emitted = []
    controller.movieClipExported.connect(emitted.append)
    controller.exportMovieClip(0)

    assert calls == [(Path("forras") / "forras.mp4", tmp_path, 2000, 8000)]
    assert emitted == [str(exported)]
    assert controller.worker_names == ["picasapy-export-movie-clip"]


def test_a_kimeneti_mappa_az_eredeti_honos_nevet_hasznalja(monkeypatch, tmp_path):
    from picasapy.app import movie_clip_export_controller as modul
    from picasapy.app.project_folder_names import ProjectFolderKind

    monkeypatch.setattr(modul, "pictures_dir", lambda: tmp_path)

    assert modul.exported_video_folder("hu") == (
        tmp_path / "Picasa" / "Exportált videoklipek"
    )
    assert modul.exported_video_folder("en") == (
        tmp_path / "Picasa" / "Exported Videos"
    )
    assert ProjectFolderKind.EXPORTED_VIDEOS.value == "exported_videos"


def test_a_linux_uzenet_megmarad_es_a_tobbi_platform_exportal():
    qml_path = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"
    )
    qml = qml_path.read_text(encoding="utf-8")
    handler = qml.split("onExportClipRequested:", 1)[1].split("\n                    }", 1)[0]

    assert 'Qt.platform.os === "linux"' in handler
    assert 'qsTr("This feature is not supported for Linux")' in handler
    assert "controller.exportMovieClip(viewer.currentIndex)" in handler
