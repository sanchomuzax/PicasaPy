"""A túlcsordulás-jelölés a MEGJELENÍTÉSI úton — #1576.

A képpont-szabályt a `tests/render/test_display_modes_1576.py` őrzi. Ez a
fájl azt méri, amit a felhasználó lát és NEM lát:

* a **megjelenített** (edit-előnézeti) kép jelölődik, ha a mód aktív,
* a mód kikapcsolása után a kép **bájtra** az eredeti,
* a **mentett és exportált** fájl a LEMEZEN változatlan (a jelölés csak a
  képernyőre hat — az eredetiben a hívás helye az ablak újrarajzolása,
  `0x009e285d`),
* a **bélyegkép-gyorstár** nem tárolja el a jelölt változatot (különben a
  mód kikapcsolása után is festve maradna — ez BLOKKOLÓ volna),
* a szolgáltató belső gyorsítótára (hisztogram, pipetta) sem mérgeződik.

A bizonyíték: `docs/specs/picasa-megjelenitesi-modok.md` 5.6. szakasz.

⚠️ A jelölés SZÁNDÉKOSAN a `requestImage`-ben, a tárolt kép ÉRINTETLENÜL
hagyásával fut. A kézenfekvő alternatíva (a `register()`-ben, tárolás előtt
jelölni) a `_images`/`_prefix_cache` gyorsítótárat mérgezné meg: a mód
kikapcsolása után a festett kép maradna a rekeszben.
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QObject

from picasapy.app.display_mode_controller import (
    DisplayModeMixin,
    wire_display_mode,
)
from picasapy.app.edit_controller import EditController
from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.render.display_modes import OVERFLOW_MARK_RGB

#: A jelölőszín KIÍRVA, a specből (`0xFFFF7F7F` ⇒ B=0x7F, G=0x7F, R=0xFF).
#: SZÁNDÉKOSAN nem a termék-konstansról olvassuk: a konstans elrontása így
#: is bukást okoz, nem csak a képlet elrontása (a „szabad paraméter elnyeli
#: a hibát" csapda).
JELOLO = (255, 127, 127)

FEHER = (255, 255, 255)
#: 254 mindhárom csatornán — a tűrés hiányának kontrollja a valódi képen.
MAJDNEM_FEHER = (254, 254, 254)


class _ModVezerlo(DisplayModeMixin, QObject):
    """A vezérlő-szelet önmagában (a #1575 tesztjének mintájára)."""

    def __init__(self):
        super().__init__()
        self._init_display_mode()


def _teszt_kep(path, meret=(6, 4)) -> None:
    """PNG (veszteségmentes!) három sávval: fehér, majdnem-fehér, fekete.

    JPEG itt hibás volna: a veszteséges kódolás magától elmozdítaná a 255-öt,
    és a küszöb-őr foga elveszne.
    """
    import cv2

    szeles, magas = meret
    kep = np.zeros((magas, szeles, 3), dtype=np.uint8)
    kep[0, :] = 255                      # tökéletesen fehér sor
    kep[1, :] = 254                      # majdnem fehér — NEM jelölendő
    # a maradék sorok feketék
    assert cv2.imwrite(str(path), kep)


def _kep_tombbe(image) -> np.ndarray:
    """`QImage` → RGB uint8 `(H, W, 3)` tömb."""
    from PySide6.QtGui import QImage

    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, stride))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _szinek(tomb: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in tomb.reshape(-1, 3)}


@pytest.fixture
def kep(tmp_path):
    path = tmp_path / "feher.png"
    _teszt_kep(path)
    return path


@pytest.fixture
def szolgaltato(qt_app, kep):
    """Regisztrált előnézet üres szűrőlánccal — a nyers forrás jelenik meg."""
    provider = EditPreviewProvider()
    provider.register("p1", kep, ())
    return provider


def _keres(provider) -> np.ndarray:
    return _kep_tombbe(provider.requestImage("p1", None, None))


class TestJeloloSzinBekotve:
    def test_a_termek_konstansa_a_speces_szin(self):
        assert OVERFLOW_MARK_RGB == JELOLO


class TestMegjelenitettKep:
    """A mód bekapcsolva fest, kikapcsolva nem — a MEGJELENÍTETT képen."""

    def test_alapbol_nincs_jeloles(self, szolgaltato):
        szinek = _szinek(_keres(szolgaltato))
        assert FEHER in szinek
        assert JELOLO not in szinek

    def test_bekapcsolva_a_feher_jelolodik(self, szolgaltato):
        szolgaltato.set_display_mode("overflow")
        szinek = _szinek(_keres(szolgaltato))
        assert JELOLO in szinek, "a kifehéredett folt nem jelölődött"
        assert FEHER not in szinek, "maradt jelöletlen tökéletesen fehér képpont"

    def test_a_majdnem_feher_bekapcsolva_sem_jelolodik(self, szolgaltato):
        szolgaltato.set_display_mode("overflow")
        szinek = _szinek(_keres(szolgaltato))
        assert MAJDNEM_FEHER in szinek, (
            "a 254-es sor is átfestődött — a küszöb ELLAZULT, ez paritás-vesztés"
        )

    def test_kikapcsolva_bajtra_az_eredeti(self, szolgaltato):
        elotte = _keres(szolgaltato)
        szolgaltato.set_display_mode("overflow")
        _keres(szolgaltato)
        szolgaltato.set_display_mode("auto")
        utana = _keres(szolgaltato)
        assert np.array_equal(elotte, utana), (
            "a mód kikapcsolása után nem az eredeti kép jött vissza — a "
            "jelölés valahol beleégett egy gyorsítótárba"
        )

    @pytest.mark.parametrize(
        "mode", ["auto", "normal", "dither16", "rdesk", "mac"]
    )
    def test_barmely_masik_mod_erintetlenul_hagy(self, szolgaltato, mode):
        """A `lcd`/`projector` (#1577) és a `linear` (#1578) azóta KIKERÜLT
        innen: azok ma már mozdítanak képpontot, a szerződésüket a
        `tests/app/test_display_mode_sotetites_gamma_1577_1578.py` őrzi.
        A `sepia` és a `bw` ugyanígy, a #1657 óta."""
        eredeti = _keres(szolgaltato)
        szolgaltato.set_display_mode(mode)
        assert np.array_equal(_keres(szolgaltato), eredeti)


class TestGyorsitotarNemMergezodik:
    """A tárolt kép és a belőle élő szolgáltatások érintetlenek maradnak."""

    def test_a_hisztogram_a_valodi_kepet_tukrozi(self, szolgaltato):
        elotte = szolgaltato.histogram_for("p1")
        szolgaltato.set_display_mode("overflow")
        _keres(szolgaltato)
        assert szolgaltato.histogram_for("p1") == elotte

    def test_a_pipetta_a_valodi_szint_adja(self, szolgaltato):
        """A pipetta a KÉP színét méri, nem a képernyő figyelmeztetését."""
        szolgaltato.set_display_mode("overflow")
        _keres(szolgaltato)
        assert szolgaltato.sample_color("p1", 0.5, 0.0) == FEHER

    def test_az_ujraregisztralas_utan_sem_ragad_be(self, szolgaltato, kep):
        szolgaltato.set_display_mode("overflow")
        _keres(szolgaltato)
        szolgaltato.register("p1", kep, ())
        szolgaltato.set_display_mode("auto")
        assert FEHER in _szinek(_keres(szolgaltato))

    def test_a_lut_kepet_soha_nem_jeloli(self, qt_app, kep):
        """A `gpulut=1` ág ADAT, nem kép — átfestve a shader hibás LUT-ot kapna."""
        provider = EditPreviewProvider()
        lut = np.full((256, 3), 255, dtype=np.uint8)
        provider.register("p1", kep, (), gpu_prefix_ops=(), gpu_lut=lut)
        provider.set_display_mode("overflow")
        kapott = _kep_tombbe(provider.requestImage("p1?gpulut=1", None, None))
        assert _szinek(kapott) == {FEHER}, (
            "a LUT-textúrát is átfestette a jelölés — a GPU-előnézet elromlana"
        )


class TestBekotes:
    """A vezérlő → szolgáltató → QML-újrakérés lánca (`wire_display_mode`)."""

    @pytest.fixture
    def lanc(self, qt_app, kep):
        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)
        edit.beginEdit("p1", str(kep))
        return vezerlo, edit, provider

    def test_a_kezdeti_allapot_atkerul(self, qt_app, kep):
        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        vezerlo.setDisplayMode("overflow")
        wire_display_mode(vezerlo, edit, provider)
        assert provider.display_mode == "overflow", (
            "a bekötés csak a KÖVETKEZŐ váltást vitte át — indításkor a "
            "szolgáltató a vezérlőtől eltérő módban maradt"
        )

    def test_a_modvaltas_atkerul_a_szolgaltatora(self, lanc):
        vezerlo, _edit, provider = lanc
        vezerlo.setDisplayMode("overflow")
        assert provider.display_mode == "overflow"

    def test_a_modvaltas_ujrakerteti_a_kepet_a_qmllel(self, lanc):
        """A `previewSource` `?rev=` része MÁS lesz — enélkül a QML a régi,
        jelöletlen képet tartaná meg a saját kép-gyorstárából."""
        vezerlo, edit, _provider = lanc
        elotte = edit.previewSource
        vezerlo.setDisplayMode("overflow")
        assert edit.previewSource != elotte

    def test_a_bekotott_lancon_at_jelolodik_a_kep(self, lanc):
        vezerlo, _edit, provider = lanc
        vezerlo.setDisplayMode("overflow")
        assert JELOLO in _szinek(_keres(provider))

    def test_szerkesztes_nelkul_sem_hasal_el(self, qt_app):
        """Mód-váltás nyitott szerkesztés nélkül (pl. a rácsból) — no-op."""
        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)
        vezerlo.setDisplayMode("overflow")  # nem dobhat
        assert provider.display_mode == "overflow"


class TestLemezreIrtFajl:
    """A mentett/exportált fájl a LEMEZEN — a jelölés nem érheti el."""

    @staticmethod
    def _dekodol(path) -> np.ndarray:
        import cv2

        kep = cv2.imread(str(path), cv2.IMREAD_COLOR)
        assert kep is not None, f"a lemezre írt fájl nem dekódolható: {path}"
        return kep[:, :, ::-1]  # BGR → RGB

    def test_az_export_bajtra_azonos_a_ket_modban(self, qt_app, kep, tmp_path):
        from picasapy.export import ExportItem, export_photos

        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)
        edit.beginEdit("p1", str(kep))

        ki_ki = tmp_path / "ki-ki"
        jelentes = export_photos((ExportItem(source=kep),), ki_ki)
        assert jelentes.exported, jelentes.reasons
        bajtok_ki = jelentes.exported[0].read_bytes()

        vezerlo.setDisplayMode("overflow")
        ki_be = tmp_path / "ki-be"
        jelentes = export_photos((ExportItem(source=kep),), ki_be)
        assert jelentes.exported, jelentes.reasons
        bajtok_be = jelentes.exported[0].read_bytes()

        assert bajtok_be == bajtok_ki, (
            "az exportált fájl BÁJTJAI eltérnek a megjelenítési mód szerint "
            "— a jelölés kiszivárgott a kimenetre"
        )
        szinek = _szinek(self._dekodol(jelentes.exported[0]))
        assert JELOLO not in szinek
        assert FEHER in szinek

    def test_a_mentett_fajl_valtozatlan(self, qt_app, kep):
        """A „Mentés" beégető útja (`save_edited`) aktív módban is tiszta."""
        from picasapy.edit.save import save_edited
        from picasapy.edit.session import EditSession
        import cv2

        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)
        edit.beginEdit("p1", str(kep))
        vezerlo.setDisplayMode("overflow")

        rendered = cv2.imread(str(kep), cv2.IMREAD_COLOR)
        save_edited(kep, rendered, EditSession())

        szinek = _szinek(self._dekodol(kep))
        assert JELOLO not in szinek, (
            "a lemezre mentett kép jelölést kapott — a mód nem csak a "
            "képernyőre hatott"
        )
        assert FEHER in szinek


class TestBelyegkepGyorstar:
    """A bélyegkép-gyorstár nem tárolhatja el a jelölt változatot."""

    def test_a_gyorstar_fajlja_azonos_a_ket_modban(self, qt_app, kep, tmp_path):
        from picasapy.thumbs import ThumbnailCache

        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)

        stat = kep.stat()
        ki = ThumbnailCache(tmp_path / "t-ki", size=8).get_or_create(
            kep, stat.st_mtime_ns, stat.st_size
        )
        assert ki is not None
        bajtok_ki = ki.read_bytes()

        vezerlo.setDisplayMode("overflow")
        be = ThumbnailCache(tmp_path / "t-be", size=8).get_or_create(
            kep, stat.st_mtime_ns, stat.st_size
        )
        assert be is not None
        assert be.read_bytes() == bajtok_ki, (
            "a bélyegkép-gyorstár a jelölt változatot írta lemezre — a mód "
            "kikapcsolása után is festve maradna (BLOKKOLÓ)"
        )

    def test_a_belyegkep_render_magja_nem_ismeri_a_modot(self):
        """Forrásszintű őr: a gyorstárakat TÖLTŐ kód nem ismeri a módot.

        ⚠️ Ez az őr a #1596-ban SZŰKÜLT. Eredetileg azt követelte meg, hogy
        a `thumbnail_provider` modul EGÉSZE ne hivatkozzon a módra — ez a
        #1576 hatókör-döntését („a mód csak a nagy nézőre hat") tükrözte.
        A #1596 ezt a döntést szándékosan megfordította: mérve, a rácson
        mind a tizenegy tétel hatástalan volt, holott az eredetiben a kampó
        helye az ablak újrarajzolása, vagyis GLOBÁLIS.

        Amit az őr véd, változatlan: **a gyorstár nem tárolhatja el a
        festett képet**. Ezért a mérce most pontosan az a két hely, amelyik
        gyorstárat tölt — a lemezes `thumbs.cache`, és a provider
        `_render()` magja (ez írja a `_FilteredThumbMemo` rekeszt is). A
        festés a `requestImage()`-ben, ezek UTÁN fut.

        A viselkedést (nem a forrást) a
        `tests/app/test_display_mode_racs_1596.py::TestGyorstarTisztasag`
        méri: a #1596 mutációs próbája szerint a festés `_render()`-be
        mozgatását ott a szűrt-bélyegkép őre elkapja.
        """
        import inspect

        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import cache

        assert "display_mode" not in inspect.getsource(cache), (
            "a lemezes bélyegkép-gyorstár hivatkozik a megjelenítési módra "
            "— a jelölt képet írná a lemezre (BLOKKOLÓ)"
        )
        assert "display_mode" not in inspect.getsource(
            ThumbnailProvider._render
        ), (
            "a bélyegkép RENDER-MAGJA hivatkozik a megjelenítési módra — ez "
            "a mag tölti a lemezes és a memóriabeli gyorstárat is, tehát a "
            "festés beleégne (BLOKKOLÓ)"
        )
