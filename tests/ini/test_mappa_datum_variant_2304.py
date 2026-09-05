"""#2304 — a valódi Picasa a mappa dátumát VARIANT-IDŐKÉNT írja, nem ISO-ként.

## A bizonyíték

A tulajdonos gépén a Picasa 3 által írt `.picasa.ini`
(`My Pictures/mappa-rendezesenek-alapja-datum/`, 2026-09-04):

```ini
[Picasa]
P2category=Exported Pictures
date=46269.390486
```

A `46269.390486` **OLE Variant-idő** — napok az 1899-12-30-i alapponttól:

    1899-12-30 + 46269,390486 nap = 2026-09-04 09:22:17

…és a mappa **pontosan akkor** jött létre (a mellette lévő képernyőmentés
09:19-kor készült). Az érték tehát nem véletlen egybeesés.

## Miért hiba

A `read_folder_date_override` eddig **csak ISO-alakot** fogadott
(`^\\d{4}-\\d{2}-\\d{2}$`), ezért a valódi Picasa-mappák dátumát **némán
eldobta**, és a szinkron a legrégebbi felvételi időre esett vissza. A modul
docstringje maga jelezte előre ezt az esetet: *„ha valódi Picasa-ini-ben
élő (elő)forduló mappa-dátum kulcs kerül elő, a specet frissíteni kell."*
Most előkerült.

⚠️ A saját írásunk **ISO** marad (`with_folder_date_override`), tehát az
olvasónak MINDKÉT alakot értenie kell.
"""

from __future__ import annotations

import pytest

from picasapy.ini import parse_document, read_folder_date_override

#: A tulajdonos gépéről származó, valódi Picasa-írta érték.
VALODI = "46269.390486"
VALODI_NAPJA = "2026-09-04"


def _dok(szoveg: str):
    return parse_document(szoveg)


class TestAVariantIdo:
    def test_a_VALODI_ertek_a_helyes_napot_adja(self):
        dok = _dok("[Picasa]\nP2category=Exported Pictures\n"
                   f"date={VALODI}\n")
        assert read_folder_date_override(dok) == VALODI_NAPJA

    @pytest.mark.parametrize(
        ("variant", "nap"),
        [
            ("37622.0", "2003-01-01"),
            ("45000.0", "2023-03-15"),
            ("46269.390486", "2026-09-04"),
            # egész szám tizedespont nélkül is előfordul
            ("40000", "2009-07-06"),
        ],
    )
    def test_tobb_ertek_a_MERT_alappontrol(self, variant, nap):
        """Az alappont 1899-12-30 — ugyanaz, mint a Picasa többi
        Variant-mezőjénél."""
        dok = _dok(f"[Picasa]\ndate={variant}\n")
        assert read_folder_date_override(dok) == nap


class TestAzISOalakMEGMARAD:
    """A saját írásunk ISO — az olvasó nem törhet el tőle."""

    def test_iso_valtozatlanul_atmegy(self):
        dok = _dok("[Picasa]\ndate=2019-07-04\n")
        assert read_folder_date_override(dok) == "2019-07-04"


class TestAmitELUTASIT:
    @pytest.mark.parametrize(
        "ertek",
        [
            "",
            "nem-datum",
            "2019-13-45",          # ISO-alakú, de értelmetlen nap
            "-5",                  # az alappont ELŐTT
            "9999999",             # túl messze a jövőben
        ],
    )
    def test_ertelmetlen_ertekre_None(self, ertek):
        dok = _dok(f"[Picasa]\ndate={ertek}\n")
        assert read_folder_date_override(dok) is None

    def test_hianyzo_kulcsra_None(self):
        assert read_folder_date_override(_dok("[Picasa]\n")) is None
