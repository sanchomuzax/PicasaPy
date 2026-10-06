"""A felvételi dátum kijelöléses módosítása (#4332).

Az eredeti tárolási cél nem bizonyított. A PicasaPy ezért tartós felülírást
tesz a SQLite-indexbe; a forráskép és a .picasa.ini változatlan marad.
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Slot

def _photo_datetime(photo) -> datetime:
    """A jelenlegi felvételi idő, az indexelt fájlidőre visszaesve."""
    if photo.taken_at:
        return datetime.fromisoformat(photo.taken_at)
    return datetime.fromtimestamp(photo.sort_mtime_ns / 1_000_000_000)


def _iso_datetime(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat(timespec="seconds")


class TimestampAdjustmentMixin:
    """A PhotoOpsMixin háttéríró útját használó indexművelet."""

    @Slot(int, result="QVariantMap")
    def adjustTimestampPreview(self, row: int) -> dict[str, str]:
        photos = self._photos.photos
        if not 0 <= int(row) < len(photos):
            return {"dateTime": "", "thumbnailUrl": ""}
        photo = photos[int(row)]
        return {
            "dateTime": _photo_datetime(photo).strftime("%Y-%m-%d %H:%M:%S"),
            "thumbnailUrl": f"image://thumbs/{photo.id}",
        }

    @Slot(list, str, str, bool, result=bool)
    def adjustPhotoDates(
        self, rows: list, current_date: str, new_date: str, relative: bool
    ) -> bool:
        """Írja a dátumfelülírást a kijelölt indexrekordokba.

        Relatív módban az első kép régi és új dátuma közti eltérést adja
        hozzá minden kijelölt kép saját idejéhez. Abszolút módban minden
        rekord ugyanazt az időt kapja.
        """
        photos = self._rows_to_photos(rows)
        if not photos:
            return False
        try:
            displayed_current = datetime.fromisoformat(current_date.strip())
            target = datetime.fromisoformat(new_date.strip())
            delta = target - displayed_current
            updates = [
                (
                    photo.id,
                    _iso_datetime(_photo_datetime(photo) + delta)
                    if relative
                    else _iso_datetime(target),
                )
                for photo in photos
            ]
        except (TypeError, ValueError, OverflowError):
            return False

        self._ensure_photo_ops_wired()
        jobs = [
            (
                photo_id,
                lambda value=value: {"taken_at_override": value},
            )
            for photo_id, value in updates
        ]
        # A végső lekérdezés újraszámolja az aktív dátum szerinti rácssorrendet.
        self._run_photo_writes(jobs, after=self._refresh_view)
        return True
