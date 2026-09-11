"""#2998: a címke-panel ELŐRE szól, ha a kijelölésben írásvédett elem van.

Az eredeti `keywords.tre` külön feliratot tart erre:
`keywords/readonly_label` → „Tags cannot be modified because one or more
items are read-only." A szöveg „one or more"-t mond, tehát **egyetlen**
írásvédett elem is elég a jelzéshez.

Nálunk eddig csak UTÓLAG derült ki: a #2506 óta az írás bukása hibasávot
kér, de a felhasználó addigra már beírta és elküldte a címkét.

## Miért nem `chmod` a próba

Windowson a `chmod` csak az írásvédett bitet állítja, mappára hatástalan
(#1560) — egy `chmod`-ra épülő teszt a windows-lábon némán zölden állna.
Ezért a vezérlő az `is_folder_writable` valódi próbafájlját használja, a
teszt pedig a MODULSZINTŰ fogantyút cseréli ki (a `fileops/trash.py`
`_access`-mintája szerint).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app import keywords_controller
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir(parents=True)
    make_jpeg(root / "a.jpg")
    make_jpeg(root / "b.jpg")
    return root


@pytest.fixture
def masik_mappa(tmp_path):
    masik = tmp_path / "zart"
    masik.mkdir()
    make_jpeg(masik / "c.jpg")
    return masik


@pytest.fixture
def controller(qt_app, tmp_path, library, masik_mappa):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        sync_tree(conn, masik_mappa)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    ctl = AppController(
        tmp_path / "index.db",
        (str(library), str(masik_mappa)),
        provider,
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )
    ctl._reload()
    return ctl


@pytest.fixture
def zarva(monkeypatch, masik_mappa):
    """A `zart` mappa írhatatlan — a valódi próbafájl helyett a fogantyú."""

    def irhato(mappa: Path) -> bool:
        return Path(mappa) != masik_mappa

    monkeypatch.setattr(keywords_controller, "_irhato_e", irhato)
    return masik_mappa


def _sorok(controller, mappa: Path) -> list[int]:
    return [
        i
        for i, foto in enumerate(controller.photos.photos)
        if Path(foto.folder_path) == mappa
    ]


class TestAJelzes:
    def test_irhato_kijelolesre_NINCS_jelzes(self, controller, library, zarva):
        sorok = _sorok(controller, library)
        assert sorok, "a könyvtár fotói nincsenek az indexben"
        assert controller.selectionReadOnly(sorok) is False

    def test_irasvedett_kijelolesre_VAN_jelzes(self, controller, zarva):
        sorok = _sorok(controller, zarva)
        assert sorok
        assert controller.selectionReadOnly(sorok) is True

    def test_EGYETLEN_irasvedett_elem_is_eleg(self, controller, library, zarva):
        """Az eredeti szövege „one or more items" — vegyes kijelölésnél is
        szól."""
        vegyes = _sorok(controller, library) + _sorok(controller, zarva)
        assert controller.selectionReadOnly(vegyes) is True

    def test_URES_kijelolesre_nincs_jelzes(self, controller, zarva):
        assert controller.selectionReadOnly([]) is False

    def test_ERVENYTELEN_sorszam_nem_dont_le_semmit(self, controller, zarva):
        assert controller.selectionReadOnly([999, -1]) is False

    def test_a_mappankent_EGYSZER_kerdez(self, controller, library, zarva, monkeypatch):
        """Két fotó ugyanabban a mappában egyetlen írhatóság-próbát ér — a
        próbafájl írása lemezművelet, kijelölésenként nem szaporítható."""
        hivasok: list[Path] = []

        def szamlalo(mappa: Path) -> bool:
            hivasok.append(Path(mappa))
            return True

        monkeypatch.setattr(keywords_controller, "_irhato_e", szamlalo)
        controller.uritsd_az_irhatosag_gyorstarat()
        sorok = _sorok(controller, library)
        assert len(sorok) >= 2, "a próbához két fotó kell egy mappában"
        controller.selectionReadOnly(sorok)
        assert hivasok == [library], f"mappánként több próba futott: {hivasok}"
