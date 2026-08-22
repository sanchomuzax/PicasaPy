"""„Eltávolítás a Picasából" — almappára is, sírkővel (#1249).

A jegy gépi mérése (2026-08-22): a helyi menü `removeWatchedFolder`-t
hívott, ami almappán némán semmit nem csinált; és még a helyes metódussal
is visszajött a mappa a `rescan()` után, mert nem volt sírkő. Az eredeti
levezetése: `docs/specs/picasa-mappakezelo.md` 15. (`0x005ce590`,
`]album:removed` — `0x004b9200`).
"""


from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _varj(vezerlo, qt_app):
    for _ in range(200):
        qt_app.processEvents()
        if vezerlo.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _vezerlo(tmp_path, qt_app):
    gyoker = tmp_path / "gyoker"
    (gyoker / "alma").mkdir(parents=True)
    make_jpeg(gyoker / "alma" / "a.jpg", size=(32, 24))
    make_jpeg(gyoker / "b.jpg", size=(32, 24))
    db = tmp_path / "i.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    vezerlo = AppController(
        db,
        (str(gyoker),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
        settings=beallitas,
    )
    # a bal panel modellje az első beolvasás után töltődik
    vezerlo.rescan()
    _varj(vezerlo, qt_app)
    return vezerlo, gyoker


def _panel_mappai(vezerlo):
    return tuple(vezerlo.folders.folder_paths())


class TestAlmappa:
    def test_almappan_is_eltunteti(self, tmp_path, qt_app):
        """⚠️ A jelentett tünet: almappára SEMMI nem történt."""
        vezerlo, gyoker = _vezerlo(tmp_path, qt_app)
        alma = str(gyoker / "alma")
        assert alma in _panel_mappai(vezerlo)

        vezerlo.removeFolder(alma)
        _varj(vezerlo, qt_app)

        assert alma not in _panel_mappai(vezerlo), (
            "az almappa a bal panel modelljében maradt"
        )

    def test_rescan_utan_sem_jon_vissza(self, tmp_path, qt_app):
        """⚠️ A sírkő-teszt: a jegy mérésében ez a lépés bukott."""
        vezerlo, gyoker = _vezerlo(tmp_path, qt_app)
        alma = str(gyoker / "alma")
        vezerlo.removeFolder(alma)
        _varj(vezerlo, qt_app)

        vezerlo.rescan()
        _varj(vezerlo, qt_app)

        assert alma not in _panel_mappai(vezerlo), (
            "az eltávolított almappa visszajött a rescan után"
        )

    def test_figyelt_gyokerre_a_regi_ut(self, tmp_path, qt_app):
        """Regresszió-őr: gyökéren a teljes meglévő logika fut."""
        vezerlo, gyoker = _vezerlo(tmp_path, qt_app)

        vezerlo.removeFolder(str(gyoker))
        _varj(vezerlo, qt_app)

        assert vezerlo.watchedFolders == []

    def test_ujra_felveve_visszajon(self, tmp_path, qt_app):
        """A sírkő nem örök: a Mappakezelő újra-hozzáadása feloldja."""
        vezerlo, gyoker = _vezerlo(tmp_path, qt_app)
        alma = str(gyoker / "alma")
        vezerlo.removeFolder(alma)
        _varj(vezerlo, qt_app)

        vezerlo.addWatchedFolder(alma)
        _varj(vezerlo, qt_app)

        assert alma in _panel_mappai(vezerlo), (
            "az újra felvett mappa nem jött vissza"
        )
