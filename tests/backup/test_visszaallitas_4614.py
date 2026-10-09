"""#4614: a mappás és ISO mentési készletből visszaállíthatóak a képek."""

from __future__ import annotations

from pathlib import Path

from picasapy.backup.visszaallitas import visszaallit
from picasapy.burn.iso import iso_kiirasa


def _peldakep(ut: Path, adat: bytes) -> Path:
    ut.parent.mkdir(parents=True, exist_ok=True)
    ut.write_bytes(adat)
    return ut


def test_mappas_keszletbol_bajtra_pontos_visszaallitas(tmp_path):
    mentes = tmp_path / "mentes"
    adat = b"PicasaPy folder backup image\x00\xff"
    _peldakep(mentes / "utazas" / "kep.jpg", adat)
    (mentes / "files.txt").write_text(
        f"utazas/kep.jpg\t{len(adat)}\t123\n", encoding="utf-8"
    )

    eredmeny = visszaallit(mentes, tmp_path / "visszaallitott")

    cel = tmp_path / "visszaallitott" / "utazas" / "kep.jpg"
    assert cel.read_bytes() == adat
    assert eredmeny.visszaallitott == 1
    assert eredmeny.kihagyott == 0


def test_iso_keszletbol_bajtra_pontos_visszaallitas(tmp_path):
    kep = _peldakep(tmp_path / "forras.jpg", b"image from disc image\x00\x91")
    lista = tmp_path / "iso-files.txt"
    lista.write_text(
        f"album/kep.jpg\t{kep.stat().st_size}\t456\n", encoding="utf-8"
    )
    iso = iso_kiirasa(
        [("album/kep.jpg", kep), ("files.txt", lista)],
        tmp_path / "mentes-01.iso",
        ido=0,
    )

    eredmeny = visszaallit(iso, tmp_path / "visszaallitott")

    cel = tmp_path / "visszaallitott" / "album" / "kep.jpg"
    assert cel.read_bytes() == kep.read_bytes()
    assert eredmeny.visszaallitott == 1
    assert eredmeny.kihagyott == 0


def test_meglevo_celfajlt_nem_ir_felul(tmp_path):
    mentes = tmp_path / "mentes"
    _peldakep(mentes / "kep.jpg", b"backup")
    (mentes / "files.txt").write_text("kep.jpg\t6\t1\n", encoding="utf-8")
    cel = _peldakep(tmp_path / "visszaallitott" / "kep.jpg", b"meglevo")

    eredmeny = visszaallit(mentes, cel.parent)

    assert cel.read_bytes() == b"meglevo"
    assert eredmeny.visszaallitott == 0
    assert eredmeny.kihagyott == 1


def test_picasa_manifest_a_p_alias_nelkul_allitja_vissza_a_kepeket(tmp_path):
    mentes = tmp_path / "picasa-mentes"
    adat = b"original Picasa manifest photo"
    _peldakep(mentes / "[P]" / "album" / "kep.jpg", adat)
    _peldakep(mentes / "[P]" / "album" / "picasa.exe", b"not a photo")
    (mentes / "PicasaManifest.xml").write_text(
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<PicasaManifest version='2.1'><files>"
        "<file><path>[P]&#92;album&#92;kep.jpg</path></file>"
        "<file shouldRestore='NO'><path>[P]&#92;album&#92;picasa.exe</path></file>"
        "</files></PicasaManifest>",
        encoding="utf-8",
    )

    eredmeny = visszaallit(mentes, tmp_path / "visszaallitott")

    assert (tmp_path / "visszaallitott" / "album" / "kep.jpg").read_bytes() == adat
    assert not (tmp_path / "visszaallitott" / "[P]").exists()
    assert eredmeny.visszaallitott == 1


def test_eredeti_picasa_mappas_files_txt_utvonalabol_visszaallit(tmp_path):
    mentes = tmp_path / "picasa-mappas-mentes"
    adat = b"original Picasa folder image"
    _peldakep(mentes / "album" / "kep.jpg", adat)
    (mentes / "files.txt").write_text(
        "# Created on 3 Sep 2026 by Picasa\n"
        "#\n"
        "# version: 141.26\n"
        "# platform: Windows 10\n"
        "\n"
        "C:\\\\Camera\\\\album\\\\kep.jpg\n"
        "Utazási kép\n",
        encoding="utf-8",
    )

    visszaallit(mentes, tmp_path / "visszaallitott")

    assert (
        tmp_path / "visszaallitott" / "album" / "kep.jpg"
    ).read_bytes() == adat


def test_eredeti_picasa_iso_manifestbol_bajtra_pontosan_visszaallit(tmp_path):
    adat = b"original Picasa disc image photo"
    kep = _peldakep(tmp_path / "forras.jpg", adat)
    manifest = tmp_path / "PicasaManifest.xml"
    manifest.write_text(
        "<?xml version='1.0' encoding='UTF-8'?>"
        "<PicasaManifest version='2.1'><files>"
        "<file><path>[P]&#92;album&#92;kep.jpg</path></file>"
        "<file shouldRestore='NO'><path>[P]&#92;app.exe</path></file>"
        "</files></PicasaManifest>",
        encoding="utf-8",
    )
    iso = iso_kiirasa(
        [
            ("[P]/album/kep.jpg", kep),
            ("PicasaManifest.xml", manifest),
        ],
        tmp_path / "picasa-disc.iso",
        ido=0,
    )

    visszaallit(iso, tmp_path / "visszaallitott")

    assert (
        tmp_path / "visszaallitott" / "album" / "kep.jpg"
    ).read_bytes() == adat
