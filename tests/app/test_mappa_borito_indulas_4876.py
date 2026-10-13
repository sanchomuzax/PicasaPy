"""#4876 — a bal hasáb indexképei induláskor azonnal, csendben jelenjenek meg.

Mérve (offscreen, 20 mappa × 250 kép, meleg bélyegkép-gyorsítótár): a
mappák borítói SORBAN készültek, mappánként ~100 ms-ig, mert a szolgáltató
minden indításkor az EREDETI fotót dekódolta — a rács kész bélyegképeit
nem használta. A huszadik sor ikonja így ~2,9 s-mal az első után jelent
meg, és ez minden induláskor megismétlődött.

A másik fele: fotó nélküli mappára (pl. csak videót tartalmazó mappa) a
szolgáltató null képet adott, amire a Qt minden alkalommal kiírta a
„Failed to get image from provider" sort — a sikertelen betöltést nem
tárolja, tehát a sor minden újrarajzolásnál újra kérte, és újra hibát írt.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import pytest

from picasapy.app.folder_cover_provider import (
    FolderCoverProvider,
    borito_belyegkepe,
    normalizald_az_azonositot,
)
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.thumbs.cache import ThumbnailCache
from support.jpeg_factory import make_jpeg

_READY = 1
_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "application.py"
)
_FOLDER_PANE = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "FolderPane.qml"
)


@pytest.fixture
def indexelt(tmp_path: Path):
    mappa = tmp_path / "kepek" / "Nyaralás 2024"
    mappa.mkdir(parents=True)
    for i in range(3):
        make_jpeg(mappa / f"k{i}.jpg", size=(320, 240))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, tmp_path / "kepek")
    tar = ThumbnailCache(tmp_path / "thumbs", size=144)
    return db, mappa, tar


class TestAMelegGyorsitotarbolJon:
    """A borító a rács bélyegkép-tárából jön, nem az eredeti fotóból."""

    def test_a_belyegkep_a_TARBAN_van(self, indexelt, tmp_path):
        db, mappa, tar = indexelt
        utak = borito_belyegkepe(db, str(mappa), tar)
        assert len(utak) == 3  # mind a három fotó kész útja
        for ut in utak:
            assert tmp_path / "thumbs" in ut.parents, (
                f"a borító nem a bélyegkép-tárból jön: {ut}"
            )

    def test_meleg_tarral_az_EREDETIHEZ_nem_nyul(self, qt_app, indexelt):
        """Az első hívás felmelegíti a tárat; utána az eredeti fájlok
        nélkül is kész a borító — tehát nem dekódoljuk őket újra."""
        db, mappa, tar = indexelt
        borito_belyegkepe(db, str(mappa), tar)
        for fajl in mappa.glob("*.jpg"):
            os.remove(fajl)
        szolgaltato = FolderCoverProvider(
            lambda m: borito_belyegkepe(db, m, tar)
        )
        kep = szolgaltato.requestImage(str(mappa), None, None)
        assert not kep.isNull() and kep.width() > 1

    def test_ismeretlen_mappara_ures(self, indexelt, tmp_path):
        db, _mappa, tar = indexelt
        assert borito_belyegkepe(db, str(tmp_path / "nincs"), tar) == []


class TestFotoNelkuliMappaCsendben:
    """Borító nélkül: sikeres, 1 képpontos jelölő — a QML ebből tudja, hogy a
    mappaikont kell mutatnia, és a Qt nem ír hibát."""

    def test_a_jelolo_ERVENYES_kep_es_1_kepponts(self, qt_app):
        kep = FolderCoverProvider(lambda _m: []).requestImage("x", None, None)
        assert not kep.isNull()
        assert (kep.width(), kep.height()) == (1, 1)
        assert kep.pixelColor(0, 0).alpha() == 0

    def test_a_hibara_futo_lekerdezo_is_jelolot_ad(self, qt_app):
        def robban(_m):
            raise RuntimeError("szándékos teszt-hiba")

        kep = FolderCoverProvider(robban).requestImage("x", None, None)
        assert (kep.width(), kep.height()) == (1, 1)

    def test_a_FolderPane_a_jelolonel_a_mappaikont_mutatja(self):
        """A `boritoLatszik` feltétele a szélességet is nézi (#2215) — enélkül
        a jelölő elrejtené a mappaikont."""
        forras = _FOLDER_PANE.read_text(encoding="utf-8")
        eleje = forras.index("readonly property bool boritoLatszik:")
        feltetel = forras[eleje:eleje + 300]
        assert "folderRowCoverImage.implicitWidth > 1" in feltetel


def _qml_statusz(qt_app, tmp_path: Path, szolgaltato, ut: str, nev: str):
    """A #3352 mintája: VALÓDI QML `Image` kéri a borítót, a Qt URL-kezelésén át."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine

    engine = QQmlApplicationEngine()
    engine.addImageProvider("foldercover", szolgaltato)
    engine.rootContext().setContextProperty("mappaUt", ut)
    qml = tmp_path / f"{nev}.qml"
    qml.write_text(
        "import QtQuick\n"
        "Image { property int allapot: status; asynchronous: false;"
        ' source: "image://foldercover/" + mappaUt }\n',
        encoding="utf-8",
    )
    engine.load(QUrl.fromLocalFile(str(qml)))
    gyoker = engine.rootObjects()[0]
    eredmeny = (gyoker.property("allapot"), gyoker.property("implicitWidth"))
    gyoker.deleteLater()
    return eredmeny


_UZENETEK: list[str] = []


def _gyujto(_tipus, _kornyezet, uzenet: str) -> None:
    _UZENETEK.append(uzenet)


class TestNincsIsmetlodoHibasor:
    def test_foto_nelkuli_mappara_nincs_Failed_sor(self, qt_app, tmp_path):
        from PySide6.QtCore import qInstallMessageHandler

        _UZENETEK.clear()
        ut = "C:\\Users\\felhasznalo\\Desktop\\x"
        regi = qInstallMessageHandler(_gyujto)
        try:
            # a motor átveszi a szolgáltatót, ezért mindkettő a sajátját kapja
            elso = _qml_statusz(
                qt_app, tmp_path, FolderCoverProvider(lambda _m: []), ut, "a"
            )
            masodik = _qml_statusz(
                qt_app, tmp_path, FolderCoverProvider(lambda _m: []), ut, "b"
            )
        finally:
            qInstallMessageHandler(regi)
        assert elso == (_READY, 1) and masodik[0] == _READY
        hibak = [u for u in _UZENETEK if "Failed to get image" in u]
        assert hibak == [], hibak


class TestWindowsosUtak:
    """A Qt a visszapert kódolva (`%5C`) adja át (#2983) — betű szerint
    vissza kell kapni az ékezetes, szóközös utat."""

    @pytest.mark.parametrize(
        "kodolt, vart",
        [
            ("C:%5CUsers%5Cfelhasznalo%5CDesktop%5Cx",
             "C:\\Users\\felhasznalo\\Desktop\\x"),
            ("C:%5CUsers%5Cfelhasznalo%5COneDrive - Ceg%5CKépek%5CFilmek",
             "C:\\Users\\felhasznalo\\OneDrive - Ceg\\Képek\\Filmek"),
            ("C:%5CUsers%5Cfelhasznalo%5COneDrive - Ceg%5CKépek%5CNyaralás",
             "C:\\Users\\felhasznalo\\OneDrive - Ceg\\Képek\\Nyaralás"),
        ],
    )
    def test_betu_szerint_visszaall(self, kodolt, vart):
        assert normalizald_az_azonositot(kodolt) == vart

    def test_a_lekerdezo_a_valodi_utat_kapja(self, qt_app):
        kapott: list[str] = []

        def lekerdezo(m):
            kapott.append(m)
            return []

        FolderCoverProvider(lekerdezo).requestImage(
            "C:%5CUsers%5Cfelhasznalo%5COneDrive - Ceg%5CKépek%5CNyaralás", None, None
        )
        assert kapott == ["C:\\Users\\felhasznalo\\OneDrive - Ceg\\Képek\\Nyaralás"]


class TestAHibasFotoNemZarjaKiATobbit:
    """A3: rekordonként elkülönített hibakezelés + tartalék a következőre."""

    def test_a_belyegkep_hibaja_utan_a_kovetkezo_jon(
        self, indexelt, monkeypatch, caplog
    ):
        db, mappa, tar = indexelt
        eredeti = tar.get_or_create
        hivasok: list[str] = []

        def get_or_create(forras, *args, **kwargs):
            hivasok.append(Path(forras).name)
            if Path(forras).name == "k0.jpg":
                raise RuntimeError("szándékos teszt-hiba")
            return eredeti(forras, *args, **kwargs)

        monkeypatch.setattr(tar, "get_or_create", get_or_create)
        with caplog.at_level(logging.WARNING):
            utak = borito_belyegkepe(db, str(mappa), tar)
        assert hivasok[:2] == ["k0.jpg", "k1.jpg"], "az első hiba után megállt"
        assert len(utak) == 2, "a hibás első fotó kizárta a többit"
        assert any("k0.jpg" in r.getMessage() for r in caplog.records)

    def test_visszaadja_az_osszes_kesz_utat_legfeljebb_negyet(self, indexelt):
        db, mappa, tar = indexelt  # 3 fotó
        assert len(borito_belyegkepe(db, str(mappa), tar)) == 3

    def test_serult_elso_tarfajl_jo_masodik_lesz_a_borito(
        self, qt_app, indexelt
    ):
        """A tár első fájlja olvashatatlan (nem kép) — a második lesz a borító."""
        db, mappa, tar = indexelt
        utak = borito_belyegkepe(db, str(mappa), tar)
        assert len(utak) >= 2
        utak[0].write_bytes(b"ez nem JPEG")
        kep = FolderCoverProvider(lambda _m: utak).requestImage("x", None, None)
        assert kep.width() > 1, "a sérült első tárfájl a jó másodikat is kizárta"

    def test_olvasasi_OSError_utan_a_kovetkezore_lep(
        self, qt_app, indexelt, monkeypatch
    ):
        import picasapy.app.folder_cover_provider as modul

        db, mappa, tar = indexelt
        utak = borito_belyegkepe(db, str(mappa), tar)
        eredeti = modul._olvasd_be

        def olvasd(ut):
            if Path(ut) == utak[0]:
                raise OSError("szándékos olvasási hiba")
            return eredeti(ut)

        monkeypatch.setattr(modul, "_olvasd_be", olvasd)
        kep = FolderCoverProvider(lambda _m: utak).requestImage("x", None, None)
        assert kep.width() > 1


class TestAVideoNemDekodolodik:
    """A6: videó + kép mappában a borító a képé, a videó-dekódoló nem fut."""

    def test_mp4_mellett_a_jpg_a_borito_es_a_dekodolo_nem_hivodik(
        self, tmp_path, monkeypatch
    ):
        import picasapy.thumbs.cache as tarmodul

        mappa = tmp_path / "kepek" / "Vegyes"
        mappa.mkdir(parents=True)
        # névsorban a videó az ELSŐ — enélkül a kihagyás nem lenne próba
        (mappa / "a.mp4").write_bytes(b"nem valodi video")
        make_jpeg(mappa / "b.jpg", size=(320, 240))
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            sync_tree(conn, tmp_path / "kepek")
            rekordok = photos_in_folder(conn, str(mappa))
        assert [r.name for r in rekordok] == ["a.mp4", "b.jpg"], (
            "a videó nem került az indexbe — a próba üres lenne"
        )
        hivasok: list[Path] = []

        def dekodolo(forras, *args, **kwargs):
            hivasok.append(Path(forras))
            return None

        # a tár MODULSZINTŰ fogantyúja — globális standard modult nem patchelünk
        monkeypatch.setattr(tarmodul, "_decode_video_frame_isolated", dekodolo)
        tar = ThumbnailCache(tmp_path / "thumbs", size=144)
        utak = borito_belyegkepe(db, str(mappa), tar)
        assert hivasok == [], f"a videót dekódoltuk: {hivasok}"
        assert len(utak) == 1


class TestAzIsmetltKeresMerve:
    """A5: egy motoron belül, forrás újra-beállításkor hányszor szólal meg a
    szolgáltató a borító nélküli (jelölő) mappára?"""

    def test_ujra_beallitott_forrasnal_a_szolgaltato_csak_egyszer_hivodik(
        self, qt_app, tmp_path
    ):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlApplicationEngine

        hivasok: list[str] = []

        class Szamlalo(FolderCoverProvider):
            def requestImage(self, id, size, requestedSize):  # noqa: A002
                hivasok.append(id)
                return super().requestImage(id, size, requestedSize)

        engine = QQmlApplicationEngine()
        engine.addImageProvider("foldercover", Szamlalo(lambda _m: []))
        qml = tmp_path / "ujra.qml"
        qml.write_text(
            "import QtQuick\n"
            "Image { property string ut: \"\"; asynchronous: false;"
            ' source: ut === "" ? "" : "image://foldercover/" + ut }\n',
            encoding="utf-8",
        )
        engine.load(QUrl.fromLocalFile(str(qml)))
        gyoker = engine.rootObjects()[0]
        for _ in range(3):
            gyoker.setProperty("ut", "/felhasznalo/Ceg/ures")
            qt_app.processEvents()
            gyoker.setProperty("ut", "")
            qt_app.processEvents()
        gyoker.deleteLater()
        qt_app.processEvents()
        assert len(hivasok) == 1, f"a szolgáltató {len(hivasok)}× szólalt meg"


class TestABekotesForrasOre:
    """A7: ⚠️ SZÖVEGET ellenőriz (az `application.py` forrását), nem
    futtatja az alkalmazást — a bekötés tényleges működését a
    `test_meleg_tarral_az_EREDETIHEZ_nem_nyul` és a QML-teszt méri."""

    def test_a_borito_szolgaltato_a_thumb_cache_et_kapja(self):
        forras = _APPLICATION.read_text(encoding="utf-8")
        minta = re.compile(
            r"FolderCoverProvider\(\s*lambda mappa:\s*borito_belyegkepe\("
            r"data_dir / \"index\.db\", mappa, thumb_cache\)\s*\)"
        )
        assert minta.search(forras), (
            "a foldercover szolgáltató nem a rács `thumb_cache`-ét kapja"
        )
        assert re.search(r"^\s*thumb_cache = ThumbnailCache\(", forras, re.M)
