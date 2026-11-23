"""#7385, második kör: a pipetta mintavétele nem fagyaszthatja meg a felületet.

A réteg ELŐTTI lánc képe az előnézet léptékében készül (ugyanazon az úton, mint
a megjelenített előnézet), és fotónként EGY bejegyzésként tárolódik, a lánc, a
fájl, a festés és a színkezelés aláírásával. Így:

- az ismételt mintavétel nem renderel újra (a nehéz láncon ez a 10 másodperces
  fagyás volt),
- a háttérben már elkészült előnézet (nem megnyitott látogatásnál ez maga a
  teljes lánc) ingyen ad mintát, az első kattintás is azonnali,
- minden változás (lánc, fájl, színkezelés, festés) érvényteleníti a bejegyzést.

A mintavétel TERÜLETÁTLAG (a #7345 E23 és B14 mérése): a bézs folt határán
(x=782 a nézőben, a kép 400. oszlopa) a p4 a bézs és a kék 8 bites átlaga, a
bézs súlya 2/5; 10 képpontra a határtól már a tiszta folt. A középre igazított
páratlan négyzetek közül az 5x5 adja a 2/5-öt: ez KIMONDOTT FELTEVÉS, a pontos
méretet a 7345-B14 mérés dönti el.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest
from PIL import Image

from picasapy.ini.filters import parse_filters

_FOLT_PX = 200
_N = 4
#: a `color_patches.jpg` (800x800) foltjai: az 1:1 nézőben a kép bal széle
#: x=382, a felső széle y=88 (job-899..902), tehát a bézs folt jobb szélét
#: követő első kék oszlop (x=782, y=588) a kép (400, 500) pontja.
_FOLTOK = (
    ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)),
    ((0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)),
    ((128, 128, 128), (0xC8, 0x97, 0x79), (0x3C, 0x5A, 0x96), (0x5B, 0x8C, 0x3B)),
    ((0xE5, 0xC8, 0x3C), (0x77, 0x3C, 0x8C), (0xF0, 0xF0, 0xF0), (0x1E, 0x1E, 0x1E)),
)
_BEZS = (0xC8, 0x97, 0x79)
_KEK = (0x3C, 0x5A, 0x96)
_Y_SOR = 500


def _foltos_kep(ut: Path, folt_px: int = _FOLT_PX) -> Path:
    kep = Image.new("RGB", (_N * folt_px, _N * folt_px))
    for sor in range(_N):
        for oszlop in range(_N):
            kep.paste(
                _FOLTOK[sor][oszlop],
                (oszlop * folt_px, sor * folt_px, (oszlop + 1) * folt_px, (sor + 1) * folt_px),
            )
    kep.save(ut, "PNG")
    return ut


def _normalt(kepoldal: int, pixel: int) -> float:
    """A `pixel` oszlop normált koordinátája (a mintavétel `round(n*(W-1))`-nel
    képez vissza, tehát pontosan ezt a képpontot adja)."""
    return pixel / (kepoldal - 1)


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def kep(tmp_path) -> Path:
    return _foltos_kep(tmp_path / "foltok.png")


class _Hivasok(list):
    """A lánc-futtatások listája; a `fo_szalon` a GUI-szálon futókat számolja."""

    def __init__(self) -> None:
        super().__init__()
        self._fo_szalon = 0

    @property
    def fo_szalon(self) -> int:
        return self._fo_szalon


@pytest.fixture
def lanc_szamlalo(provider, monkeypatch):
    """A `_futtasd_a_lancot` hívásainak számlálója (minden szálról; a
    `fo_szalon` csak a GUI-szálét: a háttér-render a pipetta kattintásától
    független)."""
    eredeti = provider._futtasd_a_lancot
    hivasok = _Hivasok()
    zar = threading.Lock()

    def figyelo(*args, **kwargs):
        with zar:
            hivasok.append(args[2] if len(args) > 2 else kwargs.get("ops"))
            if threading.current_thread() is threading.main_thread():
                hivasok._fo_szalon += 1
        return eredeti(*args, **kwargs)

    monkeypatch.setattr(provider, "_futtasd_a_lancot", figyelo)
    return hivasok


@pytest.fixture
def forras_szamlalo(provider, monkeypatch):
    """A `_resolve_source` hívásainak számlálója (a dekód költsége)."""
    eredeti = provider._resolve_source
    hivasok: list[bool] = []

    def figyelo(*args, **kwargs):
        hivasok.append(True)
        return eredeti(*args, **kwargs)

    monkeypatch.setattr(provider, "_resolve_source", figyelo)
    return hivasok


#: a (sor 1, oszlop 1) folt közepe: az 5x5 ablak végig a foltban marad
_KOZEP = (300 / 799, 300 / 799)
_BW = parse_filters("bw=1;")
_SEPIA = parse_filters("sepia=1;")


class TestEgyszeriRenderEsGyorsitotar:
    def test_az_ismetelt_mintavetel_nem_renderel_ujra(self, provider, kep, lanc_szamlalo):
        """A nehéz láncon az ismételt kattintás fagyott: most egyetlen render
        van, a további minták a tárolt képből jönnek."""
        elso = provider.sample_prefix_color("1", kep, _BW, 0.2, 0.2)
        assert len(lanc_szamlalo) == 1

        masodik = provider.sample_prefix_color("1", kep, _BW, 0.6, 0.4)
        harmadik = provider.sample_prefix_color("1", kep, _BW, 0.2, 0.2)

        assert len(lanc_szamlalo) == 1, "az ismételt mintavétel újrarenderelt"
        assert elso == harmadik
        assert masodik != elso

    def test_az_ismetelt_mintavetel_50_ms_alatt_van(self, provider, kep):
        import time

        provider.sample_prefix_color("1", kep, _BW, 0.2, 0.2)
        ideje = []
        for _ in range(7):
            kezdet = time.perf_counter()
            provider.sample_prefix_color("1", kep, _BW, 0.6, 0.4)
            ideje.append(time.perf_counter() - kezdet)

        assert min(ideje) < 0.05, f"a tárolt képből sem azonnali: {min(ideje) * 1000:.1f} ms"

    def test_a_hatterben_elkeszult_kep_ujrahasznosul(
        self, provider, kep, lanc_szamlalo, forras_szamlalo
    ):
        """Nem megnyitott látogatásnál a pipetta lánca maga a megjelenített
        lánc: a háttér-render (`shared_cache=False`) eredménye mintát ad, az
        első kattintás sem renderel és nem dekódol."""
        provider.register("1", kep, _BW, shared_cache=False, sample_prefix_ops=_BW)
        renderek = len(lanc_szamlalo)
        dekodok = len(forras_szamlalo)

        szin = provider.sample_prefix_color("1", kep, _BW, *_KOZEP)

        assert szin is not None
        assert len(lanc_szamlalo) == renderek, "a kattintás újrarenderelt"
        assert len(forras_szamlalo) == dekodok, "a kattintás újradekódolt"
        assert szin == provider.sample_color("1", *_KOZEP)

    def test_eltero_lanc_eseten_nem_jegyez_meg(self, provider, kep, lanc_szamlalo):
        """Nyitott látogatásnál a megjelenített lánc a réteggel bővebb, mint a
        pipetta lánca: a megjelenített kép NEM a minta, tehát nem tárolódik."""
        teljes = _BW + parse_filters("sepia=1;")
        provider.register("1", kep, teljes, shared_cache=False, sample_prefix_ops=_BW)
        renderek = len(lanc_szamlalo)

        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1

    def test_a_valtozo_lanc_ervenyteleniti_a_bejegyzest(self, provider, kep, lanc_szamlalo):
        provider.register("1", kep, _BW, shared_cache=False, sample_prefix_ops=_BW)
        szurke = provider.sample_prefix_color("1", kep, _BW, 0.6, 0.1)
        renderek = len(lanc_szamlalo)

        szepia = provider.sample_prefix_color("1", kep, _SEPIA, 0.6, 0.1)

        assert len(lanc_szamlalo) == renderek + 1
        assert szepia != szurke, "a másik lánc másik színt ad"

    def test_a_lecserelt_fajl_ervenyteleniti_a_bejegyzest(self, provider, kep, lanc_szamlalo):
        elso = provider.sample_prefix_color("1", kep, (), 0.1, 0.1)
        assert elso == (255, 0, 0)

        Image.new("RGB", (_N * _FOLT_PX, _N * _FOLT_PX), (0, 0, 255)).save(kep, "PNG")
        regi = kep.stat().st_mtime
        os.utime(kep, (regi + 10, regi + 10))

        assert provider.sample_prefix_color("1", kep, (), 0.1, 0.1) == (0, 0, 255)

    def test_az_alkalmazas_sajat_mtime_leptetese_nem_ervenyteleniti(
        self, provider, kep, lanc_szamlalo
    ):
        """A `photo_touch` (#2491) minden `.picasa.ini`-mentéskor előreléptet a
        kép mtime-ján: ha ez érvénytelenítené a bejegyzést, a látogatás minden
        további kattintása újra renderelne."""
        provider.sample_prefix_color("1", kep, _BW, 0.2, 0.2)
        renderek = len(lanc_szamlalo)

        regi = kep.stat().st_mtime
        os.utime(kep, (regi + 2, regi + 2))
        provider.sample_prefix_color("1", kep, _BW, 0.6, 0.4)

        assert len(lanc_szamlalo) == renderek

    def test_a_szinkezeles_valtasa_ervenyteleniti_a_bejegyzest(self, provider, kep, lanc_szamlalo):
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)
        renderek = len(lanc_szamlalo)

        provider.set_color_management(True)
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1

    def test_a_render_kozben_valtott_szinkezeles_elavultnak_jeloli_a_kepet(
        self, provider, kep, lanc_szamlalo, monkeypatch
    ):
        """A háttér-render közben váltott színkezelés a `set_color_management`
        törlése UTÁN még eltárolhatná a régi dekódú képet: az aláírást a render
        ELEJÉN kell venni, hogy a tárolt kép elavultnak látsszon."""
        eredeti = provider._render_at_preview_scale

        def valto(*args, **kwargs):
            eredmeny = eredeti(*args, **kwargs)
            provider.set_color_management(True)
            return eredmeny

        monkeypatch.setattr(provider, "_render_at_preview_scale", valto)
        provider.register("1", kep, _BW, shared_cache=False, sample_prefix_ops=_BW)
        monkeypatch.setattr(provider, "_render_at_preview_scale", eredeti)
        renderek = len(lanc_szamlalo)

        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1, "az elavult dekódú kép mintát adott"

    def test_a_festes_ervenyteleniti_a_bejegyzest(self, provider, kep, lanc_szamlalo):
        """A festés a renderbe számít: más festéssel más a kép."""
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)
        renderek = len(lanc_szamlalo)

        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5, paint_strokes=())
        assert len(lanc_szamlalo) == renderek, "azonos (üres) festésnél a bejegyzés érvényes"

        from picasapy.app.paint_mask import Vonas

        vonas = (Vonas(x=0.5, y=0.5, sugar=0.1),)
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5, paint_strokes=vonas)
        assert len(lanc_szamlalo) == renderek + 1, "más festésnél újra kell renderelni"

        provider.sample_prefix_color("1", kep, _BW, 0.2, 0.2, paint_strokes=vonas)
        assert len(lanc_szamlalo) == renderek + 1, "ugyanazzal a festéssel a bejegyzés érvényes"

    def test_gyors_elonezet_kozben_nem_jegyez_meg(self, provider, kep, lanc_szamlalo):
        """A húzás közbeni gyors (közelítő) kép nem lehet pontos minta."""
        from picasapy.render.elonezeti_arany import gyors_elonezet

        with gyors_elonezet():
            provider.register("1", kep, _BW, shared_cache=False, sample_prefix_ops=_BW)
        renderek = len(lanc_szamlalo)

        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1

    def test_az_elavult_render_nem_jegyzi_meg_a_kepet(self, provider, kep, lanc_szamlalo):
        """`is_current` hamis: a render eldobódik, a bejegyzés sem készül."""
        provider.register(
            "1",
            kep,
            _BW,
            shared_cache=False,
            sample_prefix_ops=_BW,
            is_current=lambda: False,
        )
        renderek = len(lanc_szamlalo)

        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1

    def test_a_szoveg_nem_kerul_a_mintaba(self, provider, tmp_path):
        """A szövegréteg a lánc UTÁN rajzolódik: a minta a rétegelőtti kép.
        Egyszínű képen a minta mindenhol a kép színe, a kijelzett kép pedig ott
        tér el, ahol a szöveg van."""
        import numpy as np

        from picasapy.app.edit_preview import TextOverlaySpec

        piros = tmp_path / "piros.png"
        Image.new("RGB", (200, 200), (255, 0, 0)).save(piros, "PNG")
        szoveg = TextOverlaySpec(content="MMMMMMMM", x=0.1, y=0.4, font_size_pt=96.0)
        provider.register("1", piros, (), text=szoveg, shared_cache=False, sample_prefix_ops=())
        kijelzett = provider.rendered_image("1")
        tomb = np.frombuffer(
            bytes(kijelzett.convertToFormat(kijelzett.Format.Format_RGB888).constBits()),
            dtype=np.uint8,
        )[: 200 * 200 * 3].reshape(200, 200, 3)
        szoveg_pontok = np.argwhere((tomb != np.array([255, 0, 0])).any(axis=2))
        assert len(szoveg_pontok), "a próba feltétele: a szöveg a kijelzett képen látszik"
        y, x = (int(v) for v in szoveg_pontok[len(szoveg_pontok) // 2])

        minta = provider.sample_prefix_color("1", piros, (), x / 199, y / 199)

        assert minta == (255, 0, 0)

    def test_az_unregister_felszabaditja_a_bejegyzest(self, provider, kep, lanc_szamlalo):
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)
        renderek = len(lanc_szamlalo)

        provider.unregister("1")
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1

    def test_a_kep_elengedese_felszabaditja_a_bejegyzest(self, provider, kep, lanc_szamlalo):
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)
        renderek = len(lanc_szamlalo)

        provider.kepet_elenged("1")
        provider.sample_prefix_color("1", kep, _BW, 0.5, 0.5)

        assert len(lanc_szamlalo) == renderek + 1

    def test_ket_foto_bejegyzese_egymas_mellett_el(self, provider, tmp_path, lanc_szamlalo):
        elso = _foltos_kep(tmp_path / "egy.png")
        masodik = _foltos_kep(tmp_path / "ketto.png")
        provider.sample_prefix_color("1", elso, _BW, 0.5, 0.5)
        provider.sample_prefix_color("2", masodik, _BW, 0.5, 0.5)
        renderek = len(lanc_szamlalo)

        provider.sample_prefix_color("1", elso, _BW, 0.2, 0.2)
        provider.sample_prefix_color("2", masodik, _BW, 0.2, 0.2)

        assert len(lanc_szamlalo) == renderek

    def test_a_nem_olvashato_kep_nem_ad_mintat(self, provider, tmp_path):
        assert provider.sample_prefix_color("1", tmp_path / "nincs.png", _BW, 0.5, 0.5) is None

    def test_a_kepen_kivuli_pont_nem_ad_mintat(self, provider, kep):
        assert provider.sample_prefix_color("1", kep, _BW, 2.0, 0.5) is None
        assert provider.sample_prefix_color("1", kep, _BW, 0.5, -1.0) is None


class TestTeruletAtlag:
    """A #7345 E23/B14 mérése: 8 bites csatornánkénti egyszerű átlag, 5x5."""

    @pytest.fixture
    def nagy_kep(self, tmp_path) -> Path:
        return _foltos_kep(tmp_path / "color_patches.png")

    def _minta(self, provider, nagy_kep, x: int, y: int = _Y_SOR):
        meret = _N * _FOLT_PX
        return provider.sample_prefix_color(
            "1", nagy_kep, (), _normalt(meret, x), _normalt(meret, y)
        )

    def test_a_hataron_a_bezs_sulya_ketotod(self, provider, nagy_kep):
        """x=782 a nézőben = a kép 400. oszlopa, az első kék oszlop: a
        felvétel p4-e `ff74728a` = (116,114,138)."""
        assert self._minta(provider, nagy_kep, 400) == (116, 114, 138)

    @pytest.mark.parametrize("oszlop", [390, 380, 360])
    def test_tiz_kepponttol_a_hatartol_a_tiszta_folt(self, provider, nagy_kep, oszlop):
        """x=772, 762, 742 a nézőben: a p4 a tiszta bézs `ffc89779`."""
        assert self._minta(provider, nagy_kep, oszlop) == _BEZS

    def test_a_mintaablak_kozepre_igazitott(self, provider, nagy_kep):
        """A határ két oldalán a bézs súlya 3/5 és 1/5, a 4. oszlopnál már 0."""
        sulyozott = {399: 3, 398: 4, 401: 1, 402: 0}
        for oszlop, bezs in sulyozott.items():
            minta = self._minta(provider, nagy_kep, oszlop)
            elvart = tuple(
                (bezs * b + (5 - bezs) * k + 2) // 5 for b, k in zip(_BEZS, _KEK, strict=True)
            )
            assert all(abs(a - e) <= 1 for a, e in zip(minta, elvart, strict=True)), (
                oszlop,
                minta,
                elvart,
            )

    def test_a_kep_szelen_a_kep_kozotti_pontok_atlaga(self, provider, nagy_kep):
        """A sarokban az ablak a képre vágódik: a tiszta folt marad tiszta."""
        meret = _N * _FOLT_PX
        assert provider.sample_prefix_color("1", nagy_kep, (), 0.0, 0.0) == (255, 0, 0)
        sarok = provider.sample_prefix_color("1", nagy_kep, (), 1.0, 1.0)
        assert sarok == _FOLTOK[3][3]
        assert meret == 800

    def test_a_pipetta_a_hataron_a_sulyozott_atlagot_irja_p4_be(self, qt_app, tmp_path):
        """A teljes úton: `pickNeutralColor` a határon a mért `ff74728a`-t írja."""
        from picasapy.app.edit_controller import EditController
        from picasapy.app.edit_preview import EditPreviewProvider

        nagy_kep = _foltos_kep(tmp_path / "color_patches.png")
        elonezet = EditPreviewProvider()
        vezerlo = EditController(elonezet)
        vezerlo.beginEdit("1", str(nagy_kep))
        assert vezerlo.waitForBackgroundWorkers(10.0)
        meret = _N * _FOLT_PX

        assert vezerlo.pickNeutralColor(_normalt(meret, 400), _normalt(meret, _Y_SOR)) is True

        p4 = [
            elem.split("=", 1)[1].split(",")[4]
            for elem in str(vezerlo.chainValue).split(";")
            if elem.startswith("finetune2=")
        ]
        assert p4 == ["ff74728a"]


class TestMintaablakMerete:
    def test_az_ablak_az_ot_forraskepponthoz_igazodik(self):
        from picasapy.app.edit_preview_sample import mintaablak_oldala

        assert mintaablak_oldala(1.0) == 5
        assert mintaablak_oldala(0.8) == 5
        assert mintaablak_oldala(0.64) == 3
        assert mintaablak_oldala(0.5) == 3
        assert mintaablak_oldala(0.2) == 1
        assert mintaablak_oldala(0.01) == 1

    def test_az_ablak_mindig_paratlan_es_legalabb_egy(self):
        from picasapy.app.edit_preview_sample import mintaablak_oldala

        for darab in range(1, 400):
            oldal = mintaablak_oldala(darab / 100)
            assert oldal >= 1 and oldal % 2 == 1

    def test_ervenytelen_arany_az_alap_otot_adja(self):
        from picasapy.app.edit_preview_sample import mintaablak_oldala

        assert mintaablak_oldala(0.0) == 5
        assert mintaablak_oldala(float("nan")) == 5
        assert mintaablak_oldala(-1.0) == 5

    def test_a_kicsinyitett_elonezeten_kisebb_az_ablak(self, provider, tmp_path, monkeypatch):
        """Ha az előnézet a forrás 0,2-szerese, az 5 forrás-képpont 1 előnézeti
        képpont: a határ első kék oszlopa tiszta kék, nem keverék."""
        kep = _foltos_kep(tmp_path / "foltok.png")
        monkeypatch.setattr("picasapy.app.edit_preview._elonezeti_arany", lambda *_a: 0.2)
        meret = _N * _FOLT_PX

        minta = provider.sample_prefix_color(
            "1", kep, (), _normalt(meret, 400), _normalt(meret, _Y_SOR)
        )

        assert minta == _KEK

    def test_a_kozepes_aranyu_elonezeten_haromszeles_az_ablak(
        self, provider, tmp_path, monkeypatch
    ):
        """0,64: az ablak 3 széles, a határon a bézs súlya 1/3."""
        kep = _foltos_kep(tmp_path / "foltok.png")
        monkeypatch.setattr("picasapy.app.edit_preview._elonezeti_arany", lambda *_a: 0.64)
        meret = _N * _FOLT_PX

        minta = provider.sample_prefix_color(
            "1", kep, (), _normalt(meret, 400), _normalt(meret, _Y_SOR)
        )

        elvart = tuple(round((b + 2 * k) / 3) for b, k in zip(_BEZS, _KEK, strict=True))
        assert all(abs(a - e) <= 1 for a, e in zip(minta, elvart, strict=True)), (minta, elvart)


class TestVezerloKerese:
    @pytest.fixture
    def vezerlo(self, qt_app, provider):
        from picasapy.app.edit_controller import EditController

        return EditController(provider)

    def _megnyit(self, vezerlo, kep: Path) -> None:
        vezerlo.beginEdit("1", str(kep))
        assert vezerlo.waitForBackgroundWorkers(10.0)

    def test_az_elonezeti_kerelem_a_pipetta_lancat_is_viszi(self, vezerlo, kep):
        self._megnyit(vezerlo, kep)

        kerelem = vezerlo._preview_request()

        assert kerelem["sample_prefix_ops"] == vezerlo._neutral_sample_ops()

    def test_nyitott_latogatasnal_a_pipetta_lanca_a_reteg_elotti(self, vezerlo, kep):
        self._megnyit(vezerlo, kep)
        vezerlo.applyEffect("bw")
        assert vezerlo.waitForBackgroundWorkers(10.0)
        alap = vezerlo._session.ops
        vezerlo.pickNeutralColor(0.3, 0.3)
        assert vezerlo.waitForBackgroundWorkers(10.0)

        kerelem = vezerlo._preview_request()

        assert len(kerelem["ops"]) == len(alap) + 1
        assert kerelem["sample_prefix_ops"] == alap

    def test_az_elso_kattintas_a_hatterben_elkeszult_kepbol_jon(self, vezerlo, kep, lanc_szamlalo):
        """Megnyitás után a háttér-render kész: az első pipetta-kattintás
        nem renderel (a felület nem várakozik)."""
        self._megnyit(vezerlo, kep)
        vezerlo.applyEffect("bw")
        assert vezerlo.waitForBackgroundWorkers(10.0)
        renderek = lanc_szamlalo.fo_szalon

        assert vezerlo.pickNeutralColor(0.3, 0.3) is True

        assert lanc_szamlalo.fo_szalon == renderek, "az első kattintás a GUI-szálon renderelt"

    def test_a_latogatas_tovabbi_kattintasai_sem_renderelnek(self, vezerlo, kep, lanc_szamlalo):
        """A látogatás alatt a pipetta lánca állandó: a további kattintások, a
        csúszka-húzás utániak is, a tárolt képből jönnek."""
        self._megnyit(vezerlo, kep)
        vezerlo.applyEffect("bw")
        assert vezerlo.waitForBackgroundWorkers(10.0)
        vezerlo.pickNeutralColor(0.3, 0.3)
        vezerlo.setFinetune(0.0, 0.0, 0.0, 1.0)
        assert vezerlo.waitForBackgroundWorkers(10.0)
        renderek = lanc_szamlalo.fo_szalon

        assert vezerlo.pickNeutralColor(0.7, 0.7) is True
        assert vezerlo.pickNeutralColor(0.1, 0.9) is True

        assert lanc_szamlalo.fo_szalon == renderek, "a látogatás kattintása a GUI-szálon renderelt"
