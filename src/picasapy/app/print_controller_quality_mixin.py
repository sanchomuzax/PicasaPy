"""A nyomtatási minőség és a képfelülvizsgálat témamixinje."""

from __future__ import annotations

from PySide6.QtCore import Slot
from picasapy.printing.dpi import (
    JO_MINOSEGI_KUSZOB_DPI,
    KICSI_KUSZOB_DPI,
    NyomatMeret,
    effektiv_dpi,
    minoseg_osszegzes,
    nyomtatasi_minoseg_kod,
)


class PrintControllerQualityMixin:
    @Slot(list, str, result="QVariantMap")
    def printQuality(self, rows, size_name: str):  # noqa: N802 — QML-stílus
        """A kijelölés minőség-összegzése a választott nyomatmérethez.

        #1782: eddig egy 640×480-as képet 8×10-re lehetett nyomtatni úgy,
        hogy a program egy szót sem szólt. A `smallest`/`small`/`ready`
        mezőkből a QML állítja össze az eredeti mondatait
        (`ThumbUIPrint::Smallest`, `::ReviewPrompt`).

        Az ISMERETLEN méretű kép kicsinek számít — ha nem tudjuk, mekkora,
        ne nyugtassuk meg a felhasználót."""
        meret = NyomatMeret.__members__.get(size_name) or self._alapmeret()
        meretek = [
            (rekord.width or 0, rekord.height or 0) for rekord in self._resolve_records(rows)
        ]
        best_kuszob = self._dpi_kuszob()
        good_kuszob = self._dpi_jo_kuszob()
        osszegzes = minoseg_osszegzes(meretek, meret, kuszob=best_kuszob)
        return {
            "smallest": osszegzes.legkisebb_dpi,
            "small": osszegzes.kicsik,
            "total": osszegzes.osszes,
            "ready": osszegzes.keszen_all,
            # `threshold` marad a #4275 figyelmeztető panel szerződése.
            "threshold": best_kuszob,
            "bestThreshold": best_kuszob,
            "goodThreshold": good_kuszob,
        }

    def smallPictures(self, rows, size_name: str):  # noqa: N802 — QML-stílus
        """A küszöb alatti képek NÉV szerint, a hozzájuk tartozó DPI-vel.

        #1953: eddig a párbeszéd kimondta, hogy *van* kis felbontású kép,
        de nem mondta meg, **melyik**. Az eredetiben erre való az
        „Ellenőrzés" gomb (`printpanel/reviewnowbutton`).

        A számítás UGYANAZ, mint az összegzésé (`effektiv_dpi` +
        `KICSI_KUSZOB_DPI`) — ha a két út külön számolna, előbb-utóbb
        ellentmondanának: a mondat N kis képet írna, a lista M-et mutatna.

        A lista a **legrosszabbal kezdődik**: a felhasználót az érdekli
        először. Az ismeretlen méretű kép ugyanúgy kicsinek számít, mint
        az összegzésben — 0 DPI-vel."""
        kuszob = self._dpi_kuszob()
        return [
            item for item in self._quality_picture_rows(rows, size_name) if item["dpi"] < kuszob
        ]

    @Slot(list, str, result=list)
    def reviewPictures(self, rows, size_name: str):  # noqa: N802
        """Minden nyomtatandó kép DPI-je és az eredeti 0/1/2 minőségi kódja.

        A figyelmeztető panel a teljes listát mutatja, hogy a Best és Good
        képek se tűnjenek el az ellenőrzésből. A sorok a legrosszabb DPI-től
        indulnak, a kód pedig a bináris két küszöbtesztjének összege.
        """
        return self._quality_picture_rows(rows, size_name)

    def _quality_picture_rows(self, rows, size_name: str) -> list[dict]:
        """A közös soradat a teljes Review listához és a kis-kép szűréshez."""
        meret = NyomatMeret.__members__.get(size_name) or self._alapmeret()
        best_kuszob = self._dpi_kuszob()
        good_kuszob = self._dpi_jo_kuszob()
        van_talca = (
            self._utlevel is None and self._tray_source is not None and bool(self._tray_source())
        )
        tetelek = []
        for index, rekord in enumerate(self._resolve_records(rows)):
            dpi = effektiv_dpi(rekord.width or 0, rekord.height or 0, meret)
            tetelek.append(
                {
                    "row": (
                        int(rows[index])
                        if not van_talca and self._utlevel is None and index < len(rows)
                        else -1
                    ),
                    "recordId": int(getattr(rekord, "id", -1)),
                    "name": rekord.name,
                    "dpi": dpi,
                    "qualityCode": nyomtatasi_minoseg_kod(
                        dpi,
                        best_kuszob=best_kuszob,
                        good_kuszob=good_kuszob,
                    ),
                }
            )
        return sorted(tetelek, key=lambda item: item["dpi"])

    @Slot(list)
    def excludeReviewPictures(self, record_ids) -> None:  # noqa: N802 — QML-stílus
        """#4275: rácssor nélküli (tálca/útlevél) képek kizárása."""
        self._review_excluded_ids.update(int(record_id) for record_id in record_ids)

    @Slot()
    def clearReviewExclusions(self) -> None:  # noqa: N802 — QML-stílus
        """Új nyomtatási párbeszéd előtt az előző felülvizsgálat ürítése."""
        self._review_excluded_ids.clear()

    #: A küszöb beállítás-kulcsa. Az eredetiben `Preferences\DPIWarning`
    #: (`0x0085c076`/`0x0085c07b`), alapértéke **150** (`0x0085c08b`).
    _DPI_KUSZOB_KULCS = "printing/dpiWarning"
    #: A Best/Good határ kulcsa az eredetiben `Preferences\DPISevere`,
    #: alapértéke **100** (`0x0085c28a`).
    _DPI_JO_KUSZOB_KULCS = "printing/dpiSevere"

    def _dpi_kuszob(self) -> int:
        """A „kis kép" küszöbe — beállításból, `KICSI_KUSZOB_DPI` alapértékkel.

        ⚠️ MINDKÉT út (az összegzés és a kifogásolt lista) ezt hívja. Ha
        külön olvasnák, a mondat N kis képet írna, a lista M-et — a #1953
        épp ezt az ellentmondást szüntette meg.

        Elrontott (nem szám vagy nem pozitív) beállításnál az alapértékre
        esünk vissza: a nyomtatás-előkészítés nem dőlhet be egy rossz
        kulcstól.
        """
        try:
            ertek = int(self._settings.value(self._DPI_KUSZOB_KULCS, KICSI_KUSZOB_DPI))
        except (TypeError, ValueError):
            return KICSI_KUSZOB_DPI
        return ertek if ertek > 0 else KICSI_KUSZOB_DPI

    def _dpi_jo_kuszob(self) -> int:
        """A Good/Bad küszöb beállításból, 100 DPI alapértékkel."""
        try:
            ertek = int(self._settings.value(self._DPI_JO_KUSZOB_KULCS, JO_MINOSEGI_KUSZOB_DPI))
        except (TypeError, ValueError):
            return JO_MINOSEGI_KUSZOB_DPI
        return ertek if ertek > 0 else JO_MINOSEGI_KUSZOB_DPI
