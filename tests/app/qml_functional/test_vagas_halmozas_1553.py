"""QML-funkcionális őr: #1553 — az Alkalmaz gomb HALMOZZA a vágásokat, nem
vonja össze őket egyetlen `crop64`-re.

## Miért halmozás, és mi a bizonyíték

Az eredeti Picasában a `filters=` érték MAGA a visszavonás-verem: a
`CFilterStackUI` frissítője (`Picasa3.exe`, `0x006ad530`) a visszavonás-
listát a **`filters`**, az újra-listát a **`redo`** tulajdonságból építi
(ugyanaz a `0x0069f510` hívás, két kulccsal), és a Visszavonás gomb
felirata a lánc UTOLSÓ elemének a neve (`0x00753c46` — az utolsó elem
`[+0x10]` metódusa). Egy meglévő `crop64` helyben cserélése tehát a
visszavonás-előzményt semmisítené meg.

Ezt erősíti meg az eredeti saját felirat-párja is: `IDS_CROP_LABEL` =
„Crop" és `IDS_RECROP_LABEL` = „Recrop" (magyarul **„Vágás megismétlése"**,
`referencia/stringres-en-hu.tsv` 1506/1662). A `0x007533b0` a
`0x006b0140` („van-e már érvényes vágás") visszatérési értéke szerint
választ a kettő közül — az újravágás az eredetiben önálló, névvel bíró
művelet, nem a meglévő vágás átírása.

És az éles korpusz is ezt mutatja (`referencia/ini-korpusz/korpusz.txt`):
38 láncban van egynél több `crop64`, közülük **33-ban a két téglalap
átfedése IoU > 0,5** (ugyanannak a kivágásnak az újraigazítása), **14-ben
pedig további szűrők állnak az UTOLSÓ `crop64` UTÁN** — az „Összes
effektus beillesztése" (#1544) a lánc VÉGÉRE fűz, tehát azt nem
magyarázza. A `scan0016.png` szekcióban ráadásul maga az eredeti Picasa
írt egy **`redo=crop64=1,14effffdca5;enhance=1;crop64=1,ffffdca5;`** sort:
a redo-verem kizárólag Visszavonás hatására töltődik, tehát ez a lánc
valóban a Picasa `filters=` visszavonás-verme volt — két `crop64`-gyel,
amelyek CSAK a felső élükben térnek el (334 → 0).

## Miért a gombra kattint, és miért a lemezt méri

Az `EditSession` közvetlen hívása zöld lenne akkor is, ha az Alkalmaz gomb
más úton menti a vágást. A teszt ezért valódi egérkattintást ad a
`cropApplyButton`-ra, és a LEMEZRE írt `.picasa.ini`-t olvassa vissza.
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
LANC = f"crop64=1,{encode_rect64(ELSO)};bw=1;crop64=1,{encode_rect64(UTOLSO)};"

# A felhasználó ÚJ kijelölése a vágó-eszközben (relatív x, y, szél, mag).
UJ_KIJELOLES = QRectF(0.25, 0.25, 0.5, 0.5)
UJ = Rect64(left=0.25, top=0.25, right=0.75, bottom=0.75)


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

    Az írás az `ini/` csomag API-ján megy (sávhatár)."""
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


class TestAzAlkalmazNemDobjaElAKorabbiVagasokat:
    """Az adatbiztonsági mag: a felhasználó Picasa-ban készült rétegei
    nem tűnhetnek el attól, hogy egyszer újravág."""

    def test_az_uj_vagas_a_lanc_vegere_kerul(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller)
        assert _szekcio(controller).get("filters") == LANC, (
            "az előfeltétel nem áll: nem a két crop64-es lánc van a lemezen"
        )

        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)
        _uj_kijelolest_huz(window, qt_app)
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)

        filters = _szekcio(controller).get("filters", "")
        cropok = _crop64_lista(filters)
        assert cropok == [
            encode_rect64(ELSO),
            encode_rect64(UTOLSO),
            encode_rect64(UJ),
        ], (
            "az Alkalmaz nem a lánc végére fűzte az új vágást, hanem "
            "átrendezte vagy eldobta a Picasa-eredetű rétegeket:\n"
            f"  előtte: {LANC}\n  utána : {filters}"
        )
        assert "bw=1;" in filters, (
            f"az Alkalmaz elveszítette a lánc bw rétegét: {filters!r}"
        )

    def test_a_crop_tukorkulcs_az_UJ_vagast_mutatja(self, qml_app, qt_app):
        """#1544/#1550: a `crop=` kulcs mindig az UTOLSÓ `crop64` — a
        halmozás után is (a korpuszban 761/761, a több-vágásosnál 38/38)."""
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller)
        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)
        _uj_kijelolest_huz(window, qt_app)
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)

        szekcio = _szekcio(controller)
        assert szekcio.get("crop") == f"rect64({encode_rect64(UJ)})", (
            "a crop= tükörkulcs nem az új (hatályos) vágást tükrözi: "
            f"{szekcio.get('crop')!r}"
        )


class TestALepesenkentiVisszavonas:
    """A halmozás értelme: a Visszavonás rétegenként bont vissza, tehát a
    korábbi vágás VISSZAJÖN — nem a vágatlan kép."""

    def test_a_visszavonas_az_elozo_vagast_hozza_vissza(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller)
        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)
        _uj_kijelolest_huz(window, qt_app)
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)

        _kattints(window, _elem(window, "editUndoButton"), qt_app)

        szekcio = _szekcio(controller)
        assert szekcio.get("filters") == LANC, (
            "a Visszavonás nem az Alkalmaz ELŐTTI láncot állította vissza:\n"
            f"  várt : {LANC}\n  kapott: {szekcio.get('filters')}"
        )
        assert szekcio.get("crop") == f"rect64({encode_rect64(UTOLSO)})", (
            "a Visszavonás után a crop= tükörkulcs nem a korábbi hatályos "
            f"vágás: {szekcio.get('crop')!r}"
        )


class TestAValtoztatasNelkuliAlkalmaz:
    """Ellenkező irányú őr (#1045-tanulság): a halmozás nem hizlalhatja a
    láncot olyankor, amikor a felhasználó semmit nem módosított. A #1550
    őre ugyanezt a képet a `crop=` felől nézi; itt a lánc HOSSZA a tét."""

    def test_valtozatlan_kijelolesnel_nem_no_a_lanc(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _tobb_vagasos_ini(controller)
        _nezobe_lep(window, qt_app)
        _vago_eszkozt_nyit(window, qt_app)
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)

        filters = _szekcio(controller).get("filters", "")
        assert filters == LANC, (
            "a változtatás nélküli Alkalmaz módosította a láncot:\n"
            f"  előtte: {LANC}\n  utána : {filters}"
        )
