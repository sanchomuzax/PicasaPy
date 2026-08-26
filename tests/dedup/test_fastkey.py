"""A Picasa fej+farok tartalom-kulcsa (#1481).

Az őr-értékek forrása a `docs/specs/picasa-tartalomkulcs.md` visszafejtett
algoritmusa, amelyet a felhasználó valódi `db3` adatbázisának
`imagedata_originfast.pmp` oszlopával szemben tizenkét igazi fényképen
bitre pontosan reprodukáltunk. A lenti hexa értékek azt rögzítik, hogy a
mi megvalósításunk később se csússzon el ettől.
"""

import hashlib
import struct

import pytest

from picasapy.dedup.fastkey import (
    FAROK_KUSZOB,
    FEJ_MERET,
    picasa_fast_key,
)


def minta_bajtok(hossz: int) -> bytes:
    """Determinisztikus, nem összenyomható bájtsorozat a megadott hosszal."""
    return bytes((i * 37 + 11) & 0xFF for i in range(hossz))


def naiv_kulcs(adat: bytes) -> int:
    """Az algoritmus független, szándékosan buta újraírása: a TELJES tartalmat
    a memóriában szeleteli, nem `seek`-el. A gyártási megvalósítás
    (folyamszerű olvasás) ehhez képest nem térhet el."""
    meret = len(adat)
    fej = min(meret, FEJ_MERET)
    farok = FEJ_MERET if meret > FAROK_KUSZOB else meret - fej
    puffer = struct.pack("<I", meret & 0xFFFFFFFF) + adat[:fej]
    if farok:
        puffer += adat[meret - farok :]
    return struct.unpack("<Q", hashlib.md5(puffer).digest()[:8])[0]


def ir(tmp_path, nev: str, adat: bytes):
    path = tmp_path / nev
    path.write_bytes(adat)
    return path


class TestAllandok:
    def test_a_visszafejtett_hatarok(self):
        """A bináris `0x41C2` és `0x8384` küszöbei."""
        assert FEJ_MERET == 16834
        assert FAROK_KUSZOB == 33668


class TestOrErtekek:
    """Rögzített kulcsok determinisztikus tartalomra (regressziós horgony)."""

    @pytest.mark.parametrize(
        ("hossz", "vart"),
        [
            (1, 0x410619197698A64F),
            (16833, 0x894BA7D07FCEF7C3),
            (FEJ_MERET, 0x371C039CFD56ABF7),  # 16834 — a fej pont teljes
            (16835, 0xFBCA92741A2CA183),
            (FAROK_KUSZOB, 0x6B367AFC3AC635F5),  # 33668 — fej+farok = méret
            (33669, 0x075F1A1881D2CF37),  # 33669 — innen csonkol a farok
            (40000, 0x097B7C1BE1552870),
        ],
    )
    def test_hataresetek_kulcsa(self, tmp_path, hossz, vart):
        path = ir(tmp_path, f"m{hossz}.bin", minta_bajtok(hossz))
        assert picasa_fast_key(path) == vart

    def test_rovid_szoveges_tartalom(self, tmp_path):
        path = ir(tmp_path, "picasa.bin", b"picasa")
        assert picasa_fast_key(path) == 0x184FC29BC77587A2


class TestFuggetlenReferencia:
    @pytest.mark.parametrize(
        "hossz",
        [1, 100, 16833, 16834, 16835, 33667, 33668, 33669, 50000, 120000],
    )
    def test_egyezik_a_naiv_ujrairassal(self, tmp_path, hossz):
        adat = minta_bajtok(hossz)
        path = ir(tmp_path, f"n{hossz}.bin", adat)
        assert picasa_fast_key(path) == naiv_kulcs(adat)


class TestHatarViselkedes:
    def test_ures_fajlnak_nincs_kulcsa(self, tmp_path):
        """Az eredeti `-1`-gyel tér vissza üres fájlra; nálunk ez `None`."""
        path = ir(tmp_path, "ures.bin", b"")
        assert picasa_fast_key(path) is None

    def test_hianyzo_fajl_nem_kivetel(self, tmp_path):
        assert picasa_fast_key(tmp_path / "nincs.bin") is None

    def test_konyvtar_nem_kivetel(self, tmp_path):
        assert picasa_fast_key(tmp_path) is None

    def test_a_meret_resze_a_bemenetnek(self, tmp_path):
        """Két fájl azonos fej+farokkal, de ELTÉRŐ mérettel: más kulcs.

        A `33668` határ alatt maradunk, hogy a fej+farok együtt a teljes
        tartalom legyen — ha a méret nem lenne a hash bemenetében, a
        rövidebb fájl kulcsa egybeesne a hosszabbikéval."""
        rovid = ir(tmp_path, "rovid.bin", b"AB")
        hosszu = ir(tmp_path, "hosszu.bin", b"AB" + b"\x00" * 10)
        assert picasa_fast_key(rovid) != picasa_fast_key(hosszu)

    def test_kozepen_eltero_fajlok_UTKOZNEK(self, tmp_path):
        """A Picasa-algoritmus dokumentált gyengesége — nem hiba, hanem tény.

        Azonos méret, azonos első és utolsó 16834 bájt, eltérő közép: a
        gyors kulcs MEGEGYEZIK. Épp ezért nem használható önmagában
        másodpéldány-bizonyítékként (ld. `dedup/exact.py` előszűrője)."""
        fej = minta_bajtok(FEJ_MERET)
        farok = minta_bajtok(FEJ_MERET)[::-1]
        a = ir(tmp_path, "a.bin", fej + b"\x00" * 5000 + farok)
        b = ir(tmp_path, "b.bin", fej + b"\xff" * 5000 + farok)
        assert a.stat().st_size == b.stat().st_size
        assert picasa_fast_key(a) == picasa_fast_key(b)
