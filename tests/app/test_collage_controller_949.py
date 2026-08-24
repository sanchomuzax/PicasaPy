"""#949: a kollázs-panel KIMENETE, piszkozata és megőrzött beállításai.

Spec: `docs/specs/kollazs-panel-ui-spec.md` **9.** A #943-as
`test_collage_controller_943.py` az API meglétét és a vászonműveleteket
állítja; ez a fájl azt, ami a mentés körül dől el:

- a két mentőgomb **ugyanaz a kódút**, más paraméterrel,
- a kimenet a Kollázsok albumba megy, `.cxf`-fel párban,
- a piszkozat kiírható és **ugyanazt a vásznat** adja vissza,
- a hét megőrzött beállítás körbejár,
- a hiányzó képek és a megszakítás nem hallgatnak.

A vezérlő minimális hoston fut (a #943 mintája): QML nélkül, mert ezek az
állítások adatról szólnak, nem rajzról.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings
from PySide6.QtGui import QColor

from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.collage.themes import (
    CONTACTSHEET,
    NOBORDER,
    PICTUREPILE,
    REGULARGRID,
    WHITEBORDER,
)

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_kollazs_jelzesre


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


def _uj_host(settings, library):
    from picasapy.app.collage_controller import CollageMixin

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            # az offscreen képernyő négyzetes; a formátum-eltérés vizsgálata
            # így nem a futtató gépen múlik
            return 9 / 16

        def _collage_output_width(self):
            # az éles felbontás 5120 (spec 9.1) — egy tesztben az 60 MB-os
            # vásznat és másodperceket jelentene képenként, holott ezek az
            # állítások a fájlnévről, a párról és a jelzésekről szólnak
            return 240

    return _Host()


@pytest.fixture
def settings(tmp_path):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))
    return beallitasok


@pytest.fixture
def host(qt_app, settings, library):
    instance = _uj_host(settings, library)
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def nyitott(host):
    host.openCollage([0, 1, 2])
    return host


def _wait(signal, action, timeout_ms=20000):
    """A műveletet a jelzésre FELIRATKOZVA indítja, majd bevárja azt.

    #988: a saját, csupasz hurok helyett a KÖZÖS, GC-szünetes segédre
    megy — ez a fájl kétszer bukott `exit -11`-gyel a CI-ben (a #1292 és
    a #1294 futásában), miközben a testvér `test_collage_controller_943`
    ugyanezzel az enyhítéssel már zöld volt. Az indoklás és a
    veremkiíratás a segéd docstringjében."""
    return varj_kollazs_jelzesre(signal, action, timeout_ms)


class TestEgyKodut:
    """„A két mentőgomb UGYANAZT a slotot hívja, más paraméterrel."""

    def test_nincs_kulon_asztali_hatterkep_slot(self, host):
        """Aki második kódutat ír, kétszer fogja karbantartani (spec 8.2)."""
        tiltott = ("createDesktopBackground", "makeDesktopBackground",
                   "saveCollage", "createCollageAsDesktop")
        for nev in tiltott:
            assert not hasattr(host, nev), f"második mentő kódút: {nev}"

    def test_mindket_parameter_ugyanoda_ment(self, nyitott, tmp_path):
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott
        elso = Path(args[0])
        nyitott.dropSavedCollagePath()
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(True, True)
        )
        assert megjott
        masodik = Path(args[0])
        assert elso.parent == masodik.parent == tmp_path / "Kollázsok"
        assert elso != masodik

    def test_csak_az_asztali_ag_ad_hatterkep_jelzest(self, nyitott):
        kaptunk: list[str] = []
        nyitott.collageDesktopBackgroundReady.connect(kaptunk.append)
        megjott, _ = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott and kaptunk == []


class TestKimenetiFajl:
    def test_a_fajlnev_a_FORRASMAPPA_cime(self, nyitott):
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott
        assert Path(args[0]).name == "Nyaralás 2026.jpg"

    def test_a_cxf_par_is_elkeszul(self, nyitott):
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott
        assert Path(args[0]).with_suffix(".cxf").exists()

    def test_a_cim_kivulrol_is_allithato(self, nyitott):
        nyitott.setCollageTitle("Karácsony")
        assert nyitott.collageTitle == "Karácsony"
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott and Path(args[0]).name == "Karácsony.jpg"

    def test_a_mentett_utvonal_megjegyzodik(self, nyitott):
        assert nyitott.collageSavedPath == ""
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott
        assert nyitott.collageSavedPath == args[0]

    def test_meglevo_csereje_UGYANAZT_az_utvonalat_irja(self, nyitott):
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott
        elso = Path(args[0])
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False, False, True)
        )
        assert megjott and Path(args[0]) == elso
        assert sorted(p.name for p in elso.parent.glob("*.jpg")) == [elso.name]

    def test_uj_letrehozasa_szamozott_nevet_ad(self, nyitott):
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott
        nyitott.dropSavedCollagePath()
        megjott, args = _wait(
            nyitott.collageDone, lambda: nyitott.createCollage(False)
        )
        assert megjott and Path(args[0]).name == "Nyaralás 20261.jpg"


class TestHianyzoKepek:
    """9.4: „%1 kép nem található, ezért nem jeleníthető meg…"""

    def test_a_hianyzo_kepek_szama_jelzett(self, host, library):
        host._photos.photos.append(_Photo(str(library), "nincs.jpg"))
        host.openCollage([0, 1, 3])
        kaptunk: list[int] = []
        host.collageMissingImages.connect(kaptunk.append)
        megjott, _ = _wait(host.collageDone, lambda: host.createCollage(False))
        assert megjott and kaptunk == [1]

    def test_hiany_nelkul_nincs_jelzes(self, nyitott):
        kaptunk: list[int] = []
        nyitott.collageMissingImages.connect(kaptunk.append)
        megjott, _ = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott and kaptunk == []


class TestMegszakitas:
    def test_a_megszakitott_mentes_nem_hagy_fajlt(self, nyitott, tmp_path):
        from picasapy.app import collage_output as output

        eredeti = output.render_collage

        def _kozben(nodes, settings, target, **kwargs):
            # a felhasználó a rajzolás közben nyomja meg a Megszakítást
            nyitott.cancelCollage()
            return eredeti(nodes, settings, target, **kwargs)

        output.render_collage = _kozben
        try:
            megjott, _ = _wait(
                nyitott.collageCanceled, lambda: nyitott.createCollage(False)
            )
        finally:
            output.render_collage = eredeti
        assert megjott, "nem érkezett collageCanceled"
        assert nyitott.waitForBackgroundWorkers(30.0)
        assert list((tmp_path / "Kollázsok").glob("*.jpg")) == []

    def test_futo_munka_nelkul_a_megszakitas_artalmatlan(self, host):
        host.cancelCollage()
        assert host.backgroundWorkersRunning() is False


class TestFolyamatjelzes:
    """9.1: a négy szakasz-szöveg, és hogy a százalék NEM ugrik vissza."""

    def test_a_szakaszok_sorrendben_jonnek(self, nyitott):
        lepesek: list[tuple[int, str]] = []
        nyitott.collageProgress.connect(lambda p, s: lepesek.append((p, s)))
        megjott, _ = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott
        szazalekok = [p for p, _ in lepesek]
        assert szazalekok[0] == 0 and szazalekok[-1] == 100
        assert szazalekok == sorted(szazalekok), "a százalék visszaugrott"
        assert 90 in szazalekok, "a rajzolás/kiírás határa nem jelződik"
        assert lepesek[0][1] and lepesek[-1][1]

    def test_a_tobbszoros_exponalasnak_sajat_szovege_van(self, nyitott):
        from picasapy.collage.themes import MULTIEXP

        nyitott.setCollageTheme(MULTIEXP)
        lepesek: list[str] = []
        nyitott.collageProgress.connect(lambda p, s: lepesek.append(s))
        megjott, _ = _wait(nyitott.collageDone, lambda: nyitott.createCollage(False))
        assert megjott
        assert lepesek[0] == "Stacking pictures"

    def test_a_megszakitas_leallitast_ir_ki(self, nyitott):
        from picasapy.app import collage_output as output

        eredeti = output.render_collage
        lepesek: list[str] = []
        nyitott.collageProgress.connect(lambda p, s: lepesek.append(s))

        def _kozben(nodes, settings, target, **kwargs):
            nyitott.cancelCollage()
            return eredeti(nodes, settings, target, **kwargs)

        output.render_collage = _kozben
        try:
            megjott, _ = _wait(
                nyitott.collageCanceled, lambda: nyitott.createCollage(False)
            )
        finally:
            output.render_collage = eredeti
        assert megjott
        assert "Creating collage… shutting down" in lepesek


class TestPiszkozat:
    """A bezáráskori „Piszkozat mentése" ága (spec 3.3 / 9.)."""

    def test_a_piszkozat_a_kollazsok_albumba_kerul(self, nyitott, tmp_path):
        kaptunk: list[str] = []
        nyitott.collageDraftSaved.connect(kaptunk.append)
        nyitott.saveCollageDraft()
        piszkozat = tmp_path / "Kollázsok" / AUTOSAVE_NAME
        assert piszkozat.exists()
        assert kaptunk == [str(piszkozat)]

    def test_a_visszatoltott_piszkozat_UGYANAZT_a_vasznat_adja(self, nyitott):
        nyitott.moveNode(0, 300.0, 400.0)
        elotte = [
            (n.path, round(n.center_x, 3), round(n.center_y, 3),
             round(n.width, 3), round(n.height, 3), round(n.theta, 6))
            for n in nyitott.collageNodes.nodes
        ]
        nyitott.saveCollageDraft()
        nyitott.closeCollage()
        assert nyitott.collageClipCount == 0

        nyitott.restoreCollageDraft()
        utana = [
            (n.path, round(n.center_x, 3), round(n.center_y, 3),
             round(n.width, 3), round(n.height, 3), round(n.theta, 6))
            for n in nyitott.collageNodes.nodes
        ]
        assert len(utana) == len(elotte)
        for elo, ut in zip(elotte, utana, strict=True):
            assert elo[0] == ut[0]
            for a, b in zip(elo[1:], ut[1:], strict=True):
                assert a == pytest.approx(b, abs=0.6)

    def test_a_visszatoltas_megnyitja_a_lapot(self, nyitott):
        nyitott.saveCollageDraft()
        nyitott.closeCollage()
        assert nyitott.collageOpen is False
        nyitott.restoreCollageDraft()
        assert nyitott.collageOpen is True
        assert nyitott.collageDirty is False

    def test_piszkozat_nelkul_a_visszatoltas_nem_omlik_ossze(self, host):
        host.restoreCollageDraft()
        assert host.collageClipCount == 0

    def test_kep_nelkul_nem_irunk_piszkozatot(self, host, tmp_path):
        host.saveCollageDraft()
        assert not (tmp_path / "Kollázsok" / AUTOSAVE_NAME).exists()


class TestMegorzottBeallitasok:
    """9.3: a hét kulcs mentődik és visszatölt — a KÖRJÁRAT."""

    def test_korjarat_mind_a_hat_ertekre(self, host, settings, library, qt_app):
        host.setCollageTheme(CONTACTSHEET)
        host.setCollageFormat("A4")
        host.setCollageOrientation("portrait")
        host.setCollageCaptions(False)
        host.setCollageShadows(False)
        host.setCollageBackgroundColor(QColor("#123456"))
        settings.sync()

        masik = _uj_host(settings, library)
        assert masik.collageTheme == CONTACTSHEET
        assert masik.collageFormatKey == "A4"
        assert masik.collageOrientation == "portrait"
        assert masik.collageCaptions is False
        assert masik.collageShadows is False
        assert masik.collageBackgroundColor.name() == "#123456"

    def test_a_hetedik_kulcs_a_piszkozat_utja(self, nyitott, settings, tmp_path):
        from picasapy.app import collage_prefs as prefs

        assert settings.value(prefs.AUTOSAVE_KEY, "") in ("", None)
        nyitott.saveCollageDraft()
        assert settings.value(prefs.AUTOSAVE_KEY) == str(
            tmp_path / "Kollázsok" / AUTOSAVE_NAME
        )

    def test_az_alapertelmezesek(self, host):
        assert host.collageTheme == PICTUREPILE
        assert host.collageCaptions is True
        assert host.collageShadows is True

    def test_az_arnyek_alapertelmezese_a_tema_14_bitje(self, host):
        assert host.collageShadows is True  # Képkupac
        host.setCollageTheme(REGULARGRID)
        assert host.collageShadows is False
        host.setCollageTheme(CONTACTSHEET)
        assert host.collageShadows is True

    def test_az_indexkep_alapkerete_feher_de_utolag_valaszthato(self, host):
        """Az AI6 ``whiteborder``-es; a felhasználó választása ettől még él."""
        assert host.collageBorder == NOBORDER
        host.setCollageTheme(CONTACTSHEET)
        assert host.collageBorder == WHITEBORDER
        host.setCollageBorder(NOBORDER)
        assert host.collageBorder == NOBORDER

    def test_a_projekt_fejlecmezoit_a_render_beallitas_is_megkapja(self, host):
        host._ensure_collage_panel()
        host._collage_panel_title = "AI"
        host._collage_panel_album_date = "2023. november"
        settings = host._render_settings()
        assert settings.album_title == "AI"
        assert settings.album_date == "2023. november"
