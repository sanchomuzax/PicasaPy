"""#7397: a csupa nulla Hangolás-látogatás nyom nélkül tűnik el, a Derítőfény
új `fill` réteget fűz a betöltött mellé.

Az eredeti Picasa felvételei (T6):

- E26 (job-905): pipetta nélkül a Kiemelések kihúzva és pontosan nullára
  visszahúzva a kép az eredetire áll, az Undo ÉS az Újra tiltott, nincs ini;
- E25 (job-904): pipetta-színnel ugyanez a réteget megtartja (négy nulla,
  `ffc89779`), az Undo aktív;
- E27 (job-906): betöltött `fill=1,0.5` mellett az 1. fül csúszkájának húzása
  ÚJ réteget ad (`fill=1,0.500000;fill=1,0.523364;`), a két réteg halmozódik
  (a szürke folt 169 -> 200).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QTranslator

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from support.jpeg_factory import make_jpeg

_I18N_DIR = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
_BETOLTOTT_FINETUNE = "finetune2=1,0,0,0,ffccc6b2,0;"
_BETOLTOTT_FILL = "fill=1,0.500000;"
_NULLA = (0.0, 0.0, 0.0, 0.0)


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
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(16, 12))


@pytest.fixture
def magyar(qt_app):
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_I18N_DIR)), "a hu .qm nem tölthető be"
    qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


def _betoltott_lanccal(photo: Path, filters: str) -> None:
    (photo.parent / ".picasa.ini").write_text(
        f"[IMG_0001.jpg]\nfilters={filters}\n", encoding="utf-8"
    )


def _ini_filters(photo: Path) -> str | None:
    """Az ini `filters=` kulcsa; None, ha a kulcs (vagy az ini) nincs."""
    from picasapy.ini import load_document

    ini = photo.parent / ".picasa.ini"
    if not ini.exists():
        return None
    section = load_document(ini).section("IMG_0001.jpg")
    return section.get("filters") if section else None


def _sorok(controller, nev: str) -> list[list[str]]:
    return [
        elem.split("=", 1)[1].split(",")
        for elem in str(controller.chainValue).split(";")
        if elem.startswith(f"{nev}=")
    ]


class TestCsupaNullaLatogatas:
    """T6 1. pont (E26): a látogatás Undo-lépése is eltűnik."""

    def test_a_visszahuzott_latogatas_nem_hagy_visszavonasi_lepest(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        assert controller.canUndo is True

        controller.setFinetune(*_NULLA)

        assert controller.canUndo is False
        assert controller.canRedo is False
        assert controller.undoAction == ""
        assert str(controller.chainValue) == ""
        assert controller.hasFinetune is False

    def test_az_undo_felirat_a_latogatas_elottire_all_vissza(self, controller, photo, magyar):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        assert controller.undoLabel == "Visszavonás: Finomhangolás"

        controller.setFinetune(*_NULLA)

        assert controller.undoLabel == "Visszavonás"
        assert controller.redoLabel == "Újra"

    def test_az_ini_a_latogatas_elotti_lancot_kapja_ures_lancnal_nincs_filters_kulcs(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        assert _ini_filters(photo) is not None

        controller.setFinetune(*_NULLA)

        assert _ini_filters(photo) is None

    def test_betoltott_lanc_mellett_az_ini_a_betoltott_lancot_kapja(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FINETUNE)
        controller.beginEdit("1", str(photo))
        elotte = str(controller.chainValue)
        melyseg = len(controller._undo_stack)
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        assert _ini_filters(photo).count("finetune2=") == 2

        controller.setFinetune(*_NULLA)

        assert str(controller.chainValue) == elotte
        assert _ini_filters(photo) == elotte
        assert len(controller._undo_stack) == melyseg
        assert controller.canUndo is True, "a betöltött réteg visszavonható marad"

    def test_a_korabbi_lepes_az_undo_tetejen_marad(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.3)
        melyseg = len(controller._undo_stack)

        controller.setFinetune(0.2, 0.0, 0.0, 0.0)
        controller.setFinetune(*_NULLA)

        assert len(controller._undo_stack) == melyseg
        assert controller.undoAction == "fill"
        assert controller.fixesFillLight == pytest.approx(0.3)

    def test_az_ujra_verem_erintetlen(self, controller, photo):
        """A látogatás első húzása kiüríti az Újra-vermet, a csupa nulla
        visszahúzás a látogatás előtti állapotra állítja vissza."""
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.3)
        controller.undo()
        assert controller.canRedo is True
        assert controller.redoAction == "fill"

        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        assert controller.canRedo is False
        controller.setFinetune(*_NULLA)

        assert controller.canRedo is True
        assert controller.redoAction == "fill"
        controller.redo()
        assert controller.fixesFillLight == pytest.approx(0.3)

    def test_a_kovetkezo_huzas_uj_reteget_es_uj_lepest_kezd(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        controller.setFinetune(*_NULLA)
        melyseg = len(controller._undo_stack)

        controller.setFinetune(0.0, 0.0, 0.3, 0.0)

        assert len(controller._undo_stack) == melyseg + 1
        assert len(_sorok(controller, "finetune2")) == 1
        controller.undo()
        assert str(controller.chainValue) == ""
        assert controller.canUndo is False

    def test_a_masodik_visszahuzas_is_nyom_nelkul_tunik_el(self, controller, photo):
        controller.beginEdit("1", str(photo))
        for _ in range(3):
            controller.setFinetune(0.0, 0.4, 0.0, 0.0)
            controller.setFinetune(*_NULLA)

        assert len(controller._undo_stack) == 0
        assert controller.canUndo is False
        assert controller.canRedo is False

    def test_a_nem_nulla_masodik_csuszka_megtartja_a_reteget(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)

        controller.setFinetune(0.0, 0.0, 0.2, 0.0)

        assert controller.canUndo is True
        assert len(_sorok(controller, "finetune2")) == 1

    def test_az_elso_ures_huzas_semmit_sem_ir(self, controller, photo):
        """Még nyitatlan látogatásnál az üres húzás nem tol lépést, nem ír ini-t."""
        controller.beginEdit("1", str(photo))

        controller.setFinetune(*_NULLA)

        assert controller.canUndo is False
        assert not (photo.parent / ".picasa.ini").exists()

    def test_a_latogatas_az_uj_huzas_utan_ujra_nyilik(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        controller.setFinetune(*_NULLA)

        controller.setFinetune(0.0, 0.3, 0.0, 0.0)
        controller.setFinetune(0.0, 0.6, 0.0, 0.0)

        assert len(controller._undo_stack) == 1
        assert len(_sorok(controller, "finetune2")) == 1


class TestPipettaSzinesNulla:
    """E25 (job-904): pipetta-színnel a réteg négy nullával is megmarad."""

    def test_a_pipetta_utani_nulla_huzas_megtartja_a_reteget_es_a_lepest(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyColorWand()
        szin = _sorok(controller, "finetune2")[0][4]
        assert szin != "00000000"
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)

        controller.setFinetune(*_NULLA)

        sorok = _sorok(controller, "finetune2")
        assert len(sorok) == 1, controller.chainValue
        assert sorok[0][1:4] == ["0.000000", "0.000000", "0.000000"]
        assert sorok[0][4] == szin
        assert controller.canUndo is True
        assert len(controller._undo_stack) == 1
        assert szin in (_ini_filters(photo) or "")

    def test_a_pipettas_latogatas_egy_undo_lepes_az_undo_utan_az_ujra_aktiv(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.applyColorWand()
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)
        controller.setFinetune(*_NULLA)

        controller.undo()

        assert str(controller.chainValue) == ""
        assert controller.canRedo is True


class TestFillUjReteg:
    """T6 2. pont (E27): a Derítőfény új `fill` réteget fűz a lánc végére."""

    def test_betoltott_fill_mellett_az_elso_huzas_uj_reteget_fuz(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))

        controller.setFixesFill(0.523364)

        assert str(controller.chainValue) == "fill=1,0.500000;fill=1,0.523364;"
        assert _ini_filters(photo) == "fill=1,0.500000;fill=1,0.523364;"

    def test_a_betoltott_reteg_szovege_szo_szerint_erintetlen(self, controller, photo):
        _betoltott_lanccal(photo, "fill=1,0.5;")
        controller.beginEdit("1", str(photo))

        controller.setFixesFill(0.9)

        assert str(controller.chainValue) == "fill=1,0.5;fill=1,0.900000;"

    def test_egy_undo_lepes_derítofeny_felirattal(self, controller, photo, magyar):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        melyseg = len(controller._undo_stack)

        controller.setFixesFill(0.523364)

        assert len(controller._undo_stack) == melyseg + 1
        assert controller.undoAction == "fill"
        assert controller.undoLabel == "Visszavonás: Derítőfény"

    def test_az_undo_csak_az_uj_reteget_veszi_le(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.523364)

        controller.undo()

        assert str(controller.chainValue) == "fill=1,0.500000;"
        assert controller.canUndo is True, "a betöltött réteg visszavonható marad"

    def test_megnyitaskor_betoltott_fill_mellett_az_undo_aktiv(self, controller, photo, magyar):
        """Regresszió-őr (E27, job-906 14. kocka): ez ma is így van."""
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)

        controller.beginEdit("1", str(photo))

        assert controller.canUndo is True
        assert controller.undoLabel == "Visszavonás: Derítőfény"

    def test_a_latogatas_tovabbi_huzasai_az_uj_reteget_irjak_felul(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.2)
        melyseg = len(controller._undo_stack)

        controller.setFixesFill(0.7)
        controller.setFixesFill(0.4)

        assert str(controller.chainValue) == "fill=1,0.500000;fill=1,0.400000;"
        assert len(controller._undo_stack) == melyseg

    def test_a_fulvaltas_utani_huzas_ujabb_reteget_fuz(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.2)
        controller.closeFinetuneVisit()

        controller.setFixesFill(0.6)

        assert str(controller.chainValue) == "fill=1,0.500000;fill=1,0.200000;fill=1,0.600000;"
        controller.undo()
        assert str(controller.chainValue) == "fill=1,0.500000;fill=1,0.200000;"

    def test_undo_redo_utan_uj_reteg_jon(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.3)
        controller.undo()
        controller.redo()

        controller.setFixesFill(0.6)

        assert str(controller.chainValue) == "fill=1,0.300000;fill=1,0.600000;"

    def test_masik_muvelet_lezarja_a_latogatast(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.3)
        controller.applyEffect("sepia")

        controller.setFixesFill(0.6)

        nevek = [elem.split("=")[0] for elem in str(controller.chainValue).split(";") if elem]
        assert nevek == ["fill", "sepia", "fill"]

    def test_kepvaltas_lezarja_a_latogatast(self, controller, photo, tmp_path):
        masik = make_jpeg(tmp_path / "IMG_0002.jpg", size=(16, 12))
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.3)
        controller.beginEdit("2", str(masik))
        controller.beginEdit("1", str(photo))

        controller.setFixesFill(0.6)

        assert str(controller.chainValue) == "fill=1,0.300000;fill=1,0.600000;"

    def test_hangolas_utan_a_fill_uj_latogatast_kezd(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.5, 0.0, 0.0)

        controller.setFixesFill(0.4)
        controller.setFixesFill(0.6)

        assert len(_sorok(controller, "finetune2")) == 1
        assert _sorok(controller, "fill") == [["1", "0.600000"]]
        assert len(controller._undo_stack) == 2

    def test_fill_utan_a_hangolas_uj_reteget_kezd_a_fill_erintetlen(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.4)

        controller.setFinetune(0.0, 0.5, 0.0, 0.0)

        assert _sorok(controller, "fill") == [["1", "0.400000"]]
        assert len(_sorok(controller, "finetune2")) == 1

    def test_ures_lancon_a_ketszeri_huzas_egyetlen_fill_reteg(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFixesFill(0.2)
        controller.setFixesFill(0.2)
        controller.setFixesFill(0.7)

        assert _sorok(controller, "fill") == [["1", "0.700000"]]
        assert len(controller._undo_stack) == 1

    def test_az_elonezet_a_betoltott_reteg_mellett_az_ujat_rajzolja(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        revizio = controller.revision
        lancok = []
        eredeti = controller._register_preview
        controller._register_preview = lambda session=None: (
            lancok.append(session.to_value() if session is not None else None),
            eredeti(session),
        )[1]

        controller.previewFixesFill(0.6)

        assert lancok[-1] == "fill=1,0.500000;fill=1,0.600000;", lancok
        assert controller.revision == revizio + 1
        assert _ini_filters(photo) == _BETOLTOTT_FILL
        assert len(controller._undo_stack) == 1, "az előnézet nem tolhat Undo-lépést"

    def test_a_nyitott_latogatasban_az_elonezet_nem_halmoz_tovabbi_reteget(
        self, controller, photo
    ):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.2)
        lancok = []
        eredeti = controller._register_preview
        controller._register_preview = lambda session=None: (
            lancok.append(session.to_value() if session is not None else None),
            eredeti(session),
        )[1]

        controller.previewFixesFill(0.8)

        assert lancok[-1] == "fill=1,0.500000;fill=1,0.800000;", lancok

    def test_a_fixes_fill_tulajdonsag_az_elso_fill_erteket_adja_valtozatlanul(
        self, controller, photo
    ):
        """A csúszka alaphelyzetét a panel állítja (#7383); a tulajdonság a
        mentett `fill` réteget olvassa, ez a #7397 után sem változik."""
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))

        controller.setFixesFill(0.9)

        assert controller.fixesFillLight == pytest.approx(0.5)

    def test_a_nulla_ertek_a_mai_modon_leveszi_a_fill_reteget_egy_lepessel(
        self, controller, photo
    ):
        """A `fill` nullára húzásának viselkedése NEM mért (#7397 nem része):
        a mai viselkedés marad, tehát a nulla minden `fill` réteget levesz."""
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.5)
        controller.setFixesFill(0.0)

        assert str(controller.chainValue) == ""
        assert controller.fixesFillLight == pytest.approx(0.0)
        controller.setFixesFill(0.3)
        assert _sorok(controller, "fill") == [["1", "0.300000"]]


class TestHalmozottKep:
    """E27 képpontmérés: a két `fill` réteg halmozódik a láncban (169 -> 200)."""

    @staticmethod
    def _szurke_folt(lanc: str) -> int:
        kep = np.full((8, 8, 3), 128, dtype=np.uint8)
        return int(apply_filters(kep, parse_filters(lanc)).image[4, 4, 0])

    def test_a_betoltott_reteg_egyedul_169(self):
        assert self._szurke_folt("fill=1,0.5;") == 169

    def test_az_uj_reteg_egyedul_171(self):
        assert self._szurke_folt("fill=1,0.523364;") == 171

    def test_a_ketreteges_lanc_200(self, controller, photo):
        _betoltott_lanccal(photo, _BETOLTOTT_FILL)
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.523364)

        assert self._szurke_folt(str(controller.chainValue)) == 200
