"""#433: a diavetítés átmenetei, az átmenet-hossz és a feliratmód.

Az eredeti diavetítése **nem egyszerű képváltogatás**: a vezérlősávjában
átmenet-választó ül (`slideshowctrls/transtype`), és ugyanazt a 18-as
átmenet-készletet használja, mint a filmkészítő
(`docs/specs/picasa-create-features.md` 2.1). Az `SlideshowEffectTime` az
átmenet hossza, a `captionmode` a felirat módja.

Ebből az **öt** átmenet van meg, amelyik a Picasa jellegzetes érzetét adja
(`cut`, `dissolve`, `dissolveblack`, `dissolvewhite`, `kenburns`); a választó
**csak ezt** sorolja fel — a maradék 13 a filmkészítővel együtt jön (#432).

⚠️ Ez az őr a KÖTÉSEKET és a beállítás-tárolást méri, nem a látványt: azt,
hogy egy áttűnés „szépen" fut, gépi teszt nem tudja kimondani.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

_QML_DIR = Path(picasapy.app.__file__).parent / "qml"
_VIEW = (_QML_DIR / "PicasaPy" / "SlideshowView.qml").read_text(encoding="utf-8")
_MAIN = (_QML_DIR / "Main.qml").read_text(encoding="utf-8")

ATMENETEK = ("cut", "dissolve", "dissolveblack", "dissolvewhite", "kenburns")


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache

    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    with open_index(tmp_path / "index.db"):
        pass
    return AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )


class TestAMegorzottBeallitasok:
    def test_az_alapertek_a_dissolve(self, controller):
        """A Picasa jellegzetes átmenete — a `cut` nem alapértelmezés."""
        assert controller.slideshowTransition == "dissolve"

    @pytest.mark.parametrize("kulcs", ATMENETEK)
    def test_mind_az_ot_atmenet_tarolhato(self, controller, kulcs):
        controller.setSlideshowTransition(kulcs)
        assert controller.slideshowTransition == kulcs

    def test_az_ISMERETLEN_kulcsot_nem_tarolja(self, controller):
        """Egy elgépelt érték némán átmenet nélküli vetítést adna."""
        controller.setSlideshowTransition("dissolve")
        controller.setSlideshowTransition("wipeleft")  # még nincs megvalósítva
        assert controller.slideshowTransition == "dissolve"

    def test_az_atmenet_hossza_a_dia_ido_alatt_marad(self, controller):
        """Ha az átmenet hosszabb a dia-időnél, sosem fejeződik be — a
        vezérlő ezért felső korlátot tart."""
        assert 0 < controller.slideshowTransitionMs <= 500

    @pytest.mark.parametrize("mod", ["caption", "filename", "none"])
    def test_a_feliratmod_harom_allasa(self, controller, mod):
        controller.setSlideshowCaptionMode(mod)
        assert controller.slideshowCaptionMode == mod

    def test_az_ismeretlen_feliratmodot_nem_tarolja(self, controller):
        controller.setSlideshowCaptionMode("caption")
        controller.setSlideshowCaptionMode("exif")
        assert controller.slideshowCaptionMode == "caption"

    def test_a_beallitas_TULELI_az_ujrainditast(self, controller, tmp_path):
        """A megőrzés a beállítás-tárolóba megy, nem a példányba."""
        controller.setSlideshowTransition("kenburns")
        friss = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        assert friss.value("view/slideshowTransition") == "kenburns"


class TestAValasztoAVezerlosavban:
    def test_a_valaszto_ott_van(self):
        assert 'objectName: "slideshowTransitionBox"' in _VIEW

    def test_CSAK_a_megvalositott_otot_sorolja(self):
        """A választó nem hirdethet olyan átmenetet, ami nem fut le."""
        kezd = _VIEW.index("readonly property var atmenetek:")
        blokk = _VIEW[kezd : kezd + 700]
        for kulcs in ATMENETEK:
            assert f'kulcs: "{kulcs}"' in blokk
        for nem_kesz in ("wipeleft", "circlein", "pushright", "timelapse"):
            assert nem_kesz not in blokk

    def test_a_valaszto_NEM_ir_kozvetlenul_beallitast(self):
        """A gazda dönti el, hova kerül — a `starToggled` mintája."""
        assert "signal transitionPicked(string kulcs)" in _VIEW
        assert "onTransitionPicked:" in _MAIN

    def test_a_feliratmod_gombja_korbejar(self):
        kezd = _VIEW.index('objectName: "slideshowCaptionModeButton"')
        blokk = _VIEW[kezd : kezd + 500]
        assert "feliratModok.indexOf" in blokk
        assert "captionModePicked" in blokk

    def test_a_gazda_a_MEGORZOTT_erteket_koti_be(self):
        assert "transitionKind: controller ? controller.slideshowTransition" in _MAIN
        assert "captionMode: controller ? controller.slideshowCaptionMode" in _MAIN


class TestAzAtmenetMotorja:
    def test_a_kimeno_dia_SAJAT_elem(self):
        """Áttűnéshez két kép kell — egyetlen `Image`-en nem megy."""
        assert 'objectName: "slideshowPrevImage"' in _VIEW

    def test_a_fatyol_a_fekete_feher_attuneshez(self):
        kezd = _VIEW.index('objectName: "slideshowVeil"')
        assert 'color: "#000000"' in _VIEW[kezd : kezd + 300]
        assert 'fatyol.color = show.transitionKind === "dissolvewhite"' in _VIEW

    def test_a_cut_NEM_animal(self):
        kezd = _VIEW.index("function _atmenetIndit(")
        blokk = _VIEW[kezd : kezd + 700]
        assert 'show.transitionKind === "cut"' in blokk
        assert "return" in blokk

    def test_a_kenburns_a_DIA_idojehez_kotott(self):
        """A nagyítás a tartózkodás alatt fut, nem az átmenet alatt."""
        kezd = _VIEW.index('objectName: "slideshowKenBurns"')
        blokk = _VIEW[kezd : kezd + 400]
        assert "show.intervalMs" in blokk
        assert "show.transitionMs" not in blokk

    def test_a_felirat_a_MOD_szerint_valt(self):
        kezd = _VIEW.index("readonly property string aktualisFelirat:")
        blokk = _VIEW[kezd : kezd + 700]
        assert 'show.captionMode === "none"' in blokk
        assert 'show.captionMode === "filename"' in blokk
        assert "captionAt(show.currentIndex)" in blokk
