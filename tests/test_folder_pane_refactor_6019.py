"""A FolderPane QML-felbontás szerkezeti őrei (#6019)."""

from __future__ import annotations

from pathlib import Path


_QML = Path(__file__).resolve().parents[1] / "src/picasapy/app/qml/PicasaPy"


def _qml_sorok(fajlnev: str) -> int:
    return len((_QML / fajlnev).read_text(encoding="utf-8").splitlines())


def test_mappafa_tartalma_onallo_qml_komponens():
    assert (_QML / "FolderPaneContent.qml").is_file()
    assert "FolderPaneContent {" in (_QML / "FolderPane.qml").read_text(
        encoding="utf-8"
    )


def test_mappasor_delegalta_onallo_qml_komponens():
    assert (_QML / "FolderPaneTreeRow.qml").is_file()
    assert "FolderPaneTreeRow {" in (_QML / "FolderPaneContent.qml").read_text(
        encoding="utf-8"
    )


def test_helyi_menuk_es_parbeszedablakok_onallo_qml_komponens():
    assert (_QML / "FolderPaneMenus.qml").is_file()
    assert "FolderPaneMenus {" in (_QML / "FolderPane.qml").read_text(
        encoding="utf-8"
    )


def test_mappafa_qml_fajlok_800_sor_alatt_maradnak():
    komponensek = (
        "FolderPane.qml",
        "FolderPaneContent.qml",
        "FolderPaneTreeRow.qml",
        "FolderPaneMenus.qml",
    )
    tulhosszu = {
        fajlnev: _qml_sorok(fajlnev)
        for fajlnev in komponensek
        if (_QML / fajlnev).is_file() and _qml_sorok(fajlnev) >= 800
    }
    assert not tulhosszu, f"800 soros plafon túllépve: {tulhosszu}"


def test_a_kozos_forrasor_a_mappafa_minden_komponenset_olvassa():
    from tests.support.folder_pane_components_6019 import folder_pane_sources

    forrasok = folder_pane_sources()
    assert set(forrasok) == {
        "FolderPane.qml",
        "FolderPaneContent.qml",
        "FolderPaneMenus.qml",
        "FolderPaneTreeRow.qml",
    }
