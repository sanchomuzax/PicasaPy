"""#1719 ŐR: a QML-fa előrefordítása telepítéskor tényleg megtörténik.

## Mit véd

A Qt a QML-t induláskor fordítja bájtkóddá, és a lemezes gyorsítótára a
forrás **időbélyegéhez** van kötve. A `pip install --upgrade` minden
fájlt frissre ír, ezért minden telepítés/frissítés után az első indulás
újrafordítja a teljes, 141 fájlos fát. A #1719 megoldása: a
`qmlcachegen` a telepítéskor előállítja ugyanazt a bájtkódot, **nulla**
forrás-időbélyeggel — a Qt az ilyen egységet dátum-összevetés nélkül
fogadja el.

## Miért NEM időt mér

A #1653/#1689 tanulsága: a szakasz-idők ezen a gépen 2,4 és 6,0 s között
ingadoznak azonos kódon. Az őr ezért **munkamennyiséget** mér: hány
forráshoz van használható fordított egység, és hogy a telepítő lépés
egyáltalán ki van-e kötve.

## Mutációs bizonyíték (mérve, 2026-08-31)

| visszavont javítás | melyik teszt bukik |
|---|---|
| a `--only-bytecode` helyett időbélyeges egység | `test_a_forditott_egyseg_idobelyege_nulla` |
| a Qt mégis a forrást fordítaná | `test_a_qt_a_forras_helyett_a_forditott_egyseget_hasznalja` |
| egyetlen `.qmlc` hiányzik a telepítés után | `test_egyetlen_hianyzo_egyseget_is_eszrevesz` |
| a `postinst`-ből kikerül az előrefordítás hívása | `test_a_deb_telepito_hivja_az_eloforditast` |
| a `install.bat`-ból kikerül a hívás | `test_a_windows_telepito_hivja_az_eloforditast` |
| a `pyproject.toml`-ból kikerül a belépési pont | `test_a_belepesi_pont_deklaralva_van` |
| a `.qmlc` bekerülne a repóba vagy a csomagba | `TestAFejlesztoiMunkafolyamat` |
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from picasapy.perf import qml_elofordit as elo

_REPO = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.skipif(
    elo.qmlcachegen_utvonal() is None,
    reason="nincs `qmlcachegen` a PySide6 mellett — az előrefordítás nem mérhető",
)


@pytest.fixture
def mini_fa(tmp_path: Path) -> Path:
    """Kétfájlos QML-fa — a valódi 141-es fa itt fölösleges és lassú."""
    (tmp_path / "Hello.qml").write_text(
        "import QtQuick\nItem { property int ertek: 41 + 1 }\n",
        encoding="utf-8",
    )
    (tmp_path / "Masik.qml").write_text(
        "import QtQuick\nItem { property string nev: 'a' + 'b' }\n",
        encoding="utf-8",
    )
    return tmp_path


class TestAzElofordítás:
    def test_minden_forrashoz_keszul_egyseg(self, mini_fa: Path):
        eredmeny = elo.elofordit(mini_fa)

        assert eredmeny.rendben, eredmeny.hibas
        assert eredmeny.forras_szam == 2
        assert (mini_fa / "Hello.qmlc").is_file()
        assert (mini_fa / "Masik.qmlc").is_file()

    def test_a_forditott_egyseg_idobelyege_nulla(self, mini_fa: Path):
        """EZ a javítás lényege: nulla időbélyeg = dátumfüggetlen egység.

        Ha az egység a forrás időbélyegét hordozná (ezt írja a motor
        futásidejű gyorsítótára), akkor a `pip install --upgrade` után
        azonnal érvénytelen lenne — pontosan a #1719-es baj."""
        elo.elofordit(mini_fa)

        fej = elo.fejlec(mini_fa / "Hello.qmlc")

        assert fej is not None, "nem `qv4cdata` bájtkód"
        qtverzio, idobelyeg = fej
        assert idobelyeg == 0, "a fordított egység a forrás dátumához van kötve"
        assert qtverzio == elo.qt_verzio()

    def test_nem_hagy_aotstats_melleketermeket(self, mini_fa: Path):
        elo.elofordit(mini_fa)

        assert not list(mini_fa.rglob("*.aotstats"))

    def test_a_js_fajlokat_is_forditja(self, tmp_path: Path):
        (tmp_path / "segito.js").write_text(
            ".pragma library\nfunction f() { return 1 }\n", encoding="utf-8"
        )

        eredmeny = elo.elofordit(tmp_path)

        assert eredmeny.rendben, eredmeny.hibas
        assert (tmp_path / "segito.jsc").is_file()

    def test_hibas_qml_eseten_nem_ad_zoldet(self, tmp_path: Path):
        (tmp_path / "Rossz.qml").write_text("import QtQuick\nItem {", encoding="utf-8")

        eredmeny = elo.elofordit(tmp_path)

        assert not eredmeny.rendben
        assert eredmeny.hibas


class TestAMechanizmus:
    """A Qt tényleg a mellétett egységet használja — a forrás helyett."""

    def test_a_qt_a_forras_helyett_a_forditott_egyseget_hasznalja(
        self, mini_fa: Path, tmp_path_factory
    ):
        """A bizonyíték: a forrást a fordítás UTÁN átírjuk (és jövőbeli
        dátumot adunk neki), a motor mégis a régi értéket adja vissza.

        Ez egyben megmutatja, MIÉRT nem szabad `.qmlc`-t hagyni a
        fejlesztői fában: az egység némán elnyomja a szerkesztett forrást.
        Ha ez a teszt egyszer elbukik (pl. egy Qt-frissítés bevezeti a
        dátum-összevetést nulla időbélyegnél is), akkor az egész #1719-es
        megoldás alól kicsúszott a talaj — ezért mérjük, nem feltételezzük.
        """
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        elo.elofordit(mini_fa)
        forras = mini_fa / "Hello.qml"
        forras.write_text(
            "import QtQuick\nItem { property int ertek: 7 }\n", encoding="utf-8"
        )
        # Jövőbeli dátum: időbélyeg-összevetés esetén ez BIZTOSAN
        # érvénytelenítené a fordított egységet.
        os.utime(forras, (2_000_000_000, 2_000_000_000))

        app = QGuiApplication.instance() or QGuiApplication([])
        engine = QQmlEngine()
        komponens = QQmlComponent(engine, str(forras))
        objektum = komponens.create()
        try:
            assert not komponens.isError(), komponens.errorString()
            assert objektum.property("ertek") == 42, (
                "a Qt a FORRÁST fordította — az előrefordítás hatástalan"
            )
        finally:
            del objektum
            del komponens
            engine.deleteLater()
            app.processEvents()


class TestAzEllenorzes:
    """A telepítési lépés MEGTÖRTÉNTÉNEK mércéje (munkamennyiség)."""

    def test_kesz_fan_zold(self, mini_fa: Path):
        elo.elofordit(mini_fa)

        assert elo.ellenoriz(mini_fa).rendben

    def test_egyetlen_hianyzo_egyseget_is_eszrevesz(self, mini_fa: Path):
        elo.elofordit(mini_fa)
        (mini_fa / "Masik.qmlc").unlink()

        eredmeny = elo.ellenoriz(mini_fa)

        assert not eredmeny.rendben
        assert eredmeny.keszult == 1
        assert "Masik.qml" in str(eredmeny.hibas[0][0])

    def test_idobelyeghez_kotott_egyseget_elutasit(self, mini_fa: Path):
        """A motor futásidejű gyorsítótárának másolata NEM jó ide."""
        elo.elofordit(mini_fa)
        cel = mini_fa / "Hello.qmlc"
        nyers = bytearray(cel.read_bytes())
        nyers[16:24] = (1234567890).to_bytes(8, "little")
        cel.write_bytes(bytes(nyers))

        eredmeny = elo.ellenoriz(mini_fa)

        assert not eredmeny.rendben
        assert "időbélyeg" in eredmeny.hibas[0][1]

    def test_mas_qt_verziot_elutasit(self, mini_fa: Path):
        """A bájtkód Qt-verzióhoz kötött — más verzión a Qt CSENDBEN
        eldobná, tehát az őrnek kell hangosnak lennie."""
        elo.elofordit(mini_fa)
        cel = mini_fa / "Hello.qmlc"
        nyers = bytearray(cel.read_bytes())
        nyers[12:16] = (0x060000).to_bytes(4, "little")
        cel.write_bytes(bytes(nyers))

        eredmeny = elo.ellenoriz(mini_fa)

        assert not eredmeny.rendben
        assert "Qt-verzió" in eredmeny.hibas[0][1]

    def test_takarit_visszaall_fejlesztoi_allapotba(self, mini_fa: Path):
        elo.elofordit(mini_fa)

        torolt = elo.takarit(mini_fa)

        assert torolt == 2
        assert not list(mini_fa.rglob("*.qmlc"))
        assert not elo.ellenoriz(mini_fa).rendben


class TestAParancssor:
    def test_ellenoriz_kilepokod_hianyzo_egysegnel(self, mini_fa: Path, capsys):
        kod = elo.main(["--gyoker", str(mini_fa), "--ellenoriz"])

        assert kod == 1

    def test_teljes_kor_a_parancssorbol(self, mini_fa: Path):
        assert elo.main(["--gyoker", str(mini_fa)]) == 0
        assert elo.main(["--gyoker", str(mini_fa), "--ellenoriz"]) == 0
        assert elo.main(["--gyoker", str(mini_fa), "--takarit"]) == 0
        assert elo.main(["--gyoker", str(mini_fa), "--ellenoriz"]) == 1

    def test_a_legalabb_kapcsolo_csonka_fat_elutasit(self, mini_fa: Path):
        """Munkamennyiség-mérce: egy üres/csonka QML-fán az „ellenőrzés"
        különben CSENDBEN zöld lenne (nulla forrás = nulla hiba)."""
        assert elo.main(["--gyoker", str(mini_fa)]) == 0

        assert elo.main(["--gyoker", str(mini_fa), "--legalabb", "2"]) == 0
        assert elo.main(["--gyoker", str(mini_fa), "--legalabb", "140"]) == 1

    def test_ures_fan_a_legalabb_nelkul_zold_lenne(self, tmp_path: Path):
        """Ezért kell a `--legalabb` a CI-ben és a telepítőben."""
        assert elo.main(["--gyoker", str(tmp_path), "--ellenoriz"]) == 0
        assert (
            elo.main(["--gyoker", str(tmp_path), "--ellenoriz", "--legalabb", "1"])
            == 1
        )

    def test_modulkent_is_futtathato(self, mini_fa: Path):
        """A telepítők `python -m picasapy.perf.qml_elofordit`-ot hívnak."""
        kornyezet = dict(os.environ)
        kornyezet["PYTHONPATH"] = os.pathsep.join(
            [str(_REPO / "src"), kornyezet.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)

        kesz = subprocess.run(
            [
                sys.executable,
                "-m",
                "picasapy.perf.qml_elofordit",
                "--gyoker",
                str(mini_fa),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env=kornyezet,
            check=False,
        )

        assert kesz.returncode == 0, kesz.stderr
        assert (mini_fa / "Hello.qmlc").is_file()


class TestATelepitokHivjak:
    """A lépés akkor ér valamit, ha a telepítő TÉNYLEG meghívja."""

    def test_a_belepesi_pont_deklaralva_van(self):
        szoveg = (_REPO / "pyproject.toml").read_text(encoding="utf-8")

        assert (
            'picasapy-qml-elofordit = "picasapy.perf.qml_elofordit:main"' in szoveg
        )

    def test_a_deb_telepito_hivja_az_eloforditast(self):
        szoveg = (_REPO / "packaging" / "debian" / "postinst").read_text(
            encoding="utf-8"
        )

        assert "picasapy-qml-elofordit" in szoveg
        pip_sor = szoveg.index("pip\" install --upgrade")
        elo_sor = szoveg.index("bin/picasapy-qml-elofordit")
        assert pip_sor < elo_sor, "az előrefordítás csak a telepítés UTÁN futhat"

    def test_a_windows_telepito_hivja_az_eloforditast(self):
        szoveg = (
            _REPO / "packaging" / "windows" / "install.bat.template"
        ).read_text(encoding="utf-8")

        assert "picasapy.perf.qml_elofordit" in szoveg

    def test_a_ci_a_telepitett_csomagon_ellenorzi(self):
        """A repó-szintű állítások mellé kell egy őr a VALÓDI telepítésre:
        a `package` job a wheelből telepít, és ott futtatja a lépést."""
        szoveg = (_REPO / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )

        assert "picasapy-qml-elofordit --legalabb 140" in szoveg
        assert "--ellenoriz --legalabb 140" in szoveg


class TestAFejlesztoiMunkafolyamat:
    """Egy ottfelejtett `.qmlc` némán elnyomná a szerkesztett `.qml`-t."""

    def test_a_repo_nem_kovet_egyetlen_forditott_egyseget_sem(self):
        kesz = subprocess.run(
            ["git", "ls-files", "*.qmlc", "*.jsc", "*.aotstats"],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        assert kesz.stdout.strip() == "", (
            "fordított QML-egység került a repóba — ez elnyomja a forrást"
        )

    def test_a_gitignore_kizarja(self):
        szoveg = (_REPO / ".gitignore").read_text(encoding="utf-8")

        assert "*.qmlc" in szoveg
        assert "*.jsc" in szoveg

    def test_a_manifest_kizarja_a_csomagbol(self):
        szoveg = (_REPO / "MANIFEST.in").read_text(encoding="utf-8")

        assert "*.qmlc" in szoveg

    def test_a_csomagellenorzo_nem_keri_szamon_a_wheelen(self):
        """Egy fejlesztői fán keletkezett `.qmlc` nem buktathatja el a
        `check_package_contents.py`-t — az a fájl SZÁNDÉKOSAN marad ki."""
        sys.path.insert(0, str(_REPO / "scripts"))
        import check_package_contents as cpc

        assert ".qmlc" in cpc._IGNORED_SUFFIXES
        assert ".jsc" in cpc._IGNORED_SUFFIXES

    def test_az_alkalmazas_nem_hivja_futasidoben(self):
        """Az indulás nem fordíthat: a lépés a telepítőé (#1719)."""
        szoveg = (
            _REPO / "src" / "picasapy" / "app" / "application.py"
        ).read_text(encoding="utf-8")

        assert "qml_elofordit" not in szoveg
