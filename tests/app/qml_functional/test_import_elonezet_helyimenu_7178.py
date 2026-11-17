"""#7178: az import előnézetének bélyegképén jobbklikk-menü nyílik.

Eredeti: a bélyegkép helyi menüje (`0x00733c70`, 20 bájtos rekordok) négy
parancsot kínál ebben a sorrendben: `Include File`, `Exclude File`,
`Include All`, `Exclude All`.

A próba VALÓDI egérrel dolgozik: jobbkattintás a bélyegképen, majd valódi
balkattintás a menüpontokon. Sem a menüpontok `onTriggered`-jét, sem a
vezérlő metódusait nem hívja közvetlenül; az eredményt a bélyegkép alatti
Include/Exclude felirat és a párbeszéd `previewItems` listája mutatja.

Amit a próba NEM mér: a menü vizuális egyezését az eredetivel. Eredeti
képernyőkép nincs hozzá, ezért a feliratok szövege, a sorrend és a hatás
igazolt, a menü kinézete (méret, margó, betű) nem.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QPointF, Qt

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _keszits_konyvtarat,
)
from test_menu_talca_egyeb_valodi_5135_e import _import_megnyit
from test_racs_vezerlok_valodi_5135 import (
    _kattints_elemre,
    _kattints_mindenablakban,
    _vizualis_mindenablakban,
    _zar,
)

_MENU_TETELEK = (
    ("importSourceThumbMenuIncludeFile", "Include File"),
    ("importSourceThumbMenuExcludeFile", "Exclude File"),
    ("importSourceThumbMenuIncludeAll", "Include All"),
    ("importSourceThumbMenuExcludeAll", "Exclude All"),
)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


@pytest.fixture
def import_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _forras_mappa(tmp_path: Path) -> Path:
    """Két képet tartalmazó, a könyvtáron KÍVÜLI forrásmappa."""
    forras = tmp_path / "forras"
    forras.mkdir()
    make_jpeg(forras / "elso.jpg", size=(160, 120))
    make_jpeg(forras / "masodik.jpg", size=(160, 120))
    return forras


def _felirat(index: int) -> str | None:
    """A bélyegkép alatti Include/Exclude felirat (None: nem látszik)."""
    _ablak, elem = _vizualis_mindenablakban(f"importSourceToggleLabel:{index}")
    return None if elem is None else str(elem.property("text"))


def _feliratok() -> list[str | None]:
    return [_felirat(0), _felirat(1)]


@pytest.fixture
def megnyitott_import(import_app, qt_app, tmp_path):
    """Megnyitott importablak két képpel, mindkettő bevonva."""
    window, controller, _engine = import_app
    _elokeszit(window, qt_app, controller)
    dialog = _import_megnyit(window, qt_app)
    dialog.setProperty("sourceFolder", str(_forras_mappa(tmp_path)))
    dialog.setProperty("sourceFiles", [])
    QMetaObject.invokeMethod(
        dialog, "scanCurrentSource", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert _varj(qt_app, lambda: _feliratok() == ["Exclude", "Exclude"]), (
        "a tmp forrás két bélyegképe nem jelent meg bevont állapotban"
    )
    yield dialog
    _zar(qt_app, dialog)


def _jobbklikk_a_belyegen(qt_app, index: int) -> None:
    nev = f"importSourceThumbMenuArea:{index}"
    ablak, elem = _vizualis_mindenablakban(nev)
    assert elem is not None, f"{nev} nem látszik"
    _kattints_elemre(qt_app, ablak, elem, Qt.MouseButton.RightButton)


def _menupont(nev: str):
    return _vizualis_mindenablakban(nev)[1]


def _menu_parancs(qt_app, index: int, nev: str) -> None:
    """Jobbkattintás a `index`-edik bélyegképen, majd a `nev` menüpontra."""
    _jobbklikk_a_belyegen(qt_app, index)
    assert _varj(qt_app, lambda: _menupont(nev) is not None), (
        f"a jobbklikk nem nyitotta meg a menüt: {nev} nem látszik"
    )
    _kattints_mindenablakban(qt_app, nev)


class TestBelyegHelyiMenu:
    def test_a_jobbklikk_negy_parancsot_kinal_az_eredeti_sorrendjeben(
        self, megnyitott_import, qt_app
    ):
        _jobbklikk_a_belyegen(qt_app, 0)
        assert _varj(
            qt_app,
            lambda: all(_menupont(nev) is not None for nev, _ in _MENU_TETELEK),
        ), "a jobbklikk nem nyitotta meg a négy parancsos menüt"

        szovegek = [
            str(_menupont(nev).property("text")) for nev, _ in _MENU_TETELEK
        ]
        assert szovegek == [szoveg for _, szoveg in _MENU_TETELEK]
        # az eredeti rekordtáblájának sorrendje: fentről lefelé
        magassagok = [
            _menupont(nev).mapToScene(QPointF(0, 0)).y() for nev, _ in _MENU_TETELEK
        ]
        assert magassagok == sorted(magassagok)

    def test_az_exclude_file_csak_a_jobbkattintott_kepet_zarja_ki(
        self, megnyitott_import, qt_app
    ):
        _menu_parancs(qt_app, 1, "importSourceThumbMenuExcludeFile")

        assert _varj(qt_app, lambda: _feliratok() == ["Exclude", "Include"]), (
            f"az Exclude File nem a jobbkattintott képet zárta ki: {_feliratok()}"
        )

    def test_az_include_file_visszaveszi_a_kizart_kepet(
        self, megnyitott_import, qt_app
    ):
        _menu_parancs(qt_app, 0, "importSourceThumbMenuExcludeFile")
        assert _varj(qt_app, lambda: _feliratok() == ["Include", "Exclude"])

        _menu_parancs(qt_app, 0, "importSourceThumbMenuIncludeFile")

        assert _varj(qt_app, lambda: _feliratok() == ["Exclude", "Exclude"]), (
            f"az Include File nem vette vissza a képet: {_feliratok()}"
        )

    def test_az_exclude_all_majd_include_all_minden_kepre_hat(
        self, megnyitott_import, qt_app
    ):
        _menu_parancs(qt_app, 0, "importSourceThumbMenuExcludeAll")
        assert _varj(qt_app, lambda: _feliratok() == ["Include", "Include"]), (
            f"az Exclude All nem zárt ki mindent: {_feliratok()}"
        )

        _menu_parancs(qt_app, 1, "importSourceThumbMenuIncludeAll")

        assert _varj(qt_app, lambda: _feliratok() == ["Exclude", "Exclude"]), (
            f"az Include All nem vett vissza mindent: {_feliratok()}"
        )

    def test_a_menu_ugyanazt_az_allapotot_irja_mint_a_mai_gombok(
        self, megnyitott_import, qt_app
    ):
        dialog = megnyitott_import

        def kizartak() -> list[bool]:
            elemek = dialog.property("previewItems")
            return [bool(elem["excluded"]) for elem in elemek]

        _menu_parancs(qt_app, 0, "importSourceThumbMenuExcludeAll")
        assert _varj(qt_app, lambda: kizartak() == [True, True])
        menubol = kizartak()

        _kattints_mindenablakban(qt_app, "importSourceIncludeAllButton")
        assert _varj(qt_app, lambda: kizartak() == [False, False]), (
            "a mai Include All gomb nem működik változatlanul"
        )
        _kattints_mindenablakban(qt_app, "importSourceExcludeAllButton")
        assert _varj(qt_app, lambda: kizartak() == menubol), (
            "a mai Exclude All gomb más állapotot ír, mint a menüparancs"
        )

    def test_a_mai_hivatkozas_a_jobbklikk_utan_is_valtozatlanul_kapcsol(
        self, megnyitott_import, qt_app
    ):
        _menu_parancs(qt_app, 0, "importSourceThumbMenuExcludeFile")
        assert _varj(qt_app, lambda: _feliratok() == ["Include", "Exclude"])

        _kattints_mindenablakban(qt_app, "importSourceToggle:0")

        assert _varj(qt_app, lambda: _feliratok() == ["Exclude", "Exclude"]), (
            "a bélyegkép alatti hivatkozás a jobbklikk után nem kapcsol"
        )
