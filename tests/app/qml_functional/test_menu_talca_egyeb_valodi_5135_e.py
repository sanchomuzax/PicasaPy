"""Az „Egyéb" táblázat tételei VALÓDI egérkattintással (#5135, 3. rész, E).

Fájl ▸ Import From… (Ctrl+M): a forrás-importáló párbeszéd vezérlői.
Forrás (mappa, kártya) nélkül is nyílik, és minden vezérlője engedélyezett.
Az állapotot a párbeszéd (`namingMode`, `afterCopying`) és a vezérlő
(`mediaFilter`, `resizeLimit`) mezőin mérjük.

Lefedve:
- `importSourceNamingTodayRadio`, `importSourceNamingByDateRadio` - az
  elnevezés módja;
- `importSourceAfterDeleteCopiedRadio`, `importSourceAfterDeleteAllRadio`,
  `importSourceAfterLeaveRadio` - a másolás utáni teendő. Csak a rádiót
  állítjuk át (és vissza), a törlés magát nem indítjuk el;
- `importSourceMediaFilterBox` - a médiaszűrő legördülője;
- `importSourceResizeBox` - az átméretezés-választó legördülője;
- `importSourceChooseDestButton` - a cél-mappa tallózása a mappaválasztót
  nyitja (a QML-párbeszéd `visible` állapotát mérjük, nem a natív ablakot).
- `exportBrowseButton` (Fájl ▸ Export Picture to Folder…) - a célválasztó.

Nincs lefedve ebben a körben: `importSourceToggle:<n>` (bélyegkép kizárása),
mert a bélyegképekhez egy valódi forrásmappa kell.

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _menupont_kattintasa,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _fajlvalasztó_nyitva,
    _gyerek,
    _keszits_konyvtarat,
    _latszik,
    _valasztoablak,
    _valassz_legordulobol,
    _varj,
    _zar,
)


@pytest.fixture
def import_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _import_megnyit(window, qt_app):
    """Fájl ▸ Import From… valódi kattintással; visszaadja a párbeszédet."""
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&File")
    _menupont_kattintasa(window, qt_app, "menuFileImportFrom")
    assert _varj(qt_app, lambda: _latszik(window, "importSourceDialog")), (
        "a Fájl ▸ Import From… nem nyitotta meg az importálást"
    )
    return _gyerek(window, "importSourceDialog")


def _kattint_es_var(window, qt_app, nev: str, feltetel) -> None:
    """Valódi kattintás a `nev` vezérlőn, majd várakozás az állapotra."""
    _kattints(qt_app, _gyerek(window, nev))
    assert _varj(qt_app, feltetel), f"a(z) {nev} kattintás nem váltotta az állapotot"


class TestElnevezes:
    def test_mai_datum_radio_valodi_kattintassal_valtja_az_elnevezest(
        self, import_app, qt_app
    ):
        window, controller, _engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        assert dialog.property("namingMode") == "date"

        _kattint_es_var(
            window, qt_app, "importSourceNamingTodayRadio",
            lambda: dialog.property("namingMode") == "today",
        )
        _kattint_es_var(
            window, qt_app, "importSourceNamingByDateRadio",
            lambda: dialog.property("namingMode") == "date",
        )
        _zar(qt_app, dialog)


class TestMasolasUtan:
    def test_torles_masolas_utan_radio_valodi_kattintassal_valtozik(
        self, import_app, qt_app
    ):
        window, controller, _engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        assert dialog.property("afterCopying") == "leave"

        _kattint_es_var(
            window, qt_app, "importSourceAfterDeleteCopiedRadio",
            lambda: dialog.property("afterCopying") == "delete_copied",
        )
        _kattint_es_var(
            window, qt_app, "importSourceAfterLeaveRadio",
            lambda: dialog.property("afterCopying") == "leave",
        )
        _zar(qt_app, dialog)

    def test_minden_torlese_radio_valodi_kattintassal_valtozik(
        self, import_app, qt_app
    ):
        """Csak a rádió állapota változik; a törlést nem indítjuk el."""
        window, controller, _engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)

        _kattint_es_var(
            window, qt_app, "importSourceAfterDeleteAllRadio",
            lambda: dialog.property("afterCopying") == "delete_all",
        )
        _kattint_es_var(
            window, qt_app, "importSourceAfterLeaveRadio",
            lambda: dialog.property("afterCopying") == "leave",
        )
        _zar(qt_app, dialog)


class TestLegordulok:
    def test_mediaszuro_valodi_kattintassal_allitja_a_szurot(
        self, import_app, qt_app
    ):
        window, controller, engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        import_ctl = engine.rootContext().contextProperty("importSourceController")
        szuro = _gyerek(window, "importSourceMediaFilterBox")
        assert import_ctl.property("mediaFilter") != "pictures"

        _valassz_legordulobol(qt_app, dialog, szuro, "Picture Files")
        assert _varj(
            qt_app, lambda: import_ctl.property("mediaFilter") == "pictures"
        ), (
            "a Picture Files tétel nem állította a médiaszűrőt"
        )
        _zar(qt_app, dialog)

    def test_atmeretezes_valodi_kattintassal_allitja_a_hatart(
        self, import_app, qt_app
    ):
        window, controller, engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        import_ctl = engine.rootContext().contextProperty("importSourceController")
        valaszto = _gyerek(window, "importSourceResizeBox")
        cel = valaszto.property("opciok")[1]
        cimke = valaszto.property("model")[1]

        _valassz_legordulobol(qt_app, dialog, valaszto, cimke)
        assert _varj(
            qt_app, lambda: import_ctl.property("resizeLimit") == cel
        ), f"a(z) {cimke!r} tétel nem állította az átméretezési határt"
        _zar(qt_app, dialog)


class TestCelMappa:
    def test_cel_mappa_tallozas_valodi_kattintassal_megnyitja_a_valasztot(
        self, import_app, qt_app
    ):
        window, controller, _engine = import_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        assert not _fajlvalasztó_nyitva(dialog)

        _kattints(qt_app, _gyerek(window, "importSourceChooseDestButton"))

        assert _varj(qt_app, lambda: _fajlvalasztó_nyitva(dialog)), (
            "a cél-mappa tallózása nem nyitotta meg a mappaválasztót"
        )
        for elem in dialog.findChildren(QObject):
            if _valasztoablak(elem):
                _zar(qt_app, elem)
        _zar(qt_app, dialog)


class TestKepExportalas:
    def test_export_tallozas_valodi_kattintassal_megnyitja_a_celvalasztot(
        self, import_app, qt_app
    ):
        window, controller, _engine = import_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&File")
        _menupont_kattintasa(window, qt_app, "menuFileExport")
        assert _varj(qt_app, lambda: _latszik(window, "exportDialog")), (
            "a Fájl ▸ Export Picture to Folder… nem nyitotta meg az exportot"
        )
        export = _gyerek(window, "exportDialog")
        assert not _fajlvalasztó_nyitva(window), "már nyitva volt a célválasztó"

        _kattints(qt_app, _gyerek(window, "exportBrowseButton"))

        # a célválasztó a párbeszéd szülőjében (ExportDialogs) él, nem a gyermekei közt
        assert _varj(qt_app, lambda: _fajlvalasztó_nyitva(window)), (
            "az exportban a Tallózás gomb nem nyitotta meg a célválasztót"
        )
        for elem in window.findChildren(QObject):
            if _valasztoablak(elem) and elem.property("visible") is True:
                _zar(qt_app, elem)
        _zar(qt_app, export)
