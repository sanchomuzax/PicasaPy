"""A hálózati mappa lassú fájlműveletei nem foghatják a GUI-szálat (#6948)."""

from __future__ import annotations

import threading
import time

from picasapy.ini import parse_document
from picasapy.metadata import EMPTY_EXIF_DETAILS
from support.jpeg_factory import make_jpeg


def _lassu(muvelet, hivasok, delay=0.3):
    def fut(*args, **kwargs):
        hivasok.append(threading.get_ident())
        time.sleep(delay)
        return muvelet(*args, **kwargs)

    return fut


def test_begin_edit_halozaton_a_lemezmuveleteket_hatterszalra_tereli(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import edit_controller_preview_mixin as preview_module
    from picasapy.app import edit_controller_save_mixin as save_module
    from picasapy.app import edit_controller_session_mixin as session_module
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.ini import photo_crop

    photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(32, 24))
    main_thread = threading.get_ident()
    hivasok = []
    dokumentum = parse_document(
        "[IMG_0001.jpg]\nfilters=enhance=1;\n"
    )

    monkeypatch.setattr(
        session_module,
        "fajlrendszer_gyoker",
        lambda _path: r"\\teszt-nas\kepek",
    )
    monkeypatch.setattr(
        preview_module.EditControllerPreviewMixin,
        "_read_image_size",
        staticmethod(_lassu(lambda _path: (32, 24), hivasok)),
    )
    monkeypatch.setattr(
        session_module,
        "read_exif_details",
        _lassu(lambda _path: EMPTY_EXIF_DETAILS, hivasok),
    )
    monkeypatch.setattr(
        save_module,
        "load_or_empty",
        _lassu(lambda _path: dokumentum, hivasok),
    )
    monkeypatch.setattr(
        photo_crop,
        "load_or_empty",
        _lassu(lambda _path: dokumentum, hivasok),
    )

    controller = EditController(EditPreviewProvider())
    started = time.perf_counter()
    controller.beginEdit("1", str(photo))
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"a beginEdit {elapsed:.3f} s-ig fogta a hívó szálat"
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()
    assert hivasok, "a lassú műveleteket szimuláló fogantyúk nem futottak le"
    assert main_thread not in hivasok, (
        "a méret-, ini- vagy EXIF-olvasás a fő szálon futott"
    )
    assert controller.chainValue == "enhance=1;"
    assert controller._image_size == (32, 24)


def test_crop_suggestions_halozati_kepet_hatterszalon_dekodol(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import edit_controller_crop_mixin as crop_module
    from picasapy.app import edit_controller_session_mixin as session_module
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app import edit_preview_source

    photo = make_jpeg(tmp_path / "IMG_0002.jpg", size=(32, 24))
    controller = EditController(EditPreviewProvider())
    monkeypatch.setattr(
        session_module,
        "fajlrendszer_gyoker",
        lambda _path: r"\\teszt-nas\kepek",
    )
    controller.beginEdit("2", str(photo))
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()

    main_thread = threading.get_ident()
    hivasok = []
    original_decode = edit_preview_source._decode_source
    slow_decode = _lassu(original_decode, hivasok, delay=1.2)
    monkeypatch.setattr(
        edit_preview_source,
        "_decode_source",
        slow_decode,
    )
    monkeypatch.setattr(
        crop_module,
        "_decode_source",
        slow_decode,
    )
    monkeypatch.setattr(
        crop_module,
        "fajlrendszer_gyoker",
        lambda _path: r"\\teszt-nas\kepek",
    )

    started = time.perf_counter()
    elso_javaslatok = controller.cropSuggestions
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"a vágási javaslat {elapsed:.3f} s-ig blokkolt"
    assert isinstance(elso_javaslatok, list)
    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()
    assert hivasok
    assert main_thread not in hivasok
    assert controller.cropSuggestions


def _app_controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    folder = tmp_path / "kepek"
    folder.mkdir()
    make_jpeg(folder / "IMG_0001.jpg", size=(32, 24))
    (folder / ".picasa.ini").write_text(
        "[Picasa]\ndescription=NAS próba\n", encoding="utf-8"
    )
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, folder)
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue("view/showOnlyBigImages", False)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(folder),), provider, settings=settings)
    controller.selectFolder(str(folder))
    return controller, folder


def _wait_background(controller, qt_app):
    assert controller.waitForBackgroundWorkers(10.0), "háttérmunka nem fejeződött be"
    qt_app.processEvents()


def test_mappaleiras_halozaton_gyorsan_visszater_es_hatterszalrol_tolt(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import controller_content_info_mixin as content_module

    controller, folder = _app_controller(qt_app, tmp_path)
    controller._descriptions.pop(str(folder), None)
    main_thread = threading.get_ident()
    hivasok = []
    dokumentum = parse_document("[Picasa]\ndescription=NAS próba\n")
    monkeypatch.setattr(
        content_module,
        "halozati_gyoker",
        lambda _path: r"\\teszt-nas\kepek",
        raising=False,
    )
    monkeypatch.setattr(
        content_module,
        "load_or_empty",
        _lassu(lambda _path: dokumentum, hivasok, delay=1.2),
    )

    started = time.perf_counter()
    controller.selectFolder(str(folder))
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"a leíráskérés {elapsed:.3f} s-ig blokkolt"
    _wait_background(controller, qt_app)
    assert main_thread not in hivasok
    assert controller.folderDescriptionOf(str(folder)) == "NAS próba"


def test_tulajdonsagpanel_halozati_exifje_hatterszalrol_gyorsitotarra_kerul(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import controller_content_info_mixin as content_module
    from picasapy.app import formatting_properties as properties_module
    from picasapy.metadata import ExifDetails

    controller, folder = _app_controller(qt_app, tmp_path)
    monkeypatch.setattr(
        content_module,
        "halozati_gyoker",
        lambda _path: r"\\teszt-nas\kepek",
        raising=False,
    )
    main_thread = threading.get_ident()
    hivasok = []
    monkeypatch.setattr(
        properties_module,
        "read_exif_details",
        _lassu(lambda _path: ExifDetails(model="NAS kamera"), hivasok, delay=1.2),
    )

    started = time.perf_counter()
    elso = controller.propertiesOf(0)
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"a tulajdonságkérés {elapsed:.3f} s-ig blokkolt"
    _wait_background(controller, qt_app)
    assert main_thread not in hivasok
    masodik = controller.propertiesOf(0)
    assert ("Camera Model", "NAS kamera") in [
        (entry["label"], entry["value"]) for entry in masodik
    ]
    assert elso


def test_mentett_eredeti_ellenorzese_halozaton_hatterszalra_kerul(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import save_controller as save_module

    controller, folder = _app_controller(qt_app, tmp_path)
    originals = folder / ".picasaoriginals"
    originals.mkdir()
    (originals / "IMG_0001.jpg").write_bytes(b"original")
    main_thread = threading.get_ident()
    hivasok = []
    monkeypatch.setattr(
        save_module,
        "fajlrendszer_gyoker",
        lambda _path: str(tmp_path),
    )
    monkeypatch.setattr(
        save_module,
        "_konyvtar_tartalma",
        _lassu(lambda _folder: [originals / "IMG_0001.jpg"], hivasok, delay=1.2),
    )

    started = time.perf_counter()
    elso = controller.hasSavedBackup([0])
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"a mentés-ellenőrzés {elapsed:.3f} s-ig blokkolt"
    _wait_background(controller, qt_app)
    assert main_thread not in hivasok
    assert elso is False
    assert controller.hasSavedBackup([0]) is True


def test_eltunt_gyoker_ellenorzese_nem_fogja_a_foszalat(qt_app, tmp_path, monkeypatch):
    from picasapy.app import library_controller_eltunt_gyoker as root_module

    controller, _folder = _app_controller(qt_app, tmp_path)
    main_thread = threading.get_ident()
    hivasok = []
    monkeypatch.setattr(
        root_module,
        "watched_root_missing",
        _lassu(lambda _root: False, hivasok, delay=1.2),
    )
    started = time.perf_counter()
    controller._eltunt_gyokerek_rendezese()
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0, f"a gyökér-ellenőrzés {elapsed:.3f} s-ig blokkolt"
    _wait_background(controller, qt_app)
    assert hivasok
    assert main_thread not in hivasok



def test_betoltes_alatti_szerkesztes_a_betoltes_utan_lemezre_kerul(
    qt_app, tmp_path, monkeypatch
):
    """A hálózati ini beolvasása közben alkalmazott effekt nem veszhet el:
    a beolvasás után a meglévő lánc végére fűzve kiíródik."""
    from picasapy.app import edit_controller_preview_mixin as preview_module
    from picasapy.app import edit_controller_session_mixin as session_module
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.ini import load_or_empty

    photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(32, 24))
    (tmp_path / ".picasa.ini").write_text(
        "[IMG_0001.jpg]\nfilters=enhance=1;\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        session_module,
        "fajlrendszer_gyoker",
        lambda _path: r"\\teszt-nas\kepek",
    )
    monkeypatch.setattr(
        preview_module.EditControllerPreviewMixin,
        "_read_image_size",
        staticmethod(_lassu(lambda _path: (32, 24), [], delay=0.5)),
    )

    controller = EditController(EditPreviewProvider())
    controller.beginEdit("1", str(photo))
    assert controller._network_edit_load_pending
    controller.applyEffect("bw")

    assert controller.waitForBackgroundWorkers(5.0)
    qt_app.processEvents()

    section = load_or_empty(tmp_path / ".picasa.ini").section("IMG_0001.jpg")
    filters = section.get("filters") if section is not None else ""
    assert filters.startswith("enhance=1;"), filters
    assert "bw=1" in filters, f"a betöltés alatti effekt nem került lemezre: {filters!r}"
