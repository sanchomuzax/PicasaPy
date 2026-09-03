"""#2215 — borító nélküli mappán a sor a MAPPAIKONT mutassa, ne ürességet.

A hiba: a szolgáltató „nincs borító" esetben **1×1 átlátszó** képet adott
vissza, nem hibát. Ettől a QML `Image.status`-a `Ready` lett, a fasor
`boritoLatszik` feltétele igaz — és a `FolderIcon` elrejtőzött. Bekapcsolt
„Indexképek megjelenítése a könyvtárban" mellett a sor így **teljesen
ikon nélkül** maradt; a felhasználó ezt jelentette.

A `FolderPane.qml` kommentje kifejezetten az ellenkezőjét ígérte:
„Ha nincs borító (kép nélküli mappa), a sor visszaesik a mappaikonra."
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.folder_cover_provider import FolderCoverProvider


@pytest.fixture
def ures_mappa(tmp_path: Path) -> Path:
    mappa = tmp_path / "kep-nelkul"
    mappa.mkdir()
    return mappa


class TestANincsBoritoEsetNemSikeresKep:
    """A „nincs borító" nem lehet megkülönböztethetetlen a sikerestől."""

    def test_kep_nelkuli_mappara_NULL_kep_jon(self, qt_app, ures_mappa):
        szolgaltato = FolderCoverProvider(lambda _m: [])
        kep = szolgaltato.requestImage(str(ures_mappa), None, None)
        assert kep.isNull(), (
            "a szolgáltató nem-null képet adott borító nélküli mappára — "
            "a QML ezt sikeresnek hiszi, és elrejti a mappaikont"
        )

    def test_a_HIBARA_futo_lekerdezo_is_NULL_kepet_ad(self, qt_app, ures_mappa):
        """A kivétel sem szökhet ki, de a válasz akkor sem lehet »sikeres«."""

        def robban(_mappa):
            raise RuntimeError("szándékos teszt-hiba")

        szolgaltato = FolderCoverProvider(robban)
        kep = szolgaltato.requestImage(str(ures_mappa), None, None)
        assert kep.isNull()

    def test_a_NULL_kep_nem_1x1(self, qt_app, ures_mappa):
        """Az 1×1 volt a régi, hazug válasz — ne térhessen vissza."""
        szolgaltato = FolderCoverProvider(lambda _m: [])
        kep = szolgaltato.requestImage(str(ures_mappa), None, None)
        assert (kep.width(), kep.height()) != (1, 1)


class TestAValodiBoritoTovabbraIsMukodik:
    """⚠️ A javítás nem ronthatja el a működő ágat."""

    def test_kepes_mappara_valodi_borito_jon(self, qt_app, tmp_path):
        import numpy as np
        import cv2

        mappa = tmp_path / "kepes"
        mappa.mkdir()
        fajl = mappa / "a.png"
        cv2.imwrite(str(fajl), np.full((40, 60, 3), 128, dtype=np.uint8))

        szolgaltato = FolderCoverProvider(lambda _m: [fajl])
        kep = szolgaltato.requestImage(str(mappa), None, None)
        assert not kep.isNull()
        assert kep.width() > 1 and kep.height() > 1


class TestAGyorstarANULLValasztIsTarolja:
    """Kép nélküli mappára ne fusson újra a lemez-olvasás minden sorrajzoláskor."""

    def test_masodszorra_nem_hivja_ujra_a_lekerdezot(self, qt_app, ures_mappa):
        hivasok = []

        def lekerdezo(mappa):
            hivasok.append(mappa)
            return []

        szolgaltato = FolderCoverProvider(lekerdezo)
        szolgaltato.requestImage(str(ures_mappa), None, None)
        szolgaltato.requestImage(str(ures_mappa), None, None)
        assert len(hivasok) == 1
