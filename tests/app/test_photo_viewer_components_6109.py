"""A fotónéző fő QML-fájlja kezelhető méretű komponensekből áll (#6109)."""

from pathlib import Path


GYOKER = Path(__file__).resolve().parents[2]
QML = GYOKER / "src/picasapy/app/qml/PicasaPy"
MAX_QML_COMPONENT_SOR = 800
KULON_JEGYBEN_KEZELT = {"PhotoViewerPhotoArea.qml"}


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


# rontás-kontroll: MAX_QML_COMPONENT_SOR = 799 → 1 failed
