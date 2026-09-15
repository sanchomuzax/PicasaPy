"""#2966 — a közös háttérművelet-jelző MEGSZAKÍTÁS-csatornája.

Az eredeti Picasa jobb-felső sarki jelzőjén gomb volt, amivel a futó
háttérművelet **valóban** leállt (a #3112 mérése: a megerősítő párbeszéd
IGEN ága állítja a közös ős `+0x51` jelzőjét, és a munkavégző olvassa).
Nálunk a #505 busy-nyilvántartás eddig csak azt tudta, hogy VAN munka —
azt nem, hogy leállítható-e, és nem volt mivel leállítani.

Ez a fájl a nyilvántartás megszakítás-csatornáját méri; a felületi
megjelenést a `test_qml_hatterjelzo_2966.py` őrzi.
"""

from __future__ import annotations

import threading

from picasapy.app.busy_registry import AppBusyRegistry


class TestMegszakitasCsatorna:
    def test_ures_nyilvantartas_nem_megszakithato(self, qt_app):
        nyilvantarto = AppBusyRegistry()
        assert nyilvantarto.cancellable is False

    def test_regisztralt_visszahivas_utan_megszakithato(self, qt_app):
        nyilvantarto = AppBusyRegistry()
        nyilvantarto.register_cancel(lambda: None)
        assert nyilvantarto.cancellable is True

    def test_a_kereses_minden_regisztralt_visszahivast_meghiv(self, qt_app):
        nyilvantarto = AppBusyRegistry()
        hivasok = []
        nyilvantarto.register_cancel(lambda: hivasok.append("a"))
        nyilvantarto.register_cancel(lambda: hivasok.append("b"))
        nyilvantarto.request_cancel()
        assert sorted(hivasok) == ["a", "b"]

    def test_kijelentkezes_utan_nem_hivodik(self, qt_app):
        nyilvantarto = AppBusyRegistry()
        hivasok = []
        jegy = nyilvantarto.register_cancel(lambda: hivasok.append("a"))
        nyilvantarto.unregister_cancel(jegy)
        nyilvantarto.request_cancel()
        assert hivasok == []
        assert nyilvantarto.cancellable is False

    def test_a_valtozas_jelzest_valt_ki(self, qt_app):
        nyilvantarto = AppBusyRegistry()
        valtozasok = []
        nyilvantarto.cancellableChanged.connect(lambda: valtozasok.append(1))
        jegy = nyilvantarto.register_cancel(lambda: None)
        nyilvantarto.unregister_cancel(jegy)
        assert len(valtozasok) == 2

    def test_egy_bukó_visszahivas_nem_nyeli_el_a_tobbit(self, qt_app):
        """Egy művelet hibás leállítója nem akadályozhatja meg a többiét —
        a felhasználó egyetlen kattintással MINDEN futó munkát leállít."""
        nyilvantarto = AppBusyRegistry()
        hivasok = []

        def bukik() -> None:
            raise RuntimeError("szándékos")

        nyilvantarto.register_cancel(bukik)
        nyilvantarto.register_cancel(lambda: hivasok.append("ok"))
        nyilvantarto.request_cancel()
        assert hivasok == ["ok"]

    def test_hatterszalbol_is_regisztralhato(self, qt_app):
        """A `_start_background` a hívó szálán regisztrál, a kijelentkezés
        viszont a WORKER szálán történik (a `finally`-ben)."""
        nyilvantarto = AppBusyRegistry()
        jegyek = []

        szal = threading.Thread(
            target=lambda: jegyek.append(nyilvantarto.register_cancel(lambda: None))
        )
        szal.start()
        szal.join(5)
        assert nyilvantarto.cancellable is True
        nyilvantarto.unregister_cancel(jegyek[0])
        assert nyilvantarto.cancellable is False
