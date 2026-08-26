"""A befejezés a piszkozat TÉNYLEGES helyéről takarítson, ne a jelenleg
beállított mappából (#1387).

## A hiba

A #1072 véglegesítő lépése (`finishCollageDraft` → `_discard_draft_after_render`)
a `_collage_panel_draft_dir()`-t hívta, ami mindig a **jelenleg beállított**
Kollázsok-mappát adja vissza (`OUTPUT_DIR_KEY`). Ha a felhasználó a piszkozat
mentése UTÁN, a befejezés ELŐTT átállítja a kimeneti mappát, a takarítás a
ROSSZ (új) helyen keresi az `autosave.cxf`-et — a piszkozat tényleges,
RÉGI helyén árván marad.

## A javítás

A vezérlő eltárolja, honnan jött a MOST NYITOTT piszkozat ténylegesen
(`_collage_panel_draft_source_dir`) — a `saveCollageDraft` írás után, illetve
az `openCollageProject`/`finishCollageDraft` a piszkozat `autosave.cxf`-ének
mappájából. A takarítás EZT a mappát használja, a beállítást csak akkor, ha
nincs ilyen (pl. induló, még soha nem mentett piszkozat).

## Az `autosave.jpg` döntése (#1100 mérése alapján)

A valódi Picasa egy kép nélkül talált `autosave.cxf`-re **saját**, szürke
`autosave.jpg` helykitöltőt ír (#1100). Ha a felhasználó gépén ez már
megtörtént a RÉGI mappában, mire mi takarítunk, az a fájl **nem a miénk** —
a #1100 döntése szerint ahhoz nem nyúlunk. A takarítás ezért itt is csak az
`autosave.cxf`-et (és a mi beállítás-kulcsainkat) törli, az `autosave.jpg`-t
érintetlenül hagyja."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.autosave import AUTOSAVE_NAME
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_kollazs_jelzesre


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


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
def regi_mappa(tmp_path):
    return tmp_path / "Kollazsok-regi"


@pytest.fixture
def uj_mappa(tmp_path):
    return tmp_path / "Kollazsok-uj"


@pytest.fixture
def settings(tmp_path, regi_mappa):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue(COLLAGE_OUTPUT_DIR_KEY, str(regi_mappa))
    return beallitasok


@pytest.fixture
def host(qt_app, settings, library, tmp_path):
    from picasapy.app.collage_controller import CollageMixin

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._db_path = tmp_path / "index.db"
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

        def _collage_output_width(self):
            return 240

    példány = _Host()
    yield példány
    assert példány.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def piszkozat_a_regi_mappaban(host, regi_mappa) -> Path:
    """Piszkozat mentve a RÉGI mappába, majd a lap bezárva."""
    host.openCollage([0, 1, 2])
    host.saveCollageDraft()
    host.closeCollage()
    kepek = sorted(regi_mappa.glob("*.jpg"))
    assert len(kepek) == 1, f"a piszkozatnak egy képe van, nem {kepek}"
    assert (regi_mappa / AUTOSAVE_NAME).exists()
    return kepek[0]


def test_mappavaltas_utan_a_befejezes_a_REGI_helyrol_takarit(
    host, piszkozat_a_regi_mappaban, regi_mappa, uj_mappa, settings
):
    """A piszkozat mentése után átállított kimeneti mappa ne tévessze meg a
    takarítást: a RÉGI helyen se maradjon `autosave.cxf`, és az ÚJ mappa
    (ahol sosem volt piszkozat) ne is legyen csak azért létrehozva/érintve."""
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(uj_mappa))

    megjott, _args = varj_kollazs_jelzesre(
        host.collageDone,
        lambda: host.finishCollageDraft(str(piszkozat_a_regi_mappaban)),
    )

    assert megjott, "a befejezés nem futott le"
    assert not (regi_mappa / AUTOSAVE_NAME).exists(), (
        "árva autosave.cxf maradt a RÉGI mappában — a mappaváltás után a "
        "takarítás a rossz (új) helyen kereste"
    )
    assert piszkozat_a_regi_mappaban.with_suffix(".cxf").exists(), (
        "a kész kollázs a RÉGI mappában kellene maradjon (ugyanaz a fájlnév)"
    )
    assert not host.isCollageDraft(str(piszkozat_a_regi_mappaban))


def test_a_Picasa_altal_irt_autosave_jpg_a_REGI_helyen_erintetlen(
    host, piszkozat_a_regi_mappaban, regi_mappa, uj_mappa, settings
):
    """Ha a valódi Picasa már ráírta a szürke `autosave.jpg`-t a régi
    mappában lévő árva piszkozatra (#1100), az NEM a mi fájlunk — a
    takarítás azt se törli, se máshogy nem nyúl hozzá."""
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    idegen = regi_mappa / "autosave.jpg"
    idegen.write_bytes(b"a Picasa irta")
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(uj_mappa))

    megjott, _args = varj_kollazs_jelzesre(
        host.collageDone,
        lambda: host.finishCollageDraft(str(piszkozat_a_regi_mappaban)),
    )

    assert megjott, "a befejezés nem futott le"
    assert idegen.read_bytes() == b"a Picasa irta"
