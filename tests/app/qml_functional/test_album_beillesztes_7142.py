"""#7142: albumnézetben a Beillesztés az albumhoz adja a képeket, fájlt nem másol.

Az eredeti `0x00784100` közönséges gyűjtemény (album) célnál kihagyja a
fájlműveleti ágat: nincs megerősítő kérdés, nincs fájlmásolás, az elemek az
album tagjai lesznek. A Kivágás sem töröl a forrásból.

A próbák a VALÓDI főablakon futnak (`qml_app`): a menü és a Ctrl+V közös
`beillesztAVagolaprol` függvényét hívjuk, és a lemez, az `.picasa.ini` és a
rács modellje alapján ítélünk, nem a forrás alapján.

Mit őriz (a jegy „Kész, ha” és „Nem szabad” pontjai):
  * albumnézetben a menü és a Ctrl+V a vágólap képeit az album tagjává teszi,
    és sehol nem keletkezik új fájl (a korábban megnyitott mappa változatlan);
  * a már tag kép nem kerül kétszer az albumba;
  * Kivágás után ugyanígy működik, a forrásfájl a helyén marad;
  * albumnézetben nincs megerősítő kérdés és nincs köteg (másolás/áthelyezés);
  * a célhiány-üzenet nem szól közbe albumnál, akkor sem, ha nincs mappa;
  * mappanézetben a viselkedés változatlan (az eltérő mappás kérdés megmarad).

A pozícióbeszúrás (a cél rács első kijelölt eleme) szándékosan nincs
benne: a PicasaPy kézi album-sorrendje saját kiterjesztés (#1721).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest
from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre

from picasapy.index import open_index, sync_tree
from picasapy.scanner import PICASA_INI_NAME
from picasapy.ini.albums import parse_album_refs
from picasapy.ini.document import parse_document

_CEL_HIANY = "A Folder or Album must be selected to do this."
_KEPEK = (".jpg", ".jpeg", ".png")


def _gyerek(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kepek(mappa: Path) -> dict[str, bytes]:
    """A mappa képfájljai tartalommal: ebből látszik, ha bármi keletkezik/mozdul."""
    return {
        p.name: p.read_bytes()
        for p in sorted(mappa.iterdir())
        if p.suffix.lower() in _KEPEK
    }


def _tagok(controller) -> list[str]:
    """A rácson ténylegesen látszó (album-nézet) képek nevei."""
    return sorted(photo.name for photo in controller.photos.photos)


def _vizualis_bejaras(elem):
    for gyerek in elem.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _latszo_belyegek(window) -> int:
    """A rácson KIRAJZOLT (látható, nem nulla méretű) bélyegképek száma."""
    return sum(
        1
        for elem in _vizualis_bejaras(window.contentItem())
        if elem.objectName() == "thumbImage"
        and elem.isVisible()
        and elem.width() > 0
        and elem.height() > 0
    )


def _token_szamlalo(mappa: Path, kep: str, token: str) -> int:
    ini = mappa / PICASA_INI_NAME
    if not ini.is_file():
        return 0
    document = parse_document(ini.read_text(encoding="utf-8"))
    szakasz = document.section(kep)
    if szakasz is None:
        return 0
    return parse_album_refs(szakasz.get("albums") or "").count(token)


def _beillesztes(window, qt_app) -> None:
    QMetaObject.invokeMethod(
        window, "beillesztAVagolaprol", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


class _Kotegek:
    """Albumnézetben SEM megerősítés, SEM fájlköteg nem indulhat."""

    def __init__(self, vezerlo, monkeypatch):
        self.hivasok: list[tuple[str, tuple]] = []
        self.megerositesek: list[tuple] = []
        vezerlo.clipboardPasteConfirmationRequested.connect(
            lambda *args: self.megerositesek.append(args)
        )
        for nev in ("_copy_batch", "_move_batch"):
            monkeypatch.setattr(
                vezerlo, nev, lambda *a, _nev=nev, **k: self.hivasok.append((_nev, a))
            )

    @property
    def semmi(self) -> bool:
        return not self.hivasok and not self.megerositesek


@pytest.fixture
def helyzet(qml_app, qt_app, tmp_path, monkeypatch):
    """Egy album (a.jpg tag), albumnézetben; b.jpg ugyanabból, c.jpg MÁS mappából."""
    window, controller, engine = qml_app
    vezerlo = engine.rootContext().contextProperty("fileOpsController")
    assert vezerlo is not None, "a fileOpsController nincs bekötve"
    kepek = tmp_path / "kepek"
    masik = tmp_path / "masik"
    masik.mkdir()
    make_jpeg(masik / "c.jpg", size=(64, 64))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, masik)

    token = controller.createAlbum("Album 7142", [0])
    assert token, "a próba-album nem jött létre"
    controller.showAlbum(token)
    qt_app.processEvents()
    assert controller.viewModeName == "album"
    assert _tagok(controller) == ["a.jpg"]

    return {
        "window": window,
        "controller": controller,
        "vezerlo": vezerlo,
        "qt_app": qt_app,
        "kepek": kepek,
        "masik": masik,
        "token": token,
        "gyoker": tmp_path,
        "kotegek": _Kotegek(vezerlo, monkeypatch),
    }


class TestAlbumnezetBeillesztes:
    def test_masolt_kepek_az_album_tagjai_lesznek_fajl_nelkul(self, helyzet):
        h = helyzet
        kepek_elotte, masik_elotte = _kepek(h["kepek"]), _kepek(h["masik"])
        mappa_elotte = h["controller"].currentFolder
        h["vezerlo"].copyFilesToClipboard(
            [str(h["kepek"] / "b.jpg"), str(h["masik"] / "c.jpg")]
        )
        assert h["vezerlo"].clipboardHasFiles is True

        _beillesztes(h["window"], h["qt_app"])

        assert _tagok(h["controller"]) == ["a.jpg", "b.jpg", "c.jpg"], (
            "a beillesztett képek nem lettek az album tagjai"
        )
        assert _kepek(h["kepek"]) == kepek_elotte, "új kép keletkezett a korábbi mappában"
        assert _kepek(h["masik"]) == masik_elotte, "a másik mappa képei változtak"
        assert h["controller"].currentFolder == mappa_elotte
        assert h["kotegek"].semmi, "albumnézetben nincs megerősítés és nincs köteg"
        assert _token_szamlalo(h["kepek"], "b.jpg", h["token"]) == 1
        assert _token_szamlalo(h["masik"], "c.jpg", h["token"]) == 1

    def test_az_album_rendezett_nezete_a_rajzolt_racson_is_megjelenik(self, helyzet):
        """Kirajzolt eredmény: a rács modellje a beillesztés után 2 képet ad."""
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["kepek"] / "b.jpg")])

        _beillesztes(h["window"], h["qt_app"])

        racs = _gyerek(h["window"], "photoGrid")
        assert racs.property("visible") is True
        assert var_feltetelre(h["qt_app"], lambda: _latszo_belyegek(h["window"]) == 2), (
            f"a rajzolt rácson {_latszo_belyegek(h['window'])} bélyegkép látszik, 2 kellene"
        )
        assert h["controller"].photos.rowCount() == 2
        assert h["controller"].viewModeName == "album"
        assert h["controller"].currentAlbumToken == h["token"]

    def test_a_mar_tag_kep_nem_kerul_ketszer_az_albumba(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["kepek"] / "a.jpg")])

        _beillesztes(h["window"], h["qt_app"])
        _beillesztes(h["window"], h["qt_app"])

        assert h["kotegek"].semmi, "a már tag kép beillesztése fájlt másolna"
        assert _tagok(h["controller"]) == ["a.jpg"]
        assert _token_szamlalo(h["kepek"], "a.jpg", h["token"]) == 1
        counts = {a["token"]: a["count"] for a in h["controller"].albums}
        assert counts.get(h["token"]) == 1

    def test_kivagas_utan_is_tag_lesz_es_a_forras_a_helyen_marad(self, helyzet):
        h = helyzet
        kepek_elotte, masik_elotte = _kepek(h["kepek"]), _kepek(h["masik"])
        h["vezerlo"].cutFilesToClipboard(
            [str(h["kepek"] / "b.jpg"), str(h["masik"] / "c.jpg")]
        )
        assert h["vezerlo"].clipboardHasFiles is True

        _beillesztes(h["window"], h["qt_app"])

        assert _tagok(h["controller"]) == ["a.jpg", "b.jpg", "c.jpg"]
        assert (h["kepek"] / "b.jpg").is_file(), "a kivágott kép eltűnt a forrásból"
        assert (h["masik"] / "c.jpg").is_file(), "a kivágott kép eltűnt a forrásból"
        assert _kepek(h["kepek"]) == kepek_elotte
        assert _kepek(h["masik"]) == masik_elotte
        assert h["kotegek"].semmi, "kivágásnál sem indulhat áthelyezés/kérdés"

    def test_a_ctrl_v_billentyu_is_az_albumhoz_ad(self, helyzet):
        h = helyzet
        h["vezerlo"].copyFilesToClipboard([str(h["kepek"] / "b.jpg")])
        kepek_elotte = _kepek(h["kepek"])
        h["window"].requestActivate()
        h["qt_app"].processEvents()
        assert _gyerek(h["window"], "shortcutPasteFiles").property("enabled") is True

        QTest.keyClick(h["window"], Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
        h["qt_app"].processEvents()

        assert _tagok(h["controller"]) == ["a.jpg", "b.jpg"]
        assert _kepek(h["kepek"]) == kepek_elotte
        assert h["kotegek"].semmi

    def test_a_celhiany_uzenet_nem_szol_kozbe_albumnal(self, helyzet):
        """Albumnézetben a cél az album: mappa hiányában sem „nincs cél”."""
        h = helyzet
        h["controller"]._current_folder = ""
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])

        _beillesztes(h["window"], h["qt_app"])

        szoveg = _gyerek(h["window"], "errorBannerText").property("text")
        assert szoveg != _CEL_HIANY, "az album célnál célhiány-üzenet jelent meg"
        assert _tagok(h["controller"]) == ["a.jpg", "c.jpg"]
        assert h["kotegek"].semmi

    def test_a_konyvtarban_nem_levo_fajl_nem_masolodik_es_nem_lesz_tag(
        self, helyzet
    ):
        h = helyzet
        kivul = h["gyoker"] / "kivul"
        kivul.mkdir()
        make_jpeg(kivul / "z.jpg", size=(32, 32))
        kepek_elotte = _kepek(h["kepek"])
        h["vezerlo"].copyFilesToClipboard([str(kivul / "z.jpg")])

        _beillesztes(h["window"], h["qt_app"])

        assert _tagok(h["controller"]) == ["a.jpg"]
        assert _kepek(h["kepek"]) == kepek_elotte, "albumnézetben fájl másolódott"
        assert not list(kivul.glob("*.ini")), "idegen mappába ini került"
        assert h["kotegek"].semmi


class TestMappanezetValtozatlan:
    def test_mappanezetben_az_eltero_mappas_beillesztes_tovabbra_is_kerdez(
        self, helyzet
    ):
        h = helyzet
        h["controller"].selectFolder(str(h["kepek"]))
        h["qt_app"].processEvents()
        assert h["controller"].viewModeName == "folder"
        h["vezerlo"].copyFilesToClipboard([str(h["masik"] / "c.jpg")])

        _beillesztes(h["window"], h["qt_app"])

        assert len(h["kotegek"].megerositesek) == 1, (
            "mappanézetben az eltérő mappás beillesztés megerősítést kér"
        )
        assert _token_szamlalo(h["masik"], "c.jpg", h["token"]) == 0, (
            "mappanézetben a beillesztés nem adhat albumtagságot"
        )
