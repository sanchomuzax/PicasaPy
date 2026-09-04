"""#2353: a `[Picasa] date=` kulcsot OLE Variant-alakban kell ÍRNI.

A Picasa a `.picasa.ini` `[Picasa] date=` értékét **`atof`-fal** olvassa
(`0x0044248d`, a `0x00c080d7` CRT-hívás), hibajelzés nélkül. Egy általunk
írt ISO-alakból (`date=2019-07-04`) nála **`2019.0`** lesz, ami Variant-
napként **1905-07-08** — a mappa 1905-be kerül.

Az író oldala is mérve (`0x00710080`): a formátum **`"%f"`**
(`0x00710332`), és **`0.0`-nál kihagyja a sort** (`0x0071031e`).

Élő minta a Picasa 3-tól: `date=46269.390486` — hat tizedes, pontosan a
`%f` alapértelmezése.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from picasapy.ini import (
    parse_document,
    read_folder_date_override,
    with_folder_date_override,
)

_ALAPPONT = datetime(1899, 12, 30)
#: `%f` alapértelmezése: hat tizedes.
_VARIANT_SOR = re.compile(r"^\d+\.\d{6}$")


def _kiirt_ertek(iso: str) -> str:
    doc = with_folder_date_override(parse_document(""), iso)
    szakasz = doc.section("Picasa")
    assert szakasz is not None, "nincs [Picasa] szakasz"
    ertek = szakasz.get("date")
    assert ertek is not None, "nincs date= kulcs"
    return ertek


class TestVariantIras:
    def test_a_kiirt_ertek_VARIANT_alaku(self) -> None:
        """A foga: ISO-t kiírva a Picasa `atof`-ja 2019.0-t kapna."""
        ertek = _kiirt_ertek("2019-07-04")
        assert _VARIANT_SOR.match(ertek), f"nem Variant-alak: {ertek!r}"

    def test_a_kiirt_ertek_UGYANAZT_a_napot_adja(self) -> None:
        """A Picasa oldaláról nézve: `atof`, majd Variant-nap."""
        ertek = _kiirt_ertek("2019-07-04")
        nap = (_ALAPPONT + timedelta(days=float(ertek))).date()
        assert nap.isoformat() == "2019-07-04"

    def test_az_ISO_alak_TOBBE_nem_kerul_ki(self) -> None:
        assert "-" not in _kiirt_ertek("2019-07-04")

    def test_a_sajat_kiirasunkat_visszaolvassuk(self) -> None:
        doc = with_folder_date_override(parse_document(""), "2019-07-04")
        assert read_folder_date_override(doc) == "2019-07-04"

    def test_a_PICASA_irta_ertek_round_trippel(self) -> None:
        """Picasa-írta ini -> beolvasás -> a mi kiírásunk: a `date=`
        numerikusan ugyanaz a nap marad."""
        eredeti = parse_document("[Picasa]\ndate=46269.390486\n")
        iso = read_folder_date_override(eredeti)
        assert iso == "2026-09-04"
        ujra = float(_kiirt_ertek(iso))
        assert int(ujra) == int(float("46269.390486"))
