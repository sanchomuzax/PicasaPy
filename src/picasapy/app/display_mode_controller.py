"""Megjelenítési mód (`Nézet ▸ Megjelenítési mód`) — az AppController szelete.

A `#1575` a menü **vázát** hozza: a tizenegy mód mint EGYETLEN kizáró
(rádió) csoport. Az egyes módok képpont-hatását külön jegyek adják
(#1576/#1577/#1578) — itt csak az van, hogy melyik mód aktív.

A bizonyíték: `docs/specs/picasa-megjelenitesi-modok.md` (a #1409
feltárása, `Picasa3.exe`). A három szerződés, amit ez a modul őriz:

* **Tizenegy tag, egyetlen kizáró csoport** (MÉRVE, `0x00575670`): a
  beállító a tizenegy parancsazonosító null-lezárt tömbjén megy végig, és
  `MF_CHECKED`-et pontosan egyre tesz. **Kapcsoló nincs köztük** — a
  „Túlcsordult képpontok" és a „Projektor mód" sem az, tehát nem
  kombinálhatók a gammákkal.
* **Az alapértelmezés az `Automatikus`** (MÉRVE, `0x0040bd90`).
* **Az érték SEHOL nem tárolódik** (MÉRVE: a beállító semmit nem ír):
  minden indulás alaphelyzetből kezd. Ezért ebben a modulban
  SZÁNDÉKOSAN nincs `QSettings` — a perzisztencia bevezetése eltérés
  volna az eredetitől, nem javítás.

⚠️ **A jelzés feltételes — ez nem kényelmi optimalizáció.** A menü
QML-oldalán a `checkable` + kötött `checked` minta a MÁR AKTÍV tételre
kattintva „rádió-csapdába" fut (#1464/#1468): a valódi kattintás
imperatívan átbillenti a `checked`-et, és ha a vezérlő nem jelez, a kötés
soha nem éled újra. A QML ezt a jelzés után VISSZAKÖTÉSSEL oldja meg. Ha
ez a beállító azonos értéknél is jelezne, a pipa a hibás QML mellett is
helyreállna, és a funkcionális teszt elveszítené a fogát — pontosan ez a
#1468 „őszinte címkével" ellátott gyengesége. Itt tehát a
`displayModeChanged` **csak valódi váltásnál** szól.
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

#: A tizenegy mód, a menü SORRENDJÉBEN (spec 1. szakasz). Az azonosítók a
#: bináris `ID_VIEW_*` parancsainak rövid, kisbetűs megfelelői.
#:
#: auto      ID_VIEW_AUTO       Automatikus (16 bites képernyőn szemcsézés)
#: normal    ID_VIEW_NORMAL     24 bites — nincs átalakító (alaphelyzet)
#: dither16  ID_VIEW_16         16 bites (szemcsézett)
#: rdesk     ID_VIEW_RDESK      Távoli asztal (3-3-3 bit)
#: lcd       ID_VIEW_LCD        LCD fehérpont (×246/256)
#: projector ID_VIEW_PROJECTOR  Projektor mód (×220/256)
#: overflow  ID_VIEW_OV         Túlcsordult képpontok megjelenítése
#: mac       ID_VIEW_MAC        Mac gamma (1.6)
#: linear    ID_VIEW_LINEAR     Lineáris gamma (2.2)
#: sepia     ID_VIEW_SEPIA      Szépia
#: bw        ID_VIEW_BW         Fekete-fehér
DISPLAY_MODES: tuple[str, ...] = (
    "auto",
    "normal",
    "dither16",
    "rdesk",
    "lcd",
    "projector",
    "overflow",
    "mac",
    "linear",
    "sepia",
    "bw",
)

#: A menü a tizenegy tételt KIÍRVA sorolja fel (így ismeri fel a #1468
#: forrásszintű őre kizáró csoportként), ezért a QML nem kér el listát —
#: `availableDisplayModes` property SZÁNDÉKOSAN nincs: bekötetlenül épp az
#: a szakadás volna, amit a `scripts/kepesseg_or.py` őriz.

#: Az alapértelmezés MÉRVE (`0x0040bd90`): `ID_VIEW_AUTO`. Linuxon ez —
#: 24 bites képernyőn — ugyanúgy no-op, mint a `normal`.
DEFAULT_DISPLAY_MODE = "auto"


class DisplayModeMixin:
    """`displayMode` — a tizenegy tagú kizáró csoport állapota (#1575)."""

    displayModeChanged = Signal()

    def _init_display_mode(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        __init__-et — ez a repó konvenciója, ld. `LanguageMixin`).

        Nincs beolvasás: az érték nem tárolódik el (ld. modul-docstring).
        """
        self._display_mode = DEFAULT_DISPLAY_MODE

    @Property(str, notify=displayModeChanged)
    def displayMode(self) -> str:
        """Az aktív megjelenítési mód azonosítója (`DISPLAY_MODES` egyike)."""
        return self._display_mode

    @Slot(str)
    def setDisplayMode(self, mode: str) -> None:
        """Mód beállítása; ismeretlen értéket kihagy, azonosnál NEM jelez.

        A „nem jelez" ága szándékos, ld. a modul-docstring figyelmeztetését.
        """
        if not isinstance(mode, str) or mode not in DISPLAY_MODES:
            return
        if mode == self._display_mode:
            return
        self._display_mode = mode
        self.displayModeChanged.emit()


def wire_display_mode(controller, edit_controller, preview_provider):
    """A mód ÁTVEZETÉSE a megjelenítési útra (#1576, #1596).

    Négy szereplő, egy irány:

    1. a vezérlő (`DisplayModeMixin`) tartja, melyik mód aktív,
    2. az edit-előnézet **szolgáltatója** teszi rá a hatást a KIADOTT képre
       (a tárolt képet érintetlenül hagyva, ld. ott a docstringet),
    3. az `EditController` lépteti a `previewSource` cache-busterét, hogy a
       QML tényleg újrakérje a képet,
    4. a **rács modellje** mód-cimkét tesz a bélyegkép-URL-ekre, és
       újraköti a látható cellákat (#1596).

    A 4. lépés nélkül a menü a KÖNYVTÁR RÁCSÁN semmit nem csinál: a 2–3.
    pont csak a nagy nézőt ellátó `editpreview` úton hat, a rács viszont a
    `thumbs` szolgáltatóból rajzol. Mérve (#1596): a rácson mind a
    tizenegy tétel képpontra azonos felvételt adott.

    A `wire_fileops()` mintájára KÜLÖN, nevesített bekötés: az
    `application.py` és a QML-funkcionális tesztek conftestjei ugyanezt az
    egy hívást használják, így a féloldalas tükrözés (a teszt-oldali
    bekötés elmaradása) nem tud észrevétlenül becsúszni.

    ⚠️ A rács modelljét SZÁNDÉKOSAN a vezérlőtől kérjük el, nem külön
    paraméterben. Új paraméter esetén minden hívóhelyet át kellene írni —
    és épp az a féloldalas tükrözés fenyegetne, ami ellen ez a függvény
    készült. Az `AppController.photos` mindig létezik; a `getattr` a
    #1575/#1576/#1577 vezérlő-csonkjai miatt van, amelyek csak a
    `DisplayModeMixin`-t példányosítják, rács nélkül.

    A kezdeti állapotot is átviszi — enélkül a szolgáltató a vezérlőtől
    eltérő módban indulna, amíg a felhasználó nem vált egyet.

    A visszaadott függvény a bekötött átvezető (a hívó életben tarthatja,
    illetve tesztből közvetlenül is meghívhatja).
    """
    photo_model = getattr(controller, "photos", None)

    def _atvezet() -> None:
        mode = controller.displayMode
        preview_provider.set_display_mode(mode)
        edit_controller.refresh_displayed_image()
        if photo_model is not None:
            photo_model.set_display_mode(mode)

    _atvezet()
    controller.displayModeChanged.connect(_atvezet)
    return _atvezet
