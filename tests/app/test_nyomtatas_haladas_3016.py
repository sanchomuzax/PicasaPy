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


class TestAHaladasJelzes:
    def test_laponkent_jon_jelzes(self, qt_app, tmp_path):
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

    def test_a_peldanyszam_is_beleszamit(self, qt_app, tmp_path):
        """#1819: két példány két képnél NÉGY lap — a jelző a LAPOKAT
        számolja, nem a kijelölt fotókat."""
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
