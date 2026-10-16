"""A Szerkesztő fülei és vezérlői VALÓDI kattintással (#5150, 8. rész).

Lefedve (a jegy B-listájának „Szerkesztő" csoportja, Editor*.qml):
- `editTabEffects2`, `editTabEffects4` - a fül kattintása átvált a fülre;
- az effekt-csempék (EditorEffectsTab1 - 4): a paraméteres csempén
  megnyílik a csúszkás alpanel (`paramPanelActive` + `paramEffectName`),
  a paraméter nélküli csempe (`warm`, `cinemascope`) egy kattintásra a
  láncra kerül (`effectChainCounts`);
- vágó: `cropRotateButton`; finomhangolás: a három varázseszköz;
- vörösszem: `redeyeHideOutlinesCheck`, `redeyeUndoRegionButton`;
- `effectParamEraserCheckbox` (a radír jelölő a festhető effekt alpaneljén);
- `editToolEnhance`, `editToolAutocolor` (a csempe az eszközt küldi).

Már valódi kattintással lefedett csempék (nincs itt újra):
- `effectSepia`, `effectBw`: test_effect_tile_chain_refresh_4561.py (`_click`
  = QTest.mouseClick);
- `effectGlow2`, `effectRadblur`, `effectRadsat`, `effectDirTint`,
  `effectVignette`, `effectFocalZoom`, `editTabEffects`, `editTabEffects3`:
  test_param_panel_modal_4068.py (`_click`) és test_kiegyenesites_negyzethalo_3924.py
  (`_kattint`);
- `effectPixelate`, `effectFocalZoom`, `effectDirTint`:
  test_effect_focal_puck_4553.py (`QTest.mouseClick` a csempén);
- `effectPolaroid`: test_hatterszin_felirat_4560.py (`_click_item`);
- `effectPicnikGrain`: test_grain_renderelt_4936.py (`QTest.mouseClick`);
- `legacyEffect_linblur`, `legacyEffect_dir_sat`, `legacyEffect_dir_brite`,
  `legacyEffect_dir_sharp`: test_kiegyenesites_negyzethalo_3924.py (`_kattint`);
- `cropSuggestion0`: test_crop_gyorsvagas_4551.py (`QTest.mouseClick`);
- `redeyeAutoButton`, `redeyeResetButton`: test_voros_auto_undo_4541.py
  (az egéresemények küldése, press + release);
- `effectParamCheckbox` (a sablon, index 6): test_focal_pixelate_panel_3515.py;
- `showtextcheckbox`: test_editor_maradek_4183.py (a jelölő indikátora);
- `textFontFamilyBox`: test_text_system_fonts_qml_4546.py;
- `textAlign_left`, `textAlign_center`, `textAlign_right`:
  test_szoveg_igazito_ikonok_4547.py.

A hatást a felhasználó felől nézzük (alpanel, lánc, állapot). Parancsot
közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated` és nincs
`.emit()`. A csempe a fülön belül valódi kattintással érhető el.
"""

from __future__ import annotations

import pytest

from conftest import _build_qml_app, _negyzet_kepek
from _szerkeszto_5150_helpers import (
    figyel,
    fulre,
    item,
    kattint,
    nyitott_panel,
    szerkeszto,
    varj,
    vorosszem_nyitva,
)

#: a fülek: (objectName, a fül indexe a `activeTab`-ban)
FULEK = [
    ("editTabEffects2", 3),
    ("editTabEffects4", 5),
]

#: az effekt-csempék: (fül, a fül indexe, csempe, a szűrő kulcsa, alpanel-e)
#: `alpanel` True: paraméteres szűrő, a kattintás az alpanelt nyitja;
#: False: paraméter nélküli szűrő, a kattintás azonnal a láncra teszi.
EFFEKT_CSEMPEK = [
    ("editTabEffects", 2, "effectUnsharp", "unsharp2", True),
    ("editTabEffects", 2, "effectWarm", "warm", False),
    ("editTabEffects", 2, "effectGrain2", "picnikgrain", True),
    ("editTabEffects", 2, "effectAnsel", "ansel", True),
    ("editTabEffects2", 3, "effectIr", "ir", True),
    ("editTabEffects2", 3, "effectLomo", "lomo", True),
    ("editTabEffects2", 3, "effectHdr", "hdr", True),
    ("editTabEffects2", 3, "effectCinemascope", "cinemascope", False),
    ("editTabEffects2", 3, "effectOrton", "orton", True),
    ("editTabEffects2", 3, "effectHeatMap", "heatmap", True),
    ("editTabEffects2", 3, "effectCrossProcess", "crossprocess", True),
    ("editTabEffects2", 3, "effectQuantizePalette", "quantizepalette", True),
    ("editTabEffects2", 3, "effectTwoTone", "twotone", True),
    ("editTabEffects3", 4, "effectBoost", "boost", True),
    ("editTabEffects3", 4, "effectSoften", "soften", True),
    ("editTabEffects3", 4, "effectPencilSketch", "pencilsketch", True),
    ("editTabEffects3", 4, "effectNeon", "neon", True),
    ("editTabEffects3", 4, "effectComicize", "comicize", True),
    ("editTabEffects3", 4, "effectBorder", "border", True),
    ("editTabEffects3", 4, "effectDropShadow", "dropshadow", True),
    ("editTabEffects3", 4, "effectMuseumMatte", "museummatte", True),
    ("editTabEffects4", 5, "effectMatte", "matte", True),
    ("editTabEffects4", 5, "effectNightVision", "nightvision", True),
    ("editTabEffects4", 5, "effectLocalContrast", "localcontrast", True),
]


@pytest.mark.parametrize(("fulnev", "fulindex"), FULEK, ids=[f[0] for f in FULEK])
def test_fulre_valodi_kattintasra_atvalt(qml_app_negyzet_kepek, qt_app, fulnev, fulindex):
    window, _controller, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
    assert panel.property("activeTab") != fulindex, "a próba feltétele: más fül áll"

    fulre(window, qt_app, fulnev)

    assert varj(qt_app, lambda: panel.property("activeTab") == fulindex), (
        f"a(z) {fulnev} kattintás nem váltott a {fulindex}. fülre"
    )


@pytest.mark.parametrize(
    ("fulnev", "fulindex", "csempe", "kulcs", "alpanel"),
    EFFEKT_CSEMPEK,
    ids=[c[2] for c in EFFEKT_CSEMPEK],
)
def test_effektcsempe_valodi_kattintasra_a_helyes_utat_jarja_be(
    qml_app_negyzet_kepek, qt_app, fulnev, fulindex, csempe, kulcs, alpanel
):
    window, _controller, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
    fulre(window, qt_app, fulnev)
    assert panel.property("activeTab") == fulindex, (
        f"a próba feltétele: a(z) {fulnev} fül áll"
    )

    kattint(window, item(window, csempe), qt_app)

    if alpanel:
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            f"a(z) {csempe} kattintás nem nyitotta meg a paraméteres alpanelt"
        )
        assert panel.property("paramEffectName") == kulcs
    else:
        lanc = szerkeszto(viewer)
        assert varj(
            qt_app, lambda: lanc.property("effectChainCounts").get(kulcs, 0) == 1
        ), f"a(z) {csempe} kattintás nem tette a {kulcs} szűrőt a láncra"
        assert panel.property("paramPanelActive") is False


class TestVago:
    def test_forgatas_gomb_valodi_kattintasra_forgatast_ker(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        kattint(window, item(window, "editToolCrop"), qt_app)
        assert varj(qt_app, lambda: panel.property("cropActive") is True), (
            "a vágó eszköz nem aktiválódott"
        )
        kapott = figyel(panel.cropRotateRequested)

        kattint(window, item(window, "cropRotateButton"), qt_app)

        assert len(kapott) == 1, "a Forgatás kattintás nem kérte a forgatást"

    def test_elonezet_lenyomva_tartva_a_nyers_kepet_mutatja(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        kattint(window, item(window, "editToolCrop"), qt_app)
        assert varj(qt_app, lambda: panel.property("cropActive") is True)
        kapott = figyel(panel.cropPreviewHold)

        kattint(window, item(window, "cropPreviewButton"), qt_app)

        # a kattintás nyomása és engedése: a nyers kép be, majd ki
        assert kapott == [(True,), (False,)], (
            "az Előnézet kattintás nem jelezte a nyomást és az engedést"
        )


class TestFinomhangolas:
    def test_varazspalca_valodi_kattintasra_javitast_ker(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        fulre(window, qt_app, "editTabFinetune")
        assert varj(qt_app, lambda: panel.property("activeTab") == 1)
        kapott = figyel(panel.toolActivated)

        kattint(window, item(window, "finetuneLightingWand"), qt_app)

        assert kapott == [("autolight",)], (
            "a fényjavító varázspálca nem indította az automatikus fényjavítást"
        )

    def test_semleges_pipetta_valodi_kattintasra_bekapcsol(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        fulre(window, qt_app, "editTabFinetune")
        assert varj(qt_app, lambda: panel.property("activeTab") == 1)
        assert panel.property("neutralPickerActive") is False

        kattint(window, item(window, "finetuneNeutralPicker"), qt_app)

        assert varj(qt_app, lambda: panel.property("neutralPickerActive") is True), (
            "a semleges pipetta kattintás nem kapcsolta be a pipetta-módot"
        )

    def test_szinvarazspalca_valodi_kattintasra_szinjavitast_ker(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        fulre(window, qt_app, "editTabFinetune")
        assert varj(qt_app, lambda: panel.property("activeTab") == 1)
        kapott = figyel(panel.colorWandRequested)

        kattint(window, item(window, "finetuneColorWand"), qt_app)

        assert len(kapott) == 1, "a színes varázspálca kattintás nem kérte a javítást"


class TestVorosszem:
    def test_korvonal_jelolo_valodi_kattintasra_valt(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        vorosszem_nyitva(window, qt_app, panel)
        assert panel.property("redeyeHideOutlines") is False, (
            "a próba feltétele: nincs bekapcsolva"
        )

        kattint(window, item(window, "redeyeHideOutlinesCheck"), qt_app)

        assert varj(qt_app, lambda: panel.property("redeyeHideOutlines") is True), (
            "a körvonal-jelölő kattintás nem kapcsolta át az állapotot"
        )

    def test_visszavonas_gomb_valodi_kattintasra_visszaveszi_a_regiot(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        vorosszem_nyitva(window, qt_app, panel)
        lanc = szerkeszto(viewer)
        # állapot-előkészítés a controlleren: egy vörösszem-régió a képen
        lanc.addRedeyeRegion(0.3, 0.3, 0.2, 0.2)
        assert varj(qt_app, lambda: lanc.property("redeyeRegionCount") == 1), (
            "a próba feltétele: egy régió legyen"
        )

        kattint(window, item(window, "redeyeUndoRegionButton"), qt_app)

        assert varj(qt_app, lambda: lanc.property("redeyeRegionCount") == 0), (
            "a Visszavonás kattintás nem vette vissza a vörösszem-régiót"
        )


class TestGyakoriJavitasok:
    def test_javitas_csempe_valodi_kattintasra_a_hozza_tartozo_eszkozt_kuldi(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        kapott = figyel(panel.toolActivated)

        kattint(window, item(window, "editToolEnhance"), qt_app)

        assert kapott == [("enhance",)], "az Egy kattintásos javítás csempéje nem indította az eszközt"

    def test_auto_szin_csempe_valodi_kattintasra_a_hozza_tartozo_eszkozt_kuldi(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _c, _viewer, panel = nyitott_panel(qml_app_negyzet_kepek, qt_app)
        kapott = figyel(panel.toolActivated)

        kattint(window, item(window, "editToolAutocolor"), qt_app)

        assert kapott == [("autocolor",)], "az Automatikus szín csempéje nem indította az eszközt"


@pytest.fixture
def szemszinezett_app(qt_app, tmp_path):
    """Két négyzetkép; az elsőn a mentett lánc tartalmaz Vámpírszemet.

    A Vámpírszem (`ReanimatedEyeColor`) nincs csempeként a felületen, csak
    a mentett láncból jön: a `.picasa.ini` ezt a szűrőt írja az első képre.
    """

    def _keszit(lib):
        _negyzet_kepek(lib)
        (lib / ".picasa.ini").write_text(
            "[a.jpg]\nfilters=ReanimatedEyeColor=1,6.000000,20.000000;\n",
            encoding="utf-8",
        )

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_keszit)


class TestRadirJelolo:
    def test_radir_jelolo_valodi_kattintasra_radirra_valt(
        self, szemszinezett_app, qt_app
    ):
        window, _c, viewer, panel = nyitott_panel(szemszinezett_app, qt_app)
        lanc = szerkeszto(viewer)
        assert varj(qt_app, lambda: lanc.property("paintMaskSupported") is True), (
            "a próba feltétele: a képen van festhető (Vámpírszem) effekt"
        )
        fulre(window, qt_app, "editTabEffects")
        assert varj(qt_app, lambda: panel.property("activeTab") == 2)
        kattint(window, item(window, "effectUnsharp"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            "az élesítés csempéje nem nyitotta meg az alpanelt"
        )
        assert lanc.property("paintEraser") is False, "a próba feltétele: ecset, nem radír"

        kattint(window, item(window, "effectParamEraserCheckbox"), qt_app)

        assert varj(qt_app, lambda: lanc.property("paintEraser") is True), (
            "a radír jelölő kattintás nem váltott radírra"
        )
