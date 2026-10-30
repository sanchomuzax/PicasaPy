"""Az effektlánc állapota: régi és egygombos effektek listái, darabszámok, eszközjelzők (#6267)."""

from __future__ import annotations

from .edit_controller_shared import (
    DEAD_LEGACY_OPS,
    LEGACY_EFFECTS,
    LEGACY_EFFECT_KEYS,
    Property,
    QCoreApplication,
    can_offer_filter_control,
    one_click_keys,
)
from .edit_controller_signals import EditControllerSignalsMixin as _Signals


class EditControllerEffectsStateMixin:
    """Az effektlánc állapot-tulajdonságai (#6267)."""

    @Property("QVariant", constant=True)
    def legacyEffects(self):
        """Az „Régi effektek" fül gombjai (#571) — a katalógusból, nem
        kézzel a QML-be írva.

        Minden elem: `key` (belső szűrőnév), `label` (angol felirat, a
        fordítás a szokásos `.ts` úton), `enabled` (van-e VALÓDI vizuális
        modellünk — a renderelő dönti el), `dead` (halott legacy név, #567:
        a Picasa natív regiszterében sincs hozzá feldolgozó).
        """
        return [
            {
                "key": effect.key,
                # a felirat MÁR fordítva megy a QML-nek: a katalógus adat,
                # nem forráskód, ezért `qsTr()` nem tudná kigyűjteni —
                # a `.ts`-ben a "LegacyEffects" kontextus tartja őket
                "label": QCoreApplication.translate("LegacyEffects", effect.label),
                "enabled": can_offer_filter_control(effect.key),
                "dead": effect.key in DEAD_LEGACY_OPS,
            }
            for effect in LEGACY_EFFECTS
        ]


    @Property("QVariant", notify=_Signals.revisionChanged)
    def legacyEffectsInChain(self):
        """A szerkesztési láncban szereplő ÖRÖKÖLT szűrőnevek (#571).

        Ebből teszi ki a szerkesztő az „Régi effektek" fülre a jelzést: a
        felhasználó egy régi képen ott találhat olyan effektet, amit a mai
        Picasa felülete nem is mutat — tudnia kell, hol nézze meg."""
        names = {op.name.casefold() for op in self._session.ops}
        return sorted(names & LEGACY_EFFECT_KEYS)


    @Property("QVariant", constant=True)
    def oneClickEffects(self):
        """#2126: a `mode="oneclick"` szűrők kulcsai — a kék jelvényhez.

        ÁLLANDÓ: a mód a szűrő-leíró tulajdonsága, nem a munkamenet
        állapota, ezért `constant=True` (a felületnek nem kell újraszámolnia
        minden lánc-módosításnál). A forrás egyetlen helyen van:
        `render.registry.one_click_keys()`.
        """
        return list(one_click_keys())


    @Property("QVariant", notify=_Signals.revisionChanged)
    def effectChainCounts(self):
        """Melyik szűrő HÁNYSZOR szerepel a szerkesztési láncban (#704).

        Ebből teszi ki a szerkesztő az „alkalmazva" jelvényt a csempékre: a
        felhasználó a rácsról ma egyáltalán nem tudja megállapítani, mely
        effektek vannak már a képen. Ez nem díszítés, hanem a szerkesztő
        egyik alapvető visszajelzése.

        DARABSZÁM, nem lánc-pozíció: a bejelentő képernyőképén az eredeti
        Picasa a Sepia és a Warmify csempéjén EGYARÁNT `1`-et mutat, holott
        a láncban a kettő nem lehet ugyanazon a helyen — vagyis a szám az
        adott szűrő előfordulásainak száma.

        A kulcsok a szűrőnév kisbetűs (casefold) alakjai, ahogy a QML-oldal
        is küldi őket (`effectRequested`, `applyEffectWithParams`).
        """
        counts: dict[str, int] = {}
        for op in self._session.ops:
            key = op.name.casefold()
            counts[key] = counts.get(key, 0) + 1
        return counts


    @Property(str, notify=_Signals.revisionChanged)
    def effectChain(self) -> str:
        """A szerkesztési lánc sorosított értéke az effekt-csempe előnézetéhez.

        A képszolgáltató könyvtárrekordja a szerkesztés megnyitásakor készült,
        ezért az aktuális láncot a csempe URL-jén kell átadni. A revíziójel
        minden sikeres láncmódosításkor újraköti ezt az értéket.
        """
        return self._session.to_value()


    @Property(bool, notify=_Signals.toolsChanged)
    def enhanceEnabled(self) -> bool:
        return not self._session.last_is("enhance")


    @Property(bool, notify=_Signals.toolsChanged)
    def autolightEnabled(self) -> bool:
        return not self._session.last_is("autolight")


    @Property(bool, notify=_Signals.toolsChanged)
    def autocolorEnabled(self) -> bool:
        return not self._session.last_is("autocolor")
