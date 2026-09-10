"""A kék infósáv két hiányzó eleme: címke-szám és a méret KÉT alakja (#1913).

## A mérés (spec: `docs/specs/kek-info-sav.md` 2., 7. és 10. szakasz)

A sáv szövegét az eredetiben EGY függvény állítja össze (`FUN_0056fbc0`), és
két dolog hiányzott nálunk:

**1. A méret-felirat két alakja.** A választás feltétele NEM
időbélyeg-összehasonlítás, hanem a két FORMÁZOTT dátum sztring-egyenlősége
(`0x00570266 sete al`):

| eset | kulcs | angol | magyar |
|---|---|---|---|
| a két dátum FORMÁZVA egyenlő | `il_GetSelectionInfo::5` | `     %s      %s on disk` | `     %1$s      %2$s/lemez` |
| különböző | `il_GetSelectionInfo::4` | `     %s to %s     %s on disk` | `     %1$s-%2$s     %3$s a lemezen` |

Ebből következik, hogy **nincs időablak**: ugyanaznap 00:01 és 23:59 is az
`::5` alakot adja, mert a napra pontos formátum ugyanazt a szöveget adja.

**2. A címke-rész.** A sáv szövegének UTOLSÓ, feltételes darabja
(`0x0057040e`–`0x00570442`): a honosított `Címkék: ` előtag, címkénként
`<név> (<darabszám>)`, öt szóköz elválasztóval a méret után — és **ha nincs
címke, az elválasztó sem kerül ki**.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QLocale

from picasapy.app.formatting import status_text


@dataclass
class _Rekord:
    """A `status_text` ennyit használ a rekordból."""

    size: int = 1024 * 1024
    taken_at: str | None = None
    keywords: str | None = None
    mtime_ns: int = 0
    name: str = "a.jpg"
    folder_path: str = "/kepek"


def _tr(szoveg: str) -> str:
    return szoveg


def _tr_n(szoveg: str, _komment: str, szam: int) -> str:
    return f"{szam} pictures"


def _szoveg(rekordok) -> str:
    return status_text(rekordok, QLocale("en_US"), _tr, _tr_n)


class TestAMeretKetAlakja:
    def test_azonos_datum_az_OTODIK_alak(self):
        """Egy nap → `::5`: EGY dátum, öt-öt szóközzel."""
        rekordok = [
            _Rekord(taken_at="2026-01-02T00:01:00"),
            _Rekord(taken_at="2026-01-02T23:59:00"),
        ]

        szoveg = _szoveg(rekordok)

        assert " to " not in szoveg, (
            "azonos (formázott) dátumnál nincs tartomány — a mérés szerint a "
            "feltétel a FORMÁZOTT szövegek egyenlősége, tehát nincs időablak"
        )
        assert szoveg.count("     ") >= 2, (
            "az `::5` alak öt szóközzel kezdődik, és a dátum után is öt-hat "
            "szóköz áll (a mért formátum: `     %s      %s on disk`)"
        )

    def test_kulonbozo_datum_a_NEGYEDIK_alak(self):
        rekordok = [
            _Rekord(taken_at="2026-01-02T12:00:00"),
            _Rekord(taken_at="2026-03-04T12:00:00"),
        ]

        szoveg = _szoveg(rekordok)

        assert " to " in szoveg or "-" in szoveg, (
            "eltérő dátumnál a mért alak tartományt ír (`%s to %s`)"
        )

    def test_a_ket_alak_KULONBOZIK(self):
        """A lényeg: a két eset NEM ugyanazt a formátumot használja.

        Magyarul ez a „24,7 MB/lemez" vs „86,5 MB a lemezen" különbség; a
        próba nyelvfüggetlenül azt méri, hogy a két formátum-sztring nem
        ugyanaz."""
        egy_nap = _szoveg([_Rekord(taken_at="2026-01-02T10:00:00")])
        ket_nap = _szoveg(
            [
                _Rekord(taken_at="2026-01-02T10:00:00"),
                _Rekord(taken_at="2026-02-02T10:00:00"),
            ]
        )
        assert egy_nap != ket_nap


class TestACimkeResz:
    def test_a_cimke_a_szoveg_VEGERE_kerul(self):
        rekordok = [
            _Rekord(taken_at="2026-01-02T10:00:00", keywords="AI image"),
            _Rekord(taken_at="2026-01-02T11:00:00", keywords="AI image"),
            _Rekord(taken_at="2026-01-02T12:00:00", keywords=None),
        ]

        szoveg = _szoveg(rekordok)

        assert szoveg.endswith("Tags: AI image (2)"), (
            "a címke-rész a sáv UTOLSÓ darabja, és a darabszám a CÍMKÉZETT "
            f"képek száma (nem a kijelöltek): {szoveg!r}"
        )
        assert "     Tags:" in szoveg, "az elválasztó öt szóköz (mérve)"

    def test_cimke_nelkul_NINCS_elvalaszto_sem(self):
        szoveg = _szoveg([_Rekord(taken_at="2026-01-02T10:00:00")])

        assert "Tags" not in szoveg
        assert not szoveg.endswith(" "), (
            "címke nélkül az öt szóközös elválasztó sem kerül ki (mérve: "
            "`0x00570424` NULL-ág)"
        )

    def test_tobb_cimke_mindegyike_kimegy(self):
        rekordok = [
            _Rekord(taken_at="2026-01-02T10:00:00", keywords="nyár, tenger"),
            _Rekord(taken_at="2026-01-02T11:00:00", keywords="tenger"),
        ]

        szoveg = _szoveg(rekordok)

        assert "tenger (2)" in szoveg
        assert "nyár (1)" in szoveg

    def test_ures_cimke_nem_szamit(self):
        """A mérés szerint a nulla hosszú és az üres címke is kimarad."""
        szoveg = _szoveg(
            [_Rekord(taken_at="2026-01-02T10:00:00", keywords="  ,  ")]
        )
        assert "Tags" not in szoveg
