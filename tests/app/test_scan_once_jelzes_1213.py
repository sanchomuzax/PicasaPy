"""A „Keresés egyszer" se utasítson el némán (#1213).

## A lelet

A `scanFolderOnce` ugyanazt a néma őr-sort használta, amit a #1207-ben az
`addWatchedFolder`-ből kivettünk:

```python
if not path or self._find_root(path) is not None or not Path(path).is_dir():
    return        # <- NÉMÁN
```

## Mit tesz az eredeti — megnézve

A Mappakezelő párbeszéd kezelője (`0x007c27d0`) **egyetlen** üzenetet
ismer: `CFolderMgrDialog::warning` — „Watching an entire drive can slow
down the system…". A „Keresés egyszer" ott nem azonnali művelet, hanem a
mappa ÁLLAPOTA (`foldermgr/scan_once` rádió), amit az OK érvényesít;
elutasítás-üzenet tehát nincs hozzá.

Ebből következik a mi szabályunk:

| ág | mi ez | jelezünk? |
|---|---|---|
| üres útvonal | hívási hiba | **igen** (`ures-utvonal`) |
| már figyelt gyökér | **értelmes** no-op: a folyamatos figyelés lefedi | **nem** — az eredetiben a két rádió kizárja egymást |
| nem mappa (eltűnt/elérhetetlen) | a felhasználó kérése ELMARAD | **igen** (`nem-mappa`) |

A #1207 jelzését használjuk újra (`watchedFolderRejected`), mert a
Mappakezelő már megjeleníti — új csatorna csak zajt adna.
"""

from pathlib import Path


def _vezerlo(tmp_path, qt_app):
    """A #1207 tesztjének mintája — saját, elszigetelt vezérlő."""
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir(exist_ok=True)
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, konyvtar)
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    vezerlo = AppController(
        db,
        (str(konyvtar),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
        settings=beallitas,
    )
    return vezerlo, konyvtar


def _jelzesek(controller):
    lista = []
    controller.watchedFolderRejected.connect(
        lambda utvonal, ok: lista.append((utvonal, ok))
    )
    return lista


class TestScanFolderOnce:
    def test_nem_letezo_mappa_jelzest_ad(self, tmp_path, qt_app):
        """⚠️ A jegy magja: eddig némán elmaradt a kérés."""
        controller, _lib = _vezerlo(tmp_path, qt_app)
        jelzesek = _jelzesek(controller)

        controller.scanFolderOnce(str(tmp_path / "nincs-ilyen"))

        assert jelzesek, "eltűnt mappánál semmilyen jelzés nem ment ki"
        assert jelzesek[0][1] == "nem-mappa"

    def test_ures_utvonal_jelzest_ad(self, tmp_path, qt_app):
        controller, _lib = _vezerlo(tmp_path, qt_app)
        jelzesek = _jelzesek(controller)

        controller.scanFolderOnce("")

        assert jelzesek and jelzesek[0][1] == "ures-utvonal"

    def test_mar_figyelt_gyoker_NEM_ad_jelzest(self, tmp_path, qt_app):
        """Az eredetiben a „Keresés egyszer" és a „Keresés mindig" két
        egymást kizáró rádió — a már figyelt mappánál a kérés nem
        marad el, hanem értelmét veszti. Zajt nem adunk."""
        controller, konyvtar = _vezerlo(tmp_path, qt_app)
        jelzesek = _jelzesek(controller)

        controller.scanFolderOnce(str(konyvtar))

        assert jelzesek == []

    def test_letezo_mappat_valoban_beolvassa(self, tmp_path, qt_app):
        """Megőrző: a jelzés-ág nem ronthatja el a valódi működést."""
        from support.jpeg_factory import make_jpeg

        controller, _lib = _vezerlo(tmp_path, qt_app)

        mappa = tmp_path / "kulso"
        mappa.mkdir()
        make_jpeg(mappa / "x.jpg", size=(32, 24))
        jelzesek = _jelzesek(controller)

        controller.scanFolderOnce(str(mappa))
        for _ in range(200):
            qt_app.processEvents()
            if controller.waitForBackgroundWorkers(0.05):
                break
        qt_app.processEvents()

        assert jelzesek == []
        assert Path(mappa / "x.jpg").exists()
