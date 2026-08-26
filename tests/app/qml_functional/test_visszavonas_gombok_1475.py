"""#1475: a két kötegelt visszavonásnak legyen VEZÉRLŐJE a felületen.

## A mérés (a javítás előtt)

Három tag kész volt a vezérlőn, és a 142 QML-fájlban NULLA hivatkozás
mutatott rájuk (`scripts/kepesseg_or.py` alapállapota, `#1475` blokk):

| tag | hol |
|---|---|
| `canUndoPasteAllEffects` | `photo_ops_controller.py` |
| `undoPasteAllEffects` | `photo_ops_controller.py` |
| `canUndoBatchEdit` | `batch_effect_controller.py` |
| `undoBatchEdit` | `batch_effect_controller.py` |

Közben a MŰVELET elvégezhető volt: a `Szerkesztés ▸ Az összes effektus
beillesztése` és a `Kép ▸ Csoportos szerkesztés ▸ …` menüpontok élnek.
⇒ a felhasználó tudott olyat tenni, amit nem tudott visszacsinálni.

A `tests/app/test_photo_ops_controller.py` és a
`tests/app/test_batch_effect_controller.py` mindvégig ZÖLD volt — mert a
vezérlő metódusait közvetlenül hívja. Ez a fájl ezért KIZÁRÓLAG valódi
menüpontokon át dolgozik: előbb megköveteli, hogy a tétel engedélyezett
legyen, aztán elsüti, és a végén a LEMEZRE ÍRT `.picasa.ini`-t méri.

## Hol lettek a vezérlők, és miért ott

Az eredeti Picasa a visszavonást a **Szerkesztés menü élén** kínálja
(`eMenuEdit::ID_UNDO`/`ID_REDO`, ld. `docs/specs/picasa-hu-terminology.md`),
a felirat pedig **megnevezi a visszavonandó műveletet** (a `CFilterStackUI`
`undoname` kulcsa záró szóközzel áll, ld. `app/edit_action_names.py`).
Nálunk — a #465 óta — HÁROM külön verem van, ezért a Szerkesztés menü élére
két, művelet szerint nevesített tétel került; mindegyik a SAJÁT
`canUndo…`-jától függ, tehát külön-külön szürkül el.

## A rádió-csapda (#1468) ellen

A tételek `enabled`-kötése értékkötés, nem `checkable`/`checked` pár —
kattintás után a kötés újraértékelődik. Az itteni tesztek ezt méréssel
zárják le: a visszavonás UTÁN a tételnek MAGÁTÓL szürkévé kell válnia.
"""

from __future__ import annotations

import configparser
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

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


def _ini_ut(controller, sor: int) -> Path:
    return Path(str(controller.photos.filePathAt(sor))).parent / ".picasa.ini"


def _filters(controller, sor: int) -> str | None:
    """A `sor`-hoz tartozó kép nyers `filters=` értéke a lemezen."""
    ut = _ini_ut(controller, sor)
    if not ut.exists():
        return None
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(ut, encoding="utf-8")
    nev = Path(str(controller.photos.filePathAt(sor))).name
    if not parser.has_section(nev):
        return None
    return parser[nev].get("filters")


def _lancot_ad(controller, sor: int, qt_app, window) -> None:
    """A `sor` képének adunk egy `filters=` láncot — a kötegelt úton, a
    Kép ▸ Csoportos szerkesztés menüpontról (nem a vezérlőt hívva)."""
    _kijelol(window, qt_app, [sor])
    wait_for_photo_op(
        controller,
        lambda: _elsut(window, qt_app, "menuBatchWarmify"),
        qt_app=qt_app,
    )


class TestPasteAllEffectsVisszavonasa:
    """A #1475 magja: a beillesztés visszavonható a FELÜLETRŐL."""

    def test_a_menupont_letezik_es_kezdetben_TILTOTT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])

        tetel = _elem(window, "menuEditUndoPasteAllEffects")

        assert tetel.property("enabled") is False, (
            "nincs mit visszavonni, a menüpont mégis kattintható"
        )

    def test_beillesztes_utan_ELERHETO_es_visszaallitja_a_lancot(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _lancot_ad(controller, 0, qt_app, window)
        forras_lanc = _filters(controller, 0)
        assert forras_lanc, "a kiinduló állapot nem állt elő: nincs lánc"
        assert _filters(controller, 1) is None

        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")
        assert _filters(controller, 1) == forras_lanc, (
            "a beillesztés maga nem működött — a visszavonás nem mérhető"
        )

        _elsut(window, qt_app, "menuEditUndoPasteAllEffects")

        assert _filters(controller, 1) is None, (
            "a visszavonás menüpontja nem állította vissza a beillesztés "
            "ELŐTTI (üres) láncot"
        )

    def test_visszavonas_utan_a_menupont_MAGATOL_szurke_lesz(
        self, qml_app, qt_app
    ):
        """#1468-minta: a kattintás nem hagyhat inkonzisztens állapotot."""
        window, controller, _engine = qml_app
        _lancot_ad(controller, 0, qt_app, window)
        _kijelol(window, qt_app, [0])
        _elsut(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _elsut(window, qt_app, "menuEditPasteEffects")

        _elsut(window, qt_app, "menuEditUndoPasteAllEffects")

        assert (
            _elem(window, "menuEditUndoPasteAllEffects").property("enabled")
            is False
        ), "a visszavonás után is kattintható maradt — a kötés nem frissült"

    def test_a_puszta_MASOLAS_nem_teszi_elerhetove(self, qml_app, qt_app):
        """Ellenkező irányú őr: a másolás nem ír semmit, tehát nincs mit
        visszavonni — a tételnek szürkének KELL maradnia."""
        window, controller, _engine = qml_app
        _lancot_ad(controller, 0, qt_app, window)
        _kijelol(window, qt_app, [0])

        _elsut(window, qt_app, "menuEditCopyEffects")

        assert (
            _elem(window, "menuEditUndoPasteAllEffects").property("enabled")
            is False
        ), "a másolás önmagában visszavonhatónak látszik"


class TestKotegeltSzerkesztesVisszavonasa:
    def test_a_menupont_letezik_es_kezdetben_TILTOTT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])

        tetel = _elem(window, "menuEditUndoBatchEdit")

        assert tetel.property("enabled") is False, (
            "nincs mit visszavonni, a menüpont mégis kattintható"
        )

    def test_koteg_utan_ELERHETO_es_visszaallitja_a_lancot(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        assert _filters(controller, 0) is None

        _lancot_ad(controller, 0, qt_app, window)
        assert _filters(controller, 0), "a köteg nem írt láncot"

        _elsut(window, qt_app, "menuEditUndoBatchEdit")

        assert _filters(controller, 0) is None, (
            "a kötegelt szerkesztés visszavonása nem állította vissza a "
            "köteg ELŐTTI (üres) láncot"
        )

    def test_visszavonas_utan_a_menupont_MAGATOL_szurke_lesz(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _lancot_ad(controller, 0, qt_app, window)

        _elsut(window, qt_app, "menuEditUndoBatchEdit")

        assert (
            _elem(window, "menuEditUndoBatchEdit").property("enabled") is False
        ), "a visszavonás után is kattintható maradt — a kötés nem frissült"


class TestAKetVeremKulonAll:
    """A két tétel NEM egymás szinonimája: külön veremből dolgoznak, tehát
    az egyik elérhetősége nem hozhatja magával a másikét."""

    def test_a_koteg_nem_teszi_elerhetove_a_beillesztes_visszavonasat(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        _lancot_ad(controller, 0, qt_app, window)

        assert _elem(window, "menuEditUndoBatchEdit").property("enabled") is True
        assert (
            _elem(window, "menuEditUndoPasteAllEffects").property("enabled")
            is False
        ), "a kötegelt szerkesztés a beillesztés visszavonását is felnyitotta"


class TestAKommentEltunt:
    """A `Main.qml` kódkommentje azt állította, hogy ezek a műveletek
    „csak a vezérlőn elérhetők, UI-gomb nélkül" — ez már nem igaz, és egy
    elavult komment pontosan úgy rejti el a hiányt, ahogy a #1475-öt is
    elrejtette (zárt jegyekre hivatkozva)."""

    def test_a_main_qml_nem_allitja_tobbe_hogy_nincs_gomb(self):
        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
        ).read_text(encoding="utf-8")

        assert "UI-gomb nélkül" not in forras, (
            "a Main.qml még mindig azt állítja, hogy nincs UI-gomb"
        )
