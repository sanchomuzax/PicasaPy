"""#1613 — a „Keresés" HÁROMTÉTELES almenü, nem egy lapos parancs.

Az eredetiben a rács helyi menüjében almenü van (`CThumbUI::locatemenu`),
benne három tétel:

| kulcs | felirat |
|---|---|
| `CThumbUI::locateondiskmenu` | `Fájl a lemezen` (Ctrl+Enter) |
| `CThumbUI::locateorigondiskmenu_win` | `Eredeti a lemezen` |
| `IDS_LOCATE_SOURCE_IMAGE` | `Keresés a Picasában` |

Nálunk egyetlen lapos „Keresés a lemezen" volt; a másik kettő hiányzott
(az egyik néma helyfoglalóként).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject

from picasapy.app.fileops_controller import FileOpsController


@pytest.fixture
def kep_eredetivel(tmp_path: Path) -> Path:
    """Szerkesztett kép, aminek VAN eredetije a `.picasaoriginals`-ban."""
    mappa = tmp_path / "album"
    (mappa / ".picasaoriginals").mkdir(parents=True)
    kep = mappa / "a.jpg"
    kep.write_bytes(b"szerkesztett")
    (mappa / ".picasaoriginals" / "a.jpg").write_bytes(b"eredeti")
    return kep


@pytest.fixture
def kep_eredeti_nelkul(tmp_path: Path) -> Path:
    mappa = tmp_path / "album2"
    mappa.mkdir()
    kep = mappa / "b.jpg"
    kep.write_bytes(b"erintetlen")
    return kep


class TestEredetiALemezen:
    def test_van_e_eredeti_a_lemezen(
        self, kep_eredetivel, kep_eredeti_nelkul, qt_app
    ):
        """A tétel LETILTOTT, ha nincs eredeti — ezt a vezérlő mondja meg."""
        vezerlo = FileOpsController()
        assert vezerlo.hasOriginalOnDisk(str(kep_eredetivel)) is True
        assert vezerlo.hasOriginalOnDisk(str(kep_eredeti_nelkul)) is False
        assert vezerlo.hasOriginalOnDisk("") is False

    def test_az_eredetit_mutatja_meg_nem_a_szerkesztettet(
        self, kep_eredetivel, qt_app, monkeypatch
    ):
        import picasapy.app.fileops_controller as modul

        megnyitott: list[Path] = []
        monkeypatch.setattr(modul, "reveal_in_file_manager", megnyitott.append)

        vezerlo = FileOpsController()
        vezerlo.revealOriginal(str(kep_eredetivel))

        assert len(megnyitott) == 1, "nem nyílt meg semmi"
        assert megnyitott[0].parent.name == ".picasaoriginals", (
            f"a szerkesztett fájlt mutatta meg, nem az eredetit: "
            f"{megnyitott[0]}"
        )

    def test_eredeti_nelkul_uzenetet_kap_nem_nema_bukast(
        self, kep_eredeti_nelkul, qt_app
    ):
        vezerlo = FileOpsController()
        hibak: list[tuple[str, str]] = []
        vezerlo.operationFailed.connect(
            lambda muvelet, uzenet: hibak.append((muvelet, uzenet))
        )
        vezerlo.revealOriginal(str(kep_eredeti_nelkul))
        assert len(hibak) == 1, f"nem jött üzenet: {hibak}"
        assert hibak[0][0] == "locate_original"


class TestAzAlmenuSzerkezete:
    """A menü SZERKEZETE — almenü, benne a három tétel."""

    def test_a_kereses_almenu_harom_tetelt_tartalmaz(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        almenu = window.findChild(QObject, "contextMenuLocateMenu")
        assert almenu is not None, (
            "nincs Keresés almenü a rács helyi menüjében — a három tétel "
            "továbbra is laposan áll (#1613)"
        )
        for nev in (
            "contextMenuLocate",
            "contextMenuLocateOriginal",
            "contextMenuLocateInPicasa",
        ):
            assert almenu.findChild(QObject, nev) is not None, (
                f"{nev} nincs a Keresés almenüben"
            )

    def test_az_eredeti_tetel_mar_nem_helyfoglalo(self, qml_app):
        window, _controller, _lib, _engine = qml_app
        for nev in ("contextMenuLocateOriginal", "contextMenuLocateInPicasa"):
            tetel = window.findChild(QObject, nev)
            assert tetel is not None, f"{nev} nem található"
            assert tetel.property("placeholder") is not True, (
                f"{nev} még mindig néma helyfoglaló (#1613)"
            )
