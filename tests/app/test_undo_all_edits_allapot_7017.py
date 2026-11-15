"""Az Összes szerkesztés visszavonása tétel engedélyezése az eredeti szerkesztettségi
állapotból számolódik (#7017, a #7009 összevetése alapján).

Az eredeti állapotbájtja (`0x004296a0`): nem üres `filters` -> `1`; `rotate(n)`
`n mod 4 != 0` -> `2`; pozitív `flipped` -> `1`; különben `0`. A kijelölés
sorrendjében az első nem nulla állapotú kép dönt (`0x005cb1a0`), a tétel akkor
él, ha ez `1` (`0x0056f393-0x0056f402`).

Az első rész a tiszta függvényt, a második a vezérlő slotját méri valódi
`.picasa.ini`-ből indexelt képeken. A menük tényleges `enabled` állapotát a
`tests/app/qml_functional/test_undo_all_edits_menuk_7017.py` olvassa.

rontás-kontroll: az `edit_state` `flip_flags` ágának kivétele ->
test_csak_tukrozott_kep_szerkesztett és a slot tükrözés-tesztje bukik; a
forgatás-ág előrehozása a `filters` elé -> test_szuroslanc_a_forgatas_elott_dont
bukik.
"""

from __future__ import annotations

import pytest
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op

from picasapy.app.undo_all_edits_state import (
    EDITED,
    ROTATED_ONLY,
    UNEDITED,
    edit_state,
    undo_all_edits_enabled,
)
from picasapy.index import PhotoRecord


def _photo(*, filters=None, rotate=0, flip=0) -> PhotoRecord:
    return PhotoRecord(
        id=1,
        folder_path="/x",
        name="k.jpg",
        kind="image",
        size=1,
        mtime_ns=1,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=rotate,
        filters=filters,
        taken_at=None,
        orientation=1,
        width=10,
        height=10,
        flip_flags=flip,
    )


_CHAIN = "sat=1,-0.2;"


class TestEditState:
    def test_szerkesztetlen_kep(self):
        assert edit_state(_photo()) == UNEDITED

    def test_ures_vagy_szokozos_lanc_nem_szerkesztes(self):
        assert edit_state(_photo(filters="")) == UNEDITED
        assert edit_state(_photo(filters="   ")) == UNEDITED

    def test_szuroslanc_szerkesztett(self):
        assert edit_state(_photo(filters=_CHAIN)) == EDITED

    @pytest.mark.parametrize("lepes", [1, 2, 3])
    def test_csak_elforgatott_kep(self, lepes):
        assert edit_state(_photo(rotate=lepes)) == ROTATED_ONLY

    def test_a_negyedik_lepes_mar_nem_forgatas(self):
        assert edit_state(_photo(rotate=4)) == UNEDITED

    @pytest.mark.parametrize("maszk", [1, 2, 3])
    def test_csak_tukrozott_kep_szerkesztett(self, maszk):
        assert edit_state(_photo(flip=maszk)) == EDITED

    def test_szuroslanc_a_forgatas_elott_dont(self):
        assert edit_state(_photo(filters=_CHAIN, rotate=1)) == EDITED

    def test_a_forgatas_a_tukrozes_elott_dont(self):
        """Az eredeti sorrendje: `filters`, `rotate`, `flipped`."""
        assert edit_state(_photo(rotate=1, flip=1)) == ROTATED_ONLY

    def test_a_kollazs_hasonmas_nem_ismeri_a_tukrozest(self):
        class Hasonmas:
            filters = None
            rotate_steps = 0

        assert edit_state(Hasonmas()) == UNEDITED


class TestKijelolesSzabaly:
    def test_ures_kijeloles_szurke(self):
        assert undo_all_edits_enabled([]) is False

    def test_szerkesztetlen_szurke(self):
        assert undo_all_edits_enabled([_photo()]) is False

    def test_csak_elforgatott_szurke(self):
        assert undo_all_edits_enabled([_photo(rotate=1)]) is False

    def test_csak_tukrozott_el(self):
        assert undo_all_edits_enabled([_photo(flip=1)]) is True

    def test_szuroslanc_el(self):
        assert undo_all_edits_enabled([_photo(filters=_CHAIN)]) is True

    def test_az_elso_elforgatott_a_masodik_szuroslancos_szurke(self):
        photos = [_photo(rotate=1), _photo(filters=_CHAIN)]
        assert undo_all_edits_enabled(photos) is False

    def test_az_elso_szuroslancos_a_masodik_elforgatott_el(self):
        photos = [_photo(filters=_CHAIN), _photo(rotate=1)]
        assert undo_all_edits_enabled(photos) is True

    def test_a_szerkesztetlenek_atugorhatok(self):
        photos = [_photo(), _photo(), _photo(filters=_CHAIN)]
        assert undo_all_edits_enabled(photos) is True
        photos = [_photo(), _photo(rotate=2), _photo(filters=_CHAIN)]
        assert undo_all_edits_enabled(photos) is False

    def test_generator_is_jo_bemenet(self):
        assert undo_all_edits_enabled(p for p in [_photo(flip=2)]) is True


# A fájlnevek a rács (név szerinti) sorrendjét rögzítik: a szűrőláncos kép
# egyszer az elforgatott ELŐTT, egyszer UTÁN áll.
_INI = (
    "[0_szurt.jpg]\nfilters=sat=1,-0.2;\n"
    "[a_forgatott.jpg]\nrotate=rotate(1)\n"
    "[b_szurt.jpg]\nfilters=sat=1,-0.2;\n"
    "[c_tukrozott.jpg]\nflipped=flipped(1)\n"
)
_NEVEK = (
    "0_szurt.jpg",
    "a_forgatott.jpg",
    "b_szurt.jpg",
    "c_tukrozott.jpg",
    "d_sima.jpg",
)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    folder = root / "a"
    folder.mkdir(parents=True)
    for name in _NEVEK:
        make_jpeg(folder / name, size=(800, 600))
    (folder / ".picasa.ini").write_text(_INI, encoding="utf-8")
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
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "a háttérszál nem állt le"


def _rows(controller, *names) -> list:
    by_name = {p.name: i for i, p in enumerate(controller.photos.photos)}
    return [by_name[name] for name in names]


class TestVezerloSlot:
    """A QML-menük ugyanezt a slotot hívják, ezért az indexelt valós képek
    állapota itt dől el."""

    def test_a_racs_sorrendje_a_fixture_feltevese(self, controller):
        rows = _rows(controller, *_NEVEK)
        assert rows == sorted(rows)

    def test_szerkesztetlen_kep_szurke(self, controller):
        assert controller.undoAllEditsEnabled(_rows(controller, "d_sima.jpg")) is False

    def test_csak_elforgatott_kep_szurke(self, controller):
        rows = _rows(controller, "a_forgatott.jpg")
        assert controller.undoAllEditsEnabled(rows) is False

    def test_csak_tukrozott_kep_el(self, controller):
        rows = _rows(controller, "c_tukrozott.jpg")
        assert controller.undoAllEditsEnabled(rows) is True

    def test_szuroslancos_kep_el(self, controller):
        assert controller.undoAllEditsEnabled(_rows(controller, "b_szurt.jpg")) is True

    def test_ures_kijeloles_szurke(self, controller):
        assert controller.undoAllEditsEnabled([]) is False

    def test_ervenytelen_sor_nem_dob(self, controller):
        assert controller.undoAllEditsEnabled([999, -1]) is False

    def test_az_elso_elforgatott_a_masodik_szuroslancos_szurke(self, controller):
        rows = _rows(controller, "a_forgatott.jpg", "b_szurt.jpg")
        assert controller.undoAllEditsEnabled(rows) is False

    def test_az_elso_szuroslancos_a_masodik_elforgatott_el(self, controller):
        rows = _rows(controller, "0_szurt.jpg", "a_forgatott.jpg")
        assert controller.undoAllEditsEnabled(rows) is True

    def test_a_racs_sorrendje_dont_nem_a_kattintase(self, controller):
        """Az „első kijelölt" a rács szerinti első (#6995 mintája): a
        fordított kattintási sorrend sem változtat az eredményen."""
        elore = _rows(controller, "a_forgatott.jpg", "b_szurt.jpg")
        forditva = list(reversed(elore))
        assert controller.undoAllEditsEnabled(elore) is False
        assert controller.undoAllEditsEnabled(forditva) is False
        elore = _rows(controller, "0_szurt.jpg", "a_forgatott.jpg")
        assert controller.undoAllEditsEnabled(list(reversed(elore))) is True

    def test_a_szerkesztetlenek_atugorhatok(self, controller):
        rows = _rows(controller, "d_sima.jpg", "c_tukrozott.jpg")
        assert controller.undoAllEditsEnabled(rows) is True

    def test_az_undo_all_utan_a_csak_tukrozott_kep_szurke(self, controller):
        rows = _rows(controller, "c_tukrozott.jpg")
        assert controller.undoAllEditsEnabled(rows) is True

        wait_for_photo_op(controller, lambda: controller.clearAllEffectsMany(rows))

        rows = _rows(controller, "c_tukrozott.jpg")
        assert controller.undoAllEditsEnabled(rows) is False
