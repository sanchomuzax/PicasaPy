"""#7367: az `applyCrop` a lánc végén álló `crop64`-et helyben frissíti.

A vizsgált állapot a Visszavonás/Újra verem és a lemezre írt `.picasa.ini`:
helyben frissítésnél nincs új rekord, nincs új visszavonás-lépés és a redo
nem ürül; más végrekordnál új `crop64` kerül a végére és a redo kiürül.
"""

from __future__ import annotations

import pytest

from picasapy.ini.rect64 import Rect64, encode_rect64
from support.jpeg_factory import make_jpeg

ELSO = Rect64(left=0.0, top=0.0, right=0.5, bottom=0.5)
MASODIK = Rect64(left=0.25, top=0.25, right=0.75, bottom=0.75)
HARMADIK = Rect64(left=0.5, top=0.5, right=1.0, bottom=1.0)


def _crop(rect: Rect64) -> str:
    return f"crop64=1,{encode_rect64(rect)};"


def _rel(rect: Rect64) -> tuple[float, float, float, float]:
    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _ini_kulcs(photo, kulcs: str) -> str | None:
    szoveg = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
    for sor in szoveg.splitlines():
        if sor.startswith(f"{kulcs}="):
            return sor.split("=", 1)[1]
    return None


def _lanc_ini_bol(photo, filters: str, hatalyos: Rect64) -> None:
    """A windowsos Picasa alakja: `filters=` + a hatályos vágás tükre."""
    (photo.parent / ".picasa.ini").write_text(
        f"[IMG_0001.jpg]\nfilters={filters}\ncrop=rect64({encode_rect64(hatalyos)})\n",
        encoding="utf-8",
    )


def _vag(controller, rect: Rect64) -> None:
    controller.applyCrop(*_rel(rect))


class TestKetEgymasUtaniVagas:
    def test_a_lanc_egyetlen_crop64_et_tartalmaz_a_masodik_teglalappal(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        _vag(controller, ELSO)
        _vag(controller, MASODIK)

        assert _ini_kulcs(photo, "filters") == _crop(MASODIK)

    def test_a_crop_tukorkulcs_a_masodik_vagast_mutatja(self, controller, photo):
        controller.beginEdit("1", str(photo))
        _vag(controller, ELSO)
        _vag(controller, MASODIK)

        assert _ini_kulcs(photo, "crop") == f"rect64({encode_rect64(MASODIK)})"

    def test_egy_visszavonas_mindket_vagast_visszaveszi(self, controller, photo):
        controller.beginEdit("1", str(photo))
        _vag(controller, ELSO)
        _vag(controller, MASODIK)

        controller.undo()

        assert not controller.hasCrop
        assert not controller.canUndo
        assert "crop64" not in (photo.parent / ".picasa.ini").read_text(encoding="utf-8")

    def test_az_ujra_a_masodik_teglalapot_hozza_vissza(self, controller, photo):
        controller.beginEdit("1", str(photo))
        _vag(controller, ELSO)
        _vag(controller, MASODIK)
        controller.undo()

        controller.redo()

        assert _ini_kulcs(photo, "filters") == _crop(MASODIK)
        assert _ini_kulcs(photo, "crop") == f"rect64({encode_rect64(MASODIK)})"


class TestPicasaEredetuVegCrop:
    def test_a_beolvasott_lanc_vegi_crop64_helyben_frissul(self, controller, photo):
        _lanc_ini_bol(photo, f"bw=1;{_crop(ELSO)}", ELSO)
        controller.beginEdit("1", str(photo))

        _vag(controller, MASODIK)

        assert _ini_kulcs(photo, "filters") == f"bw=1;{_crop(MASODIK)}"
        assert _ini_kulcs(photo, "crop") == f"rect64({encode_rect64(MASODIK)})"

    def test_a_visszavonas_a_vagas_nelkuli_lancot_allitja_vissza(
        self, controller, photo
    ):
        _lanc_ini_bol(photo, f"bw=1;{_crop(ELSO)}", ELSO)
        controller.beginEdit("1", str(photo))
        _vag(controller, MASODIK)

        controller.undo()

        assert _ini_kulcs(photo, "filters") == "bw=1;"

    def test_a_valtozatlan_kijeloles_nem_nyul_a_lanchoz(self, controller, photo):
        _lanc_ini_bol(photo, f"bw=1;{_crop(ELSO)}", ELSO)
        controller.beginEdit("1", str(photo))

        _vag(controller, ELSO)

        assert _ini_kulcs(photo, "filters") == f"bw=1;{_crop(ELSO)}"


class TestAUjraListaSorsa:
    def test_helyben_frissitesnel_a_redo_lista_nem_urul(self, controller, photo):
        _lanc_ini_bol(photo, f"{_crop(ELSO)}bw=1;{_crop(MASODIK)}", MASODIK)
        controller.beginEdit("1", str(photo))
        controller.undo()
        controller.undo()
        assert controller.canRedo
        assert _ini_kulcs(photo, "filters") == _crop(ELSO)

        _vag(controller, HARMADIK)

        assert controller.canRedo
        assert _ini_kulcs(photo, "filters") == _crop(HARMADIK)

    def test_hozzafuzesnel_a_redo_lista_kiurul(self, controller, photo):
        _lanc_ini_bol(photo, f"{_crop(ELSO)}bw=1;enhance=1;", ELSO)
        controller.beginEdit("1", str(photo))
        controller.undo()
        assert controller.canRedo

        _vag(controller, MASODIK)

        assert not controller.canRedo
        assert _ini_kulcs(photo, "filters") == f"{_crop(ELSO)}bw=1;{_crop(MASODIK)}"


class TestMasMuveletKoztuk:
    def test_a_vegere_fuzott_ujravagas_visszavonasa_az_elozo_vagast_hozza_vissza(
        self, controller, photo
    ):
        _lanc_ini_bol(photo, f"{_crop(ELSO)}bw=1;", ELSO)
        controller.beginEdit("1", str(photo))
        _vag(controller, MASODIK)
        assert _ini_kulcs(photo, "filters") == f"{_crop(ELSO)}bw=1;{_crop(MASODIK)}"

        controller.undo()

        assert _ini_kulcs(photo, "filters") == f"{_crop(ELSO)}bw=1;"
        assert _ini_kulcs(photo, "crop") == f"rect64({encode_rect64(ELSO)})"

    def test_ures_lancon_az_elso_vagas_uj_rekord_es_visszavonhato(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))

        _vag(controller, ELSO)

        assert _ini_kulcs(photo, "filters") == _crop(ELSO)
        assert controller.canUndo


class TestUresKijelolesuAlkalmaz:
    def test_crop64_vegu_lancnal_az_utolso_vagas_torlodik(self, controller, photo):
        _lanc_ini_bol(photo, f"bw=1;{_crop(ELSO)}", ELSO)
        controller.beginEdit("1", str(photo))

        controller.applyEmptyCrop()

        assert _ini_kulcs(photo, "filters") == "bw=1;"
        assert not controller.hasCrop

    def test_mas_vegrekordnal_a_lanc_nem_valtozik(self, controller, photo):
        _lanc_ini_bol(photo, f"{_crop(ELSO)}bw=1;", ELSO)
        controller.beginEdit("1", str(photo))
        elotte = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")

        controller.applyEmptyCrop()

        assert (photo.parent / ".picasa.ini").read_text(encoding="utf-8") == elotte

    def test_a_torolt_vagas_visszavonhato(self, controller, photo):
        controller.beginEdit("1", str(photo))
        _vag(controller, ELSO)
        controller.applyEmptyCrop()

        controller.undo()

        assert _ini_kulcs(photo, "filters") == _crop(ELSO)
