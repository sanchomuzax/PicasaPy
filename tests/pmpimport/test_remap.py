"""PathRemapper: Windows-útvonalak átírása helyi (POSIX) megfelelőre (#1)."""

from picasapy.pmpimport.remap import PathRemapper


class TestPathRemapper:
    def test_basic_prefix_remap(self):
        remapper = PathRemapper.from_dict(
            {"C:\\Users\\anna\\Pictures": "/mnt/nas/fotok"}
        )
        assert (
            remapper.remap("C:\\Users\\anna\\Pictures\\2024\\IMG_0001.jpg")
            == "/mnt/nas/fotok/2024/IMG_0001.jpg"
        )

    def test_case_insensitive_prefix_match(self):
        # a Windows-fájlrendszer kis-nagybetű-tűrő; a WatchedFolders.txt
        # élesben kisbetűs alakot is tartalmaz (MEMORY.md tanulság)
        remapper = PathRemapper.from_dict({"c:\\users\\anna\\pictures": "/mnt/nas"})
        assert (
            remapper.remap("C:\\Users\\Anna\\Pictures\\a.jpg") == "/mnt/nas/a.jpg"
        )

    def test_remainder_case_preserved(self):
        # a prefix-egyezés kis-nagybetű-tűrő, de a fájlnév kis-nagybetűi
        # nem sérülhetnek
        remapper = PathRemapper.from_dict({"C:\\kepek": "/mnt/nas"})
        assert remapper.remap("C:\\kepek\\IMG_0001.JPG") == "/mnt/nas/IMG_0001.JPG"

    def test_longest_prefix_wins(self):
        remapper = PathRemapper.from_dict(
            {
                "C:\\Users\\anna": "/home/anna",
                "C:\\Users\\anna\\Pictures": "/mnt/nas/fotok",
            }
        )
        assert (
            remapper.remap("C:\\Users\\anna\\Pictures\\a.jpg")
            == "/mnt/nas/fotok/a.jpg"
        )
        assert remapper.remap("C:\\Users\\anna\\doc.txt") == "/home/anna/doc.txt"

    def test_exact_prefix_match(self):
        remapper = PathRemapper.from_dict({"C:\\kepek": "/mnt/nas"})
        assert remapper.remap("C:\\kepek") == "/mnt/nas"

    def test_no_match_returns_none(self):
        remapper = PathRemapper.from_dict({"C:\\kepek": "/mnt/nas"})
        assert remapper.remap("D:\\mashol\\a.jpg") is None

    def test_partial_component_does_not_match(self):
        # a "C:\kepek2" NEM a "C:\kepek" alá tartozik
        remapper = PathRemapper.from_dict({"C:\\kepek": "/mnt/nas"})
        assert remapper.remap("C:\\kepek2\\a.jpg") is None

    def test_trailing_backslash_in_prefix_tolerated(self):
        remapper = PathRemapper.from_dict({"C:\\kepek\\": "/mnt/nas"})
        assert remapper.remap("C:\\kepek\\a.jpg") == "/mnt/nas/a.jpg"

    def test_casefold_length_change_does_not_shift_remainder(self):
        # ß→ss a casefold során hosszabb lesz — ha a levágás a foldolt
        # prefix HOSSZÁVAL, de az EREDETI (nem foldolt) útvonalon történik,
        # elcsúszik: az "alma.jpg" első karaktere lemarad ("lma.jpg" lesz)
        remapper = PathRemapper.from_dict(
            {"C:\\Straße\\Straße": "/mnt/nas"}
        )
        assert (
            remapper.remap("C:\\Straße\\Straße\\alma.jpg")
            == "/mnt/nas/alma.jpg"
        )
