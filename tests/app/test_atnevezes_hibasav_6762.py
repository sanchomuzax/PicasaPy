# ruff: noqa: F811  (a kepernyokepek fixture importja és paraméterként való használata)
"""Az átnevezett figyelt mappa után nincs téves hibasáv (#6762).

A #6751 óta a program követi az Intézőben átnevezett figyelt mappát, de ha
az átnevezés zárt program mellett történt, az indulási szinkron a régi
gyökeret még hibának jelentette („A szkennelendő gyökér nem létezik”), és a
felületen piros hibasáv jelent meg. Az átnevezést a #6751 szabálya ismeri
fel (a szülő megvan, a régi képek egy testvérmappában állnak); ilyenkor
nincs mit jelenteni. A testvér nélkül eltűnt gyökér (lecsatolt meghajtó,
elavult útvonal) hibajelzése marad.
"""

from __future__ import annotations

from tests.app.test_eltunt_gyoker_atnevezes_6751 import (  # noqa: F401
    _leallit,
    _mappak,
    _var,
    kepernyokepek,
)


def _indit_atnevezes_utan(qt_app, tmp_path, gyoker, valtoztatas):
    """Index a régi állapotról, változás zárt program mellett, majd indulás."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
    valtoztatas()
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyoker),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    hibak: list[str] = []
    ctl.syncFailed.connect(hibak.append)
    ctl.start()
    return ctl, hibak


def test_zart_program_mellett_atnevezett_gyokernel_nincs_hibajelzes(
    qt_app, tmp_path, kepernyokepek
):
    a = kepernyokepek / "202611-a"
    b = kepernyokepek / "202611-b"
    ctl, hibak = _indit_atnevezes_utan(qt_app, tmp_path, a, lambda: a.rename(b))
    try:
        assert _var(qt_app, lambda: not ctl._sync_running and str(b) in _mappak(ctl)), (
            "az átnevezett mappát a program nem követte"
        )
        assert hibak == [], f"téves hibasáv az átnevezés után: {hibak}"
    finally:
        _leallit(ctl)


def test_testver_nelkul_eltunt_gyokernel_marad_a_hibajelzes(
    qt_app, tmp_path, kepernyokepek
):
    a = kepernyokepek / "202611-a"

    def torles():
        for f in a.iterdir():
            f.unlink()
        a.rmdir()

    ctl, hibak = _indit_atnevezes_utan(qt_app, tmp_path, a, torles)
    try:
        assert _var(qt_app, lambda: not ctl._sync_running and bool(hibak))
        assert any("202611-a" in h for h in hibak)
    finally:
        _leallit(ctl)
