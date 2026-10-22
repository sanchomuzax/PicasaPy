"""A cache-fájl átmeneti olvasási hibája nem sérült fotó (#5553).

A Windows CI-n egy frissen írt bélyegkép-fájl átmenetileg olvashatatlan
lehet. Ilyenkor a provider újrapróbálja, és a sérültfotó-jelzést csak akkor
adja, ha a forrásból sem készül bélyegkép.
"""

from picasapy.app import thumbnail_provider as provider_module
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


def _provider(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    make_jpeg(library / "photo.jpg", size=(320, 240))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=64))
    provider.register_photos(photos)
    return provider, photos


def _hibas_olvaso(hibak_szama):
    valodi = provider_module.read_image_bytes
    hivasok = []

    def olvas(path):
        hivasok.append(path)
        if len(hivasok) <= hibak_szama:
            return None
        return valodi(path)

    return olvas, hivasok


def test_atmeneti_olvasasi_hiba_utan_a_kep_betoltodik(qt_app, tmp_path, monkeypatch):
    provider, photos = _provider(tmp_path)
    olvas, hivasok = _hibas_olvaso(2)
    monkeypatch.setattr(provider_module, "read_image_bytes", olvas)
    monkeypatch.setattr(provider_module, "_alszik", lambda _s: None)
    jelzesek = []
    provider.brokenImageDetected.connect(jelzesek.append)

    image = provider.requestImage(str(photos[0].id), None, None)

    assert not image.isNull()
    assert len(hivasok) == 3
    assert jelzesek == []


def test_tartos_cache_olvasasi_hiba_ujrageneral_es_nem_jelez_serultet(
    qt_app, tmp_path, monkeypatch
):
    provider, photos = _provider(tmp_path)
    monkeypatch.setattr(provider_module, "read_image_bytes", lambda _p: None)
    monkeypatch.setattr(provider_module, "_alszik", lambda _s: None)
    jelzesek = []
    provider.brokenImageDetected.connect(jelzesek.append)

    provider.requestImage(str(photos[0].id), None, None)

    assert jelzesek == []


def test_a_cache_fajl_olvashatatlansaga_utan_ujrairja_a_belyegkepet(
    qt_app, tmp_path, monkeypatch
):
    provider, photos = _provider(tmp_path)
    provider.requestImage(str(photos[0].id), None, None)
    kesz = list((tmp_path / "thumbs").rglob("*.jpg"))
    assert len(kesz) == 1
    kesz[0].write_bytes(b"csonka")
    monkeypatch.setattr(provider_module, "_alszik", lambda _s: None)
    jelzesek = []
    provider.brokenImageDetected.connect(jelzesek.append)

    image = provider.requestImage(str(photos[0].id), None, None)

    assert not image.isNull()
    assert jelzesek == []
