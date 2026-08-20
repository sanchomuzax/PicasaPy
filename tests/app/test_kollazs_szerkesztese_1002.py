"""A kész kollázs újranyitása SZERKESZTÉSRE (#1002).

## A tulajdonos jelentése a v0.8.17-ről

> „…majd ha kész, akkor a »Kollázs szerkesztése« gomb megjelenik balra
> fent. Ez a gomb **mindig megjelenik, ha megnyitom a kollázst**. Jelenleg
> ennek hiányában **nem szerkeszthető a kollázs**."

## Az eredeti vezérlő

`editpanel.tre:1350` — és a **SZERKESZTŐPANELÉ**, nem a kollázs-panelé,
ezért nem találtuk sokáig:

```
editpanel/editcollage: root
m_hidden          ← alapból rejtett, csak kollázsnál látszik
```

Gyerekei: `collage_icon` és `editcollage-label`. Feliratok szó szerint:
`Edit Collage` → **„Kollázs szerkesztése"**, tooltip
`Edit the collage from which this image was created` →
**„A kép alapjául szolgáló kollázs szerkesztése"**.

⚠️ Nem tévesztendő össze a `collagepanel::back_to_collage` =
„Vissza a kollázshoz" gombbal — az MÁSIK vezérlő, a könyvtár lapján.

## A kapcsoló: a `.cxf` pár léte

A gomb nem a létrehozás emlékétől látszik, hanem attól, hogy a megnyitott
kép mellett ott van a projektfájl. Ezért `hasCollageProject(útvonal)`, és
nem egy „most készült kollázst" megjegyző állapot.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.cxf import dumps
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import NOBORDER, PICTUREPILE
from support.jpeg_factory import make_jpeg


class _Photo:
    def __init__(self, folder_path, name):
        self.folder_path = folder_path
        self.name = name
        self.caption = None
        self.width = 400
        self.height = 300


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [_Photo(str(library), n) for n in ("a.jpg", "b.jpg", "c.jpg")]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    peldany = _Host()
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def kesz_kollazs(tmp_path, library):
    """Egy „kész kollázs": JPEG + a mellette álló `.cxf` pár."""
    mappa = tmp_path / "Kollázsok"
    mappa.mkdir()
    kep = mappa / "Nyaralás 2026.jpg"
    make_jpeg(kep, size=(400, 300))

    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, border=NOBORDER, width=1600, height=1200
    )
    csomopontok = [
        CollageNode(
            path=str(library / nev),
            center_x=SHEET_UNITS * (0.3 + 0.2 * i),
            center_y=SHEET_UNITS * 0.4,
            width=280.0, height=337.0, theta=0.1 * i, border=NOBORDER,
        )
        for i, nev in enumerate(("a.jpg", "b.jpg", "c.jpg"))
    ]
    projekt = project_from_nodes(
        csomopontok, beallitas, album_title="Nyaralás 2026"
    )
    (mappa / "Nyaralás 2026.cxf").write_bytes(dumps(projekt))
    return kep


class TestAGombLathatosaga:
    """A `.cxf` pár léte kapcsolja — nem a létrehozás emléke."""

    def test_kollazsra_igaz(self, host, kesz_kollazs):
        assert host.hasCollageProject(str(kesz_kollazs)) is True

    def test_sima_fenykepre_hamis(self, host, library):
        assert host.hasCollageProject(str(library / "a.jpg")) is False

    def test_ures_utvonalra_hamis(self, host):
        assert host.hasCollageProject("") is False

    def test_nem_letezo_utvonalra_hamis(self, host, tmp_path):
        assert host.hasCollageProject(str(tmp_path / "nincs.jpg")) is False


class TestAzUjranyitas:
    """⚠️ A tulajdonos panasza: „nem szerkeszthető a kollázs"."""

    def test_megnyitja_a_kollazs_lapot(self, host, kesz_kollazs):
        host.openCollageProject(str(kesz_kollazs))

        assert host.collageOpen is True

    def test_a_csomopontok_a_projektfajlbol_jonnek(self, host, kesz_kollazs):
        host.openCollageProject(str(kesz_kollazs))

        assert host.collageClipCount == 3

    def test_a_tema_es_a_cim_visszajon(self, host, kesz_kollazs):
        host.openCollageProject(str(kesz_kollazs))

        assert host.collageTheme == PICTUREPILE
        assert host.collageTitle == "Nyaralás 2026"

    def test_a_mentes_a_MEGLEVO_fajlt_celozza(self, host, kesz_kollazs):
        """⚠️ Nem másolatot készítünk: a „Létrehozás" ugyanazt a kollázst
        írja felül, amit a felhasználó megnyitott szerkesztésre."""
        host.openCollageProject(str(kesz_kollazs))

        assert host.collageSavedPath == str(kesz_kollazs)

    def test_a_lap_nem_piszkos_megnyitas_utan(self, host, kesz_kollazs):
        """Megnyitás nem módosítás — a bezárás ne kérdezzen rá."""
        host.openCollageProject(str(kesz_kollazs))

        assert host.collageDirty is False


class TestAHibasBemenet:
    """Egy rossz fájl sem tehet elérhetetlenné semmit."""

    def test_projektfajl_nelkul_nem_tortenik_semmi(self, host, library):
        host.openCollageProject(str(library / "a.jpg"))

        assert host.collageOpen is False

    def test_serult_projektfajlra_JELZUNK(self, host, tmp_path):
        mappa = tmp_path / "Kollázsok2"
        mappa.mkdir()
        kep = mappa / "csonk.jpg"
        make_jpeg(kep, size=(80, 60))
        (mappa / "csonk.cxf").write_bytes(b"<collage")
        kaptunk: list[str] = []
        host.collageFailed.connect(kaptunk.append)

        host.openCollageProject(str(kep))

        assert kaptunk, "a sérült projektfájl NÉMÁN nem hiúsulhat meg"
        assert host.collageOpen is False
