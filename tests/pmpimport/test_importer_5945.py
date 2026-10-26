"""#5945: útvonalütközésnél az újabb db3-rekord nyer, az átvétel ismételhető."""

from picasapy.pmpimport.db3_atvetel import rekordokat_atvesz
from picasapy.pmpimport.importer import iter_photo_records
from picasapy.pmpimport.remap import PathRemapper
from support.pmp_factory import build_pmp_column, build_thumb_index


def test_utkozeskor_ujabb_mtime_nyer_es_ujraimportalva_nem_duplaz(tmp_path):
    db3 = tmp_path / "db3"
    db3.mkdir()
    foto_mappa = tmp_path / "fotok"
    foto_mappa.mkdir()
    (foto_mappa / "kozos.jpg").write_bytes(b"")

    # Két forrásrekord két külön windowsos útvonalon ugyanarra a helyi képre
    # remappelődik. A második sor később módosult, ezért annak adatai nyernek.
    (db3 / "thumbindex.db").write_bytes(
        build_thumb_index(
            [
                (r"C:\archivum", None),
                ("kozos.jpg", 0, 2, 1, 100, 1_000),
                (r"D:\friss", None),
                ("kozos.jpg", 2, 2, 1, 200, 2_000),
            ]
        )
    )
    (db3 / "imagedata_caption.pmp").write_bytes(
        build_pmp_column(0x00, ["", "régi felirat", "", "friss felirat"])
    )
    (db3 / "imagedata_tags.pmp").write_bytes(
        build_pmp_column(0x06, ["", "régi", "", "friss"])
    )
    (db3 / "imagedata_lat.pmp").write_bytes(
        build_pmp_column(0x02, [0.0, 47.0, 0.0, 48.0])
    )
    (db3 / "imagedata_long.pmp").write_bytes(
        build_pmp_column(0x02, [0.0, 19.0, 0.0, 20.0])
    )
    (db3 / "imagedata_geoview.pmp").write_bytes(
        build_pmp_column(0x00, ["", "régi", "", "friss"])
    )

    remapper = PathRemapper.from_dict(
        {
            r"C:\archivum": str(foto_mappa),
            r"D:\friss": str(foto_mappa),
        }
    )
    rekordok = iter_photo_records(db3, remapper)

    assert len(rekordok) == 1
    assert rekordok[0].row == 3
    assert rekordok[0].modified_filetime == 2_000
    assert rekordok[0].tags == ("friss",)
    assert rekordok[0].latitude == 48.0
    assert rekordok[0].longitude == 20.0

    rekordokat_atvesz(rekordok, backup=False)
    ini = foto_mappa / ".picasa.ini"
    elso_iras = ini.read_bytes()
    assert b"keywords=friss" in elso_iras
    assert b"geotag=48.000000,20.000000" in elso_iras

    masodik_rekordok = iter_photo_records(db3, remapper)
    masodik_jelentes = rekordokat_atvesz(masodik_rekordok, backup=False)
    assert masodik_rekordok == rekordok
    assert ini.read_bytes() == elso_iras
    assert masodik_jelentes.mappak == 0
    assert sum(line.startswith(b"keywords=") for line in elso_iras.splitlines()) == 1
