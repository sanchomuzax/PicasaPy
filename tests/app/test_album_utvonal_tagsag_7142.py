"""#7142: az útvonal szerinti albumtagság (a Beillesztés albumcélja).

A vezérlő-szintű mérés: a `addPathsToAlbum` a vágólap fájlútvonalait a
könyvtár képeire oldja fel, és az album tagjává teszi őket a meglévő
tagság-úton (`_write_album_batch`). Az `.picasa.ini` tartalmát és a
fájlrendszert olvassuk, nem a forrást.

Az ablakos (renderelt) párja: `qml_functional/test_album_beillesztes_7142.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QByteArray, QMimeData, QUrl
from support.jpeg_factory import make_jpeg

from picasapy.index import open_index, sync_tree
from picasapy.index.queries import photo_by_path
from picasapy.ini.albums import parse_album_refs
from picasapy.ini.document import parse_document
from picasapy.scanner import PICASA_INI_NAME

_GNOME = "x-special/gnome-copied-files"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "varos").mkdir()
    make_jpeg(root / "nyaralas" / "a.jpg")
    make_jpeg(root / "nyaralas" / "b.jpg")
    make_jpeg(root / "varos" / "c.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


def _ini_szakasz(mappa: Path, kep: str):
    ini = mappa / PICASA_INI_NAME
    if not ini.is_file():
        return None
    return parse_document(ini.read_text(encoding="utf-8")).section(kep)


def _tagsag(mappa: Path, kep: str) -> tuple[str, ...]:
    szakasz = _ini_szakasz(mappa, kep)
    return parse_album_refs((szakasz.get("albums") if szakasz else "") or "")


def _kepek(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.suffix.lower() == ".jpg"
    }


def _album_a_jpg_taggal(controller, library) -> str:
    """Album, amelynek EGYETLEN tagja a nyaralas/a.jpg (a rács sorát név adja)."""
    sor = next(
        i
        for i, photo in enumerate(controller.photos.photos)
        if photo.name == "a.jpg"
    )
    token = controller.createAlbum("Nyár", [sor])
    assert token
    return token


class TestAddPathsToAlbum:
    def test_a_konyvtar_kepei_tagok_lesznek_mappakon_at(self, controller, library):
        token = _album_a_jpg_taggal(controller, library)
        elotte = _kepek(library)

        assert controller.addPathsToAlbum(
            [str(library / "nyaralas" / "b.jpg"), str(library / "varos" / "c.jpg")],
            token,
        ) is True

        assert _tagsag(library / "nyaralas", "b.jpg") == (token,)
        assert _tagsag(library / "varos", "c.jpg") == (token,)
        assert _kepek(library) == elotte, "új vagy módosult képfájl"

    def test_a_mar_tag_kep_es_az_ismetelt_utvonal_nem_duplazodik(
        self, controller, library
    ):
        token = _album_a_jpg_taggal(controller, library)
        a = str(library / "nyaralas" / "a.jpg")
        b = str(library / "nyaralas" / "b.jpg")

        assert controller.addPathsToAlbum([a, b, b], token) is True
        assert controller.addPathsToAlbum([b], token) is True

        assert _tagsag(library / "nyaralas", "a.jpg") == (token,)
        assert _tagsag(library / "nyaralas", "b.jpg") == (token,)
        counts = {a["token"]: a["count"] for a in controller.albums}
        assert counts[token] == 2, "a már tag és az ismételt kép többször számolt"

    def test_a_konyvtaron_kivuli_utvonal_marad_ki_es_nem_hoz_letre_semmit(
        self, controller, library, tmp_path
    ):
        token = _album_a_jpg_taggal(controller, library)
        kivul = tmp_path / "kivul"
        kivul.mkdir()
        make_jpeg(kivul / "z.jpg")
        elotte = _kepek(library)

        assert controller.addPathsToAlbum([str(kivul / "z.jpg")], token) is False
        assert controller.addPathsToAlbum(
            [str(kivul / "z.jpg"), str(library / "varos" / "c.jpg")], token
        ) is True

        assert not (kivul / PICASA_INI_NAME).exists()
        assert _tagsag(library / "varos", "c.jpg") == (token,)
        assert _kepek(library) == elotte

    @pytest.mark.parametrize("token", ["", "   "])
    def test_ures_token_vagy_ures_lista_nem_tesz_semmit(
        self, controller, library, token
    ):
        c = str(library / "varos" / "c.jpg")

        assert controller.addPathsToAlbum([c], token) is False
        assert controller.addPathsToAlbum([], "bármi") is False

        assert _tagsag(library / "varos", "c.jpg") == ()

    def test_az_ini_nelkuli_ures_album_az_elso_taggal_kap_definiciot(
        self, controller, library
    ):
        """A csak az indexben élő (üres) album az első taggal ini-be kerül."""
        token = controller.createEmptyAlbum(
            "Budapest", str(library / "varos"), "2026-10-25", "", "", False, ""
        )
        assert token
        assert not (library / "varos" / PICASA_INI_NAME).exists()

        assert controller.addPathsToAlbum([str(library / "varos" / "c.jpg")], token)

        assert _tagsag(library / "varos", "c.jpg") == (token,)
        assert token in {a["token"] for a in controller.albums}


class TestPhotoByPath:
    def test_az_indexelt_kepet_megtalalja_a_hianyzot_nem(self, controller, library):
        with open_index(controller._db_path) as conn:
            talalt = photo_by_path(conn, library / "varos", "c.jpg")
            nincs = photo_by_path(conn, library / "varos", "nincs.jpg")
            masik_mappa = photo_by_path(conn, library / "nyaralas", "c.jpg")

        assert talalt is not None and talalt.name == "c.jpg"
        assert Path(talalt.folder_path) == library / "varos"
        assert nincs is None
        assert masik_mappa is None


def _mime(utak, muvelet: str) -> QMimeData:
    adat = QMimeData()
    urlek = [QUrl.fromLocalFile(str(u)) for u in utak]
    adat.setUrls(urlek)
    sorok = [muvelet, *(u.toString() for u in urlek)]
    adat.setData(_GNOME, QByteArray("\n".join(sorok).encode("utf-8")))
    return adat


class TestPasteFilesFromClipboardAlbumCelnal:
    """A `pasteFilesFromClipboard` album-tokennel: tagság, nem fájlművelet."""

    @pytest.fixture
    def vezerlo(self, qt_app, controller, monkeypatch):
        from picasapy.app.application_services import wire_fileops
        from picasapy.app.fileops_controller import FileOpsController

        vezerlo = FileOpsController()
        wire_fileops(vezerlo, controller)
        vezerlo.hivasok = []
        vezerlo.megerositesek = []
        for nev in ("_copy_batch", "_move_batch"):
            monkeypatch.setattr(
                vezerlo,
                nev,
                lambda *a, _nev=nev, **k: vezerlo.hivasok.append(_nev),
            )
        vezerlo.clipboardPasteConfirmationRequested.connect(
            lambda *args: vezerlo.megerositesek.append(args)
        )
        return vezerlo

    @pytest.mark.parametrize("muvelet", ["copy", "cut"])
    def test_masolas_es_kivagas_is_tagsagot_ad_fajl_nelkul(
        self, vezerlo, controller, library, monkeypatch, muvelet
    ):
        token = _album_a_jpg_taggal(controller, library)
        b, c = library / "nyaralas" / "b.jpg", library / "varos" / "c.jpg"
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([b, c], muvelet))
        elotte = _kepek(library)

        assert vezerlo.pasteFilesFromClipboard("", False, token) is True

        assert _tagsag(library / "nyaralas", "b.jpg") == (token,)
        assert _tagsag(library / "varos", "c.jpg") == (token,)
        assert _kepek(library) == elotte, "a forrás a helyén és érintetlen marad"
        assert vezerlo.hivasok == [] and vezerlo.megerositesek == []

    def test_a_celmappa_es_a_mappa_jelzo_albumnal_nem_szamit(
        self, vezerlo, controller, library, monkeypatch
    ):
        """A korábbi mappa (más forrásmappa, `True` jelző) sem kérdést, sem
        másolást nem indít: a token dönt."""
        token = _album_a_jpg_taggal(controller, library)
        c = library / "varos" / "c.jpg"
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([c], "copy"))

        assert vezerlo.pasteFilesFromClipboard(
            str(library / "nyaralas"), True, token
        ) is True

        assert vezerlo.hivasok == [] and vezerlo.megerositesek == []
        assert _tagsag(library / "varos", "c.jpg") == (token,)

    def test_ures_vagolap_vagy_konyvtaron_kivuli_fajl_hamis_es_nem_masol(
        self, vezerlo, controller, library, tmp_path, monkeypatch
    ):
        token = _album_a_jpg_taggal(controller, library)
        kivul = tmp_path / "z.jpg"
        make_jpeg(kivul)

        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: None)
        assert vezerlo.pasteFilesFromClipboard("", False, token) is False
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([kivul], "cut"))
        assert vezerlo.pasteFilesFromClipboard("", False, token) is False

        assert vezerlo.hivasok == [] and vezerlo.megerositesek == []
        assert kivul.is_file()

    def test_bekotetlen_iroval_sem_esik_vissza_fajlmuveletre(
        self, vezerlo, controller, library, monkeypatch
    ):
        token = _album_a_jpg_taggal(controller, library)
        vezerlo._album_tagsag_iro = None
        c = library / "varos" / "c.jpg"
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([c], "copy"))

        assert vezerlo.pasteFilesFromClipboard(str(library / "nyaralas"), True, token) is False

        assert vezerlo.hivasok == [] and vezerlo.megerositesek == []

    def test_token_nelkul_a_mappas_ut_valtozatlan(
        self, vezerlo, controller, library, monkeypatch
    ):
        """Mappanézet (nincs token): az eltérő mappás beillesztés kérdez."""
        c = library / "varos" / "c.jpg"
        monkeypatch.setattr(vezerlo, "_vagolap_adata", lambda: _mime([c], "copy"))

        assert vezerlo.pasteFilesFromClipboard(str(library / "nyaralas"), True, "") is True

        assert len(vezerlo.megerositesek) == 1
        assert vezerlo.hivasok == []
