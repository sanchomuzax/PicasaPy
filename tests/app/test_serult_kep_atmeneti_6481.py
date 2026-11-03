"""Átmeneti bélyegkép-hiba nem sérült kép (#6481).

A tulajdonos (1.0.29, Windows): szerkesztés közben, az effekt-előnézetek
frissülésekor időnként felugrott a „sérült fájlok elrejtése” ablak az épp
szerkesztett, ép képre. Az ok: ha a bélyegkép EGYSZER nem készült el (a
gyorstár None-t adott, például mert Windowson a gyorstár-fájl cseréje egy
párhuzamos olvasás miatt elbukott), a szolgáltató azonnal sérültnek jelölte
a képet. Most újrapróbál, és csak akkor jelez, ha a forráskép maga sem
olvasható.
"""

from __future__ import annotations

from picasapy.app import thumbnail_provider_render as render_module
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _provider(tmp_path, *, serult: bool = False):
    library = tmp_path / "library"
    library.mkdir()
    kep = library / "photo.jpg"
    make_jpeg(kep, size=(320, 240))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library)
    if serult:
        kep.write_bytes(b"\xff\xd8 nem kep, csak szemet" * 10)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=64))
    provider.register_photos(photos)
    return provider, photos


def _egyszer_bukik(cache, nev):
    valodi = getattr(cache, nev)
    hivasok = []

    def hivas(*args, **kwargs):
        hivasok.append(1)
        if len(hivasok) == 1:
            return None
        return valodi(*args, **kwargs)

    return hivas, hivasok


def test_egyszeri_gyorstar_hiba_utan_betoltodik_es_nem_jelez(qt_app, tmp_path, monkeypatch):
    provider, photos = _provider(tmp_path)
    hivas, hivasok = _egyszer_bukik(provider._cache, "get_or_create")
    monkeypatch.setattr(provider._cache, "get_or_create", hivas)
    monkeypatch.setattr(render_module, "_varakozas", lambda _s: None)
    jelzesek = []
    provider.brokenImageDetected.connect(jelzesek.append)

    kep = provider.requestImage(str(photos[0].id), None, None)

    assert len(hivasok) >= 2, "nem próbálta újra"
    assert not kep.isNull()
    assert jelzesek == []


def test_tartos_gyorstar_hiba_ep_forrasnal_nem_ajanl_elrejtest(qt_app, tmp_path, monkeypatch):
    provider, photos = _provider(tmp_path)
    monkeypatch.setattr(provider._cache, "get_or_create", lambda *a, **k: None)
    monkeypatch.setattr(render_module, "_varakozas", lambda _s: None)
    jelzesek = []
    provider.brokenImageDetected.connect(jelzesek.append)

    provider.requestImage(str(photos[0].id), None, None)

    assert jelzesek == [], "ép képre nem ajánlhatjuk fel az elrejtést"


def test_valoban_serult_fajlnal_tovabbra_is_jelez(qt_app, tmp_path, monkeypatch):
    provider, photos = _provider(tmp_path, serult=True)
    monkeypatch.setattr(render_module, "_varakozas", lambda _s: None)
    jelzesek = []
    provider.brokenImageDetected.connect(jelzesek.append)

    provider.requestImage(str(photos[0].id), None, None)

    assert jelzesek == [str(photos[0].id)]
