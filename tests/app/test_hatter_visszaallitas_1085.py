"""A visszatöltés a HÁTTERET is visszahozza (#1085).

## A tulajdonos jelentése a v0.8.20-ról

> „…helyreállítja az előbbi fél mentést, **de a háttérképet elfelejti, sima
> színre kapcsolja vissza**."

## A lelet

Az `_apply_cxf_project` — amit a piszkozat-visszatöltés (#1051) és a kész
kollázs újranyitása (#1002) egyaránt használ — visszaállítja a témát, a
tájolást, az árnyékot, a képfeliratot, a címet és a csomópontokat, **a
hátteret viszont nem**: se a módot, se a színt, se a képet.

A `.cxf` mindent tárol hozzá (`<background type="solid" color="…">`, illetve
`type="image"` + `<src>`), tehát nem adathiány, hanem kimaradt lépés.

⚠️ **A képháttér INDEXként él a panelen** (#1009: „a háttérkép a kollázs
SAJÁT képeinek egyike, indexszel hivatkozva"), a `.cxf` viszont
**útvonalat** tárol. A visszaállításnak tehát meg kell keresnie, hányadik
csomópont az — és ha a kép már nincs a kollázsban, nem szabad törött
hivatkozást csinálni.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings
from PySide6.QtGui import QColor

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


def _piszkozatot_ment_es_visszatolt(vezerlo):
    """A tulajdonos útja: piszkozat mentése → újraindítás → visszaállítás."""
    vezerlo.saveCollageDraft()
    vezerlo.setCollageBackgroundMode("solid")
    vezerlo.setCollageBackgroundColor(QColor("#ffffff"))
    vezerlo.restoreCollageDraft()


class TestAKephatter:
    """⚠️ Ez a tulajdonos panasza."""

    def test_a_kep_mod_visszajon(self, host):
        host.openCollage([0, 1, 2])
        host.setCollageBackgroundMode("image")

        _piszkozatot_ment_es_visszatolt(host)

        assert host.collageBackgroundMode == "image"

    def test_a_KONKRET_kep_jon_vissza(self, host):
        """Nem elég a mód: ugyanaz a kép legyen a háttér, mint mentéskor."""
        host.openCollage([0, 1, 2])
        host.setCollageBackgroundMode("image")
        host.setCollageSelection([2])
        host.setBackgroundFromSelection()
        vart = host.collageBackgroundImage

        _piszkozatot_ment_es_visszatolt(host)

        assert host.collageBackgroundImage == vart


class TestASzinhatter:
    def test_a_szin_mod_visszajon(self, host):
        host.openCollage([0, 1, 2])
        host.setCollageBackgroundMode("solid")
        host.setCollageBackgroundColor(QColor("#204060"))

        host.saveCollageDraft()
        host.setCollageBackgroundColor(QColor("#ffffff"))
        host.restoreCollageDraft()

        assert host.collageBackgroundMode == "solid"
        assert host.collageBackgroundColor.name() == "#204060"


class TestAHibasHivatkozas:
    """Törött hivatkozás nem keletkezhet."""

    def test_ismeretlen_hatterkepre_SZIN_modba_esik(self, host, tmp_path):
        """Ha a `.cxf` olyan képre hivatkozik, ami már nincs a kollázsban,
        a háttér essen vissza színre — üres képhátteret mutatni rosszabb."""
        from picasapy.collage.draft import project_from_nodes

        host.openCollage([0, 1, 2])

        beallitas = host._render_settings()
        projekt = project_from_nodes(
            host.collageNodes.nodes, beallitas, background_image="/nincs/ilyen.jpg"
        )
        assert projekt.background.type == "image"

        host._apply_cxf_project(projekt, saved_path="")

        assert host.collageBackgroundMode == "solid"
