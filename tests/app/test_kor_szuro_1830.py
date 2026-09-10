"""Az idő-csúszka KOR-szűrő — a mért képlet és a négy felirat (#1830).

## Amit a bináris mond (spec: `docs/specs/picasa-kereses-modok.md`)

A keresősáv csúszkája NEM tartományt választ (a felirata — „Filter by date
range" — az EREDETIBEN is félrevezet), hanem egyetlen értékkel **maximális
KORT** ad meg:

```
s == 0    →  NINCS kor-szűrés
egyébként →  napok = 2 ^ (13 · (1 − s)) + 1
             vágópont = MOST − napok
```

A három konstans a binárisból olvasva: `0xcf4c08 = 13.0`,
`0xcf3a48 = 2.0`, `0xc7e328 = 1.0`; a képlet KÉT független helyen azonos (a
felirat-építő `0x0066345c` és a tényleges szűrő `0x0065ee3f`), és a
második ténylegesen szűkíti a találatokat.

A mértékegység mind **csonkolt** egész (`0x006634b0`):

```
napok < 30                 → „Legfeljebb <trunc(napok)> napos képek.”
trunc(napok/7) < 10        → „Legfeljebb <hetek> hetes képek.”
trunc(napok/30) ≤ 12 vagy trunc(napok/365) == 0 → „… hónapos képek.”
különben                   → „… éves képek.”
```

## Mit mér ez a fájl

A képletet a mért `s → napok` párokon, a feliratot a HATÁROKON (29/30 nap,
9/10 hét, 12/13 hónap), és a lekérdezést a vágóponton. A felirat
szövegformáit a `.tre`-ből átvett négy kulcs adja.
"""

from __future__ import annotations

import math

import pytest

from picasapy.app import kor_szuro


def _tr(szoveg: str) -> str:
    """A `tr` helyettesítője a próbákban — a magyar szöveget nem mérjük."""
    return szoveg


class TestAKepletMertPontjai:
    """A jegy táblájának `s → napok` párjai, a binárisból számolva."""

    @pytest.mark.parametrize(
        "s,napok",
        [
            (0.10, 3328.0),
            (0.20, 1352.2),
            (0.30, 549.7),
        ],
    )
    def test_a_csuszka_ertekebol_napok(self, s: float, napok: float):
        assert kor_szuro.napok(s) == pytest.approx(napok, rel=0.001)

    def test_a_nulla_nem_szur(self):
        assert kor_szuro.napok(0.0) is None

    def test_az_egy_a_legszukebb(self):
        """`s = 1` → 2^0 + 1 = 2 nap; a csúszka jobb széle a legfrissebb."""
        assert kor_szuro.napok(1.0) == pytest.approx(2.0)

    def test_a_hatokoron_kivuli_ertek_hibat_ad(self):
        with pytest.raises(ValueError):
            kor_szuro.napok(1.5)


class TestAFeliratHatarai:
    """A csonkítás miatt a határok EGY nappal is átfordulnak."""

    @pytest.mark.parametrize(
        "napok,vart",
        [
            (1.0, "Pictures up to 1 days old."),
            (29.9, "Pictures up to 29 days old."),
            (30.0, "Pictures up to 4 weeks old."),
            (69.9, "Pictures up to 9 weeks old."),
            (70.0, "Pictures up to 2 months old."),
            (389.0, "Pictures up to 12 months old."),
            (390.0, "Pictures up to 1 years old."),
            (3328.0, "Pictures up to 9 years old."),
        ],
    )
    def test_a_mertekegyseg_valtasa(self, napok: float, vart: str):
        assert kor_szuro.felirat(napok, _tr) == vart

    def test_a_honap_ag_akkor_is_all_ha_az_ev_nulla(self):
        """A mért szabály: `hónap ≤ 12 VAGY év == 0`.

        A `VAGY` nem díszítés: 365 napnál a hónap 12, az év 1 — a hónap-ág
        az `≤ 12` miatt nyer. 370 napnál a hónap 12, tehát még hónap; 390
        napnál a hónap 13 ÉS az év 1, tehát év. Ha valaki `ÉS`-re írja át,
        a 370 nap „1 éves"-re fordul."""
        assert kor_szuro.felirat(370.0, _tr) == "Pictures up to 12 months old."


class TestAVagopont:
    def test_a_vagopont_most_minusz_napok(self):
        from datetime import datetime

        most = datetime(2026, 9, 10, 6, 0, 0)
        assert kor_szuro.vagopont(2.0, most) == datetime(2026, 9, 8, 6, 0, 0)

    def test_a_tort_nap_is_szamit(self):
        """A napok `double`, nem egész — a vágópont órára pontos."""
        from datetime import datetime

        most = datetime(2026, 9, 10, 12, 0, 0)
        assert kor_szuro.vagopont(0.5, most) == datetime(2026, 9, 10, 0, 0, 0)


class TestALekerdezes:
    def test_csak_a_vagopont_UTANI_kepek(self, tmp_path):
        from picasapy.index import open_index
        from picasapy.index.queries import photos_up_to_age

        db = tmp_path / "index.db"
        with open_index(db) as conn:
            conn.execute(
                "INSERT INTO folders(id, path, has_ini) VALUES (1, ?, 0)",
                (str(tmp_path),),
            )
            mappa_id = 1
            for nev, mikor in (
                ("friss.jpg", "2026-09-09T10:00:00"),
                ("regi.jpg", "2020-01-01T10:00:00"),
                ("datum_nelkul.jpg", None),
            ):
                conn.execute(
                    "INSERT INTO photos(folder_id, name, kind, size,"
                    " mtime_ns, taken_at) VALUES (?, ?, 'image', 10, 1, ?)",
                    (mappa_id, nev, mikor),
                )
            conn.commit()

            nevek = {r.name for r in photos_up_to_age(conn, "2026-09-01T00:00:00")}

        assert nevek == {"friss.jpg"}, (
            "a régi képnek ki kell esnie, a dátum nélkülinek pedig nem lehet "
            "kora — ha az utóbbi bent van, a szűrő hamis találatot ad"
        )


class TestAKepletKonstansai:
    def test_a_konstansok_a_binarisbol_valok(self):
        """Ha valaki „szebb" számra írja át, itt bukik el.

        A három érték a Picasa `.text` szakaszából olvasott konstans
        (`0xcf4c08 = 13.0`, `0xcf3a48 = 2.0`, `0xc7e328 = 1.0`) — nem
        hangolható paraméter."""
        assert kor_szuro.KITEVO_SZORZO == 13.0
        assert kor_szuro.ALAP == 2.0
        assert kor_szuro.ELTOLAS == 1.0
        # a képlet ebből következik, tehát a mért pár is ezt adja
        assert math.isclose(
            kor_szuro.ALAP ** (kor_szuro.KITEVO_SZORZO * (1 - 0.1))
            + kor_szuro.ELTOLAS,
            3328.0,
            rel_tol=0.001,
        )
