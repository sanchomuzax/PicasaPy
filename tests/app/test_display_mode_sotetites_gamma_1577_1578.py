"""A projektor/LCD sötétítés (#1577) és a lineáris gamma (#1578) a
MEGJELENÍTÉSI úton.

A képpont-szabályt a `tests/render/test_display_modes_1577_1578.py` őrzi.
Ez a fájl azt méri, amit a felhasználó lát és NEM lát:

* a **megjelenített** (edit-előnézeti) kép a mért szabály szerint változik,
* a mód elhagyása után a kép **bájtra** az eredeti,
* a **mentett és exportált** fájl a LEMEZEN változatlan (az eredetiben a
  hívás helye az ablak újrarajzolása, `0x009e285d`),
* a **bélyegkép-gyorstár** nem tárolja el a sötétített változatot,
* a hisztogram (#25) és a pipetta (#464) a VALÓDI képet méri.

Bizonyíték: `docs/specs/picasa-megjelenitesi-modok.md` 5.4, 5.5, 5.9.

⚠️ Minden várt érték KIÍRT LITERÁL (`(c·220)>>8`, `(c·246)>>8`, illetve a
spec 5.9 táblájának elemei) — nem a termék konstansairól olvasva.
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

#: A teszt-kép három sávja.
FEHER = (255, 255, 255)
KOZEPSZURKE = (128, 128, 128)
FEKETE = (0, 0, 0)

#: A várt eredmények KIÍRVA, módonként — a fenti három sávra.
#: projektor: (255·220)>>8 = 219, (128·220)>>8 = 110, 0 → 0
VART_PROJEKTOR = {(219, 219, 219), (110, 110, 110), (0, 0, 0)}
#: lcd: (255·246)>>8 = 245, (128·246)>>8 = 123, 0 → 0
VART_LCD = {(245, 245, 245), (123, 123, 123), (0, 0, 0)}
#: lineáris gamma: a spec 5.9 táblája a 255/128/0 indexeken → 255/158/0
VART_LINEAR = {(255, 255, 255), (158, 158, 158), (0, 0, 0)}

VARTAK = {
    "projector": VART_PROJEKTOR,
    "lcd": VART_LCD,
    "linear": VART_LINEAR,
}


class _ModVezerlo(DisplayModeMixin, QObject):
    """A vezérlő-szelet önmagában (a #1575/#1576 tesztjének mintájára)."""

    def __init__(self):
        super().__init__()
        self._init_display_mode()


def _teszt_kep(path) -> None:
    """PNG (veszteségmentes!) három sávval: fehér, középszürke, fekete.

    JPEG itt hibás volna: a veszteséges kódolás magától elmozdítaná a
    255/128 értékeket, és a képpontra pontos várakozás foga elveszne.
    """
    import cv2

    kep = np.zeros((4, 6, 3), dtype=np.uint8)
    kep[0, :] = 255
    kep[1, :] = 128
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
    path = tmp_path / "savok.png"
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


class TestMegjelenitettKep:
    """A három mód a MEGJELENÍTETT képen, képpontra pontosan."""

    def test_alapbol_erintetlen(self, szolgaltato):
        assert _szinek(_keres(szolgaltato)) == {FEHER, KOZEPSZURKE, FEKETE}

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_bekapcsolva_a_mert_szabaly_szerint_hat(self, szolgaltato, mode):
        szolgaltato.set_display_mode(mode)
        assert _szinek(_keres(szolgaltato)) == VARTAK[mode], (
            f"a(z) {mode!r} mód nem a mért szabály szerint hatott"
        )

    def test_a_ket_sotetites_kulonbozik(self, szolgaltato):
        """Kontroll: nem ugyanaz a két mód — a szorzó tényleg más."""
        szolgaltato.set_display_mode("projector")
        projektor = _keres(szolgaltato)
        szolgaltato.set_display_mode("lcd")
        assert not np.array_equal(projektor, _keres(szolgaltato))

    def test_a_gamma_vilagosit_a_sotetitesek_sotetitenek(self, szolgaltato):
        eredeti = _keres(szolgaltato)
        szolgaltato.set_display_mode("linear")
        assert _keres(szolgaltato).mean() > eredeti.mean()
        szolgaltato.set_display_mode("projector")
        assert _keres(szolgaltato).mean() < eredeti.mean()

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_kikapcsolva_bajtra_az_eredeti(self, szolgaltato, mode):
        elotte = _keres(szolgaltato)
        szolgaltato.set_display_mode(mode)
        _keres(szolgaltato)
        szolgaltato.set_display_mode("normal")
        assert np.array_equal(_keres(szolgaltato), elotte), (
            "a mód elhagyása után nem az eredeti kép jött vissza — a hatás "
            "valahol beleégett egy gyorsítótárba"
        )

    #: A `sepia`/`bw` a #1657 óta NEM tartozik ide — képpontot mozdít.
    #: A `mac` a #1730 óta szintén nem: a Mac gamma világosít, és a
    #: képpont-szabályát a `tests/render/test_mac_gamma_1730.py` őrzi.
    @pytest.mark.parametrize("mode", ["auto", "normal", "dither16", "rdesk"])
    def test_a_tobbi_mod_erintetlenul_hagy(self, szolgaltato, mode):
        eredeti = _keres(szolgaltato)
        szolgaltato.set_display_mode(mode)
        assert np.array_equal(_keres(szolgaltato), eredeti)


class TestGyorsitotarNemMergezodik:
    """A tárolt kép és a belőle élő szolgáltatások érintetlenek maradnak."""

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_hisztogram_a_valodi_kepet_tukrozi(self, szolgaltato, mode):
        elotte = szolgaltato.histogram_for("p1")
        szolgaltato.set_display_mode(mode)
        _keres(szolgaltato)
        assert szolgaltato.histogram_for("p1") == elotte

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_pipetta_a_valodi_szint_adja(self, szolgaltato, mode):
        """A pipetta a KÉP színét méri, nem a képernyőre sötétítettet."""
        szolgaltato.set_display_mode(mode)
        _keres(szolgaltato)
        assert szolgaltato.sample_color("p1", 0.5, 0.0) == FEHER

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_az_ujraregisztralas_utan_sem_ragad_be(self, szolgaltato, kep, mode):
        szolgaltato.set_display_mode(mode)
        _keres(szolgaltato)
        szolgaltato.register("p1", kep, ())
        szolgaltato.set_display_mode("normal")
        assert _szinek(_keres(szolgaltato)) == {FEHER, KOZEPSZURKE, FEKETE}

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_lut_kepet_soha_nem_bantja(self, qt_app, kep, mode):
        """A `gpulut=1` ág ADAT, nem kép — sötétítve a shader hibás LUT-ot
        kapna, és a GPU-előnézet elszíneződne."""
        provider = EditPreviewProvider()
        lut = np.full((256, 3), 255, dtype=np.uint8)
        provider.register("p1", kep, (), gpu_prefix_ops=(), gpu_lut=lut)
        provider.set_display_mode(mode)
        kapott = _kep_tombbe(provider.requestImage("p1?gpulut=1", None, None))
        assert _szinek(kapott) == {FEHER}, (
            f"a(z) {mode!r} mód a LUT-textúrát is átírta"
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

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_bekotott_lancon_at_hat(self, lanc, mode):
        vezerlo, _edit, provider = lanc
        vezerlo.setDisplayMode(mode)
        assert _szinek(_keres(provider)) == VARTAK[mode]

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_modvaltas_ujrakerteti_a_kepet_a_qmllel(self, lanc, mode):
        """A `previewSource` `?rev=` része MÁS lesz — enélkül a QML a régi,
        érintetlen képet tartaná meg a saját kép-gyorstárából."""
        vezerlo, edit, _provider = lanc
        elotte = edit.previewSource
        vezerlo.setDisplayMode(mode)
        assert edit.previewSource != elotte

    def test_a_modok_kozott_oda_vissza(self, lanc):
        """Kizáró csoport: az új mód LECSERÉLI az előzőt, nem rakódik rá."""
        vezerlo, _edit, provider = lanc
        vezerlo.setDisplayMode("projector")
        assert _szinek(_keres(provider)) == VART_PROJEKTOR
        vezerlo.setDisplayMode("linear")
        assert _szinek(_keres(provider)) == VART_LINEAR, (
            "a gamma az előzőleg sötétített képre rakódott — a módok "
            "halmozódnak, holott kizáró csoport tagjai"
        )
        vezerlo.setDisplayMode("lcd")
        assert _szinek(_keres(provider)) == VART_LCD


class TestLemezreIrtFajl:
    """A mentett/exportált fájl a LEMEZEN — a mód nem érheti el."""

    @staticmethod
    def _dekodol(path) -> np.ndarray:
        import cv2

        kep = cv2.imread(str(path), cv2.IMREAD_COLOR)
        assert kep is not None, f"a lemezre írt fájl nem dekódolható: {path}"
        return kep[:, :, ::-1]  # BGR → RGB

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_az_export_bajtra_azonos_a_ket_modban(
        self, qt_app, kep, tmp_path, mode
    ):
        from picasapy.export import ExportItem, export_photos

        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)
        edit.beginEdit("p1", str(kep))

        ki_ki = tmp_path / f"ki-ki-{mode}"
        jelentes = export_photos((ExportItem(source=kep),), ki_ki)
        assert jelentes.exported, jelentes.reasons
        bajtok_ki = jelentes.exported[0].read_bytes()

        vezerlo.setDisplayMode(mode)
        ki_be = tmp_path / f"ki-be-{mode}"
        jelentes = export_photos((ExportItem(source=kep),), ki_be)
        assert jelentes.exported, jelentes.reasons
        bajtok_be = jelentes.exported[0].read_bytes()

        assert bajtok_be == bajtok_ki, (
            f"az exportált fájl BÁJTJAI eltérnek a(z) {mode!r} mód szerint — "
            "a megjelenítési hatás kiszivárgott a kimenetre"
        )
        # Az export JPEG-be kódol, tehát a képpontok ±néhány egységgel
        # elmozdulnak; a legkisebb mért hatás (LCD, 255→245) viszont 10-es
        # eltérés, a projektoré 36, a gammáé 30 — a 4-es tűrés mindhármat
        # megfogja, a kódolási zajt viszont átengedi.
        exportalt = self._dekodol(jelentes.exported[0]).astype(np.int16)
        eredeti = self._dekodol(kep).astype(np.int16)
        assert np.abs(exportalt - eredeti).max() <= 4, (
            f"az exportált kép képpontjai elmozdultak a(z) {mode!r} mód "
            "hatásának nagyságrendjével"
        )

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_mentett_fajl_valtozatlan(self, qt_app, kep, mode):
        """A „Mentés" beégető útja (`save_edited`) aktív módban is tiszta."""
        import cv2

        from picasapy.edit.save import save_edited
        from picasapy.edit.session import EditSession

        elotte = kep.read_bytes()

        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)
        edit.beginEdit("p1", str(kep))
        vezerlo.setDisplayMode(mode)

        rendered = cv2.imread(str(kep), cv2.IMREAD_COLOR)
        save_edited(kep, rendered, EditSession())

        assert _szinek(self._dekodol(kep)) == {FEHER, KOZEPSZURKE, FEKETE}, (
            f"a lemezre mentett kép a(z) {mode!r} mód hatását kapta — a mód "
            "nem csak a képernyőre hatott"
        )
        assert kep.read_bytes() == elotte, (
            "a mentett fájl bájtjai megváltoztak az aktív mód mellett"
        )


class TestBelyegkepGyorstar:
    """A bélyegkép-gyorstár nem tárolhatja el a sötétített változatot."""

    @pytest.mark.parametrize("mode", ["projector", "lcd", "linear"])
    def test_a_gyorstar_fajlja_azonos_a_ket_modban(
        self, qt_app, kep, tmp_path, mode
    ):
        from picasapy.thumbs import ThumbnailCache

        provider = EditPreviewProvider()
        edit = EditController(provider)
        vezerlo = _ModVezerlo()
        wire_display_mode(vezerlo, edit, provider)

        stat = kep.stat()
        ki = ThumbnailCache(tmp_path / f"t-ki-{mode}", size=8).get_or_create(
            kep, stat.st_mtime_ns, stat.st_size
        )
        assert ki is not None
        bajtok_ki = ki.read_bytes()

        vezerlo.setDisplayMode(mode)
        be = ThumbnailCache(tmp_path / f"t-be-{mode}", size=8).get_or_create(
            kep, stat.st_mtime_ns, stat.st_size
        )
        assert be is not None
        assert be.read_bytes() == bajtok_ki, (
            f"a bélyegkép-gyorstár a(z) {mode!r} változatot írta lemezre — a "
            "mód kikapcsolása után is sötét maradna (BLOKKOLÓ)"
        )
