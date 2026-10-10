"""#4839: a korai Picasa.ini is bájtra pontosan járja meg a mentést."""

from __future__ import annotations

from pathlib import Path

from picasapy.backup import futtasd, tervezd_meg
from picasapy.backup.lemezkep import LemezkepTetel, lemezkepekbe
from picasapy.backup.visszaallitas import visszaallit
from picasapy.burn import DVD
from picasapy.index import open_index
from picasapy.index.backup_sets import keszlet_letrehozasa
from picasapy.ini.names import LEGACY_INI_NAME


def test_legacy_ini_backup_and_restore_preserve_original_bytes(tmp_path):
    source = tmp_path / "forras" / "album"
    source.mkdir(parents=True)
    photo = source / "kep.jpg"
    photo.write_bytes(b"\xff\xd8\xffkep")
    legacy_bytes = b"\xef\xbb\xbf[kep.jpg]\r\nstar=yes\r\ncaption=\xff\r\n"
    (source / LEGACY_INI_NAME).write_bytes(legacy_bytes)
    backup = tmp_path / "mentes"

    with open_index(tmp_path / "index.db") as conn:
        set_ = keszlet_letrehozasa(conn, "teszt", str(backup))
        plan = tervezd_meg(conn, set_, [photo], gyokerek=[tmp_path / "forras"])
        futtasd(conn, set_, plan)

    archived_legacy = backup / "album" / LEGACY_INI_NAME
    assert archived_legacy.read_bytes() == legacy_bytes
    assert not (backup / "album" / ".picasa.ini").exists()

    restored = tmp_path / "visszaallitott"
    visszaallit(backup, restored)

    assert (restored / "album" / LEGACY_INI_NAME).read_bytes() == legacy_bytes
    assert not (restored / "album" / ".picasa.ini").exists()


def test_legacy_ini_iso_backup_and_restore_preserve_original_bytes(tmp_path):
    source = tmp_path / "forras" / "album"
    source.mkdir(parents=True)
    photo = source / "kep.jpg"
    photo.write_bytes(b"\xff\xd8\xffkep")
    legacy_bytes = b"[kep.jpg]\r\nstar=yes\r\ncaption=regi\r\n"
    (source / LEGACY_INI_NAME).write_bytes(legacy_bytes)

    result = lemezkepekbe(
        [
            LemezkepTetel(
                relativ=Path("album/kep.jpg"),
                forras=photo,
                meret=photo.stat().st_size,
            )
        ],
        tmp_path / "lemezkep",
        media=DVD,
        szektorszam=2_295_104,
    )
    restored = tmp_path / "visszaallitott_iso"
    visszaallit(result.kepek[0], restored)

    assert (restored / "album" / LEGACY_INI_NAME).read_bytes() == legacy_bytes
    assert not (restored / "album" / ".picasa.ini").exists()
