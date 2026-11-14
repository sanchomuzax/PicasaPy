"""`image://slideshowlabelcard/<fájl>?name=...` szolgáltató (#6920)."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs, unquote

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QImageReader, QTransform
from PySide6.QtQuick import QQuickImageProvider

from .slideshow_label_card import create_slideshow_label_card


_log = logging.getLogger(__name__)


def _keresd_szet(azonosito: str) -> tuple[str, str, int, int, int]:
    kodolt_ut, _, lekerdezes = azonosito.partition("?")
    parameterek = parse_qs(lekerdezes)

    def _egesz(kulcs: str, alap: int = 0) -> int:
        try:
            return int(parameterek.get(kulcs, [alap])[0])
        except (TypeError, ValueError):
            return alap

    nev = parameterek.get("name", [""])[0]
    return (
        unquote(kodolt_ut),
        nev,
        _egesz("rotation") % 4,
        _egesz("viewWidth"),
        _egesz("viewHeight"),
    )


class SlideshowLabelCardProvider(QQuickImageProvider):
    """Az első fotóból állítja elő a QML kimenő címkártyáját."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, id: str, size, requestedSize) -> QImage:  # noqa: A002
        path, name, rotation, view_width, view_height = _keresd_szet(id)
        if not path:
            return QImage()

        reader = QImageReader(path)
        reader.setAutoTransform(True)
        source = reader.read()
        if source.isNull():
            _log.warning("az Időrend címkártya-képe nem tölthető be: %s", path)
            return QImage()
        if rotation:
            source = source.transformed(
                QTransform().rotate(rotation * 90),
                Qt.TransformationMode.SmoothTransformation,
            )

        display_scale = 1.0
        if view_width > 0 and view_height > 0:
            display_scale = min(
                view_width / source.width(), view_height / source.height()
            )
        card = create_slideshow_label_card(
            source, name, display_scale=display_scale
        )

        if (
            requestedSize is not None
            and requestedSize.width() > 0
            and requestedSize.height() > 0
            and (
                card.width() > requestedSize.width()
                or card.height() > requestedSize.height()
            )
        ):
            card = card.scaled(
                requestedSize,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        if size is not None:
            size.setWidth(card.width())
            size.setHeight(card.height())
        return card
