"""A nyomtatásvezérlő beállításainak és nyomatopcióinak témamixinje."""

from __future__ import annotations

from PySide6.QtCore import Slot
from PySide6.QtGui import QFont, QFontDatabase
from picasapy.index import PhotoRecord
from picasapy.printing.dpi import NyomatMeret, alapmeretek_teruleti_mereshez
from picasapy.printing.layout import PageGeometry
from picasapy.printing.options import (
    BORDER_SIZE_MAX,
    PrintOptions,
    TEXT_SIZE_VALUES,
    load_print_options,
    save_print_options,
    update_print_option,
)
from .print_controller_shared import (
    _PICASA_PRINT_SIZE_IDS,
    _PRINT_OPTION_SIZES,
    _PRINT_SIZE_PRESET_KEYS,
)


class PrintControllerSettingsMixin:
    @Slot(result=list)
    def printSizePresets(self) -> list[str]:  # noqa: N802 — QML-stílus
        """A Nyomtatás fül öt, a panel gyorsgombjaihoz tartozó mérete.

        A rendszer területi mértékegysége adja az eredeti Picasa ötösének
        kezdőértékeit (#4435). A mentett PrintSize0–4 azonosítók felülírják
        ezeket; a bővebb PicasaPy-katalógus további méretei nem változnak.
        """
        sizes = set(_PRINT_OPTION_SIZES)
        result = []
        defaults = tuple(
            meret if isinstance(meret, str) else meret.name
            for meret in alapmeretek_teruleti_mereshez()
        )
        for key, default in zip(_PRINT_SIZE_PRESET_KEYS, defaults, strict=True):
            value = str(self._settings.value(key, default))
            result.append(value if value in sizes else default)
        return result

    @Slot(int, str)
    def setPrintSizePreset(self, index: int, name: str) -> None:  # noqa: N802
        """A kiválasztott gyorsgomb méretét azonnal elmenti."""
        sizes = set(_PRINT_OPTION_SIZES)
        if 0 <= int(index) < len(_PRINT_SIZE_PRESET_KEYS) and name in sizes:
            self._settings.setValue(_PRINT_SIZE_PRESET_KEYS[int(index)], name)

    @Slot(result=list)
    def printOptionSizes(self) -> list[str]:  # noqa: N802
        """Az `options.fen` 16 elemű méretlistája, FullPage nélkül (#5492)."""
        return list(_PRINT_OPTION_SIZES)

    @Slot(str, result=bool)
    def canUsePrintSizePreset(self, name: str) -> bool:  # noqa: N802
        """A méretgomb csak ismert méretet vagy Indexképek módot választhat.

        A CD-borító mérete a projekt specében nem kapott fizikai méretet,
        ezért a konfigurálható listában szerepel, de a gomb nem nyomtatható.
        """
        return name in NyomatMeret.__members__ or name == "CONTACT"

    @Slot(str, result=bool)
    def setPresetPrintSize(self, name: str) -> bool:  # noqa: N802
        """A Beállításokban kiosztott gyorsgomb méretét használja a nyomathoz."""
        if name not in NyomatMeret.__members__:
            return False
        self._meret_felulirva = NyomatMeret[name]
        return True

    @Slot(result=bool)
    def printProxyPreview(self) -> bool:  # noqa: N802
        """Igaz, ha az előnézet a gyorsabb, proxy felbontást használja."""
        value = self._settings.value("printing/proxyPreview", True)
        if isinstance(value, str):
            return value.strip().casefold() not in {"0", "false", "no", "off"}
        return bool(value)

    @Slot(bool)
    def setPrintProxyPreview(self, enabled: bool) -> None:  # noqa: N802
        self._settings.setValue("printing/proxyPreview", bool(enabled))

    @Slot(result=bool)
    def printerOptimized(self) -> bool:  # noqa: N802
        """A párbeszéd eredeti optimalizált módját olvassa vissza.

        A nyers pár külön kulcsot kap a PicasaPy saját `printerQuality`
        2/3-as előnézet-felbontási beállításától. Az eredeti állapotvizsgáló
        szerint az Optimalizált mód feltétele: `PrinterQuality != 1001` és
        `PrinterUseTiles != 0`.
        """
        try:
            quality = int(self._settings.value("printing/jobPrinterQuality", 2))
        except (TypeError, ValueError):
            quality = 2
        try:
            use_tiles = int(self._settings.value("printing/jobPrinterUseTiles", 0))
        except (TypeError, ValueError):
            use_tiles = 0
        return quality != 1001 and use_tiles != 0

    @Slot(bool)
    def setPrinterOptimized(self, optimized: bool) -> None:  # noqa: N802
        """Az eredeti Picasa nyers `PrinterQuality`/`PrinterUseTiles` párját menti."""
        self._settings.setValue("printing/jobPrinterQuality", 1 if optimized else 2)
        self._settings.setValue("printing/jobPrinterUseTiles", 1 if optimized else 0)

    def _printer_job_quality(self) -> int:
        """A nyomtatási feladat eredeti `PrinterQuality` értéke (1 vagy 2)."""
        try:
            quality = int(self._settings.value("printing/jobPrinterQuality", 2))
        except (TypeError, ValueError):
            return 2
        return quality if quality in {1, 2} else 2

    def _printer_job_output_scale(self) -> float:
        """A renderer 1/q koordinátaskálája (#5760).

        Az Optimalizált mód (`PrinterQuality=1`) teljes skálát ad. A Normál
        mód a Beállítások minőségét követi: 2 esetén 1/2, a 3-as „teljes
        felbontású” mód 1/1 marad, mert annak hatását a spec nyitva hagyja.
        A `PrinterUseTiles` a tárolt mód része, de a rajzoló út nem olvassa.
        """
        if self._printer_job_quality() == 1:
            return 1.0
        return 0.5 if self.printerQuality() == 2 else 1.0

    def _printer_output_scale(self) -> float:
        """Visszafelé kompatibilis név: a feladat szerinti skála."""
        return self._printer_job_output_scale()

    @Slot(result=int)
    def printerQuality(self) -> int:  # noqa: N802
        """Az eredeti `PrinterQuality` módja: 2 = kompatibilis, 3 = kiváló."""
        value = self._settings.value("printing/printerQuality", 2)
        if isinstance(value, str):
            regi_szoveges = {"compatible": 2, "highQuality": 3}
            if value in regi_szoveges:
                return regi_szoveges[value]
            try:
                value = int(value)
            except ValueError:
                return 2
        try:
            value = int(value)
        except (TypeError, ValueError):
            return 2
        return value if value in {2, 3} else 2

    @Slot(int)
    def setPrinterQuality(self, value: int | str) -> None:  # noqa: N802
        """A minőséget 2/3-ként menti, a régi szöveges hívókat is elfogadva."""
        if isinstance(value, str):
            value = {"compatible": 2, "highQuality": 3}.get(value, value)
        try:
            value = int(value)
        except (TypeError, ValueError):
            return
        if value in {2, 3}:
            self._settings.setValue("printing/printerQuality", value)

    @Slot(result=int)
    def printResamplerQuality(self) -> int:  # noqa: N802
        """Az eredeti `PrintResamplerQuality` értéke: 5 vagy 8.

        A régi PicasaPy-beállítás 3-as értéke ugyanazt a General rádiót
        jelenti, ezért olvasáskor 5-re normalizáljuk, íráskor viszont már
        csak az eredeti 5/8 értékeket mentjük.
        """
        try:
            value = int(self._settings.value("printing/resamplerQuality", 5))
        except (TypeError, ValueError):
            return 5
        if value in {3, 5}:
            return 5
        return 8 if value == 8 else 5

    @Slot(int)
    def setPrintResamplerQuality(self, value: int) -> None:  # noqa: N802
        if int(value) in {5, 8}:
            self._settings.setValue("printing/resamplerQuality", int(value))

    def _print_resampler_radius(self) -> int:
        """Az eredeti 5-ös beállítás Lanczos-3 szűrősugárra fordítása."""
        return 3 if self.printResamplerQuality() == 5 else 8

    def _alapmeret(self) -> NyomatMeret:
        """A nyomatkatalógus alapértelmezett mérete: **Teljes oldal** (#3733).

        A `docs/specs/picasa-nyomtatas.md` élő mérése (Colab EN 29/30,
        picasa-colab-jobs #55) szerint az eredeti nyomtatási nézet
        alapállása FullPage — a listában ez az utolsó tétel
        (`TELJES_OLDAL`), minden területi beállításban ugyanazzal az
        alapmérettel. Korábban itt a mért 4×6/10×15 cm állt, ami az
        eredetiben csak GOMB, nem alapállás."""
        return NyomatMeret.TELJES_OLDAL

    #: A QML-nek átadott eredeti `ytPrintSizes` azonosítók. A területi
    #: beállítás csak az öt gyorsgomb alapértékét választja, a katalógust nem.
    @Slot(result=list)
    def printSizes(self) -> list[str]:  # noqa: N802 — QML-stílus
        """A teljes, eredeti sorrendű `ytPrintSizes` katalógus (#5683)."""
        return list(_PICASA_PRINT_SIZE_IDS)

    @Slot(result=str)
    def printSize(self) -> str:  # noqa: N802 — QML-stílus
        """A megjegyzett nyomatméret (`PrintLastSize`), alapból Teljes oldal.

        #5683: a teljes katalógus mindkét területi rendszerben elérhető, így
        a mentett méretet a területi beállítás nem teszi listán kívülivé."""
        alap = self._alapmeret()
        tarolt = self._settings.value("print/lastSize", alap.name)
        nevek = set(NyomatMeret.__members__)
        return tarolt if tarolt in nevek else alap.name

    @Slot(str)
    def setPrintSize(self, nev: str) -> None:  # noqa: N802 — QML-stílus
        """A fizikai nyomatméret megjegyzése; a külön utak nem tartósak."""
        if nev in NyomatMeret.__members__:
            self._settings.setValue("print/lastSize", nev)
            self._meret_felulirva = None

    # -- Szegély- és felirat-opciók (#1780) -------------------------------

    @Slot(result="QVariantMap")
    def printOptions(self):  # noqa: N802 — QML-stílus
        """A 11 tartós printoptions-beállítás QML-kompatibilis térképe."""
        return load_print_options(self._settings).as_mapping()

    @Slot(result=list)
    def printTextSizes(self):  # noqa: N802 — QML-stílus
        """A binárisból mért 16 betűméret, sorrendben."""
        return list(TEXT_SIZE_VALUES)

    @Slot(result=list)
    def printFontFamilies(self):  # noqa: N802 — QML-stílus
        """A gép tényleges Qt-betűkészlete, az aktuális Arial-lal együtt."""
        aktualis = load_print_options(self._settings).textFont
        nevek = set(QFontDatabase.families())
        nevek.add(aktualis)
        return sorted(nevek, key=str.casefold)

    @Slot(str, "QVariant")
    def setPrintOption(self, nev: str, ertek) -> None:  # noqa: N802
        """Egy vezérlő azonnali mentése, mint az eredeti panelben.

        Az `Alkalmaz` ezért nem külön mentési pont: csak a már elmentett
        állapotból kéri újra az előnézetet. A validálás közös rétegben él,
        így QML-ből érkező hibás vagy határon túli érték nem kerül a tárba.
        """
        regi = load_print_options(self._settings)
        uj = update_print_option(regi, nev, ertek)
        if uj != regi:
            save_print_options(self._settings, uj)

    @Slot("QVariantMap")
    def restorePrintOptions(self, ertekek) -> None:  # noqa: N802
        """A `Mégse` által visszatöltött állapot explicit mentése."""
        regi = load_print_options(self._settings)
        uj = regi
        for nev, ertek in dict(ertekek or {}).items():
            uj = update_print_option(uj, str(nev), ertek)
        save_print_options(self._settings, uj)

    def _print_options(self) -> PrintOptions:
        """A renderelő mindig a tartós, legfrissebb állapotot olvassa."""
        return load_print_options(self._settings)

    @staticmethod
    def _caption_text(record: PhotoRecord, options: PrintOptions) -> str:
        """A négy mért feliratforrásból előálló szöveg."""
        if options.textSource == 0:
            return ""
        if options.textSource == 1:
            return str(getattr(record, "caption", None) or "")
        if options.textSource == 2:
            return str(getattr(record, "name", ""))
        taken = str(getattr(record, "taken_at", None) or "").strip()
        width = getattr(record, "width", None)
        height = getattr(record, "height", None)
        reszletek = [darab for darab in (taken,) if darab]
        if width and height:
            reszletek.append(f"{width} × {height}")
        return " · ".join(reszletek) or str(getattr(record, "name", ""))

    @staticmethod
    def _font_for_print(options: PrintOptions, dpi: float) -> QFont:
        font = QFont(options.textFont or "Arial")
        font.setPixelSize(max(1, round(options.textSize * dpi / 72.0)))
        return font

    @staticmethod
    def _border_width(options: PrintOptions, page: PageGeometry) -> float:
        """A tárolt 0..1024 skálát a nyomtatható területre vetíti.

        A bináris a tárolási skálát méri; a renderer képpontos végső
        ecsetméretét nem adja át dokumentált konstansként. Ez az explicit,
        determinisztikus terméki leképezés a PDF és az előnézet között közös:
        nulla nincs, a maximum pedig a rövidebb nyomtatható oldal.
        """
        if options.borderSize <= 0:
            return 0.0
        return min(
            min(page.printable_width, page.printable_height),
            max(
                1.0,
                min(page.printable_width, page.printable_height)
                * options.borderSize
                / BORDER_SIZE_MAX,
            ),
        )
