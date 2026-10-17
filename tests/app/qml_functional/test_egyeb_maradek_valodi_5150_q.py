"""Az „Egyéb" csoport maradék vezérlői VALÓDI bemenettel (#5150, Egyéb, Q. fájl).

Lefedve:
- Mappafa (fa-nézet): a sor kattintása kiválasztja a mappát, a nyíl kattintása
  kinyitja az ágat. Mindkét vezérlő objectName-je a mappa útját viseli
  (`folderTreeRowMouse:<út>`, `hierArrowMouse:<út>`), ezért előtagra keresünk.

Nincs rajta teszt, mert még nem kivizsgált (jegyben nyitva kell hagyni):
- `hierMentesCheck:<út>` (fa, mentés-mód): a sor kattintása sem a pipa közepén,
  sem a sor szövegén nem jelöli meg a mappát, pedig a lapos mappalistában
  ugyanez a logika működik.

A fa-nézetet a Nézet ▸ Mappanézet ▸ Fa-nézet tétellel kapcsoljuk be, valódi
menükattintással. Külső programot nem indítunk, nincs helyettesítő.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MASIK,
    app_epitese,
    keszits_konyvtarat,
    nyitott,
)
from tests.app.qml_functional._menusor_maradek_5150_helpers import tetel_kattintasa as menusor_tetel
from tests.app.qml_functional._nezet_menu_5150_helpers import tetel_kattintasa
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints, varj
from tests.app.qml_functional._racs_maradek_5150_helpers import (
    _ablak_elemei,
    kattint,
    keres,
    utvonal,
)

ALMAPPA = "gyerek"


def _keszits_fat(lib: Path) -> None:
    """A `fotok` mappa (három kép), mellette a `masik` mappa egy almappával.

    A `masik`-nak gyermeke van, így a fa-nézetben nyíl jelzi, hogy nyitható."""
    keszits_konyvtarat(lib)
    masik = lib / MASIK
    (masik / ALMAPPA).mkdir(parents=True)
    make_jpeg(masik / "d_nagy.jpg", size=(160, 120))
    make_jpeg(masik / ALMAPPA / "e_kicsi.jpg", size=(40, 30))


@pytest.fixture
def fa_app(qt_app, tmp_path, monkeypatch):
    """A rendszermappák (Képek, Iratok, Asztal) a teszt saját mappái: a futtató gép
    mappáitól a fa nem függhet (ld. a test_nezet_menu_valodi_5150_b.py mintáját)."""
    from picasapy.app import folder_hierarchy_controller as fhc
    from picasapy.app import folder_tree_controller as ftc

    utak = {}
    for token, nev in (("mypics", "Kepek"), ("mydocs", "Iratok"), ("desktop", "Asztal")):
        mappa = tmp_path / "rendszer" / nev
        mappa.mkdir(parents=True)
        utak[token] = str(mappa)
    monkeypatch.setattr(fhc, "_rendszermappa", lambda token: utak.get(token, ""))
    # a Mappakezelő gyökerei a futtató gép mappái helyett a teszt Képek mappája
    monkeypatch.setattr(
        ftc,
        "_root_entries",
        lambda *_args, **_kwargs: [
            {"name": "Képek", "path": utak["mypics"], "hasChildren": False}
        ],
    )
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_keszits_fat)


def _utas_elem(window, elotag: str, ut: Path):
    """A látható `elotag:<út>` nevű elem, ahol az út Path-ként egyezik.

    Windowson a modell útja és a `watchedFolders` szövege eltérhet
    (elválasztó, kis-nagybetű), ezért nem a teljes objectName-et vetjük össze."""
    for elem in _ablak_elemei(window):
        nev = elem.objectName()
        if nev.startswith(elotag) and elem.isVisible() and Path(nev[len(elotag):]) == ut:
            return elem
    return None


def _utas_kattintas(window, qt_app, elotag: str, ut: Path) -> None:
    elem = _utas_elem(window, elotag, ut)
    assert elem is not None, f"nincs látható {elotag}{ut} elem"
    kattints(window, qt_app, elem)


def _masik_utja(controller) -> Path:
    return Path(str(controller.watchedFolders[0])) / MASIK


def _fa_nezet_bekapcsolasa(window, qt_app, controller) -> tuple[Path, Path]:
    """Nézet ▸ Mappanézet ▸ Fa-nézet (valódi menükattintással), majd a watched
    gyökér kinyitása a nyíllal. Visszaadja a gyökér és a `masik` útját."""
    kepek = Path(str(controller.watchedFolders[0]))
    masik = kepek / MASIK
    tetel_kattintasa(window, qt_app, "menuViewTreeView", almenu_utvonal=("menuViewFolderView",))
    assert varj(qt_app, lambda: _utas_elem(window, "hierRow:", kepek) is not None), (
        "a fa-nézetben nem látszik a gyökér sora"
    )
    _utas_kattintas(window, qt_app, "hierArrowMouse:", kepek)
    assert varj(qt_app, lambda: _utas_elem(window, "hierRow:", masik) is not None), (
        "a gyökér nyílja nem nyitotta ki a masik mappát"
    )
    return kepek, masik


class TestMappafa:
    def test_a_mappakezelo_sora_valodi_kattintasra_kijeloli_a_mappat(
        self, fa_app, qt_app, tmp_path
    ):
        """Fájl ▸ Add Folder to Picasa...: a Mappakezelő fájában a sor kijelöli a mappát."""
        window, _controller, _engine = fa_app
        window.show()
        window.requestActivate()
        kepek = Path(tmp_path) / "rendszer" / "Kepek"
        menusor_tetel(window, qt_app, "&File", "menuFileAddFolder")
        kezelo = keres(window, "folderManagerDialog")
        assert varj(qt_app, lambda: nyitott(kezelo)), "a Mappakezelő nem nyílt meg"

        kattint(window, qt_app, "folderTreeRowMouse:" + str(kepek))

        assert varj(qt_app, lambda: utvonal(kezelo.property("selectedPath")) == kepek), (
            f"a fa sorának kattintása nem a Képek mappát jelölte ki: {kezelo.property('selectedPath')}"
        )

    def test_a_nyil_valodi_kattintasra_kinyitja_az_agat(self, fa_app, qt_app):
        window, controller, _engine = fa_app
        window.show()
        window.requestActivate()
        _kepek, masik = _fa_nezet_bekapcsolasa(window, qt_app, controller)
        gyerek = masik / ALMAPPA
        assert _utas_elem(window, "hierRow:", gyerek) is None, (
            "az almappa már nyitva volt a nyíl előtt"
        )

        _utas_kattintas(window, qt_app, "hierArrowMouse:", masik)

        assert varj(qt_app, lambda: _utas_elem(window, "hierRow:", gyerek) is not None), (
            "a nyíl kattintása nem nyitotta ki a masik ágát"
        )

