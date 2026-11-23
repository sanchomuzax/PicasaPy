"""A Hangolás pipettája VALÓDI kattintással és nyíllal: forrásszín és képváltás (#7385).

Az eredeti Picasában (J5a, J5d):

- a pipetta a kép FORRÁSÁNAK színét írja p4-be (`ffc89779`), akkor is, ha a
  Színhőmérséklet a jobb szélen áll, vagy a folt az előző mintavétel óta már
  szürke;
- a képváltás a pipettát felengedi: következő kép, vissza, a gomb nincs
  lenyomva, és az első képkattintás nem mintáz (J5d 15., 17. kocka).

Minden gomb- és képkattintás `QTest.mouseClick`, a képváltás `QTest.keyClick`
(nyíl); a teszt sosem emittál és nem hív `clicked`-et. A Színhőmérséklet
beállítása állapot-előkészítés a vezérlőn (a csúszka-húzás nem tárgya ennek a
tesztnek). Rontás-kontroll: ha a mintavétel visszakerül a megjelenített
előnézetre, a forrásszínes teszt elbukik; ha a képváltás nem kapcsolja ki a
pipettát, a képváltásos.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import _build_qml_app
from PIL import Image
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from _szerkeszto_5150_helpers import fulre, item, kattint, nyitott_panel, szerkeszto, varj

_N = 4
_FOLT_PX = 150
#: a J5-ös mintakép foltjai (`job-855` 13. kocka: módosítatlan kép)
_FOLTOK = (
    ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)),
    ((0, 255, 255), (255, 0, 255), (255, 255, 255), (0, 0, 0)),
    ((128, 128, 128), (0xC8, 0x97, 0x79), (0x3C, 0x5A, 0x96), (0x5B, 0x8C, 0x3B)),
    ((0xE5, 0xC8, 0x3C), (0x77, 0x3C, 0x8C), (0xF0, 0xF0, 0xF0), (0x1E, 0x1E, 0x1E)),
)
#: a beige folt közepe a kirajzolt kép [0..1] koordinátáiban (2. sor, 1. oszlop)
_BEIGE_X = (1 * _FOLT_PX + _FOLT_PX / 2) / (_N * _FOLT_PX)
_BEIGE_Y = (2 * _FOLT_PX + _FOLT_PX / 2) / (_N * _FOLT_PX)
_FOLT_KEP = "a_foltok.jpg"


def _foltos_kepek(konyvtar: Path) -> None:
    """A folt-kép és egy másik kép: a nyíl a másikra léptet."""
    kep = Image.new("RGB", (_N * _FOLT_PX, _N * _FOLT_PX))
    for sor in range(_N):
        for oszlop in range(_N):
            kep.paste(
                _FOLTOK[sor][oszlop],
                (
                    oszlop * _FOLT_PX,
                    sor * _FOLT_PX,
                    (oszlop + 1) * _FOLT_PX,
                    (sor + 1) * _FOLT_PX,
                ),
            )
    kep.save(konyvtar / _FOLT_KEP, "JPEG", quality=100, subsampling=0)
    Image.new("RGB", (_N * _FOLT_PX, _N * _FOLT_PX), (40, 90, 160)).save(
        konyvtar / "b_masik.jpg", "JPEG", quality=100, subsampling=0
    )


@pytest.fixture
def foltos_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_foltos_kepek)


def _forras_szine(tmp_path: Path) -> str:
    """A beige folt színe `#rrggbb` alakban, ugyanazzal a dekóderrel olvasva."""
    kep = QImage(str(tmp_path / "kepek" / _FOLT_KEP))
    assert not kep.isNull()
    szin = kep.pixelColor(
        round(_BEIGE_X * (kep.width() - 1)), round(_BEIGE_Y * (kep.height() - 1))
    )
    return szin.name()


def _mintavetel_figyelese(viewer) -> list:
    """A mintavételek számlálója: a pipetta két lehetséges útját is figyeli."""
    hivasok: list = []
    szolgaltato = szerkeszto(viewer)._provider
    for nev in ("sample_prefix_color", "sample_color"):
        eredeti = getattr(szolgaltato, nev)

        def csonk(*args, _eredeti=eredeti, _nev=nev, **kwargs):
            hivasok.append(_nev)
            return _eredeti(*args, **kwargs)

        setattr(szolgaltato, nev, csonk)
    return hivasok


def _pipetta_elesitve(window, qt_app, panel) -> None:
    fulre(window, qt_app, "editTabFinetune")
    assert varj(qt_app, lambda: panel.property("activeTab") == 1)
    kattint(window, item(window, "finetuneNeutralPicker"), qt_app)
    assert varj(qt_app, lambda: panel.property("neutralPickerActive") is True), (
        "a próba feltétele: a pipetta élesítve"
    )


def _kattint_a_beige_foltra(window, qt_app) -> None:
    """Valódi bal egérkattintás a kirajzolt kép beige foltjára."""
    terulet = item(window, "neutralPickArea")
    assert terulet.width() > 0 and terulet.height() > 0
    pont = terulet.mapToScene(
        QPointF(_BEIGE_X * terulet.width(), _BEIGE_Y * terulet.height())
    )
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont.toPoint())
    for _ in range(5):
        qt_app.processEvents()


def _nyil(window, qt_app, gomb) -> None:
    QTest.keyClick(window, gomb)
    for _ in range(5):
        qt_app.processEvents()


def _varj_a_rajzra(viewer) -> None:
    assert szerkeszto(viewer).waitForBackgroundWorkers(10.0), "az előnézeti worker nem állt le"


def test_a_pipetta_a_forras_szinet_irja_nem_nulla_homerseklet_mellett_is(
    foltos_app, qt_app, tmp_path
):
    """J5a 23-25. kocka: a beige folt előnézete `cf9c54`, a p4 mégis a forrás
    `c89779`; az első mintavétel után a folt szürke, és a p4 újra a forrás."""
    window, _c, viewer, panel = nyitott_panel(foltos_app, qt_app)
    elvart = _forras_szine(tmp_path)
    assert elvart == "#c89779", "a próba feltétele: a kép beige foltja a J5-ös szín"
    vezerlo = szerkeszto(viewer)
    _pipetta_elesitve(window, qt_app, panel)

    _kattint_a_beige_foltra(window, qt_app)

    assert varj(qt_app, lambda: vezerlo.property("neutralColor") == elvart), (
        f"az első mintavétel nem a forrás színét írta: {vezerlo.property('neutralColor')}"
    )
    assert panel.property("neutralPickerActive") is False, "az egyszeri használat után a pipetta nem kapcsolt ki"

    # a folt most szürke, a Színhőmérséklet a jobb szélre: az előnézet eltér a forrástól
    vezerlo.setFinetune(0.0, 0.0, 0.0, 1.0)
    _varj_a_rajzra(viewer)
    _pipetta_elesitve(window, qt_app, panel)
    _kattint_a_beige_foltra(window, qt_app)

    assert varj(qt_app, lambda: panel.property("neutralPickerActive") is False)
    assert vezerlo.property("neutralColor") == elvart, (
        "a második mintavétel az előnézet színét írta, nem a forrásét: "
        f"{vezerlo.property('neutralColor')}"
    )
    ini = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
    assert "ffc89779" in ini, ini


def test_kepvaltas_utan_a_pipetta_felengedve_es_az_elso_kepkattintas_nem_mintaz(
    foltos_app, qt_app
):
    """J5d 15., 17. kocka: élesített pipetta, következő kép, vissza: a gomb
    felengedett, és az első képkattintás nem vesz mintát, nem ír réteget."""
    window, _c, viewer, panel = nyitott_panel(foltos_app, qt_app)
    hivasok = _mintavetel_figyelese(viewer)
    _pipetta_elesitve(window, qt_app, panel)
    assert viewer.property("currentIndex") == 0

    _nyil(window, qt_app, Qt.Key.Key_Right)

    assert varj(qt_app, lambda: viewer.property("currentIndex") == 1), "a nyíl nem léptetett"
    assert panel.property("neutralPickerActive") is False, (
        "a következő képre lépés nem kapcsolta ki a pipettát"
    )
    assert item(window, "finetuneNeutralPicker").property("active") is False, (
        "a pipettagomb lenyomva látszik a következő képen"
    )

    _nyil(window, qt_app, Qt.Key.Key_Left)

    assert varj(qt_app, lambda: viewer.property("currentIndex") == 0), "a nyíl nem léptetett vissza"
    assert panel.property("neutralPickerActive") is False
    assert item(window, "finetuneNeutralPicker").property("active") is False, (
        "a pipettagomb lenyomva látszik a visszaléptetett képen"
    )
    kattint(window, item(window, "neutralPickArea"), qt_app)
    assert hivasok == [], "az első képkattintás visszatéréskor mintát vett"
    assert szerkeszto(viewer).property("canUndo") is False, (
        "az első képkattintás visszatéréskor réteget írt a láncra"
    )


def test_kepvaltas_nelkul_az_elesitett_pipetta_marad_eles(foltos_app, qt_app):
    """Szomszéd-regresszió: a képváltás-kikapcsolás nem érinti az élesítést
    magát: képváltás nélkül a gomb lenyomva marad, és az első kattintás mintáz."""
    window, _c, viewer, panel = nyitott_panel(foltos_app, qt_app)
    hivasok = _mintavetel_figyelese(viewer)

    _pipetta_elesitve(window, qt_app, panel)

    assert panel.property("neutralPickerActive") is True
    assert item(window, "finetuneNeutralPicker").property("active") is True
    _kattint_a_beige_foltra(window, qt_app)
    assert hivasok == ["sample_prefix_color"], hivasok
    assert panel.property("neutralPickerActive") is False
