"""#2271 — a szöveg-stílus ténylegesen kerüljön a `.picasa.ini`-be.

Két, a felhasználó által látott hiba:

* **minden felirat félkövérként ment ki** — a `TextStyle.weight`
  osztály-alapértéke fixen 700;
* **minden körvonal eltűnt** — a körvonalvastagság (5. mező) fixen
  `0.000000`, ami a valódi Picasában »nincs körvonal«.

A mezők számozása ELLENŐRZÖTT (a jegy táblája, egy valódi korpusz-sorból):
`v1, fill, outline, 128.0, 1.0, KÖRVONAL, 1.0, SÚLY, unknown_b, 49152`.

⚠️ A **4., 6., 8. és 9.** mezőhöz nem nyúlunk — azok jelentése nyitva van
(#371, #2108). A valódi Picasa-sorok round-tripjének bájtra változatlannak
kell maradnia.
"""

from __future__ import annotations

import pytest

from picasapy.ini.text_overlay import TextStyle


class TestASulyAlapertekeNEM_felkover:
    def test_az_alapertelmezett_suly_400(self):
        """A #1994 az ÍRÁST javította; az osztály alapértéke maradt 700.

        Aki `TextStyle(fill_argb=…, outline_argb=…)`-t épít súly nélkül —
        például egy jövőbeli hívó —, ma némán félkövéret kapna."""
        stilus = TextStyle(fill_argb=0, outline_argb=0)
        assert stilus.weight == 400

    def test_a_felkover_tovabbra_is_700(self):
        assert TextStyle(fill_argb=0, outline_argb=0, weight=700).weight == 700


class TestAKorvonalvastagsagMezoje:
    """Az 5. mező (`unknown_a`) a körvonalvastagság — a kutatói kör
    kimérte, hogy a csúszka `[0, 1]` folytonos, tehát az érték
    ÁTSZÁMÍTÁS NÉLKÜL megy a mezőbe."""

    def test_az_alapertek_nulla_marad(self):
        """»Nincs körvonal« — ez az eredeti alapállapota is."""
        assert TextStyle(fill_argb=0, outline_argb=0).unknown_a == 0.0

    @pytest.mark.parametrize("ertek", [0.0, 0.25, 0.5, 1.0])
    def test_a_megadott_vastagsag_megmarad(self, ertek):
        stilus = TextStyle(fill_argb=0, outline_argb=0, unknown_a=ertek)
        assert stilus.unknown_a == pytest.approx(ertek)


class TestAmihezNEM_nyulunk:
    """A nyitott jelentésű mezők alapértéke változatlan (#371, #2108)."""

    def test_a_nyitott_mezok_valtozatlanok(self):
        s = TextStyle(fill_argb=0, outline_argb=0)
        assert s.constant_128 == 128.0
        assert s.constant_1a == 1.0
        assert s.constant_1b == 1.0
        assert s.unknown_b == 0
        assert s.trailer == 49152
        assert s.version == "v1"


class TestAKorvonalTENYLEG_kimegy_a_fajlba:
    """A jegy fő panasza: minden körvonal eltűnt mentés után.

    A mérce a KIÍRT sor, nem a szándék — ezért a nyilvános
    `serialize_text()`-en át mérünk, ugyanazon az úton, amin a mentés is
    megy.
    """

    def _sor(self, vastagsag: float) -> str:
        from picasapy.ini.text_overlay import (
            TextBlock,
            TextGeometry,
            TextOverlay,
            serialize_text,
        )

        blokk = TextBlock(
            content="proba",
            font="Arial",
            geometry=TextGeometry(x=0.5, y=0.5),
            style=TextStyle(
                fill_argb=1, outline_argb=2, unknown_a=vastagsag
            ),
        )
        return serialize_text(TextOverlay(blocks=(blokk,)))

    @pytest.mark.parametrize("vastagsag,vart", [(0.25, "0.250000"), (0.5, "0.500000")])
    def test_a_beallitott_vastagsag_a_kiirt_sorban_van(self, vastagsag, vart):
        assert vart in self._sor(vastagsag)

    def test_a_NULLA_tovabbra_is_nulla(self):
        """»Nincs körvonal« — az eredeti alapállapota."""
        assert "0.000000" in self._sor(0.0)

    def test_a_ket_kulonbozo_vastagsag_KULONBOZO_sort_ad(self):
        """Magvetés-védelem: ha az érték némán elveszne, a két sor egyezne."""
        assert self._sor(0.25) != self._sor(0.5)
