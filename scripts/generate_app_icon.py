#!/usr/bin/env python3
"""Generate PicasaPy icon assets from the mark in ``assets/logo.svg``."""

from __future__ import annotations

import copy
import os
import struct
import sys
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication, QPixmap


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "src/picasapy/app/assets"
LOGO_PATH = ASSETS_DIR / "logo.svg"
DEFAULT_OUTPUT_DIR = ASSETS_DIR
SIZES = (16, 24, 32, 48, 64, 128, 256)
SVG_NS = "http://www.w3.org/2000/svg"
MARK_ID = "picasapy-icon-mark"

# Original Picasa frames, alpha==255 bounding boxes from
# docs/specs/picasa-inditoikon-meres.md: (white disk diameter, center x, center y).
# The other sizes scale the 256 px geometry by size / 256.
MEASURED_GEOMETRY = {
    32: (30.0, 16.0, 16.0),
    48: (44.0, 23.0, 23.0),
    256: (226.0, 124.0, 126.0),
}
SCALED_GEOMETRY = (226.0, 124.0, 126.0)
# Diameter of the colored mark in the original Picasa frames (saturated pixels).
MEASURED_MARK = {16: 14.0, 32: 29.0, 48: 42.0, 256: 210.0}
SCALED_MARK = 210.0

# The existing wordmark's mark has this measured alpha>=250 bounding box.
MARK_CENTER = (181.25, 185.25)
MARK_LONGEST_SIDE = 370.5
ICON_BACKGROUND = "#ffffff"
SMALL_TILE_BACKGROUND = "#f9f9f9"


def _load_mark() -> ET.Element:
    ET.register_namespace("", SVG_NS)
    root = ET.parse(LOGO_PATH).getroot()
    for element in root.iter():
        if element.get("id") == MARK_ID:
            return element
    raise ValueError(f"Missing SVG icon mark group: {MARK_ID}")


def _geometry(size: int) -> tuple[float, float, float]:
    if size in MEASURED_GEOMETRY:
        return MEASURED_GEOMETRY[size]
    factor = size / 256
    diameter, center_x, center_y = SCALED_GEOMETRY
    return diameter * factor, center_x * factor, center_y * factor


def _mark_diameter(size: int) -> float:
    return MEASURED_MARK.get(size, SCALED_MARK * size / 256)


def _icon_svg(mark: ET.Element, size: int) -> bytes:
    root = ET.Element(
        f"{{{SVG_NS}}}svg",
        {"width": str(size), "height": str(size), "viewBox": f"0 0 {size} {size}"},
    )

    if size == 16:
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}rect",
            {
                "width": "16",
                "height": "16",
                "fill": SMALL_TILE_BACKGROUND,
            },
        )
        center_x = center_y = 8.0
        mark_size = _mark_diameter(16)
    else:
        diameter, center_x, center_y = _geometry(size)
        # Edge antialiasing leaves one partial pixel on each side.
        radius = diameter / 2 + 1
        ET.SubElement(
            root,
            f"{{{SVG_NS}}}circle",
            {
                "cx": f"{center_x:.6f}",
                "cy": f"{center_y:.6f}",
                "r": f"{radius:.6f}",
                "fill": ICON_BACKGROUND,
            },
        )
        mark_size = _mark_diameter(size)

    scaled_mark = copy.deepcopy(mark)
    scale = mark_size / MARK_LONGEST_SIDE
    translate_x = center_x - MARK_CENTER[0] * scale
    translate_y = center_y - MARK_CENTER[1] * scale
    scaled_mark.set(
        "transform",
        f"translate({translate_x:.8f} {translate_y:.8f}) scale({scale:.8f})",
    )
    root.append(scaled_mark)
    return ET.tostring(root, encoding="utf-8")


def _render_png(svg: bytes) -> bytes:
    pixmap = QPixmap()
    if not pixmap.loadFromData(svg):
        raise RuntimeError("Qt could not render the generated SVG icon")
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise RuntimeError("Could not open the in-memory PNG buffer")
    if not pixmap.save(buffer, "PNG"):
        raise RuntimeError("Qt could not encode the generated PNG icon")
    image = Image.open(BytesIO(bytes(data))).convert("RGBA")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _ico_bytes(frames: dict[int, bytes]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(frames))
    entries = bytearray()
    payload = bytearray()
    offset = 6 + 16 * len(frames)

    for size in SIZES:
        png = frames[size]
        dimension = 0 if size == 256 else size
        entries.extend(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(png),
                offset,
            )
        )
        payload.extend(png)
        offset += len(png)

    return header + bytes(entries) + bytes(payload)


def generate(output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])
    mark = _load_mark()
    frames = {size: _render_png(_icon_svg(mark, size)) for size in SIZES}

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "icon.ico").write_bytes(_ico_bytes(frames))
    (output_dir / "icon.png").write_bytes(frames[256])


def main(argv: list[str]) -> int:
    output_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT_DIR
    generate(output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
