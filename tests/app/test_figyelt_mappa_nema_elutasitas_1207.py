"""A figyelt mappa hozzáadása NEM utasíthat el némán (#1207).

## A tulajdonos jelentése (v0.8.34, Windows)

> „Valamiért a képen látható mappát nem jegyzi meg »OK« gomb után. Nem
> jelenik meg. Talán mert már vannak ilyen nevű mappák csak más útvonalon?
> Nem értem…"

A „nem értem" a lényeg: **a program nem mondta meg, mi történt.**

## A lelet

`library_controller.addWatchedFolder` két ágon fordul vissza, MINDKETTŐ
szó nélkül:

```python
if not path or self._find_root(path) is not None or not Path(path).is_dir():
    return        # <- NÉMÁN
```

⚠️ A duplikáció-védelem némasága a #507 óta SZÁNDÉKOS — más hívási
helyeken (első indítás, importálás) helyes is. De amikor a felhasználó
KIFEJEZETTEN kért valamit a Mappakezelőben, a néma elutasítás azt a
látszatot kelti, hogy sikerült.

⚠️ Ez a teszt **nem a gyökérokot** javítja (az a tulajdonos gépén dől el),
hanem azt, hogy a hiba LÁTHATÓ legyen. Enélkül a következő kör is
találgatna.
"""

from __future__ import annotations




def _vezerlo(tmp_path, qt_app):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir()
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, konyvtar)
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    return AppController(
        db,
        (str(konyvtar),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
        settings=beallitas,
    )


def test_nemletezo_mappa_elutasitasa_JELZODIK(tmp_path, qt_app):
    """⚠️ Eddig szó nélkül elmaradt — a felhasználó azt hitte, sikerült."""
    vezerlo = _vezerlo(tmp_path, qt_app)
    elutasitasok: list[tuple[str, str]] = []
    vezerlo.watchedFolderRejected.connect(
        lambda ut, ok: elutasitasok.append((ut, ok))
    )

    vezerlo.addWatchedFolder(str(tmp_path / "nincs-ilyen"))

    assert elutasitasok, (
        "a nem létező mappa elutasítása NÉMA volt — a felhasználó nem tudja "
        "meg, miért nem jegyezte meg a program"
    )
    vezerlo.waitForBackgroundWorkers(10.0)


def test_mar_figyelt_mappa_elutasitasa_JELZODIK(tmp_path, qt_app):
    """A duplikátum sem tűnhet el szó nélkül, ha a felhasználó KÉRTE."""
    vezerlo = _vezerlo(tmp_path, qt_app)
    ujmappa = tmp_path / "masik"
    ujmappa.mkdir()
    vezerlo.addWatchedFolder(str(ujmappa))

    elutasitasok: list[tuple[str, str]] = []
    vezerlo.watchedFolderRejected.connect(
        lambda ut, ok: elutasitasok.append((ut, ok))
    )
    vezerlo.addWatchedFolder(str(ujmappa))  # másodszor

    assert elutasitasok, "a már figyelt mappa ismételt hozzáadása néma volt"
    vezerlo.waitForBackgroundWorkers(10.0)


def test_a_SIKERES_hozzaadas_NEM_jelez_elutasitast(tmp_path, qt_app):
    """⚠️ A jelzés ne legyen zaj: sikernél nem szólalhat meg."""
    vezerlo = _vezerlo(tmp_path, qt_app)
    ujmappa = tmp_path / "harmadik"
    ujmappa.mkdir()

    elutasitasok: list[tuple[str, str]] = []
    vezerlo.watchedFolderRejected.connect(
        lambda ut, ok: elutasitasok.append((ut, ok))
    )
    vezerlo.addWatchedFolder(str(ujmappa))

    assert not elutasitasok
    vezerlo.waitForBackgroundWorkers(10.0)
