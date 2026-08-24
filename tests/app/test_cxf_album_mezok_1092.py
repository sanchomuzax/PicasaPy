"""Az `albumUID` és az `<albumDate>` a SAJÁT kollázsainkba is kikerül (#1092).

A #1274 elérte, hogy egy **Picasával készült** kollázs album-mezői
túléljék az újramentést. Amit nem oldott meg — és ez a #1092 —: a
PicasaPy SAJÁT kollázsaiba a mezők egyáltalán nem kerülnek bele, mert a
panel üresen indul, és nincs ki kitöltse.

A forrás mind a kettőnél ugyanaz, mint a `<albumTitle>`-nél: a képek
**közös forrásmappája** (`collage_sources.common_source_folder`). Több
mappából érkező kijelölésnél nincs egy forrásalbum, tehát nem is találunk
ki egyet.

## A dátum az INDEXBŐL jön, nem a látott képekből

Ez a modul első nekifutásában a betöltött fotólistából számolt — és ez
**hibás volt**: a rács tartalmát a főablak szűri (rejtett képek, keresés,
csillag-szűrő), tehát ugyanabból a mappából két kollázs két különböző
dátumot kapott volna. Pont az az invariáns dőlt volna meg, amiért a modul
készült: a 12 golden minta 11 kollázsa ugyanabból a mappából, más-más
képekkel készült, és mindegyik UGYANAZT az `albumDate`-et viseli.

Az index `folders.date` oszlopa a helyes forrás, mert MÁR tartalmazza a
teljes szabályt (`index/sync.py` `_sync_folder_date`): a `.picasa.ini`
`[Picasa] date=` kézi felülírása elsőbbséget élvez, és csak annak
hiányában jön a `MIN(taken_at)`.

Az `albumDate` alakja mérve: `2023. november` — év, pont, honos hónapnév.
A hónapnév a FELÜLET nyelvéből jön, nem a rendszerlokálból: a #1131 mérte
ki, hogy a `QLocale()` alapértelmezése magyar rendszeren, angol felülettel
hazudik, a CI „C" lokálján pedig futtatókörnyezet-függővé tenné a
kimenetet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.collage_album_fields import album_date_label, album_fields_of
from picasapy.collage.contact_sheet import header_lines
from picasapy.collage.cxf import loads
from picasapy.index import open_index
from support.jpeg_factory import make_jpeg

ALBUM_UID = re.compile(r"^[0-9a-f]{32}$")
NODE_UID = re.compile(r"^[0-9a-f]{16}0{16}$")

DATUM_ISO = "2023-11-04T18:30:00"
DATUM_FELIRAT = "2023. november"


@dataclass
class _Photo:
    """A `PhotoRecord` azon mezői, amiket a kollázs-panel használ."""

    folder_path: str
    name: str
    caption: str | None = None
    width: int | None = 400
    height: int | None = 300


class _Photos:
    def __init__(self, photos=()):
        self.photos = list(photos)


@dataclass
class _Source:
    path: str


def _index_with_folder(tmp_path: Path, folder: Path, date_iso: str | None) -> Path:
    """Egyetlen mappa-sor az indexben, a megadott dátummal."""
    db = tmp_path / "index.sqlite"
    with open_index(db) as conn:
        conn.execute(
            "INSERT INTO folders (path, has_ini, date) VALUES (?, 1, ?)",
            (str(folder), date_iso),
        )
        conn.commit()
    return db


class TestAzAlbumDatumFelirata:
    """`2023. november` — a mért alak."""

    def test_a_mert_alak_magyarul(self):
        assert album_date_label(DATUM_ISO, "hu") == DATUM_FELIRAT

    def test_a_datum_ora_nelkul_is_jo(self):
        assert album_date_label("2023-11-04", "hu") == DATUM_FELIRAT

    def test_a_felulet_nyelve_donti_el_a_honapnevet(self):
        """⚠️ Csak a MAGYAR alak van kimérve; az angol Picasa alakja a
        #1390-en áll. Ez a teszt azt rögzíti, amit MI írunk, nem azt,
        amit az eredeti angol Picasa írna."""
        assert album_date_label("2023-11-04", "en") == "2023. November"

    @pytest.mark.parametrize("rossz", ["", "nem-datum", "2023", "0000-99-01"])
    def test_ertelmezhetetlen_datumra_ures(self, rossz):
        """Kitalálni nem szabad: hibás dátumnál a mező marad ki."""
        assert album_date_label(rossz, "hu") == ""


class TestAKozosForrasmappa:
    """A két mező forrása — ugyanaz, mint a címé."""

    def test_egy_mappabol_mindket_mezo_megvan(self, tmp_path):
        mappa = tmp_path / "AI"
        db = _index_with_folder(tmp_path, mappa, DATUM_ISO)

        uid, datum = album_fields_of(
            [_Source(str(mappa / "a.jpg"))], db_path=db, language="hu"
        )

        assert ALBUM_UID.match(uid)
        assert datum == DATUM_FELIRAT

    def test_a_datum_a_SZURT_nezetben_is_ugyanaz(self, tmp_path):
        """A golden invariáns: 11 kollázs ugyanabból a mappából — MIND
        ugyanazt az `albumDate`-et viseli.

        A rács tartalma a felhasználó szűrőitől függ; a dátum nem függhet
        tőle. A teszt foga: a kijelölés EGYETLEN képre szűkül, a mappa
        dátuma mégis a teljes mappáé marad, mert az indexből jön."""
        mappa = tmp_path / "AI"
        db = _index_with_folder(tmp_path, mappa, DATUM_ISO)

        teljes = album_fields_of(
            [_Source(str(mappa / "a.jpg")), _Source(str(mappa / "b.jpg"))],
            db_path=db,
            language="hu",
        )
        szurt = album_fields_of(
            [_Source(str(mappa / "b.jpg"))], db_path=db, language="hu"
        )

        assert teljes == szurt == (teljes[0], DATUM_FELIRAT)

    def test_a_kezi_felulirast_is_hozza(self, tmp_path):
        """Az index `folders.date`-je MÁR a helyes szabály eredménye: a
        `[Picasa] date=` kézi felülírás (#320) elsőbbséget élvez a
        legrégebbi felvételi idővel szemben."""
        mappa = tmp_path / "AI"
        db = _index_with_folder(tmp_path, mappa, "2019-07-01")

        _, datum = album_fields_of(
            [_Source(str(mappa / "a.jpg"))], db_path=db, language="hu"
        )

        assert datum == "2019. július"

    def test_nem_indexelt_mappanal_az_ini_feluliras_az_utolso_esely(
        self, tmp_path
    ):
        """Ha a mappa nincs az indexben, a `.picasa.ini` kézi dátuma marad.

        A mappát EXIF-ért végigolvasni itt tilos: a felület a mentés
        útjában áll, egy hálózati mappa bejárása másodperceket vinne el."""
        mappa = tmp_path / "nem-indexelt"
        mappa.mkdir()
        (mappa / ".picasa.ini").write_text(
            "[Picasa]\ndate=2019-07-01\n", encoding="utf-8"
        )

        _, datum = album_fields_of(
            [_Source(str(mappa / "a.jpg"))], db_path=None, language="hu"
        )

        assert datum == "2019. július"

    def test_ket_mappabol_nincs_forrasalbum(self, tmp_path):
        db = _index_with_folder(tmp_path, tmp_path / "AI", DATUM_ISO)

        assert album_fields_of(
            [
                _Source(str(tmp_path / "AI" / "a.jpg")),
                _Source(str(tmp_path / "lake" / "b.jpg")),
            ],
            db_path=db,
            language="hu",
        ) == ("", "")

    def test_nem_indexelt_mappa_azonositot_meg_kap(self, tmp_path):
        """A hiányzó dátum nem viheti el az azonosítót sem."""
        uid, datum = album_fields_of(
            [_Source(str(tmp_path / "AI" / "a.jpg"))], db_path=None, language="hu"
        )

        assert ALBUM_UID.match(uid)
        assert datum == ""

    def test_olvashatatlan_index_nem_bukatatja_a_lapot(self, tmp_path):
        """Az index baja legfeljebb a dátumot viszi el, a lapot nem."""
        romlott = tmp_path / "romlott.sqlite"
        romlott.write_bytes(b"nem egy adatbazis")

        uid, datum = album_fields_of(
            [_Source(str(tmp_path / "AI" / "a.jpg"))],
            db_path=romlott,
            language="hu",
        )

        assert ALBUM_UID.match(uid)
        assert datum == ""


@pytest.fixture
def host(qt_app, tmp_path, monkeypatch):
    from picasapy.app import collage_output
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    # A felület nyelve dönti el a hónapnevet; a teszt kimondja, melyik
    # nyelven mér — enélkül a CI „C" lokálja adná a választ.
    monkeypatch.setattr(collage_output, "_felulet_nyelve", lambda: "hu")

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    mappa = tmp_path / "AI"
    mappa.mkdir()
    for nev in ("a.jpg", "b.jpg"):
        make_jpeg(mappa / nev, size=(80, 60))
    db = _index_with_folder(tmp_path, mappa, DATUM_ISO)

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._db_path = db
            self._photos = _Photos(
                [_Photo(str(mappa), "a.jpg"), _Photo(str(mappa), "b.jpg")]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    peldany = _Host()
    yield peldany
    assert peldany.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


class TestAMentettPiszkozat:
    """A körbejárás vége: mind a három mező OTT VAN a lemezre írt `.cxf`-ben."""

    def test_a_harom_mezo_a_fajlba_kerul(self, host):
        host.openCollage([0, 1])

        host.saveCollageDraft()

        piszkozat = host._collage_panel_draft_dir() / "autosave.cxf"
        assert piszkozat.is_file(), "nem született piszkozat"
        projekt = loads(piszkozat.read_bytes())
        assert ALBUM_UID.match(projekt.album_uid), "hiányzik az albumUID (#1092)"
        assert projekt.album_date == DATUM_FELIRAT
        assert projekt.nodes, "nem került csomópont a piszkozatba"
        for node in projekt.nodes:
            assert NODE_UID.match(node.uid), f"hiányzó/rossz <uid>: {node.uid!r}"

    def test_a_megnyitott_projekt_uid_jai_tulelik_az_ujramentest(self, host, tmp_path):
        """Egy Picasa-fájl `<uid>`-jait nem cserélhetjük a sajátunkra."""
        forras = str(tmp_path / "AI" / "a.jpg")
        eredeti_uid = "c91b4354e61f4a5a0000000000000000"
        kep = _picasa_kollazs(
            tmp_path,
            forras,
            uid=eredeti_uid,
            album_uid="a4ef8e0fd2dbb152d25d79eb2bd2a28b",
        )

        host.openCollageProject(str(kep))
        host.saveCollageDraft()

        projekt = loads(
            (host._collage_panel_draft_dir() / "autosave.cxf").read_bytes()
        )
        assert [node.uid for node in projekt.nodes] == [eredeti_uid], (
            "a Picasa írta <uid> elveszett újramentéskor"
        )
        assert projekt.album_uid == "a4ef8e0fd2dbb152d25d79eb2bd2a28b"

    def test_uj_kollazs_nem_orokli_az_elozo_projekt_uid_jait(self, host, tmp_path):
        """A megnyitott projekt leképezése nem ragadhat bent a panelen."""
        idegen = "c91b4354e61f4a5a0000000000000000"
        kep = _picasa_kollazs(tmp_path, str(tmp_path / "AI" / "a.jpg"), uid=idegen)
        host.openCollageProject(str(kep))

        host.openCollage([0, 1])
        host.saveCollageDraft()

        projekt = loads(
            (host._collage_panel_draft_dir() / "autosave.cxf").read_bytes()
        )
        assert idegen not in [node.uid for node in projekt.nodes], (
            "az előző projekt azonosítója átszivárgott az új kollázsba"
        )

    def test_a_lap_bezarasa_torli_az_album_mezoket(self, host, tmp_path):
        """A bezárt lap adatai nem tapadhatnak rá a következőre."""
        host.openCollage([0, 1])

        host.closeCollage()

        assert host._collage_panel_album_uid == ""
        assert host._collage_panel_album_date == ""
        assert host._collage_panel_node_uids == {}


class TestAzIndexkepFejlece:
    """A dátum a KIRAJZOLT Indexkép fejlécébe is bekerül (#1273 + #1092).

    Az eredeti `AI6.jpg` fejléce `9 kép, 2023. november`; nálunk eddig
    csak akkor volt dátum, ha a kollázs Picasával készült fájlból nyílt.
    Az `albumDate` kitöltésével a SAJÁT indexképeink is megkapják — ez
    látható képváltozás, ezért külön állítás őrzi."""

    def test_a_fejlec_masodik_sora_hordozza_a_datumot(self, host):
        host.openCollage([0, 1])

        settings = host._render_settings()

        assert settings.album_date == DATUM_FELIRAT
        _, alcim = header_lines(settings.album_title, settings.album_date, 9)
        assert alcim == f"9 kép, {DATUM_FELIRAT}"

    def test_datum_nelkuli_mappanal_nincs_logo_vesszo(self, host, tmp_path):
        """Nem indexelt mappa: a fejléc a régi, dátum nélküli alakra esik."""
        masik = tmp_path / "datumtalan"
        masik.mkdir()
        make_jpeg(masik / "c.jpg", size=(80, 60))
        host._photos.photos.append(_Photo(str(masik), "c.jpg"))

        host.openCollage([2])
        settings = host._render_settings()

        assert settings.album_date == ""
        assert header_lines(settings.album_title, settings.album_date, 1)[1] == "1 kép"


def _picasa_kollazs(
    tmp_path: Path, forras: str, *, uid: str, album_uid: str = ""
) -> Path:
    """Picasa-stílusú `.cxf` + a mellette álló kép, egy csomóponttal."""
    mappa = tmp_path / "Kollázsok"
    mappa.mkdir(exist_ok=True)
    kep = mappa / "AI.jpg"
    make_jpeg(kep, size=(400, 300))
    uid_attr = f' albumUID="{album_uid}"' if album_uid else ""
    (mappa / "AI.cxf").write_text(
        '<?xml version="1.0" encoding="utf-8" ?>\r\n'
        '<collage version="2" format="4:3" orientation="landscape"'
        f' theme="picturepile" shadows="0" captions="0"{uid_attr}>\r\n'
        " <albumTitle>AI</albumTitle>\r\n"
        ' <background type="solid" color="FFFFFFFF"/>\r\n'
        ' <spacing value="0.000000"/>\r\n'
        ' <node x="0.1" y="0.1" w="0.3" h="0.3" theta="0.0" scale="1.0">\r\n'
        "  <theme>noborder</theme>\r\n"
        f"  <src>{forras}</src>\r\n"
        f"  <uid>{uid}</uid>\r\n"
        " </node>\r\n"
        "</collage>\r\n",
        encoding="utf-8",
    )
    return kep
