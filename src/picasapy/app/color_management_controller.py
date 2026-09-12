r"""`Nézet ▸ Színkezelés használata` — az AppController szelete (#1725).

A viselkedés MÉRVE az eredeti binárison
(`docs/specs/picasa-megjelenitesi-modok.md` 5.12):

* **Tárolás:** `Preferences\EnableColorManagement`, **alapérték 0 = ki**
  (`0x005c95bf`). Ezért ez a kapcsoló — a megjelenítési módokkal szemben —
  perzisztens: nálunk QSettings, a `view/` névtérben.
* **A kapu egyetlen bájt:** a kezelő (`0x005c95a0`) a színkezelés-objektum
  `+0x5c`-jébe ír, és mind a négy fogyasztó ezen a bájton áll vagy bukik
  (`0x00a3e3bd`, `0x00a3e591`) — kikapcsolva minden hívás no-op. Nálunk is
  EGY kapcsoló zárja a láncot, nem szórt feltételek.
* **A motor littleCMS** (`"not an ICC profile, invalid signature"`,
  `"cmsWhitePointFromTemp"`), tehát a hatás a beágyazott ICC-profil
  **szabványos** átalakítása. A mi oldalunkon ezt a Qt saját
  ICC-átalakítása adja (`QImage.convertToColorSpace`), nem becslés.
* **Bekapcsoláskor a szerkesztő-előnézet újraépül** (`editpanel/previewclip2`,
  `0x005c966a`) — ezt a `wire_color_management` végzi.

⚠️ Az `icc_camera_to_tone_matrix` (3×3) a **nyers kamerakép** külön útja; a
beszorzás helye nincs kimérve, ezért ez a modul nem is állít róla semmit.

⚠️ A jelzés **feltételes**: azonos értéknél nincs. A menü `checkable` +
kötött `checked` mintája a jelzés után VISSZAKÖTÉSSEL javítja magát, és ha
itt azonos értéknél is jeleznénk, a pipa a hibás QML mellett is helyreállna
— a funkcionális teszt elvesztené a fogát (#1468).
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

#: A QSettings-kulcs — a `view/` névtér a többi nézet-beállításé is
#: (darkTheme, folderSort, showHidden).
COLOR_MANAGEMENT_KEY = "view/colorManagement"

#: Igaznak számító mentett értékek (a QSettings platformonként bool-t vagy
#: szöveget ad vissza ugyanarra az írásra).
_TRUE_VALUES = ("true", "1")


def coerce_color_management_flag(value) -> bool:
    """A mentett beállítás bool-lá; minden ismeretlen érték = KI.

    Az eredeti alapértéke 0, tehát a hibás vagy kézzel átírt beállításból
    sem lehet bekapcsolt színkezelés.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return False


class ColorManagementMixin:
    """`colorManagement` kapcsoló — perzisztens, jelzéssel a QML-kötésnek."""

    colorManagementChanged = Signal()

    def _init_color_management(self) -> None:
        """Az AppController.__init__ hívja (a mixinek nem definiálnak saját
        __init__-et — ez a repó konvenciója, ld. `AppearanceMixin`)."""
        self._color_management = coerce_color_management_flag(
            self._get_settings().value(COLOR_MANAGEMENT_KEY)
        )

    @Property(bool, notify=colorManagementChanged)
    def colorManagement(self) -> bool:
        """Nézet → Színkezelés használata: érvényesüljön-e a beágyazott profil."""
        return self._color_management

    def setColorManagement(self, enabled: bool) -> None:
        """Beállítás; azonos értéknél nincs írás és nincs jelzés (ld. a
        modul-docstring figyelmeztetését).

        ⚠️ SZÁNDÉKOSAN **nem** `@Slot`: a felület a `toggleColorManagement`-et
        hívja, egy bekötetlen slot pedig a `scripts/kepesseg_or.py`
        alapállapotát hizlalná (az a lista csak rövidülhet). Python-oldali
        hívóknak (bekötés, tesztek) sima metódusként így is elérhető.
        """
        enabled = bool(enabled)
        if enabled == self._color_management:
            return
        self._color_management = enabled
        self._get_settings().setValue(
            COLOR_MANAGEMENT_KEY, "true" if enabled else "false"
        )
        self.colorManagementChanged.emit()

    @Slot()
    def toggleColorManagement(self) -> None:
        self.setColorManagement(not self._color_management)


def wire_color_management(controller, edit_controller, preview_provider):
    """A kapcsoló ÁTVEZETÉSE az előnézeti útra (a `wire_display_mode` mintája).

    Három szereplő, egy irány: a vezérlő tartja az állapotot, az előnézet
    szolgáltatója alkalmazza a beágyazott profilt a DEKÓDOLT forrásra, az
    `EditController` pedig lépteti a cache-busterét, hogy a QML tényleg
    újrakérje a képet — ez az eredeti „előnézet újraépítése" lépése
    (`0x005c966a`).

    A kezdeti állapotot is átviszi: enélkül a szolgáltató a vezérlőtől
    eltérő állapotban indulna, amíg a felhasználó nem vált egyet.

    A visszaadott függvény a bekötött átvezető (tesztből közvetlenül is
    hívható).
    """

    def _atvezet() -> None:
        preview_provider.set_color_management(controller.colorManagement)
        edit_controller.refresh_displayed_image()

    _atvezet()
    controller.colorManagementChanged.connect(_atvezet)
    return _atvezet
