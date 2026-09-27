"""#3776: a mentés a gyökereket a szkennerrel AZONOS módon oldja fel.

A `BackupController._jeloltek` korábban `Path(gyoker).rglob`-bal járta be a
figyelt gyökereket, feloldás NÉLKÜL — a szkenner (`scanner/walker.py`)
viszont `normalize_path`-dal ír az indexbe. Symlinkes, Windows 8.3-rövidnevű
vagy eltérő betűzésű gyökérnél ez két ELTÉRŐ kulcsot adott ugyanarra a
mappára: a mentetlen mappák lapos listája (`FolderPane.mentesTerkep`,
`FolderListModel.rowOfPath`) pontos egyezéssel keresett, tehát a mappa
szűrve sem jelent meg.

Ezt a fájlt a `run_tests.py`-n át, közös `--basetemp`-pel futtasd.
"""

from __future__ import annotations

import sys

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.backup_sets import keszlet_letrehozasa
from picasapy.paths import normalize_path

from support.jpeg_factory import make_jpeg


@pytest.fixture
def szimlinkes_konyvtar(tmp_path):
    """Valódi mappa egy képpel, és egy rá mutató szimbolikus link."""
    valodi = tmp_path / "valodi" / "kepek"
    valodi.mkdir(parents=True)
    make_jpeg(valodi / "IMG_0001.jpg")
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "valodi", target_is_directory=True)
    return link, valodi


@pytest.mark.skipif(
    sys.platform == "win32", reason="szimbolikus link létrehozása csak POSIX-on"
)
class TestSzimlinkesGyoker:
    def test_a_jeloltek_a_feloldott_gyoker_alatt_vannak(
        self, szimlinkes_konyvtar
    ):
        """A `_jeloltek` a szimlinken át is a VALÓDI (feloldott) útvonalat
        adja — enélkül a mappa kulcsa eltérne az indexétől."""
        from picasapy.app.backup_controller import BackupController

        link, valodi = szimlinkes_konyvtar
        ctl = BackupController(
            db_path=link / "nincs.db", gyokerek=(str(link / "kepek"),)
        )

        jeloltek = ctl._jeloltek()

        assert jeloltek, "a szimlinkes gyökér alatt nem talált fájlt"
        vart_szulo = normalize_path(str(link / "kepek"))
        assert vart_szulo == str(valodi)
        for fajl in jeloltek:
            assert str(fajl.parent) == vart_szulo, (
                f"{fajl} nem a feloldott gyökér alatt van"
            )

    def test_a_mentetlen_mappa_kulcsa_egyezik_az_index_mappajaval(
        self, tmp_path, szimlinkes_konyvtar, qt_app
    ):
        """Végponttól végpontig: a szkenner a szimlinken át szinkronizál, a
        mentés-vezérlő ugyanazon a szimlinken át keresi a jelölteket — a két
        oldal kulcsának EGYEZNIE kell, különben a lapos lista (#3776) nem
        találja meg a mappát."""
        from picasapy.app.backup_controller import BackupController
        from picasapy.app.models import FolderListModel

        link, _valodi = szimlinkes_konyvtar
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, link)
            keszlet_id = keszlet_letrehozasa(conn, "Teszt", str(tmp_path / "mentes")).id
            conn.commit()

        model = FolderListModel()
        with open_index(db) as conn:
            model.load(conn)
        indexelt_utak = list(model.folder_paths())
        assert indexelt_utak, "a szinkron nem talált mappát"

        ctl = BackupController(db_path=db, gyokerek=(str(link),))
        sorok = ctl._mentetlen_sorok(keszlet_id)

        assert sorok, "a mentetlen mappák listája üres"
        mentetlen_utak = {sor["mappa"] for sor in sorok}
        assert mentetlen_utak == set(indexelt_utak), (
            "a mentetlen mappa kulcsa eltér az index kulcsától — a lapos "
            "lista pontos egyezéssel nem találná meg"
        )
        for ut in mentetlen_utak:
            assert model.rowOfPath(ut) >= 0


class TestLaposListaNormalizaltKulccsal:
    """#3776: a lapos lista is normalizált kulccsal keres — Windows-alakú,
    eltérő betűzésű útvonalon, TISZTA függvényként (fájlrendszer-hozzáférés
    nélkül), ezért `_platform` fogantyúval (#1217) Linuxon is mérhető."""

    def test_rowofpath_windows_alakon_eltero_betuzessel_is_talal(
        self, qt_app, monkeypatch
    ):
        import picasapy.paths as paths_modul
        from picasapy.app.models import FolderListModel
        from picasapy.app.search_results import SearchGroup

        monkeypatch.setattr(paths_modul, "_platform", lambda: "win32")

        model = FolderListModel()
        model.load_matches(
            (SearchGroup("C:\\Kepek\\Nyar", "Nyar", 0, None, ()),)
        )

        assert model.rowOfPath("c:/kepek/nyar") == 0
        assert model.rowOfPath("c:\\kepek\\nyar") == 0

    def test_rowofpath_posix_kis_nagybetu_valodi_kulonbseg(
        self, qt_app, monkeypatch
    ):
        import picasapy.paths as paths_modul
        from picasapy.app.models import FolderListModel
        from picasapy.app.search_results import SearchGroup

        monkeypatch.setattr(paths_modul, "_platform", lambda: "linux")

        model = FolderListModel()
        model.load_matches(
            (SearchGroup("/mnt/Kepek/Nyar", "Nyar", 0, None, ()),)
        )

        assert model.rowOfPath("/mnt/kepek/nyar") == -1
        assert model.rowOfPath("/mnt/Kepek/Nyar") == 0

    def test_mentes_kulcs_szlot_a_flat_key_et_hivja(self, qt_app, monkeypatch):
        """A `BackupController.mentesKulcs` (QML-hívható) ugyanazt a tiszta
        függvényt hívja, mint a `FolderListModel.rowOfPath` — a lapos lista
        (`FolderPane.mentesTerkep`) ezért egyet talál a modell sorával."""
        import picasapy.paths as paths_modul
        from picasapy.app.backup_controller import BackupController

        monkeypatch.setattr(paths_modul, "_platform", lambda: "win32")

        ctl = BackupController(db_path="ignored.db", gyokerek=())

        assert ctl.mentesKulcs("C:\\Kepek\\Nyar") == "c:/kepek/nyar"
        assert ctl.mentesKulcs("C:\\Kepek\\Nyar") == ctl.mentesKulcs("c:/kepek/nyar")
