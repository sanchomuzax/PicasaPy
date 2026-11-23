"""#7383: a Hangolás-látogatás egy új `finetune2` réteg és EGY Undo-lépés.

Az eredeti Picasában (J3d, J4a, J6c):

- a látogatás első húzása ÚJ `finetune2` réteget fűz a lánc végére, a betöltött
  réteg mellé (két réteg a láncban),
- a látogatás további húzásai és a pipetta ugyanazt a réteget módosítják,
- az egész látogatás egyetlen visszavonási lépés (felirata: Finomhangolás).

A látogatás véget ér: a fül elhagyásakor (`closeFinetuneVisit`), képváltáskor,
Undo/Redo-nál és minden másik, saját visszavonási lépést toló művelet előtt.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QTranslator

from support.jpeg_factory import make_jpeg

_I18N_DIR = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"
_BETOLTOTT = "finetune2=1,0,0,0,ffccc6b2,0;"


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


def _betoltott_lanccal(photo: Path, filters: str = _BETOLTOTT) -> None:
    (photo.parent / ".picasa.ini").write_text(
        f"[IMG_0001.jpg]\nfilters={filters}\n", encoding="utf-8"
    )


def _finetune_sorok(controller) -> list[list[str]]:
    sorok = []
    for elem in str(controller.chainValue).split(";"):
        if elem.startswith("finetune2="):
            sorok.append(elem.split("=", 1)[1].split(","))
    return sorok


class TestEgyReteg:
    def test_az_elso_huzas_uj_reteget_fuz_a_betoltott_melle(self, controller, photo):
        """J6c: két `finetune2` sor, a második p4-je `00000000`."""
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)

        sorok = _finetune_sorok(controller)
        assert len(sorok) == 2, controller.chainValue
        assert sorok[0][4] == "ffccc6b2"
        assert sorok[1][4] == "00000000"
        assert float(sorok[1][2]) == pytest.approx(0.2)

    def test_a_tobbi_huzas_ugyanazt_a_reteget_modositja(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.setFinetune(0.5, 0.2, 0.1, -0.3)
        controller.setFinetune(0.5, 0.4, 0.1, -0.3)

        sorok = _finetune_sorok(controller)
        assert len(sorok) == 2, controller.chainValue
        assert [float(x) for x in (sorok[1][1], sorok[1][2], sorok[1][3], sorok[1][5])] == (
            pytest.approx([0.5, 0.4, 0.1, -0.3])
        )

    def test_a_betoltott_reteg_erintetlen(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.3, 0.2, 0.1, 0.5)
        assert _finetune_sorok(controller)[0] == ["1", "0", "0", "0", "ffccc6b2", "0"]

    def test_az_ismeretlen_reteg_es_a_sorrend_erintetlen(self, controller, photo):
        _betoltott_lanccal(photo, "grain2=1,0.5;finetune2=1,0.5,0,0,00000000,0;sat=1,0.5;")
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.1, 0.0, 0.0)
        nevek = [elem.split("=")[0] for elem in str(controller.chainValue).split(";") if elem]
        assert nevek == ["grain2", "finetune2", "sat", "finetune2"]

    def test_a_fill_reteg_a_hangolasra_nem_hat(self, controller, photo):
        _betoltott_lanccal(photo, "fill=1,0.5;")
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        assert str(controller.chainValue).count("fill=1,0.5") == 1


class TestEgyUndoLepes:
    def test_hat_huzas_egyetlen_undo_lepes(self, controller, photo):
        """J3d: hat húzás négy csúszkán, egy Undo mindent visszaállít."""
        controller.beginEdit("1", str(photo))
        for ertekek in (
            (0.0, 0.1, 0.0, 0.0),
            (0.0, 0.3, 0.0, 0.0),
            (0.0, 0.2, 0.0, 0.0),
            (0.4, 0.2, 0.0, 0.0),
            (0.4, 0.2, 0.2, 0.0),
            (0.4, 0.2, 0.2, 0.3),
        ):
            controller.setFinetune(*ertekek)

        controller.undo()

        assert str(controller.chainValue) == ""
        assert controller.canUndo is False
        assert controller.canRedo is True
        assert controller.redoAction == "finetune"

    def test_a_felirat_finomhangolas(self, controller, photo, magyar):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.1, 0.0, 0.0)
        controller.setFinetune(0.0, 0.3, 0.0, 0.0)
        assert controller.undoLabel == "Visszavonás: Finomhangolás"
        controller.undo()
        assert controller.redoLabel == "Újra: Finomhangolás"

    def test_az_undo_csak_az_ujat_veszi_le(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.setFinetune(0.0, 0.4, 0.0, 0.0)

        controller.undo()

        sorok = _finetune_sorok(controller)
        assert sorok == [["1", "0", "0", "0", "ffccc6b2", "0"]], controller.chainValue
        assert controller.redoAction == "finetune"

    def test_negy_huzas_undo_undo_redo(self, controller, photo):
        """J4a: a második Undo már a (betöltött) láncra hatna; üres láncnál
        tiltott, a Redo visszahozza az egész látogatást."""
        controller.beginEdit("1", str(photo))
        for ertekek in (
            (0.5, 0.0, 0.0, 0.0),
            (0.5, 0.24, 0.0, 0.0),
            (0.5, 0.24, 0.24, 0.0),
            (0.5, 0.24, 0.24, 0.73),
        ):
            controller.setFinetune(*ertekek)

        controller.undo()
        controller.undo()  # üres veremnél no-op
        controller.redo()

        sorok = _finetune_sorok(controller)
        assert len(sorok) == 1
        assert [float(x) for x in (sorok[0][1], sorok[0][2], sorok[0][3], sorok[0][5])] == (
            pytest.approx([0.5, 0.24, 0.24, 0.73])
        )
        assert controller.canUndo is True
        assert controller.canRedo is False

    def test_a_huzasok_nem_novelik_a_veremet_az_elso_utan(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.1, 0.0, 0.0)
        melyseg = len(controller._undo_stack)
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.setFinetune(0.3, 0.2, 0.0, 0.0)
        assert len(controller._undo_stack) == melyseg


class TestLatogatasVege:
    def test_a_ful_elhagyasa_utan_uj_reteg_jon(self, controller, photo):
        """A fül elhagyása utáni húzás új réteget ad (a J6c általánosítása,
        közvetlenül nem mért)."""
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.closeFinetuneVisit()
        controller.setFinetune(0.0, 0.0, 0.3, 0.0)

        assert len(_finetune_sorok(controller)) == 2, controller.chainValue
        controller.undo()
        assert len(_finetune_sorok(controller)) == 1

    def test_undo_redo_utan_uj_reteg_jon(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.undo()
        controller.redo()
        controller.setFinetune(0.0, 0.0, 0.3, 0.0)

        assert len(_finetune_sorok(controller)) == 2, controller.chainValue

    def test_masik_muvelet_lezarja_a_latogatast(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.applyEffect("sepia")
        controller.setFinetune(0.0, 0.0, 0.3, 0.0)

        nevek = [elem.split("=")[0] for elem in str(controller.chainValue).split(";") if elem]
        assert nevek == ["finetune2", "sepia", "finetune2"]

    def test_kepvaltas_lezarja_a_latogatast(self, controller, photo, tmp_path):
        masik = make_jpeg(tmp_path / "IMG_0002.jpg", size=(16, 12))
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        controller.beginEdit("2", str(masik))
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.0, 0.0, 0.3, 0.0)

        assert len(_finetune_sorok(controller)) == 2, controller.chainValue

    def test_a_nulla_ertek_leveszi_a_reteget_es_a_lepest_a_kovetkezo_huzas_ujat_kezd(
        self, controller, photo
    ):
        """#7397 (E26): a csupa nulla látogatás Undo-lépése is eltűnik, a
        látogatás lezárul; a következő húzás új réteget és új lépést kezd."""
        controller.beginEdit("1", str(photo))
        melyseg = len(controller._undo_stack)
        controller.setFinetune(0.5, 0.0, 0.0, 0.0)
        assert len(controller._undo_stack) == melyseg + 1

        controller.setFinetune(0.0, 0.0, 0.0, 0.0)
        assert controller.hasFinetune is False
        assert len(controller._undo_stack) == melyseg
        controller.setFinetune(0.2, 0.0, 0.0, 0.0)

        assert len(_finetune_sorok(controller)) == 1
        assert len(controller._undo_stack) == melyseg + 1

    def test_nulla_ertek_betoltott_reteg_mellett_semmit_sem_valtoztat(
        self, controller, photo
    ):
        """A látogatás üres húzása (a csúszka a helyén marad) nem kezd új
        réteget, nem tol visszavonási lépést és nem nyúl a betöltött réteghez."""
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        elotte = str(controller.chainValue)
        melyseg = len(controller._undo_stack)

        controller.setFinetune(0.0, 0.0, 0.0, 0.0)

        assert str(controller.chainValue) == elotte
        assert len(controller._undo_stack) == melyseg

    def test_a_latogatas_vege_jelzi_a_csuszkak_alaphelyzetet(self, controller, photo):
        jelek = []
        controller.finetuneSlidersReset.connect(lambda: jelek.append(1))
        controller.beginEdit("1", str(photo))
        elozo = len(jelek)
        controller.setFinetune(0.0, 0.2, 0.0, 0.0)
        assert len(jelek) == elozo, "a húzás nem állíthatja alaphelyzetbe a csúszkát"
        controller.undo()
        assert len(jelek) == elozo + 1
        controller.redo()
        assert len(jelek) == elozo + 2
        controller.beginEdit("1", str(photo))
        assert len(jelek) == elozo + 3


class TestElonezet:
    def test_az_elonezet_a_betoltott_reteg_mellett_az_ujat_rajzolja(
        self, controller, photo
    ):
        _betoltott_lanccal(photo, "finetune2=1,0.5,0,0,00000000,0;")
        controller.beginEdit("1", str(photo))
        lancok = []
        eredeti = controller._register_preview
        controller._register_preview = lambda session=None: (
            lancok.append(session.to_value() if session is not None else None),
            eredeti(session),
        )[1]

        controller.previewFinetune(0.0, 0.2, 0.0, 0.0)

        assert lancok, "az előnézet nem regisztrált láncot"
        assert lancok[-1].count("finetune2=") == 2, lancok[-1]
        assert "finetune2=1,0.500000" in lancok[-1] or "finetune2=1,0.5," in lancok[-1]


class TestPipetta:
    def test_a_pipetta_a_latogatas_retegeben_ir_nem_toll_ujat(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.3, 0.2, 0.1, 0.4)
        melyseg = len(controller._undo_stack)

        controller.applyColorWand()

        sorok = _finetune_sorok(controller)
        assert len(sorok) == 1
        assert sorok[0][4].startswith("ff")
        assert [float(x) for x in (sorok[0][1], sorok[0][2], sorok[0][3], sorok[0][5])] == (
            pytest.approx([0.3, 0.2, 0.1, 0.4])
        )
        assert len(controller._undo_stack) == melyseg

    def test_a_pipetta_betoltott_reteg_mellett_uj_reteget_nyit(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))

        controller.applyColorWand()

        sorok = _finetune_sorok(controller)
        assert len(sorok) == 2, controller.chainValue
        assert sorok[0][4] == "ffccc6b2"
        assert sorok[1][4].startswith("ff") and sorok[1][4] != "ffccc6b2"
        controller.undo()
        assert len(_finetune_sorok(controller)) == 1

    def test_a_pipetta_utan_a_huzas_megorzi_a_szint(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.3, 0.0, 0.0, 0.0)
        controller.applyColorWand()
        szin = _finetune_sorok(controller)[0][4]

        controller.setFinetune(0.3, 0.2, 0.0, 0.0)

        assert _finetune_sorok(controller)[0][4] == szin

    def test_a_szinminta_a_latogatas_retegenek_szinet_mutatja(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        # látogatás nélkül alaphelyzet (fekete minta), a betöltött réteg
        # `ffccc6b2` színe mellett is: J6c 16. kocka
        assert controller.neutralColor == ""
        controller.applyColorWand()
        sorok = _finetune_sorok(controller)
        assert controller.neutralColor == "#" + sorok[1][4][2:]
        controller.undo()
        assert controller.neutralColor == ""


class TestAlaphelyzetiJelolt:
    """A négy nulla értékű jelölt (a csúszkák alaphelyzete) nem fűz fantom
    réteget: a lánc-nézet (`EffectSliceBox`) a valódi lépésszámot mutatja."""

    def test_nulla_ertek_nem_fuz_reteget_a_betoltott_lanc_mellett(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        ures = controller._finetune_visit_session(
            controller._session, fill=0.0, highlights=0.0, shadows=0.0, temperature=0.0
        )
        assert ures.to_value() == controller._session.to_value()

        egy = controller._finetune_visit_session(
            controller._session, fill=0.0, highlights=0.2, shadows=0.0, temperature=0.0
        )
        assert len(egy.ops) == len(controller._session.ops) + 1

    def test_nyitott_latogatasban_a_nulla_jelolt_a_latogatas_elotti_lanc(
        self, controller, photo
    ):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        elotte = controller._session.to_value()
        controller.setFinetune(0.0, 0.3, 0.0, 0.0)

        ures = controller._finetune_visit_session(
            controller._session, fill=0.0, highlights=0.0, shadows=0.0, temperature=0.0
        )

        assert ures.to_value() == elotte

    def test_a_pipetta_szine_megtartja_a_reteget_nulla_csuszkaknal(self, controller, photo):
        _betoltott_lanccal(photo)
        controller.beginEdit("1", str(photo))
        controller.applyColorWand()
        szin = _finetune_sorok(controller)[1][4]

        jelolt = controller._finetune_visit_session(
            controller._session, fill=0.0, highlights=0.0, shadows=0.0, temperature=0.0
        )

        assert len(jelolt.ops) == len(controller._session.ops)
        assert jelolt.to_value().count(szin) == 1, jelolt.to_value()
