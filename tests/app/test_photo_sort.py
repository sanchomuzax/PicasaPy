"""#1436: a mappa-blokkon belüli képrendezés magja (`app/photo_sort.py`).

Qt nélküli, gyors egységpróbák. A lényeg, amit KIMOND: a függvény a
MAPPA-BLOKKON BELÜL rendez — a blokkok (és így a mappák) sorrendje sosem
mozdul —, és az alapirány NÖVEKVŐ.
"""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.app.photo_sort import (
    DEFAULT_SORT_MODE,
    coerce_reverse_flag,
    coerce_sort_mode,
    photo_date,
    sort_folder_blocks,
)


@dataclass(frozen=True)
class _Photo:
    folder_path: str
    name: str
    taken_at: str | None = None
    size: int = 0
    mtime_ns: int = 0


def _names(records) -> list[str]:
    return [r.name for r in records]


def _folders(records) -> list[str]:
    seen: list[str] = []
    for record in records:
        if not seen or seen[-1] != record.folder_path:
            seen.append(record.folder_path)
    return seen


_BLOKKOK = (
    _Photo("/a", "a3.jpg", "2024-01-01T00:00:00", size=30),
    _Photo("/a", "a1.jpg", "2010-01-01T00:00:00", size=10),
    _Photo("/a", "a2.jpg", "2018-01-01T00:00:00", size=20),
    _Photo("/b", "b2.jpg", "2005-01-01T00:00:00", size=200),
    _Photo("/b", "b1.jpg", "2030-01-01T00:00:00", size=100),
)


class TestAHatokorABlokkonBelul:
    def test_a_datum_a_blokkon_belul_rendez_novekvo_sorrendben(self):
        assert _names(sort_folder_blocks(_BLOKKOK, "date")) == [
            "a1.jpg",
            "a2.jpg",
            "a3.jpg",
            "b2.jpg",
            "b1.jpg",
        ]

    def test_a_blokkok_sorrendje_egyik_szempontnal_sem_mozdul(self):
        for mode in ("date", "name", "size"):
            for reverse in (False, True):
                rendezett = sort_folder_blocks(_BLOKKOK, mode, reverse)
                assert _folders(rendezett) == ["/a", "/b"], (mode, reverse)

    def test_az_azonos_mappa_ket_kulon_futama_kulon_blokk_marad(self):
        # a rács így rajzolja: minden összefüggő futam SAJÁT fejlécet kap
        futamok = (
            _Photo("/a", "a2.jpg", "2024-01-01T00:00:00"),
            _Photo("/b", "b1.jpg", "2000-01-01T00:00:00"),
            _Photo("/a", "a1.jpg", "2010-01-01T00:00:00"),
        )
        assert _names(sort_folder_blocks(futamok, "date")) == [
            "a2.jpg",
            "b1.jpg",
            "a1.jpg",
        ]


class TestAzIrany:
    def test_a_forditas_megforditja_a_blokkon_beluli_sorrendet(self):
        assert _names(sort_folder_blocks(_BLOKKOK, "date", reverse=True)) == [
            "a3.jpg",
            "a2.jpg",
            "a1.jpg",
            "b1.jpg",
            "b2.jpg",
        ]

    def test_a_meret_a_legkisebbtol_indul(self):
        assert _names(sort_folder_blocks(_BLOKKOK, "size")) == [
            "a1.jpg",
            "a2.jpg",
            "a3.jpg",
            "b1.jpg",
            "b2.jpg",
        ]

    def test_a_nev_kis_nagybetu_tureen_novekvo(self):
        vegyes = (
            _Photo("/a", "Beta.jpg"),
            _Photo("/a", "alfa.jpg"),
        )
        assert _names(sort_folder_blocks(vegyes, "name")) == [
            "alfa.jpg",
            "Beta.jpg",
        ]


class TestADatumForrasa:
    """EXIF-felvételi dátum az elsődleges; hiányában a FÁJL ideje."""

    def test_az_exif_datum_nyer(self):
        record = _Photo("/a", "x.jpg", "2001-02-03T04:05:06", mtime_ns=0)
        assert photo_date(record) == "2001-02-03T04:05:06"

    def test_exif_nelkul_a_fajlido_dontheti_el_a_sorrendet(self):
        regi = _Photo("/a", "regi.jpg", None, mtime_ns=1_000_000_000)
        uj = _Photo("/a", "uj.jpg", None, mtime_ns=2_000_000_000_000_000_000)
        assert _names(sort_folder_blocks((uj, regi), "date")) == [
            "regi.jpg",
            "uj.jpg",
        ]


class TestVisszaesesek:
    def test_ismeretlen_szempont_a_fajlnevre_esik_vissza(self):
        assert coerce_sort_mode("csillagok") == DEFAULT_SORT_MODE
        assert coerce_sort_mode(None) == DEFAULT_SORT_MODE
        assert _names(sort_folder_blocks(_BLOKKOK, "csillagok"))[:3] == [
            "a1.jpg",
            "a2.jpg",
            "a3.jpg",
        ]

    def test_a_mentett_forditas_szovegkent_is_ertheto(self):
        assert coerce_reverse_flag("true") is True
        assert coerce_reverse_flag("1") is True
        assert coerce_reverse_flag("false") is False
        assert coerce_reverse_flag(None) is False

    def test_ures_lista_nem_hibazik(self):
        assert sort_folder_blocks((), "date") == ()

    def test_a_bemenetet_nem_modositja(self):
        eredeti = list(_BLOKKOK)
        sort_folder_blocks(_BLOKKOK, "date")
        assert list(_BLOKKOK) == eredeti
