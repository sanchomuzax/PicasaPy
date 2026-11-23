"""#7373 - a javaslatküszöb változása az OK után azonnal frissíti a javaslatokat.

Az eredeti Picasa OK-kezelője (`0x005cf5b0`) csak akkor egyezteti a
személyek tagságát, ha a `FRSuggestionThreshold` változott (`0x0048aab0`);
a csoportküszöb (`FRSortThreshold`) változása nem váltja ki.

Két szint:

* a vezérlő `refreshSuggestions()` résztvevője: lazított küszöbnél új
  javaslatot ír és jelez, szigorúbbnál nem ír, a munka háttérszálon fut;
* a valódi Beállítások-ablak OK-ja: csak a javaslatküszöb tényleges
  változása hívja, a változatlan érték és a csoportküszöb önmagában nem.

A felvétel alapú (látás szerinti) elfogadási próba a jegyen vár a felvételre,
ezek a próbák azt nem pótolják.
"""

from __future__ import annotations

import threading

import numpy as np
import pytest
from PySide6.QtCore import QSettings, Slot

from picasapy.app.face_scan_controller import FaceScanController
from picasapy.faces.clustering import DEFAULT_SUGGEST_STEP, step_to_threshold
from picasapy.index import open_index
from picasapy.index.face_groups import lazitott_lepcso
from tests.app.test_qml_options_dialog import (  # noqa: F401 -- fixture-ok
    FakeFaceScanController,
    _child,
    _csuszkara_kattint,
    _elfogad,
    _var,
    dialog,
    fake_confirm_settings,
    fake_controller,
)
from tests.app.test_tobb_javaslat_vezerlo_3237 import _arc, _kozeli

_NEVCIMKE_FUL = 7


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    """Vezérlő egy nevesített és egy köztes hasonlóságú névtelen arccal.

    Az alapküszöbön (85) a köztes arc nem kap javaslatot, a lazított (75)
    küszöbön igen.
    """
    alap = np.array([1.0, 0.0], dtype=np.float32)
    alap_kuszob = step_to_threshold(DEFAULT_SUGGEST_STEP)
    lazitott = step_to_threshold(lazitott_lepcso(DEFAULT_SUGGEST_STEP))
    kozepe = (alap_kuszob + lazitott) / 2
    with open_index(tmp_path / "index.db") as conn:
        conn.execute("INSERT INTO folders (path, has_ini) VALUES ('/k', 0)")
        _arc(conn, "anna.jpg", alap, allapot="named", nev="Kiss Anna")
        _arc(conn, "ketes.jpg", _kozeli(alap, kozepe))
        conn.commit()
    beallitas = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    ctl = FaceScanController(tmp_path / "index.db", settings=beallitas)
    yield ctl, tmp_path
    ctl.waitForBackgroundWorkers(10.0)


def _javaslatos_arcok(tmp_path) -> int:
    with open_index(tmp_path / "index.db") as conn:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM face WHERE suggested_name IS NOT NULL"
        ).fetchone()["n"]


def _frissit_es_var(ctl, qt_app) -> None:
    ctl.refreshSuggestions()
    assert ctl.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()


class TestAVezerloFrissitese:
    def test_lazitott_kuszob_utan_no_a_javaslatos_arcok_szama_es_jelez(
        self, vezerlo, qt_app
    ):
        ctl, tmp_path = vezerlo
        jelzesek = []
        ctl.unnamedCountChanged.connect(lambda: jelzesek.append(1))

        ctl.setSuggestionThreshold(75)
        assert _javaslatos_arcok(tmp_path) == 0, (
            "a küszöb mentése önmagában nem számol újra"
        )

        _frissit_es_var(ctl, qt_app)

        assert _javaslatos_arcok(tmp_path) == 1
        assert jelzesek, "az unnamedCountChanged nem érkezett meg"

    def test_szigorubb_kuszob_nem_ir_es_nem_jelez(self, vezerlo, qt_app):
        ctl, tmp_path = vezerlo
        jelzesek = []
        ctl.unnamedCountChanged.connect(lambda: jelzesek.append(1))

        ctl.setSuggestionThreshold(95)
        _frissit_es_var(ctl, qt_app)

        assert _javaslatos_arcok(tmp_path) == 0
        assert jelzesek == []

    def test_kikapcsolt_javaslatoknal_nem_szamol_ujra(self, vezerlo, qt_app):
        ctl, tmp_path = vezerlo
        ctl.setSuggestionsEnabled(False)
        ctl.setSuggestionThreshold(75)

        _frissit_es_var(ctl, qt_app)

        assert _javaslatos_arcok(tmp_path) == 0

    def test_a_szamitas_hatterszalon_fut(self, vezerlo, qt_app, monkeypatch):
        """Nagy könyvtárban az OK nem fagyaszthatja a felületet."""
        import picasapy.app.face_scan_controller_suggestions_mixin as modul

        szalak = []
        eredeti = modul.javaslatokat_ujraszamol

        def megfigyelt(*args, **kwargs):
            szalak.append(threading.current_thread())
            return eredeti(*args, **kwargs)

        monkeypatch.setattr(modul, "javaslatokat_ujraszamol", megfigyelt)
        ctl, _tmp_path = vezerlo
        ctl.setSuggestionThreshold(75)

        _frissit_es_var(ctl, qt_app)

        assert len(szalak) == 1
        assert szalak[0] is not threading.main_thread()

    def test_a_felulet_szamara_slotkent_elerheto(self):
        meta = FaceScanController.staticMetaObject
        nevek = {
            bytes(meta.method(i).name()).decode("utf-8")
            for i in range(meta.methodCount())
        }
        assert "refreshSuggestions" in nevek


class _KovetoFaceScanController(FakeFaceScanController):
    """A hamis vezérlő, amely a frissítés hívását is a beállítások sorába írja."""

    def __init__(self):
        super().__init__()
        self.refresh_calls = 0

    @Slot()
    def refreshSuggestions(self):  # noqa: N802 -- QML-slot-stílus
        self.refresh_calls += 1
        self.setting_calls.append(("refreshSuggestions", self.suggestion_threshold))


@pytest.fixture
def fake_face_scan_controller():
    return _KovetoFaceScanController()


@pytest.fixture
def window(request):
    """A betöltött Beállítások ablak; a `dialog` fixture-t név szerint kéri."""
    window, *_ = request.getfixturevalue("dialog")
    return window


def _nevcimke_ful(window, qt_app):
    from PySide6.QtQml import QQmlEngine

    window.setProperty("visible", True)
    assert _var(qt_app, lambda: window.isExposed()), "a Beállítások ablak nem jelent meg"
    _child(window, "optionsTabBar").setProperty("currentIndex", _NEVCIMKE_FUL)
    assert _var(
        qt_app, lambda: _child(window, "optionsFaceSuggestionsCheck").isVisible()
    ), "a Névcímkék fül nem jelent meg"
    vezerlo = QQmlEngine.contextForObject(window).contextProperty(
        "faceScanController"
    )
    return (
        vezerlo,
        _child(window, "optionsFaceSuggestionThresholdSlider"),
        _child(window, "optionsFaceClusterThresholdSlider"),
    )


class TestAzOkGomb:
    def test_a_javaslatkuszob_valtozasa_az_ok_utan_frissit(self, window, qt_app):
        vezerlo, javaslat_csuszka, _csoport_csuszka = _nevcimke_ful(window, qt_app)

        _csuszkara_kattint(window, qt_app, javaslat_csuszka, 70)
        assert vezerlo.refresh_calls == 0, "OK előtt nem frissíthet"
        _elfogad(window, qt_app)

        assert vezerlo.suggestion_threshold == 70
        assert vezerlo.refresh_calls == 1
        assert vezerlo.setting_calls.index(("suggestionThreshold", 70)) < (
            vezerlo.setting_calls.index(("refreshSuggestions", 70))
        ), "a frissítés az ÚJ küszöb mentése után fut"

    def test_valtozatlan_kuszobnel_az_ok_nem_szamol_ujra(self, window, qt_app):
        vezerlo, javaslat_csuszka, _csoport_csuszka = _nevcimke_ful(window, qt_app)

        # A csúszka érintve van, de az érték visszaáll az eredetire.
        _csuszkara_kattint(window, qt_app, javaslat_csuszka, 90)
        _csuszkara_kattint(window, qt_app, javaslat_csuszka, 85)
        _elfogad(window, qt_app)

        assert vezerlo.suggestion_threshold == 85
        assert vezerlo.refresh_calls == 0

    def test_ok_a_beallitasok_erintese_nelkul_nem_szamol_ujra(
        self, window, qt_app
    ):
        vezerlo, _javaslat_csuszka, _csoport_csuszka = _nevcimke_ful(window, qt_app)

        _elfogad(window, qt_app)

        assert vezerlo.refresh_calls == 0

    def test_a_csoportkuszob_onmagaban_nem_indit_ujraszamolast(
        self, window, qt_app
    ):
        vezerlo, _javaslat_csuszka, csoport_csuszka = _nevcimke_ful(window, qt_app)

        _csuszkara_kattint(window, qt_app, csoport_csuszka, 75)
        _elfogad(window, qt_app)

        assert vezerlo.cluster_threshold == 75
        assert vezerlo.refresh_calls == 0

