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


class TestLoadOrEmpty:
    """#151/7: a `load_document-ha-létezik + üres dokumentum` minta közös
    helpere — a controllerek 6 helyett 1 helyen tartalmazzák a logikát."""

    def test_missing_file_gives_empty_document(self, tmp_path):
        from picasapy.ini import load_or_empty

        doc = load_or_empty(tmp_path / ".picasa.ini")
        assert doc.serialize() == ""

    def test_existing_file_is_loaded(self, tmp_path):
        from picasapy.ini import load_or_empty

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        doc = load_or_empty(path)
        assert doc.section("a.jpg").get("star") == "yes"

    def test_roundtrip_with_save(self, tmp_path):
        from picasapy.ini import load_or_empty, save_document

        path = tmp_path / ".picasa.ini"
        doc = load_or_empty(path).with_value("a.jpg", "star", "yes")
        save_document(doc, path, backup=True)
        assert load_or_empty(path).section("a.jpg").get("star") == "yes"


class TestSourceFingerprint:
    """#137: a betöltéskori forrás-ujjlenyomat rögzíti a lemezállapotot, és a
    kulcs-szintű módosítók változatlanul megőrzik (az ütközésdetektáláshoz)."""

    def test_load_records_fingerprint_of_existing_file(self, tmp_path):
        from picasapy.ini import load_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        doc = load_document(path)
        assert doc.source_fingerprint is not None
        assert doc.source_fingerprint.exists is True
        assert doc.source_fingerprint.digest  # nem üres

    def test_missing_file_gets_no_source_fingerprint(self, tmp_path):
        from picasapy.ini import NO_SOURCE_FILE, load_or_empty

        doc = load_or_empty(tmp_path / ".picasa.ini")
        assert doc.source_fingerprint == NO_SOURCE_FILE
        assert doc.source_fingerprint.exists is False

    def test_mutation_preserves_fingerprint(self, tmp_path):
        from picasapy.ini import load_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        doc = load_document(path)
        mutated = doc.with_value("a.jpg", "caption", "x").with_removed("a.jpg", "star")
        assert mutated.source_fingerprint == doc.source_fingerprint

    def test_fingerprint_equality_ignores_mtime(self, tmp_path):
        from picasapy.ini.io import _fingerprint_of

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        first = _fingerprint_of(path)
        # Csak az mtime változik (azonos tartalom): a két ujjlenyomat egyenlő.
        import os

        os.utime(path, ns=(first.mtime_ns + 1_000_000_000, first.mtime_ns + 1_000_000_000))
        second = _fingerprint_of(path)
        assert second.mtime_ns != first.mtime_ns
        assert second == first

    def test_fingerprint_differs_on_content_change(self, tmp_path):
        from picasapy.ini.io import _fingerprint_of

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        first = _fingerprint_of(path)
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\ncaption=hi\r\n")
        assert _fingerprint_of(path) != first


class TestUpdateDocument:
    """#137: ütközésbiztos load→mutate→save — a párhuzamosan futó eredeti
    Picasa írásának lost update-je kizárva."""

    def test_simple_update_writes_file(self, tmp_path):
        from picasapy.ini import load_document, update_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        update_document(path, lambda d: d.with_value("a.jpg", "caption", "hi"))
        reloaded = load_document(path)
        assert reloaded.section("a.jpg").get("caption") == "hi"
        assert reloaded.section("a.jpg").get("star") == "yes"

    def test_creates_new_file_when_absent(self, tmp_path):
        from picasapy.ini import load_document, update_document

        path = tmp_path / ".picasa.ini"
        update_document(path, lambda d: d.with_value("a.jpg", "star", "yes"))
        assert load_document(path).section("a.jpg").get("star") == "yes"

    def test_backup_created_by_default(self, tmp_path):
        from picasapy.ini import update_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        update_document(path, lambda d: d.with_value("a.jpg", "caption", "hi"))
        assert (tmp_path / ".picasa.ini.bak").exists()

    def test_concurrent_writer_change_is_not_lost(self, tmp_path):
        """A KULCS teszt: a mutate közben egy másik író (a Picasa) frissít egy
        MÁSIK kulcsot — a végeredményben MINDKÉT módosítás megvan."""
        from picasapy.ini import load_document, update_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")

        calls = {"n": 0}

        def mutate(document):
            calls["n"] += 1
            # Az ELSŐ hívás közben egy párhuzamos író (Picasa) csillagot ad.
            if calls["n"] == 1:
                intruder = load_document(path).with_value("a.jpg", "star", "yes")
                save_document_direct(intruder, path)
            return document.with_value("a.jpg", "caption", "mine")

        from picasapy.ini import save_document as save_document_direct

        result = update_document(path, mutate)
        # Mindkettő megvan (a Picasa csillaga ÉS a mi feliratunk):
        reloaded = load_document(path)
        assert reloaded.section("a.jpg").get("star") == "yes"
        assert reloaded.section("a.jpg").get("caption") == "mine"
        assert result.section("a.jpg").get("star") == "yes"
        assert calls["n"] == 2  # egy újrajátszás történt

    def test_unchanged_file_does_not_reload(self, tmp_path):
        """Változatlan fájlnál nincs újrajátszás (nincs felesleges munka)."""
        from picasapy.ini import update_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
        calls = {"n": 0}

        def mutate(document):
            calls["n"] += 1
            return document.with_value("a.jpg", "caption", "hi")

        update_document(path, mutate)
        assert calls["n"] == 1  # pontosan egyszer

    def test_persistent_conflict_raises(self, tmp_path):
        """Ha MINDEN ablakban közbeír egy másik író, a helper nem ír felül
        csendben, hanem IniConflictError-t emel."""
        from picasapy.ini import IniConflictError, save_document, update_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")
        counter = {"n": 0}

        def mutate(document):
            # Minden hívásnál más tartalmat írunk a fájlba a mentés előtt →
            # az ujjlenyomat MINDIG eltér, sosem lesz ütközésmentes ablak.
            counter["n"] += 1
            save_document(
                document.with_value("a.jpg", "intruder", str(counter["n"])), path
            )
            return document.with_value("a.jpg", "caption", "mine")

        with pytest.raises(IniConflictError):
            update_document(path, mutate, max_retries=2)
