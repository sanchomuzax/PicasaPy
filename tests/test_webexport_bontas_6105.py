"""A webexport QML-bontás szerkezeti elfogadási őrei (#6105)."""

from pathlib import Path


_QML = (
    Path(__file__).parents[1]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
)
_RESZEK = (
    "WebExportTemplatePane",
    "WebExportStatusPane",
    "FtpAccountDialog",
)


def test_minden_webexport_qml_resz_800_sor_alatt_marad():
    fajlok = [_QML / "WebExportDialog.qml"] + [
        _QML / f"{nev}.qml" for nev in _RESZEK
    ]
    hianyzo = [ut.name for ut in fajlok if not ut.is_file()]
    assert not hianyzo, f"a webexport részek hiányoznak: {hianyzo}"

    hosszu = {ut.name: len(ut.read_text(encoding="utf-8").splitlines()) for ut in fajlok}
    hosszu = {nev: sor for nev, sor in hosszu.items() if sor > 800}
    assert not hosszu, f"800 sornál hosszabb webexport QML-rész: {hosszu}"


def test_a_nem_parbeszedablak_reszek_neve_nem_tartalmaz_dialogot():
    nevek = ("WebExportTemplatePane", "WebExportStatusPane")
    assert all("Dialog" not in nev for nev in nevek)


def test_az_uj_reszek_a_picasapy_qml_modulban_regisztralva_vannak():
    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    hianyzo = [
        f"{nev} 1.0 {nev}.qml"
        for nev in _RESZEK
        if f"{nev} 1.0 {nev}.qml" not in qmldir
    ]
    assert not hianyzo, f"a qmldir-ből hiányzó komponensek: {hianyzo}"
