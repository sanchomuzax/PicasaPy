"""WebExportController (#351) — a `picasapy.webexport` motor QML-hídja.

A `test_relocate_controller.py` mintáját követi: valódi ideiglenes
könyvtárral, mock nélkül, valódi eseményhurok-várakozással a
háttérszálas eredményre."""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.webexport_controller import WebExportController
from picasapy.index import PhotoRecord
from support.jpeg_factory import make_jpeg
from support.qt_wait import hangos_hurok


def _quit_on(signal):
    """Eseményhurok, amit a `signal` érkezése zár le — HANGOS vészfékkel.

    #1467: a korábbi `QTimer.singleShot(5000, loop.quit)` NÉMÁN engedte
    tovább a tesztet, ha az idő járt le: a bukás egy későbbi, látszólag
    független állításon jelentkezett, vagy a teszt véletlenül zöld maradt.
    A közös segéd az `exec()`-ben, ott helyben bukik, beszédes üzenettel."""
    return hangos_hurok(signal)


def _record(folder, name, **overrides):
    path = folder / name
    if not path.exists():
        make_jpeg(path, size=(80, 60))
    defaults = dict(
        id=1, folder_path=str(folder), name=name, kind="photo",
        size=path.stat().st_size, mtime_ns=0, star=False, caption=None,
        keywords=None, rotate_steps=0, filters=None, taken_at=None,
        orientation=1, width=80, height=60,
    )
    defaults.update(overrides)
    return PhotoRecord(**defaults)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    return root


@pytest.fixture
def make_controller(qt_app):
    """`WebExportController`-gyár, ami a teszt végén MEGVÁRJA a háttérszálat.

    A generálás daemon-szálon fut: ha a teszt (vagy maga a processz) a szál
    alatt ér véget, a szál a Qt/Python leépítése közben emitálna jelzést egy
    már felszámolt objektumnak — ez a #430-as, futásonként változó SIGSEGV.
    A determinista leépítés ezért a fixture felelőssége."""
    created: list[WebExportController] = []

    def _make(photo_source, settings=None):
        controller = WebExportController(photo_source=photo_source, settings=settings)
        created.append(controller)
        return controller

    yield _make

    for controller in created:
        assert controller.waitForExport(30.0), "a webexport háttérszál nem állt le"


@pytest.fixture
def controller(make_controller, library):
    photos = [_record(library, "a.jpg", caption="Kutya"), _record(library, "b.jpg")]
    return make_controller(lambda: photos)


class TestListWebExportTemplates:
    def test_includes_bundled_feher_template(self, controller):
        templates = controller.listWebExportTemplates()
        ids = [t["id"] for t in templates]
        assert "feher" in ids
        assert all({"id", "name", "description"} <= set(t) for t in templates)


class TestGenerateWebExportValidation:
    def test_missing_target_emits_failure_synchronously(self, controller):
        seen = []
        controller.webExportFailed.connect(seen.append)
        controller.generateWebExport("", "feher", "Album", 0, False)
        assert seen

    def test_unknown_template_emits_failure_synchronously(self, controller, tmp_path):
        seen = []
        controller.webExportFailed.connect(seen.append)
        controller.generateWebExport(
            str(tmp_path / "out"), "nemletezik", "Album", 0, False
        )
        assert seen

    def test_empty_photo_source_emits_failure(self, make_controller, tmp_path):
        controller = make_controller(lambda: [])
        seen = []
        controller.webExportFailed.connect(seen.append)
        controller.generateWebExport(
            str(tmp_path / "out"), "feher", "Album", 0, False
        )
        assert seen


class TestGenerateWebExportSuccess:
    def test_full_run_emits_finished_with_output_files(self, controller, tmp_path):
        target = tmp_path / "kimenet"
        finished = []
        controller.webExportFinished.connect(
            lambda out_dir, count: finished.append((out_dir, count))
        )
        loop = _quit_on(controller.webExportFinished)
        controller.generateWebExport(
            str(target), "feher", "Nyaralás", 2, False
        )
        loop.exec()

        assert len(finished) == 1
        out_dir, page_count = finished[0]
        assert out_dir == str(target)
        # 1 index oldal + 2 kép egyenkénti oldala (index0/index1)
        assert page_count == 3
        assert (target / "index.html").is_file()
        assert "Nyaralás" in (target / "index.html").read_text(encoding="utf-8")
        assert (target / "style.css").is_file()

    def test_progress_signal_reports_processed_count(self, controller, tmp_path):
        progress = []
        controller.webExportProgress.connect(lambda done, total: progress.append((done, total)))
        loop = _quit_on(controller.webExportFinished)
        controller.generateWebExport(
            str(tmp_path / "kimenet"), "feher", "Album", 0, False
        )
        loop.exec()
        assert progress == [(2, 2)]

    def test_video_only_selection_fails_after_image_generation(
        self, make_controller, library, tmp_path
    ):
        video_path = library / "v.mp4"
        video_path.write_bytes(b"nem-igazi-video")
        record = _record(library, "v.mp4", kind="video")
        controller = make_controller(lambda: [record])
        failed = []
        controller.webExportFailed.connect(failed.append)
        loop = _quit_on(controller.webExportFailed)
        controller.generateWebExport(
            str(tmp_path / "kimenet"), "feher", "Album", 0, False
        )
        loop.exec()
        assert failed


class TestBackgroundThreadTeardown:
    """#430: a háttérszál élettartama legyen determinista — se a teszt, se az
    alkalmazás ne érhessen véget úgy, hogy a szál még Qt-jelzést emitál."""

    def test_wait_for_export_without_a_run_returns_immediately(self, controller):
        assert controller.waitForExport(0.0)

    def test_wait_for_export_joins_the_worker_thread(self, controller, tmp_path):
        loop = _quit_on(controller.webExportFinished)
        controller.generateWebExport(
            str(tmp_path / "kimenet"), "feher", "Album", 0, False
        )
        loop.exec()
        assert controller.waitForExport(30.0)
        assert not controller.exportRunning()


class TestAzAlapertelmezettCelmappa:
    """#534: az eredetinek van alapértelmezett kimeneti mappája
    (`IDS_DEFAULT_WEB_EXPORT_PATH` — „Picasa HTML Exports\\"), nálunk a
    párbeszéd eddig „(nincs kijelölve)" állapotban nyílt, tehát minden
    exportnál tallózni kellett."""

    def test_a_rendszer_kepmappajabol_szarmazik(self, monkeypatch, tmp_path, controller):
        """A képmappát a RENDSZER adja (#1088) — nem `home()/Pictures`."""
        from picasapy.app import collage_output
        from picasapy.app import webexport_controller as modul

        # a nem windowsos út; a windowsos alapmappát (#5714) külön teszt méri
        monkeypatch.setattr(modul, "_platform", lambda: "linux")
        monkeypatch.setattr(collage_output, "pictures_dir", lambda: tmp_path / "Képek")
        assert controller.defaultWebExportTarget() == str(
            tmp_path / "Képek" / "Picasa HTML exportok"
        )

    def test_nem_hozza_letre_a_mappat(self, monkeypatch, tmp_path, controller):
        """Csak javaslat: aki megnyitja a párbeszédet és mégsem exportál, ne
        hagyjon üres mappát a képei közt."""
        from picasapy.app import collage_output

        monkeypatch.setattr(collage_output, "pictures_dir", lambda: tmp_path / "Képek")
        controller.defaultWebExportTarget()
        assert not (tmp_path / "Képek").exists()

    def test_windowson_a_personal_mappat_es_az_eredeti_nevet_hasznalja(
        self, monkeypatch, tmp_path, controller
    ):
        from picasapy.app import webexport_controller as modul

        hivasok = []
        monkeypatch.setattr(modul, "_platform", lambda: "win32")
        monkeypatch.setattr(
            modul.QStandardPaths,
            "writableLocation",
            lambda hely: hivasok.append(hely) or str(tmp_path / "Személyes"),
        )

        cel = controller.defaultWebExportTarget()

        assert Path(cel) == tmp_path / "Személyes" / "Picasa HTML Exports"
        assert hivasok == [modul.QStandardPaths.StandardLocation.DocumentsLocation]


class _MemSettings:
    """`value()`/`setValue()` páros a QSettings helyett (#4610)."""

    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):  # noqa: N802 — a QSettings neve
        self.values[key] = value


def _kep_merete(path):
    from picasapy.cvimage import dekodolj_forrast

    kep = dekodolj_forrast(path)
    assert kep is not None, f"nem olvasható: {path}"
    return max(kep.shape[:2])


class TestMeretvalasztoEsMozgokepMod4610:
    """#4610: egy méretválasztó (a nagy kép), a bélyegkép a sablonból (144),
    a mozgókép-mód és mindkettő megőrzése (`WebExportSize`/`WebExportMovie`,
    spec `picasa-menu-parancsok-viselkedes.md` 6.1)."""

    def test_alapertekek_640_es_elso_kepkocka(self, make_controller):
        controller = make_controller(lambda: [], settings=_MemSettings())
        assert controller.webExportPrefs() == {
            "sizeIndex": 3,
            "movieFull": False,
            "targetDir": "",
            "templateId": "",
        }

    def test_a_mentett_valasztas_visszajon(self, make_controller):
        tarolo = _MemSettings({"webexport/size": 4, "webexport/movieFull": "true"})
        controller = make_controller(lambda: [], settings=tarolo)
        assert controller.webExportPrefs() == {
            "sizeIndex": 4,
            "movieFull": True,
            "targetDir": "",
            "templateId": "",
        }

    def test_hibas_tarolt_ertek_az_alapertekre_esik(self, make_controller):
        tarolo = _MemSettings({"webexport/size": "x", "webexport/movieFull": None})
        controller = make_controller(lambda: [], settings=tarolo)
        assert controller.webExportPrefs() == {
            "sizeIndex": 3,
            "movieFull": False,
            "targetDir": "",
            "templateId": "",
        }

    def test_a_webexport_utvonalat_es_sablont_is_visszaadja(self, make_controller):
        tarolo = _MemSettings(
            {
                "webexport/targetDir": "/sajat/webexport",
                "webexport/templateId": "fekete",
            }
        )
        controller = make_controller(lambda: [], settings=tarolo)

        assert controller.webExportPrefs()["targetDir"] == "/sajat/webexport"
        assert controller.webExportPrefs()["templateId"] == "fekete"

    def test_valodi_qsettingsben_uj_vezerlonel_is_visszajon_a_cel_es_sablon(
        self, make_controller, library, tmp_path
    ):
        from PySide6.QtCore import QSettings

        photo = _record(library, "valodi.jpg")
        beallitasfajl = tmp_path / "webexport.ini"
        elso = make_controller(
            lambda: [photo],
            settings=QSettings(str(beallitasfajl), QSettings.Format.IniFormat),
        )
        cel = tmp_path / "webexport-kimenet"
        loop = _quit_on(elso.webExportFinished)
        elso.generateWebExport(str(cel), "feher", "Album", 3, False)
        loop.exec()
        assert elso.waitForExport(30.0)

        masodik = make_controller(
            lambda: [],
            settings=QSettings(str(beallitasfajl), QSettings.Format.IniFormat),
        )

        assert Path(masodik.webExportPrefs()["targetDir"]) == cel
        assert masodik.webExportPrefs()["templateId"] == "feher"

    def test_tablan_kivuli_tarolt_index_az_alapra_esik(self, make_controller):
        tarolo = _MemSettings({"webexport/size": 9})
        controller = make_controller(lambda: [], settings=tarolo)
        assert controller.webExportPrefs()["sizeIndex"] == 3

    def test_az_index_kepmeretet_ad_a_belyegkep_a_sablone(
        self, make_controller, library, tmp_path
    ):
        make_jpeg(library / "nagy.jpg", size=(1600, 1200))
        photos = [_record(library, "nagy.jpg", width=1600, height=1200)]
        tarolo = _MemSettings()
        controller = make_controller(lambda: photos, settings=tarolo)
        target = tmp_path / "kimenet"
        loop = _quit_on(controller.webExportFinished)
        # 4. index = „320 pixels (for email)"
        controller.generateWebExport(str(target), "feher", "A", 4, True)
        loop.exec()

        assert _kep_merete(target / "image" / "nagy.jpg") == 320
        assert _kep_merete(target / "thumbnail" / "nagy.jpg") == 144
        # a választás megmarad a következő megnyitásig
        mentett_cel = tarolo.values.pop("webexport/targetDir")
        assert Path(mentett_cel) == target
        assert tarolo.values == {
            "webexport/size": 4,
            "webexport/movieFull": True,
            "webexport/templateId": "feher",
        }

    def test_hibas_inditas_nem_ment(self, make_controller):
        tarolo = _MemSettings()
        controller = make_controller(lambda: [], settings=tarolo)
        controller.generateWebExport("", "feher", "A", 1, True)
        assert tarolo.values == {}


class TestArnyekASablonbol4849:
    """#4849: a vezérlő nem vár árnyék-értéket; a kimenetben a bélyegkép
    a sablon alapértéke szerint árnyékolt (`shadowedThumbnails` 1)."""

    def test_a_belyegkepek_arnyekosak_a_kep_nem(self, controller, tmp_path):
        target = tmp_path / "kimenet"
        loop = _quit_on(controller.webExportFinished)
        controller.generateWebExport(str(target), "feher", "A", 3, False)
        loop.exec()
        html = (target / "index.html").read_text(encoding="utf-8")
        assert 'class="thumb shadow"' in html
        assert 'class="item-figure shadow"' not in (
            target / "index0.html"
        ).read_text(encoding="utf-8")
