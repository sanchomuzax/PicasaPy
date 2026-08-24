"""Az `albumUID` és az `<albumDate>` a SAJÁT kollázsainkba is kikerül (#1092).

A #1274 elérte, hogy egy **Picasával készült** kollázs album-mezői
túléljék az újramentést. Amit nem oldott meg — és ez a #1092 —: a
PicasaPy SAJÁT kollázsaiba a mezők egyáltalán nem kerülnek bele, mert a
panel üresen indul, és nincs ki kitöltse.

A forrás mind a kettőnél ugyanaz, mint a `<albumTitle>`-nél: a képek
**közös forrásmappája** (`_title_from_sources`). Több mappából érkező
kijelölésnél nincs egy forrásalbum, tehát nem is találunk ki egyet.

Az `albumDate` alakja mérve: `2023. november` — év, pont, honos hónapnév
(a 12 golden mintában mind ilyen). A hónapnév a FELÜLET nyelvéből jön, nem
a rendszerlokálból: a #1131 mérte ki, hogy a `QLocale()` alapértelmezése
magyar rendszeren, angol felülettel hazudik, a CI „C" lokálján pedig
futtatókörnyezet-függővé tenné a kimenetet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.collage_album_fields import album_date_label, album_fields_of
from picasapy.collage.cxf import loads
from support.jpeg_factory import make_jpeg

ALBUM_UID = re.compile(r"^[0-9a-f]{32}$")
NODE_UID = re.compile(r"^[0-9a-f]{16}0{16}$")


@dataclass
class _Photo:
    """A `PhotoRecord` azon mezői, amiket a kollázs-panel használ."""

    folder_path: str
    name: str
    caption: str | None = None
    width: int | None = 400
    height: int | None = 300
    taken_at: str | None = None


class _Photos:
    def __init__(self, photos=()):
        self.photos = list(photos)


@dataclass
class _Source:
    path: str


class TestAzAlbumDatumFelirata:
    """`2023. november` — a mért alak."""

    def test_a_mert_alak_magyarul(self):
        assert album_date_label("2023-11-04T18:30:00", "hu") == "2023. november"

    def test_a_datum_ora_nelkul_is_jo(self):
        assert album_date_label("2023-11-04", "hu") == "2023. november"

    def test_a_felulet_nyelve_donti_el_a_honapnevet(self):
        assert album_date_label("2023-11-04", "en") == "2023. November"

    @pytest.mark.parametrize("rossz", ["", "nem-datum", "2023", "0000-99-01"])
    def test_ertelmezhetetlen_datumra_ures(self, rossz):
        """Kitalálni nem szabad: hibás dátumnál a mező marad ki."""
        assert album_date_label(rossz, "hu") == ""


class TestAKozosForrasmappa:
    """A két mező forrása — ugyanaz, mint a címé."""

    def test_egy_mappabol_mindket_mezo_megvan(self, tmp_path):
        mappa = tmp_path / "AI"
        photos = [
            _Photo(str(mappa), "a.jpg", taken_at="2023-11-04T18:30:00"),
            _Photo(str(mappa), "b.jpg", taken_at="2023-11-20T09:00:00"),
        ]

        uid, datum = album_fields_of(
            [_Source(str(mappa / "a.jpg"))], photos, language="hu"
        )

        assert ALBUM_UID.match(uid)
        assert datum == "2023. november"

    def test_az_album_datuma_a_MAPPA_legregebbi_kepe(self, tmp_path):
        """A golden invariáns: 11 kollázs ugyanabból a mappából — MIND
        ugyanazt az `albumDate`-et viseli. A kijelölés tehát nem
        befolyásolhatja: nem a kiválasztott, hanem a mappa képeiből megy."""
        mappa = tmp_path / "AI"
        photos = [
            _Photo(str(mappa), "regi.jpg", taken_at="2023-11-04T18:30:00"),
            _Photo(str(mappa), "uj.jpg", taken_at="2024-01-02T09:00:00"),
        ]

        _, csak_ujjal = album_fields_of(
            [_Source(str(mappa / "uj.jpg"))], photos, language="hu"
        )

        assert csak_ujjal == "2023. november"

    def test_ket_mappabol_nincs_forrasalbum(self, tmp_path):
        photos = [
            _Photo(str(tmp_path / "AI"), "a.jpg", taken_at="2023-11-04T18:30:00"),
            _Photo(str(tmp_path / "lake"), "b.jpg", taken_at="2024-01-02T09:00:00"),
        ]

        assert album_fields_of(
            [
                _Source(str(tmp_path / "AI" / "a.jpg")),
                _Source(str(tmp_path / "lake" / "b.jpg")),
            ],
            photos,
            language="hu",
        ) == ("", "")

    def test_datum_nelkuli_mappa_azonositot_meg_kap(self, tmp_path):
        """A hiányzó dátum nem viheti el az azonosítót is."""
        mappa = tmp_path / "AI"
        uid, datum = album_fields_of(
            [_Source(str(mappa / "a.jpg"))],
            [_Photo(str(mappa), "a.jpg")],
            language="hu",
        )

        assert ALBUM_UID.match(uid)
        assert datum == ""


@pytest.fixture
def host(qt_app, tmp_path):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    mappa = tmp_path / "AI"
    mappa.mkdir()
    for nev in ("a.jpg", "b.jpg"):
        make_jpeg(mappa / nev, size=(80, 60))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(mappa), "a.jpg", taken_at="2023-11-04T18:30:00"),
                    _Photo(str(mappa), "b.jpg", taken_at="2023-11-20T09:00:00"),
                ]
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

    def test_a_harom_mezo_a_fajlba_kerul(self, host, monkeypatch):
        # A felület nyelve dönti el a hónapnevet; a teszt kimondja, melyik
        # nyelven mér — enélkül a CI „C" lokálja adná a választ.
        from picasapy.app import collage_output

        monkeypatch.setattr(collage_output, "_felulet_nyelve", lambda: "hu")

        host.openCollage([0, 1])

        host.saveCollageDraft()

        piszkozat = host._collage_panel_draft_dir() / "autosave.cxf"
        assert piszkozat.is_file(), "nem született piszkozat"
        projekt = loads(piszkozat.read_bytes())
        assert ALBUM_UID.match(projekt.album_uid), "hiányzik az albumUID (#1092)"
        assert projekt.album_date == "2023. november"
        assert projekt.nodes, "nem került csomópont a piszkozatba"
        for node in projekt.nodes:
            assert NODE_UID.match(node.uid), f"hiányzó/rossz <uid>: {node.uid!r}"

    def test_a_megnyitott_projekt_uid_jai_tulelik_az_ujramentest(self, host, tmp_path):
        """Egy Picasa-fájl `<uid>`-jait nem cserélhetjük a sajátunkra."""
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir(exist_ok=True)
        kep = mappa / "AI.jpg"
        make_jpeg(kep, size=(400, 300))
        forras = str(tmp_path / "AI" / "a.jpg")
        eredeti_uid = "c91b4354e61f4a5a0000000000000000"
        (mappa / "AI.cxf").write_text(
            '<?xml version="1.0" encoding="utf-8" ?>\r\n'
            '<collage version="2" format="4:3" orientation="landscape"'
            ' theme="picturepile" shadows="0" captions="0"'
            ' albumUID="a4ef8e0fd2dbb152d25d79eb2bd2a28b">\r\n'
            " <albumTitle>AI</albumTitle>\r\n"
            " <albumDate>2023. november</albumDate>\r\n"
            ' <background type="solid" color="FFFFFFFF"/>\r\n'
            ' <spacing value="0.000000"/>\r\n'
            ' <node x="0.1" y="0.1" w="0.3" h="0.3" theta="0.0" scale="1.0">\r\n'
            "  <theme>noborder</theme>\r\n"
            f"  <src>{forras}</src>\r\n"
            f"  <uid>{eredeti_uid}</uid>\r\n"
            " </node>\r\n"
            "</collage>\r\n",
            encoding="utf-8",
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
        mappa = tmp_path / "Kollázsok"
        mappa.mkdir(exist_ok=True)
        kep = mappa / "AI.jpg"
        make_jpeg(kep, size=(400, 300))
        forras = str(tmp_path / "AI" / "a.jpg")
        (mappa / "AI.cxf").write_text(
            '<?xml version="1.0" encoding="utf-8" ?>\r\n'
            '<collage version="2" format="4:3" orientation="landscape"'
            ' theme="picturepile" shadows="0" captions="0">\r\n'
            ' <background type="solid" color="FFFFFFFF"/>\r\n'
            ' <spacing value="0.000000"/>\r\n'
            ' <node x="0.1" y="0.1" w="0.3" h="0.3" theta="0.0" scale="1.0">\r\n'
            "  <theme>noborder</theme>\r\n"
            f"  <src>{forras}</src>\r\n"
            "  <uid>c91b4354e61f4a5a0000000000000000</uid>\r\n"
            " </node>\r\n"
            "</collage>\r\n",
            encoding="utf-8",
        )
        host.openCollageProject(str(kep))

        host.openCollage([0, 1])
        host.saveCollageDraft()

        projekt = loads(
            (host._collage_panel_draft_dir() / "autosave.cxf").read_bytes()
        )
        assert "c91b4354e61f4a5a0000000000000000" not in [
            node.uid for node in projekt.nodes
        ], "az előző projekt azonosítója átszivárgott az új kollázsba"
