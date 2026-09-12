"""#3021: igazi windowsos telepítő — PyInstaller + Inno Setup, CI-ban.

## A tulajdonos szava (2026-09-11)

> „A baj nem a parancsikon, hanem az, hogy a telepítés egy repó mélyén lévő
> `.bat` fájl. Windowson ez nem telepítő. Egy felhasználó nem klónoz repót,
> nem keres batch fájlt, és nincs Pythonja."

A négy pont, amit a jegy kér: PyInstaller-csomagolás · Inno Setup-telepítő ·
a kész `PicasaPy-Setup-x.y.z.exe` a kiadáson · a build a CI-ban fut.

## Miért forrás-őr és nem füstpróba

A csomagolás WINDOWSON fut; fejlesztői Linux-gépen nem reprodukálható. Az
igazi bizonyíték a CI windows-lába, ami a csomagolt programot **el is
indítja** (`--onellenorzes`). Ez az őr azt tartja fenn, hogy az a lépés
LÉTEZIK és be van kötve — enélkül a füstpróba csendben kikerülhetne a
munkafolyamatból, és a hiányos csomag a tulajdonos gépén bukna el.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

_GYOKER = Path(__file__).resolve().parents[2]
_SPEC = _GYOKER / "packaging" / "windows" / "picasapy.spec"
_ISS = _GYOKER / "packaging" / "windows" / "picasapy.iss"
_MUNKAFOLYAMAT = _GYOKER / ".github" / "workflows" / "package.yml"


@pytest.fixture(scope="module")
def spec() -> str:
    return _SPEC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def iss() -> str:
    return _ISS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def munkafolyamat() -> dict:
    return yaml.safe_load(_MUNKAFOLYAMAT.read_text(encoding="utf-8"))


class TestAPyInstallerCsomag:
    def test_a_spec_letezik(self):
        assert _SPEC.is_file()

    def test_a_belepesi_pont_IMPORT_MENTES_indito(self, spec):
        """A PyInstaller SZKRIPTKÉNT futtatja a belépőt, tehát relatív
        import nem lehet benne. A `__main__.py`-val mérve `ImportError`
        lett, és — ablakos csomagban — egy kattintásra váró hibaablak."""
        assert "picasapy_launcher.py" in spec
        assert "__main__.py" not in spec.split("a = Analysis")[1][:200]

    def test_az_indito_letezik_es_nincs_benne_relativ_import(self):
        indito = _GYOKER / "packaging" / "windows" / "picasapy_launcher.py"
        assert indito.is_file()
        #: csak a KÓD-sorokat nézzük: a docstring maga idézi a hibás alakot
        kod = [
            sor for sor in indito.read_text(encoding="utf-8").splitlines()
            if sor and not sor.startswith(("#", " ", '"', "'"))
        ]
        assert any("from picasapy.app" in sor for sor in kod)
        assert not [sor for sor in kod if sor.startswith("from .")], (
            f"relatív import a csomag belépőjében: {kod}"
        )

    def test_a_QML_konyvtarat_VISZI(self, spec):
        """Qt/QML-programnál ez a legkényesebb pont: a `.qml` fájlok nem
        importok, tehát a csomagoló magától nem találja meg őket."""
        assert "qml" in spec, "a QML-fa nélkül a program ablak nélkül indul"

    def test_a_forditast_es_az_ikont_is_VISZI(self, spec):
        assert "i18n" in spec, "a .qm nélkül a felület angol lenne"
        assert "icon.ico" in spec

    def test_ABLAKOS_program_nem_konzolos(self, spec):
        assert "console=False" in spec.replace(" ", ""), (
            "konzolos csomagolásnál minden indításnál fekete ablak nyílik"
        )


class TestAzInnoSetupTelepito:
    def test_az_iss_letezik(self):
        assert _ISS.is_file()

    def test_a_verzio_KIVULROL_jon(self, iss):
        """Egyetlen verzióforrás: a `pyproject.toml`. A telepítőbe a build
        adja át, hogy ne kelljen két helyen átírni."""
        assert "MyAppVersion" in iss
        assert '#define MyAppVersion "0.' not in iss, (
            "beégetett verzió — a kiadásnál némán elavulna"
        )

    def test_START_MENU_bejegyzest_ad(self, iss):
        assert "[Icons]" in iss
        assert "{autoprograms}" in iss or "{group}" in iss

    def test_ASZTALI_ikont_ad(self, iss):
        assert "{autodesktop}" in iss or "{commondesktop}" in iss

    def test_ELTAVOLITHATO(self, iss):
        """Az Inno magától ír uninstall-bejegyzést; ehhez viszont kell
        `AppId` — enélkül egy átnevezés két bejegyzést hagyna."""
        assert "AppId" in iss

    def test_a_kimenet_neve_a_MEGBESZELT(self, iss):
        assert "PicasaPy-Setup-" in iss, (
            "a tulajdonos ezt a fájlnevet kérte a kiadásra"
        )


class TestACI:
    def _windows_lepesek(self, munkafolyamat) -> list[dict]:
        for _nev, job in munkafolyamat["jobs"].items():
            fut = str(job.get("runs-on", ""))
            if "windows" in fut:
                return job["steps"]
        raise AssertionError("nincs windowsos job a package.yml-ben")

    def test_van_windowsos_job(self, munkafolyamat):
        assert self._windows_lepesek(munkafolyamat)

    def test_a_PyInstaller_es_az_Inno_is_fut(self, munkafolyamat):
        szoveg = " ".join(
            str(lepes.get("run", "")) for lepes in self._windows_lepesek(munkafolyamat)
        )
        assert "pyinstaller" in szoveg.lower()
        assert "iscc" in szoveg.lower() or "innosetup" in szoveg.lower()

    def test_a_fustproba_IDOKORLATOS(self, munkafolyamat):
        """Mérve: a lezárás nélküli önellenőrzés 38 percig ÁLLT a windowsos
        futtatón, és a job időkorlátja vágta le — a napló nem mondta meg,
        mi történt. Kemény időkorlát nélkül a füstpróba pont azt nem
        mutatja meg, amiért van."""
        szoveg = " ".join(
            str(lepes.get("run", "")) for lepes in self._windows_lepesek(munkafolyamat)
        )
        assert "timeout " in szoveg, (
            "a füstpróbát időkorláttal kell futtatni"
        )

    def test_a_csomagolt_programot_EL_IS_INDITJA(self, munkafolyamat):
        """A jegy Kész-ha pontja: füstpróba, nem csak fordítás. Hiányos
        csomag esetén ITT kell elbukni, nem a tulajdonos gépén."""
        szoveg = " ".join(
            str(lepes.get("run", "")) for lepes in self._windows_lepesek(munkafolyamat)
        )
        assert "--onellenorzes" in szoveg, (
            "a felépített .exe-t el kell indítani, különben csak azt tudjuk, "
            "hogy a csomagoló lefutott"
        )

    def test_a_telepito_FELKERUL_a_kiadasra(self, munkafolyamat):
        szoveg = " ".join(
            str(lepes.get("run", "")) + str(lepes.get("uses", ""))
            for lepes in self._windows_lepesek(munkafolyamat)
        )
        assert "PicasaPy-Setup-" in szoveg or "upload" in szoveg.lower()


class TestAzOnellenorzes:
    """A csomagolás füstpróbájának belépője a programban is létezzen."""

    def test_a_kapcsolo_be_van_kotve(self):
        forras = (
            _GYOKER / "src" / "picasapy" / "app" / "application.py"
        ).read_text(encoding="utf-8")
        assert "--onellenorzes" in forras

    def test_a_kapcsolo_NEM_kerul_a_gyokerek_koze(self):
        """Az `_resolve_roots` MINDEN argumentumot figyelt mappának vesz —
        a kapcsolót ki kell szedni, különben `--onellenorzes` nevű mappát
        próbálnánk indexelni (ez a `--tesztuzem` mért hibája volt)."""
        import sys

        sys.path.insert(0, str(_GYOKER / "src"))
        from picasapy.app.application import argv_onellenorzes

        kert, maradek = argv_onellenorzes(["picasapy", "--onellenorzes", "/kepek"])
        assert kert is True
        assert maradek == ["picasapy", "/kepek"]

        kert, maradek = argv_onellenorzes(["picasapy", "/kepek"])
        assert kert is False
        assert maradek == ["picasapy", "/kepek"]
