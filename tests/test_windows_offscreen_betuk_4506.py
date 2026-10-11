"""#4506: a windowsos offscreen tesztkörnyezet lássa a rendszerbetűket.

A windowsos `qoffscreen.dll` (PySide6 6.11.2) betű-adatbázisa a
`QFreeTypeFontDatabase` — a DLL importjai közt ennek a konstruktora áll, a
`QWindowsFontDatabase`-é nem. Ez az adatbázis kizárólag a `fontDir()`
mappát olvassa (`QT_QPA_FONTDIR`, ennek híján `<Qt-lib>/fonts`), a
PySide6-kerékben pedig nincs `fonts` mappa: a CI-n így EGYETLEN rendszerbetű
sem látszott. A szöveg-effekt ilyenkor betűkép nélkül rajzolt, a félkövér és
a dőlt ugyanazt a képet adta (3645 == 3645), és a betűlistában csak a
próbák saját „Open Sanz" másolata állt.

A valódi alkalmazás Windowson a `windows` platformmal fut, annak saját
(rendszer-)betűadatbázisa van — a hiba a tesztkörnyezeté.

A próbák a platformot és a környezetet PARAMÉTERKÉNT kapják, így Linuxon is
a windowsos ágat mérik.
"""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

from support.qt_betukonyvtar import qt_betukonyvtar_kiegeszites

_GYOKER = Path(__file__).resolve().parent


def _mindig_letezik(_ut: str) -> bool:
    return True


def test_windowson_a_rendszer_betumappaja_lesz_a_qt_betukonyvtara():
    kiegeszites = qt_betukonyvtar_kiegeszites(
        {"WINDIR": r"C:\Windows"}, "win32", letezik=_mindig_letezik
    )
    assert kiegeszites == {"QT_QPA_FONTDIR": str(PureWindowsPath(r"C:\Windows") / "Fonts")}


def test_windir_hijan_a_systemroot_dont():
    kiegeszites = qt_betukonyvtar_kiegeszites(
        {"SystemRoot": r"D:\Win"}, "win32", letezik=_mindig_letezik
    )
    assert kiegeszites == {"QT_QPA_FONTDIR": str(PureWindowsPath(r"D:\Win") / "Fonts")}


def test_a_kezzel_megadott_betukonyvtar_erintetlen_marad():
    kiegeszites = qt_betukonyvtar_kiegeszites(
        {"WINDIR": r"C:\Windows", "QT_QPA_FONTDIR": r"E:\sajat"},
        "win32",
        letezik=_mindig_letezik,
    )
    assert kiegeszites == {}


def test_nem_letezo_betumappat_nem_allit_be():
    kiegeszites = qt_betukonyvtar_kiegeszites(
        {"WINDIR": r"C:\Windows"}, "win32", letezik=lambda _ut: False
    )
    assert kiegeszites == {}


def test_linuxon_nem_nyul_semmihez():
    # Linuxon a fontconfig-adatbázis dolgozik, a QT_QPA_FONTDIR-t nem nézi
    kiegeszites = qt_betukonyvtar_kiegeszites(
        {"WINDIR": r"C:\Windows"}, "linux", letezik=_mindig_letezik
    )
    assert kiegeszites == {}


def test_a_bemeno_kornyezet_nem_valtozik():
    kornyezet = {"WINDIR": r"C:\Windows"}
    qt_betukonyvtar_kiegeszites(kornyezet, "win32", letezik=_mindig_letezik)
    assert kornyezet == {"WINDIR": r"C:\Windows"}


def test_a_gyoker_conftest_alkalmazza_az_elso_qt_alkalmazas_elott():
    """A beállítás csak a `QGuiApplication` létrejötte ELŐTT hat (a Qt az
    adatbázist egyszer tölti fel), ezért a gyökér-`conftest` modulszinten,
    importkor alkalmazza — nem fixture-ben."""
    forras = (_GYOKER / "conftest.py").read_text(encoding="utf-8")
    assert "qt_betukonyvtar_kiegeszites(os.environ, sys.platform)" in forras
