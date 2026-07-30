"""Nyelvválasztás (#333) — az AppController vezérlő-szelete.

A fordítás szabványos Qt-úton megy (`.ts` → `.qm` + `QTranslator`); ez a
modul csak azt dönti el, MELYIK nyelvet töltse be az alkalmazás.

A felhasználó döntése szerint az **alapértelmezés az angol**, és a magyar
választható mellé — a korábbi viselkedés (a rendszer nyelve dönt) magyar
Windowson nem engedett angolra váltani. A választás a QSettings-ben él, így
a következő induláskor visszaáll.

Hibás vagy kézzel átírt beállításból SOSEM lesz elérhetetlen felület: az
ismeretlen érték az alapértelmezésre esik vissza (az appearance_controller
„értelmetlen mentés = alapértelmezés" elvének mintájára).
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

#: A QSettings-kulcs — a `general/` névtér az alkalmazás-szintű beállításoké.
LANGUAGE_KEY = "general/language"

#: Az alapértelmezett nyelv. A felhasználó kifejezett kérése (#333).
DEFAULT_LANGUAGE = "en"

#: A választható nyelvek. Új nyelv felvételéhez elég ide beírni a kódot és
#: a `picasapy_<kód>.qm`-et a `i18n/` mappába tenni.
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "hu")


def coerce_language(value) -> str:
    """A mentett/kapott érték nyelvkóddá alakítása, ismeretlennél az
    alapértelmezéssel.

    A nyelvi VÁLTOZATOKAT felismeri (`hu_HU` → `hu`), mert a `QLocale.name()`
    ilyen alakot ad — így a korábbi, rendszer-nyelvből mentett érték is
    értelmes marad.
    """
    if not isinstance(value, str):
        return DEFAULT_LANGUAGE
    code = value.strip().replace("-", "_").split("_")[0].lower()
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


class LanguageMixin:
    """`language` beállítás — perzisztens, jelzéssel a felület újrafordításához."""

    languageChanged = Signal()

    def _init_language(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        __init__-et — ez a repó konvenciója, ld. AppearanceMixin)."""
        self._language = coerce_language(self._get_settings().value(LANGUAGE_KEY))

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        """A felület nyelve: `en` vagy `hu`."""
        return self._language

    @Property(list, notify=languageChanged)
    def availableLanguages(self):
        """A választható nyelvek a menünek (listát adunk, nem tuple-t: a
        QML-oldalon a tuple NEM tömb, #232)."""
        return list(SUPPORTED_LANGUAGES)

    @Slot(str)
    def setLanguage(self, code: str) -> None:
        """Nyelv beállítása; ismeretlen kódot kihagy, azonos értéknél nem jelez.

        A tényleges fordító-cserét az alkalmazás végzi a `languageChanged`
        jelzésre (application.py) — a vezérlő csak a döntést tárolja.
        """
        if not isinstance(code, str):
            return
        normalised = code.strip().replace("-", "_").split("_")[0].lower()
        if normalised not in SUPPORTED_LANGUAGES:
            return
        if normalised == self._language:
            return
        self._language = normalised
        self._get_settings().setValue(LANGUAGE_KEY, normalised)
        self.languageChanged.emit()
