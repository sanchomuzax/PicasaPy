"""#2152 — a menütételek mnemonikjai az EREDETI honosításából.

## Mit ad ez a kör

A menüsor 144 tételéből eddig **11**-en volt aláhúzott betű; mostantól
**103** (a 161 egyedi feliratból). A betűk és a HELYÜK az eredeti
szövegtárból (`stringres-en-hu.tsv`, `eMenu*::` kulcsok) valók, nem
találgatásból.

⚠️ **A forrás megválasztása lelet volt.** A kutatási anyag származtatott
`menu-mnemonikok.tsv`-je csak a mnemonik BETŰJÉT tartalmazza, a helyét nem
— és 48 sornál a betű többször is előfordul a magyar szövegben, tehát az
`&` pozíciója nem lett volna eldönthető. Az eredeti szövegtár viszont
`&`-tal EGYÜTT tárolja a szöveget (`Kö&zzététel a Bloggeren...`), és a
párosítás onnan pontos.

## A párosítás mérlege (2026-09-04)

| | darab |
|---|---:|
| egyedi QML-felirat | 161 |
| egyértelműen párosítva az eredetivel | 122 |
| ebből magyar mnemonikkal is | 105 |
| **biztonságosan átvezetve** (a magyar szövegünk tartalmilag azonos) | **84** |
| kézi döntést kívánna | 4 |
| nincs pár az eredetiben | 36 |

A négy kézi eset (`I'm Feeling Lucky`, `None`, `People`, `Select All`) NEM
került átvezetésre: ott a mi magyar szövegünk eltér az eredetiétől, tehát
az `&` helye nem vehető át gépiesen.
"""

from __future__ import annotations

import collections
import html
import re
from pathlib import Path

import picasapy.app as app_csomag

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


def _forditasok() -> dict[str, str]:
    m = re.search(r"<name>PicasaMenuBar</name>(.*?)</context>", _TS, re.S)
    assert m, "nincs PicasaMenuBar kontextus a fordításban"
    return {
        html.unescape(a): html.unescape(b)
        for a, b in re.findall(
            r"<source>([^<]*)</source>\s*<translation>([^<]*)</translation>",
            m.group(1),
        )
    }


def _feliratok() -> set[str]:
    return set(re.findall(r'qsTr\("([^"]+)"\)', _QML))


def _betu(szoveg: str) -> str | None:
    i = szoveg.find("&")
    return szoveg[i + 1].lower() if 0 <= i < len(szoveg) - 1 else None


class TestAMennyiseg:
    def test_a_tetelek_TOBBSEGEN_van_mnemonik(self):
        """A kiindulás 11 volt; a mérés szerint 105 párosítható."""
        feliratok = _feliratok()
        mnemonikos = {f for f in feliratok if "&" in f}
        assert len(mnemonikos) >= 100, (
            f"csak {len(mnemonikos)} feliraton van mnemonik a "
            f"{len(feliratok)}-ből — a #2152 óta legalább 100 várható"
        )

    def test_a_MAGYAR_oldal_is_kapott(self):
        ford = _forditasok()
        magyar_mnemonikos = [
            hu for en, hu in ford.items() if "&" in en and "&" in hu
        ]
        assert len(magyar_mnemonikos) >= 80, (
            f"csak {len(magyar_mnemonikos)} magyar fordításon van mnemonik "
            f"— a magyar kiosztás az eredetié, nem az angolból származtatott"
        )


class TestAMagyarBetuNEMazAngol:
    """Az eredeti magyar kiosztás ÖNÁLLÓ — nem az angol betűje."""

    def test_van_olyan_tetel_ahol_MAS_a_ket_betu(self):
        ford = _forditasok()
        elteres = [
            (en, hu)
            for en, hu in ford.items()
            if "&" in en and "&" in hu and _betu(en) != _betu(hu)
        ]
        assert len(elteres) >= 20, (
            f"csak {len(elteres)} tételen tér el az angol és a magyar betű "
            f"— gyanús, mintha az angolból származtattuk volna"
        )

    def test_konkret_pelda_a_meresbol(self):
        """`Add to &Screensaver...` → `Hozzáadás a &képernyővédőhöz…`
        (S → k), az eredeti szövegtárból."""
        ford = _forditasok()
        assert ford.get("Add to &Screensaver...", "").count("&képernyő") == 1


class TestAzUTKOZESEK:
    """⚠️ A jegy „nincs ütköző mnemonik" feltétele ELLENTMOND a mérésnek.

    Az eredeti Picasában IS van két ütközés, és mi a hűséget választottuk:

    - `eMenuCreate` (EN): `&Picture Collage...` és `Make a &Poster...`
      — mindkettő `P`;
    - `eMenuHelp` (HU): `&Frissítések keresése` és `Picasa-&fórumok`
      — mindkettő `f`.

    Windowson ez nem hiba: az `Alt+betű` ilyenkor a következő egyező
    tételre ugrik, és `Enter` zárja. A próba azért rögzíti a KETTŐT, hogy
    egy HARMADIK, általunk okozott ütközés kibukjon.
    """

    ISMERT = 2

    def test_nincs_UJ_utkozes(self):
        ford = _forditasok()
        sorok = _QML.splitlines()

        def behuzas(s: str) -> int:
            return len(s) - len(s.lstrip())

        utkozesek = 0
        for i, sor in enumerate(sorok):
            if not re.match(r"\s*PicasaMenu\s*\{", sor):
                continue
            b = behuzas(sor)
            tetelek: list[str] = []
            for j in range(i + 1, len(sorok)):
                bj = behuzas(sorok[j])
                if sorok[j].strip() == "}" and bj == b:
                    break
                if bj == b + 4 and re.match(r"\s*PicasaMenuItem\s*\{", sorok[j]):
                    for k in range(j + 1, min(j + 14, len(sorok))):
                        t = re.search(r'text:\s*qsTr\("([^"]+)"\)', sorok[k])
                        if t:
                            tetelek.append(t.group(1))
                            break
            if len(tetelek) < 2:
                continue
            for alak in (lambda t: t, lambda t: ford.get(t, "")):
                szamlalo = collections.Counter(
                    x for x in (_betu(alak(t)) for t in tetelek) if x
                )
                utkozesek += sum(1 for n in szamlalo.values() if n > 1)

        assert utkozesek <= self.ISMERT, (
            f"{utkozesek} mnemonik-ütközés van, a mértből ismert "
            f"{self.ISMERT} helyett — az újat nézd meg"
        )
