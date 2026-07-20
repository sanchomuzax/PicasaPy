""".picasa.ini fájl-I/O: kódolás-felismerés, atomikus mentés — legacy
(nem UTF-8) fájlok kezelése (#133)."""

import pytest

from picasapy.ini import load_document, parse_document, save_document
from picasapy.ini.io import IniSaveError


class TestLoadLegacyEncoding:
    def test_latin1_fallback_on_invalid_utf8(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        # CP1250 "ő" bájtja (0xF5) UTF-8-ként érvénytelen sorozat.
        path.write_bytes("[a.jpg]\r\nstar=yes\r\n".encode("utf-8") + b"\xf5\r\n")
        doc = load_document(path)
        assert doc.encoding == "latin-1"


class TestSaveLegacyEncoding:
    """#133: a latin-1-ként betöltött (valójában CP1250) fájlba ékezetes
    (ő/ű) szöveg írásakor a `serialize().encode("latin-1")` kezeletlen
    UnicodeEncodeError-t dobott — a mentés elveszett, hibajelzés nélkül."""

    def test_hungarian_accents_do_not_crash_save(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        # A 0xF5 bájt (CP1250 "ő") UTF-8-ként érvénytelen — a betöltés
        # így latin-1-re esik vissza (ez a valós legacy-fájl helyzete).
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n; \xf5\r\n")
        doc = load_document(path)
        assert doc.encoding == "latin-1"
        updated = doc.with_value("a.jpg", "caption", "őszi túra — árvíztűrő tükörfúrógép")
        # Nem szabad UnicodeEncodeError-t dobnia — a mentésnek sikerülnie kell.
        save_document(updated, path)
        reloaded = load_document(path)
        assert reloaded.section("a.jpg").get("caption") == (
            "őszi túra — árvíztűrő tükörfúrógép"
        )

    def test_switches_to_utf8_when_latin1_cannot_encode(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        doc = load_document(path)
        updated = doc.with_value("a.jpg", "caption", "őű")
        save_document(updated, path)
        reloaded = load_document(path)
        # A dokumentált szabály: ha a legacy kódolás nem tudja kifejezni az
        # új szöveget, a mentés UTF-8-ra vált.
        assert reloaded.encoding == "utf-8"

    def test_ascii_only_legacy_content_keeps_latin1(self, tmp_path):
        # Ha nincs olyan karakter, ami nem fér a latin-1-be, a kódolás nem
        # változik (kevesebb felesleges byte-eltérés a régi Picasa felé).
        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n; \xf5\r\n")
        doc = load_document(path)
        assert doc.encoding == "latin-1"
        updated = doc.with_value("a.jpg", "caption", "sima szoveg")
        save_document(updated, path)
        reloaded = load_document(path)
        assert reloaded.encoding == "latin-1"

    def test_unencodable_utf8_raises_explicit_error(self, monkeypatch, tmp_path):
        # Ha VALÓBAN nem menthető (még UTF-8-ként sem), a hívó explicit
        # hibát kapjon, ne csendben vesszen el az adat.
        path = tmp_path / ".picasa.ini"
        doc = parse_document("[a.jpg]\nstar=yes\n")

        # A serialize()-t úgy cseréljük, hogy encode()-kor mindig hibázzon —
        # a valódi (nem szimulált) eset ritka, de a hibaútnak működnie kell.
        class _BadStr(str):
            def encode(self, *args, **kwargs):
                raise UnicodeEncodeError("utf-8", "x", 0, 1, "teszt")

        monkeypatch.setattr(type(doc), "serialize", lambda self: _BadStr("x"))
        with pytest.raises(IniSaveError):
            save_document(doc, path)
