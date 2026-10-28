"""A szerkesztési előnézet vörösszem-találatai és geometriája."""

from __future__ import annotations

from pathlib import Path

from picasapy.faces.redeye import detect_eye_circles
from picasapy.ini import PhotoCropReader
from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.render import count_redeye_spots, normalize_crop_ops
from picasapy.render.chain_geometry import AZONOSSAG, Matrix, _szorzat
from picasapy.render.chain_report import validate_and_clamp_op
from picasapy.render.op_geometry import LancHelyzet, invertal, op_geometria
from picasapy.scanner import PICASA_INI_NAME

_REDEYE_DETECTION_SPLIT = FilterOp("__redeye_detection_split__", ())

#: #2271: a körvonalvastagság `[0, 1]`-ből képpontba. A felső határ a
#: KORÁBBI csúszka maximuma (8 képpont) — így a megjelenés nem ugrik meg
#: a mértékegység-váltástól. ⚠️ Ez KÖZELÍTÉS: az eredeti `[0, 1]` →
#: képpont képlete nincs megmérve (a jegy a TÁROLÁST mérte ki, a
#: rajzolást nem). Ha egyszer megmérjük, csak ez az egy szám változik.
_OUTLINE_MAX_PX = 8


def _outline_px(vastagsag: float) -> int:
    """A `[0, 1]`-es körvonalvastagság képpontban, rajzoláshoz."""
    return max(0, round(float(vastagsag) * _OUTLINE_MAX_PX))


def _normalize_redeye_ops(
    crop_reader: PhotoCropReader,
    path: Path,
    ops: tuple[FilterOp, ...],
    post_ops: tuple[FilterOp, ...],
    crop: str | None,
    crop_ini_readable: bool | None,
) -> tuple[tuple[FilterOp, ...], tuple[FilterOp, ...]]:
    """A redeye előtti és utáni láncrész a renderrel azonos crop64-et kapja."""
    if crop_ini_readable is None:
        crop, crop_ini_readable = crop_reader.read(path.parent / PICASA_INI_NAME, path.name)
    normalized = normalize_crop_ops(
        (*ops, _REDEYE_DETECTION_SPLIT, *post_ops),
        crop,
        crop_ini_readable=crop_ini_readable,
        warning_key=str(path),
    )
    split_index = normalized.index(_REDEYE_DETECTION_SPLIT)
    return normalized[:split_index], normalized[split_index + 1 :]


def _post_ops_geometry(
    ops: tuple[FilterOp, ...],
    width: int,
    height: int,
    position: LancHelyzet,
) -> tuple[int, int, Matrix]:
    """A végső méretet és affin leképezést számolja, képszűrők futtatása nélkül."""
    original_matrix = position.eredeti_matrix
    initial_matrix = original_matrix
    original_width = position.eredeti_szelesseg
    original_height = position.eredeti_magassag
    crop_ops = [op for op in ops if op.name == "crop64"]
    last_crop = crop_ops[-1] if crop_ops else None

    for op in ops:
        if op.name == "crop64":
            if op is not last_crop or len(op.params) < 2:
                continue
            try:
                rect = decode_rect64(op.params[1])
                (a, b, c), (d, e, f) = original_matrix
                corners = (
                    (
                        a * (rect.left * original_width) + b * (rect.top * original_height) + c,
                        d * (rect.left * original_width) + e * (rect.top * original_height) + f,
                    ),
                    (
                        a * (rect.right * original_width) + b * (rect.bottom * original_height) + c,
                        d * (rect.right * original_width) + e * (rect.bottom * original_height) + f,
                    ),
                )
                left = max(0, min(round(min(x for x, _ in corners)), width))
                right = max(0, min(round(max(x for x, _ in corners)), width))
                top = max(0, min(round(min(y for _, y in corners)), height))
                bottom = max(0, min(round(max(y for _, y in corners)), height))
                if right <= left or bottom <= top:
                    continue
            except (IndexError, ValueError, ZeroDivisionError):
                continue
            crop_matrix: Matrix = (
                (1.0, 0.0, float(-left)),
                (0.0, 1.0, float(-top)),
            )
            original_matrix = _szorzat(crop_matrix, original_matrix)
            width, height = right - left, bottom - top
            continue

        try:
            validated_op, _warnings = validate_and_clamp_op(op)
            step = op_geometria(validated_op, width, height)
        except (IndexError, TypeError, ValueError, ZeroDivisionError):
            continue
        original_matrix = _szorzat(step.matrix, original_matrix)
        width, height = step.szelesseg, step.magassag

    return width, height, _szorzat(original_matrix, invertal(initial_matrix))


class EditPreviewRedeyeMixin:
    """Az automatikus vörösszem-eredmények előnézeti kezelése."""

    def redeye_auto_result(
        self, photo_id: str, path: Path, ops: tuple[FilterOp, ...]
    ) -> tuple[int, tuple[tuple[float, float, float], ...] | None]:
        """Az Auto gomb régi, képméret nélküli eredményformátuma (#4261)."""
        count, circles, *_geometry = self.redeye_auto_result_with_size(photo_id, path, ops)
        return count, circles

    def redeye_auto_result_with_size(
        self,
        photo_id: str,
        path: Path,
        ops: tuple[FilterOp, ...],
        post_ops: tuple[FilterOp, ...] = (),
        crop: str | None = None,
        crop_ini_readable: bool | None = None,
    ) -> tuple[
        int,
        tuple[tuple[float, float, float], ...] | None,
        tuple[int, int] | None,
        tuple[int, int] | None,
        Matrix,
    ]:
        """Az Auto gomb találatszáma és normalizált YuNet-szemkörei (#4261).

        Az `ops` a láncban a `redeye` beszúrási pontjáig tart (új rétegnél
        a teljes lánc) — így a körök ugyanabban a képméretben értendők,
        amelyen a renderben alkalmazódnak. A visszaadott méret és leképezés
        a kereteket a végső előnézetre vetíti, ha a mentett vörösszem-réteg
        után geometriai művelet (például vágás) következik.
        A detektálás itt, az app-oldalon történik; a visszaadott körök az
        `eye64` FilterOp-paraméterbe kerülnek, így a render sávnak nem kell
        modellt vagy `faces` csomagot ismernie. Modell nélkül `None` a
        körlista, ilyenkor a `redeye` teljes képes útja marad a tartalék.

        A GUI-szálról hívandó (a `_sources`/prefix gyorsítótárat használja,
        ld. `_resolve_source` #546-os megjegyzését). Ha a forrás nem
        dekódolható, üres köröket és méret nélküli geometriai adatot ad.
        """
        key = str(photo_id)
        path = Path(path)
        detection_ops, post_ops = _normalize_redeye_ops(
            self._crop_reader,
            path,
            tuple(ops),
            tuple(post_ops),
            crop,
            crop_ini_readable,
        )
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = None
        source_array = self._resolve_source(key, path, mtime, shared_cache=True)
        if source_array is None:
            return 0, (), None, None, AZONOSSAG
        rendered, _placement, input_position = self._render_cached_jelentes(
            key, source_array, detection_ops
        )
        if rendered is None:
            return 0, (), None, None, AZONOSSAG
        height, width = rendered.shape[:2]
        image_size = (int(width), int(height))
        if input_position is None:
            input_position = LancHelyzet.kezdo(width, height)
        display_width, display_height, eye_to_display = _post_ops_geometry(
            post_ops, width, height, input_position
        )
        display_size = (display_width, display_height)
        detected = detect_eye_circles(rendered)
        pixel_circles = (
            None
            if detected is None
            else tuple((circle.x, circle.y, circle.radius) for circle in detected)
        )
        count = count_redeye_spots(rendered, eye_circles=pixel_circles)
        if detected is None:
            return count, None, image_size, display_size, eye_to_display
        scale = float(min(width, height))
        normalized = tuple(
            (circle.x / width, circle.y / height, circle.radius / scale)
            for circle in detected
            if circle.radius > 0
        )
        return count, normalized, image_size, display_size, eye_to_display

    def redeye_spot_count(self, photo_id: str, path: Path, ops: tuple[FilterOp, ...]) -> int:
        """Kompatibilitási burkoló a találatszámot kérő hívóknak."""
        return self.redeye_auto_result(photo_id, path, ops)[0]
