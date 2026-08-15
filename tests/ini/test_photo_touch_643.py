"""#643 — a KÉPFÁJL módosítási idejének megérintése az ini-írás után.

## Miért van erre szükség (a jegy kutatói szála, lezárva)

A futó eredeti Picasa a fotó rekordját a saját `db3` adatbázisából tekinti
igazságforrásnak, és a rekord ÉRVÉNYESSÉGÉT a **képfájlhoz** méri
(`moddate`, `onlinechecksum` — `0x00467ca0`). A `.picasa.ini` írása
kivált ugyan operációs rendszer szintű értesítést (a figyelő szűrőjében
benne van a `LAST_WRITE` bit), de egy **már indexelt** fotót nem tesz
elavulttá: a rekord érvényes marad, a `filters=`-ünket a Picasa sosem
olvassa be, sőt a következő saját írásánál felül is írja.

A spec (`docs/specs/picasa-ini-format.md`, „A beolvasás életciklusa") ebből
egyetlen mérhető megkerülési utat vezet le: **ha a külső író a képfájl
módosítási idejét is megérinti (a tartalom változtatása nélkül), a fotó
bekerülhet az újrafeldolgozandók közé.**

## Amit ez a teszt ÁLLÍT (és amit nem)

Ez a teszt a MI oldalunkat méri: az érintés megtörténik-e, pontosan akkor,
amikor kell, a képfájl bájtjainak és az `atime`-nak a megőrzésével, és
kikapcsolható-e. **Azt, hogy a valódi Picasa emiatt tényleg újraolvassa-e
az init, Linuxon nem lehet mérni** — az a felhasználó windowsos
párhuzamos próbájára vár.
"""

from __future__ import annotations

import os

import pytest

from picasapy.ini import load_document, update_document
from picasapy.ini.photo_touch import TOUCH_ENV_VAR

#: Egy apró, de valódi bájtsorozat képfájl helyett — a teszt sosem dekódolja,
#: csak a bájtazonosságát ellenőrzi.
_IMAGE_BYTES = b"\xff\xd8\xff\xe0PicasaPy-teszt-kep\xff\xd9"

#: Jól a múltban lévő időbélyeg (2020-01-01 körül), hogy a „frissült-e"
#: összehasonlítás a fájlrendszer időfelbontásától függetlenül eldőljön.
_OLD_NS = 1_577_836_800_000_000_000


@pytest.fixture
def folder(tmp_path, monkeypatch):
    """Egy mappa `kep.jpg` + `masik.jpg` képpel és üres `.picasa.ini`-vel.

    A környezeti kapcsolót MINDEN teszt előtt eltávolítjuk, hogy az
    alapértelmezett viselkedést mérjük, ne a futtató gép beállítását.
    """
    monkeypatch.delenv(TOUCH_ENV_VAR, raising=False)
    (tmp_path / "kep.jpg").write_bytes(_IMAGE_BYTES)
    (tmp_path / "masik.jpg").write_bytes(_IMAGE_BYTES)
    (tmp_path / ".picasa.ini").write_text("[kep.jpg]\nstar=yes\n", encoding="utf-8")
    for name in ("kep.jpg", "masik.jpg"):
        os.utime(tmp_path / name, ns=(_OLD_NS, _OLD_NS))
    return tmp_path


def _write_filters(folder, section: str = "kep.jpg", value: str = "bw=1;") -> None:
    update_document(
        folder / ".picasa.ini",
        lambda document: document.with_value(section, "filters", value),
        backup=False,
    )


class TestErintesAlapertelmezesben:
    """Alapértelmezés: BE — a round-trip ígéret ezen áll vagy bukik (#643)."""

    def test_a_kep_mtime_ja_frissul(self, folder):
        _write_filters(folder)
        assert (folder / "kep.jpg").stat().st_mtime_ns > _OLD_NS

    def test_a_kep_bajtjai_valtozatlanok(self, folder):
        _write_filters(folder)
        assert (folder / "kep.jpg").read_bytes() == _IMAGE_BYTES

    def test_az_atime_megorzodik(self, folder):
        _write_filters(folder)
        # A `read_bytes` az előző tesztben módosíthatná az atime-ot, ezért itt
        # külön, olvasás NÉLKÜL mérünk.
        assert (folder / "kep.jpg").stat().st_atime_ns == _OLD_NS

    def test_az_ini_iras_maga_megtortenik(self, folder):
        _write_filters(folder)
        section = load_document(folder / ".picasa.ini").section("kep.jpg")
        assert section.get("filters") == "bw=1;"
        # A round-trip: a meglévő kulcs érintetlen.
        assert section.get("star") == "yes"


class TestCsakAzErintettKep:
    """Nem szórunk szét érintést: csak az a fotó, amelynek a szakasza
    ténylegesen változott."""

    def test_a_tobbi_kep_erintetlen(self, folder):
        _write_filters(folder, section="kep.jpg")
        assert (folder / "masik.jpg").stat().st_mtime_ns == _OLD_NS

    def test_valtozatlan_szakasznal_nincs_erintes(self, folder):
        # A `mutate` nem módosít semmit — az ini ugyan újraíródik, de a fotó
        # rekordja nem változott, tehát nincs mit újraolvastatni a Picasával.
        update_document(folder / ".picasa.ini", lambda document: document, backup=False)
        assert (folder / "kep.jpg").stat().st_mtime_ns == _OLD_NS

    def test_specialis_szakasz_nem_fajl(self, folder):
        # A `[Picasa]` nem fotó-szakasz; nincs hozzá képfájl, nem is szabad
        # kivételbe futni tőle.
        update_document(
            folder / ".picasa.ini",
            lambda document: document.with_value("Picasa", "name", "teszt"),
            backup=False,
        )
        assert (folder / "kep.jpg").stat().st_mtime_ns == _OLD_NS

    def test_nem_letezo_kepfajl_szakasza_nem_hiba(self, folder):
        _write_filters(folder, section="nincs-ilyen.jpg")
        section = load_document(folder / ".picasa.ini").section("nincs-ilyen.jpg")
        assert section.get("filters") == "bw=1;"


class TestKikapcsolhatosag:
    """A mtime rendezési/biztonsági mentési szempontból számíthat — legyen
    kikapcsolható a felhasználónak, kód módosítása nélkül."""

    @pytest.mark.parametrize("kikapcsolo", ["0", "false", "no", "off", "FALSE"])
    def test_kikapcsolva_semmi_nem_valtozik(self, folder, monkeypatch, kikapcsolo):
        monkeypatch.setenv(TOUCH_ENV_VAR, kikapcsolo)
        _write_filters(folder)
        stat = (folder / "kep.jpg").stat()
        assert stat.st_mtime_ns == _OLD_NS
        assert stat.st_atime_ns == _OLD_NS
        assert (folder / "kep.jpg").read_bytes() == _IMAGE_BYTES

    def test_kikapcsolva_is_menti_az_init(self, folder, monkeypatch):
        monkeypatch.setenv(TOUCH_ENV_VAR, "0")
        _write_filters(folder)
        section = load_document(folder / ".picasa.ini").section("kep.jpg")
        assert section.get("filters") == "bw=1;"

    @pytest.mark.parametrize("bekapcsolo", ["1", "true", "yes", "on"])
    def test_explicit_bekapcsolas(self, folder, monkeypatch, bekapcsolo):
        monkeypatch.setenv(TOUCH_ENV_VAR, bekapcsolo)
        _write_filters(folder)
        assert (folder / "kep.jpg").stat().st_mtime_ns > _OLD_NS


class TestHibaturés:
    """Az érintés SOHA nem boríthatja a mentést: a felhasználó szerkesztése
    fontosabb, mint a Picasa értesítése."""

    def test_az_utime_hibaja_nem_boritja_a_mentest(self, folder, monkeypatch, caplog):
        eredeti_utime = os.utime

        def bukó_utime(path, *args, **kwargs):
            if str(path).endswith("kep.jpg"):
                raise PermissionError("írásvédett hálózati megosztás")
            return eredeti_utime(path, *args, **kwargs)

        monkeypatch.setattr(os, "utime", bukó_utime)
        with caplog.at_level("WARNING"):
            _write_filters(folder)
        section = load_document(folder / ".picasa.ini").section("kep.jpg")
        assert section.get("filters") == "bw=1;"
        assert any("kep.jpg" in record.getMessage() for record in caplog.records)


class TestTorlesIsValtozas:
    """A kulcs/szakasz TÖRLÉSE ugyanúgy elavulttá teszi a fotó rekordját —
    ez a `revert` és a „Mentés visszavonása" útja (#21, #444)."""

    def test_kulcs_torlese_is_erint(self, folder):
        update_document(
            folder / ".picasa.ini",
            lambda document: document.with_removed("kep.jpg", "star"),
            backup=False,
        )
        assert (folder / "kep.jpg").stat().st_mtime_ns > _OLD_NS

    def test_szakasz_torlese_is_erint(self, folder):
        update_document(
            folder / ".picasa.ini",
            lambda document: document.without_section("kep.jpg"),
            backup=False,
        )
        assert (folder / "kep.jpg").stat().st_mtime_ns > _OLD_NS
