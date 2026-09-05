"""#2435: a thumbindex slot-ellenőrzőösszege — mindkét mód.

## A kiindulási mérés (2026-09-05, `research/testdata/Picasa2/db3`)

**140 755 valódi slot**, a két képlettel:

```
1. mód (útvonalas)   129 047   91,7%
2. mód (időbélyeges)   6 058    4,3%
egyik sem              5 650    4,0%
```

⇒ a két képlet együtt a slotok **96%-át** magyarázza. Ekkora egyezés
véletlenül kizárt (32 bites érték), tehát mindkét képlet áll.

A maradék 4% oka NINCS ELDÖNTVE — másik Picasa-verzió, nem-ASCII név más
kódlappal, vagy tényleges romlás. A #2435 ezt nem is dönti el; a szám azért
áll itt, hogy a következő kör lássa, honnan indul.

## Miért nem „az egyezésnek 100%-nak kell lennie"

Az eredeti verifikálója (`FUN_006b9870`) **időzóna-toleráns**: −12 h…+12 h
között minden egész órás eltolást végigpróbál. Ez ELLENŐRZÉS, nem képlet —
a mi képletünk egyetlen eltolással számol, tehát a zónahatáron átcsúszott
bejegyzéseket eleve nem találja el. A 4% ezért nem feltétlenül romlás.
"""

from __future__ import annotations

import pytest

from picasapy.pmpimport.thumbchecksum import (
    checksum_idobelyeges,
    checksum_utvonalas,
    js_hash,
    rol,
    utvonalas_modot_kell,
)


class TestRol:
    @pytest.mark.parametrize(
        ("ertek", "bit", "vart"),
        [
            (0x00000001, 1, 0x00000002),
            (0x80000000, 1, 0x00000001),   # a legfelső bit ÁTFORDUL
            (0x12345678, 0, 0x12345678),
            (0xFFFFFFFF, 13, 0xFFFFFFFF),
            (0x00000001, 32, 0x00000001),  # teljes kör
        ],
    )
    def test_ismert_ertekek(self, ertek, bit, vart):
        assert rol(ertek, bit) == vart


class TestJsHash:
    def test_az_ures_szoveg_a_kezdoerteket_adja_modulussal(self):
        """A ciklus le sem fut: `h` marad `0x12345678`, majd `mod 1000231`."""
        assert js_hash("") == 0x12345678 % 1_000_231

    def test_a_NAGYBETU_kisbetusodik(self):
        """`'A'..'Z'` → `+0x20` (`0x006b98d2`–`0x006b98e0`)."""
        assert js_hash("ABC") == js_hash("abc")

    def test_csak_az_ASCII_nagybetuk(self):
        """A kisbetűsítés `0x41`–`0x5A`-ra szól — a `[` (0x5B) nem az."""
        assert js_hash("[") != js_hash("{")

    def test_az_eredmeny_a_modulus_alatt_marad(self):
        for szoveg in ("", "a", "C:\\kepek\\nyaralas\\IMG_0001.jpg", "á" * 40):
            assert 0 <= js_hash(szoveg) < 1_000_231

    def test_a_bajt_ELOJELES(self):
        """⚠️ `movsx` (`0x006b98da`): a 0x80 fölötti bájt NEGATÍV.

        Előjeltelen olvasattal az „á" (UTF-8: C3 A1) más hasht adna. Ez nem
        részletkérdés: a spec 8.10 mérése épp ezen bukott 615 soron.
        """
        elojeltelen = _hash_elojeltelen_bajttal("á")
        assert js_hash("á") != elojeltelen, (
            "az előjeles és az előjeltelen olvasat ugyanazt adta — a teszt "
            "nem méri, amit állít"
        )

    def test_a_tolas_ELOJELTELEN(self):
        """⚠️ `shr`, NEM `sar` (`0x006b98f1`).

        A kezdőérték felső bitje 0, de a hash az első pár bájt után átbillen;
        egy `sar`-os változat onnantól eltér.
        """
        elojeles_tolassal = _hash_elojeles_tolassal("valami hosszabb útvonal")
        assert js_hash("valami hosszabb útvonal") != elojeles_tolassal


def _hash_elojeltelen_bajttal(szoveg: str) -> int:
    """A SZÁNDÉKOSAN hibás változat — csak a fenti teszt fogához kell."""
    h = 0x12345678
    for bajt in szoveg.encode("utf-8"):
        c = bajt + 0x20 if 0x41 <= bajt <= 0x5A else bajt
        h = (h ^ (((h << 5) & 0xFFFFFFFF) + c + (h >> 2))) & 0xFFFFFFFF
    return h % 1_000_231


def _hash_elojeles_tolassal(szoveg: str) -> int:
    """`sar` helyett `shr` — szintén szándékosan hibás."""
    h = 0x12345678
    for bajt in szoveg.encode("utf-8"):
        c = bajt + 0x20 if 0x41 <= bajt <= 0x5A else bajt
        if c >= 0x80:
            c -= 256
        elojeles = h - 0x100000000 if h & 0x80000000 else h
        h = (h ^ (((h << 5) & 0xFFFFFFFF) + c + (elojeles >> 2))) & 0xFFFFFFFF
    return h % 1_000_231


class TestIdobelyegesMod:
    def test_a_masodpercre_kerekites(self):
        """`(FILETIME + 5e6) / 1e7` — a fél másodperc FÖLFELÉ kerekít."""
        egy_mp = 10_000_000
        assert checksum_idobelyeges(3 * egy_mp) == checksum_idobelyeges(
            3 * egy_mp + 4_999_999
        )
        assert checksum_idobelyeges(3 * egy_mp) != checksum_idobelyeges(
            3 * egy_mp + 5_000_000
        )

    def test_NEM_fugg_utvonaltol_es_merettol(self):
        """A 2. mód aláírásában sem útvonal, sem méret nincs."""
        assert checksum_idobelyeges(123456789) == checksum_idobelyeges(123456789)


class TestUtvonalasMod:
    def test_a_meret_szamit(self):
        assert checksum_utvonalas("C:\\a.jpg", 10**9, 100) != checksum_utvonalas(
            "C:\\a.jpg", 10**9, 101
        )

    def test_az_utvonal_szamit(self):
        assert checksum_utvonalas("C:\\a.jpg", 10**9, 100) != checksum_utvonalas(
            "C:\\b.jpg", 10**9, 100
        )

    def test_az_ido_szamit(self):
        assert checksum_utvonalas("C:\\a.jpg", 10**9, 100) != checksum_utvonalas(
            "C:\\a.jpg", 10**9 + 10**7, 100
        )


class TestModvalasztas:
    """Három kizáró feltétel (`0x004e3bc2` · `0x004e3bcb` · `0x004e3bd7`)."""

    def test_a_rendes_eset_az_utvonalas(self):
        assert utvonalas_modot_kell(kert_mod=1, tipus=2, van_szuloje=True) is True

    @pytest.mark.parametrize(
        ("kert_mod", "tipus", "van_szuloje"),
        [
            (0, 2, True),     # a hívó kifejezetten 0-t kér
            (1, 0, True),     # a rekord típusa 0 (üres slot)
            (1, 2, False),    # nincs szülője (könyvtár)
        ],
    )
    def test_barmelyik_feltetel_a_masodik_modra_valt(
        self, kert_mod, tipus, van_szuloje
    ):
        assert (
            utvonalas_modot_kell(
                kert_mod=kert_mod, tipus=tipus, van_szuloje=van_szuloje
            )
            is False
        )


class TestEllenorzoJelentes:
    """Az összesítő NEM dob — a nem egyező sor ma is használható adat."""

    def test_a_nem_egyezo_sor_NEM_dob_kivetelt(self, caplog):
        import logging

        from picasapy.pmpimport.thumbchecksum import ellenorizd

        with caplog.at_level(logging.WARNING):
            jelentes = ellenorizd([(0xDEADBEEF, "C:\\a.jpg", 10**9, 100)])

        assert jelentes.nem_egyezik == 1
        assert jelentes.egyezik == 0
        assert any("NEM dobjuk el" in r.getMessage() for r in caplog.records), (
            "a nem egyezést jelezni KELL — némán elnyelni ugyanolyan rossz, "
            "mint kivételt dobni miatta"
        )

    def test_az_egyezo_sorokat_MOD_szerint_bontja(self):
        from picasapy.pmpimport.thumbchecksum import (
            checksum_idobelyeges,
            checksum_utvonalas,
            ellenorizd,
        )

        ut, ft, meret = "C:\\kepek\\a.jpg", 132_000_000_000_000_000, 4096
        jelentes = ellenorizd(
            [
                (checksum_utvonalas(ut, ft, meret), ut, ft, meret),
                (checksum_idobelyeges(ft), ut, ft, meret),
                (0, ut, ft, meret),
            ]
        )

        assert jelentes.osszes == 3
        assert jelentes.utvonalas_egyezik == 1
        assert jelentes.idobelyeges_egyezik == 1
        assert jelentes.nem_egyezik == 1
        assert jelentes.egyezes_aranya == pytest.approx(2 / 3)

    def test_ures_bemenetre_teljes_egyezes(self):
        from picasapy.pmpimport.thumbchecksum import ellenorizd

        assert ellenorizd([]).egyezes_aranya == 1.0
