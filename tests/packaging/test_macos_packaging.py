"""Tests for macOS packaging configuration and scripts."""

from __future__ import annotations

import ast
from pathlib import Path

try:
    import pytest
except ImportError:
    pytest = None  # type: ignore

_GYOKER = Path(__file__).resolve().parents[2]
_SPEC = _GYOKER / "packaging" / "macos" / "picasapy.spec"
_LAUNCHER = _GYOKER / "packaging" / "macos" / "picasapy_launcher.py"
_BUILD_SH = _GYOKER / "packaging" / "macos" / "build_macos.sh"
_MERGE_PY = _GYOKER / "packaging" / "macos" / "merge_universal.py"
_ICON_ICNS = _GYOKER / "src" / "picasapy" / "app" / "assets" / "icon.icns"
_WORKFLOW = _GYOKER / ".github" / "workflows" / "package.yml"


def _spec_content() -> str:
    return _SPEC.read_text(encoding="utf-8")


if pytest is not None:
    @pytest.fixture(scope="module")
    def spec_content() -> str:
        return _spec_content()


def test_macos_spec_file_exists():
    assert _SPEC.is_file(), "packaging/macos/picasapy.spec is missing"


def test_macos_spec_configures_bundle_and_assets(spec_content: str | None = None):
    content = spec_content if spec_content is not None else _spec_content()
    assert "BUNDLE(" in content
    assert "PicasaPy.app" in content
    assert "org.picasapy.picasapy" in content
    assert "icon.icns" in content
    assert "qml" in content
    assert "i18n" in content
    assert "picasapy_launcher.py" in content


def test_macos_launcher_has_no_relative_imports():
    assert _LAUNCHER.is_file(), "packaging/macos/picasapy_launcher.py is missing"
    tree = ast.parse(_LAUNCHER.read_text(encoding="utf-8"))
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    relative_imports = [
        node for node in imports
        if isinstance(node, ast.ImportFrom) and node.level > 0
    ]
    assert not relative_imports, f"Relative imports found in macOS launcher: {relative_imports}"


def test_macos_build_script_exists_and_executable():
    assert _BUILD_SH.is_file(), "packaging/macos/build_macos.sh is missing"
    assert _BUILD_SH.stat().st_mode & 0o111, "packaging/macos/build_macos.sh is not executable"


def test_merge_universal_script_is_valid_python():
    assert _MERGE_PY.is_file(), "packaging/macos/merge_universal.py is missing"
    ast.parse(_MERGE_PY.read_text(encoding="utf-8"))


def test_icon_icns_exists():
    assert _ICON_ICNS.is_file(), "src/picasapy/app/assets/icon.icns is missing"
    assert _ICON_ICNS.stat().st_size > 1024, "icon.icns is too small or invalid"


def test_package_workflow_includes_macos():
    assert _WORKFLOW.is_file()
    content = _WORKFLOW.read_text(encoding="utf-8")
    assert "macos-telepito:" in content
    assert "packaging/macos/**" in content
    assert "./packaging/macos/build_macos.sh all" in content
    assert "macOS-arm64.dmg" in content
    assert "macOS-universal.dmg" in content
    assert "--onellenorzes" in content
    assert "--indulasellenorzes" in content


if __name__ == "__main__":
    test_macos_spec_file_exists()
    test_macos_spec_configures_bundle_and_assets()
    test_macos_launcher_has_no_relative_imports()
    test_macos_build_script_exists_and_executable()
    test_merge_universal_script_is_valid_python()
    test_icon_icns_exists()
    test_package_workflow_includes_macos()
    print("All macOS packaging tests passed successfully!")

