"""#7027 - a képfelirat írási szabályai az eredeti Picasa szerint.

Az eredeti (`docs/specs/paritas-ellenorzes-archiv-1.md`, #7024):

- J5: a setter az egyező szöveget eldobja (`0x00437df5-0x00437e69`), tehát
  változatlan szövegnél a fájl és az ini érintetlen marad;
- J4: írásvédett fájlnál a fájlba írást kihagyja (`0x0043859e-0x004385a5`),
  a felirat a `.picasa.ini`-be megy (`0x00438775`);
- J6: a felirat-vágólap segédek a felületről nem hívhatók, ezért nincsenek.

A próbák a lemezt mérik (bájtok, módosítási idő), nem a hívásokat: a „nem
írt" állítás csak úgy hiteles, ha a fájl valóban érintetlen.
"""

from __future__ import annotations

import os
import stat
import time

import pytest
from PySide6.QtCore import QSettings

from picasapy.ini import load_document
from picasapy.metadata import read_file_metadata
from support.jpeg_factory import make_jpeg
from tests.support.qt_wait import wait_for_photo_op

_RÉGI_NS = 1_000_000_000_000_000_000


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    mappa = root / "a"
    mappa.mkdir(parents=True)
    make_jpeg(mappa / "egy.jpg", size=(120, 90))
    make_jpeg(mappa / "ketto.jpg", size=(120, 90))
    return root, mappa


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root, mappa = library
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    ctl = AppController(
        tmp_path / "index.db",
        (str(root),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(mappa))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _sor(controller, nev: str) -> int:
    for i, photo in enumerate(controller.photos.photos):
        if photo.name == nev:
            return i
    raise AssertionError(f"nincs ilyen kép a rácson: {nev}")


def _ini(mappa):
    return mappa / ".picasa.ini"


def _ini_felirat(mappa, nev: str):
    utvonal = _ini(mappa)
    if not utvonal.exists():
        return None
    szakasz = load_document(utvonal).section(nev)
    return None if szakasz is None else szakasz.get("caption")


def _regire_allit(*utvonalak) -> dict:
    """Az érintett fájlok módosítási idejét régire teszi, és visszaadja a
    lenyomatukat. Egy későbbi írás ettől megkülönböztethetően új időt hagy
    (a kernel durva időbélyege két közeli írást azonosnak mutatna)."""
    lenyomat = {}
    for utvonal in utvonalak:
        if utvonal.exists():
            os.utime(utvonal, ns=(_RÉGI_NS, _RÉGI_NS))
            lenyomat[utvonal] = (utvonal.read_bytes(), utvonal.stat().st_mtime_ns)
    return lenyomat


def _varj_csendet(controller, qt_app) -> None:
    """A háttérmunkák lefutnak, és a Qt-események is feldolgozódnak."""
    assert controller.waitForBackgroundWorkers(30.0)
    for _ in range(5):
        qt_app.processEvents()
        time.sleep(0.01)


def _ird_le(controller, qt_app, sor: int, szoveg: str) -> None:
    wait_for_photo_op(
        controller, lambda: controller.setCaption(sor, szoveg), qt_app=qt_app
    )


class TestValtozatlanSzovegNincsIras:
    """J5: ha a levágott új szöveg a kép mai felirata, nincs írás."""

    def test_ugyanaz_a_szoveg_nem_irja_ujra_a_fajlt_es_az_init(
        self, controller, qt_app, library
    ):
        _root, mappa = library
        sor = _sor(controller, "egy.jpg")
        _ird_le(controller, qt_app, sor, "Nyaralás")
        assert controller.photos.captionAt(sor) == "Nyaralás"
        elotte = _regire_allit(mappa / "egy.jpg", _ini(mappa))

        controller.setCaption(sor, "Nyaralás")
        _varj_csendet(controller, qt_app)

        for utvonal, (bajtok, ido) in elotte.items():
            assert utvonal.read_bytes() == bajtok, f"{utvonal.name} tartalma változott"
            assert utvonal.stat().st_mtime_ns == ido, (
                f"{utvonal.name} újra íródott változatlan szövegnél"
            )

    def test_a_szokoz_nem_szamit_valtozasnak(self, controller, qt_app, library):
        _root, mappa = library
        sor = _sor(controller, "egy.jpg")
        _ird_le(controller, qt_app, sor, "Nyaralás")
        elotte = _regire_allit(mappa / "egy.jpg", _ini(mappa))

        controller.setCaption(sor, "  Nyaralás \n")
        _varj_csendet(controller, qt_app)

        for utvonal, (_bajtok, ido) in elotte.items():
            assert utvonal.stat().st_mtime_ns == ido, (
                f"{utvonal.name} újra íródott a körülvevő szóköz miatt"
            )

    def test_felirat_nelkuli_kepen_az_ures_szoveg_sem_ir(
        self, controller, qt_app, library
    ):
        _root, mappa = library
        sor = _sor(controller, "ketto.jpg")
        elotte = _regire_allit(mappa / "ketto.jpg", _ini(mappa))

        controller.setCaption(sor, "")
        controller.setCaption(sor, "   ")
        _varj_csendet(controller, qt_app)

        for utvonal, (bajtok, ido) in elotte.items():
            assert utvonal.read_bytes() == bajtok
            assert utvonal.stat().st_mtime_ns == ido
        assert not _ini(mappa).exists() or _ini_felirat(mappa, "ketto.jpg") is None

    def test_megvaltozott_szoveg_tovabbra_is_ir(self, controller, qt_app, library):
        """Védőpróba: a kapu nem nyelhet el valódi módosítást."""
        _root, mappa = library
        sor = _sor(controller, "egy.jpg")
        _ird_le(controller, qt_app, sor, "Nyaralás")

        _ird_le(controller, qt_app, sor, "Tengerpart")

        assert controller.photos.captionAt(sor) == "Tengerpart"
        assert read_file_metadata(mappa / "egy.jpg").caption == "Tengerpart"

    def test_a_felirat_torlese_tovabbra_is_ir(self, controller, qt_app, library):
        _root, mappa = library
        sor = _sor(controller, "egy.jpg")
        _ird_le(controller, qt_app, sor, "Nyaralás")

        _ird_le(controller, qt_app, sor, "")

        assert controller.photos.captionAt(sor) == ""
        assert not read_file_metadata(mappa / "egy.jpg").caption

    def test_ket_gyors_egymas_utani_azonos_hivas_egyszer_ir(
        self, controller, qt_app, library
    ):
        """A fókuszvesztés és az Enter ugyanazt a szöveget mentheti: a
        második hívás még a modell frissülése előtt érkezik, mégsem ír."""
        _root, mappa = library
        sor = _sor(controller, "egy.jpg")
        irasok = []
        import picasapy.app.photo_ops_write_text_mixin as modul

        eredeti = modul.write_iptc_caption

        def szamol(utvonal, szoveg):
            irasok.append(szoveg)
            return eredeti(utvonal, szoveg)

        modul.write_iptc_caption = szamol
        try:
            wait_for_photo_op(
                controller,
                lambda: (
                    controller.setCaption(sor, "Egyszer"),
                    controller.setCaption(sor, "Egyszer"),
                ),
                qt_app=qt_app,
            )
        finally:
            modul.write_iptc_caption = eredeti

        assert irasok == ["Egyszer"], f"a fájlba {len(irasok)}-szor írt: {irasok}"


class TestIrasvedettJpeg:
    """J4: írásvédett JPEG-nél a felirat a `.picasa.ini`-be megy."""

    @staticmethod
    def _vedd_ra_az_irasvedelmet(utvonal) -> None:
        os.chmod(utvonal, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    def test_a_fajl_bajtra_valtozatlan_es_az_ini_tartja_a_feliratot(
        self, controller, qt_app, library
    ):
        _root, mappa = library
        kep = mappa / "egy.jpg"
        eredeti = kep.read_bytes()
        self._vedd_ra_az_irasvedelmet(kep)
        sor = _sor(controller, "egy.jpg")

        _ird_le(controller, qt_app, sor, "Írásvédett felirat")

        assert kep.read_bytes() == eredeti, "az írásvédett JPEG tartalma változott"
        assert _ini_felirat(mappa, "egy.jpg") == "Írásvédett felirat"
        assert not read_file_metadata(kep).caption

    def test_a_racs_es_a_mezo_forrasa_mutatja_a_feliratot(
        self, controller, qt_app, library
    ):
        _root, mappa = library
        self._vedd_ra_az_irasvedelmet(mappa / "egy.jpg")
        sor = _sor(controller, "egy.jpg")

        _ird_le(controller, qt_app, sor, "Látszik")

        assert controller.photos.captionAt(sor) == "Látszik"

    def test_a_felirat_torlese_az_ini_kulcsot_veszi_le(
        self, controller, qt_app, library
    ):
        _root, mappa = library
        kep = mappa / "egy.jpg"
        eredeti = kep.read_bytes()
        self._vedd_ra_az_irasvedelmet(kep)
        sor = _sor(controller, "egy.jpg")
        _ird_le(controller, qt_app, sor, "Törlendő")
        assert _ini_felirat(mappa, "egy.jpg") == "Törlendő"

        _ird_le(controller, qt_app, sor, "")

        assert _ini_felirat(mappa, "egy.jpg") is None
        assert controller.photos.captionAt(sor) == ""
        assert kep.read_bytes() == eredeti

    def test_az_irhato_jpeg_tovabbra_a_fajl_iptc_jebe_ir(
        self, controller, qt_app, library
    ):
        """Védőpróba: a szabály csak az írásvédett fájlra vonatkozik."""
        _root, mappa = library
        sor = _sor(controller, "ketto.jpg")

        _ird_le(controller, qt_app, sor, "Fájlba megy")

        assert read_file_metadata(mappa / "ketto.jpg").caption == "Fájlba megy"
        assert _ini_felirat(mappa, "ketto.jpg") is None


class TestAHalottFeliratBeillesztesNincs:
    """J6: a felületről nem hívható felirat-vágólap út megszűnt."""

    @pytest.mark.parametrize(
        "nev",
        [
            "pasteCaptionText",
            "copyCaptionText",
            "confirmCaptionPaste",
            "cancelCaptionPaste",
            "captionPasteConfirmationRequested",
            "setCaptionClipboardText",
            "captionClipboardText",
            "_write_caption_text",
        ],
    )
    def test_a_vezerlon_nincs_ilyen_tag(self, controller, nev):
        assert not hasattr(controller, nev), (
            f"{nev} halott út: a felületről nem hívható, az eredetiben a "
            "beillesztés megerősítése a szövegmezőbe épül (#7027)"
        )

    def test_a_menusorban_nincs_beillesztes_megerosito_parbeszed(self):
        from support.menubar_components_6016 import menu_sources

        forras = menu_sources()
        assert "pasteCaptionReplaceDialog" not in forras
        assert "confirmCaptionPaste" not in forras
        assert "not undoable" not in forras
