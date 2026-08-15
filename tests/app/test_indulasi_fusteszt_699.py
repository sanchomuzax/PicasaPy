"""#699: a program INDULJON EL — indulási füst-teszt valódi rekordokkal.

A v0.7.53 nem indult el: az indítóképernyő végtelen ciklusban maradt, mert a
`start()` → `restoreSession()` → `selectFolder()` → `_show()` láncon
`AttributeError: 'PhotoRecord' object has no attribute 'path'` szállt el.

**Miért nem fogta meg semmi.** A CI-ben van telepítés-füstteszt (#651), de az
csak a belépési pont IMPORTÁLÁSÁIG megy — a `controller.start()`-ot soha nem
hívja meg. A #644 saját tesztje pedig **csonk rekordot** használt `path`
mezővel: olyan szerződést rögzített, amit a valóságban egyik `PhotoRecord`
sem teljesít. Ez ugyanaz a hibaosztály, mint a #651: *az ellenőrzés nem azt
mérte, ami élesben fut.*

Ez a füst-teszt ezért **valódi indexet, valódi `index.queries.PhotoRecord`
objektumokat és mentett munkamenetet** használ — csonk nélkül.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from picasapy.index.queries import photos_in_folder
from support.jpeg_factory import make_jpeg


@pytest.fixture
def konyvtar(tmp_path):
    """Kétképes könyvtár, indexelve — ahogy egy valódi indulásnál áll."""
    mappa = tmp_path / "kepek"
    mappa.mkdir()
    make_jpeg(mappa / "a.jpg", size=(64, 48))
    make_jpeg(mappa / "b.jpg", size=(64, 48))
    db = tmp_path / "index.sqlite"
    with open_index(db) as conn:
        sync_tree(conn, mappa)
    return mappa, db


def _controller(db, mappa, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # mentett munkamenet: pontosan ezen az úton bukott el az indulás
    settings.setValue("session/lastFolder", str(mappa))
    settings.sync()
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    return AppController(db, (str(mappa),), provider, settings=settings)


class TestIndulas:
    def test_a_start_vegigfut_mentett_munkamenettel(self, konyvtar, tmp_path, qt_app):
        """`controller.start()` kivétel NÉLKÜL fut le.

        A v0.7.53-ban itt szállt el a program; a füst-teszt hiánya miatt
        jutott el a felhasználóig.
        """
        mappa, db = konyvtar
        controller = _controller(db, mappa, tmp_path)
        # FONTOS: a hiba csak NEM ÜRES naplónál üt be — a
        # `_check_external_overwrites` üres naplóval azonnal visszatér.
        # Enélkül ez a teszt a HIBÁS kódon is zölden futna (ez a hiányosság
        # volt az első változatában is).
        controller.recordSavedChain(str(mappa / "a.jpg"), "holga=1;")

        controller.start()
        qt_app.processEvents()

        assert controller.photos.rowCount() > 0, (
            "az indulás után a rácsnak tartalmaznia kell a mentett mappa képeit"
        )


class TestNaploEllenorzesValodiRekorddal:
    """A napló-ellenőrzés a VALÓDI `PhotoRecord`-dal — csonk nélkül."""

    def test_a_valodi_rekordbol_kepzett_utvonal_egyezik_a_naploeval(
        self, konyvtar, tmp_path, qt_app
    ):
        """A napló írás/olvasás kulcsa bájtra azonos ugyanarra a fotóra.

        Ha a két oldal másképp képezné az útvonalat, a `detect_lost_edits`
        némán SOHA nem találna egyezést, és a #644 védelme csendben
        hatástalan maradna — ami rosszabb, mint egy hangos hiba.
        """
        mappa, db = konyvtar
        controller = _controller(db, mappa, tmp_path)
        kep = mappa / "a.jpg"

        # az ÍRÓ oldal: a mentési út a fotó teljes útvonalával naplóz
        controller.recordSavedChain(str(kep), "holga=1;")

        # az OLVASÓ oldal: a valódi rekordokból képzett kulcs
        with open_index(db) as conn:
            rekordok = photos_in_folder(conn, str(mappa))
        assert rekordok, "az indexnek tartalmaznia kell a képeket"

        from picasapy.index.queries import full_path

        naplo = controller._load_journal()          # {útvonal: bejegyzés}
        assert str(kep) in naplo, "az író oldal a teljes útvonallal naplóz"
        # és az OLVASÓ oldal ugyanazt a kulcsot képzi a valódi rekordból
        assert any(full_path(r) == str(kep) for r in rekordok)

    def test_a_nezetfrissites_nem_szall_el_valodi_rekordokon(
        self, konyvtar, tmp_path, qt_app
    ):
        """A `_check_external_overwrites` a valódi rekordokkal fut le.

        A #644 tesztje csonk `path` mezős rekordot használt — ez a teszt
        pontosan azt a hiányt zárja be.
        """
        mappa, db = konyvtar
        controller = _controller(db, mappa, tmp_path)
        controller.recordSavedChain(str(mappa / "a.jpg"), "holga=1;")

        with open_index(db) as conn:
            rekordok = photos_in_folder(conn, str(mappa))

        controller._check_external_overwrites(rekordok)  # nem dobhat


def test_a_naplo_utvonalszabalya_egyetlen_helyen_el():
    """Harmadik útvonal-szabályt tilos írni (#699).

    A `_check_external_overwrites` a `queries.full_path()`-t hívja — ha
    valaki visszaír egy saját `str(Path(...))` képzést, ez az őr elbukik.
    """
    forras = (
        Path(__file__).resolve().parents[2]
        / "src/picasapy/app/edit_journal_controller.py"
    ).read_text(encoding="utf-8")
    assert "full_path(" in forras, "a közös útvonal-képzést kell használni"
    assert ".path)" not in forras.split("def _check_external_overwrites")[1][:400]
