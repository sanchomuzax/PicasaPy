"""#1401 — az „Útlevélkép…" a Kísérleti almenü HATODIK tétele.

Az eredetiben (`docs/specs/picasa-menu-parancsok-viselkedes.md`, 24.
szakasz) a Kísérleti almenü kilenc tétele: Publish via FTP… (tiltva) ·
Show Duplicate Files · Search for ▸ · Save search results… · Show tag as
album… · **Passport photo…** · Delete empty online albums… (hatókörön
kívül) · Choose database location… · Write faces to XMP….

Nálunk a `Choose database location…` már korábban, más helyre került (ld.
#2142) — az Útlevélkép ezért a nálunk MEGLÉVŐ szomszédok szerint kerül a
helyére: a `Show &tag as album…` UTÁN, a `Write faces to XMP…` ELŐTT."""

from __future__ import annotations

from pathlib import Path

import picasapy.app as app_csomag
from tests.support.qml_blokk import blokk_horgonyra

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


def _kiserleti_blokk() -> str:
    return blokk_horgonyra(_QML, 'title: qsTr("Experimental")')


class TestAzUtlevelkepMenupont:
    def test_a_KISERLETI_almenuben_van(self):
        assert 'objectName: "menuToolsPassportPhoto"' in _kiserleti_blokk()

    def test_a_MERT_feliratot_viseli(self):
        tetel = blokk_horgonyra(
            _kiserleti_blokk(), 'objectName: "menuToolsPassportPhoto"'
        )
        assert 'qsTr("&Passport photo...")' in tetel

    def test_a_SHOW_TAG_AS_ALBUM_UTAN_a_WRITE_XMP_ELOTT_all(self):
        blokk = _kiserleti_blokk()
        elotte = blokk.index('objectName: "menuToolsShowTagAsAlbum"')
        sajat = blokk.index('objectName: "menuToolsPassportPhoto"')
        utana = blokk.index('objectName: "menuToolsWriteXmpFaces"')
        assert elotte < sajat < utana, (
            "az Útlevélkép nem a `Show tag as album…` és a `Write faces "
            "to XMP…` között áll"
        )

    def test_a_parancs_a_bar_jelzeset_hasznalja(self):
        tetel = blokk_horgonyra(
            _kiserleti_blokk(), 'objectName: "menuToolsPassportPhoto"'
        )
        assert "bar.passportPhotoRequested()" in tetel

    def test_a_MAGYAR_alak_a_dokumentaltbol_jon(self):
        assert "<source>&amp;Passport photo...</source>" in _TS
        assert "<translation>&amp;Útlevélkép…</translation>" in _TS
