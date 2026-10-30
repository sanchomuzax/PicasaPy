"""A thumbnail-gyorsítótár képgenerálási műveletei."""

from __future__ import annotations

from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes, reduced_color_flag, scale_down_picasa_mag

_JPEG_QUALITY = 85


class _CacheGenerationMixin:
    def get_or_create(
        self,
        photo_path: str | Path,
        mtime_ns: int,
        size_bytes: int,
        level: int | None = None,
    ) -> Path | None:
        """A kész thumbnail útvonala; None, ha a forrás nem dekódolható.

        `level` (#598) a kért szint; érvénytelen értéket a legközelebbi
        szintre kerekítünk, mert egy elgépelt szám némán negyedik, sosem
        találatot adó tárat nyitna."""
        source = Path(photo_path)
        px = self._size if level is None else self.level_for(level)
        target = self.thumbnail_path(source, mtime_ns, size_bytes, px)
        if target.exists():
            return target
        image = self._szint_forras(source, mtime_ns, size_bytes, px)
        if image is None:
            return None
        # #871: a bélyegkép a Picasa magjával készül — ott mértük
        # (bigthumbs, 119 kép), és ott gyorsabb is az INTER_AREA-nál.
        thumb = scale_down_picasa_mag(image, px)
        ok, encoded = cv2.imencode(
            ".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
        )
        if not ok:
            return None
        try:
            self._write_atomic(target, encoded.tobytes())
        except OSError:
            return None  # tele lemez / NAS-hiba — a hívó placeholderre esik
        return target

    def _szint_forras(
        self, source: Path, mtime_ns: int, size_bytes: int, px: int
    ):
        """Egy szint bemenete: a legkisebb NAGYOBB, már kész szint — ha nincs,
        a forrásfájl (#598).

        A mérés szerint (`szintek` modul) ez a lépés adja a nyereséget: a
        72/144-es szint felépítése egy kész 256-osból nagyságrenddel kevesebb
        munka, mint a forrásfotó újradekódolása."""
        for nagyobb in self._szintek:
            if nagyobb <= px:
                continue
            kesz = self.thumbnail_path(source, mtime_ns, size_bytes, nagyobb)
            if not kesz.exists():
                continue
            payload = read_image_bytes(kesz)
            if payload is None:
                continue
            kep = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
            if kep is not None:
                return kep
        return self._decode_source(source)

    def _read_flag(self, payload: np.ndarray, target: int | None = None) -> int:
        """Dekódolási flag a MÁR beolvasott bájtokból: nagy képre redukált
        beolvasás (memóriakímélés). A döntés a közös `picasapy.cvimage.
        reduced_color_flag`-ben él (#294) — ugyanazt hívja a dedup dHash-e is."""
        return reduced_color_flag(payload, self._size if target is None else target)
