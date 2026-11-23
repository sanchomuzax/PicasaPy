"""QML-funkcionális őr: #1553 és #7367, az Alkalmaz gomb hatása a `crop64`-ekre.

## A szabály

Az eredeti Picasa a lánc UTOLSÓ elemének nevét a `crop64` literálhoz
hasonlítja (`Picasa3.exe`, `0x006b4300`): egyezéskor a meglévő rekord
koordinátáit írja át, minden más végrekordnál új `crop64` elemet fűz a
lánc végére (#7367). A korábbi és a közbeeső elemek mindig megmaradnak
(#1553: az Alkalmaz nem vonja össze a Picasa-eredetű rétegeket).

A Visszavonás a `filters=` lánc elemein lépked. Helyben frissítésnél nincs
új lépés, ezért két közvetlenül egymás utáni Alkalmaz után EGY Visszavonás
mindkét vágást visszaveszi, az Újra pedig a MÁSODIK téglalapot hozza vissza.
Ha a két vágás között más művelet áll, az új `crop64` a lánc végére kerül, és
a Visszavonás az előző vágást állítja vissza.

## Miért a gombra kattint, és miért a lemezt méri

Az `EditSession` közvetlen hívása zöld lenne akkor is, ha az Alkalmaz gomb
más úton menti a vágást. A teszt ezért valódi egérkattintást ad a
`cropApplyButton`-ra (és a Visszavonás/Újra gombokra), és a LEMEZRE írt
`.picasa.ini`-t olvassa vissza.
"""

from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest

from picasapy.ini import load_document, parse_document, save_document
from picasapy.ini.rect64 import Rect64, encode_rect64

# A Picasa-eredetű, KÉT vágásos kiindulási lánc (a #1550 mintája): a két
# téglalap szándékosan átfedés nélküli, hogy összetéveszthetetlen legyen.
ELSO = Rect64(left=0.0, top=0.0, right=0.5, bottom=0.5)
UTOLSO = Rect64(left=0.75, top=0.5, right=1.0, bottom=1.0)
# A lánc `crop64`-gyel VÉGZŐDIK: az Alkalmaz ezt írja át helyben (#7367).
LANC_CROP_VEGU = f"crop64=1,{encode_rect64(ELSO)};bw=1;crop64=1,{encode_rect64(UTOLSO)};"
# A lánc `bw`-re végződik: az Alkalmaz új `crop64`-et fűz a végére.
LANC_BW_VEGU = f"crop64=1,{encode_rect64(ELSO)};crop64=1,{encode_rect64(UTOLSO)};bw=1;"

# A felhasználó ÚJ kijelölése a vágó-eszközben (relatív x, y, szél, mag).
UJ_KIJELOLES = QRectF(0.25, 0.25, 0.5, 0.5)
UJ = Rect64(left=0.25, top=0.25, right=0.75, bottom=0.75)
MASODIK_KIJELOLES = QRectF(0.125, 0.125, 0.5, 0.5)
MASODIK = Rect64(left=0.125, top=0.125, right=0.625, bottom=0.625)


def _crop(rect: Rect64) -> str:
    return f"crop64=1,{encode_rect64(rect)};"


def _elem(root, nev: str) -> QObject:
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kozeppont(item) -> QPoint:
    kozep = item.mapToScene(
        QPointF(item.property("width") / 2, item.property("height") / 2)
    )
    return QPoint(round(kozep.x()), round(kozep.y()))


def _kattints(window, item, qt_app) -> None:
    """Valódi egérkattintás a vezérlőre — tiltott/takart gomb nem reagál."""
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _kozeppont(item),
    )
    qt_app.processEvents()


def _ini_ut(controller) -> Path:
    kep = Path(str(controller.photos.filePathAt(0)))
    return kep.parent / ".picasa.ini"


def _tobb_vagasos_ini(controller, lanc: str) -> None:
    """A 0. képhez a windowsos Picasa alakját utánzó, KÉT `crop64`-es lánc.

    A `crop=` tükör a lánc utolsó `crop64`-ét mutatja. Az írás az `ini/`
    csomag API-ján megy (sávhatár)."""
    ut = _ini_ut(controller)
    nev = Path(str(controller.photos.filePathAt(0))).name
    doc = load_document(ut) if ut.exists() else parse_document("")
    doc = doc.with_value(nev, "filters", lanc, carried=True)
    doc = doc.with_value(nev, "crop", f"rect64({encode_rect64(UTOLSO)})")
    save_document(doc, ut)


def _szekcio(controller) -> dict[str, str]:
    ut = _ini_ut(controller)
    if not ut.exists():
        return {}
    nev = Path(str(controller.photos.filePathAt(0))).name
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(ut, encoding="utf-8")
    return dict(parser[nev]) if parser.has_section(nev) else {}


def _nezobe_lep(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    return nezo


def _vago_eszkozt_nyit(window, qt_app):
    panel = _elem(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    return panel


def _uj_kijelolest_huz(window, qt_app, rect: QRectF = UJ_KIJELOLES) -> None:
    atfedes = _elem(window, "cropOverlay")
    atfedes.setProperty("cropRect", rect)
    atfedes.setProperty("hasSelection", True)
    qt_app.processEvents()


def _crop64_lista(filters: str) -> list[str]:
    """A lánc `crop64` bejegyzéseinek hex-értékei, sorrendben."""
    return [
        elem.split(",", 1)[1]
        for elem in filters.split(";")
        if elem.lower().startswith("crop64=")
    ]


def _vag(window, qt_app, rect: QRectF = UJ_KIJELOLES) -> None:
    """Vágó-eszköz megnyitása, új kijelölés húzása, valódi kattintás az Alkalmazra."""
    _vago_eszkozt_nyit(window, qt_app)
    _uj_kijelolest_huz(window, qt_app, rect)
    _kattints(window, _elem(window, "cropApplyButton"), qt_app)


def _gomb_engedelyezett(window, nev: str) -> bool:
    return bool(_elem(window, nev).property("buttonEnabled"))


def _szerkeszto_vezerlo(engine):
    return engine.rootContext().contextProperty("editController")


class TestAzAlkalmazNemDobjaElAKorabbiVagasokat:
    """Az adatbiztonsági mag: a felhasználó Picasa-ban készült rétegei
    nem tűnhetnek el attól, hogy egyszer újravág."""

    def test_az_uj_vagas_a_lanc_vegere_kerul_ha_nem_crop64_a_vegrekord(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller, LANC_BW_VEGU)
        assert _szekcio(controller).get("filters") == LANC_BW_VEGU, (
            "az előfeltétel nem áll: nem a bw-végű lánc van a lemezen"
        )

        _nezobe_lep(window, qt_app)
        _vag(window, qt_app)

        filters = _szekcio(controller).get("filters", "")
        assert filters == LANC_BW_VEGU + _crop(UJ), (
            "az Alkalmaz nem a lánc végére fűzte az új vágást, hanem "
            "átrendezte vagy eldobta a Picasa-eredetű rétegeket:\n"
            f"  előtte: {LANC_BW_VEGU}\n  utána : {filters}"
        )

    def test_a_crop_tukorkulcs_az_UJ_vagast_mutatja(self, qml_app, qt_app):
        """#1544/#1550: a `crop=` kulcs mindig az UTOLSÓ `crop64` (a
        korpuszban 761/761, a több-vágásosnál 38/38)."""
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller, LANC_BW_VEGU)
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app)

        szekcio = _szekcio(controller)
        assert szekcio.get("crop") == f"rect64({encode_rect64(UJ)})", (
            "a crop= tükörkulcs nem az új (hatályos) vágást tükrözi: "
            f"{szekcio.get('crop')!r}"
        )


class TestALancVegiVagasHelybenFrissul:
    """#7367: `crop64`-gyel végződő láncon az Alkalmaz az utolsó rekordot írja
    át, a lánc nem nő, a korábbi elemek érintetlenek."""

    def test_az_utolso_crop64_koordinatai_valtoznak_a_rekordok_szama_nem(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller, LANC_CROP_VEGU)
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app)

        filters = _szekcio(controller).get("filters", "")
        assert filters == f"{_crop(ELSO)}bw=1;{_crop(UJ)}", (
            "az Alkalmaz nem a lánc végi crop64-et írta át:\n"
            f"  előtte: {LANC_CROP_VEGU}\n  utána : {filters}"
        )
        assert len(_crop64_lista(filters)) == len(_crop64_lista(LANC_CROP_VEGU))

    def test_a_crop_tukorkulcs_az_atirt_vagast_mutatja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller, LANC_CROP_VEGU)
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app)

        assert _szekcio(controller).get("crop") == f"rect64({encode_rect64(UJ)})"


class TestALepesenkentiVisszavonas:
    """A Visszavonás a `filters=` lánc elemein lépked."""

    def test_a_visszavonas_az_elozo_vagast_hozza_vissza(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller, LANC_BW_VEGU)
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app)

        _kattints(window, _elem(window, "editUndoButton"), qt_app)

        szekcio = _szekcio(controller)
        assert szekcio.get("filters") == LANC_BW_VEGU, (
            "a Visszavonás nem az Alkalmaz ELŐTTI láncot állította vissza:\n"
            f"  várt : {LANC_BW_VEGU}\n  kapott: {szekcio.get('filters')}"
        )
        assert szekcio.get("crop") == f"rect64({encode_rect64(UTOLSO)})", (
            "a Visszavonás után a crop= tükörkulcs nem a korábbi hatályos "
            f"vágás: {szekcio.get('crop')!r}"
        )

    def test_ket_egymas_utani_alkalmaz_utan_egy_visszavonas_a_vagatlan_kepet_adja(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app, UJ_KIJELOLES)
        _vag(window, qt_app, MASODIK_KIJELOLES)
        assert _szekcio(controller).get("filters") == _crop(MASODIK), (
            "az előfeltétel nem áll: a két Alkalmaz nem egyetlen crop64-et hagyott"
        )

        _kattints(window, _elem(window, "editUndoButton"), qt_app)

        szekcio = _szekcio(controller)
        assert "crop64" not in szekcio.get("filters", ""), (
            "egy Visszavonás nem vette vissza mindkét vágást: "
            f"{szekcio.get('filters')!r}"
        )
        assert "crop" not in szekcio, f"a crop= tükör megmaradt: {szekcio.get('crop')!r}"
        assert not _gomb_engedelyezett(window, "editUndoButton")

    def test_az_ujra_a_masodik_teglalapot_hozza_vissza(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app, UJ_KIJELOLES)
        _vag(window, qt_app, MASODIK_KIJELOLES)
        _kattints(window, _elem(window, "editUndoButton"), qt_app)

        _kattints(window, _elem(window, "editRedoButton"), qt_app)

        szekcio = _szekcio(controller)
        assert szekcio.get("filters") == _crop(MASODIK), (
            f"az Újra nem a MÁSODIK téglalapot hozta vissza: {szekcio.get('filters')!r}"
        )
        assert szekcio.get("crop") == f"rect64({encode_rect64(MASODIK)})"

    def test_masik_muvelet_utan_az_ujravagas_visszavonasa_az_elozo_vagast_hozza_vissza(
        self, qml_app, qt_app
    ):
        window, controller, engine = qml_app
        _nezobe_lep(window, qt_app)
        _vag(window, qt_app, UJ_KIJELOLES)
        _szerkeszto_vezerlo(engine).toggleTool("autocolor")
        qt_app.processEvents()
        _vag(window, qt_app, MASODIK_KIJELOLES)
        assert _szekcio(controller).get("filters") == (
            f"{_crop(UJ)}autocolor=1;{_crop(MASODIK)}"
        ), "az előfeltétel nem áll: az újravágás nem a lánc végére került"

        _kattints(window, _elem(window, "editUndoButton"), qt_app)

        szekcio = _szekcio(controller)
        assert szekcio.get("filters") == f"{_crop(UJ)}autocolor=1;", (
            f"a Visszavonás nem az előző vágást állította vissza: {szekcio.get('filters')!r}"
        )
        assert szekcio.get("crop") == f"rect64({encode_rect64(UJ)})"


class TestAValtoztatasNelkuliAlkalmaz:
    """Ellenkező irányú őr (#1045-tanulság): az Alkalmaz nem nyúlhat a lánchoz
    olyankor, amikor a felhasználó semmit nem módosított. A #1550 őre ugyanezt
    a képet a `crop=` felől nézi; itt a lánc tartalma a tét."""

    def test_valtozatlan_kijelolesnel_nem_valtozik_a_lanc(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller, LANC_CROP_VEGU)
        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)

        filters = _szekcio(controller).get("filters", "")
        assert filters == LANC_CROP_VEGU, (
            "a változtatás nélküli Alkalmaz módosította a láncot:\n"
            f"  előtte: {LANC_CROP_VEGU}\n  utána : {filters}"
        )
