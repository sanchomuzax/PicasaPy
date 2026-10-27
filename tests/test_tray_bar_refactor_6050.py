"""A képtálca QML-komponensekre bontásának szerkezeti őrei (#6050)."""

from __future__ import annotations

from pathlib import Path


_QML = (
    Path(__file__).resolve().parents[1]
    / "src/picasapy/app/qml/PicasaPy"
)
_COMPONENTS = (
    "TrayInfoBar.qml",
    "TrayScratchPanel.qml",
    "TrayRightPane.qml",
    "TrayTopRow.qml",
    "TrayActionArea.qml",
    "TraySingleActionBar.qml",
)


def _sorok(fajlnev: str) -> int:
    return len((_QML / fajlnev).read_text(encoding="utf-8").splitlines())


def test_a_talca_vizualis_reszei_onallo_qml_fajlokban_vannak():
    hianyzo = [nev for nev in _COMPONENTS if not (_QML / nev).is_file()]
    assert not hianyzo, f"hiányzó képtálca-komponensek: {hianyzo}"

    for fajlnev, instantiation in (
        ("TrayBar.qml", "TrayInfoBar {"),
        ("TrayBar.qml", "TrayScratchPanel {"),
        ("TrayBar.qml", "TrayRightPane {"),
        ("TrayBar.qml", "TraySingleActionBar {"),
        ("TrayRightPane.qml", "TrayTopRow {"),
        ("TrayRightPane.qml", "TrayActionArea {"),
    ):
        assert instantiation in (_QML / fajlnev).read_text(encoding="utf-8"), (
            f"{fajlnev} nem használja a {instantiation.strip()} komponenst"
        )


def test_a_talca_uj_komponensei_a_qmldirben_vannak():
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    hianyzo = [nev.removesuffix(".qml") for nev in _COMPONENTS if nev.removesuffix(".qml") not in qmldir]
    assert not hianyzo, f"a qmldir nem regisztrálja ezeket: {hianyzo}"


def test_a_talca_minden_qml_resze_800_sor_alatt_marad():
    fajlok = ("TrayBar.qml", *_COMPONENTS)
    meretek = {nev: _sorok(nev) for nev in fajlok if (_QML / nev).is_file()}
    tulhosszu = {nev: sor for nev, sor in meretek.items() if sor >= 800}
    assert not tulhosszu, f"a 800 soros határ túllépve: {tulhosszu}"

