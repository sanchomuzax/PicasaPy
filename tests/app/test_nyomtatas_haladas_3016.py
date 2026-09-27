"""A nyomtatás LAPONKÉNTI haladás-jelzése — a #3016 őre.

## Miért nem háttérszál a válasz

A #514 eredetileg azt javasolta, hogy a nyomtatás menjen háttérszálra. A
#3016 mérése ezt megdöntötte (12 megapixeles fotók, PDF-kimenet):

| lapszám | dekódolás | festés + PDF |
|---:|---:|---:|
| 1 | 50 ms | **300 ms** |
| 12 | 543 ms | **975 ms** |

A festés a munka kétharmada, és a Qt festő-/nyomtató-API-ja a **GUI-szálhoz
kötött** — nem tolható háttérszálra. ⇒ a megoldás nem a szál, hanem a
**visszajelzés**.

## Amit ez a lap kiköt

1. a `printProgress(kész, összes)` jelzés minden lapról szól, sorrendben;
2. ugyanaz a jelzés a PDF-ágon ÉS a nyomtatóra menő ágon (egy közös `_run`);
3. a jelzés **a festés közben** jön, nem a végén egy csomóban — különben
   nem visszajelzés, hanem utólagos jelentés;
4. a hosszú feladat alatt a közös haladásjelző (#505) is fut;
5. ⛔ **újbóli indítás TILOS**: a jelzés kedvéért a festés-ciklus
   eseményeket pörget, tehát a felhasználó rákattinthatna a Nyomtatás
   gombra másodszor is. A második hívás nem indulhat el.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QGuiApplication

from support.jpeg_factory import make_jpeg

try:
    from picasapy.app.busy_registry import get_app_busy_registry
    from picasapy.app.print_controller import PrintController

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csonka PySide6-telepítésen
    PrintController = None
    get_app_busy_registry = None
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen",
)


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _FakePhoto:
    folder_path: str
    name: str


def _vezerlo_harom_keppel(tmp_path):
    fotok = []
    for i in range(3):
        forras = make_jpeg(tmp_path / f"kep{i}.jpg", size=(200, 120))
        fotok.append(_FakePhoto(folder_path=str(tmp_path), name=forras.name))
    return PrintController(photo_source=lambda: fotok), fotok


def _egyetlen_cellas_lapot_kenyszerit(monkeypatch):
    """A lapgeometriát a nyomatméretnél (M4X6) csak KICSIT nagyobb, NÉGYZETES
    lapra rögzíti, hogy a #3647-es rács MINDIG pontosan egy cellát fogadjon
    laponként (a `test_nyomtatas_peldanyszam_1819.py` mintájára, #3685
    átnézése) — a `_device_page_geometry`-t, tehát a VALÓDI (PDF-)
    nyomtatási utat cseréli le, mert ez a fájl azt méri.

    Ez a fájl a LAPONKÉNTI HALADÁS-JELZÉST méri, nem a rácsba-rendezést —
    azt a `printing/test_nyomtatasi_racs_3647.py` fedi. A #3647 óta a
    fizikai lapszám a nyomatmérettől és a papírtól függ (nem képenként egy
    lap), ezért enélkül ezek a próbák a valódi (A4 alapértelmezésre eső)
    rácsszámításon múlnának — jelen esetben a 200×120-as tesztképek simán
    ELFÉRNÉNEK többedmagukkal egy A4-es lapon, tehát 3 kép NEM adna 3
    külön lapot.

    ⚠️ A lap oldala a nyomtató TÉNYLEGES felbontásához igazodik (a
    nyomatméret hosszabb oldalának 7-szerese, nem egy rögzített pixelszám):
    a #3685 átnézésekor egy korábbi próbálkozás rögzített `resolution × 15`
    lapot használt, ami 1200 DPI-n 3×2 cellát is elfogadott volna
    laponként — a 7-szeres szorzó mindkét cellatájolással (a
    `choose_page_orientation` a papírt már NEM forgatja, csak a cellát,
    ld. ott) PONTOSAN egy cellát enged, a gép tényleges DPI-jétől
    függetlenül."""
    import picasapy.app.print_controller as pc_modul

    def hamis_eszkoz(printer, orientation):
        printer.setPageOrientation(orientation)
        oldal = printer.resolution() * 7.0
        return pc_modul.PageGeometry(width=oldal, height=oldal, margin=0.0)

    monkeypatch.setattr(
        pc_modul.PrintController, "_device_page_geometry", staticmethod(hamis_eszkoz)
    )


class TestAHaladasJelzes:
    def test_laponkent_jon_jelzes(self, qt_app, tmp_path, monkeypatch):
        """#3685 átnézése: a #3647 óta a lapszám a nyomatmérettől és a
        papírtól függ, nem képenként egy lap — a próba ezért EGYETLEN
        cellás lapra kényszerítve méri, hogy a jelzés valóban laponként jön."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        jelzesek: list[tuple[int, int]] = []
        vezerlo.printProgress.connect(lambda k, o: jelzesek.append((k, o)))

        assert vezerlo.renderPrintPreviewPdf(
            [0, 1, 2], "fit", "auto", str(tmp_path / "ki.pdf")
        )

        assert jelzesek, "egyetlen haladás-jelzés sem jött"
        assert {o for _k, o in jelzesek} == {3}, (
            f"az ÖSSZES lapszám nem egységesen 3: {jelzesek}"
        )
        keszek = [k for k, _o in jelzesek]
        assert keszek == sorted(keszek), f"a jelzések nem monoton nőnek: {keszek}"
        assert keszek[-1] == 3, f"az utolsó jelzés nem a teljes: {keszek}"

    def test_a_peldanyszam_is_beleszamit(self, qt_app, tmp_path, monkeypatch):
        """#1819: két példány két képnél NÉGY lap — a jelző a LAPOKAT
        számolja, nem a kijelölt fotókat. EGYETLEN cellás lapra kényszerítve
        (#3685 átnézése), különben a lapszám a papírtól/nyomatmérettől
        függene, nem a példányszámtól."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        jelzesek: list[tuple[int, int]] = []
        vezerlo.printProgress.connect(lambda k, o: jelzesek.append((k, o)))

        assert vezerlo.renderPrintPreviewPdf(
            [0, 1], "fit", "auto", str(tmp_path / "ki.pdf"), 2
        )

        assert {o for _k, o in jelzesek} == {4}, jelzesek

    def test_a_jelzes_MENET_KOZBEN_jon(self, qt_app, tmp_path):
        """⛔ Ha a jelzések a festés UTÁN, egy csomóban jönnének, a
        felhasználó semmit nem látna belőlük. A próba a festés közben
        számol: az első lap jelzésekor a PDF még nincs kész."""
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        kimenet = tmp_path / "ki.pdf"
        kozben: list[bool] = []

        def figyel(kesz: int, _ossz: int) -> None:
            if kesz == 1:
                # a Qt a PDF-et a festő lezárásakor írja ki: ha ez a jelzés
                # tényleg menet közben jön, a fájl még nem teljes
                kozben.append(not kimenet.exists() or kimenet.stat().st_size == 0)

        vezerlo.printProgress.connect(figyel)
        assert vezerlo.renderPrintPreviewPdf([0, 1, 2], "fit", "auto", str(kimenet))
        assert kozben and kozben[0], (
            "az első lap jelzésekor a kimenet már kész volt — a jelzés "
            "utólagos jelentés, nem visszajelzés"
        )

    def test_a_kozos_haladasjelzo_is_fut(self, qt_app, tmp_path):
        """#505: a hosszú feladat alatt a közös csík is dolgozik."""
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        allapotok: list[bool] = []
        nyilvantartas = get_app_busy_registry()

        def figyel(_kesz: int, _ossz: int) -> None:
            allapotok.append(nyilvantartas.activeCount > 0)

        vezerlo.printProgress.connect(figyel)
        assert vezerlo.renderPrintPreviewPdf(
            [0, 1, 2], "fit", "auto", str(tmp_path / "ki.pdf")
        )
        assert allapotok and all(allapotok), (
            "a nyomtatás nem jelentkezett be a közös busy-nyilvántartásba"
        )
        assert nyilvantartas.activeCount == 0, "a bejelentkezés a végén nem oldódott fel"


class TestAzUjbolIndulasTILOS:
    """⛔ A jelzés kedvéért a ciklus eseményeket pörget — a felhasználó
    ilyenkor ismét megnyomhatja a Nyomtatás gombot."""

    def test_a_masodik_hivas_nem_indul_el(self, qt_app, tmp_path):
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        masodik: list[bool] = []

        def figyel(kesz: int, _ossz: int) -> None:
            if kesz == 1 and not masodik:
                masodik.append(
                    vezerlo.renderPrintPreviewPdf(
                        [0], "fit", "auto", str(tmp_path / "masodik.pdf")
                    )
                )

        vezerlo.printProgress.connect(figyel)
        assert vezerlo.renderPrintPreviewPdf(
            [0, 1, 2], "fit", "auto", str(tmp_path / "ki.pdf")
        )
        assert masodik == [False], (
            "a nyomtatás közben indított MÁSODIK nyomtatás elindult — a "
            "két feladat ugyanarra a festőre menne"
        )
        assert not (tmp_path / "masodik.pdf").exists()

    def test_a_zar_a_vegen_felold(self, qt_app, tmp_path):
        """A védés nem ragadhat be: a feladat után újra lehet nyomtatni."""
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        assert vezerlo.renderPrintPreviewPdf([0], "fit", "auto", str(tmp_path / "a.pdf"))
        assert vezerlo.renderPrintPreviewPdf([1], "fit", "auto", str(tmp_path / "b.pdf"))


class TestAFrissitesRITKITASA:
    """⏱️ #3016: a jelzés MINDEN lapról szól, az eseményhurkot viszont
    ritkítva engedjük vissza.

    **Mért indok** (12 megapixeles fotók, PDF, RPi5): laponkénti
    `processEvents` mellett a 12 lapos feladat 2388 → 2815 ms lett,
    **+427 ms (+18 %)**. Egy és négy lapnál a különbség a zajban maradt.
    A ritkítás után a 12 lapos esetet HÁROMSZOR mértem: −100 / +7 / +144 ms
    (medián +7) — a különbség tehát a futások közti SZÓRÁSBA esik, szemben
    a ritkítás nélküli, következetes +427 ms-mal. A jegy negyedik feltétele
    („az észlelt megállás ideje nem nő") ezzel mérésből teljesül.
    """

    def _szamlalo(self, monkeypatch, kesleltetes_ms: float):
        """A modul `QCoreApplication`-jét cseréljük, hogy SZÁMOLNI tudjuk,
        hányszor engedtük vissza az eseményhurkot."""
        from picasapy.app import print_controller as modul

        hivasok: list[int] = []

        class _Alkalmazas:
            @staticmethod
            def processEvents() -> None:  # noqa: N802 — Qt-API
                hivasok.append(1)

        class _Csere:
            @staticmethod
            def instance() -> _Alkalmazas:
                return _Alkalmazas()

        monkeypatch.setattr(modul, "QCoreApplication", _Csere)
        monkeypatch.setattr(modul, "_FRISSITES_MS", kesleltetes_ms)
        return hivasok

    def test_hosszu_kesleltetesnel_csak_az_ELSO_es_az_UTOLSO_lap_enged(
        self, qt_app, tmp_path, monkeypatch
    ):
        """Két lap MINDIG átengedi az eseményeket, a ritkítástól függetlenül:

        * az **első** — hogy a felhasználó azonnal lássa, elindult a munka
          (a feladat elején a ritkítás-óra nullázódik);
        * az **utolsó** — hogy a „kész" állapot ne késsen.

        A köztes lapokat ritkítjuk; ez adja a mért nyereséget.

        EGYETLEN cellás lapra kényszerítve (#3685 átnézése) — a jelzés
        laponkénti mivoltát ez a fájl méri, nem a rácsba-rendezést."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        hivasok = self._szamlalo(monkeypatch, 10_000.0)
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        jelzesek: list[int] = []
        vezerlo.printProgress.connect(lambda k, _o: jelzesek.append(k))

        assert vezerlo.renderPrintPreviewPdf(
            [0, 1, 2], "fit", "auto", str(tmp_path / "ki.pdf")
        )

        assert jelzesek == [1, 2, 3], "a JELZÉS minden lapról szól, ezt nem ritkítjuk"
        assert len(hivasok) == 2, (
            f"{len(hivasok)} eseményhurok-átengedés történt 2 helyett (az "
            "elsőnek és az utolsónak kell átengednie) — a ritkítás nem "
            "a várt módon működik"
        )

    def test_nulla_kesleltetesnel_MINDEN_lap_enged(
        self, qt_app, tmp_path, monkeypatch
    ):
        """EGYETLEN cellás lapra kényszerítve (#3685 átnézése)."""
        _egyetlen_cellas_lapot_kenyszerit(monkeypatch)
        hivasok = self._szamlalo(monkeypatch, 0.0)
        vezerlo, _ = _vezerlo_harom_keppel(tmp_path)
        assert vezerlo.renderPrintPreviewPdf(
            [0, 1, 2], "fit", "auto", str(tmp_path / "ki.pdf")
        )
        assert len(hivasok) == 3
