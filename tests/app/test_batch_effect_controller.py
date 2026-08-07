"""`BatchEffectMixin` — Kép ▸ Csoportos szerkesztés (#425): a kijelölt N kép
mindegyikére egyszerre alkalmazott egykattintásos effekt, mappánkénti
kötegelt ini-írással, haladásjelzéssel, megszakíthatósággal és egyetlen
visszavonási lépéssel. A `test_rename_many_controller.py` fixtúra-mintáját
követi (AppController + QEventLoop, amíg a háttérszál végez)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    folder_a = root / "a"
    folder_b = root / "b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    make_jpeg(folder_a / "x.jpg", size=(800, 600))
    make_jpeg(folder_a / "y.jpg", size=(800, 600))
    make_jpeg(folder_b / "z.jpg", size=(800, 600))
    (folder_a / ".picasa.ini").write_text(
        "[x.jpg]\nfilters=sat=1,-0.2;\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    return ctl


def _rows_by_name(controller, *names) -> list:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[name] for name in names]


def _ini_text(folder) -> str:
    return (folder / "a" / ".picasa.ini").read_text(encoding="utf-8")


def _ini_text_b(folder) -> str:
    return (folder / "b" / ".picasa.ini").read_text(encoding="utf-8")


def _run(controller, action) -> None:
    loop = QEventLoop()
    controller.photoOpFinished.connect(loop.quit)
    action()
    QTimer.singleShot(5000, loop.quit)
    loop.exec()


class TestApplyEffectMany:
    def test_ismeretlen_effekt_nem_ir(self, controller, library):
        before = _ini_text(library)
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg"), "nemletezo"
            ),
        )
        assert _ini_text(library) == before

    def test_ures_kijeloles_nem_ir(self, controller, library):
        before = _ini_text(library)
        _run(controller, lambda: controller.applyEffectMany([], "autolight"))
        assert _ini_text(library) == before

    def test_meglevo_lanc_vegere_fuzi_appendonly(self, controller, library):
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg"), "autolight"
            ),
        )
        section_line = [
            line for line in _ini_text(library).splitlines()
            if line.startswith("filters=")
        ][0]
        assert section_line == "filters=sat=1,-0.2;autolight=1;"

    def test_uj_kepen_letrehozza_a_szekciot(self, controller, library):
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "y.jpg"), "enhance"
            ),
        )
        text = _ini_text(library)
        assert "[y.jpg]" in text
        lines = text.splitlines()
        y_index = lines.index("[y.jpg]")
        assert lines[y_index + 1] == "filters=enhance=1;"

    def test_mappankent_minden_erintett_mappa_iridik(self, controller, library):
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg", "z.jpg"), "warm"
            ),
        )
        assert "warm=1;" in _ini_text(library)
        assert "warm=1;" in _ini_text_b(library)

    def test_redeye_toggle_szemantika(self, controller, library):
        # a redeye az EGYETLEN toggle-effekt: kétszeri alkalmazás levágja
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg"), "redeye"
            ),
        )
        assert "redeye=1;" in _ini_text(library)
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg"), "redeye"
            ),
        )
        assert "redeye=1;" not in _ini_text(library)

    def test_haladasjelzes_eleri_az_osszest(self, controller, library):
        assert controller.batchEditActive is False
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg", "z.jpg"), "grain2"
            ),
        )
        assert controller.batchEditActive is False
        assert controller.batchEditDoneCount == controller.batchEditTotalCount == 2

    def test_photoopfinished_kifut_ures_kijolesnel_is(self, controller):
        # a `_run` helper a photoOpFinished-re vár — üres kijelölésnél is
        # ki kell futnia (early-return se ragadjon be)
        _run(controller, lambda: controller.applyEffectMany([], "autolight"))


class TestUndoBatchEdit:
    def test_egy_lepesben_visszavonja_a_koteget(self, controller, library):
        assert controller.canUndoBatchEdit is False
        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg", "z.jpg"), "unsharp"
            ),
        )
        assert controller.canUndoBatchEdit is True
        controller.undoBatchEdit()
        assert "unsharp=1;" not in _ini_text(library)
        assert "unsharp=1;" not in _ini_text_b(library)
        # az x.jpg eredeti lánca (sat=1,-0.2;) visszaállt
        section_line = [
            line for line in _ini_text(library).splitlines()
            if line.startswith("filters=")
        ][0]
        assert section_line == "filters=sat=1,-0.2;"
        assert controller.canUndoBatchEdit is False

    def test_ures_verem_noop(self, controller):
        controller.undoBatchEdit()  # nem dob
        assert controller.canUndoBatchEdit is False


class TestCancelBatchEdit:
    def test_megszakitas_kihagyja_a_meg_el_nem_kezdett_mappakat(
        self, controller, library, monkeypatch
    ):
        """Az első mappa megírása UTÁN a cancel-jelzőt MAGA a worker-szál
        állítja be (a monkeypatch-elt `update_document` mellékhatásaként,
        `a` mappa megírása után) — ez szálon belül, versenyhelyzet nélkül
        determinisztikus: a ciklus a KÖVETKEZŐ (b) mappa ELŐTTI cancel-
        ellenőrzésen áll meg (a `test_fileops_controller.py`
        monkeypatch-mintája)."""
        import picasapy.app.batch_effect_controller as batch_module

        original = batch_module.update_document

        def controlled_update(ini_path, mutate, backup=True):
            result = original(ini_path, mutate, backup=backup)
            if "a" in ini_path.parts:
                controller.cancelBatchEdit()
            return result

        monkeypatch.setattr(batch_module, "update_document", controlled_update)

        _run(
            controller,
            lambda: controller.applyEffectMany(
                _rows_by_name(controller, "x.jpg", "z.jpg"), "autocolor"
            ),
        )
        assert "autocolor=1;" in _ini_text(library)
        # a "b" mappa .picasa.ini-je nem is jött létre — a megszakítás a
        # ciklus KÖVETKEZŐ (még el nem kezdett) elemét kihagyta
        assert not (library / "b" / ".picasa.ini").exists()
        # a megszakított köteg is visszavonható (csak a ténylegesen megírt
        # mappára vonatkozik)
        assert controller.canUndoBatchEdit is True
