"""A kollázs KIMENETÉNEK felülete, KIRAJZOLVA — #949.

Spec: `docs/specs/kollazs-panel-ui-spec.md` **9.** (létrehozás, mentés
meglévő fölé, hiányzó képek) és **3.3** (bezárás), valamint **12.**

Három dolog miatt kell ide kirajzolt teszt:

1. **A folyamatjelző a vászon KÖZEPÉN áll**, 224 × 80-as dobozban — ezt
   csak a valódi elrendezésből lehet megmérni.
2. **A párbeszédek `Popup`-ok**: a tartalmuk nem a szülő vizuális fájában
   ül, ezért a `_walk()` nem látja őket — `findChild`-dal keressük, és
   VALÓDI kattintást kapnak.
3. **Egy bezárási út van.** A gomb, az `Esc` és a mentés utáni önzáródás
   mind a `requestClose()`-ba fut be. Ezt csak úgy lehet állítani, ha
   mindhárom kaput ugyanaz a teszt hajtja meg.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtTest import QTest

from support.collage_canvas_harness import (
    _ablakban,
    _child,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: A folyamatjelző doboz mérete (spec 9.1).
OVERLAY_MERET = (224, 80)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


@pytest.fixture
def panel(controller):
    return _panel(controller)


def _kattints(panel, item):
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        panel.property("_view"),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    QTest.qWait(50)


def _parbeszed(panel, nev):
    dialog = panel.findChild(QObject, nev)
    assert dialog is not None, f"{nev} nincs a fában"
    return dialog


def _gomb(panel, dialog_nev, gomb_nev):
    gomb = _parbeszed(panel, dialog_nev).findChild(QObject, gomb_nev)
    assert gomb is not None, f"{gomb_nev} nincs a(z) {dialog_nev} párbeszédben"
    return gomb


def _var(feltetel, ms=2000):
    """Esemény-pörgetés HATÁRIDŐVEL — fejnélküli környezetben az elrendezés
    és a `Popup` megnyílása nem azonnali."""
    eltelt = 0
    while eltelt < ms:
        if feltetel():
            return True
        QTest.qWait(25)
        eltelt += 25
    return feltetel()


def _esc(panel):
    QTest.keyClick(panel.property("_view"), Qt.Key.Key_Escape)
    QTest.qWait(50)


class TestFolyamatjelzo:
    """9.1: 224 × 80, a vászon közepén, alapból REJTETT."""

    def test_alapbol_rejtett(self, panel):
        assert _child(panel, "collageProgressOverlay").isVisible() is False

    def test_a_meret_es_a_hely(self, panel):
        overlay = _child(panel, "collageProgressOverlay")
        canvas = _child(panel, "collageCanvas")
        x, y, w, h = _ablakban(overlay)
        cx, cy, cw, ch = _ablakban(canvas)
        assert (round(w), round(h)) == OVERLAY_MERET
        assert round(x + w / 2) == round(cx + cw / 2)
        assert round(y + h / 2) == round(cy + ch / 2)

    def test_harom_resze_van(self, panel):
        for nev in (
            "collageProgressTitle",
            "collageProgressSpinner",
            "collageProgressStatus",
        ):
            assert _child(panel, nev) is not None

    def test_a_cim_fent_a_pörgo_kozepen_az_allapot_lent(self, panel):
        _, cim_y, _, cim_h = _ablakban(_child(panel, "collageProgressTitle"))
        _, porgo_y, _, porgo_h = _ablakban(_child(panel, "collageProgressSpinner"))
        _, allapot_y, _, _ = _ablakban(_child(panel, "collageProgressStatus"))
        assert cim_y + cim_h <= porgo_y
        assert porgo_y + porgo_h <= allapot_y

    def test_a_jelzesre_megjelenik(self, panel, controller):
        controller.collageProgress.emit(0, "Creating collage… initializing")
        assert _var(lambda: _child(panel, "collageProgressOverlay").isVisible())
        assert (
            _child(panel, "collageProgressTitle").property("text")
            == "Creating collage… initializing"
        )

    def test_az_allapotsor_a_szazalekot_mutatja(self, panel, controller):
        controller.collageProgress.emit(42, "Creating collage")
        assert _var(lambda: _child(panel, "collageProgressOverlay").isVisible())
        assert "42" in _child(panel, "collageProgressStatus").property("text")

    def test_megszakitaskor_eltunik(self, panel, controller):
        controller.collageProgress.emit(10, "Creating collage")
        assert _var(lambda: _child(panel, "collageProgressOverlay").isVisible())
        controller.collageCanceled.emit()
        assert _var(
            lambda: not _child(panel, "collageProgressOverlay").isVisible()
        )

    def test_hibanal_eltunik(self, panel, controller):
        controller.collageProgress.emit(10, "Creating collage")
        assert _var(lambda: _child(panel, "collageProgressOverlay").isVisible())
        controller.collageFailed.emit("teszt")
        assert _var(
            lambda: not _child(panel, "collageProgressOverlay").isVisible()
        )


class TestMentesMellozve:
    """9.1: kép nélkül „Mentés mellőzve" + a hivatalos magyar szöveg."""

    def test_a_jelzesre_megnyilik(self, panel, controller):
        controller.collageNoImages.emit()
        assert _var(
            lambda: _parbeszed(panel, "collageSaveSkippedDialog").property("visible")
        )

    def test_a_szoveg_a_hivatalos(self, panel, controller):
        controller.collageNoImages.emit()
        _var(
            lambda: _parbeszed(panel, "collageSaveSkippedDialog").property("visible")
        )
        uzenet = _parbeszed(panel, "collageSaveSkippedDialog").findChild(
            QObject, "collageSaveSkippedMessage"
        )
        assert "removed" in uzenet.property("text")


class TestFormatumEltéres:
    """9.1: „Figyelmeztetés: eltérő formátumok" — két gomb."""

    def test_a_jelzesre_megnyilik(self, panel, controller):
        controller.collageFormatMismatch.emit()
        assert _var(
            lambda: _parbeszed(panel, "collageFormatMismatchDialog").property(
                "visible"
            )
        )

    def test_a_beallitas_ennek_ellenere_atlepi_a_figyelmeztetest(
        self, panel, controller
    ):
        controller.collageFormatMismatch.emit()
        _var(
            lambda: _parbeszed(panel, "collageFormatMismatchDialog").property(
                "visible"
            )
        )
        _kattints(panel, _gomb(panel, "collageFormatMismatchDialog",
                              "collageFormatSetAnywayButton"))
        assert _var(lambda: controller.backgroundWorkersRunning()
                    or controller.collageSavedPath != "")
        assert controller.waitForBackgroundWorkers(30.0)

    def test_a_beallitas_mellozese_nem_ment(self, panel, controller):
        controller.collageFormatMismatch.emit()
        _var(
            lambda: _parbeszed(panel, "collageFormatMismatchDialog").property(
                "visible"
            )
        )
        _kattints(panel, _gomb(panel, "collageFormatMismatchDialog",
                               "collageFormatDontSetButton"))
        QTest.qWait(100)
        assert controller.collageSavedPath == ""


class TestMeglevoFole:
    """9.2: „Lecseréli a meglévőt, vagy újat hoz létre?"

    ⚠️ Ez a kérdés NEM úgy áll elő, hogy kétszer mentünk egymás után: a
    sikeres mentés után a lap MAGÁTÓL bezárul (9.1/b). Akkor jön elő, ha a
    lapot egy KORÁBBI kollázsból nyitották meg (3.2) — a vezérlő ilyenkor a
    `setCollageSavedPath`-tal kapja meg, melyik fájlból dolgozunk. A teszt
    ezt az állapotot állítja be, nem egy mesterséges dupla mentést."""

    def _mar_mentett(self, controller, tmp_path):
        """A lap egy meglévő kollázsból nyílt: a fájl a lemezen van."""
        mappa = tmp_path / "kimenet"
        mappa.mkdir(parents=True, exist_ok=True)
        korabbi = mappa / "kepek.jpg"
        korabbi.write_bytes(b"korabbi")
        controller.setCollageSavedPath(str(korabbi))
        return korabbi

    def test_elso_mentesnel_NEM_kerdez(self, panel, controller):
        _kattints(panel, _child(panel, "collageShareButton"))
        assert not _parbeszed(panel, "collageReplaceDialog").property("visible")
        assert controller.waitForBackgroundWorkers(30.0)

    def test_mar_mentett_kollazsnal_kerdez(self, panel, controller, tmp_path):
        self._mar_mentett(controller, tmp_path)
        _kattints(panel, _child(panel, "collageShareButton"))
        assert _var(
            lambda: _parbeszed(panel, "collageReplaceDialog").property("visible")
        )
        assert controller.backgroundWorkersRunning() is False

    def test_a_meglevo_csereje_UGYANOTT_ment(self, panel, controller, tmp_path):
        korabbi = self._mar_mentett(controller, tmp_path)
        _kattints(panel, _child(panel, "collageShareButton"))
        _var(lambda: _parbeszed(panel, "collageReplaceDialog").property("visible"))
        _kattints(panel, _gomb(panel, "collageReplaceDialog",
                               "collageReplaceExistingButton"))
        assert _var(lambda: controller.collageSavedPath == str(korabbi), 20000)
        assert controller.waitForBackgroundWorkers(30.0)
        # az eredeti útvonal felülírva, NINCS számozott második fájl
        assert sorted(p.name for p in korabbi.parent.glob("*.jpg")) == [korabbi.name]
        assert korabbi.read_bytes() != b"korabbi"

    def test_az_uj_letrehozasa_UJ_fajlt_ad(self, panel, controller, tmp_path):
        korabbi = self._mar_mentett(controller, tmp_path)
        _kattints(panel, _child(panel, "collageShareButton"))
        _var(lambda: _parbeszed(panel, "collageReplaceDialog").property("visible"))
        _kattints(panel, _gomb(panel, "collageReplaceDialog",
                               "collageCreateNewButton"))
        assert _var(
            lambda: controller.collageSavedPath not in ("", str(korabbi)), 20000
        )
        assert controller.waitForBackgroundWorkers(30.0)
        assert korabbi.read_bytes() == b"korabbi", "a meglévő fájl SÉRÜLT"
        assert len(list(korabbi.parent.glob("*.jpg"))) == 2


class TestEgyBezarasiUt:
    """3.3: a gomb, az Esc és a mentés utáni önzáródás EGY kapun megy."""

    def test_piszkozat_nelkul_a_gomb_azonnal_zar(self, panel, controller):
        assert controller.collageDirty is False
        _kattints(panel, _child(panel, "collageCloseButton"))
        assert _var(lambda: controller.collageOpen is False)
        assert not _parbeszed(panel, "collageCloseConfirmDialog").property("visible")

    @pytest.mark.parametrize("kapu", ["gomb", "esc"])
    def test_mentetlen_modositasnal_KERDEZ(self, panel, controller, kapu):
        controller.moveNode(0, 300.0, 300.0)
        assert controller.collageDirty is True
        if kapu == "gomb":
            _kattints(panel, _child(panel, "collageCloseButton"))
        else:
            _esc(panel)
        assert _var(
            lambda: _parbeszed(panel, "collageCloseConfirmDialog").property("visible")
        )
        assert controller.collageOpen is True

    def test_a_piszkozat_mentese_kiirja_es_bezar(self, panel, controller, tmp_path):
        controller.moveNode(0, 300.0, 300.0)
        _kattints(panel, _child(panel, "collageCloseButton"))
        _var(
            lambda: _parbeszed(panel, "collageCloseConfirmDialog").property("visible")
        )
        _kattints(panel, _gomb(panel, "collageCloseConfirmDialog",
                               "collageSaveDraftButton"))
        assert _var(lambda: controller.collageOpen is False)
        assert (tmp_path / "kimenet" / "autosave.cxf").exists()

    def test_a_modositasok_elvetese_NEM_ir_piszkozatot(
        self, panel, controller, tmp_path
    ):
        controller.moveNode(0, 300.0, 300.0)
        _kattints(panel, _child(panel, "collageCloseButton"))
        _var(
            lambda: _parbeszed(panel, "collageCloseConfirmDialog").property("visible")
        )
        _kattints(panel, _gomb(panel, "collageCloseConfirmDialog",
                               "collageDiscardChangesButton"))
        assert _var(lambda: controller.collageOpen is False)
        assert not (tmp_path / "kimenet" / "autosave.cxf").exists()

    def test_a_megse_NYITVA_hagyja_a_lapot(self, panel, controller):
        controller.moveNode(0, 300.0, 300.0)
        _kattints(panel, _child(panel, "collageCloseButton"))
        _var(
            lambda: _parbeszed(panel, "collageCloseConfirmDialog").property("visible")
        )
        _kattints(panel, _gomb(panel, "collageCloseConfirmDialog",
                               "collageCloseCancelButton"))
        QTest.qWait(150)
        assert controller.collageOpen is True
        assert controller.collageDirty is True

    def test_a_mentes_utan_a_lap_MAGATOL_bezarul(self, panel, controller):
        """9.1/b: a sikeres mentés után a program maga nyomja meg a
        Bezárás gombot, a mentetlen-módosítás kérdését ELNYOMVA."""
        controller.moveNode(0, 300.0, 300.0)
        kaptunk: list[str] = []
        panel.collageSaved.connect(kaptunk.append)
        _kattints(panel, _child(panel, "collageShareButton"))
        assert _var(lambda: controller.collageOpen is False, 20000)
        assert controller.waitForBackgroundWorkers(30.0)
        assert len(kaptunk) == 1 and kaptunk[0].endswith(".jpg")
        assert not _parbeszed(panel, "collageCloseConfirmDialog").property("visible")


class TestMegszakitas:
    """9.1: „Megszakítja a kollázs létrehozását?"""

    def test_a_folyamatjelzore_kattintva_kerdez(self, panel, controller):
        controller.collageProgress.emit(30, "Creating collage")
        _var(lambda: _child(panel, "collageProgressOverlay").isVisible())
        _kattints(panel, _child(panel, "collageProgressOverlay"))
        assert _var(
            lambda: _parbeszed(panel, "collageCancelConfirmDialog").property("visible")
        )

    def test_a_megszakitas_mellozese_nem_szakit_meg(self, panel, controller):
        controller.collageProgress.emit(30, "Creating collage")
        _var(lambda: _child(panel, "collageProgressOverlay").isVisible())
        _kattints(panel, _child(panel, "collageProgressOverlay"))
        _var(
            lambda: _parbeszed(panel, "collageCancelConfirmDialog").property("visible")
        )
        _kattints(panel, _gomb(panel, "collageCancelConfirmDialog",
                               "collageDontCancelButton"))
        QTest.qWait(100)
        assert _child(panel, "collageProgressOverlay").isVisible() is True


class TestHianyzoKepek:
    """9.4: „%1 kép nem található, ezért nem jeleníthető meg…"""

    def test_a_jelzesre_megnyilik_a_darabszammal(self, panel, controller):
        controller.collageMissingImages.emit(3)
        assert _var(
            lambda: _parbeszed(panel, "collageMissingImagesDialog").property("visible")
        )
        uzenet = _parbeszed(panel, "collageMissingImagesDialog").findChild(
            QObject, "collageMissingImagesMessage"
        )
        assert "3" in uzenet.property("text")


class TestKijelolesKotelezo:
    """10/b.1: „Kötelező a kijelölés" — a Képkockaközéppont gombhoz."""

    def test_a_jelzesre_megnyilik(self, panel, controller):
        controller.collageNeedsSelection.emit()
        assert _var(
            lambda: _parbeszed(panel, "collageSelectionRequiredDialog").property(
                "visible"
            )
        )


_TS_FORRAS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


class TestHivatalosMagyar:
    """A párbeszédek szövege a `picasa-kollazs-felulet.md` 9.1–9.3-ból.

    Ezt egyetlen futásidejű teszt sem fogja meg: a rossz magyar szöveggel is
    zöld minden. A `.ts` bejegyzést tehát KÜLÖN állítjuk — az a hely, ahol a
    felhasználó által OLVASOTT mondat áll."""

    @pytest.mark.parametrize(
        "angol,magyar",
        [
            ("Save Skipped", "Mentés mellőzve"),
            (
                "The collage cannot be saved because all of the pictures have "
                "been removed. Add at least one picture and try again.",
                "A kollázs nem menthető, mert az összes képet eltávolították. "
                "Vegyen fel legalább egy képet, és próbálkozzon újra.",
            ),
            ("Format Mismatch Warning", "Figyelmeztetés: eltérő formátumok"),
            ("Set Anyway", "Beállítás ennek ellenére"),
            ("Don't Set", "Beállítás mellőzése"),
            (
                "Would you like to replace the existing one, or create a new one?",
                "Lecseréli a meglévőt, vagy újat hoz létre?",
            ),
            ("Replace Existing", "Meglévő cseréje"),
            ("Create New", "Új létrehozása"),
            ("Save Draft", "Piszkozat mentése"),
            ("Discard Changes", "Módosítások elvetése"),
            (
                "Cancel creating the collage?",
                "Megszakítja a kollázs létrehozását?",
            ),
            ("Cancel Collage", "Kollázs megszakítása"),
            ("Don't Cancel", "Megszakítás mellőzése"),
            (
                "%1 pictures could not be found, so they cannot be displayed…",
                "%1 kép nem található, ezért nem jeleníthető meg…",
            ),
            ("Selection Required", "Kötelező a kijelölés"),
            (
                "Please select the single image you want to place in the center "
                "of the collage BEFORE pressing this button.",
                "MIELŐTT erre a gombra kattintana, jelölje ki azt az egy képet, "
                "amelyet a kollázs közepére szeretne helyezni.",
            ),
            ("Creating collage - %1%", "Kollázs létrehozása - %1%"),
            ("%1 / %2 processed", "%1 / %2 feldolgozva"),
            ("Stacking pictures", "Képek egymásra helyezése"),
        ],
    )
    def test_a_forras_es_a_forditas_parban_all(self, angol, magyar):
        assert f"<source>{angol}</source>" in _TS_FORRAS, angol
        assert f"<translation>{magyar}</translation>" in _TS_FORRAS, magyar
