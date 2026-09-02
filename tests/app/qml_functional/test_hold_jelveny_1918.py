"""#1918: a MEGTARTOTT tálca-bélyegképen jelvény van.

## A lelet

A megtartás nálunk **csak számként** létezett (`heldCount`): a képen semmi
nem jelezte, hogy egy elem megtartott-e. A gomb ikonja jelezte az
állapotot, a bélyegkép nem. A `holdadorner` szóra nulla találat volt a
forrásfában.

## Bizonyíték

A `thumbui/#holdadorner` sztring (`0x00cad36c`) egyetlen helyről
hivatkozott: `0x007145c0`, az **adorner-képek gyorsítótárának** egyszeri
feltöltője. A betöltési sorrend: `#holdadorner` (+0x00) · `shortcut`
(+0x28) · `star` (+0x50) · `web` (+0x78) · `geo` (+0xa0) · `sync` ·
`suppress` · `dirty` · `movie` · `people`.

⇒ **Jelvény, nem elrendezési elem** — ugyanabból a családból, mint a
csillag vagy a geocímke. Mérete a respack-rétegfejléc szerint 10×10.

## ⚠️ A jelvény a MEGLÉVŐ `hold-pin.svg`

Nem a respackből kicsomagolt PNG: a projekt egyetlen kicsomagolt
Picasa-képet sem szállít, és a **rács-cella ugyanezt a rajzot** használja
(#455, `holdMark`) — így a két hely ugyanazt jelenti ugyanazzal a jellel.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_jpeg


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elemek(window, nev: str) -> list:
    return [it for it in _walk(window.contentItem()) if it.objectName() == nev]


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _harom_kep(qml_app, qt_app):
    window, controller, _e = qml_app
    lib = Path(controller.watchedFolders[0])
    for i in range(3):
        make_jpeg(lib / f"h{i}.jpg", size=(60, 40))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()
    return window, controller


class TestAJelveny:
    def test_a_MEGTARTOTT_kepen_megjelenik(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        sorok = list(range(min(3, controller.photos.rowCount())))
        window.setProperty("selectedIndexes", sorok)
        window.setProperty("selectedIndex", sorok[0])
        qt_app.processEvents()

        # kijelölés alatt (nincs megtartás) EGYETLEN jelvény sem látszik
        assert _var(qt_app, lambda: len(_elemek(window, "trayPreviewThumb")) > 0)
        assert not [j for j in _elemek(window, "trayHoldMark") if j.isVisible()], (
            "megtartás nélkül is látszik jelvény"
        )

        controller.holdRows(sorok[:1])
        qt_app.processEvents()
        assert _var(
            qt_app,
            lambda: len([j for j in _elemek(window, "trayHoldMark") if j.isVisible()]) == 1,
        ), "a megtartott képen nem jelent meg a jelvény (#1918)"

    def test_a_jelveny_a_BELYEGKEPEN_ul_es_belefer(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        sorok = list(range(min(3, controller.photos.rowCount())))
        window.setProperty("selectedIndexes", sorok)
        window.setProperty("selectedIndex", sorok[0])
        qt_app.processEvents()
        controller.holdRows(sorok[:1])
        assert _var(
            qt_app,
            lambda: any(j.isVisible() for j in _elemek(window, "trayHoldMark")),
        )
        for jelveny in _elemek(window, "trayHoldMark"):
            if not jelveny.isVisible():
                continue
            cella = jelveny.parentItem()
            assert jelveny.width() <= cella.width(), "a jelvény szélesebb a cellánál"
            assert jelveny.height() <= cella.height(), "a jelvény magasabb a cellánál"

    def test_a_RACS_es_a_TALCA_ugyanazt_a_rajzot_hasznalja(self):
        """Ugyanaz az állapot, ugyanaz a jel — két helyen."""
        import picasapy.app

        qml = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
        racs = (qml / "ThumbDelegate.qml").read_text(encoding="utf-8")
        talca = (qml / "TrayBar.qml").read_text(encoding="utf-8")
        assert 'source: "icons/hold-pin.svg"' in racs
        assert 'source: "icons/hold-pin.svg"' in talca

    def test_a_forras_kimondja_hogy_NEM_kicsomagolt_kep(self):
        import picasapy.app

        talca = (
            Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
        ).read_text(encoding="utf-8")
        kezdet = talca.index('objectName: "trayHoldMark"')
        assert "kicsomagolt" in talca[kezdet - 1200 : kezdet]
