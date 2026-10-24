"""#4599 (ADR-016): az album rendezési kulcsai és a hely szerinti sorrend.

A kulcsok a `docs/specs/album-sorrend.md` 2.4 szakaszából valók: Név =
UTF-8 bájtokon természetes összevetés (32 bites számérték modulo, ASCII
`A-Z` kisbetűsítése, előjeles nem-számjegy kulcs), Dátum = metaadat-dátum
(egyenlőségnél név), Méret = fájlméret; Shift = csökkenő, Fordított = kulcs
nélkül megfordít.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.album_sort import natural_name_key, new_places, sorted_album
from picasapy.index.albums import album_photos
from support.jpeg_factory import make_jpeg

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"


def _nev_szerint(nevek):
    return sorted(nevek, key=natural_name_key)


class TestTermeszetesNev:
    def test_a_szamjegy_sorozat_szamkent_hasonlit(self):
        assert _nev_szerint(["kep10.jpg", "kep2.jpg", "kep1.jpg"]) == [
            "kep1.jpg", "kep2.jpg", "kep10.jpg",
        ]

    def test_az_ascii_nagybetu_kisbetukent_hasonlit(self):
        assert _nev_szerint(["b.jpg", "A.jpg", "c.jpg"]) == ["A.jpg", "b.jpg", "c.jpg"]

    def test_a_kis_szamszakasz_a_peldabeli_bajtkulcsok_elott_all(self):
        assert _nev_szerint(["a.jpg", "9.jpg", "_.jpg", "~.jpg"]) == [
            "9.jpg", "_.jpg", "a.jpg", "~.jpg",
        ]

    def test_az_egyik_a_masik_elotagja_a_rovidebb_elol(self):
        assert _nev_szerint(["kep.jpg", "ke", "kep"]) == [
            "ke", "kep", "kep.jpg",
        ]

    def test_nem_ascii_betu_nem_kisbetusodik(self):
        # az eredeti csak az ASCII A–Z-t kisbetűsíti: az `É` nem esik az `é` mellé
        assert natural_name_key("É") != natural_name_key("é")

    def test_utf8_bajtok_szerint_rendez_az_ascii_es_az_ekezetes_neveket(self):
        assert _nev_szerint(["á", "ő", "Z", "a", "z"]) == [
            "á", "ő", "a", "Z", "z",
        ]

    def test_a_szamszakasz_32_bites_modulo_utan_hasonlit(self):
        assert _nev_szerint(["x4294967295", "xz", "x4294967296", "x1"]) == [
            "x4294967296",
            "x1",
            "xz",
            "x4294967295",
        ]

    def test_a_nagy_szam_es_a_bajtkulcs_unsigned_erteke_osszevetheto(self):
        assert _nev_szerint(["x4294967295", "xz"]) == ["xz", "x4294967295"]

    def test_vezeto_nullak_es_azonos_maradek_utani_folytatas(self):
        assert natural_name_key("x0002") == natural_name_key("x2")
        assert _nev_szerint(
            ["x0002b", "x4294967296b", "x02", "x0a", "x2a"]
        ) == ["x0a", "x4294967296b", "x02", "x2a", "x0002b"]

    def test_nagy_szamsorozat_sem_dob(self):
        assert natural_name_key("9" * 40 + ".jpg") > natural_name_key("1.jpg")


def _rekord(nev, *, mappa="/m", meret=10, taken_at=None, mtime_ns=1):
    from picasapy.index.queries import PhotoRecord

    return PhotoRecord(
        id=0, folder_path=mappa, name=nev, kind="image", size=meret,
        mtime_ns=mtime_ns,
        star=False, caption=None, keywords=None, rotate_steps=0, filters=None,
        taken_at=taken_at, orientation=1, width=1, height=1,
    )


class TestRendezes:
    def test_nev_novekvo_es_shifttel_csokkeno(self):
        kepek = [_rekord("b2.jpg"), _rekord("b10.jpg"), _rekord("a.jpg")]
        assert [k.name for k in sorted_album(kepek, "name")] == [
            "a.jpg", "b2.jpg", "b10.jpg",
        ]
        assert [k.name for k in sorted_album(kepek, "name", descending=True)] == [
            "b10.jpg", "b2.jpg", "a.jpg",
        ]

    def test_meret_novekvo_es_csokkeno(self):
        kepek = [_rekord("a", meret=30), _rekord("b", meret=10), _rekord("c", meret=20)]
        assert [k.name for k in sorted_album(kepek, "size")] == ["b", "c", "a"]
        assert [k.name for k in sorted_album(kepek, "size", descending=True)] == [
            "a", "c", "b",
        ]

    def test_datum_novekvo_a_legregebbi_elol_egyenlosegnel_nev(self):
        kepek = [
            _rekord("z", taken_at="2020-01-02T10:00:00"),
            _rekord("b", taken_at="2020-01-01T10:00:00"),
            _rekord("a", taken_at="2020-01-01T10:00:00"),
        ]
        assert [k.name for k in sorted_album(kepek, "date")] == ["a", "b", "z"]
        assert [k.name for k in sorted_album(kepek, "date", descending=True)] == [
            "z", "b", "a",
        ]

    def test_datum_nelkuli_kep_a_fajl_idejevel_rendezodik_nem_az_elejen(self):
        # spec 4.1 / pmp-database 10.3: EXIF-dátum hiányában a (befagyasztott)
        # fájlidő a tartalék — a dátum nélküli kép nem kerülhet a lista elejére
        kepek = [
            _rekord("exif", taken_at="2020-01-01T10:00:00"),
            _rekord("fajl_regi", mtime_ns=1_000_000_000),  # 1970
            _rekord("fajl_uj", mtime_ns=2_000_000_000_000_000_000),  # 2033
        ]
        assert [k.name for k in sorted_album(kepek, "date")] == [
            "fajl_regi", "exif", "fajl_uj",
        ]

    def test_romlott_fajlido_a_lista_vegere_kerul_es_nem_dob(self):
        kepek = [
            _rekord("romlott", mtime_ns=10**26),
            _rekord("exif", taken_at="2020-01-01T10:00:00"),
        ]
        assert [k.name for k in sorted_album(kepek, "date")] == ["exif", "romlott"]

    def test_fordított_kulcs_nelkul_megfordit_shifttel_is(self):
        kepek = [_rekord("c"), _rekord("a"), _rekord("b")]
        # a tárolt sorrend (c, a, b) fordítottja
        assert [k.name for k in sorted_album(kepek, "reverse")] == ["b", "a", "c"]
        assert [k.name for k in sorted_album(kepek, "reverse", descending=True)] == [
            "b", "a", "c",
        ]

    def test_ismeretlen_modra_hangos_hiba(self):
        with pytest.raises(ValueError):
            sorted_album([_rekord("a"), _rekord("b")], "szin")

    def test_tobb_mappara_szoro_album_osszefesulve_rendezodik(self):
        kepek = [
            _rekord("c.jpg", mappa="/egy"),
            _rekord("a.jpg", mappa="/ketto"),
            _rekord("b.jpg", mappa="/egy"),
        ]
        rendezett = sorted_album(kepek, "name")
        assert [(k.folder_path, k.name) for k in rendezett] == [
            ("/ketto", "a.jpg"), ("/egy", "b.jpg"), ("/egy", "c.jpg"),
        ]
        assert new_places(rendezett) == {
            ("/ketto", "a.jpg"): 1.0, ("/egy", "b.jpg"): 2.0, ("/egy", "c.jpg"): 3.0,
        }


@pytest.fixture
def konyvtar(tmp_path):
    root = tmp_path / "kepek"
    (root / "egy").mkdir(parents=True)
    (root / "ketto").mkdir()
    for nev in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / "egy" / nev)
    make_jpeg(root / "ketto" / "d.jpg")
    (root / "egy" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\nname=X\ntoken={_TOKEN}\n"
        f"[a.jpg]\nalbums={_TOKEN}\nalbumorder={_TOKEN}:3.0\n"
        f"[b.jpg]\nalbums={_TOKEN}\nalbumorder={_TOKEN}:1.0\n"
        f"[c.jpg]\nalbums={_TOKEN}\n",
        encoding="utf-8",
    )
    (root / "ketto" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\nname=X\ntoken={_TOKEN}\n"
        f"[d.jpg]\nalbums={_TOKEN}\nalbumorder={_TOKEN}:2.0\n",
        encoding="utf-8",
    )
    return root


class TestHelySzerintiSorrend:
    def test_hely_szerint_a_helynelkuliek_a_vegen(self, tmp_path, konyvtar):
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, konyvtar)
            assert [r.name for r in album_photos(conn, _TOKEN)] == [
                "b.jpg", "d.jpg", "a.jpg", "c.jpg",
            ]

    def test_hely_nelkuli_album_a_mai_rend_mappa_majd_nev(self, tmp_path, konyvtar):
        for ini in konyvtar.rglob(".picasa.ini"):
            szoveg = ini.read_text(encoding="utf-8")
            ini.write_text(
                "\n".join(
                    sor for sor in szoveg.split("\n") if not sor.startswith("albumorder=")
                ),
                encoding="utf-8",
            )
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, konyvtar)
            assert [r.name for r in album_photos(conn, _TOKEN)] == [
                "a.jpg", "b.jpg", "c.jpg", "d.jpg",
            ]

    def test_elarvult_es_romlott_par_nem_befolyasolja_a_sorrendet(
        self, tmp_path, konyvtar
    ):
        ini = konyvtar / "egy" / ".picasa.ini"
        szoveg = ini.read_text(encoding="utf-8").replace(
            f"albumorder={_TOKEN}:3.0", "albumorder=ffffffffffffffffffffffffffffffff:1.0,x:y"
        )
        ini.write_text(szoveg, encoding="utf-8")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, konyvtar)
            assert [r.name for r in album_photos(conn, _TOKEN)] == [
                "b.jpg", "d.jpg", "a.jpg", "c.jpg",
            ]

    def test_eltero_kis_nagybetus_szakasznev_is_megtalalja_a_helyet(self, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        for nev in ("img_1.jpg", "img_2.jpg"):
            make_jpeg(root / nev)
        (root / ".picasa.ini").write_text(
            f"[.album:{_TOKEN}]\nname=X\ntoken={_TOKEN}\n"
            f"[IMG_1.JPG]\nalbums={_TOKEN}\nalbumorder={_TOKEN}:9.0\n"
            f"[img_2.jpg]\nalbums={_TOKEN}\nalbumorder={_TOKEN}:1.0\n",
            encoding="utf-8",
        )
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
            assert conn.execute(
                "SELECT place FROM photo_albums pa JOIN photos p ON p.id = pa.photo_id"
                " WHERE p.name = 'img_1.jpg'"
            ).fetchone()[0] == 9.0
            assert [r.name for r in album_photos(conn, _TOKEN)] == [
                "img_2.jpg", "img_1.jpg",
            ]

    def test_egyenlo_helynel_utvonal_majd_nev(self, tmp_path, konyvtar):
        for ini in konyvtar.rglob(".picasa.ini"):
            szoveg = ini.read_text(encoding="utf-8")
            for hely in ("3.0", "1.0", "2.0"):
                szoveg = szoveg.replace(f"{_TOKEN}:{hely}", f"{_TOKEN}:5.0")
            ini.write_text(szoveg, encoding="utf-8")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, konyvtar)
            assert [r.name for r in album_photos(conn, _TOKEN)] == [
                "a.jpg", "b.jpg", "d.jpg", "c.jpg",
            ]
