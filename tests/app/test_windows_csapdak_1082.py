r"""Két WINDOWS-CSAPDA, ami linuxon láthatatlan — ŐRTESZT (#1082).

A főág windows-lába három egymást követő futáson piros volt, két frissen
bekerült teszt miatt. **Egyik eset sem volt program-hiba** — mindkettő a
teszt olyan feltevése, ami csak linuxon igaz.

**A két konkrét bukást a #1077 már megjavította** (0.8.20). Ez a fájl nem
azt javítja újra: azt akadályozza meg, hogy **visszajöjjenek**. Mindkét
mechanizmus platformfüggetlenül van rögzítve, tehát **linuxon is elbukik**,
ha valaki újra beleesik — ez a lényeg, mert a windows-lábon a hiba mindig
csak utólag, a főágon derül ki.

# 1. csapda — a `QSettings` INI-jében a VISSZAPERJEL escape-jel

A `test_collage_draft_restore_1051.py` a piszkozat mappáját **kézzel** írta
be a `settings.ini`-be:

```python
(tmp_path / "settings.ini").write_text(f"[collage]\noutputDir={mappa}\n")
```

Linuxon ez ártalmatlan. Windowson viszont a `mappa` visszaperjeles
(`C:\Users\runneradmin\...\kollazsok`), és a `QSettings` az INI-ben a
visszaperjelet **escape-jelként** értelmezi: a `\U` egy Unicode-escape
kezdete, a `\k` pedig egyszerűen elnyeli a perjelet. A visszaolvasott érték
`C:sers\runneradminppData…` lett — egy nem létező mappa. A CI-napló szó
szerint ezt mutatta, `WinError 123` kíséretében.

**Miért nem mentette meg a conftest.** A `qml_functional/conftest.py` csak
akkor állítja be a saját kimeneti mappáját, `ha not settings.value(...)` — a
romlott érték viszont *igaznak* látszik, tehát a tartalék nem lépett közbe.

**Miért a teszté a hiba, és nem a programé.** A program `setValue`-val ír,
ami rendesen escape-el (`outputDir=C:\\Users\\...`), és pontosan olvas
vissza. A `TestAKeziIrasELBUKNA` ezt a különbséget rögzíti — ha a Qt egyszer
megváltoztatná az INI-escape szabályát, ez a fájl mondja meg, hogy a #1082
indoklása elavult.

# 2. csapda — a `QUrl.toLocalFile()` Windowson is PER-JELES

A `test_fajl_url_szerep_1019.py` így állított:

```python
assert url.toLocalFile() == str(tmp_path / "kép #1.jpg")
```

A Qt `C:/Users/...`-t ad vissza, a `str(Path(...))` viszont
`C:\Users\...`-t. Ugyanaz a fájl, kétféle írásmód. A programot ez sem
érinti: a `toLocalFile()` az egész forrásfában EGY helyen szerepel, a
`formatting.to_local_path`-ban, ami épp ezért futtatja át `Path`-on a
visszaalakított útvonalat — a docstringje ezt ki is mondja. Minden hívó
(`drop_import`, `export`, `create`, `print`, `webexport`, `import_source`,
`fileops`) ezen megy át.

A tanulság általános: **útvonalat normalizálva hasonlíts, ne sztringként.**

# Miért a harmadik osztály a legfontosabb

Az első kettő a MECHANIZMUST írja le. Az ismétlődést viszont csak az
akadályozza meg, ha senki nem ír többé kézzel `settings.ini`-t — ezt a
`TestNincsTobbKeziIni` őrzi, a `test_fajl_url_szerep_1019.py`
QML-keresésének mintájára.
"""

from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath

import pytest
from PySide6.QtCore import QSettings, QUrl

from picasapy.app.collage_prefs import OUTPUT_DIR_KEY
from picasapy.app.formatting import to_file_url, to_local_path

#: Windowsos alakú útvonal — a `\U`, a `\A` és a `\k` mind más módon romlik el.
WINDOWSOS_UT = r"C:\Users\runneradmin\AppData\Local\Temp\pytest-0\kollazsok"


def _ini(tmp_path: Path) -> Path:
    return tmp_path / "settings.ini"


def _nativ(posix_alak: str) -> str:
    """A várt útvonal a FUTTATÓ platform natív írásmódjában (#1634).

    A `to_local_path` a végén `str(Path(...))`-ot ad vissza, tehát Windowson
    VISSZAperjelre vált. Egy per-jeles sztringet beégetni ezért nem mérce,
    hanem platform-feltevés — a #1626 négy állítása pontosan ezen bukott el a
    windows-lábon, miközben a program helyesen működött.

    A várt értéket ugyanazzal a normalizálással állítjuk elő, amivel a
    termék is dolgozik: így a mérce a KÉT írásmód különbségére vak, a
    tartalmi eltérésre viszont nem."""
    return str(Path(posix_alak))


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

        olvasat = QSettings(str(_ini(tmp_path)), QSettings.Format.IniFormat).value(
            OUTPUT_DIR_KEY
        )

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
                # a hívás a következő sorra is átcsúszhat (a formázó tördeli)
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
        """Normalizálva azonos — ezért szabad így összehasonlítani."""
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


class TestAProgramSzerzodese:
    """A valódi szerződés: `to_file_url` → `to_local_path` = azonosság.

    Ez az, amit a program tényleg csinál, és ez az, ami platformfüggetlenül
    a NATÍV alakot adja vissza — mert a `to_local_path` `Path`-on futtat át.
    Ha valaki ezt a normalizálást kiveszi, itt derül ki, nem a windows-CI-n
    két nappal később."""

    @pytest.mark.parametrize(
        "nev", ["a.jpg", "kép #1.jpg", "árvíztűrő tükörfúrógép.jpg"]
    )
    def test_a_ket_iranyt_egymas_utan_futtatva_azonossag(self, tmp_path, nev):
        ut = str(tmp_path / nev)

        assert to_local_path(to_file_url(ut).toString()) == ut

    def test_ures_bemenetre_ures_marad(self):
        assert to_file_url("").isEmpty()
        assert to_local_path("") == ""


def test_a_kulcs_neve_nem_valtozott():
    """Az őr a kulcson át fog: ha átnevezik, itt derüljön ki."""
    assert OUTPUT_DIR_KEY == "collage/outputDir"


class TestAMeghajtobetusUrlLinuxonIsMerheto:
    """#1626: a `file:///C:/...` URL feloldása — a WINDOWSOS ág, Linuxon.

    A Qt a meghajtóbetű elé tett perjelet csak Windowson szedi le
    (`QUrlPrivate::toLocalFile`, `#ifdef Q_OS_WIN`), ezért a `to_local_path`
    ezt a lépést a `_platform()` fogantyún át maga is elvégzi (#1217). Így
    az az ág, amelyik a #1626-ban éles hibát okozott, itt, Linuxon is
    mérhető — nem kell hozzá windows-CI-kör.

    A mért hiba: az `ExportDialogs.qml` a `file://` előtagot nyersen
    levágta, `/C:/Users/...` maradt, és a `mkdir` `WinError 123`-mal
    elhasalt — a Google Earth-KML SOHA nem készült el a windows-lábon.

    ## #1634 — a fogantyú jó volt, a MÉRCE maradt POSIX-alakú

    Ez a négy állítás eredetileg BEÉGETETT, per-jeles sztringgel mért
    (`== "C:/Temp/pp"`), és mind a négy elbukott a windows-lábon (futás
    `33085887241`) — miközben a program pontosan azt csinálta, amit kell:

    | bemenet | `_platform()` | linux | windows |
    |---|---|---|---|
    | `file:///C:/Temp/pp` | `win32` | `C:/Temp/pp` | `C:\\Temp\\pp` |
    | `file:///tmp/kep.jpg` | `win32` | `/tmp/kep.jpg` | `\\tmp\\kep.jpg` |
    | `/C:/Temp/pp` | — | `/C:/Temp/pp` | `\\C:\\Temp\\pp` |

    A javítás NEM az állítás gyengítése: a várt értéket ugyanazzal a
    `Path`-normalizálással állítjuk elő (`_nativ`), amivel a termék is
    dolgozik, a lényeget pedig — hogy a meghajtóbetű elé nem kerülhet
    perjel — egy szeparátor-független `PureWindowsPath`-állítás mondja ki.

    A MÉRŐ láb a linuxos: a vezető perjel visszatétele (a `_platform()`-
    kapuzott levágás törlése) itt megbuktatja az első állítást, Windowson
    viszont a Qt már maga elvégezte a levágást, tehát ott nem is látszana.
    Pontosan ezért íródott ez az osztály Linuxra.
    """

    def test_windowson_a_meghajtobetu_elol_eltunik_a_per(self, monkeypatch):
        from picasapy.app import formatting

        monkeypatch.setattr(formatting, "_platform", lambda: "win32")

        eredmeny = formatting.to_local_path("file:///C:/Temp/pp")

        assert eredmeny == _nativ("C:/Temp/pp")
        # …és a szeparátortól FÜGGETLENÜL: a meghajtóbetű az út ELEJÉN áll.
        # A `/C:/…` alakra ez üres meghajtót adna — épp az a #1626 hibája.
        assert PureWindowsPath(eredmeny).drive == "C:"

    def test_a_posix_ut_valtozatlan_marad_a_windowsos_agon_is(self, monkeypatch):
        """A meghajtó-levágás nem eshet rá közönséges POSIX útra."""
        from picasapy.app import formatting

        monkeypatch.setattr(formatting, "_platform", lambda: "win32")

        assert formatting.to_local_path("file:///tmp/kep.jpg") == _nativ(
            "/tmp/kep.jpg"
        )

    def test_a_posix_agon_nem_nyulunk_a_meghajtobetus_alakhoz(self, monkeypatch):
        """POSIX-on a `/C:/…` VALÓDI (bár szokatlan) útvonal lehet — a
        levágás ott adatvesztő volna, ezért a fogantyú dönt, nem a minta.

        A mérce itt a Qt SAJÁT kimenete: a posix ág nem tehet hozzá és nem
        vehet el belőle semmit, csak normalizál. Linuxon ez a valódi mérés
        (a Qt `/C:/Temp/pp`-t ad, tehát a fölösleges levágás azonnal
        látszana); Windowson a Qt maga már levágta a perjelet, ott az
        állítás annyit mond, hogy utólag mi sem nyúltunk hozzá. A mérő láb
        tehát a linuxos — ezért is íródott ide ez az osztály."""
        from picasapy.app import formatting

        monkeypatch.setattr(formatting, "_platform", lambda: "linux")
        qt_alak = QUrl("file:///C:/Temp/pp").toLocalFile()

        assert formatting.to_local_path("file:///C:/Temp/pp") == _nativ(qt_alak)

    def test_a_nyers_ut_erintetlen_marad(self):
        """Csak a `file:`-előtagos bemenetet oldjuk fel — a sima útvonalat
        nem. (A #1626 hibás alakja pont ilyen volt: `/C:/Temp/pp`.)

        „Érintetlen" itt az ÚTVONALRA értendő, nem a karakterekre: a
        `Path`-normalizálás Windowson a szeparátort így is átírja
        (`\\C:\\Temp\\pp`) — a vezető perjelet viszont nem szedi le."""
        from picasapy.app import formatting

        assert formatting.to_local_path("/C:/Temp/pp") == _nativ("/C:/Temp/pp")


class TestNincsBeegetettPerjelesMerce:
    """3. csapda: a `to_local_path` VÁRT értékét beégetni platform-feltevés.

    Ez az igazi őr a #1634-re — ugyanaz a szerep, mint a
    `TestNincsTobbKeziIni`-é a #1082-re. Az egyes állítások javítása
    egyszeri; azt, hogy a hibaosztály ne jöjjön vissza, csak egy
    fájlokon átfutó ellenőrzés tudja.

    A tiltott alak: `to_local_path(...) == "…/…"`, azaz szeparátort
    tartalmazó SZTRING-irodalom a jobb oldalon. A helyes alak a `_nativ()`
    (vagy bármi, ami a várt értéket `Path`-on át állítja elő).

    ⚠️ A SAJÁT fájlját kihagyja — ahogy a `TestNincsTobbKeziIni` is —, mert
    az alábbi két önteszt épp a tiltott alakot tartalmazza szövegként. A
    fájlon belüli visszaesést tehát nem ez fogja meg, hanem a
    `TestAMeghajtobetusUrlLinuxonIsMerheto` `PureWindowsPath`-állítása.
    """

    #: A tiltott alak. Csak a szeparátort TARTALMAZÓ irodalomra szólal meg:
    #: a `to_local_path("") == ""` szabályos, ott nincs mit normalizálni.
    _MINTA = re.compile(
        r"""to_local_path\([^\n]*\)\s*==\s*(?:r?["'])[^"'\n]*[/\\][^"'\n]*["']"""
    )

    def _talalatok(self) -> list[str]:
        gyoker = Path(__file__).resolve().parents[1]
        talalatok = []
        for ut in gyoker.rglob("test_*.py"):
            if ut.name == Path(__file__).name:
                continue
            sorok = ut.read_text(encoding="utf-8").splitlines()
            elozo_talalat = 0
            for szam in range(1, len(sorok) + 1):
                # a hívás a következő sorra is átcsúszhat (a formázó tördeli)
                kornyek = " ".join(sorok[szam - 1 : szam + 1])
                if not self._MINTA.search(kornyek):
                    continue
                # a kétsoros ablak ugyanazt a hibát kétszer látná meg
                if szam - 1 == elozo_talalat:
                    continue
                elozo_talalat = szam
                talalatok.append(f"{ut.relative_to(gyoker)}:{szam}")
        return talalatok

    def test_egyetlen_teszt_sem_eget_be_perjeles_mercet(self):
        talalatok = self._talalatok()

        assert not talalatok, (
            "beégetett, per-jeles várt érték a to_local_path mellett — "
            "Windowson a visszaperjel miatt elbukik (#1634); állítsd elő "
            "`str(Path(...))`-szal: " + ", ".join(talalatok)
        )

    def test_az_or_FELISMERI_a_regi_hibas_alakot(self):
        """Az őr foga: a #1634-ben bukott sorokat tényleg megfogja."""
        assert self._MINTA.search(
            'assert formatting.to_local_path("file:///C:/Temp/pp") == "C:/Temp/pp"'
        )
        assert self._MINTA.search(
            'assert to_local_path("file:///tmp/kep.jpg") == "/tmp/kep.jpg"'
        )

    def test_az_or_NEM_szol_a_helyes_alakra(self):
        """…és nem szól arra, ami platformfüggetlenül állítja elő a mércét."""
        assert not self._MINTA.search(
            'assert to_local_path("file:///C:/Temp/pp") == _nativ("C:/Temp/pp")'
        )
        assert not self._MINTA.search('assert to_local_path("") == ""')
