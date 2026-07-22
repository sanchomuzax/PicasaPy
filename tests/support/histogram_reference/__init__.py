"""Determinisztikus hisztogram-referencia képkészlet (#236).

A csomag kicsi, előre ismert hisztogramú szintetikus képeket állít elő, hogy
a `picasapy.app.histogram_helper.compute_rgb_histogram` kimenetét
összevethessük a Picasa 3.x hisztogram-megjelenítésével (golden-összevetés).

A képek numpy-val, futásidőben, determinisztikusan készülnek — nincs bináris
melléklet a repóban. Minden referenciához tartozik egy emberi leírás a várt
hisztogram-alakról (csúcs-pozíciók, laposság), ld. `REFERENCES`.
"""

from tests.support.histogram_reference.generator import (
    REFERENCES,
    ReferenceImage,
    reference_by_name,
    reference_images,
    write_reference_pngs,
)

__all__ = [
    "REFERENCES",
    "ReferenceImage",
    "reference_by_name",
    "reference_images",
    "write_reference_pngs",
]
