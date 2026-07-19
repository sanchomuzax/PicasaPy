"""Útvonal-átírás (path remap) Windows-os db3-útvonalakról helyi útvonalakra."""

from picasapy.pmpimport import PathRemapper


class TestRemap:
    def test_windows_prefix_to_posix(self):
        remapper = PathRemapper({"C:\\Users\\anna\\Képek": "/mnt/nas/kepek"})
        assert (
            remapper.remap("C:\\Users\\anna\\Képek\\2020\\tél.jpg")
            == "/mnt/nas/kepek/2020/tél.jpg"
        )

    def test_prefix_match_is_case_insensitive(self):
        # A Windows-útvonalak kis-nagybetű-függetlenek.
        remapper = PathRemapper({"c:\\users\\ANNA": "/home/anna"})
        assert remapper.remap("C:\\Users\\anna\\a.jpg") == "/home/anna/a.jpg"

    def test_longest_prefix_wins(self):
        remapper = PathRemapper(
            {
                "C:\\Képek": "/mnt/rossz",
                "C:\\Képek\\2020": "/mnt/jo",
            }
        )
        assert remapper.remap("C:\\Képek\\2020\\a.jpg") == "/mnt/jo/a.jpg"

    def test_prefix_matches_whole_component_only(self):
        remapper = PathRemapper({"C:\\Kep": "/mnt/x"})
        assert remapper.remap("C:\\Képek\\a.jpg") is None

    def test_unmatched_returns_none(self):
        remapper = PathRemapper({"D:\\Fotók": "/mnt/fotok"})
        assert remapper.remap("C:\\Egyéb\\b.jpg") is None

    def test_trailing_separators_are_tolerated(self):
        remapper = PathRemapper({"C:\\Képek\\": "/mnt/kepek/"})
        assert remapper.remap("C:\\Képek\\a.jpg") == "/mnt/kepek/a.jpg"

    def test_exact_prefix_maps_to_target(self):
        remapper = PathRemapper({"C:\\Képek": "/mnt/kepek"})
        assert remapper.remap("C:\\Képek\\") == "/mnt/kepek"
