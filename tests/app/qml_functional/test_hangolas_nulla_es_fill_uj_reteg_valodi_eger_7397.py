"""#7397: a csupa nulla Hangolás-látogatás nyom nélkül eltűnik, a Derítőfény új
`fill` réteget fűz a betöltött mellé - VALÓDI egérrel, KIRAJZOLT képpel.

Az eredeti Picasa felvételei (T6):

- E26 (job-905 12., 14., 17., 22.): a Kiemelések kihúzva és pontosan nullára
  visszahúzva, pipetta nélkül a kép az eredeti (bézs (200,151,121)), az Undo
  ÉS az Újra tiltott, a Save nem kínálódik fel (nincs `filters=` az ini-ben),
  nincs ini-változás;
- E25 (job-904 15., 18., 20., 22.): pipetta-színnel (`ffc89779`) a réteg négy
  nullával is megmarad, a kép a csak-pipettás állapot, az Undo aktív, a Save
  felkínálódik;
- E27 (job-906 14., 15., 17.): betöltött `fill=1,0.5` mellett az 1. fül
  csúszkájának húzása ÚJ réteget ad, a két réteg halmozódik (a szürke folt a
  csak-betöltött 169-ről 200 körülire világosodik), az Undo "Derítőfény".

A próbák a ténylegesen kirajzolt vezérlőt és képet használják: egéreseményt
küldenek az ablaknak (nem a kontroller metódusát hívják), a láncot, a gombok
állapotát és a felirataikat a kirajzolt elemekről, a képpontokat az ablak
képkockájáról olvassák vissza. A mintakép négy foltja a mért forrásfoltok
(szürke 128, bézs `c89779`, kék `3c5a96`), a kép a nézőben illesztve áll.

Rontás-kontroll: ha a csupa nulla látogatás Undo-lépése visszakerül (a #7383
régi `is_noop` ága), az Undo-gomb aktív marad és az `E26` próbák elbuknak; ha a
`setFixesFill` ismét a helyén cserél (`set_fill`), a `fill=` sorok száma 1 marad
és a kép nem világosodik tovább (169 helyett 171 körül marad).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPointF, Qt, QTranslator
from PySide6.QtTest import QTest

from picasapy.app.model_helpers import _has_edits
from picasapy.ini import load_document
from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

_I18N_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "i18n"

_SZURKE = (128, 128, 128)
_BEZS = (200, 151, 121)
_KEK = (60, 90, 150)
_FEHER = (230, 230, 230)
_MERES_TURES = 4
_ELSO_FUL, _HANGOLAS_FUL = 0, 1
_FOLTOK = {"szurke": (0.25, 0.25), "bezs": (0.75, 0.25), "kek": (0.25, 0.75)}


@pytest.fixture
def _magyar_forditas(qt_app):
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_I18N_DIR)), "a hu .qm nem tölthető be"
    qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


def _foltos_kep(utvonal: Path) -> None:
    """600x600, négy egyenletes folt: a mért szürke, bézs, kék és egy világos."""
    kep = np.zeros((600, 600, 3), dtype=np.uint8)
    kep[:300, :300] = _SZURKE
    kep[:300, 300:] = _BEZS
    kep[300:, :300] = _KEK
    kep[300:, 300:] = _FEHER
    Image.fromarray(kep).save(utvonal, quality=98, subsampling=0)


def _kepek_foltokkal(lib: Path) -> None:
    _foltos_kep(lib / "a.jpg")
    _foltos_kep(lib / "b.jpg")


def _kepek_betoltott_fill_lanccal(lib: Path) -> None:
    _kepek_foltokkal(lib)
    (lib / ".picasa.ini").write_text("[a.jpg]\nfilters=fill=1,0.5;\n", encoding="utf-8")


@pytest.fixture
def app_foltos(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_foltokkal)


@pytest.fixture
def app_betoltott_fill(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_betoltott_fill_lanccal)


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _megnyit(app, qt_app):
    window, _controller, engine = app
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    assert var_feltetelre(
        qt_app,
        lambda: _item(window, "viewerEditorPanel").property("visible") is True,
        10.0,
    ), "a szerkesztőpanel nem nyílt meg"
    assert not window.grabWindow().isNull(), "a főablak nem rajzolódott ki"
    edit = engine.rootContext().contextProperty("editController")
    return window, _item(window, "viewerEditorPanel"), edit


def _pont(item, arany: float) -> QPointF:
    return item.mapToScene(
        QPointF(float(item.property("width")) * arany, float(item.property("height")) / 2)
    )


def _huzas(window, slider, qt_app, honnan: float, hova: float) -> None:
    """Valódi egérhúzás: lenyomás, mozgatás, elengedés (az elengedés ment).
    A `hova` lehet a csúszka sávján kívül is (a fogantyú a szélén áll meg)."""
    assert slider.property("visible") is True, f"{slider.objectName()} nem látható"
    kezd = _pont(slider, honnan).toPoint()
    veg = _pont(slider, hova).toPoint()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezd)
    qt_app.processEvents()
    QTest.mouseMove(window, veg)
    qt_app.processEvents()
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, veg)
    qt_app.processEvents()


def _kattint(window, gomb, qt_app) -> None:
    pont = _pont(gomb, 0.5).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _ful(panel, qt_app, index: int) -> None:
    panel.setProperty("activeTab", index)
    qt_app.processEvents()


def _ertek(window, nev: str) -> float:
    return float(_item(window, nev).property("value"))


def _sorok(edit, nev: str) -> list[list[str]]:
    return [
        elem.split("=", 1)[1].split(",")
        for elem in str(edit.property("chainValue")).split(";")
        if elem.startswith(f"{nev}=")
    ]


def _gomb_aktiv(window, nev: str) -> bool:
    return _item(window, nev).property("buttonEnabled") is True


def _felirat(window, nev: str) -> str:
    return str(_item(window, nev).property("text"))


def _ini_filters(tmp_path: Path) -> str | None:
    """Az a.jpg ini-szakaszának `filters=` kulcsa; None, ha nincs kulcs vagy ini."""
    ini = tmp_path / "kepek" / ".picasa.ini"
    if not ini.exists():
        return None
    szakasz = load_document(ini).section("a.jpg")
    return szakasz.get("filters") if szakasz else None


def _save_felkinalhato(tmp_path: Path) -> bool:
    """Felkínálja-e a program a mentést: a modell `hasEdits` jelzése (ez engedi
    a Ctrl+S-t és a Save ablakot) a `.picasa.ini` `filters=` sorából ered
    (`_has_edits`). A próba-harness a szerkesztő mentését nem köti a modellhez,
    ezért a szabályt az ini-n mérjük, nem a billentyűn (az ott mindig tiltott
    lenne, tehát hamis zöld)."""
    return _has_edits(SimpleNamespace(filters=_ini_filters(tmp_path)))


def _folt_szine(window, folt: str) -> tuple[int, int, int]:
    """A kirajzolt kép adott foltjának színe az ablak friss képkockájáról."""
    kep = _item(window, "viewerImage")
    festett_w = float(kep.property("paintedWidth"))
    festett_h = float(kep.property("paintedHeight"))
    bal = (float(kep.property("width")) - festett_w) / 2
    felso = (float(kep.property("height")) - festett_h) / 2
    fx, fy = _FOLTOK[folt]
    pont = kep.mapToScene(QPointF(bal + festett_w * fx, felso + festett_h * fy))
    pixel = window.grabWindow().pixelColor(round(pont.x()), round(pont.y()))
    return (pixel.red(), pixel.green(), pixel.blue())


def _kozel(szin: tuple[int, int, int], cel: tuple[int, int, int]) -> bool:
    return all(abs(a - b) <= _MERES_TURES for a, b in zip(szin, cel, strict=True))


def _varj_szinre(qt_app, window, folt: str, cel: tuple[int, int, int], mp: float = 10.0):
    """Vár, amíg a kirajzolt folt a célszínt mutatja (a háttér-render aszinkron);
    visszaadja az utoljára mért színt, hogy a hibaüzenet a látottat mutassa."""
    utolso = [(-1, -1, -1)]

    def kesz() -> bool:
        utolso[0] = _folt_szine(window, folt)
        return _kozel(utolso[0], cel)

    var_feltetelre(qt_app, kesz, mp)
    return utolso[0]


def _vart_szin(lanc: str, folt: tuple[int, int, int]) -> tuple[int, int, int]:
    """A lánc szerint várt szín egy forrásfoltra (a renderer maga számolja)."""
    kep = np.full((8, 8, 3), folt, dtype=np.uint8)
    pixel = apply_filters(kep, parse_filters(lanc)).image[4, 4]
    return (int(pixel[0]), int(pixel[1]), int(pixel[2]))


def _elso_osszehasonlitas_alapja(app_foltos, qt_app):
    window, panel, edit = _megnyit(app_foltos, qt_app)
    szurke = _varj_szinre(qt_app, window, "szurke", _SZURKE)
    bezs = _varj_szinre(qt_app, window, "bezs", _BEZS)
    assert _kozel(szurke, _SZURKE), f"a szerkesztetlen kép szürke foltja: {szurke}"
    assert _kozel(bezs, _BEZS), f"a szerkesztetlen kép bézs foltja: {bezs}"
    return window, panel, edit


class TestCsupaNullaLatogatas:
    """T6 1. pont, E26: a kihúzott és nullára visszahúzott csúszka nyom nélkül tűnik el."""

    def _kihuz(self, window, qt_app) -> None:
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.97)

    def _visszahuz(self, window, qt_app) -> None:
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.97, -0.4)

    def _kihuz_es_visszahuz(self, window, qt_app) -> None:
        self._kihuz(window, qt_app)
        self._visszahuz(window, qt_app)

    def test_a_kep_az_eredeti_az_undo_es_az_ujra_tiltott_nincs_save_es_ini(
        self, _magyar_forditas, app_foltos, qt_app, tmp_path
    ):
        """job-905 14., 17., 22.: bézs (200,151,121), Undo és Újra tiltott,
        a Save nem kínálódik fel (az ini-ben nincs `filters=`), nincs ini-változás."""
        window, panel, edit = _elso_osszehasonlitas_alapja(app_foltos, qt_app)
        _ful(panel, qt_app, _HANGOLAS_FUL)
        kiemelesek = _item(window, "finetuneHighlightsSlider")

        _huzas(window, kiemelesek, qt_app, 0.1, 0.97)

        # a kihúzott állapot már szerkesztett: a mérés nem üres (kontroll)
        assert _ertek(window, "finetuneHighlightsSlider") > 0.4
        assert len(_sorok(edit, "finetune2")) == 1, edit.property("chainValue")
        assert _gomb_aktiv(window, "editUndoButton")
        assert _ini_filters(tmp_path) is not None, "a kihúzott állapot nem íródott ini-be"
        assert _save_felkinalhato(tmp_path), "kontroll: a kihúzott állapot nem kínál Save-et"

        _huzas(window, kiemelesek, qt_app, 0.97, -0.4)

        assert _ertek(window, "finetuneHighlightsSlider") == pytest.approx(0.0, abs=1e-9)
        assert str(edit.property("chainValue")) == ""
        assert _gomb_aktiv(window, "editUndoButton") is False, "az Undo üres lépést vehetne le"
        assert _gomb_aktiv(window, "editRedoButton") is False
        assert _felirat(window, "editUndoButtonLabel") == "Visszavonás"
        assert _felirat(window, "editRedoButtonLabel") == "Újra"
        assert edit.property("canUndo") is False
        assert edit.property("canRedo") is False
        assert _ini_filters(tmp_path) is None, "az ini a látogatás előtti (üres) láncot kapja"
        assert not _save_felkinalhato(tmp_path), "a program Save ablakot kínálna"
        bezs = _varj_szinre(qt_app, window, "bezs", _BEZS)
        szurke = _varj_szinre(qt_app, window, "szurke", _SZURKE)
        assert _kozel(bezs, _BEZS), f"a bézs folt nem az eredeti (200,151,121): {bezs}"
        assert _kozel(szurke, _SZURKE), f"a szürke folt nem az eredeti: {szurke}"

    def test_a_kovetkezo_huzas_uj_reteget_es_uj_lepest_kezd(
        self, _magyar_forditas, app_foltos, qt_app
    ):
        window, panel, edit = _elso_osszehasonlitas_alapja(app_foltos, qt_app)
        _ful(panel, qt_app, _HANGOLAS_FUL)
        self._kihuz_es_visszahuz(window, qt_app)

        _huzas(window, _item(window, "finetuneShadowsSlider"), qt_app, 0.1, 0.6)

        assert len(_sorok(edit, "finetune2")) == 1, edit.property("chainValue")
        assert _gomb_aktiv(window, "editUndoButton")
        assert _felirat(window, "editUndoButtonLabel") == "Visszavonás: Finomhangolás"
        _kattint(window, _item(window, "editUndoButton"), qt_app)
        assert str(edit.property("chainValue")) == ""
        assert _gomb_aktiv(window, "editUndoButton") is False
        assert _gomb_aktiv(window, "editRedoButton") is True

    def test_az_ujra_allapota_a_latogatas_elottire_all_vissza(
        self, _magyar_forditas, app_foltos, qt_app
    ):
        """Az Újra-verem érintetlen: egy korábbi Undo után a csupa nulla
        látogatás az Újra gombot sem veszi el."""
        window, panel, edit = _elso_osszehasonlitas_alapja(app_foltos, qt_app)
        _huzas(window, _item(window, "fixesFillSlider"), qt_app, 0.1, 0.6)
        _kattint(window, _item(window, "editUndoButton"), qt_app)
        assert _gomb_aktiv(window, "editRedoButton") is True
        assert _felirat(window, "editRedoButtonLabel") == "Újra: Derítőfény"
        _ful(panel, qt_app, _HANGOLAS_FUL)

        self._kihuz_es_visszahuz(window, qt_app)

        assert _gomb_aktiv(window, "editUndoButton") is False
        assert _gomb_aktiv(window, "editRedoButton") is True
        assert _felirat(window, "editRedoButtonLabel") == "Újra: Derítőfény"

    def test_pipettaval_a_reteg_negy_nullaval_is_megmarad(
        self, _magyar_forditas, app_foltos, qt_app, tmp_path
    ):
        """E25 (job-904 18., 20.): a kép a csak-pipettás állapot, az Undo aktív,
        a Save felkínálódik, az ini-ben négy nulla és a pipetta-szín áll."""
        window, panel, edit = _elso_osszehasonlitas_alapja(app_foltos, qt_app)
        _ful(panel, qt_app, _HANGOLAS_FUL)
        # a pipetta a bézs foltra kattint (job-904: `ffc89779`, a folt szürkére áll)
        assert edit.pickNeutralColor(0.75, 0.25) is True, "a pipetta nem mintavételezett"
        qt_app.processEvents()
        szin = _sorok(edit, "finetune2")[0][4]
        assert szin == "ffc89779", szin
        csak_pipetta = _vart_szin(str(edit.property("chainValue")), _BEZS)
        _varj_szinre(qt_app, window, "bezs", csak_pipetta)

        self._kihuz_es_visszahuz(window, qt_app)

        sorok = _sorok(edit, "finetune2")
        assert len(sorok) == 1, edit.property("chainValue")
        assert sorok[0][1:4] == ["0.000000", "0.000000", "0.000000"]
        assert sorok[0][4] == szin
        assert _gomb_aktiv(window, "editUndoButton") is True
        assert _felirat(window, "editUndoButtonLabel") == "Visszavonás: Finomhangolás"
        assert szin in (_ini_filters(tmp_path) or ""), _ini_filters(tmp_path)
        assert _save_felkinalhato(tmp_path), "a Save nem kínálódik fel"
        bezs = _varj_szinre(qt_app, window, "bezs", csak_pipetta)
        assert _kozel(bezs, csak_pipetta), f"a kép nem a csak-pipettás állapot: {bezs}"
        assert not _kozel(csak_pipetta, _BEZS), "a pipetta nem változtatta a képet (kontroll)"


class TestDerítofenyUjReteg:
    """T6 2. pont, E27: a Derítőfény új `fill` réteget fűz a betöltött mellé."""

    def test_a_huzas_uj_reteget_ad_a_ket_reteg_halmozodik(
        self, _magyar_forditas, app_betoltott_fill, qt_app, tmp_path
    ):
        """job-906 14., 15.: a szürke folt a csak-betöltött 169-ről 200 körülire
        világosodik, a láncban két `fill` áll, az Undo "Derítőfény"."""
        window, _panel, edit = _megnyit(app_betoltott_fill, qt_app)
        csak_betoltott = _vart_szin("fill=1,0.5;", _SZURKE)
        assert csak_betoltott == (169, 169, 169)
        elotte = _varj_szinre(qt_app, window, "szurke", csak_betoltott)
        assert _kozel(elotte, csak_betoltott), f"a betöltött fill képe nem 169: {elotte}"
        assert _gomb_aktiv(window, "editUndoButton"), "megnyitáskor az Undo már aktív (job-906 14.)"

        _huzas(window, _item(window, "fixesFillSlider"), qt_app, 0.1, 0.52)

        sorok = _sorok(edit, "fill")
        assert len(sorok) == 2, edit.property("chainValue")
        assert sorok[0] == ["1", "0.5"], "a betöltött réteg érintetlen"
        assert float(sorok[1][1]) == pytest.approx(
            _ertek(window, "fixesFillSlider"), abs=1e-5
        )
        assert _felirat(window, "editUndoButtonLabel") == "Visszavonás: Derítőfény"
        vart = _vart_szin(str(edit.property("chainValue")), _SZURKE)
        assert vart[0] > 190, f"a két réteg halmozott hatása nem látszik a modellben: {vart}"
        latott = _varj_szinre(qt_app, window, "szurke", vart)
        assert _kozel(latott, vart), f"a kirajzolt szürke folt {latott}, a halmozott hatás {vart}"
        assert latott[0] > elotte[0] + 15, f"a kép nem világosodott: {elotte} -> {latott}"
        assert "fill=1,0.5;fill=1," in (_ini_filters(tmp_path) or "")

    def test_az_undo_csak_az_uj_reteget_veszi_le(
        self, app_betoltott_fill, qt_app
    ):
        window, _panel, edit = _megnyit(app_betoltott_fill, qt_app)
        _huzas(window, _item(window, "fixesFillSlider"), qt_app, 0.1, 0.7)
        assert len(_sorok(edit, "fill")) == 2

        _kattint(window, _item(window, "editUndoButton"), qt_app)

        assert str(edit.property("chainValue")) == "fill=1,0.5;"
        assert _gomb_aktiv(window, "editUndoButton") is True, "a betöltött réteg visszavonható"
        assert _gomb_aktiv(window, "editRedoButton") is True
        szurke = _varj_szinre(qt_app, window, "szurke", (169, 169, 169))
        assert _kozel(szurke, (169, 169, 169)), f"az Undo után a szürke folt: {szurke}"
        assert _ertek(window, "fixesFillSlider") == pytest.approx(0.0, abs=1e-6)

    def test_a_latogatas_tovabbi_huzasa_az_uj_reteget_irja_felul(
        self, app_betoltott_fill, qt_app
    ):
        window, _panel, edit = _megnyit(app_betoltott_fill, qt_app)
        csuszka = _item(window, "fixesFillSlider")
        _huzas(window, csuszka, qt_app, 0.1, 0.8)
        elso = float(_sorok(edit, "fill")[1][1])

        _huzas(window, csuszka, qt_app, 0.8, 0.3)

        sorok = _sorok(edit, "fill")
        assert len(sorok) == 2, edit.property("chainValue")
        assert sorok[0] == ["1", "0.5"]
        assert float(sorok[1][1]) < elso - 0.2

    def test_a_ful_elhagyasa_utani_huzas_ujabb_reteget_fuz(self, app_betoltott_fill, qt_app):
        window, panel, edit = _megnyit(app_betoltott_fill, qt_app)
        csuszka = _item(window, "fixesFillSlider")
        _huzas(window, csuszka, qt_app, 0.1, 0.6)
        _ful(panel, qt_app, _HANGOLAS_FUL)
        _ful(panel, qt_app, _ELSO_FUL)

        _huzas(window, csuszka, qt_app, 0.1, 0.4)

        assert len(_sorok(edit, "fill")) == 3, edit.property("chainValue")

    def test_ures_lancon_a_ketszeri_huzas_egyetlen_fill_reteg_egy_undo(
        self, app_foltos, qt_app
    ):
        """Szomszéd-regresszió: betöltött réteg nélkül nincs mit halmozni."""
        window, _panel, edit = _megnyit(app_foltos, qt_app)
        csuszka = _item(window, "fixesFillSlider")

        _huzas(window, csuszka, qt_app, 0.1, 0.8)
        _huzas(window, csuszka, qt_app, 0.8, 0.4)

        assert len(_sorok(edit, "fill")) == 1, edit.property("chainValue")
        _kattint(window, _item(window, "editUndoButton"), qt_app)
        assert str(edit.property("chainValue")) == ""
        assert _gomb_aktiv(window, "editUndoButton") is False

    def test_egy_masik_gyakori_javitas_lezarja_a_latogatast(self, app_foltos, qt_app):
        """Szomszéd-regresszió: az Auto Contrast kattintás után a Derítőfény
        újabb húzása új réteg, a két `fill` között ott marad a másik javítás."""
        window, _panel, edit = _megnyit(app_foltos, qt_app)
        csuszka = _item(window, "fixesFillSlider")
        _huzas(window, csuszka, qt_app, 0.1, 0.5)
        _kattint(window, _item(window, "editToolAutolight"), qt_app)
        assert var_feltetelre(
            qt_app, lambda: "autolight" in str(edit.property("chainValue")), 8.0
        ), "az Auto Contrast kattintás nem került a láncba"

        _huzas(window, csuszka, qt_app, 0.1, 0.4)

        nevek = [e.split("=")[0] for e in str(edit.property("chainValue")).split(";") if e]
        assert nevek.count("fill") == 2, nevek
        assert nevek.index("autolight") < len(nevek) - 1 and nevek[-1] == "fill", nevek

    def test_a_hangolas_fulon_a_visit_modell_valtozatlan_ket_latogatas_ket_reteg(
        self, app_betoltott_fill, qt_app
    ):
        """Szomszéd-regresszió (E22): két Hangolás-látogatás két réteg, a
        betöltött `fill` mindkettő mellett érintetlen."""
        window, panel, edit = _megnyit(app_betoltott_fill, qt_app)
        _ful(panel, qt_app, _HANGOLAS_FUL)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.6)
        _ful(panel, qt_app, _ELSO_FUL)
        _ful(panel, qt_app, _HANGOLAS_FUL)
        _huzas(window, _item(window, "finetuneShadowsSlider"), qt_app, 0.1, 0.6)

        assert len(_sorok(edit, "finetune2")) == 2, edit.property("chainValue")
        assert _sorok(edit, "fill") == [["1", "0.5"]]
