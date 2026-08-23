"""#1116: a Fotótálca Kollázs gombjának legyen felirata és buboréksúgója.

Az eredeti `outputlayout` sávjában a `collage` vezérlőnek felirata
(„Collage" → **„Kollázs"**) és súgója (`Create a Photo Collage with your
selection` → **„Készítsen fotókollázst a kijelölt képekből"**) is van; a
mi sávunk ráadásul önmagában sem volt egységes, mert a Nyomtatás/
Exportálás gombunk feliratos.

A `ToolTip` CSATOLT tulajdonság — Pythonból nem olvasható ki a
kirajzolt elemről (`test_collage_clips_tab_949.py` mintája), ezért a QML
forrását és a `.ts` fordítását állítjuk. A felirat LÁTHATÓSÁGÁT a
`tests/app/test_qml_tray_responsive.py` méri a valódi komponensen.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app

_QML_FORRAS = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")

_TS_FORRAS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

#: A gomb két szövege — forrás (angol) és a Picasa saját honosítási
#: táblájából átvett magyar (`outputlayout_text.tre`).
FELIRAT = ("Collage", "Kollázs")
SUGO = (
    "Create a Photo Collage with your selection",
    "Készítsen fotókollázst a kijelölt képekből",
)


class TestForrasszovegek:
    @pytest.mark.parametrize("angol", [FELIRAT[0], SUGO[0]])
    def test_a_qml_forditasra_jeloli(self, angol):
        assert f'qsTr("{angol}")' in _QML_FORRAS

    def test_a_gombnak_van_szoveg_tulajdonsaga(self):
        """A felirat a `text`-en át jön, mint a Nyomtatás/Exportálás
        gomboknál — így a súgó és a felirat egy forrásból származik."""
        blokk = _QML_FORRAS.split("id: trayCollageBtn", 1)[1].split("PicasaButton {", 1)[0]
        assert 'text: qsTr("Collage")' in blokk
        assert "ToolTip.text:" in blokk
        assert "trayCollageLabel" in blokk


class TestHivatalosMagyar:
    @pytest.mark.parametrize("angol,magyar", [FELIRAT, SUGO])
    def test_a_ts_ben_all(self, angol, magyar):
        assert f"<source>{angol}</source>" in _TS_FORRAS
        assert f"<translation>{magyar}</translation>" in _TS_FORRAS


class TestKompaktKuszob:
    def test_a_kollazs_feliratnak_sajat_mert_kuszobe_van(self):
        """#406 invariánsa: a küszöb a MÉRT feliratszélességekből áll,
        nem fix képpontszámból — különben a szélesebb rendszerbetűvel
        (windows-CI) kilógna a sáv.

        #1116: a Kollázs felirata nem fér bele az alap 1280 px-es ablakba
        a többi felirat mellé, ezért KÜLÖN, magasabb küszöbe van — így a
        gomb ikon-only marad, de a Nyomtatás/Exportálás felirata megmarad
        az alap ablakszélességen is."""
        assert "id: collageLabelMetrics" in _QML_FORRAS
        kuszob = _QML_FORRAS.split(
            "readonly property real collageLabelThreshold", 1
        )[1].split("readonly property bool collageLabelVisible", 1)[0]
        assert "compactThreshold" in kuszob
        assert "collageLabelMetrics.width" in kuszob
