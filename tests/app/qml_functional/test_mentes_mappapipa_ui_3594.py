"""#3594/#3681 — a mentés 2. lépésének SZÖVEGEI a kiadás-panelen.

Az eredeti mentés-üzemmód 2. lépése (`backuprect2`, `biztonsagi-mentes.md`
10.3):

```
Mappák és albumok kijelölése biztonsági másolat készítéséhez
A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem
készült biztonsági másolat.
Jelölje ki azokat a mappákat, … vagy »Az összes kijelölése« …
[Az összes kijelölése] [Az összes kijelölés megszüntetése]
```

⚠️ #3681: a mappánkénti PIPÁS LISTA — korábban a panel fölötti
`BackupFolderStrip` sávban — a KÖNYVTÁRBA (`FolderPane`/
`FolderHierarchyView`, `mentesSzuroAktiv` szerződés) költözött, az eredeti
Picasa `backuptext2`/`backuptext3` viselkedését követve. Az ottani
kattintásos tesztek: `test_mentes_konyvtar_szuro_3681.py` (önálló
komponens) és `test_mentes_szuro_main_3681.py` (a valódi `Main.qml`-ben:
pipa → mentés → a mappa eltűnik, „Számítás…", darabszám, a két gomb). A
mentés-üzemmód BACKEND-logikáját a `test_mentes_mappak_vezerlo_3594.py`
méri. Ez a fájl a PANEL (`PublishPanel.qml`) mért szövegeit és a gazda
(`BackupHost`) lekérdezés-fegyelmét nézi.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, Slot

import picasapy.app
from support.backup_host_harness import epits_ablakot
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

_QML = Path(picasapy.app.__file__).parent / "qml"
_PANEL = (_QML / "PicasaPy" / "PublishPanel.qml").read_text(encoding="utf-8")


class TestAMertSzovegek:
    @pytest.mark.parametrize("szoveg", [
        "Choose folders & albums to back up",
        "Picasa is now showing the files you have not previously backed up.",
        "Check the folders you want to back up, or choose 'Select All' to "
        "choose everything.",
        "Select All",
        "Select None",
    ])
    def test_a_mert_felirat_ott_van(self, szoveg):
        assert szoveg in _PANEL, szoveg


class TestAMagyarFelirat:
    @pytest.mark.parametrize("forras, magyar", [
        ("Choose folders & albums to back up",
         "Mappák és albumok kijelölése biztonsági másolat készítéséhez"),
        ("Picasa is now showing the files you have not previously backed up.",
         "A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban "
         "nem készült biztonsági másolat."),
        ("Select All", "Az összes kijelölése"),
        ("Select None", "Az összes kijelölés megszüntetése"),
    ])
    def test_a_hivatalos_magyar_a_qm_bol_jon(self, qt_app, forras, magyar):
        from PySide6.QtCore import QTranslator

        fordito = QTranslator()
        assert fordito.load("picasapy_hu", str(_QML.parent / "i18n"))
        assert fordito.translate("PublishPanel", forras) == magyar

    def test_a_szamitas_felirata_a_konyvtarban(self, qt_app):
        """`il_BurnPanel::calculating` (`biztonsagi-mentes.md` 15.7) — a
        felirat a könyvtár mentés-szűrőjében áll (#3681)."""
        from PySide6.QtCore import QTranslator

        fordito = QTranslator()
        assert fordito.load("picasapy_hu", str(_QML.parent / "i18n"))
        assert fordito.translate("FolderPane", "Calculating…") == "Számítás…"
        # `thumbui/lightbox_bgtext` Text2 — a hivatalos magyar
        assert fordito.translate(
            "FolderPane", "All Files are backed up in this set"
        ) == "A készlet valamennyi fájljáról készült biztonsági másolat"


def _vard_a_mappakat(ablak, qt_app) -> None:
    assert varj_feltetelre(
        qt_app, lambda: ablak.property("mappakToltodnek") is False
    ), "a mappa-lista nem érkezett meg"
    qt_app.processEvents()


class TestEgyetlenLekerdezes:
    def test_a_kivalasztas_valtasa_egyetlen_lekerdezest_indit(
        self, qt_app, tmp_path, monkeypatch
    ):
        """A törlés átállítja a kiválasztást — az `onKivalasztottChanged`
        már kér, a `frissitsd` ne kérjen még egyszer."""
        monkeypatch.setattr(
            "picasapy.app.backup_controller._kepek_mappaja",
            lambda: str(tmp_path / "Kepek"),
        )
        from picasapy.app.backup_controller import BackupController
        from picasapy.index import open_index, sync_tree

        class _Szamlalo(BackupController):
            lekeresek = 0

            @Slot(int, result=int)
            def mentetlenMappakLekerese(self, keszlet_id):  # noqa: N802
                type(self).lekeresek += 1
                return super().mentetlenMappakLekerese(keszlet_id)

        gyoker = tmp_path / "kepek"
        (gyoker / "nyaralas").mkdir(parents=True)
        make_jpeg(gyoker / "nyaralas" / "a.jpg")
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, gyoker)
        vezerlo = _Szamlalo(db, (str(gyoker),))
        vezerlo.ujKeszlet("Külső", str(tmp_path / "cel"), "minden", "lemez")
        vezerlo.ujKeszlet("Másik", str(tmp_path / "cel2"), "minden", "lemez")
        view, ablak = epits_ablakot(_QML, {"backupController": vezerlo})
        try:
            QMetaObject.invokeMethod(ablak, "nyisd")
            ablak.setProperty("kivalasztott", 1)
            _vard_a_mappakat(ablak, qt_app)
            masodik = vezerlo.keszletek()[1]["id"]

            _Szamlalo.lekeresek = 0
            # a törlés után a kiválasztás 1 → 0 lesz
            vezerlo.torisdAKeszletet(masodik)
            qt_app.processEvents()
            _vard_a_mappakat(ablak, qt_app)
            assert ablak.property("kivalasztott") == 0
            assert _Szamlalo.lekeresek == 1
        finally:
            view.hide()
