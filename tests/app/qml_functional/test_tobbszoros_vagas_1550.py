"""QML-funkcionális őr: #1550 — TÖBB `crop64`-et tartalmazó láncnál az
UTOLSÓ a hatályos, a felület is azt mutassa és mentse.

## Honnan van ilyen lánc?

A felhasználó gyűjteményét a **windowsos Picasa** írta: az éles korpuszban
(859 `.picasa.ini`, 18 801 szekció) **38** lánc tartalmaz egynél több
`crop64`-et. Ezeket mi OLVASSUK — a teszt ezért egy kézzel elhelyezett,
valósághű `.picasa.ini`-vel indul, nem a felületen gyártja a láncot.

## A szabály két, egymástól független bizonyítéka (a #1550-ben újramérve)

1. **Render-lánc** (`render/chain.py`, #130): a bejárás felülírja a
   `crop_op`-ot, tehát az UTOLSÓ `crop64` vág. Mérve: 800×600-as képre a
   `crop64=1,0000000080008000;bw=1;crop64=1,c0008000ffffffff;` lánc
   **200×300**-at ad — az első szerint 400×300 lenne.
2. **Éles korpusz:** a 38 több-`crop64`-es láncnál **38/38** esetben a
   `crop=rect64(...)` tükör-kulcs az UTOLSÓT tükrözi, az elsőt **nulla**
   esetben. (Összesen 763 lánc tartalmaz `crop64`-et, 761-hez van `crop=`,
   mind a 761 az utolsót tükrözi; `crop64` nélküli `crop=` nulla van.)

## Miért a vezérlőn keresztül, és miért a lemezt méri

A `EditSession.crop()` közvetlen hívása zöld lenne akkor is, ha a vágó-
eszköz a kijelölést más úton tölti elő, vagy a mentés máshonnan veszi a
`crop=` értéket. Ezért a teszt a valódi vezérlőket mozgatja (a néző
megnyitása, a Vágás eszköz nyitása, kattintás az **Alkalmaz** gombra), és
a végén a LEMEZRE ÍRT `.picasa.ini`-t olvassa vissza.

A javítás előtt mindhárom állítás bukott: a felület a bal felső negyedet
kínálta fel kijelölésként, és az Alkalmaz gomb a `crop=` kulcsot is arra
írta át — vagyis a kép látható tartalma megváltozott attól, hogy a
felhasználó semmit nem módosított.
"""

from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.ini import load_document, parse_document, save_document
from picasapy.ini.rect64 import Rect64, encode_rect64

# A két vágás szándékosan ÁTFEDÉS NÉLKÜLI, hogy az „első" és az „utolsó"
# összetéveszthetetlen legyen (a kerekítési tűrés se moshassa össze).
ELSO = Rect64(left=0.0, top=0.0, right=0.5, bottom=0.5)
UTOLSO = Rect64(left=0.75, top=0.5, right=1.0, bottom=1.0)
LANC = (
    f"crop64=1,{encode_rect64(ELSO)};bw=1;crop64=1,{encode_rect64(UTOLSO)};"
)


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


def _tobb_vagasos_ini(controller) -> None:
    """A 0. képhez a windowsos Picasa alakját utánzó, KÉT `crop64`-es lánc.

    Az írás az `ini/` csomag API-ján megy (sávhatár): `load_document` +
    `with_value` + `save_document`."""
    ut = _ini_ut(controller)
    nev = Path(str(controller.photos.filePathAt(0))).name
    doc = load_document(ut) if ut.exists() else parse_document("")
    doc = doc.with_value(nev, "filters", LANC, carried=True)
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


class TestAFeluletAzUtolsoVagastMutatja:
    """A vágó-eszköz nyitásakor betöltött kijelölés (`cropSelection` →
    `cropOverlay`) az UTOLSÓ `crop64` téglalapja."""

    def test_a_vago_eszkoz_az_utolso_crop64_et_tolti_elo(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller)
        assert _szekcio(controller).get("filters") == LANC, (
            "az előfeltétel nem áll: nem a két crop64-es lánc van a lemezen"
        )

        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)

        atfedes = _elem(window, "cropOverlay")
        assert atfedes.property("hasSelection") is True, (
            "a vágó-eszköz nem töltött elő kijelölést, pedig a láncban van "
            "crop64"
        )
        r = atfedes.property("cropRect")
        assert abs(r.x() - UTOLSO.left) < 0.01 and abs(r.y() - UTOLSO.top) < 0.01, (
            "a vágó-eszköz nem az UTOLSÓ (hatályos) vágást kínálja fel, "
            f"hanem mást: x={r.x():.3f} y={r.y():.3f} "
            f"(elvárt x={UTOLSO.left} y={UTOLSO.top})"
        )

    def test_a_hasCrop_igaz_marad(self, qml_app, qt_app):
        """Ellenkező irányú őr (#1045-tanulság): a javítás nem veheti el a
        „Visszavonás: Vágás"/„Alaphelyzet" utat — a gomb engedélyezettsége
        a `hasCrop`-on áll. A QML ugyanezt a property-t köti."""
        window, controller, engine = qml_app
        _tobb_vagasos_ini(controller)
        _nezobe_lep(window, qt_app)
        edit_ctl = engine.rootContext().contextProperty("editController")
        assert edit_ctl.property("hasCrop") is True


class TestAMentesAzUtolsotRogziti:
    """A lemezre írt `crop=` tükör-kulcs az UTOLSÓ `crop64`-et tükrözi —
    ugyanaz a szabály, amit az éles korpusz 38/38-ban mutat."""

    def test_valtoztatas_nelkuli_alkalmaz_nem_irja_at_a_vagast(
        self, qml_app, qt_app
    ):
        """A felhasználó megnyitja a vágó-eszközt és rányom az Alkalmazra,
        anélkül hogy a kijelölésen igazítana: a kép látható tartalma NEM
        változhat meg."""
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller)
        elotte = _szekcio(controller)["crop"]

        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)

        utana = _szekcio(controller)
        assert utana["crop"] == elotte, (
            "a változtatás nélküli Alkalmaz átírta a hatályos vágást — a "
            "felhasználó képe más kivágást mutat, pedig semmit nem "
            f"módosított:\n  előtte: {elotte}\n  utána : {utana.get('crop')}"
        )
        assert f"crop64=1,{encode_rect64(UTOLSO)};" in utana["filters"], (
            "az Alkalmaz nem az UTOLSÓ (hatályos) crop64-et tartotta meg: "
            f"{utana.get('filters')!r}"
        )
