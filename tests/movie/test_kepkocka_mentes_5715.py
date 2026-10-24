"""#5715: a videóból mentett képkocka projektjelölése és JPEG-minősége."""

from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image

from picasapy.ini import (
    INI_NAME,
    PROJECTS_CATEGORY,
    load_document,
    read_folder_category,
)
from picasapy.movie.frame_capture import mentsd_a_kepkockat


def _q85_tabla(alap: tuple[int, ...]) -> list[int]:
    skala = 200 - 2 * 85
    return [max(1, min(255, (ertek * skala + 50) // 100)) for ertek in alap]


class TestKepkockaMentes5715:
    def test_uj_mappa_projektjelolot_kap_a_meglevo_ini_valtozatlan(self, tmp_path):
        kep = np.full((12, 16, 3), (33, 121, 207), dtype=np.uint8)

        uj_mappa = tmp_path / "uj"
        mentsd_a_kepkockat(kep, uj_mappa, "uj-klip")

        assert read_folder_category(load_document(uj_mappa / INI_NAME)) == (
            PROJECTS_CATEGORY
        )
        from picasapy.index import open_index, project_folders, sync_tree

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, tmp_path)
            assert any(
                folder.path == str(uj_mappa) for folder in project_folders(conn)
            )

        letezo_mappa = tmp_path / "letezo"
        letezo_mappa.mkdir()
        ini = letezo_mappa / INI_NAME
        eredeti_ini = b"[Picasa]\nP2category=Folders on Disk\nname=Korabbi\n"
        ini.write_bytes(eredeti_ini)

        mentsd_a_kepkockat(kep, letezo_mappa, "letezo-klip")

        assert ini.read_bytes() == eredeti_ini

    def test_a_kimeneti_jpeg_kvantalo_tabla_85_os_minosegu(self, tmp_path):
        kep = np.zeros((32, 32, 3), dtype=np.uint8)
        kep[::2, ::2] = (255, 40, 180)
        cel = mentsd_a_kepkockat(kep, tmp_path, "q85")

        with Image.open(BytesIO(cel.read_bytes())) as jpeg:
            tablazatok = jpeg.quantization

        luma_alap = (
            16, 11, 10, 16, 24, 40, 51, 61,
            12, 12, 14, 19, 26, 58, 60, 55,
            14, 13, 16, 24, 40, 57, 69, 56,
            14, 17, 22, 29, 51, 87, 80, 62,
            18, 22, 37, 56, 68, 109, 103, 77,
            24, 35, 55, 64, 81, 104, 113, 92,
            49, 64, 78, 87, 103, 121, 120, 101,
            72, 92, 95, 98, 112, 100, 103, 99,
        )
        chroma_alap = (
            17, 18, 24, 47, 99, 99, 99, 99,
            18, 21, 26, 66, 99, 99, 99, 99,
            24, 26, 56, 99, 99, 99, 99, 99,
            47, 66, 99, 99, 99, 99, 99, 99,
            99, 99, 99, 99, 99, 99, 99, 99,
            99, 99, 99, 99, 99, 99, 99, 99,
            99, 99, 99, 99, 99, 99, 99, 99,
            99, 99, 99, 99, 99, 99, 99, 99,
        )

        assert tablazatok[0] == _q85_tabla(luma_alap)
        assert tablazatok[1] == _q85_tabla(chroma_alap)
