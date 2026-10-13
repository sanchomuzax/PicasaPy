"""#4534 — a fotó-rács végéig kijelölt képek új testvérmappába kerülnek."""

from __future__ import annotations

from pathlib import Path

from picasapy.ini import (
    load_or_empty,
    parse_document,
    read_folder_date_override,
    read_folder_music,
    save_document,
)
from support.jpeg_factory import make_jpeg


def _source_ini(folder: Path, names: list[str]) -> None:
    document = parse_document("")
    document = document.with_value("Picasa", "description", "Régi leírás")
    document = document.with_value("Picasa", "location", "Régi hely")
    for name in names:
        document = document.with_value(name, "star", "1")
        document = document.with_value(name, "caption", f"Felirat {name}")
        document = document.with_value(name, "filters", "sepia=1;")
        document = document.with_value(name, "faces", "rect64(abc),Személy;")
        document = document.with_value(name, "albums", "album-token")
        document = document.with_value(name, "vendor", "megőrzendő")
    save_document(document, folder / ".picasa.ini")


def test_split_folder_creates_unique_sibling_and_moves_metadata(qt_app, tmp_path):
    from picasapy.app.fileops_controller import FileOpsController

    library = tmp_path / "library"
    source = library / "forras"
    source.mkdir(parents=True)
    names = [f"{index:02}.jpg" for index in range(1, 7)]
    paths = []
    for name in names:
        path = source / name
        make_jpeg(path)
        paths.append(path)
    _source_ini(source, names)
    (source / "jegyzet.txt").write_text("marad", encoding="utf-8")
    thm = source / "05.THM"
    thm.write_bytes(b"video thumbnail companion")
    originals = source / ".picasaoriginals"
    originals.mkdir()
    (originals / "04.jpg").write_bytes(b"preserved original")

    collision = library / "cut folder"
    collision.mkdir()
    (collision / "sentinel.txt").write_text("érintetlen", encoding="utf-8")

    controller = FileOpsController()
    moved: list[tuple[str, str]] = []
    failures: list[tuple[str, str]] = []
    controller.photoMoved.connect(lambda old, new: moved.append((old, new)))
    controller.operationFailed.connect(
        lambda operation, message: failures.append((operation, message))
    )

    split = getattr(controller, "splitFolderHere", None)
    assert callable(split), "hiányzik a FolderPhoto felosztás vezérlőútja"
    split(
        [str(path) for path in paths[2:]],
        "cut? folder",
        "2025-05-03",
        "Lake",
        "Új leírás",
        True,
        str(tmp_path / "music.mp3"),
    )

    target = library / "cut folder_1"
    assert failures == []
    assert target.is_dir(), "az új mappa a forrás testvére legyen"
    assert source.is_dir(), "a régi mappának üresen is meg kell maradnia"
    assert (source / "jegyzet.txt").read_text(encoding="utf-8") == "marad"
    assert (collision / "sentinel.txt").read_text(encoding="utf-8") == "érintetlen"
    assert sorted(path.name for path in source.glob("*.jpg")) == names[:2]
    assert sorted(path.name for path in target.glob("*.jpg")) == names[2:]
    assert not thm.exists()
    assert (target / thm.name).read_bytes() == b"video thumbnail companion"
    assert not (originals / "04.jpg").exists()
    assert (target / ".picasaoriginals" / "04.jpg").read_bytes() == b"preserved original"
    assert moved == [
        (str(path), str(target / path.name)) for path in paths[2:]
    ]

    source_doc = load_or_empty(source / ".picasa.ini")
    target_doc = load_or_empty(target / ".picasa.ini")
    assert source_doc.section("Picasa").get("description") == "Régi leírás"
    assert source_doc.section("Picasa").get("location") == "Régi hely"
    assert [section.name for section in source_doc.file_sections()] == names[:2]
    assert [section.name for section in target_doc.file_sections()] == names[2:]
    for name in names[2:]:
        section = target_doc.section(name)
        assert section.get("star") == "1"
        assert section.get("caption") == f"Felirat {name}"
        assert section.get("filters") == "sepia=1;"
        assert section.get("faces") == "rect64(abc),Személy;"
        assert section.get("albums") == "album-token"
        assert section.get("vendor") == "megőrzendő"
    target_folder_metadata = target_doc.section("Picasa")
    assert target_folder_metadata.get("description") == "Új leírás"
    assert target_folder_metadata.get("location") == "Lake"
    assert read_folder_date_override(target_doc) == "2025-05-03"
    assert read_folder_music(target_doc) == (True, str(tmp_path / "music.mp3"))


def test_empty_split_selection_does_not_create_a_folder(qt_app, tmp_path):
    from picasapy.app.fileops_controller import FileOpsController

    controller = FileOpsController()
    failures: list[tuple[str, str]] = []
    controller.operationFailed.connect(
        lambda operation, message: failures.append((operation, message))
    )
    split = getattr(controller, "splitFolderHere", None)
    assert callable(split), "hiányzik a FolderPhoto felosztás vezérlőútja"
    split([], "Névtelen", "2025-05-03", "", "", False, "")
    assert failures == []
    assert list(tmp_path.iterdir()) == []


def test_photo_moved_is_emitted_before_the_thm_companion_moves(qt_app, tmp_path):
    from picasapy.app.fileops_controller import FileOpsController

    library = tmp_path / "library"
    source = library / "forras"
    source.mkdir(parents=True)
    photo = source / "05.jpg"
    make_jpeg(photo)
    thm = source / "05.THM"
    thm.write_bytes(b"thumbnail companion")

    controller = FileOpsController()
    companion_at_emit: list[bool] = []
    controller.photoMoved.connect(
        lambda old, new: companion_at_emit.append(thm.exists())
    )

    controller.splitFolderHere(
        [str(photo)], "cut folder", "2025-05-03", "", "", False, ""
    )

    assert companion_at_emit == [True], "a fő mozgatás után, a THM előtt jelezzen"
    assert not thm.exists()
    assert (library / "cut folder" / "05.THM").read_bytes() == b"thumbnail companion"


def test_video_thm_companion_moves_with_the_video(qt_app, tmp_path):
    from picasapy.app.fileops_controller import FileOpsController

    library = tmp_path / "library"
    source = library / "forras"
    source.mkdir(parents=True)
    clip = source / "clip.mp4"
    clip.write_bytes(b"video")
    (source / "clip.THM").write_bytes(b"video thumbnail companion")

    controller = FileOpsController()
    controller.splitFolderHere([str(clip)], "video klip", "2025-05-03", "", "", False, "")

    target = library / "video klip"
    assert (target / "clip.mp4").read_bytes() == b"video"
    assert (target / "clip.THM").read_bytes() == b"video thumbnail companion"
    assert not (source / "clip.THM").exists()


def test_thm_stays_when_a_same_named_file_stays_behind(qt_app, tmp_path):
    from picasapy.app.fileops_controller import FileOpsController

    library = tmp_path / "library"
    source = library / "forras"
    source.mkdir(parents=True)
    photo = source / "IMG.JPG"
    photo.write_bytes(b"jpeg")
    (source / "IMG.MOV").write_bytes(b"video")
    (source / "IMG.THM").write_bytes(b"companion")

    controller = FileOpsController()
    controller.splitFolderHere([str(photo)], "kepek", "2025-05-03", "", "", False, "")

    target = library / "kepek"
    assert (target / "IMG.JPG").read_bytes() == b"jpeg"
    assert (source / "IMG.MOV").exists()
    assert (source / "IMG.THM").read_bytes() == b"companion"
    assert not (target / "IMG.THM").exists()
