r"""Két WINDOWS-CSAPDA, ami linuxon láthatatlan (#1082).

A főág windows-lába három egymást követő futáson piros volt, két frissen
bekerült teszt miatt. **Egyik program-hiba sem volt** — mindkettő a teszt
olyan feltevése, ami csak linuxon igaz. Ez a fájl mindkét mechanizmust
rögzíti, PLATFORMFÜGGETLENÜL: linuxon is elbukik, ha valaki visszahozza.

# 1. csapda — a `QSettings` INI-jében a VISSZAPERJEL escape-jel

## A lelet

A `tests/app/qml_functional/test_collage_draft_restore_1051.py` a piszkozat
mappáját **kézzel írta be** a `settings.ini`-be:

```python
(tmp_path / "settings.ini").write_text(f"[collage]\noutputDir={mappa}\n")
```

Linuxon ez ártalmatlan. Windowson viszont a `mappa` visszaperjeles
(`C:\Users\runneradmin\...\kollazsok`), és a `QSettings` az INI-ben a
visszaperjelet **escape-jelként** értelmezi: a `\U` egy Unicode-escape
kezdete, a `\k` pedig egyszerűen elnyeli a perjelet. A visszaolvasott érték
`C:sers\runneradminppData…` lett — egy nem létező mappa.

Következmény: a kollázs-piszkozat mappája sehova nem mutatott, a
visszaállítás felajánlása soha nem jött elő, és a **főág windows-lába három
egymást követő futáson piros volt**.

## Miért a TESZT hibája, és nem a programé

A program az `setValue`-t használja, ami rendesen escape-el
(`outputDir=C:\\Users\\...`), és a visszaolvasás pontos. A `_kezi_ini`
alábbi tesztje ezt a különbséget rögzíti — ha egyszer a Qt megváltoztatná
az INI-escape szabályát, ez a fájl mondja meg, hogy az indoklás elavult.

## Miért kell a harmadik teszt

Az első kettő a MECHANIZMUST írja le. Az ismétlődést viszont csak az
akadályozza meg, ha senki nem ír többé kézzel `settings.ini`-t — ezt a
`TestNincsTobbKeziIni` őrzi, a `test_fajl_url_szerep_1019.py`
QML-keresésének mintájára.

# 2. csapda — a `QUrl.toLocalFile()` Windowson is PER-JELES

A `test_fajl_url_szerep_1019.py` így állított:

```python
assert url.toLocalFile() == str(tmp_path / "kép #1.jpg")
```

A Qt `C:/Users/...`-t ad vissza, a `str(Path(...))` viszont
`C:\Users\...`-t. Ugyanaz a fájl, kétféle írásmód. A programot ez sem
érinti: a `formatting.to_local_path` pontosan ezért futtatja át `Path`-on
a visszaalakított útvonalat — a kommentje is ezt mondja.

A tanulság általános: **útvonalat `Path`-ként hasonlíts, ne sztringként.**
"""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

import pytest
from PySide6.QtCore import QSettings, QUrl

from picasapy.app.collage_prefs import OUTPUT_DIR_KEY

#: Windowsos alakú útvonal — a `\U`, a `\A` és a `\k` mind más módon romlik el.
WINDOWSOS_UT = r"C:\Users\runneradmin\AppData\Local\Temp\pytest-0\kollazsok"


def _ini(tmp_path: Path) -> Path:
    return tmp_path / "settings.ini"


class TestASzabalyosIras:
    """`QSettings.setValue` → `value`: az útvonal bitre visszajön."""

    def test_a_windowsos_utvonal_korbejar(self, tmp_path):
        settings = QSettings(str(_ini(tmp_path)), QSettings.Format.IniFormat)
        settings.setValue(OUTPUT_DIR_KEY, WINDOWSOS_UT)
        settings.sync()

        vissza = QSettings(str(_ini(tmp_path)), QSettings.Format.IniFormat)

        assert vissza.value(OUTPUT_DIR_KEY) == WINDOWSOS_UT

    def test_a_fajlban_kettozott_visszaperjel_all(self, tmp_path):
        """A bizonyíték, hogy az escape-elés tényleg a `QSettings` dolga."""
        settings = QSettings(str(_ini(tmp_path)), QSettings.Format.IniFormat)
        settings.setValue(OUTPUT_DIR_KEY, WINDOWSOS_UT)
        settings.sync()

        assert r"C:\\Users\\runneradmin" in _ini(tmp_path).read_text(encoding="utf-8")


class TestAKeziIrasELBUKNA:
    """A jegy bizonyítéka, tesztként — a kézi INI-írás elrontja az utat.

    Ha ez az állítás egyszer megfordul (a Qt máshogy kezeli az escape-et),
    akkor a #1082 indoklása is elavult; ezért áll itt, és nem csak a
    docstringben."""

    def test_a_kezzel_irt_sor_nem_jon_vissza_epen(self, tmp_path):
        _ini(tmp_path).write_text(
            f"[collage]\noutputDir={WINDOWSOS_UT}\n", encoding="utf-8"
        )

        olvasat = QSettings(
            str(_ini(tmp_path)), QSettings.Format.IniFormat
        ).value(OUTPUT_DIR_KEY)

        assert olvasat != WINDOWSOS_UT
        assert "Users" not in str(olvasat)


class TestNincsTobbKeziIni:
    """Egyetlen teszt se írjon kézzel `settings.ini`-t — ez az igazi őr."""

    #: Amivel egy fájl kézzel íródhat. A `QSettings` NEM ezeken megy át.
    _IRO_HIVASOK = ("write_text", "write_bytes", "writelines")

    def _talalatok(self) -> list[str]:
        gyoker = Path(__file__).resolve().parents[1]
        talalatok = []
        for ut in gyoker.rglob("test_*.py"):
            if ut.name == Path(__file__).name:
                continue
            sorok = ut.read_text(encoding="utf-8").splitlines()
            for szam, sor in enumerate(sorok, start=1):
                if "settings.ini" not in sor:
                    continue
                # a hívás a következő sorra is átcsúszhat (fekete formázás)
                kornyek = " ".join(sorok[szam - 1 : szam + 2])
                if any(hivas in kornyek for hivas in self._IRO_HIVASOK):
                    talalatok.append(f"{ut.relative_to(gyoker)}:{szam}")
        return talalatok

    def test_egyetlen_teszt_sem_irja_kezzel(self):
        talalatok = self._talalatok()

        assert not talalatok, (
            "kézzel írt settings.ini — a visszaperjel escape-elődik "
            "(#1082), használj QSettings.setValue-t: " + ", ".join(talalatok)
        )


class TestAzUtvonalOsszehasonlitas:
    """2. csapda: `toLocalFile()` per-jeles, a `str(Path)` visszaperjeles."""

    def test_a_ket_irasmod_ugyanaz_a_fajl(self):
        """`Path`-ként azonos — ezért szabad így összehasonlítani."""
        perjeles = PureWindowsPath(r"C:/Users/runneradmin/kép #1.jpg")
        visszaperjeles = PureWindowsPath(r"C:\Users\runneradmin\kép #1.jpg")

        assert perjeles == visszaperjeles

    def test_SZTRINGKENT_viszont_kulonbozik(self):
        """A jegy bizonyítéka: a sztring-egyenlőség windowsos úton elbukik."""
        assert r"C:/Users/runneradmin/kép #1.jpg" != r"C:\Users\runneradmin\kép #1.jpg"

    def test_a_Qt_perjelre_normalizal(self, tmp_path):
        """Platformfüggetlen: a `toLocalFile()` sosem ad vissza visszaperjelet.

        Linuxon ez triviálisan igaz, windowsi úton pedig épp ez a csapda —
        az állítás mindkét helyen ugyanaz, ezért itt is elbukna, ha a Qt
        egyszer megváltoztatná a szabályt."""
        url = QUrl.fromLocalFile(str(tmp_path / "kép #1.jpg"))

        assert "\\" not in url.toLocalFile()


@pytest.mark.parametrize("nev", ["collage/outputDir"])
def test_a_kulcs_neve_nem_valtozott(nev):
    """Az őr a kulcson át fog: ha átnevezik, itt derüljön ki."""
    assert OUTPUT_DIR_KEY == nev
