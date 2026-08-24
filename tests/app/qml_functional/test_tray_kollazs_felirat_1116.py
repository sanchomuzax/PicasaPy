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
    def test_a_kuszob_mert_feliratszelessegbol_all(self):
        """#406 invariánsa: a küszöb a MÉRT feliratszélességből áll, nem
        fix képpontszámból — különben a szélesebb rendszerbetűvel
        (windows-CI) kilógna a sáv.

        #1116-ban a Kollázs gombnak KÜLÖN, magasabb küszöbe volt, mert a
        felirata a gomb MELLETT ült, és így szélesítette a sávot. A #1345
        óta a kimeneti gombok fix 55 × 36 képpontosak, a felirat a gombon
        BELÜL van: egyik kimeneti felirat sem szélesíti a sávot, ezért a
        külön kollázs-küszöb megszűnt. A küszöb egyetlen felirat-függő
        tagja a tartalomhoz igazodó zöld „Feltöltés" gomb maradt —
        a mérés elve viszont VÁLTOZATLAN, és ezt őrizzük itt."""
        assert "id: uploadLabelMetrics" in _QML_FORRAS
        kuszob = _QML_FORRAS.split(
            "readonly property real compactThreshold", 1
        )[1].split("readonly property bool compact:", 1)[0]
        assert "uploadLabelMetrics.width" in kuszob, (
            "a küszöb nem mért feliratszélességből áll"
        )
        assert "collageLabelMetrics" not in _QML_FORRAS, (
            "a külön kollázs-küszöb a #1345 óta tárgytalan"
        )

    def test_a_kollazs_felirata_nem_kuszobhoz_kotott(self):
        """A #1345 következménye: a Kollázs felirata nem tűnhet el.

        A gomb doboza fix, a felirat benne ül — a `visible` kötése ezért
        nem hivatkozhat semmilyen szélesség-küszöbre. (A LÁTHATÓSÁGOT
        magát a `tests/app/test_qml_tray_responsive.py` méri a valódi
        komponensen.)"""
        blokk = _QML_FORRAS.split("id: trayCollageBtn", 1)[1].split(
            "TrayActionCell {", 1
        )[0]
        assert "labelVisible" not in blokk
        assert "collageLabelVisible" not in _QML_FORRAS
