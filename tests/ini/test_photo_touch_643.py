"""#643 / #1320 — a KÉPFÁJL módosítási idejének megérintése az ini-írás után.

## Mit mér ez a teszt

A `photo_touch` modul egy **feltételezett** Picasa-oldali megkerülési utat
valósít meg (ld. a modul fejlécét és a `docs/decisions/photo-mtime-erintes.md`
ADR-t). A #1320 óta **alapértelmezésben KI van kapcsolva**, mert az ini
újraolvasásának valódi kulcsa a `.picasa.ini` SAJÁT írási ideje
(`albumdata_inisync`, 99,5%-os mért egyezés) — a képfájl `mtime`-ja a
mechanizmusnak nem része.

Ez a teszt ezért három dolgot állít:

1. **alapértelmezésben a képfájlhoz hozzá sem nyúlunk** — az `st_mtime_ns`
   bitre azonos marad (ez a #1320 kifejezett követelménye);
2. **kifejezett bekapcsolásra** (`PICASAPY_TOUCH_PHOTO_MTIME=1`) az érintés
   pontosan akkor és arra fut le, amire kell, a bájtok és az `atime`
   megőrzésével;
3. **a hatás látható**: bekapcsolt állapotban a modul naplózza, hány fájl
   időbélyegét írta át.

Azt, hogy a valódi, windowsos Picasa mit kezd az érintéssel, **Linuxon nem
lehet mérni** — épp ezért nem alapértelmezés.
"""

from __future__ import annotations

import os

import pytest

from picasapy.ini import load_document, update_document
from picasapy.ini.photo_touch import TOUCH_ENV_VAR, is_touch_enabled

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


@pytest.fixture
def folder_be(folder, monkeypatch):
    """Ugyanaz a mappa, de az érintés KIFEJEZETTEN bekapcsolva.

    A #1320 óta ez a nem alapértelmezett ág; a régi „alapból BE" tesztek
    ezen a fixture-ön futnak tovább, mert a viselkedésük maga nem változott,
    csak az kell hozzá, hogy a felhasználó kérje.
    """
    monkeypatch.setenv(TOUCH_ENV_VAR, "1")
    return folder


def _write_filters(folder, section: str = "kep.jpg", value: str = "bw=1;") -> None:
    update_document(
        folder / ".picasa.ini",
        lambda document: document.with_value(section, "filters", value),
        backup=False,
    )


class TestAlapertelmezesKI:
    """#1320: alapértelmezésben a képfájlhoz HOZZÁ SEM NYÚLUNK.

    Az újraolvasás kulcsa a `.picasa.ini` saját írási ideje; a fotó
    `mtime`-jának átírása mért haszon nélküli, visszafordíthatatlan
    mellékhatás az éles fotógyűjteményen.
    """

    def test_a_kapcsolo_alapertelmezese_ki(self):
        assert is_touch_enabled({}) is False

    def test_a_kep_mtime_ja_bitre_azonos_marad(self, folder):
        elotte = (folder / "kep.jpg").stat().st_mtime_ns
        _write_filters(folder)
        assert (folder / "kep.jpg").stat().st_mtime_ns == elotte == _OLD_NS

    def test_az_atime_sem_valtozik(self, folder):
        _write_filters(folder)
        assert (folder / "kep.jpg").stat().st_atime_ns == _OLD_NS

    def test_a_kep_bajtjai_valtozatlanok(self, folder):
        _write_filters(folder)
        assert (folder / "kep.jpg").read_bytes() == _IMAGE_BYTES

    def test_az_ini_iras_maga_megtortenik(self, folder):
        """A lényeg, ami a Picasát tényleg érdekli: az ini frissül."""
        _write_filters(folder)
        section = load_document(folder / ".picasa.ini").section("kep.jpg")
        assert section.get("filters") == "bw=1;"
        # A round-trip: a meglévő kulcs érintetlen.
        assert section.get("star") == "yes"

    def test_az_ini_sajat_ideje_frissul(self, folder):
        """Az `albumdata_inisync`-mechanizmus kiváltása: az ini írási ideje.

        Ez az EGYETLEN dolog, amit a mért mechanizmus megkövetel — és ez
        magától, a fájl kiírásából adódik, külön lépés nélkül.
        """
        ini = folder / ".picasa.ini"
        os.utime(ini, ns=(_OLD_NS, _OLD_NS))
        _write_filters(folder)
        assert ini.stat().st_mtime_ns > _OLD_NS


class TestBekapcsolvaErint:
    """Kifejezett bekapcsolásra a viselkedés a régi (#643)."""

    def test_a_kep_mtime_ja_frissul(self, folder_be):
        _write_filters(folder_be)
        assert (folder_be / "kep.jpg").stat().st_mtime_ns > _OLD_NS

    def test_a_kep_bajtjai_valtozatlanok(self, folder_be):
        _write_filters(folder_be)
        assert (folder_be / "kep.jpg").read_bytes() == _IMAGE_BYTES

    def test_az_atime_megorzodik(self, folder_be):
        _write_filters(folder_be)
        # A `read_bytes` az előző tesztben módosíthatná az atime-ot, ezért itt
        # külön, olvasás NÉLKÜL mérünk.
        assert (folder_be / "kep.jpg").stat().st_atime_ns == _OLD_NS


class TestANaploLathatovaTeszi:
    """#1320: ha az érintés fut, a hatásának LÁTSZANIA kell a naplóban.

    Egy éles fotógyűjtemény időbélyegeit átírni nem csendes művelet.
    """

    def test_a_naplo_kiirja_hany_fajlt_erintett(self, folder_be, caplog):
        with caplog.at_level("INFO", logger="picasapy.ini.photo_touch"):
            _write_filters(folder_be)
        assert any(
            "1 képfájl" in record.getMessage() for record in caplog.records
        ), [r.getMessage() for r in caplog.records]

    def test_kikapcsolva_nincs_ilyen_naplosor(self, folder, caplog):
        with caplog.at_level("INFO", logger="picasapy.ini.photo_touch"):
            _write_filters(folder)
        assert not any("képfájl" in record.getMessage() for record in caplog.records)


class TestCsakAzErintettKep:
    """Nem szórunk szét érintést: csak az a fotó, amelynek a szakasza
    ténylegesen változott."""

    def test_a_tobbi_kep_erintetlen(self, folder_be):
        _write_filters(folder_be, section="kep.jpg")
        assert (folder_be / "masik.jpg").stat().st_mtime_ns == _OLD_NS

    def test_valtozatlan_szakasznal_nincs_erintes(self, folder_be):
        # A `mutate` nem módosít semmit — az ini ugyan újraíródik, de a fotó
        # rekordja nem változott, tehát nincs mit újraolvastatni a Picasával.
        update_document(
            folder_be / ".picasa.ini", lambda document: document, backup=False
        )
        assert (folder_be / "kep.jpg").stat().st_mtime_ns == _OLD_NS

    def test_specialis_szakasz_nem_fajl(self, folder_be):
        # A `[Picasa]` nem fotó-szakasz; nincs hozzá képfájl, nem is szabad
        # kivételbe futni tőle.
        update_document(
            folder_be / ".picasa.ini",
            lambda document: document.with_value("Picasa", "name", "teszt"),
            backup=False,
        )
        assert (folder_be / "kep.jpg").stat().st_mtime_ns == _OLD_NS

    def test_nem_letezo_kepfajl_szakasza_nem_hiba(self, folder_be):
        _write_filters(folder_be, section="nincs-ilyen.jpg")
        section = load_document(folder_be / ".picasa.ini").section("nincs-ilyen.jpg")
        assert section.get("filters") == "bw=1;"


class TestKapcsolo:
    """A kapcsoló mindkét irányban, a `PICASAPY_*` szokásos elnéző olvasatával."""

    @pytest.mark.parametrize("kikapcsolo", ["0", "false", "no", "off", "FALSE", ""])
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

    @pytest.mark.parametrize("bekapcsolo", ["1", "true", "yes", "on", "IGEN", "be"])
    def test_explicit_bekapcsolas(self, folder, monkeypatch, bekapcsolo):
        monkeypatch.setenv(TOUCH_ENV_VAR, bekapcsolo)
        _write_filters(folder)
        assert (folder / "kep.jpg").stat().st_mtime_ns > _OLD_NS

    def test_ismeretlen_ertek_nem_kapcsol_be(self, folder, monkeypatch):
        """Elgépelésre a BIZTONSÁGOS irányba dőlünk: nem nyúlunk a fájlhoz."""
        monkeypatch.setenv(TOUCH_ENV_VAR, "talán")
        _write_filters(folder)
        assert (folder / "kep.jpg").stat().st_mtime_ns == _OLD_NS


class TestHibaturés:
    """Az érintés SOHA nem boríthatja a mentést: a felhasználó szerkesztése
    fontosabb, mint a Picasa értesítése."""

    def test_az_utime_hibaja_nem_boritja_a_mentest(self, folder_be, monkeypatch, caplog):
        eredeti_utime = os.utime

        def bukó_utime(path, *args, **kwargs):
            if str(path).endswith("kep.jpg"):
                raise PermissionError("írásvédett hálózati megosztás")
            return eredeti_utime(path, *args, **kwargs)

        monkeypatch.setattr(os, "utime", bukó_utime)
        with caplog.at_level("WARNING"):
            _write_filters(folder_be)
        section = load_document(folder_be / ".picasa.ini").section("kep.jpg")
        assert section.get("filters") == "bw=1;"
        assert any("kep.jpg" in record.getMessage() for record in caplog.records)


class TestTorlesIsValtozas:
    """A kulcs/szakasz TÖRLÉSE ugyanúgy elavulttá teszi a fotó rekordját —
    ez a `revert` és a „Mentés visszavonása" útja (#21, #444)."""

    def test_kulcs_torlese_is_erint(self, folder_be):
        update_document(
            folder_be / ".picasa.ini",
            lambda document: document.with_removed("kep.jpg", "star"),
            backup=False,
        )
        assert (folder_be / "kep.jpg").stat().st_mtime_ns > _OLD_NS

    def test_szakasz_torlese_is_erint(self, folder_be):
        update_document(
            folder_be / ".picasa.ini",
            lambda document: document.without_section("kep.jpg"),
            backup=False,
        )
        assert (folder_be / "kep.jpg").stat().st_mtime_ns > _OLD_NS
