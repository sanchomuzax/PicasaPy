"""#4448: a mappában beállított zene a diavetítés és a film forrása."""

from pathlib import Path

from PySide6.QtCore import QUrl

from picasapy.app.create_controller import film_zene_mappabol
from picasapy.ini import with_folder_music, parse_document, save_document
from picasapy.app.folder_date_controller import FolderDateMixin


def _mappa_ini(mappa: Path, engedelyezve: bool, zene: Path) -> None:
    save_document(
        with_folder_music(parse_document(""), engedelyezve, str(zene)),
        mappa / ".picasa.ini",
    )


class TestFolderMusicMixin:
    def test_mappatulajdonsagbol_ment_es_visszaolvas(self, tmp_path):
        mappa = tmp_path / "nyar"
        mappa.mkdir()
        zene = mappa / "tavasz.mp3"
        zene.write_bytes(b"teszt")

        class Host(FolderDateMixin):
            def jelentsdAzIrasiHibat(self, _error):
                raise AssertionError("nem várt ini-írási hiba")

        host = Host()
        host.setFolderMusic(str(mappa), True, str(zene))

        assert host.folderMusicEnabled(str(mappa)) is True
        assert host.folderMusicFile(str(mappa)) == str(zene)

    def test_diavetites_urlje_a_beallitott_fajl_es_kikapcsolva_ures(self, tmp_path):
        mappa = tmp_path / "nyar"
        mappa.mkdir()
        zene = mappa / "tavasz.mp3"
        zene.write_bytes(b"teszt")
        _mappa_ini(mappa, True, zene)

        class Host(FolderDateMixin):
            pass

        host = Host()
        urls = host.folderMusicTrackUrls(str(mappa))
        assert len(urls) == 1
        assert QUrl(urls[0]).toLocalFile() == str(zene)
        host.setFolderMusic(str(mappa), False, str(zene))
        assert host.folderMusicTrackUrls(str(mappa)) == []


def test_mozgofilm_a_kozos_mappa_beallitott_zenefajljat_kapja(tmp_path):
    mappa = tmp_path / "nyar"
    mappa.mkdir()
    zene = mappa / "tavasz.mp3"
    zene.write_bytes(b"teszt")
    (mappa / ".picasa.ini").write_text(
        f"[Picasa]\nusemusic=1\nmusic={zene}\n", encoding="utf-8"
    )

    assert film_zene_mappabol([mappa / "egy.jpg", mappa / "ketto.jpg"]) == zene


def test_mozgofilm_nem_hasznal_mappazenet_kulonbozo_mappakbol(tmp_path):
    egyik, masik = tmp_path / "egy", tmp_path / "ketto"
    egyik.mkdir()
    masik.mkdir()
    zene = egyik / "tavasz.mp3"
    zene.write_bytes(b"teszt")
    (egyik / ".picasa.ini").write_text(
        f"[Picasa]\nusemusic=1\nmusic={zene}\n", encoding="utf-8"
    )

    assert film_zene_mappabol([egyik / "egy.jpg", masik / "ketto.jpg"]) is None
