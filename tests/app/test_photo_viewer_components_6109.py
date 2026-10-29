"""A fotónéző fő QML-fájlja kezelhető méretű komponensekből áll (#6109)."""

from pathlib import Path


GYOKER = Path(__file__).resolve().parents[2]
QML = GYOKER / "src/picasapy/app/qml/PicasaPy"
MAX_QML_COMPONENT_SOR = 800
KULON_JEGYBEN_KEZELT = {"PhotoViewerPhotoArea.qml"}
MAX_QML_6234 = 400
FOTONEZO_6234_FAJLOK = (
    "PhotoViewer.qml",
    "PhotoViewerKeyboard.qml",
    "PhotoViewerLayout.qml",
    "PhotoViewerState.qml",
)


def test_a_fotonezo_komponensei_nyolcszaz_sor_alatt_maradnak() -> None:
    """A fotóterület saját jegyének fájlját nem méri ez a szerződés."""
    for fajl in sorted(QML.glob("PhotoViewer*.qml")):
        if fajl.name in KULON_JEGYBEN_KEZELT:
            continue
        sorok = len(fajl.read_text(encoding="utf-8").splitlines())
        assert sorok <= MAX_QML_COMPONENT_SOR, (
            f"{fajl.name}: {sorok} sor; legfeljebb "
            f"{MAX_QML_COMPONENT_SOR} lehet"
        )


def test_6234_a_nezo_bontott_fajljai_400_sor_alatt_es_a_qmldirben_vannak() -> None:
    """A #6234 bontási határát és a QML modulba felvételt őrzi."""
    qmldir = (QML / "qmldir").read_text(encoding="utf-8").splitlines()
    for nev in FOTONEZO_6234_FAJLOK:
        fajl = QML / nev
        assert fajl.is_file(), f"hiányzó fotónéző-komponens: {nev}"
        sorok = len(fajl.read_text(encoding="utf-8").splitlines())
        assert sorok < MAX_QML_6234, (
            f"{nev}: {sorok} sor; a #6234 határa {MAX_QML_6234} alatt van"
        )
        assert any(sor.split()[-1:] == [nev] for sor in qmldir), (
            f"{nev} nincs regisztrálva a qmldir-ben"
        )


# rontás-kontroll: MAX_QML_COMPONENT_SOR = 799 → 1 failed
# rontás-kontroll: MAX_QML_6234 = 1 → 1 failed
