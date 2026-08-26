"""Pontos (bitre azonos) duplikátum-keresés."""

from picasapy.dedup import exact as exact_module
from picasapy.dedup.exact import file_content_hash, group_exact_duplicates
from picasapy.dedup.fastkey import FEJ_MERET, picasa_fast_key

from support.jpeg_factory import make_jpeg


class TestFileContentHash:
    def test_identical_bytes_same_hash(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"ugyanaz a tartalom")
        b.write_bytes(b"ugyanaz a tartalom")
        assert file_content_hash(a) == file_content_hash(b)

    def test_different_bytes_different_hash(self, tmp_path):
        a = tmp_path / "a.jpg"
        b = tmp_path / "b.jpg"
        a.write_bytes(b"elso tartalom")
        b.write_bytes(b"masodik tartalom")
        assert file_content_hash(a) != file_content_hash(b)

    def test_missing_file_returns_none(self, tmp_path):
        assert file_content_hash(tmp_path / "nincs.jpg") is None


class TestGroupExactDuplicates:
    def test_two_identical_files_form_a_group(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())

        groups = group_exact_duplicates((original, copy))

        assert len(groups) == 1
        assert groups[0].paths == tuple(sorted((original, copy), key=str))

    def test_unique_files_produce_no_group(self, tmp_path):
        one = make_jpeg(tmp_path / "egy.jpg", size=(40, 20))
        two = make_jpeg(tmp_path / "ketto.jpg", size=(41, 20))  # eltérő méret/tartalom

        assert group_exact_duplicates((one, two)) == ()

    def test_different_size_never_hashed_as_pair(self, tmp_path):
        small = tmp_path / "kicsi.bin"
        big = tmp_path / "nagy.bin"
        small.write_bytes(b"x" * 10)
        big.write_bytes(b"x" * 20)
        assert group_exact_duplicates((small, big)) == ()

    def test_three_way_duplicate_single_group(self, tmp_path):
        payload = b"harmas duplikatum"
        paths = []
        for name in ("c.jpg", "a.jpg", "b.jpg"):
            path = tmp_path / name
            path.write_bytes(payload)
            paths.append(path)

        groups = group_exact_duplicates(paths)

        assert len(groups) == 1
        assert groups[0].paths == tuple(sorted(paths, key=str))

    def test_input_sequence_not_mutated(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        copy = tmp_path / "masolat.jpg"
        copy.write_bytes(original.read_bytes())
        paths = [copy, original]
        before = list(paths)

        group_exact_duplicates(paths)

        assert paths == before

    def test_deterministic_group_order(self, tmp_path):
        payload_1 = b"elso duplikatum part"
        payload_2 = b"masodik duplikatum part"
        names_and_payloads = [
            ("z1.jpg", payload_1),
            ("a1.jpg", payload_1),
            ("z2.jpg", payload_2),
            ("a2.jpg", payload_2),
        ]
        paths = []
        for name, payload in names_and_payloads:
            path = tmp_path / name
            path.write_bytes(payload)
            paths.append(path)

        forward = group_exact_duplicates(paths)
        backward = group_exact_duplicates(list(reversed(paths)))

        assert forward == backward
        assert [group.paths[0].name for group in forward] == ["a1.jpg", "a2.jpg"]

    def test_missing_file_is_skipped_not_raised(self, tmp_path):
        original = make_jpeg(tmp_path / "eredeti.jpg", size=(40, 20))
        assert group_exact_duplicates((original, tmp_path / "nincs.jpg")) == ()


class TestGyorskulcsEloszuro:
    """#1481 — a Picasa fej+farok kulcsa mint MÁSODIK előszűrő.

    A méret-előszűrő után a gyors kulcs dönti el, kell-e egyáltalán teljes
    tartalom-hash. A teljes SHA-256 ettől nem tűnik el: az ütközés
    lehetősége miatt a kulcs-egyezőket továbbra is bitre összevetjük."""

    def test_azonos_meret_elteru_kulcs_nem_hashel_teljesen(
        self, tmp_path, monkeypatch
    ):
        """Azonos méretű, de eltérő fejű fájlokra NEM indul teljes olvasás."""
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(b"A" + b"\x00" * 50000)
        b.write_bytes(b"B" + b"\x00" * 50000)

        eredeti = exact_module.file_content_hash
        hivasok = []

        def figyelo(path):
            hivasok.append(path)
            return eredeti(path)

        monkeypatch.setattr(exact_module, "file_content_hash", figyelo)

        assert group_exact_duplicates((a, b)) == ()
        assert hivasok == []

    def test_kulcs_utkozes_eseten_a_teljes_hash_dont(self, tmp_path):
        """Azonos méret + azonos fej/farok + eltérő közép: NEM másodpéldány.

        A Picasa gyors kulcsa itt ütközne; a mi rétegünk a teljes
        tartalom-hash-sel cáfolja meg. Ez a réteg dokumentált ígérete
        ("bitre azonos"), és a törlést/import-kihagyást ez védi."""
        fej = bytes((i * 37 + 11) & 0xFF for i in range(FEJ_MERET))
        farok = fej[::-1]
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(fej + b"\x00" * 5000 + farok)
        b.write_bytes(fej + b"\xff" * 5000 + farok)
        assert picasa_fast_key(a) == picasa_fast_key(b)  # a kulcs tényleg ütközik

        assert group_exact_duplicates((a, b)) == ()

    def test_valodi_masodpeldanyt_tovabbra_is_megtalal(self, tmp_path):
        """Az előszűrő nem ejtheti el az igazi másodpéldányokat."""
        payload = bytes((i * 13 + 7) & 0xFF for i in range(70000))
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        a.write_bytes(payload)
        b.write_bytes(payload)

        groups = group_exact_duplicates((a, b))

        assert len(groups) == 1
        assert groups[0].paths == (a, b)

    def test_haladas_jelzes_minden_kepre_lepked(self, tmp_path):
        """A gyors kulccsal kiszűrt fájlok is beleszámítanak a haladásba."""
        a = tmp_path / "a.bin"
        b = tmp_path / "b.bin"
        c = tmp_path / "c.bin"
        a.write_bytes(b"A" + b"\x00" * 50000)
        b.write_bytes(b"B" + b"\x00" * 50000)
        c.write_bytes(b"C" * 7)

        latott = []
        group_exact_duplicates((a, b, c), progress=latott.append)

        assert latott[-1] == 3
