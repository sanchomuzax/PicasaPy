"""A nyomtatandó képek feloldásának és betöltésének témamixinje."""

from __future__ import annotations

from PySide6.QtGui import QImage
from collections.abc import Sequence
from pathlib import Path
from picasapy.index import PhotoRecord
from picasapy.ini.filters import parse_filters_prefix
from picasapy.lazy_cv2 import cv2
from picasapy.render import normalize_crop_ops
from picasapy.scanner import PICASA_INI_NAME
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS
from .print_controller_shared import _log


class PrintControllerSourceMixin:
    def _resolve_records(self, rows: Sequence[int]) -> list[PhotoRecord]:
        """A művelet bemenete — #1671: HA A TÁLCA NEM ÜRES, ŐK nyernek.

        A rács pillanatnyi kijelölése és a látott mappa ilyenkor nem
        számít: a tálca épp arra való, hogy több mappából gyűjtött képekkel
        lehessen dolgozni. Az eredeti súgója is így fogalmaz — *„Print
        photos in the Photo Tray"* —, és a mappába exportálás (#455) már
        régóta így viselkedik.

        Üres tálcánál (vagy `tray_source` nélkül) marad a régi, sor-alapú
        feloldás.

        #1401: az Útlevélkép kivágott képe (`setPassportSource`) mindkettőt
        megelőzi — a nyomtatási nézet ilyenkor EZT az egy képet nyomtatja."""
        if self._utlevel is not None:
            rekordok = [self._utlevel]
        else:
            talca = list(self._tray_source()) if self._tray_source is not None else []
            if talca:
                rekordok = talca
            else:
                photos = tuple(self._photo_source())
                rekordok = [photos[int(row)] for row in rows if 0 <= int(row) < len(photos)]
        if self._review_excluded_ids:
            rekordok = [
                rekord
                for rekord in rekordok
                if int(getattr(rekord, "id", -1)) not in self._review_excluded_ids
            ]
        return rekordok

    def _resolve_paths(self, rows: Sequence[int]) -> list[Path]:
        return [Path(record.folder_path) / record.name for record in self._resolve_records(rows)]

    def _render_photo(self, record: PhotoRecord) -> QImage:
        """A rácson látott szerkesztett fotó képpontjai QImage-ként (#4602)."""
        path = Path(record.folder_path) / record.name
        if getattr(record, "kind", "") == "video" or path.suffix.lower() in VIDEO_EXTENSIONS:
            return QImage()
        filters = getattr(record, "filters", None)
        ops = parse_filters_prefix(filters) if filters else ()
        crop, crop_ini_readable = (
            self._crop_reader.read(path.parent / PICASA_INI_NAME, path.name)
            if ops
            else (None, True)
        )
        ops = normalize_crop_ops(
            ops,
            crop,
            crop_ini_readable=crop_ini_readable,
            warning_key=str(path),
        )
        try:
            image = self._render_print_pixels(
                path,
                ops,
                rotate_steps=int(getattr(record, "rotate_steps", 0) or 0),
                flip_flags=int(getattr(record, "flip_flags", 0) or 0),
            )
        except (OSError, ValueError) as error:
            _log.warning("nyomtatás: nem dekódolható kép — kihagyva: %s (%s)", path, error)
            return QImage()

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        return QImage(
            rgb.data,
            width,
            height,
            int(rgb.strides[0]),
            QImage.Format.Format_RGB888,
        ).copy()

    def _is_printable(self, record: PhotoRecord) -> bool:
        """A teljes dekóderrel ellenőrzi, hogy nyomtatható-e a forrás."""
        path = Path(record.folder_path) / record.name
        if getattr(record, "kind", "") == "video" or path.suffix.lower() in VIDEO_EXTENSIONS:
            return False
        try:
            self._decode_print_image(path)
        except (OSError, ValueError) as error:
            _log.warning("nyomtatás: nem dekódolható kép — kihagyva: %s (%s)", path, error)
            return False
        return True
