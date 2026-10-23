"""#4887 — a rejtett mappa képei a vezérlő nézeteiben sem látszanak.

Valódi `AppController`-rel, valódi könyvtárral: a gyökérmappa `a.jpg`-je
látszik, a `titkos` almappa `b.jpg`-je a menü útján (`toggleFolderHidden`)
lett elrejtve. Minden nézetre három állapotot mérünk:

1. a rejtettek megjelenítése KI → a rejtett kép nem látszik;
2. jelszó nélkül, a kapcsolóval BE → látszik;
3. jelszóval: a kapcsoló tárolva be, de zárva → nem látszik; feloldás után
   látszik.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from PySide6.QtCore import QSettings

from picasapy.index import open_index, sync_tree
from picasapy.index.hidden_scope import set_hidden_folders_visible
from picasapy.scanner import PICASA_INI_NAME
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
_ANNA = "a1a1a1a1a1a1a1a1"
_RECT = "3f840000c3509f84"
_ALBUM = "0123456789abcdef0123456789abcdef"
_JELSZO = "titok123"


def _ini(kep: str) -> str:
    return (
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n{_ANNA}=Anna;;\n"
        f"[.album:{_ALBUM}]\nname=Nyar\ntoken={_ALBUM}\n"
        f"[{kep}]\nstar=yes\nkeywords=nyar\nalbums={_ALBUM}\n"
        f"faces=rect64({_RECT}),{_ROY};rect64({_RECT}),{_ANNA}\n"
    )


def _epit_vezerlo(tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    controller = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller._reload_after_sync()
    controller.library = library
    return controller


@pytest.fixture
def ctrl(qt_app, tmp_path):
    library = tmp_path / "kepek"
    titkos = library / "titkos"
    titkos.mkdir(parents=True)
    friss = (datetime.now() - timedelta(days=2)).strftime("%Y:%m:%d %H:%M:%S")
    for mappa, kep in ((library, "a.jpg"), (titkos, "b.jpg")):
        # bájtra azonos képek: másodpéldányok és hasonlók is egymásnak
        make_jpeg(mappa / kep, taken_at=friss, gps=(47.5, 19.05))
        (mappa / PICASA_INI_NAME).write_text(_ini(kep), encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller = _epit_vezerlo(tmp_path, library)
    controller.toggleFolderHidden(str(titkos))
    return controller


def _nevek(rekordok) -> list[str]:
    return sorted(r.name for r in rekordok)


def _racs(ctrl) -> list[str]:
    return _nevek(ctrl._photos.photos)


def _feed(ctrl):
    ctrl.selectFolder(str(ctrl.library))
    return _racs(ctrl)


def _kereses_szoveg(ctrl):
    ctrl.search("nyar")
    return _racs(ctrl)


def _kereses_mappanev(ctrl):
    ctrl.search("titkos")
    return _racs(ctrl)


def _csillag(ctrl):
    ctrl.showStarred()
    return _racs(ctrl)


def _filmek(ctrl):
    with open_index(ctrl._db_path) as conn:
        conn.execute("UPDATE photos SET kind = 'video'")
        conn.commit()
    ctrl.showVideosOnly()
    return _racs(ctrl)


def _kor(ctrl):
    ctrl.setAgeFilter(0.5)  # ~91 napos képekig
    return _racs(ctrl)


def _arcos(ctrl):
    ctrl.showFacesOnly()
    return _racs(ctrl)


def _album(ctrl):
    ctrl.showAlbum(_ALBUM)
    return _racs(ctrl)


def _szemely_album(ctrl):
    ctrl.showPerson("Roy Avery")
    return _racs(ctrl)


def _nevsor_darab(ctrl):
    darab = {p["name"]: p["count"] for p in ctrl.people}["Roy Avery"]
    return ["b.jpg"] if darab == 2 else ["a.jpg"]


def _terkep(ctrl):
    ctrl.showGeotagged()
    return _racs(ctrl)


def _idovonal(ctrl):
    from picasapy.app.timeline_controller import TimelineController

    idovonal = TimelineController(ctrl._db_path, ctrl._provider)
    idovonal.reload()
    return sorted(
        photo["name"]
        for collection in idovonal.collections
        for photo in collection["photos"]
    )


def _hasonlok(ctrl):
    return _nevek(ctrl._similar_records(str(ctrl.library / "a.jpg")))


def _masodpeldanyok(ctrl):
    return _nevek(ctrl._duplicate_records()) or ["a.jpg"]


def _diavetites_szulomappa(ctrl):
    ctrl.setScreensaverSources([f"folder:{ctrl.library}"])
    ctrl.prepareScreensaverPreview()
    return _nevek(ctrl._screensaver_photos.photos)


_NEZETEK = {
    "feed": _feed,
    "kereses-szoveg": _kereses_szoveg,
    "kereses-mappanev": _kereses_mappanev,
    "csillag": _csillag,
    "csak-filmek": _filmek,
    "kor-szuro": _kor,
    "arcos-kepek": _arcos,
    "album": _album,
    "szemely-album": _szemely_album,
    "emberek-nevsor": _nevsor_darab,
    "terkep": _terkep,
    "idovonal": _idovonal,
    "hasonlok": _hasonlok,
    "masodpeldanyok": _masodpeldanyok,
    "diavetites-szulomappa": _diavetites_szulomappa,
}


@pytest.mark.parametrize("nezet", sorted(_NEZETEK))
def test_rejtett_mappa_kepe_nem_latszik(ctrl, nezet):
    nevek = _NEZETEK[nezet](ctrl)
    assert "b.jpg" not in nevek
    if nezet != "kereses-mappanev":
        assert "a.jpg" in nevek  # a nézet tényleg mér, nem üres


@pytest.mark.parametrize("nezet", sorted(_NEZETEK))
def test_jelszo_nelkul_a_kapcsoloval_latszik(ctrl, nezet):
    ctrl.setShowHidden(True)
    assert ctrl.showHidden is True
    assert "b.jpg" in _NEZETEK[nezet](ctrl)
    ctrl.setShowHidden(False)
    assert "b.jpg" not in _NEZETEK[nezet](ctrl)


@pytest.mark.parametrize("nezet", sorted(_NEZETEK))
def test_jelszoval_csak_feloldas_utan_latszik(ctrl, nezet):
    ctrl.setHiddenPassword(_JELSZO)
    # a tárolt kapcsoló be van kapcsolva, de a kapu zárva (pl. újraindítás)
    ctrl._get_settings().setValue("view/showHidden", True)
    assert ctrl.showHidden is False
    assert "b.jpg" not in _NEZETEK[nezet](ctrl)
    assert ctrl.unlockHidden(_JELSZO) is True
    assert ctrl.showHidden is True
    assert "b.jpg" in _NEZETEK[nezet](ctrl)


def test_ujrainditas_utan_zarva_indul(ctrl, tmp_path):
    """A feloldás nem marad meg: az új vezérlő az indexnek is zárt
    láthatóságot közöl, hiába volt az előző munkamenet feloldva."""
    ctrl.setHiddenPassword(_JELSZO)
    ctrl.unlockHidden(_JELSZO)
    ctrl.setShowHidden(True)
    assert "b.jpg" in _feed(ctrl)
    uj = _epit_vezerlo(tmp_path, ctrl.library)
    assert uj.showHidden is False
    assert "b.jpg" not in _feed(uj)


class TestKepernyovedo:
    def test_forraslista_nem_kinalja_a_rejtett_mappat(self, ctrl):
        kulcsok = {s["key"] for s in ctrl.screensaverSources}
        titkos = f"folder:{ctrl.library / 'titkos'}"
        assert titkos not in kulcsok
        ctrl.setShowHidden(True)
        assert titkos in {s["key"] for s in ctrl.screensaverSources}

    def test_album_forras_darabszama_csak_a_lathato(self, ctrl):
        darab = {s["key"]: s["count"] for s in ctrl.screensaverSources}
        assert darab[f"album:{_ALBUM}"] == 1

    def test_a_tetlenseg_inditotta_vetites_sem_vetiti(self, ctrl, tmp_path):
        """A `--screensaver` belépési pont vezérlő nélkül fut — a biztonságos
        alapértéket kapja, a szülőmappa rejtett almappáját nem vetíti."""
        from picasapy.app.screensaver_controller import load_screensaver_slides

        set_hidden_folders_visible(ctrl._db_path, False)
        beallitas = QSettings(str(tmp_path / "ss.ini"), QSettings.Format.IniFormat)
        beallitas.setValue("screensaver/sources", [f"folder:{ctrl.library}"])
        kepek = load_screensaver_slides(ctrl._db_path, beallitas, (str(ctrl.library),))
        assert _nevek(kepek) == ["a.jpg"]


def test_mappa_elrejtese_azonnal_eltunteti_a_feedbol(ctrl):
    """A menüből elrejtett mappa képe a már nyitott feedből is eltűnik."""
    ctrl.toggleFolderHidden(str(ctrl.library / "titkos"))  # vissza látható
    assert "b.jpg" in _feed(ctrl)
    ctrl.toggleFolderHidden(str(ctrl.library / "titkos"))
    assert "b.jpg" not in _racs(ctrl)


def test_talca_nem_adja_tovabb_a_rejtett_kepet(ctrl):
    """A tálca (export, kollázs, film forrása) a megjelenítés kikapcsolása
    után a korábban megtartott rejtett képet sem adja tovább."""
    ctrl.setShowHidden(True)
    ctrl.selectFolder(str(ctrl.library))
    sor = [p.name for p in ctrl._photos.photos].index("b.jpg")
    ctrl.holdRows([sor])
    assert "b.jpg" in _nevek(ctrl._tray_records())
    ctrl.setShowHidden(False)
    assert "b.jpg" not in _nevek(ctrl._tray_records())
