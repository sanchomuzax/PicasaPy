"""Az ini `originhash` KISZÁMÍTÁSA (#2733) — `originfast` ‖ `originslow`.

A képlet forrása a `docs/specs/picasa-tartalomkulcs.md` „⭐⭐ MEGVAN: az
`originhash` = `originfast` ‖ `originslow`" szakasza (219. kutatói kör,
#2675): mindkét fél a saját MD5-jének első 8 bájtja, 64 bites számként,
`%016I64x` alakban kiírva — vagyis a hexa jegyek a digest bájtsorrendjéhez
képest MEGFORDULNAK.

Két, egymást ellenőrző horgony van itt:

1. **független újraírás** (`naiv_*`) — a gyártási megvalósítás
   (folyamszerű, darabolt olvasás) ettől nem térhet el;
2. **rögzített őr-értékek** determinisztikus tartalomra — ezek fogják meg,
   ha a bájtsorrend vagy a formázás később elcsúszik.

⚠️ A képlet HELYESSÉGÉT nem ez a fájl bizonyítja, hanem a valós korpuszon
mért 55/60 (91,7 %) egyezés (a spec fenti szakasza). Ez a teszt azt őrzi,
hogy a kódunk a MÉRT képletet valósítsa meg.
"""

import hashlib
import struct

import pytest

from picasapy.dedup.fastkey import FAROK_KUSZOB, FEJ_MERET, picasa_fast_key
from picasapy.dedup.originhash import origin_hash, originhash_szetszed, originhash_szoveg
from picasapy.dedup.slowkey import picasa_slow_key


def minta_bajtok(hossz: int) -> bytes:
    """Determinisztikus, nem összenyomható bájtsorozat a megadott hosszal."""
    return bytes((i * 37 + 11) & 0xFF for i in range(hossz))


def naiv_slow(adat: bytes) -> int:
    """A lassú kulcs szándékosan buta újraírása: egyetlen `md5()` hívás a
    memóriában lévő teljes tartalomra, darabolás nélkül."""
    return struct.unpack("<Q", hashlib.md5(adat).digest()[:8])[0]


def naiv_originhash(adat: bytes) -> str:
    """A teljes `originhash` független újraírása a spec képletéből."""
    meret = len(adat)
    fej = min(meret, FEJ_MERET)
    farok = FEJ_MERET if meret > FAROK_KUSZOB else meret - fej
    puffer = struct.pack("<I", meret & 0xFFFFFFFF) + adat[:fej]
    if farok:
        puffer += adat[meret - farok :]
    gyors = struct.unpack("<Q", hashlib.md5(puffer).digest()[:8])[0]
    lassu = struct.unpack("<Q", hashlib.md5(adat).digest()[:8])[0]
    return "%016x%016x" % (gyors, lassu)


def ir(tmp_path, nev: str, adat: bytes):
    path = tmp_path / nev
    path.write_bytes(adat)
    return path


class TestLassuKulcs:
    """`originslow` = MD5(teljes fájl)[0:8] kis-endián (#1482)."""

    @pytest.mark.parametrize("hossz", [1, 1000, FEJ_MERET, FAROK_KUSZOB, 200_000])
    def test_egyezik_a_naiv_ujrairassal(self, tmp_path, hossz):
        adat = minta_bajtok(hossz)
        path = ir(tmp_path, f"s{hossz}.bin", adat)
        assert picasa_slow_key(path) == naiv_slow(adat)

    def test_ures_fajl_nincs_kulcs(self, tmp_path):
        """Az üres fájlra nincs értelmes származás-kulcs (a gyors kulcs is
        `None`-t ad) — a hívó kihagyja a tételt."""
        assert picasa_slow_key(ir(tmp_path, "ures.bin", b"")) is None

    def test_olvashatatlan_utvonal_nincs_kulcs(self, tmp_path):
        assert picasa_slow_key(tmp_path / "nincs-ilyen.jpg") is None
        assert picasa_slow_key(tmp_path) is None  # könyvtár

    def test_a_darabolas_hatarat_atleopo_fajl(self, tmp_path):
        """A bináris 0x10000 bájtos darabokban olvas (`FUN_00a4ce40`); a mi
        darabolásunk sem változtathatja meg az eredményt."""
        adat = minta_bajtok(0x10000 * 2 + 123)
        path = ir(tmp_path, "nagy.bin", adat)
        assert picasa_slow_key(path) == naiv_slow(adat)


class TestSzovegesOsszefuzes:
    """A két 64 bites szám `%016I64x` alakú, kisbetűs összefűzése."""

    def test_pontosan_32_kisbetus_hexa_jegy(self):
        szoveg = originhash_szoveg(0x0123456789ABCDEF, 0xFEDCBA9876543210)
        assert szoveg == "0123456789abcdeffedcba9876543210"
        assert len(szoveg) == 32
        assert szoveg == szoveg.lower()

    def test_nulla_feltoltes_mindket_felen(self):
        """A `%016I64x` nullákkal tölt fel — a rövid értékből sem lehet
        16 jegynél kevesebb (különben a szétszedő elcsúszna)."""
        assert originhash_szoveg(1, 0) == "0000000000000001" + "0" * 16

    def test_a_szetszedo_visszaadja_a_ket_felet(self):
        """A bináris szétszedője (`0x00414b40`) pontosan 32 karaktert vár, és
        az első 16-ot a gyors, a másodikat a lassú kulcsnak olvassa."""
        assert originhash_szetszed("0123456789abcdeffedcba9876543210") == (
            0x0123456789ABCDEF,
            0xFEDCBA9876543210,
        )

    @pytest.mark.parametrize(
        "rossz",
        [
            "",
            "0123456789abcdef",  # csak 16 jegy
            "0123456789abcdeffedcba98765432100",  # 33 jegy
            "0123456789ABCDEFFEDCBA9876543210",  # nagybetűs: a korpuszban egy sem
            "0123456789abcdeffedcba98765432zz",  # nem hexa
        ],
    )
    def test_rossz_alakra_nincs_talalgatas(self, rossz):
        assert originhash_szetszed(rossz) is None


class TestOriginHashFajlbol:
    @pytest.mark.parametrize(
        "hossz", [1, 1000, FEJ_MERET, FAROK_KUSZOB, FAROK_KUSZOB + 1, 120_000]
    )
    def test_egyezik_a_naiv_ujrairassal(self, tmp_path, hossz):
        adat = minta_bajtok(hossz)
        path = ir(tmp_path, f"o{hossz}.jpg", adat)
        assert origin_hash(path) == naiv_originhash(adat)

    @pytest.mark.parametrize(
        ("hossz", "vart"),
        [
            (1, "410619197698a64f03370177d9ffc813"),
            (FEJ_MERET, "371c039cfd56abf70ab49c9fa8711170"),
            (FAROK_KUSZOB, "6b367afc3ac635f5e5441a46487d5e07"),
            (FAROK_KUSZOB + 1, "075f1a1881d2cf37b7b41319a40dfc81"),
        ],
    )
    def test_rogzitett_or_ertekek(self, tmp_path, hossz, vart):
        """Regressziós horgony. Az első 16 jegy a `test_fastkey.py` már
        rögzített gyors kulcsaival egyezik — ez köti össze a két mérést."""
        path = ir(tmp_path, f"h{hossz}.jpg", minta_bajtok(hossz))
        assert origin_hash(path) == vart

    def test_az_elso_fele_a_gyors_kulcs(self, tmp_path):
        """A három független bináris jel szerint az ELSŐ fél az `originfast`
        (a spec „Melyik fél melyik" szakasza)."""
        path = ir(tmp_path, "fele.jpg", minta_bajtok(5000))
        szoveg = origin_hash(path)
        assert szoveg[:16] == "%016x" % picasa_fast_key(path)
        assert szoveg[16:] == "%016x" % picasa_slow_key(path)

    def test_ures_es_olvashatatlan_fajl(self, tmp_path):
        assert origin_hash(ir(tmp_path, "ures.jpg", b"")) is None
        assert origin_hash(tmp_path / "nincs.jpg") is None

    def test_a_szetszedo_es_a_szamitas_egymas_inverze(self, tmp_path):
        path = ir(tmp_path, "kor.jpg", minta_bajtok(70_000))
        szoveg = origin_hash(path)
        assert originhash_szetszed(szoveg) == (
            picasa_fast_key(path),
            picasa_slow_key(path),
        )
