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
    """#137/#4471: belső szerializálás és külső írások best-effort észlelése."""

    def test_external_write_between_fingerprint_check_and_save(self, monkeypatch, tmp_path):
        """A külső író a sikeres ellenőrzés után, a mentés előtt módosít.

        Ez a determinisztikus TOCTOU-próba megmutatja, hogy a fingerprint
        ellenőrzése nem compare-and-swap: a közbeírt változás elveszhet.
        """
        from picasapy.ini import load_document, update_document
        from picasapy.ini import io as ini_io

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")
        real_save_document = ini_io.save_document
        external_write_happened = False

        def external_write_then_save(document, target, *, backup=False, in_place=False):
            nonlocal external_write_happened
            if target == path and not external_write_happened:
                # A fogantyúban az update_document fingerprint-ellenőrzése
                # már sikeres; a valódi save_document még nem kezdett írni.
                path.write_bytes(b"[a.jpg]\r\nstar=yes\r\n")
                external_write_happened = True
            return real_save_document(
                document, target, backup=backup, in_place=in_place
            )

        monkeypatch.setattr(ini_io, "save_document", external_write_then_save)

        update_document(path, lambda doc: doc.with_value("a.jpg", "caption", "mine"))

        assert external_write_happened
        final = load_document(path)
        assert final.section("a.jpg").get("caption") == "mine"
        # A külső írás a sikeres check után történt, ezért ez a fájlrendszeri
        # API-kkal nem védhető rés: a csillag elveszett, ezt a teszt korlátként
        # rögzíti, nem ígért védelemként.
        assert final.section("a.jpg").get("star") is None

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

    def test_change_before_fingerprint_check_is_replayed(self, tmp_path):
        """Az előzetes fingerprint-ellenőrzés előtti külső változás újrajátszódik."""
        from picasapy.ini import load_document, update_document

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")

        calls = {"n": 0}

        def mutate(document):
            calls["n"] += 1
            # A fingerprint-ellenőrzés előtt a külső író csillagot ad.
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

    def test_two_workers_on_same_ini_keep_both_updates(self, monkeypatch, tmp_path):
        """Az azonos ini-útvonalon futó PicasaPy-írók sorban módosítanak."""
        from threading import Event, Thread, current_thread

        from picasapy.ini import load_document, update_document
        from picasapy.ini import io as ini_io

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")
        alias_directory = tmp_path / "path-alias"
        alias_directory.mkdir()
        second_path = alias_directory / ".." / ".picasa.ini"
        real_path_lock = ini_io._ini_path_lock
        second_lock_requested = Event()
        first_mutating = Event()
        release_first = Event()
        second_mutating = Event()
        errors = []

        def observed_path_lock(target):
            if current_thread().name == "second-ini-writer":
                second_lock_requested.set()
            return real_path_lock(target)

        monkeypatch.setattr(ini_io, "_ini_path_lock", observed_path_lock)

        def first_mutate(document):
            first_mutating.set()
            assert release_first.wait(timeout=3)
            return document.with_value("a.jpg", "caption", "first")

        def second_mutate(document):
            second_mutating.set()
            return document.with_value("a.jpg", "star", "yes")

        def run(mutate):
            try:
                target = second_path if current_thread().name == "second-ini-writer" else path
                update_document(target, mutate)
            except BaseException as exc:  # a szál hibája a főszálon is bukjon
                errors.append(exc)

        first = Thread(target=run, args=(first_mutate,), name="first-ini-writer", daemon=True)
        second = Thread(
            target=run, args=(second_mutate,), name="second-ini-writer", daemon=True
        )
        first.start()
        try:
            assert first_mutating.wait(timeout=3)
            second.start()
            assert second_lock_requested.wait(timeout=3)
            # A második dolgozó már a lock fogantyújánál van, az első még
            # módosít: a második mutate csak az első mentése után futhat.
            assert not second_mutating.wait(timeout=0.1)
        finally:
            release_first.set()

        first.join(timeout=3)
        second.join(timeout=3)
        assert not first.is_alive()
        assert not second.is_alive()
        assert errors == []
        final = load_document(path)
        assert final.section("a.jpg").get("caption") == "first"
        assert final.section("a.jpg").get("star") == "yes"

    def test_different_ini_files_can_be_written_in_parallel(self, tmp_path):
        """A path-lock csak az azonos fájlra várakoztat; más útvonal futhat."""
        from threading import Barrier, Thread

        from picasapy.ini import load_document, update_document
        from picasapy.ini import io as ini_io

        first_path = tmp_path / "first" / ".picasa.ini"
        second_path = tmp_path / "second" / ".picasa.ini"
        first_path.parent.mkdir()
        second_path.parent.mkdir()
        first_path.write_bytes(b"[a.jpg]\r\n")
        second_path.write_bytes(b"[b.jpg]\r\n")
        both_mutating = Barrier(2)
        errors = []
        assert callable(ini_io._ini_path_lock)

        def worker(path, section, key):
            def mutate(document):
                both_mutating.wait(timeout=3)
                return document.with_value(section, key, "yes")

            try:
                update_document(path, mutate)
            except BaseException as exc:
                errors.append(exc)

        first = Thread(target=worker, args=(first_path, "a.jpg", "caption"), daemon=True)
        second = Thread(target=worker, args=(second_path, "b.jpg", "star"), daemon=True)
        first.start()
        second.start()
        first.join(timeout=4)
        second.join(timeout=4)

        assert not first.is_alive()
        assert not second.is_alive()
        assert errors == []
        assert load_document(first_path).section("a.jpg").get("caption") == "yes"
        assert load_document(second_path).section("b.jpg").get("star") == "yes"

    def test_path_lock_releases_after_exception(self, tmp_path):
        """A mutate kivétele után egy másik szál is írhatja ugyanazt az ini-t."""
        from threading import Event, Thread

        from picasapy.ini import load_document, update_document
        from picasapy.ini import io as ini_io

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")
        assert callable(ini_io._ini_path_lock)

        def fail_mutation(_document):
            raise ValueError("szándékos tesztkivétel")

        with pytest.raises(ValueError, match="szándékos tesztkivétel"):
            update_document(path, fail_mutation)

        finished = Event()
        errors = []

        def write_after_exception():
            try:
                update_document(
                    path, lambda doc: doc.with_value("a.jpg", "star", "yes")
                )
            except BaseException as exc:
                errors.append(exc)
            finally:
                finished.set()

        writer = Thread(target=write_after_exception, daemon=True)
        writer.start()
        assert finished.wait(timeout=3)
        writer.join(timeout=1)
        assert not writer.is_alive()
        assert errors == []
        assert load_document(path).section("a.jpg").get("star") == "yes"

    def test_reentrant_update_on_same_ini_does_not_deadlock(self, tmp_path):
        """Az ugyanazon szálból, ugyanarra az ini-re belépő írás befejeződik."""
        from threading import Event, Thread

        from picasapy.ini import load_document, update_document
        from picasapy.ini import io as ini_io

        path = tmp_path / ".picasa.ini"
        path.write_bytes(b"[a.jpg]\r\n")
        assert callable(ini_io._ini_path_lock)
        nested_update_done = False
        finished = Event()
        errors = []

        def mutate_outer(document):
            nonlocal nested_update_done
            if not nested_update_done:
                nested_update_done = True
                update_document(
                    path,
                    lambda inner: inner.with_value("a.jpg", "star", "nested"),
                )
            return document.with_value("a.jpg", "caption", "outer")

        def run_outer():
            try:
                update_document(path, mutate_outer)
            except BaseException as exc:
                errors.append(exc)
            finally:
                finished.set()

        writer = Thread(target=run_outer, daemon=True)
        writer.start()
        assert finished.wait(timeout=3)
        writer.join(timeout=1)
        assert not writer.is_alive()
        assert errors == []
        final = load_document(path)
        assert final.section("a.jpg").get("caption") == "outer"
        assert final.section("a.jpg").get("star") == "nested"
