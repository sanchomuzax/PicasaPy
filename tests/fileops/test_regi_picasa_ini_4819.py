"""#4819: csak régi `Picasa.ini`-s mappában a fájlművelet viszi a bejegyzést.

A régi fájl olvasási forrás: az új `.picasa.ini` a tartalmával együtt jön
létre, a régi `Picasa.ini` bájtra azonos marad.
"""

from picasapy.fileops import copy_photo, move_photo, rename_photo
from picasapy.ini import load_document

_REGI = b"[a.jpg]\r\nstar=yes\r\ncaption=regi felirat\r\n\r\n[b.jpg]\r\nstar=yes\r\n"


def _mappa_regi_inivel(gyoker, nev):
    mappa = gyoker / nev
    mappa.mkdir()
    (mappa / "a.jpg").write_bytes(b"kep")
    (mappa / "Picasa.ini").write_bytes(_REGI)
    return mappa


def test_atnevezes_viszi_a_regi_bejegyzest(tmp_path):
    mappa = _mappa_regi_inivel(tmp_path, "m")
    rename_photo(mappa / "a.jpg", "c.jpg")
    uj = load_document(mappa / ".picasa.ini")
    assert uj.section("a.jpg") is None
    assert uj.section("c.jpg").get("caption") == "regi felirat"
    assert uj.section("b.jpg").get("star") == "yes"
    assert (mappa / "Picasa.ini").read_bytes() == _REGI


def test_athelyezes_viszi_a_regi_bejegyzest(tmp_path):
    mappa = _mappa_regi_inivel(tmp_path, "m")
    cel = tmp_path / "cel"
    cel.mkdir()
    move_photo(mappa / "a.jpg", cel)
    uj = load_document(cel / ".picasa.ini")
    assert uj.section("a.jpg").get("caption") == "regi felirat"
    assert (mappa / "Picasa.ini").read_bytes() == _REGI


def test_masolas_viszi_a_regi_bejegyzest(tmp_path):
    mappa = _mappa_regi_inivel(tmp_path, "m")
    cel = tmp_path / "cel"
    cel.mkdir()
    copy_photo(mappa / "a.jpg", cel)
    uj = load_document(cel / ".picasa.ini")
    assert uj.section("a.jpg").get("caption") == "regi felirat"
    assert (mappa / "Picasa.ini").read_bytes() == _REGI
