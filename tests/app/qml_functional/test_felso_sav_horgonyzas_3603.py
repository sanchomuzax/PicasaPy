"""A felső eszköztár bal gombsora és a keresősáv horgonyzása — KIRAJZOLVA
(#3603, a #3582 R2/R3-összevetésének két talált eltérése).

## Honnan jönnek a számok

A tulajdonos 1917 px széles Picasa-képernyőképe
(`research/testdata/screenshot/Képernyőkép 2026-07-18 150933.png`) +
a `thumbui.tre`/`searchcontainer.tre` kényszerei, levezetve a
`docs/specs/picasa-fo-ablak-elrendezes.md` „R2/R3" szakaszában:

- a négy bal gomb FIX bal-felső horgonyú (`m_offsetLT`): x 6 / 124 / 160
  (190) / 225, mind y 9 a sáv tetejétől — az ablakszélességtől FÜGGETLEN;
- a szűrőzóna bal széle `0,4 · W − 2` (`filterbase`);
- a keresőmező látható kerete (`searchbase`, 24 magas) bal széle
  `0,4 · W + 238`, jobb széle `W − 47` (kizáró), teteje a sávtól 7.

A képen mért keret: x 1006 … 1872 (a jobb szélső keretoszlop 1872, tehát
a kizáró jobb szél 1873), y 50 … 73 a sáv 43-as tetejéhez; a szűrők 766-nál
kezdődnek. Ez a képlet **W = 1920**-as értéke, nem az 1917-esé: a kép 1917
képpont széles, de a Picasa-ablak kliensterülete 1920 volt, és a jobb
szélső 3 képpontja lemaradt a képről (az ablak jobb kerete nem látszik, az
utolsó oszlop is a sáv szürkéje). Ezért a képpel való egyezést az 1920-as
kirajzolás méri, az 1917-es kirajzolás pedig a képletet.

## Miért KIRAJZOLT, jelenet-koordinátában

A `MainToolbar.qml` a `Main.qml` `header:`-je — a `mainToolbar`
koordinátarendszerében mérünk (`mapToItem`), mert a bal gombsor és a
kereső/szűrő-zóna a `content` belső `Item` gyerekei.

A `TestAKirajzoltKep` a `grabWindow()` képén, képpont-oszlopokat és
-sorokat keresve állapítja meg a keret és a gombok szélét — nem a
property-kből számol. A helyi referenciakép a CI-n nincs meg
(`research/` a `.gitignore`-ban), ezért a teszt a jegy képről mért
számaival veti össze a kirajzolt képet. Az új album és a ▾ gomb kerete
csak rámutatásra rajzolódik ki, ezért azok helyét a geometria méri.

## A verziófelirat

A verziófelirat (#706) saját elemünk, az eredetiben ott semmi nincs. A
mező mögötti 47 px-en él: csak a rövid verzió látszik („v0.8.590”), a
build-azonosító a buboréksúgóban.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF

#: Egy képpont tűrés: a QML geometriája tört szám lehet (0,4 · W).
TURES = 1.0

#: A mért ablakszélességek — az 1917 a referenciakép szélessége.
ABLAKOK = (1280, 1600, 1917, 1920)

#: A jegy képről mért számai (W = 1920 kliensszélesség, ld. a fejlécet).
KEP_1920 = {
    "import_bal": 6,
    "sikbeli_bal": 160,
    "fanezet_bal": 190,
    "mezo_bal": 1006,
    "mezo_jobb_keretoszlop": 1872,
    "mezo_teteje": 7,
    "mezo_alja_keretsor": 30,
}

#: Ennyivel kell eltérnie egy képpontnak (a három csatorna összegében) a
#: sáv hátterétől, hogy él legyen. A mező kerete (`chromeBorder`) halvány:
#: a különbség ~60.
ELKULONBSEG = 30

GOMBOK = (
    "toolbarImportButton",
    "toolbarNewAlbumButton",
    "toolbarFolderViewToggle",
    "toolbarFolderViewPopupButton",
)


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _szelesseg(window, qt_app, szelesseg: int) -> None:
    window.setProperty("width", szelesseg)
    for _ in range(4):
        qt_app.processEvents()


def _x_a_savban(window, nev: str) -> float:
    sav = _elem(window, "mainToolbar")
    return _elem(window, nev).mapToItem(sav, QPointF(0, 0)).x()


def _y_a_savban(window, nev: str) -> float:
    sav = _elem(window, "mainToolbar")
    return _elem(window, nev).mapToItem(sav, QPointF(0, 0)).y()


def _jobb_szel(window, nev: str) -> float:
    return _x_a_savban(window, nev) + _elem(window, nev).property("width")


class TestABalGombsorFixHelye:
    """A négy gomb x/y-ja NEM függ az ablakszélességtől."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_negy_gomb_x_helye(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _x_a_savban(window, "toolbarImportButton") == pytest.approx(6, abs=TURES)
        assert _x_a_savban(window, "toolbarNewAlbumButton") == pytest.approx(124, abs=TURES)
        assert _x_a_savban(window, "toolbarFolderViewToggle") == pytest.approx(160, abs=TURES)
        assert _x_a_savban(window, "toolbarFolderViewPopupButton") == pytest.approx(225, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_nezetvalto_par_belso_x_helye(self, qml_app_module, qt_app, ablak):
        """`flatview` 160, `folderview` 190 — a `hviewtoggle` csoporton belül."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _x_a_savban(window, "toolbarFlatViewButton") == pytest.approx(160, abs=TURES)
        assert _x_a_savban(window, "toolbarTreeViewButton") == pytest.approx(190, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_negy_gomb_teteje_a_sav_tetejetol_9(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        for nev in GOMBOK:
            assert _y_a_savban(window, nev) == pytest.approx(9, abs=TURES), nev


class TestASzuroesKeresoKeplet:
    """A szűrőzóna és a keresőmező az ablakszélesség FÜGGVÉNYE."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_szurozona_bal_szele(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        vart = 0.4 * ablak - 2
        assert _x_a_savban(window, "toolbarFilterZone") == pytest.approx(vart, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_bal_szele(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        vart = 0.4 * ablak + 238
        assert _x_a_savban(window, "toolbarSearchBox") == pytest.approx(vart, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_jobb_szele_W_minusz_47(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _jobb_szel(window, "toolbarSearchBox") == pytest.approx(
            ablak - 47, abs=TURES
        )

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_keresomezo_teteje_7_magassaga_24(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _y_a_savban(window, "toolbarSearchBox") == pytest.approx(7, abs=TURES)
        assert _elem(window, "toolbarSearchBox").property("height") == 24


class TestAVerziofelirat:
    """A felirat a mező mögötti 47 px-en fér el."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_mezo_mogotti_savban_marad(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        bal = _x_a_savban(window, "versionLabel")
        assert bal >= _jobb_szel(window, "toolbarSearchBox") + 2, (
            f"{ablak}px-nél a verziófelirat ({bal}) a mezőre lóg"
        )
        assert _jobb_szel(window, "versionLabel") <= ablak

    def test_csak_a_rovid_verzio_latszik(self, qml_app_module):
        from picasapy import __version__
        from picasapy.version import version_string

        cimke = _elem(qml_app_module[0], "versionLabel")
        assert cimke.property("text") == f"v{__version__}"
        assert cimke.property("fullText") == version_string()

    def test_a_build_azonosito_a_buboreksugoban(self, qml_app_module):
        from picasapy.version import version_string

        cimke = _elem(qml_app_module[0], "versionLabel")
        assert version_string() in cimke.property("tooltipText")


class TestASzukAblak:
    """A #423 elrejtése csak a számolt küszöb (675 px) alatt dolgozik, és
    a négy bal gomb soha nem rejtőzik el."""

    def test_a_kuszob_a_szamolt_utkozesi_pont(self, qml_app_module):
        # max((247 + 2) / 0,4 = 622,5 ; (120 + 285) / 0,6 = 675)
        sav = _elem(qml_app_module[0], "mainToolbar")
        assert sav.property("compactWidth") == pytest.approx(675)

    @pytest.mark.parametrize("ablak", (600, 674, 676, 800, 1280))
    def test_a_negy_gomb_mindig_latszik(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        for nev in GOMBOK:
            assert _elem(window, nev).property("visible") is True, (ablak, nev)

    @pytest.mark.parametrize(
        ("ablak", "latszik"), ((674, False), (676, True), (800, True))
    )
    def test_a_szurozona_a_kuszobnel_rejtozik(
        self, qml_app_module, qt_app, ablak, latszik
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _elem(window, "toolbarFilterZone").property("visible") is latszik

    @pytest.mark.parametrize("ablak", (600, 674, 676, 800))
    def test_a_mezo_nem_log_ra_semmire_es_van_merete(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        mezo_bal = _x_a_savban(window, "toolbarSearchBox")
        mezo_jobb = _jobb_szel(window, "toolbarSearchBox")
        assert mezo_jobb - mezo_bal >= 120, f"{ablak}px-nél a mező túl keskeny"
        assert mezo_jobb <= _x_a_savban(window, "versionLabel") - 2
        assert mezo_bal >= _jobb_szel(window, "toolbarFolderViewPopupButton")
        if _elem(window, "toolbarFilterZone").property("visible"):
            assert mezo_bal >= _jobb_szel(window, "toolbarFilterZone")
            assert _x_a_savban(window, "toolbarFilterZone") >= _jobb_szel(
                window, "toolbarFolderViewPopupButton"
            )


def _kep_es_sav_teteje(window, qt_app, ablak):
    _szelesseg(window, qt_app, ablak)
    window.setProperty("height", 700)
    for _ in range(4):
        qt_app.processEvents()
    sav = _elem(window, "mainToolbar")
    return window.grabWindow(), round(sav.mapToScene(QPointF(0, 0)).y())


def _osszeg(kep, x: int, y: int) -> int:
    szin = kep.pixelColor(x, y)
    return szin.red() + szin.green() + szin.blue()


def _elso_oszlop(kep, xek, y, hatter):
    return next(
        (x for x in xek if abs(_osszeg(kep, x, y) - hatter) > ELKULONBSEG), None
    )


def _elso_sor(kep, x, yok, hatter):
    return next(
        (y for y in yok if abs(_osszeg(kep, x, y) - hatter) > ELKULONBSEG), None
    )


def _meresek(kep, teteje: int, ablak: int) -> dict:
    """A keret és a gombok széle a KÉPPONTOKBÓL — property-t nem olvas."""
    kozep = teteje + 19
    # a sáv háttere a szűrőzóna jobb széle (0,4·W + 222) és a mező bal
    # széle (0,4·W + 238) közötti résből
    res_x = int(0.4 * ablak + 230)
    hatter = _osszeg(kep, res_x, kozep)
    mezo_bal = _elso_oszlop(kep, range(res_x, ablak), kozep, hatter)
    # jobbról a verziófelirat előtti résből (W − 44) indulunk balra
    mezo_jobb = _elso_oszlop(kep, range(ablak - 44, res_x, -1), kozep, hatter)
    oszlop = mezo_bal + 40
    mezo_teteje = _elso_sor(kep, oszlop, range(teteje, teteje + 35), hatter)
    mezo_alja = _elso_sor(kep, oszlop, range(teteje + 33, teteje, -1), hatter)
    # a nézetváltó pár kerete a gombsor alsó sorában (9 + 22 − 1 = 30)
    also = teteje + 30
    return {
        "import_bal": _elso_oszlop(kep, range(0, 60), kozep, hatter),
        "mezo_bal": mezo_bal,
        "mezo_jobb_keretoszlop": mezo_jobb,
        "mezo_teteje": mezo_teteje - teteje,
        "mezo_alja_keretsor": mezo_alja - teteje,
        "nezetvalto": [
            x
            for x in range(150, 230)
            if abs(_osszeg(kep, x, also) - hatter) > ELKULONBSEG
        ],
    }


class TestAKirajzoltKep:
    """A `grabWindow()` képén keresett élek a jegy képről mért számaival."""

    def test_1920_on_a_kep_szamai(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        kep, teteje = _kep_es_sav_teteje(window, qt_app, 1920)
        m = _meresek(kep, teteje, 1920)
        for kulcs in (
            "import_bal",
            "mezo_bal",
            "mezo_jobb_keretoszlop",
            "mezo_teteje",
            "mezo_alja_keretsor",
        ):
            assert m[kulcs] == pytest.approx(KEP_1920[kulcs], abs=1), (kulcs, m)
        # a sík/fa pár kerete 160-nál kezdődik, és a 190-es határon át fut
        assert m["nezetvalto"], m
        assert m["nezetvalto"][0] == pytest.approx(KEP_1920["sikbeli_bal"], abs=1)
        assert any(abs(x - KEP_1920["fanezet_bal"]) <= 1 for x in m["nezetvalto"])

    def test_1917_en_a_keplet(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        kep, teteje = _kep_es_sav_teteje(window, qt_app, 1917)
        m = _meresek(kep, teteje, 1917)
        assert m["mezo_bal"] == pytest.approx(0.4 * 1917 + 238, abs=1), m
        # kizáró jobb szél W − 47 → az utolsó keretoszlop W − 48
        assert m["mezo_jobb_keretoszlop"] == pytest.approx(1917 - 48, abs=1), m
        assert m["mezo_teteje"] == pytest.approx(7, abs=1), m
        assert m["import_bal"] == pytest.approx(6, abs=1), m
