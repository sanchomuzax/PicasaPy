"""Az alsó sáv 105 képpontja és a 36,5 %-os osztópont — KIRAJZOLVA (#1420).

## Honnan jönnek a számok

A Picasa saját elrendezés-forrásából (`respack.yt` → `thumbui.tre`), és
minden egyes szám VISSZAMÉRVE egy valódi Picasa-képernyőképen
(`research/testdata/screenshot/Képernyőkép 2026-07-18 145027.png`,
1918 × 1030 — az ablak alja 2 képponttal le van vágva, ezért látszik a
sáv 105 helyett 103 képpontja):

| forrás | elem | kényszer | a képernyőképen (ablak: 1918 px) |
|---|---|---|---|
| `thumbui.tre` | `publishbottom` | −105 | a sáv teteje y = 927, a 105 px vége 1032 |
| `thumbui.tre` | `scratchback` | `0,0,5` … `1,.365,-15` | **x 5…684**, **y 947…1027 = 81 px** |
| `thumbui.tre` | `separator` | `0,.365,-3` … `1,1,-17`, y 50…52 | **x 697…1902**, y 977…978 |
| `thumbui.tre` | `webupload_rect` | `0,.365,-5` … `1,.365,140` | a gomb **x 697…837 = 141 px**, y 988…1022 = **35 px** |
| `thumbui.tre` | `outputs` | `0,.365,140` … `1,1,-10` | az első gomb közepe x 867,5 = 840 + 55/2 |
| `konyvtar-ablak-meretek.md` 5.4 | `startoggle`/`rotate*` | 36 × 22 | **x 697…732, 738…773, 775…810** |

`0,365 × 1918 = 700,07` — tehát a mért `697 = osztópont − 3` és a
`684 = osztópont − 15 − 1` a kényszerekkel képpontra egyezik.

## Melyik állítás beégetett és melyik relatív — és miért

- **Beégetett** minden olyan méret, ami a QML-ben literálként áll és nem
  felirat-szélességből származik: 105 · 20 · 85 · 81 · 141 × 35 ·
  147 × 44 · 59. Ezek betűtől és platformtól függetlenek.
- **Relatív** az osztópont: nem képpontszám, hanem az ablakszélesség
  0,365-szörösének kerekítettje — ezért három ablakszélességen mérjük.
- **Relatív** a szélesség-igény őrzése: a `requiredWidth` most már TISZTA
  GEOMETRIA (nincs benne feliratszélesség), de az őr akkor is ÉLŐBEN
  méri, hogy a minimumra állított ablakban tényleg nem lóg ki semmi — ez
  fogja meg, ha egy betűfüggő elem (a − / + jelek, a „Kijelölés" felirat)
  mégis megnő.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF

#: Fél képpont tűrés: a QML geometriája tört szám lehet.
TURES = 0.5

#: A mért ablakszélességek — a `Main.qml` alapmérete és két nagyobb.
ABLAKOK = (1280, 1600, 1920)


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _szelesseg(window, qt_app, szelesseg: int) -> None:
    window.setProperty("width", szelesseg)
    for _ in range(4):
        qt_app.processEvents()


def _x_a_savban(window, nev: str) -> float:
    """Az elem bal széle a `trayMainBar` koordinátarendszerében.

    ⚠️ A mérés EGYSÉGE itt lapegység (a QML logikai képpontja), és
    minden összehasonlítás ugyanabban az egységben történik — ezért nem
    kell képernyő-skálázással számolni.
    """
    sav = _elem(window, "trayMainBar")
    elem = _elem(window, nev)
    return elem.mapToItem(sav, QPointF(0, 0)).x()


def _y_a_savban(window, nev: str) -> float:
    sav = _elem(window, "trayMainBar")
    elem = _elem(window, nev)
    return elem.mapToItem(sav, QPointF(0, 0)).y()


class TestASavMagassaga:
    """`publishbottom` = −105: az alsó sáv 105 képpont, és a tartalom
    tölti ki.

    ⚠️ #1914: a felosztás MEGVÁLTOZOTT. A #1420-ban a csík 20 képpont
    volt — „szándékos eltérés a 14-től, olvashatóságért" —, és épp ettől
    ÉRTEK a gombok a kék csíkhoz, amit a tulajdonos élesben jelentett.
    A #1914 a `respack.yt` rétegfejléceiből kimérte a teljes függőleges
    felosztást (a tálca függőlegesen 1:1-ben képpont, két független
    méréssel igazolva):

        infotext      y 429…443   14 magas
        vezérlők       y 448-tól   ⇒ 5 pont TÉRKÖZ
        scratchback   y 449…530   81 magas
        a sáv alja    y 534        ⇒ 5 pont alsó hézag

        14 + 5 + 81 + 5 = 105 ✓

    A különbség tehát nem az olvashatóságé volt, hanem a hiányzó
    térközé. A mérés felülírja a saját döntésünket."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_teljes_sav_105_kepont(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        assert _elem(window, "trayBar").property("height") == 105

    def test_a_sav_ket_resze_14_es_91(self, qml_app_module, qt_app):
        """#1914: a MÉRT felosztás — 14 (`infotext`) + 91 = 105."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        assert _elem(window, "trayInfoBar").property("height") == 14
        assert _elem(window, "trayMainBar").property("height") == 91

    def test_a_keptalca_81_magas_5_terkozzel_es_5_also_hezaggal(
        self, qml_app_module, qt_app
    ):
        """#1914: `scratchback` y 449…530 a `basecontrolset` 429…534-én
        belül ⇒ a kék csík (…443) alatt **5 pont térköz**, alul **5**.

        Ez a jegy lényege: az 5 pontos térköz hiányzott, ezért értek a
        gombok a csíkhoz."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        sav = _elem(window, "trayMainBar")
        talca = _elem(window, "trayScratchBack")
        assert talca.property("height") == 81
        assert _y_a_savban(window, "trayScratchBack") == pytest.approx(5, abs=TURES), (
            "a kék csík alól hiányzik az 5 pontos MÉRT térköz (#1914)"
        )
        alsó_hézag = sav.property("height") - (
            _y_a_savban(window, "trayScratchBack") + talca.property("height")
        )
        assert alsó_hézag == pytest.approx(5, abs=TURES)

    def test_nincs_holt_sav_a_jobb_oldalon(self, qml_app_module, qt_app):
        """A magasságot ÖNMAGÁBAN emelni hiba lenne: a jobb oldalon is
        tartalomnak kell kitöltenie a sávot.

        ⚠️ #1914: a korlát mostantól MÉRT érték, nem a sajátunk. Az
        eredetiben a zöld gomb (`thumbui/superbutton(...): webupload`)
        y 490…525, a `basecontrolset` alja y 534 ⇒ **9 pont** hézag alatta.
        Korábban itt a saját elrendezésünkből vett 5 állt, és a MÉRT
        térköz bevezetésekor (a csík 20→14, a doboz +5) ez 6-ra mozdult —
        a szám a mi elrendezésünké volt, nem az eredetié.

        Az állítás célja változatlan: NE maradjon holt sáv. A mérce a
        mért 9."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        sav = _elem(window, "trayMainBar")
        hely = _elem(window, "trayUploadSlot")
        alja = _y_a_savban(window, "trayUploadSlot") + hely.property("height")
        hezag = sav.property("height") - alja
        assert 0 <= hezag <= 9, (
            f"{hezag:.0f} pont holt sáv a jobb oldal alján; az eredetiben a "
            "zöld gomb alatt 9 pont marad (y 525 → 534)"
        )


class TestAzOsztopont:
    """A sáv az ablakszélesség 0,365-szörösénél válik ketté."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_keptalca_5_tol_az_osztopont_minusz_15_ig_er(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        assert osztopont == pytest.approx(round(ablak * 0.365), abs=TURES)
        talca = _elem(window, "trayScratchBack")
        assert _x_a_savban(window, "trayScratchBack") == pytest.approx(5, abs=TURES)
        jobb_szel = _x_a_savban(window, "trayScratchBack") + talca.property("width")
        assert jobb_szel == pytest.approx(osztopont - 15, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_jobb_sav_az_osztoponton_kezdodik(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        assert _x_a_savban(window, "trayRightPane") == pytest.approx(
            osztopont, abs=TURES
        )
        jobb = _elem(window, "trayRightPane")
        jobb_szel = _x_a_savban(window, "trayRightPane") + jobb.property("width")
        assert jobb_szel == pytest.approx(ablak - 10, abs=TURES)

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_muveletsor_az_osztopont_plusz_140_nel_kezdodik(
        self, qml_app_module, qt_app, ablak
    ):
        """`outputs`: `XConstraint 0, .365, 140`."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        assert _x_a_savban(window, "trayActionRow") == pytest.approx(
            osztopont + 140, abs=TURES
        )


class TestAZoldGomb:
    """`webupload` 141 × 35 egy `webupload_rect` 147 × 44-es helyen, az
    osztóponttól 5 képponttal balra kezdve."""

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_hely_147x44_az_osztopont_minusz_5_nel(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        osztopont = _elem(window, "trayMainBar").property("splitX")
        hely = _elem(window, "trayUploadSlot")
        assert hely.property("width") == 147
        assert hely.property("height") == 44
        assert _x_a_savban(window, "trayUploadSlot") == pytest.approx(
            osztopont - 5, abs=TURES
        )

    def test_a_gomb_141x35(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayUploadButton")
        assert gomb.property("width") == 141
        assert gomb.property("height") == 35

    def test_a_gomb_felirata_tordel_es_nem_csonkul(self, qml_app_module, qt_app):
        """A felirat KÉT SORBA tördel a 141 képpontos gombban — pontosan
        úgy, ahogy az eredetin („Feltöltés a Google / Fotókba").

        A `>= 2` sorszám RELATÍV állítás, nem képpontszám: azt a hibát
        fogja meg, amikor a `Text.Fit` a tördelés HELYETT egyetlen,
        zsugorított sorra esik vissza. Ez élesben megtörtént: a felirat
        magassága a saját `contentHeight`-je volt (a `Row`-ban nem kapott
        explicit magasságot), és a `Text.Fit` ebbe a körbe futva 9
        képpontos, egysoros megoldást választott. Szélesebb rendszerbetűnél
        a sorszám csak NŐHET, tehát az állítás nem platformfüggő."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayUploadButton")
        felirat = _elem(window, "trayUploadLabel")
        assert felirat.property("width") <= gomb.property("width") + TURES
        assert felirat.property("lineCount") >= 2, (
            "a felirat egyetlen sorba szorult — a Text.Fit zsugorított "
            "a tördelés helyett"
        )
        assert felirat.property("truncated") is False
        assert felirat.property("contentWidth") <= felirat.property("width") + TURES
        assert felirat.property("contentHeight") <= felirat.property("height") + TURES


class TestSzelessegIgeny:
    """A #1345 és a #1367 mért állandói — ÚJRAMÉRVE a #1420 elrendezésén.

    Az új sávban a szélesség-igény TISZTA GEOMETRIA: a jobb oldal az
    ablak 63,5 %-a mínusz 10, ebbe kell beleférnie a 140 képpontos
    eltolásnak és a fix 59 képpontos celláknak. Feliratszélesség NINCS
    benne — épp az a csapda tűnt el, amin a windows-CI egyszer elbukott.
    """

    def test_az_ablak_minimuma_fedi_a_sav_igenyet(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        sav = _elem(window, "trayMainBar")
        assert window.property("minimumWidth") >= sav.property("requiredWidth")

    def test_a_minimumon_semmi_nem_log_ki(self, qml_app_module, qt_app):
        """ÉLŐ mérés: a minimumra állított ablakban a sáv minden
        (takaratlan, saját geometriájú) eleme a sávon belül marad."""
        window, _, _ = qml_app_module
        minimum = int(window.property("minimumWidth"))
        _szelesseg(window, qt_app, minimum)
        sav = _elem(window, "trayMainBar")
        for nev in (
            "trayScratchBack",
            "trayRightPane",
            "trayActionRow",
            "trayUploadSlot",
            "trayUploadButton",
            "trayZoomGroup",
        ):
            elem = _elem(window, nev)
            bal = elem.mapToItem(sav, QPointF(0, 0)).x()
            jobb = bal + elem.property("width")
            assert bal >= -TURES, f"{nev} balra lóg ki: {bal}"
            assert jobb <= sav.property("width") + TURES, (
                f"{nev} jobbra lóg ki: {jobb} > {sav.property('width')}"
            )

    def test_a_ket_sor_nem_er_egymasba_a_minimumon(self, qml_app_module, qt_app):
        """A jobb oldal két sora (fent ★/forgatás/csúszka, lent zöld gomb
        + műveletsor) a minimumon sem csúszhat egymásra."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, int(window.property("minimumWidth")))
        felso = _elem(window, "trayTopRow")
        felso_alja = _y_a_savban(window, "trayTopRow") + felso.property("height")
        assert felso_alja <= _y_a_savban(window, "trayUploadSlot") + TURES

    def test_az_elvalasztok_kuszobe_mert_es_befer(self, qml_app_module, qt_app):
        """A két csoportelválasztó két TELJES cellát tesz a sorba; a
        küszöb az a szélesség, ahol ez a többlet is elfér."""
        window, _, _ = qml_app_module
        sav = _elem(window, "trayMainBar")
        kuszob = int(sav.property("separatorThreshold"))
        _szelesseg(window, qt_app, kuszob)
        assert sav.property("separatorsVisible") is True
        sor = _elem(window, "trayActionRow")
        jobb = _x_a_savban(window, "trayActionRow") + sor.property("width")
        assert jobb <= kuszob - 10 + TURES, (
            f"a műveletsor az elválasztókkal kilóg: {jobb} > {kuszob - 10}"
        )

    def test_az_elvalasztok_kuszob_alatt_elmaradnak(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        sav = _elem(window, "trayMainBar")
        _szelesseg(window, qt_app, int(sav.property("separatorThreshold")) - 20)
        assert sav.property("separatorsVisible") is False


class TestAKeptalcaBelseje:
    """A bélyegképsor jobbján 50 képpont marad a három ikongombnak
    (`scratch`: `XConstraint 1, 1, -50`), a gombok 34 képpont szélesek."""

    def test_a_belyegkepsor_jobbjan_50_kepont_marad(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        talca = _elem(window, "trayScratchBack")
        sor = _elem(window, "trayScratchStrip")
        assert talca.property("width") - sor.property("width") == pytest.approx(
            55, abs=TURES
        ), "5 px bal margó + 50 px fenntartott hely a gomboknak"

    @pytest.mark.parametrize(
        "nev", ["trayHoldButton", "trayClearButton", "trayAddToButton"]
    )
    def test_a_harom_gomb_34_kepont_szeles(self, qml_app_module, qt_app, nev):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        assert _elem(window, nev).property("width") == 34

    def test_a_harom_gomb_egymas_alatt_all(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        y = [
            _y_a_savban(window, nev)
            for nev in ("trayHoldButton", "trayClearButton", "trayAddToButton")
        ]
        assert y == sorted(y), f"a három gomb nem egymás alatt áll: {y}"
        assert len(set(y)) == 3


class TestAzInfoSzovegClipje1934:
    """#1934: a szövegnek SAJÁT clipje van — `bal + 20 … jobb − 20`.

    A `respack.yt` az `infotext_clip`-re `x 183…664`-et tárol, a
    `thumbui.tre:690–693` viszont `XConstraint 0, 0, 20` / `1, 1, -20`-at
    ad ugyanarra az elemre. **A kettő nem ugyanaz**, és nem is
    „mindegy": a `respack` téglalap a 800-as vásznon NEM szimmetrikus
    (balra 183, jobbra 136), a közepe 423,5 — a `.tre`-olvasaté 400. A
    különbség 1920 képpontos ablakra **56 képpont**.

    A `docs/specs/kek-info-sav.md` 6. szakasza ezt lemérte mind a 20
    felvételen: a szöveg közepe az ablak közepén áll, `|Δ| ≤ 0,5`
    képpont (19/20; a huszadikon egy másik világos elem is a sávba lóg).
    ⇒ a `respack`-olvasat MEGDŐLT, a `.tre` az igaz.

    A kék HÁTTÉR viszont teljes szélességű marad — az is mérve
    (`y = 942`-n a kék `x 0…1919`, nem-kék képpont: 0). Ezt a két
    állítást együtt kell őrizni, különben egy későbbi kör a szöveg
    behúzását a háttérre is ráhúzza.
    """

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_kek_hatter_teljes_szelessegu_marad(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        sav = _elem(window, "trayBar")
        csik = _elem(window, "trayInfoBar")
        assert abs(csik.property("width") - sav.property("width")) <= TURES

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_szoveg_clipje_20_20_behuzast_kap(
        self, qml_app_module, qt_app, ablak
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        csik = _elem(window, "trayInfoBar")
        szoveg = _elem(window, "trayInfoText")
        assert abs(szoveg.property("x") - 20) <= TURES
        assert abs(
            szoveg.property("width") - (csik.property("width") - 40)
        ) <= TURES

    @pytest.mark.parametrize("ablak", ABLAKOK)
    def test_a_szoveg_kozepe_a_sav_kozepen_all(
        self, qml_app_module, qt_app, ablak
    ):
        """A MÉRT állítás: a szöveg közepe = a sáv közepe.

        Ez az, ami a 20 felvételen látszik — és amit a `respack`-olvasat
        (közép 423,5/800) megsértene.
        """
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        csik = _elem(window, "trayInfoBar")
        szoveg = _elem(window, "trayInfoText")
        kozep = szoveg.property("x") + szoveg.property("width") / 2
        assert abs(kozep - csik.property("width") / 2) <= TURES
