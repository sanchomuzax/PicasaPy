"""A verzió-/build-címke felépítése és git-hiba elleni robusztussága."""

import picasapy
from picasapy import version


class TestBuildLabel:
    def test_number_and_commit_combined(self, monkeypatch):
        monkeypatch.setattr(version, "build_number", lambda: "81")
        monkeypatch.setattr(version, "build_id", lambda: "3706d78")
        assert version.build_label() == "81.3706d78"

    def test_falls_back_to_commit_only(self, monkeypatch):
        monkeypatch.setattr(version, "build_number", lambda: None)
        monkeypatch.setattr(version, "build_id", lambda: "3706d78")
        assert version.build_label() == "3706d78"

    def test_falls_back_to_number_only(self, monkeypatch):
        monkeypatch.setattr(version, "build_number", lambda: "81")
        monkeypatch.setattr(version, "build_id", lambda: None)
        assert version.build_label() == "81"

    def test_dev_when_no_git(self, monkeypatch):
        monkeypatch.setattr(version, "build_number", lambda: None)
        monkeypatch.setattr(version, "build_id", lambda: None)
        assert version.build_label() == "dev"


class TestGitFailureIsSilent:
    def test_missing_git_returns_none(self, monkeypatch):
        def boom(*args, **kwargs):
            raise FileNotFoundError("git")

        monkeypatch.setattr(version, "_run", boom)
        assert version.build_number() is None
        assert version.build_id() is None
        # a címke sosem dobhat — legrosszabb esetben "dev"
        assert version.build_label() == "dev"


class TestVersionString:
    def test_starts_with_package_version(self, monkeypatch):
        monkeypatch.setattr(version, "build_label", lambda: "81.3706d78")
        result = version.version_string()
        assert result == f"v{picasapy.__version__} (81.3706d78)"

    def test_real_repo_has_numeric_build(self):
        # Az élő repóban a git elérhető: a build-szám csupa számjegy.
        number = version.build_number()
        assert number is not None and number.isdigit()


class TestCsomagoltProgram:
    """#6344: a PyInstaller-csomagból nem indul `git` az induláskor."""

    def test_csomagolt_programbol_nem_indul_git(self, monkeypatch):
        def tilos(*args, **kwargs):
            raise AssertionError("a csomagolt program git-et indított")

        monkeypatch.setattr(version, "_run", tilos)
        monkeypatch.setattr(version, "_futtato", type("Fagyott", (), {"frozen": True}))
        assert version.build_label() == "dev"


class TestCsomagVerzio:
    """#6348: a PyInstaller-csomag verzióját a build által írt fájl adja."""

    def test_a_csomag_verziofajlbol_olvas(self, monkeypatch, tmp_path):
        (tmp_path / picasapy._CSOMAG_VERZIO_FAJL).write_text("1.2.3\n", encoding="utf-8")
        monkeypatch.setattr(picasapy, "__file__", str(tmp_path / "__init__.py"))
        assert picasapy._verzio_a_csomagbol() == "1.2.3"

    def test_hianyzo_fajlnal_none(self, monkeypatch, tmp_path):
        monkeypatch.setattr(picasapy, "__file__", str(tmp_path / "__init__.py"))
        assert picasapy._verzio_a_csomagbol() is None

    def test_a_spec_ugyanazt_a_fajlt_irja_a_csomagba(self):
        from pathlib import Path

        spec = (
            Path(__file__).resolve().parents[1] / "packaging" / "windows" / "picasapy.spec"
        ).read_text(encoding="utf-8")
        assert f'"{picasapy._CSOMAG_VERZIO_FAJL}"' in spec
        assert '(str(_VERZIO_FAJL), "picasapy")' in spec
