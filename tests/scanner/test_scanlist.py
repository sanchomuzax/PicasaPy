from picasapy.scanner import read_scan_list, write_scan_list


def test_scanlist_round_trip_keeps_three_ordered_sections(tmp_path):
    path = tmp_path / "scanlist.txt"
    write_scan_list(path, ("/once",), ("/excluded",), ("/always",))

    assert path.read_text(encoding="utf-8") == (
        "/once\n-/excluded\n+/always\n"
    )
    assert read_scan_list(path) == (
        ("/once",),
        ("/excluded",),
        ("/always",),
    )


def test_missing_scanlist_is_empty(tmp_path):
    assert read_scan_list(tmp_path / "missing.txt") == ((), (), ())
