"""#3173 — az album tulajdonságainak szerkesztése a vezérlőn át.

A definíció (`[.album:<token>]`) MINDEN olyan mappa ini-jében ott van, ahol az
albumnak van tagja (a `createAlbum` így írja ki, ahogy a Picasa is) — tehát az
átnevezésnek is mindegyiket át kell írnia, különben a bal hasáb mappánként más
nevet látna.

Amit mérünk:

* a négy mért mező kiírása MINDEN érintett mappába;
* a nem érintett mappa ini-je **érintetlen** marad (nem keletkezik
  szellem-album);
* a prefill (`albumProperties`) a mai értékeket adja vissza;
* ismeretlen tokenre semmi nem történik, és a hívó `False`-t kap.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.ini.albums import albums_of
from picasapy.ini.document import parse_document


def _ini(mappa: Path) -> str:
    ut = mappa / ".picasa.ini"
    return ut.read_text(encoding="utf-8") if ut.exists() else ""


_TOKEN = "a" * 32


@pytest.fixture
def ket_mappas_album(qt_app, tmp_path):
    """Két mappa, mindkettőben UGYANAZ az album egy-egy taggal.

    A `createAlbum` a definíciót minden érintett mappába kiírja (ahogy a
    Picasa is) — a szerkesztésnek tehát mindegyiket át kell írnia.
    """
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from support.jpeg_factory import make_jpeg

    gyoker = tmp_path / "kepek"
    for nev in ("egy", "ketto", "harom"):
        (gyoker / nev).mkdir(parents=True)
        make_jpeg(gyoker / nev / f"{nev}.jpg")
    for nev in ("egy", "ketto"):
        (gyoker / nev / ".picasa.ini").write_text(
            f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Régi név\n"
            f"[{nev}.jpg]\nalbums={_TOKEN}\n",
            encoding="utf-8",
        )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    beallitas = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    vezerlo = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        provider,
        settings=beallitas,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    vezerlo._reload()
    return vezerlo, gyoker, _TOKEN


class TestAzIras:
    def test_mindket_mappaban_atirja(self, ket_mappas_album):
        vezerlo, gyoker, token = ket_mappas_album
        assert vezerlo.editAlbumProperties(
            token, "Nyaralás", "2026-07-14", "Balaton", "A nagy kör"
        ) is True
        for nev in ("egy", "ketto"):
            album = albums_of(parse_document(_ini(gyoker / nev)))[0]
            assert album.name == "Nyaralás"
            assert album.date == "2026-07-14"
            assert album.location == "Balaton"
            assert album.description == "A nagy kör"

    def test_az_album_NELKULI_mappat_nem_bantja(self, ket_mappas_album):
        vezerlo, gyoker, token = ket_mappas_album
        harmadik = gyoker / "harom"
        harmadik.mkdir(exist_ok=True)
        (harmadik / "harom.jpg").write_bytes(b"")
        vezerlo.editAlbumProperties(token, "Nyaralás", "", "", "")
        assert not (harmadik / ".picasa.ini").exists(), (
            "az album nélküli mappába szellem-albumot írtunk"
        )

    def test_ismeretlen_tokenre_FALSE(self, ket_mappas_album):
        vezerlo, _gyoker, _token = ket_mappas_album
        assert vezerlo.editAlbumProperties("b" * 32, "X", "", "", "") is False

    def test_ures_tokenre_FALSE(self, ket_mappas_album):
        vezerlo, _gyoker, _token = ket_mappas_album
        assert vezerlo.editAlbumProperties("", "X", "", "", "") is False


class TestAPrefill:
    def test_a_mai_ertekeket_adja(self, ket_mappas_album):
        vezerlo, _gyoker, token = ket_mappas_album
        adat = vezerlo.albumProperties(token)
        assert adat["name"] == "Régi név"
        assert adat["date"] == ""
        assert adat["location"] == ""
        assert adat["description"] == ""

    def test_ismeretlen_tokenre_URES(self, ket_mappas_album):
        vezerlo, _gyoker, _token = ket_mappas_album
        assert vezerlo.albumProperties("b" * 32) == {}
