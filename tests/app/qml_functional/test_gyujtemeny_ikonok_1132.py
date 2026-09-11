"""#1132 — a bal hasáb bejegyzés-TÍPUSAI külön ikont kapnak.

Az eredetiben az `icons/` névtér **kilenc** ikont ad, és az ikon nem
díszítés: a bejegyzés TÍPUSÁT kódolja. A tulajdonos „három színt" látott —
abból az egyik (a sárga mappa) a MI eltérésünk volt, az eredeti lemezes-mappa
ikonja **kék**.

| erőforrás | mért méret | típus |
|---|---|---|
| `icons/folder` | 17 × 15 | lemezes mappa — **KÉK** |
| `icons/album` | 16 × 18 | rendes album — narancs könyv |
| `icons/special_album` | 16 × 18 | különleges album (Csillagozott) — zöld könyv csillaggal |
| `icons/projects` | 15 × 16 | projekt-mappa — lila könyv csillaggal |
| `icons/label` | 15 × 12 | címke — szürke címke |

⚠️ A MÉRET és a JELENTÉS mért, a RAJZ és a színérték a miénk
(`docs/specs/design-guide.md`) — az eredeti PNG-ket tilos a repóba másolni.
Ez az őr ezért **a típus-hozzárendelést és az arányokat** méri, nem a
képpontokat.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"


def _forras(nev: str) -> str:
    return (_QML / nev).read_text(encoding="utf-8")


class TestAKomponensekMegvannak:
    @pytest.mark.parametrize(
        "nev",
        ["AlbumIcon.qml", "SpecialAlbumIcon.qml", "ProjectIcon.qml",
         "LabelIcon.qml"],
    )
    def test_a_komponens_letezik_es_regisztralt(self, nev):
        assert (_QML / nev).exists(), f"{nev} hiányzik"
        tipus = nev.removesuffix(".qml")
        assert f"{tipus} 1.0 {nev}" in _forras("qmldir"), (
            f"{tipus} nincs a qmldir-ben — a modulból nem érhető el"
        )

    @pytest.mark.parametrize(
        "nev,arany",
        [
            ("AlbumIcon.qml", "1.125"),        # 16 × 18
            ("SpecialAlbumIcon.qml", "1.125"),
            ("ProjectIcon.qml", "16 / 15"),
            ("LabelIcon.qml", "12 / 15"),
        ],
    )
    def test_a_MERT_aranyt_hasznalja(self, nev, arany):
        """A magasság a mért méretarányból jön, nem szabadon választott."""
        assert arany in _forras(nev), f"{nev}: nem a mért arány áll benne"


class TestATipusHozzarendeles:
    def test_a_csillagozott_sor_KULONLEGES_album_ikont_kap(self):
        forras = _forras("AlbumsSection.qml")
        assert "SpecialAlbumIcon {" in forras
        assert 'objectName: "starredRowIcon"' in forras

    def test_a_rendes_album_ALBUM_ikont_kap(self):
        forras = _forras("AlbumsSection.qml")
        assert "AlbumIcon {" in forras
        assert 'objectName: "albumRowIcon_"' in forras

    def test_a_regi_zold_teglalap_ELTUNT(self):
        """Ismert negatív: a rendes album eddig ZÖLD téglalapot kapott, ami a
        KÜLÖNLEGES album zöldjével esett egybe — a típus így nem látszott."""
        forras = _forras("AlbumsSection.qml")
        assert "Theme.picasaGreen" not in forras

    def test_a_projekt_mappa_PROJEKT_ikont_kap(self):
        forras = _forras("ProjectsSection.qml")
        assert "ProjectIcon {" in forras
        assert "FolderIcon {" not in forras, (
            "a projekt-mappa a lemezes mappa ikonját kapja — a kettő így nem "
            "megkülönböztethető (#1132)"
        )

    def test_a_cimke_CIMKE_ikont_kap(self):
        forras = _forras("TagsPanel.qml")
        assert "LabelIcon {" in forras
        assert "Theme.folderGold" not in forras, (
            "a címke a MAPPA aranyát használja (#1132)"
        )


class TestAMappaIkonKEK:
    def test_a_mappa_ikon_a_KEK_szint_hasznalja(self):
        forras = _forras("FolderIcon.qml")
        assert "Theme.folderBlue" in forras
        assert "Theme.folderGold" not in forras, (
            "a lemezes mappa ikonja arany maradt — az eredetié KÉK (#1132)"
        )

    def test_a_forras_megnevezi_a_MERT_eroforrast(self):
        """A komment sem hazudhat: a szín eredete nevesítve áll."""
        forras = _forras("FolderIcon.qml")
        assert "icons/folder" in forras
        assert "17 × 15" in forras

    def test_a_temaban_MINDEN_uj_szin_ott_van_ket_modban(self):
        """A `dark` mód nem maradhat le: a Theme minden színt párban ad."""
        forras = _forras("Theme.qml")
        for nev in (
            "folderBlue", "albumOrange", "specialAlbumGreen",
            "projectPurple", "labelGray",
        ):
            assert f"readonly property color {nev}:" in forras, nev
            assert f"readonly property color {nev}Border:" in forras, nev
            kezd = forras.index(f"readonly property color {nev}:")
            assert "dark ?" in forras[kezd : kezd + 120], (
                f"{nev}: nincs sötét változat"
            )


class TestARajzoltFa:
    def test_a_hasabon_a_HELYES_ikonok_epulnek_fel(self, qml_app, qt_app):
        from PySide6.QtCore import QObject

        window, _c, _e = qml_app
        assert window.findChild(QObject, "starredRowIcon") is not None, (
            "a Csillagozott sor ikonja nem épült fel"
        )
