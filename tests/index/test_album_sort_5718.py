"""#5718: a név szerinti rendezés a Picasa bájtszintű kulcsát követi."""

from picasapy.index.album_sort import natural_name_key, sorted_album
from picasapy.index.queries import PhotoRecord


def _nev_szerint(nevek: list[str]) -> list[str]:
    return sorted(nevek, key=natural_name_key)


def _rekord(nev: str) -> PhotoRecord:
    return PhotoRecord(
        id=0,
        folder_path="/mappa",
        name=nev,
        kind="image",
        size=1,
        mtime_ns=1,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=1,
        height=1,
    )


def test_utf8_bajtok_ascii_hajtas_es_ekezetesek_sorrendje():
    nevek = ["z.jpg", "á.jpg", "A.jpg", "a.jpg", "Á.jpg"]

    assert natural_name_key("á") == (0xFFFF_FEC3, 0xFFFF_FEA1)
    assert natural_name_key("z") == (0xFFFF_FF7A,)
    assert natural_name_key("A") == (0xFFFF_FF61,)
    assert natural_name_key("á") < natural_name_key("z")
    assert natural_name_key("A") == natural_name_key("a")
    assert natural_name_key("Á") != natural_name_key("á")
    assert _nev_szerint(nevek) == [
        "Á.jpg",
        "á.jpg",
        "A.jpg",
        "a.jpg",
        "z.jpg",
    ]


def test_32_bites_modulo_vezeto_nullak_es_a_szamszakasz_utani_folytatas():
    assert natural_name_key("4294967295") == (0xFFFF_FFFF,)
    assert natural_name_key("4294967296") == (0,)
    assert _nev_szerint(["x4294967295", "x4294967296", "x1"]) == [
        "x4294967296",
        "x1",
        "x4294967295",
    ]
    assert natural_name_key("x4294967296b") == natural_name_key("x0b")
    assert natural_name_key("x0002b") == natural_name_key("x2b")
    assert natural_name_key("x2a") < natural_name_key("x0002b")
    assert natural_name_key("x2") < natural_name_key("x2a")


def test_album_nev_szerinti_novekvo_es_csokkeno_irany():
    kepek = [
        _rekord("x4294967295.jpg"),
        _rekord("x1.jpg"),
        _rekord("x4294967296.jpg"),
    ]

    assert [kep.name for kep in sorted_album(kepek, "name")] == [
        "x4294967296.jpg",
        "x1.jpg",
        "x4294967295.jpg",
    ]
    assert [
        kep.name for kep in sorted_album(kepek, "name", descending=True)
    ] == [
        "x4294967295.jpg",
        "x1.jpg",
        "x4294967296.jpg",
    ]
