"""Nyelvválasztás (#333, #3555) — az AppController vezérlő-szelete.

A fordítás szabványos Qt-úton megy (`.ts` → `.qm` + `QTranslator`); ez a
modul csak azt dönti el, MELYIK nyelvet töltse be az alkalmazás.

#3555 (a #3553 kutatása alapján): az eredeti Picasa a nyelvváltást a
program KÖVETKEZŐ indításáig halasztja — a felhasználó a Beállítások OK-
jára csak egy MEGERŐSÍTŐ kérdést kap, a futó felület nyelve nem vált.
Nálunk a Beállítások ablaknak nincs OK-ja (minden vezérlő azonnal ír), ezért
a kérdés a tétel KIVÁLASZTÁSAKOR jön — a legördülőben és az Eszközök → Nyelv
menüben egyaránt; a szöveg és a két ág az eredetié. Ezért a tárolt állapot
KÉT részre válik:

* `language` — az EBBEN a futásban érvényes, ténylegesen betöltött nyelv
  (`general/language` kulcs, mint eddig);
* `pendingLanguage` — a felhasználó által kiválasztott, a KÖVETKEZŐ
  indításra váró érték (`general/language_pending` kulcs). Ez lehet a
  `SYSTEM_LANGUAGE_CODE` álkód is — ekkor minden induláskor újra a
  rendszer nyelvéből dől el, melyik konkrét nyelv legyen az érvényes.

A `setLanguage` ezért CSAK a `pendingLanguage`-et írja, és nem vált
fordítót — a QML oldal a döntés előtt megerősítő kérdést tesz fel (a
kattintás önmagában nem elég), és a tényleges betöltést a következő
indítás `resolve_startup_language`-hívása végzi.

Hibás vagy kézzel átírt beállításból SOSEM lesz elérhetetlen felület: az
ismeretlen érték az alapértelmezésre esik vissza (az appearance_controller
„értelmetlen mentés = alapértelmezés" elvének mintájára).
"""

from __future__ import annotations

from PySide6.QtCore import Property, QLocale, Signal, Slot

#: A QSettings-kulcs — a `general/` névtér az alkalmazás-szintű beállításoké.
LANGUAGE_KEY = "general/language"

#: A KÖVETKEZŐ indításra kért, még nem alkalmazott választás (#3555). Lehet
#: konkrét nyelvkód, vagy a `SYSTEM_LANGUAGE_CODE` álkód.
PENDING_LANGUAGE_KEY = "general/language_pending"

#: Az alapértelmezett nyelv. A felhasználó kifejezett kérése (#333).
DEFAULT_LANGUAGE = "en"

#: A választható nyelvek, a spec sorrendjében (`docs/specs/
#: picasa-fo-ablak-elrendezes.md`, „A nyelvválasztó" szakasz — a teljes,
#: 41 nyelves `langnames.xml` sorrendből csak azok, amelyekhez ma van
#: szótárunk). Új nyelv felvételéhez elég ide beírni a kódot (a helyére, a
#: spec-sorrend szerint) és a `picasapy_<kód>.qm`-et az `i18n/` mappába tenni.
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "hu")

#: A nyelvek SAJÁT nyelvükön írt neve (`langnames.xml` mintájára) — ez a
#: lista FÜGGETLEN a felület aktuális nyelvétől, ezért NEM qsTr-ezett. A mi
#: `en` kódunk az eredeti `Lang::enUS` tétele (spec A, 6. sor), a felirata
#: ezért a hivatalos „English (US)” (őre: `test_hivatalos_feliratok_3358`).
OWN_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English (US)",
    "hu": "Magyar",
}

#: A „rendszer szerinti” tétel álkódja — a legördülő/menü első tétele
#: (spec A) szakasz), minden induláskor újra feloldva.
SYSTEM_LANGUAGE_CODE = "system"


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


def _normalise_pending(value) -> str | None:
    """A `setLanguage`/tárolt `pending` érték normalizálása.

    A `SYSTEM_LANGUAGE_CODE`-ot változatlanul átengedi (nem nyelvkód, nem
    esik a `coerce_language` alá); minden más a támogatott nyelvek közül
    kell legyen, különben `None` (a hívó eldönti, mi a teendő ismeretlennel).
    """
    if not isinstance(value, str):
        return None
    if value == SYSTEM_LANGUAGE_CODE:
        return SYSTEM_LANGUAGE_CODE
    code = value.strip().replace("-", "_").split("_")[0].lower()
    return code if code in SUPPORTED_LANGUAGES else None


def resolve_system_language() -> str:
    """A rendszer nyelve a mi nyelvkódjaink közül — ismeretlennél az
    alapértelmezés (a `SYSTEM_LANGUAGE_CODE` választás induláskori feloldása).
    """
    code = QLocale.system().name().split("_")[0].lower()
    return code if code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


#: Az országkód tartaléka (spec B: `0x0098d607`–`0x0098d670`).
_FALLBACK_COUNTRY = "US"


def format_system_suffix(language: str, country: str) -> str:
    """A „rendszer szerinti” tétel felirat-utótagja (spec B szakasz).

    `xx-YY`; hiányzó, számjegyes vagy háromnál hosszabb országkódnál az
    ország `US`. Ha a nyelvkód már az országkódra végződik, csak a nyelvkód.
    Ez utóbbi próba az eredetiben (`0x00987150`) kis-nagybetű-ÉRZÉKENY — a
    spec példája „(hu-HU)”, nem „(hu)” —, ezért a szokásos kisbetűs nyelv- és
    nagybetűs országkód-párnál nem teljesül; szándékosan így vesszük át.

    A nem ISO nyelvkód (pl. a POSIX „C” locale-é) az alapnyelvre esik — a
    `resolve_system_language` is ezt választja ilyenkor.
    """
    letters = language.replace("-", "")
    if len(letters) < 2 or not (letters.isascii() and letters.isalpha()):
        language = DEFAULT_LANGUAGE
    if not country or len(country) > 3 or not country.isalpha():
        country = _FALLBACK_COUNTRY
    if language.endswith(country):
        return language
    return f"{language}-{country}"


def system_language_suffix() -> str:
    """A gép területi beállításának utótagja, ld. `format_system_suffix`."""
    locale = QLocale.system()
    return format_system_suffix(
        QLocale.languageToCode(locale.language()),
        QLocale.territoryToCode(locale.territory()),
    )


def resolve_startup_language(settings) -> str:
    """A `pending` választás beérése induláskor — a #3555 három lépése
    (OK ⇒ pending, kilépés ⇒ megmarad, indítás ⇒ alkalmaz) egyetlen
    idempotens hívásban: akárhányszor és akárhonnan hívható egy induláson
    belül (előbb az alkalmazás-indító a fordító betöltése előtt, utána az
    `AppController` is), a második hívás már nem változtat semmit.

    Visszaadja az EBBEN a futásban érvényes (konkrét) nyelvkódot, és
    ezt írja a `LANGUAGE_KEY` alá is.
    """
    current = coerce_language(settings.value(LANGUAGE_KEY))
    pending_raw = _normalise_pending(settings.value(PENDING_LANGUAGE_KEY))
    if pending_raw is None:
        pending_raw = current
    resolved = (
        resolve_system_language() if pending_raw == SYSTEM_LANGUAGE_CODE else pending_raw
    )
    settings.setValue(LANGUAGE_KEY, resolved)
    settings.setValue(PENDING_LANGUAGE_KEY, pending_raw)
    return resolved


class LanguageMixin:
    """`language`/`pendingLanguage` beállítás — perzisztens, jelzéssel a
    Beállítások és az Eszközök → Nyelv menü frissítéséhez."""

    languageChanged = Signal()
    pendingLanguageChanged = Signal()

    def _init_language(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        __init__-et — ez a repó konvenciója, ld. AppearanceMixin)."""
        settings = self._get_settings()
        self._language = resolve_startup_language(settings)
        pending_raw = _normalise_pending(settings.value(PENDING_LANGUAGE_KEY))
        self._pending_language = pending_raw if pending_raw is not None else self._language

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        """Az EBBEN a futásban érvényes felület-nyelv: `en` vagy `hu`.

        #3555 óta ez a fordító-betöltés után NEM változik a futás alatt —
        a váltás csak a következő indításkor lép életbe."""
        return self._language

    @Property(str, notify=pendingLanguageChanged)
    def pendingLanguage(self) -> str:
        """A KÖVETKEZŐ indításra kért választás — konkrét nyelvkód, vagy a
        `systemLanguageCode` (a legördülő/menü kijelölése ezt tükrözi,
        nem a jelenleg érvényes `language`-t, ld. spec D) szakasz)."""
        return self._pending_language

    @Property(str, constant=True)
    def systemLanguageCode(self) -> str:
        """A „rendszer szerinti” tétel álkódja — QML-nek, hogy ne
        duplikálja a sztringet."""
        return SYSTEM_LANGUAGE_CODE

    @Property(str, constant=True)
    def systemLanguageSuffix(self) -> str:
        """A rendszer-tétel felirat-utótagja, pl. `hu-HU` (spec B) szakasz).

        A gépi locale a futás alatt nem változik, ezért elég egyszer
        kiszámítani."""
        return system_language_suffix()

    @Property(list, notify=languageChanged)
    def availableLanguages(self):
        """A választható KONKRÉT nyelvek a menünek/legördülőnek, a spec
        sorrendjében — a „rendszer szerinti” tételt a QML teszi elé (listát
        adunk, nem tuple-t: a QML-oldalon a tuple NEM tömb, #232)."""
        return list(SUPPORTED_LANGUAGES)

    @Slot(str, result=str)
    def ownLanguageName(self, code: str) -> str:
        """A `code` SAJÁT nyelvén írt neve — a felület nyelvétől függetlenül
        (spec B) szakasz: a lista a `langnames.xml` neveit mutatja, bármi a
        felület nyelve)."""
        return OWN_LANGUAGE_NAMES.get(code, code)

    @Slot(str)
    def setLanguage(self, code: str) -> None:
        """A KÖVETKEZŐ indításra kért nyelv beállítása; ismeretlen kódot
        kihagy, azonos értéknél nem jelez.

        Ez NEM vált fordítót — a hívó (QML) a megerősítő kérdés UTÁN hívja
        csak, és az érvénybe lépés a következő indításkor történik
        (`resolve_startup_language`)."""
        normalised = _normalise_pending(code)
        if normalised is None:
            return
        if normalised == self._pending_language:
            return
        self._pending_language = normalised
        self._get_settings().setValue(PENDING_LANGUAGE_KEY, normalised)
        self.pendingLanguageChanged.emit()
