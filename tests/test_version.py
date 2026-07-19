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

        monkeypatch.setattr(version.subprocess, "run", boom)
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
