"""#1544: „Az összes effektus beillesztése" a TELJES láncot vigye át — a
vágást és a vörösszem-javítást is.

## A mérés (a javítás előtt)

A `crop64=1,…;bw=1;sepia=1;redeye=1,abc;tilt=…` lánccal mérve a bekötött
(kötegelt, #426) réteg eredménye `bw=1;sepia=1;tilt=…` volt: elveszett a
**vágás** és a **vörösszem-javítás**. A `edit/effect_clipboard.py` a
`filterdesc.xml` `mode="history"` oszlopából KÖVETKEZTETVE szűrt.

## Miért téves volt a szűrés

A `Picasa3.exe` diszasszemblálva (#1534, `docs/decisions/
effektus-vagolap-ket-reteg.md`): a másoló (`0x005fecd0`) és a beillesztő
(`0x005fefc0`) teljes hívási útján **nincs szűrő-névre vonatkozó
összehasonlítás**; a bináris-indexben a `"filters"` sztringnek 33
kódhivatkozása van, a `crop64`-nek **nulla**.

## Miért a `.picasa.ini`-t méri, és miért a menüpontról

A `tests/app/test_photo_ops_controller.py` a vezérlő metódusait KÖZVETLENÜL
hívja — az zöld maradna akkor is, ha a menütétel tiltott vagy takart. Ez a
fájl (a #1475 mintájára) a valódi menütételeket süti el, és a végén a
LEMEZRE ÍRT `.picasa.ini` tartalmát olvassa vissza, nem a hívás
visszatérését.

## A célkép MÁS MÉRETARÁNYÚ

A fixture két képe szándékosan eltérő alakú: `a.jpg` 320×160 (fekvő 2:1),
`b.jpg` 100×100 (négyzet). A `crop64` rect64-koordinátái **relatívak**
([0..1]), ezért a vágás a más alakú célképre is érvényes marad — arányosan
ugyanazt a részt jelöli ki, sosem lóg ki a képből. A kompozíció más lesz;
adat nem vész el (az eredeti JPEG érintetlen, és a művelet visszavonható).
Ez az eredeti Picasa viselkedése is: a beillesztő a láncot egészben írja
vissza, célkép-méret szerinti kivétel nélkül.
"""

from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest

from support.qt_wait import wait_for_photo_op


def _elem(root, nev: str) -> QObject:
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _elsut(window, qt_app, nev: str) -> None:
    """A VALÓDI menütétel aktiválása — előbb megkövetelve, hogy a
    felhasználó egyáltalán rá tudjon kattintani."""
    tetel = _elem(window, nev)
    assert tetel.property("enabled") is True, (
        f"a(z) {nev} menüpont le van tiltva — a felhasználó nem éri el"
    )
    assert not tetel.property("placeholder"), (
        f"a(z) {nev} menüpont helyfoglaló (#416), tehát halott"
    )
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _kozeppont(item) -> QPoint:
    kozep = item.mapToScene(
        QPointF(item.property("width") / 2, item.property("height") / 2)
    )
    return QPoint(round(kozep.x()), round(kozep.y()))


def _kattints(window, item, qt_app) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _kozeppont(item),
    )
    qt_app.processEvents()


def _szekcio(controller, sor: int) -> dict[str, str]:
    """A `sor`-hoz tartozó kép SZEKCIÓJA a lemezre írt `.picasa.ini`-ből."""
    ut_kep = Path(str(controller.photos.filePathAt(sor)))
    ut = ut_kep.parent / ".picasa.ini"
    if not ut.exists():
        return {}
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(ut, encoding="utf-8")
    if not parser.has_section(ut_kep.name):
        return {}
    return dict(parser[ut_kep.name])


def _vagas_a_nulladik_kepre(window, qt_app) -> None:
    """Vágás a 0. képre a szerkesztőből (a #1528 tesztjének mintája) — így
    a `crop64` a láncba, a `crop=rect64(...)` tükör-kulcs pedig a szekcióba
    kerül, ugyanúgy, mint valódi használatkor."""
    window.setProperty("viewerOpen", True)
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = _elem(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    atfedes = _elem(window, "cropOverlay")
    atfedes.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
    atfedes.setProperty("hasSelection", True)
    qt_app.processEvents()
    _kattints(window, _elem(window, "cropApplyButton"), qt_app)
    window.setProperty("viewerOpen", False)
    qt_app.processEvents()


def _kotegelt(window, qt_app, controller, sor: int, nev: str) -> None:
    _kijelol(window, qt_app, [sor])
    wait_for_photo_op(
        controller, lambda: _elsut(window, qt_app, nev), qt_app=qt_app
    )


def _forras_lancot_epit(window, qt_app, controller) -> dict[str, str]:
    """A 0. képre vágás + vörösszem + melegítés — csupa valódi menüpontról.

    Így áll elő a jegyben mért lánc alakja: geometria (`crop64`), régió-adat
    (`redeye`) és „hangulat"-effekt (`warm`) egyszerre."""
    _vagas_a_nulladik_kepre(window, qt_app)
    _kotegelt(window, qt_app, controller, 0, "menuBatchAutoRedeye")
    _kotegelt(window, qt_app, controller, 0, "menuBatchWarmify")
    forras = _szekcio(controller, 0)
    assert "crop64=1," in forras.get("filters", ""), (
        "az előfeltétel nem áll: a vágás nem került a forráskép láncába — "
        f"{forras}"
    )
    assert "redeye" in forras.get("filters", ""), (
        f"az előfeltétel nem áll: nincs redeye a forrásláncban — {forras}"
    )
    return forras


class TestABeillesztesAtviszAVagast:
    """A #1544 magja: a menüpontról indított beillesztés után a célkép
    LEMEZRE ÍRT szekciója a teljes forrásláncot tartalmazza."""

    def test_a_cel_ugyanazt_a_lancot_kapja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        forras = _forras_lancot_epit(window, qt_app, controller)
        assert _szekcio(controller, 1).get("filters") is None

        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")

        cel = _szekcio(controller, 1)
        assert cel.get("filters") == forras["filters"], (
            "a beillesztés nem a teljes láncot vitte át:\n"
            f"  forrás: {forras.get('filters')!r}\n"
            f"  cél   : {cel.get('filters')!r}"
        )

    def test_a_VAGAS_atmegy(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _forras_lancot_epit(window, qt_app, controller)

        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")

        cel = _szekcio(controller, 1)
        assert "crop64=1," in cel.get("filters", ""), (
            "a vágás (crop64) elveszett a beillesztéskor — ez a #1544 "
            f"lelete; a cél lánca: {cel.get('filters')!r}"
        )

    def test_a_VOROSSZEM_javitas_atmegy(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _forras_lancot_epit(window, qt_app, controller)

        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")

        cel = _szekcio(controller, 1)
        assert "redeye" in cel.get("filters", ""), (
            "a vörösszem-javítás elveszett a beillesztéskor — ez a #1544 "
            f"lelete; a cél lánca: {cel.get('filters')!r}"
        )


class TestACropTukorkulcsIsKovet:
    """A `crop=` tükör-kulcs a rendereléshez kell (`docs/specs/
    filters-decoded.md`): a `filters=`-beli `crop64` önmagában az EREDETI
    Picasában nem vág. Az éles korpuszban 761/761 esetben a `crop=` értéke
    pontosan a lánc utolsó `crop64`-je — ezért a beillesztésnek is így kell
    írnia, különben ugyanaz a NAS-mappa a windowsos Picasában vágatlan
    képet mutatna."""

    def test_a_cel_megkapja_a_crop_kulcsot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        forras = _forras_lancot_epit(window, qt_app, controller)
        assert forras.get("crop", "").startswith("rect64("), (
            f"az előfeltétel nem áll: a forrásnak nincs crop= kulcsa — {forras}"
        )

        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")

        cel = _szekcio(controller, 1)
        assert cel.get("crop") == forras["crop"], (
            "a célkép nem kapta meg a `crop=` tükör-kulcsot, így a "
            "windowsos Picasa vágatlanul mutatná:\n"
            f"  forrás: {forras.get('crop')!r}\n"
            f"  cél   : {cel.get('crop')!r}"
        )

    def test_vagas_NELKULI_lanc_leveszi_a_cel_crop_kulcsat(self, qml_app, qt_app):
        """Ellenkező irányú őr (#1045-tanulság): ha a vágólapon NINCS
        `crop64`, a beillesztés a célkép meglévő `crop=` kulcsát is
        elveszi — a teljes csere szemantikája szerint. Enélkül a cél egy
        olyan `crop=`-pal maradna, aminek a láncban nincs párja: az éles
        korpuszban ilyen eset **nulla** van (761-ből)."""
        window, controller, _engine = qml_app
        # a CÉL (1. sor) kap vágást, a FORRÁS (0. sor) csak sima effektet
        window.setProperty("viewerOpen", True)
        nezo = _elem(window, "photoViewer")
        nezo.setProperty("currentIndex", 1)
        qt_app.processEvents()
        panel = _elem(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        atfedes = _elem(window, "cropOverlay")
        atfedes.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
        atfedes.setProperty("hasSelection", True)
        qt_app.processEvents()
        _kattints(window, _elem(window, "cropApplyButton"), qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert _szekcio(controller, 1).get("crop", "").startswith("rect64("), (
            "az előfeltétel nem áll: a célképnek nincs crop= kulcsa"
        )

        _kotegelt(window, qt_app, controller, 0, "menuBatchWarmify")
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")

        cel = _szekcio(controller, 1)
        assert "crop" not in cel, (
            "a beillesztés vágás nélküli láncot írt, de a célkép régi "
            f"`crop=` kulcsa bent maradt: {cel!r}"
        )


class TestAVisszavonasAVagastIsVisszaadja:
    """A beillesztés MINDKÉT kulcsot írja, ezért a visszavonásnak mindkettőt
    vissza kell állítania — különben a cél a régi lánccal, de az ÚJ
    vágással maradna (ugyanaz a hiba, amit a #465 a köteges úton javított)."""

    def test_a_visszavonas_a_cel_crop_kulcsat_is_visszaallitja(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _forras_lancot_epit(window, qt_app, controller)
        assert _szekcio(controller, 1) == {}

        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")
        assert "crop" in _szekcio(controller, 1), (
            "a beillesztés nem írt crop= kulcsot — a visszavonás nem mérhető"
        )

        _elsut(window, qt_app, "menuEditUndoPasteAllEffects")

        cel = _szekcio(controller, 1)
        assert "filters" not in cel and "crop" not in cel, (
            "a visszavonás nem állította vissza a beillesztés ELŐTTI "
            f"(üres) állapotot: {cel!r}"
        )
