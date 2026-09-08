"""A felhasználót érintő PR-nek CHANGELOG-bejegyzést kell hoznia (#1340).

## A lelet

A v0.8.71 és a v0.8.72 ezzel a mondattal jelent meg a Releases hasábon:

    „Ez a kiadás nem hoz felhasználónak látszó változást."

Miközben az egyikben a letiltott gombok megjelenése javult (#893), a
másikban a lasszós kijelölés készült el (#897). A mondat HAZUDOTT, és a
tulajdonos vette észre.

Az ok egyszerű: egyik PR sem írt CHANGELOG-bejegyzést, a kiadó lépés pedig
szakasz híján tartaléksablonra váltott. A szabály („a CHANGELOG szövegét
EMBER írja") le volt írva, de **semmi nem őrizte**.

Ez a fájl az őr. A másik felét — hogy a tartalék se állíthasson valótlant —
a `test_ensure_release_896.py` méri.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import changelog_or as cor  # noqa: E402

_DIFF_BEJEGYZESSEL = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -6,6 +6,9 @@
 ## [Nem kiadott]
 
+### Javítva
+- **A letiltott gombok halványan jelennek meg (#893).** A zöld gombokra
+  sincs kivétel.
 
 ## [0.8.70] – 2026-08-24
"""

_DIFF_CSAK_ATRENDEZES = """\
diff --git a/CHANGELOG.md b/CHANGELOG.md
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -6,6 +6,6 @@
-## [Nem kiadott]
+## [0.8.71] – 2026-08-24
"""


class TestMikorKellBejegyzes:
    def test_felhasznaloi_kodhoz_kell(self) -> None:
        assert cor.kell_bejegyzes(["src/picasapy/app/qml/PicasaPy/PicasaButton.qml"])

    def test_a_1331_es_1333_esete_kellett_volna(self) -> None:
        """A két PR, amelyik a hamis jegyzetet okozta."""
        assert cor.kell_bejegyzes(
            ["src/picasapy/app/qml/PicasaPy/lasso.js",
             "tests/app/qml_functional/test_lasszo_pillanatfelvetel_897.py"]
        )

    @pytest.mark.parametrize(
        "fajl",
        ["docs/specs/valami.md", "tests/render/test_effects.py",
         ".github/workflows/ci.yml", "scripts/ensure_release.py", "CHANGELOG.md"],
    )
    def test_belso_valtozashoz_nem_kell(self, fajl: str) -> None:
        assert not cor.kell_bejegyzes([fajl])


class TestMiSzamitBejegyzesnek:
    def test_uj_felsorolas_szamit(self) -> None:
        assert cor.van_uj_bejegyzes(_DIFF_BEJEGYZESSEL)

    def test_a_szakaszcim_atnevezese_NEM_bejegyzes(self) -> None:
        """A verzióemelés átnevezi a címet — az nem emberi összefoglaló."""
        assert not cor.van_uj_bejegyzes(_DIFF_CSAK_ATRENDEZES)

    def test_erintetlen_changelog_nem_bejegyzes(self) -> None:
        assert not cor.van_uj_bejegyzes("")


class TestKiadatlanSzakasz:
    def test_a_bejegyzesnek_a_Nem_kiadott_szakaszban_a_helye(self) -> None:
        assert cor.van_kiadatlan_szakasz("# Változásnapló\n\n## [Nem kiadott]\n\n- x\n")

    def test_szakasz_nelkul_bukik(self) -> None:
        assert not cor.van_kiadatlan_szakasz("# Változásnapló\n\n## [0.8.70] – ma\n")


class TestParancssor:
    def _futtato(self, valaszok: dict[str, str]):
        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            for kulcs, kimenet in valaszok.items():
                if kulcs in " ".join(args):
                    return subprocess.CompletedProcess(args, 0, kimenet, "")
            return subprocess.CompletedProcess(args, 0, "", "")

        return futtat

    def test_hianyzo_bejegyzes_BUKTATJA_a_kort(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({"--name-only": "src/picasapy/render/vivid.py\n"}),
        )
        assert kod == 1
        kimenet = capsys.readouterr().out
        assert "::error" in kimenet, "néma bukás — a naplóban elveszne"
        assert "CHANGELOG" in kimenet

    def test_meglevo_bejegyzessel_atmegy(self, tmp_path: Path) -> None:
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n\n- x\n", encoding="utf-8")
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({
                "--name-only": "src/picasapy/render/vivid.py\nCHANGELOG.md\n",
                "-- CHANGELOG.md": _DIFF_BEJEGYZESSEL,
            }),
        )
        assert kod == 0

    def test_belso_valtozas_atmegy_bejegyzes_nelkul(self, tmp_path: Path) -> None:
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")
        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato({"--name-only": "docs/specs/a.md\n"}),
        )
        assert kod == 0


_DIFF_CSAK_VERZIOSOR = """\
diff --git a/pyproject.toml b/pyproject.toml
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -10,7 +10,7 @@
-version = "0.8.73"
+version = "0.8.74"
"""

_DIFF_ERDEMI_PYPROJECT = """\
diff --git a/pyproject.toml b/pyproject.toml
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -30,6 +30,7 @@
 dependencies = [
+  "uj-fuggoseg>=1.0",
 ]
"""


class TestAVerzioemeloSajatPRje:
    """Az őrnek NEM szabad a saját automatikánkat megfognia.

    A verzióemelő PR a `[Nem kiadott]` címet nevezi át és a verziósort
    írja át — emberi mondatot nem hoz, mert nem is neki kell. Ha az őr ezt
    megfogná, a verzióemelés soha nem tudna beolvadni, és a kiadás állna:
    pont az a baj, amit a #1319 megszüntetett.
    """

    def test_a_verziosor_onmagaban_nem_erdemi_valtozas(self) -> None:
        assert not cor.van_erdemi_valtozas(_DIFF_CSAK_VERZIOSOR)

    def test_uj_fuggoseg_viszont_erdemi(self) -> None:
        assert cor.van_erdemi_valtozas(_DIFF_ERDEMI_PYPROJECT)

    def test_a_verzioemelo_PR_atmegy(self, tmp_path: Path) -> None:
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [0.8.74] – ma\n\n- x\n", encoding="utf-8")

        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            egy = " ".join(args)
            if "--name-only" in egy:
                return subprocess.CompletedProcess(args, 0, "CHANGELOG.md\npyproject.toml\n", "")
            if "-- pyproject.toml" in egy:
                return subprocess.CompletedProcess(args, 0, _DIFF_CSAK_VERZIOSOR, "")
            return subprocess.CompletedProcess(args, 0, _DIFF_CSAK_ATRENDEZES, "")

        assert cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)], runner=futtat
        ) == 0

    def test_valodi_fuggosegvaltozas_viszont_bejegyzest_ker(self, tmp_path: Path) -> None:
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")

        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            egy = " ".join(args)
            if "--name-only" in egy:
                return subprocess.CompletedProcess(args, 0, "pyproject.toml\n", "")
            return subprocess.CompletedProcess(args, 0, _DIFF_ERDEMI_PYPROJECT, "")

        assert cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)], runner=futtat
        ) == 1


class TestAMeresBukasa:
    """Ha az őr nem tud mérni, NEM adhat zöld utat (#1340).

    Éles próbán jött elő: hibás refekkel meghívva a `git diff` elbukott, a
    fájllista üres lett, és az őr azt mondta, hogy „nem jut el a
    felhasználóhoz — nem kell bejegyzés". A sikertelen mérésből megint
    állítás lett, pontosan az a hibaosztály, ami miatt ez a jegy megnyílt.
    """

    def _bukó_git(self):
        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args, 128, "", "fatal: bad object")

        return futtat

    def test_a_bukott_diff_BUKTATJA_az_ort(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        kod = cor.main(["--base", "rossz", "--head", "refek"], runner=self._bukó_git())
        assert kod == 1
        assert "::error" in capsys.readouterr().out

    def test_ures_diff_sikeres_lekerdezessel_viszont_rendben(self) -> None:
        """A tényleg üres változás nem hiba — csak a MÉRÉS bukása az."""

        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args, 0, "", "")

        assert cor.main(["--base", "a", "--head", "b"], runner=futtat) == 0


class TestBokezuKontextus2749:
    """A fájlonkénti mérés BŐKEZŰ diff-kontextust kér (#2749).

    A #2708 docstring-felismerése csak akkor tud dönteni, ha a hunk LÁTJA a
    hármas-idézőjelet. A `git diff` alapértelmezett három sora egy hosszú
    docstring KÖZEPÉN történt változásnál egyet sem mutat — az őr ilyenkor
    (helyesen, szigorúan) kódnak veszi, és CHANGELOG-bejegyzést követel.
    Élesben megtörtént: a #2744 (tisztán docstring-átírás két `render/`
    modulban) ubuntu-lába emiatt lett piros.

    A próba a KÉT kontextust adja vissza aszerint, hogy az őr kérte-e a
    bőkezű alakot — így a fix nélküli kód is mérhető: az szűk diffet kap,
    és elbukik.
    """

    #: szűk (3 soros) kontextus: egyetlen `"""` sem látszik
    SZUK_DIFF = (
        "--- a/src/picasapy/render/vivid.py\n"
        "+++ b/src/picasapy/render/vivid.py\n"
        "@@ -40,7 +40,7 @@\n"
        "     A mért levezetés a spec 5.7-ben áll.\n"
        "     \n"
        "-    A pontos algoritmus NEM ismert.\n"
        "+    A pontos algoritmus MÉRVE (#2231): rácsos.\n"
        "     \n"
        "     Ld. a testvérfüggvényt.\n"
    )

    #: bőkezű kontextus: a modul-docstring nyitása és zárása is látszik
    BO_DIFF = (
        "--- a/src/picasapy/render/vivid.py\n"
        "+++ b/src/picasapy/render/vivid.py\n"
        "@@ -1,10 +1,10 @@\n"
        " def kvantal(kep):\n"
        '     """Kvantálás.\n'
        " \n"
        "     A mért levezetés a spec 5.7-ben áll.\n"
        " \n"
        "-    A pontos algoritmus NEM ismert.\n"
        "+    A pontos algoritmus MÉRVE (#2231): rácsos.\n"
        " \n"
        "     Ld. a testvérfüggvényt.\n"
        '     """\n'
        "     return kep\n"
    )

    def _futtato(self):
        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            egyben = " ".join(args)
            if "--name-only" in egyben:
                return subprocess.CompletedProcess(
                    args, 0, "src/picasapy/render/vivid.py\n", ""
                )
            if "-- src/picasapy/render/vivid.py" in egyben:
                # EZ a próba lényege: a bőkezű kontextust kérő őr látja a
                # docstring határait, a mai (szűk) alak nem
                # `getattr`, hogy a próba a JAVÍTÁS NÉLKÜLI kódon is
                # lefusson: ott a szűk diffet kapja, és az őr elbukik —
                # így a RED-ág a VISELKEDÉST méri, nem egy hiányzó nevet
                zaszlo = getattr(cor, "DIFF_KONTEXTUS", "-U100000")
                kimenet = self.BO_DIFF if zaszlo in args else self.SZUK_DIFF
                return subprocess.CompletedProcess(args, 0, kimenet, "")
            return subprocess.CompletedProcess(args, 0, "", "")

        return futtat

    def test_a_hosszu_docstring_KOZEPEN_torteno_valtozas_atmegy(self, tmp_path: Path):
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")

        kod = cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)],
            runner=self._futtato(),
        )

        assert kod == 0, (
            "az őr CHANGELOG-bejegyzést követelt egy tisztán docstring-"
            "változásra — a fájlonkénti diffet szűk kontextussal kérte, így a "
            "docstring határai nem látszottak (#2749)"
        )

    def test_a_docstring_MELLETT_torteno_kodsor_tovabbra_is_BUKIK(self, tmp_path: Path):
        """A bőkezű kontextus nem enged fel semmit."""
        naplo = tmp_path / "CHANGELOG.md"
        naplo.write_text("# Változásnapló\n\n## [Nem kiadott]\n", encoding="utf-8")
        kodsoros = self.BO_DIFF.replace(
            "     return kep\n", "-    return kep\n+    return kep * 2\n"
        )

        def futtat(args: list[str]) -> subprocess.CompletedProcess[str]:
            egyben = " ".join(args)
            if "--name-only" in egyben:
                return subprocess.CompletedProcess(
                    args, 0, "src/picasapy/render/vivid.py\n", ""
                )
            if "-- src/picasapy/render/vivid.py" in egyben:
                return subprocess.CompletedProcess(args, 0, kodsoros, "")
            return subprocess.CompletedProcess(args, 0, "", "")

        assert cor.main(
            ["--base", "a", "--head", "b", "--changelog", str(naplo)], runner=futtat
        ) == 1
