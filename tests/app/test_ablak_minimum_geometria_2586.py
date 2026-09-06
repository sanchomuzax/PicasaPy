"""#2586 — a mentett geometria visszaállítása tartsa be az ablak MINIMUMÁT.

## A bejelentés (v0.8.313, Windows, induláskor a konzolon)

    QWindowsWindow::setGeometry: Unable to set geometry 958x1120+961+31 …
    Resulting geometry: 993x1120+961+31 … minimum size: 993x419

A kért kliensméret **958 × 1120**, a bejelentett ablak-minimum **993 × 419**
— a platform felülbírálta, és 993-at adott. A `sanitize_geometry()` a
mentett értéket csak a VIRTUÁLIS ASZTALHOZ igazította; az ablak tényleges
minimumát nem ismerte, egyetlen alsó korlátja a `_MIN_SIZE = 200`
szentinel volt (az „értelmetlen mentés" szűrője, nem méret-politika).

## Miért nem egyszeri eset

A minimum a QML-ből jön, és MÉRT, VÁLTOZÓ érték: `Main.qml`
`minimumWidth: trayBar.requiredWidth` (#1367) és
`minimumHeight: photoViewer.requiredHeight` (#641). Valahányszor a sáv
szélesség-igénye nő (új gomb, más cellaméret — ma éjjel épp a #1504
csökkentette), a korábban mentett geometria elavul, és a következő
induláson újra előjön a figyelmeztetés.

## A sorrend, amiért ez az őr felel

**méret felemelése a minimumra → asztalra vágás → pozíció-korrekció.**
Ha a virtuális asztal keskenyebb, mint a minimum, a **minimum nyer** — a
platform úgyis azt adja; a `min(width, vw)` visszavágná, és pont a
figyelmeztetést hoznánk vissza.
"""

from __future__ import annotations

from picasapy.app.window_geometry import (
    restore_window_geometry,
    sanitize_geometry,
)

#: a bejelentésből: a mentett méret és az ablak minimuma
MENTETT = (961, 31, 958, 1120)
MINIMUM = (993, 419)
ASZTAL = (0, 0, 1920, 1200)


class _Ablak:
    """Duck-typed ablak MINIMUM-mal — a valódi `QQuickWindow` felülete."""

    def __init__(self, min_w: int = 0, min_h: int = 0):
        self._geo = (0, 0, 800, 600)
        self._min = (min_w, min_h)
        self.maximize_calls = 0

    def x(self): return self._geo[0]
    def y(self): return self._geo[1]
    def width(self): return self._geo[2]
    def height(self): return self._geo[3]
    def minimumWidth(self): return self._min[0]
    def minimumHeight(self): return self._min[1]
    def setGeometry(self, x, y, w, h): self._geo = (x, y, w, h)
    def showMaximized(self): self.maximize_calls += 1

    def visibility(self):
        from PySide6.QtGui import QWindow
        return QWindow.Visibility.Windowed


def _ment(settings, geo=MENTETT) -> None:
    x, y, w, h = geo
    settings.setValue("window/x", x)
    settings.setValue("window/y", y)
    settings.setValue("window/width", w)
    settings.setValue("window/height", h)


class TestSanitizeAMinimummal:
    def test_a_minimumnal_kisebb_meret_FELEMELKEDIK(self):
        geo = sanitize_geometry(*MENTETT, ASZTAL, min_size=MINIMUM)
        assert geo is not None
        assert geo[2] == 993, (
            f"a szélesség {geo[2]} maradt — a platform 993-at adna, tehát a "
            "visszaállítás nem a mentett méretre áll"
        )

    def test_a_minimumnal_nagyobb_meret_VALTOZATLAN(self):
        geo = sanitize_geometry(100, 100, 1200, 800, ASZTAL, min_size=MINIMUM)
        assert geo == (100, 100, 1200, 800)

    def test_min_size_nelkul_a_regi_viselkedes(self):
        """A paraméter opcionális — a meglévő hívók változatlanul mennek."""
        assert sanitize_geometry(*MENTETT, ASZTAL) == MENTETT

    def test_SZUK_asztalon_a_MINIMUM_nyer(self):
        """Ha az asztal keskenyebb a minimumnál, a `min(width, vw)` épp a
        figyelmeztetést hozná vissza — a platform úgyis a minimumot adja."""
        szuk = (0, 0, 800, 600)
        geo = sanitize_geometry(0, 0, 700, 500, szuk, min_size=MINIMUM)
        assert geo is not None
        # a SZÉLESSÉG: a 993-as minimum nyer a 800-as asztal fölött
        assert geo[2] == 993, (
            f"a szélesség {geo[2]} — a `min(width, vw)` visszavágta az asztal "
            "800-ára, pedig a platform úgyis a 993-as minimumot adja"
        )
        # a MAGASSÁG: az 500 nagyobb a 419-es minimumnál és belefér a 600-as
        # asztalba, tehát változatlan — a minimum ALSÓ korlát, nem cél
        assert geo[3] == 500

    def test_a_pozicio_korrekcio_a_FELEMELT_merettel_szamol(self):
        """A sorrend számít: a jobb szélre mentett, minimumra emelt ablak
        pozíciója a NAGYOBB mérettel igazodjon, különben kilóg."""
        geo = sanitize_geometry(1900, 100, 300, 500, ASZTAL, min_size=MINIMUM)
        assert geo is not None
        x, _y, w, _h = geo
        assert w == 993
        assert x + w >= 48, "az ablak fogható része lecsúszott az asztalról"
        assert x <= 1920 - 48

    def test_az_ERTELMETLEN_mentes_tovabbra_is_kiesik(self):
        """A `_MIN_SIZE = 200` szentinel MARAD, ami: a hibás adat szűrője,
        nem méret-politika — a minimumra emelés nem írhatja felül."""
        assert sanitize_geometry(0, 0, 10, 10, ASZTAL, min_size=MINIMUM) is None


class TestRestoreAzAblakMinimumaval:
    def test_a_visszaallitas_az_ablak_minimumat_hasznalja(self, settings):
        _ment(settings)
        ablak = _Ablak(*MINIMUM)

        assert restore_window_geometry(ablak, settings, ASZTAL) is True

        assert ablak.width() == 993, (
            f"a visszaállított szélesség {ablak.width()} — az ablak minimuma "
            "993, tehát a platform felülbírálná (ez a #2586 bejelentése)"
        )
        assert ablak.height() == 1120

    def test_minimum_NELKULI_ablakon_valtozatlan(self):
        """Régi/csonk ablakon (minimum 0) a viselkedés a korábbi."""
        from PySide6.QtCore import QSettings
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            s = QSettings(str(Path(td) / "s.ini"), QSettings.Format.IniFormat)
            _ment(s)
            ablak = _Ablak(0, 0)
            restore_window_geometry(ablak, s, ASZTAL)
            assert (ablak.width(), ablak.height()) == (958, 1120)


import pytest  # noqa: E402


@pytest.fixture
def settings(tmp_path):
    from PySide6.QtCore import QSettings

    return QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
