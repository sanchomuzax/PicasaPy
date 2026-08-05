"""#348: az exe string-tábláiból újonnan azonosított `.picasa.ini` kulcsok
(`[encoding]` szekció, `[Picasa]` verziószámok, per-kép `hidden`/`flipped`/
`edit_width`/`edit_height`/`moviestart`/`movieend`) byte-pontos round-trip
megőrzése — a round-trip elv szerint amit nem értünk, változatlanul
visszaírjuk. Ez a teszt a meglévő, generikus sor-alapú rétegen (`document.py`,
`io.py`) rögzíti/dokumentálja ezt a garanciát az új kulcsokra."""

from __future__ import annotations

from picasapy.ini import load_document, parse_document, save_document, update_document

# A `docs/specs/picasa-ini-format.md` és `docs/specs/picasa-exe-strings.md`
# alapján összeállított minta — MINDEN #348-ban felsorolt új kulcsot
# tartalmaz.
SAMPLE = (
    "[encoding]\r\n"
    "utf8=1\r\n"
    "\r\n"
    "[Picasa]\r\n"
    "name=Nyaralás 2024\r\n"
    "contactsversion=42\r\n"
    "frversion=7\r\n"
    "gpsversion=3\r\n"
    "colorspaceversion=1\r\n"
    "rawversion=5\r\n"
    "\r\n"
    "[IMG_0001.jpg]\r\n"
    "star=yes\r\n"
    "hidden=yes\r\n"
    "flipped(0)=1\r\n"
    "edit_width=800\r\n"
    "edit_height=600\r\n"
    "\r\n"
    "[clip.mp4]\r\n"
    "moviestart=12345\r\n"
    "movieend=67890\r\n"
)


class TestParseNewKeys:
    """A `parse_document` a `[encoding]` szekciót és az új kulcsokat
    ugyanúgy generikus sorokként kezeli, mint bármely mást — ezért nem
    veszíthetnek el adatot."""

    def test_encoding_section_recognized(self):
        doc = parse_document(SAMPLE)
        section = doc.section("encoding")
        assert section is not None
        assert section.get("utf8") == "1"

    def test_encoding_section_is_special_not_a_file_entry(self):
        # A `[encoding]` szekció nem fizikai fájlbejegyzés — nem szabad
        # megjelennie a `file_sections()` listában (ugyanúgy, mint
        # `[Picasa]`/`[Contacts]`).
        doc = parse_document(SAMPLE)
        file_section_names = [s.name for s in doc.file_sections()]
        assert "encoding" not in file_section_names
        assert "IMG_0001.jpg" in file_section_names
        assert "clip.mp4" in file_section_names

    def test_picasa_version_keys_preserved(self):
        doc = parse_document(SAMPLE)
        picasa = doc.section("Picasa")
        assert picasa.get("contactsversion") == "42"
        assert picasa.get("frversion") == "7"
        assert picasa.get("gpsversion") == "3"
        assert picasa.get("colorspaceversion") == "1"
        assert picasa.get("rawversion") == "5"

    def test_hidden_key_preserved(self):
        doc = parse_document(SAMPLE)
        assert doc.section("IMG_0001.jpg").get("hidden") == "yes"

    def test_flipped_format_string_key_preserved(self):
        # A `flipped(0)` a `rotate(N)` mintáját követi: a kulcs NEVE
        # tartalmazza a zárójeles paramétert — a parser ezt egyetlen
        # kulcsként kezeli, ahogy a `rotate(1)`-et is.
        doc = parse_document(SAMPLE)
        assert doc.section("IMG_0001.jpg").get("flipped(0)") == "1"

    def test_edit_dimensions_preserved(self):
        doc = parse_document(SAMPLE)
        section = doc.section("IMG_0001.jpg")
        assert section.get("edit_width") == "800"
        assert section.get("edit_height") == "600"

    def test_movie_trim_keys_preserved(self):
        doc = parse_document(SAMPLE)
        section = doc.section("clip.mp4")
        assert section.get("moviestart") == "12345"
        assert section.get("movieend") == "67890"


class TestRoundTripNewKeys:
    """A teljes minta bitre pontosan visszaadja önmagát `serialize()`-en át —
    ez a round-trip elv alapgaranciája (#348)."""

    def test_serialize_is_byte_identical(self):
        doc = parse_document(SAMPLE)
        assert doc.serialize() == SAMPLE

    def test_unrelated_edit_preserves_all_new_keys(self):
        # Egy VALÓS módosítás (más kulcson) mellett az összes új/ismeretlen
        # kulcsnak és szekciónak változatlanul meg kell maradnia.
        doc = parse_document(SAMPLE)
        updated = doc.with_value("IMG_0001.jpg", "caption", "teszt felirat")
        text = updated.serialize()
        assert "[encoding]" in text
        assert "utf8=1" in text
        assert "contactsversion=42" in text
        assert "frversion=7" in text
        assert "gpsversion=3" in text
        assert "colorspaceversion=1" in text
        assert "rawversion=5" in text
        assert "hidden=yes" in text
        assert "flipped(0)=1" in text
        assert "edit_width=800" in text
        assert "edit_height=600" in text
        assert "moviestart=12345" in text
        assert "movieend=67890" in text
        assert "caption=teszt felirat" in text


class TestFileIoNewKeys:
    """A fájl-alapú betöltés/mentés (`load_document`/`save_document`) és az
    atomikus, ütközésbiztos `update_document` sem sérti a round-tripet."""

    def test_load_save_roundtrip_is_byte_identical(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(SAMPLE.encode("utf-8"))
        doc = load_document(path)
        save_document(doc, path)
        assert path.read_bytes() == SAMPLE.encode("utf-8")

    def test_update_document_preserves_unrelated_new_keys(self, tmp_path):
        path = tmp_path / ".picasa.ini"
        path.write_bytes(SAMPLE.encode("utf-8"))
        update_document(
            path, lambda d: d.with_value("IMG_0001.jpg", "star", "yes")
        )
        reloaded = load_document(path)
        assert reloaded.section("encoding").get("utf8") == "1"
        assert reloaded.section("Picasa").get("rawversion") == "5"
        assert reloaded.section("IMG_0001.jpg").get("hidden") == "yes"
        assert reloaded.section("IMG_0001.jpg").get("flipped(0)") == "1"
        assert reloaded.section("IMG_0001.jpg").get("edit_width") == "800"
        assert reloaded.section("clip.mp4").get("moviestart") == "12345"
        assert reloaded.section("clip.mp4").get("movieend") == "67890"

    def test_parsing_new_keys_does_not_crash(self, tmp_path):
        # Nem szabad kivételt dobnia sem a betöltésnek, sem a mentésnek —
        # az új kulcsok pusztán generikus sorok a modell szempontjából.
        path = tmp_path / ".picasa.ini"
        path.write_bytes(SAMPLE.encode("utf-8"))
        doc = load_document(path)
        save_document(doc, path, backup=True)
        assert (tmp_path / ".picasa.ini.bak").exists()
