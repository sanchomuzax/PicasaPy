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
    # ⚠️ CSAK a szöveg, a `qsTr(...)` burkolat NÉLKÜL: a #1420-ban a
    # hívás két sorra tördelődött, és az egzakt alakra menő egyeztetés
    # elbukott — miközben a súgó változatlanul ott volt. A felirat léte a
    # követelmény, nem a forrás formázása.
    "Create a Photo Collage with your selection",
    "Készítsen fotókollázst a kijelölt képekből",
)


class TestForrasszovegek:
    @pytest.mark.parametrize("angol", [FELIRAT[0], SUGO[0]])
    def test_a_qml_forditasra_jeloli(self, angol):
        """A `qsTr(...)` burkolat és a szöveg KÜLÖN mérve.

        ⚠️ Az egzakt `qsTr("…")` alakra menő egyeztetés a #1420-ban
        elbukott, mert az elrendezés-átépítés a hívást két sorra tördelte —
        miközben a súgó változatlanul ott volt, fordításra jelölve. Az őr
        a KÖVETELMÉNYT mérje (a szöveg fordítható), ne a forrás
        formázását."""
        # a forrást szóköz-normalizálva nézzük: a sortörés és a behúzás
        # a `qsTr(` után nem viselkedésbeli különbség
        tomor = " ".join(_QML_FORRAS.split())
        assert angol in tomor, "a felirat eltűnt a forrásból"
        assert f'qsTr( "{angol}"' in tomor or f'qsTr("{angol}"' in tomor, (
            f"ez a felirat nincs qsTr(...)-be csomagolva, tehat nem "
            f"forditható: {angol}"
        )

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
    def test_a_kuszob_MAR_NEM_feliratszelessegbol_all(self):
        """⚠️ MEGFORDÍTOTT ŐR (#1420) — az eredeti állítás tárgytalan.

        A #406 invariánsa az volt, hogy a küszöb a MÉRT feliratszélességből
        álljon, különben a szélesebb rendszerbetűvel (windows-CI) kilógna a
        sáv. Ez akkor helyes volt.

        A #1420-ban a sáv a binárisból mért elrendezést kapta: a zöld
        „Feltöltés" gomb is FIX méretű (141 × 35 egy 147 × 44-es helyen),
        tehát a sávban **egyetlen felirat sem szélesít semmit**. A küszöb
        ezért tiszta geometria lett — és ez nem visszalépés, hanem épp azt a
        csapdát szünteti meg, amin a #1367 elbukott: ott a mért szélesség
        helyben 850, a CI-futón 860 volt, mert a betű más.

        Ez az őr ellenkező irányban áll helyt: ha valaki VISSZAHOZZA a
        feliratszélesség-mérést a küszöbbe, itt bukik, és ezt a
        magyarázatot kapja."""
        assert "uploadLabelMetrics" not in _QML_FORRAS, (
            "visszakerült a feliratszélesség-mérés a küszöbbe. A #1420 óta a "
            "sáv geometriája fix (a zöld gomb is), tehát erre nincs szükség — "
            "és a betűszélesség platformonként eltér (#1367: helyi 850 / CI 860)."
        )
        assert "collageLabelMetrics" not in _QML_FORRAS, (
            "a külön kollázs-küszöb a #1345 óta tárgytalan"
        )
        assert "separatorThreshold" in _QML_FORRAS, (
            "a küszöbnek léteznie kell — csak már geometriából, nem betűből"
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
