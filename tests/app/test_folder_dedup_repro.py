"""#507 bizonyíték: ugyanaz a mappa két, karakterláncként eltérő alakban
kétszer kerülhet a figyelt gyökerek közé és/vagy az indexbe.

Ez a fájl a JAVÍTÁS ELŐTTI állapotot dokumentálja bukó tesztekkel — az egyes
`test_repro_*` esetek célja, hogy megmutassák, MELYIK alak-eltérés vezet
duplikációhoz. A javítás után ugyanezek a tesztek REGRESSZIÓ-ŐRKÉNT maradnak
(most már zöldre)."""

from __future__ import annotations

import sys

import pytest


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    return root


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db"):
        pass
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le a teardownban"


def _add(controller, path_str: str) -> None:
    """`addWatchedFolder` hívása. A `_roots`-listára gyakorolt hatás
    SZINKRON (a háttérszál csak a szinkront futtatja, a lista már a
    metódus visszatérése előtt bővül) — nem kell jelzésre várni ahhoz,
    hogy a duplikáció ellenőrizhető legyen; a háttérszálak leállását a
    `controller` fixture teardownja (`waitForBackgroundWorkers`) várja be."""
    controller.addWatchedFolder(path_str)


class TestFolderDedupRepro:
    def test_repro_trailing_slash(self, controller, library):
        """Ugyanaz a mappa záró perjellel és anélkül."""
        _add(controller, str(library))
        _add(controller, str(library) + "/")
        assert len(controller._roots) == 1, controller._roots

    def test_repro_file_url_vs_plain(self, controller, library):
        """`file://` URL és sima útvonal ugyanarra a mappára."""
        from PySide6.QtCore import QUrl

        _add(controller, str(library))
        _add(controller, QUrl.fromLocalFile(str(library)).toString())
        assert len(controller._roots) == 1, controller._roots

    def test_repro_dotdot_segment(self, controller, library, tmp_path):
        """`..` szegmenst tartalmazó útvonal ugyanarra a mappára mutat."""
        sibling = tmp_path / "kepek2"
        sibling.mkdir()
        dotdot_path = str(tmp_path / "kepek2" / ".." / "kepek")
        _add(controller, str(library))
        _add(controller, dotdot_path)
        assert len(controller._roots) == 1, controller._roots

    @pytest.mark.skipif(sys.platform == "win32", reason="szimbolikus link csak POSIX-on")
    def test_repro_symlink(self, controller, library, tmp_path):
        """Szimbolikus link és a valódi útvonal ugyanarra a mappára."""
        link = tmp_path / "kepek_link"
        link.symlink_to(library, target_is_directory=True)
        _add(controller, str(library))
        _add(controller, str(link))
        assert len(controller._roots) == 1, controller._roots

    def test_repro_nested_watched_roots(self, controller, library):
        """Ugyanaz a mappa két, egymásba ágyazott figyelt gyökéren át."""
        sub = library / "alma"
        sub.mkdir()
        _add(controller, str(library))
        _add(controller, str(sub))
        # a beágyazott gyökér ELFOGADHATÓ (más funkció, nem duplikátum) —
        # ez a teszt csak dokumentálja, hogy ez NEM ugyanaz az eset, mint a
        # fenti string-alak-eltérések; nincs itt szigorú elvárás a
        # duplikáció-számra, csak hogy a két bejegyzés különböző útvonal.
        assert str(library) in controller._roots
        assert str(sub) in controller._roots
