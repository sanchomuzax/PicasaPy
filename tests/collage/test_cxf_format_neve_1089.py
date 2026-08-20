"""A `.cxf` `format` attribútuma a LAPFORMÁTUM NEVE (#1089).

A tulajdonos 11 valódi Picasa-kollázsán mérve: a `format` a kiválasztott
oldalformátum azonosítója (A4 = `297:210` — milliméterben!), **nem** a
képpontméretből számolt arány, és **nincs** legegyszerűbb alakra hozva.
A régi képletünk 11-ből 6-ot elrontott.
"""

from __future__ import annotations

import pytest

from picasapy.collage.draft import page_ratio_of
from picasapy.collage.page_formats import PAGE_FORMATS, format_text, page_ratio


@pytest.mark.parametrize(
    ("kulcs", "vart"),
    [
        # a tulajdonos 11 kollázsán ELŐFORDULÓ négy formátum — nem
        # kitalált variációk, hanem a mért esetek
        ("A4", "297:210"),  # AI8, AI9, AI10 — a képpontarány 256:181 volna
        ("10x15m", "15:10"),  # AI — a `gcd` 3:2-re rontaná
        ("Desktop4x3", "4:3"),  # AI2…AI7
        ("Square", "1:1"),  # AI1
    ],
)
def test_a_mert_mintak_formatumneve(kulcs, vart):
    """A mért `format` értékek — nyers alak, se osztás, se képpontarány."""
    assert format_text(kulcs) == vart


def test_a_nev_NEM_forog_a_tajolassal():
    """Álló lapon is `297:210` — a tájolást külön mező mondja meg.

    Az AI2 és az AI6 álló (3841×5120), az eredeti mégis `format="4:3"
    orientation="portrait"`-ot ír. A régi, képpontból számoló képlet
    `5120:3841`-et adott volna."""
    assert format_text("A4") == format_text("A4")
    assert page_ratio_of(format_text("A4"), "portrait") > 1.0
    assert page_ratio_of(format_text("A4"), "landscape") < 1.0


@pytest.mark.parametrize("fmt", [f for f in PAGE_FORMATS if f.long is not None])
@pytest.mark.parametrize("tajolas", ["landscape", "portrait"])
def test_a_nev_visszaadja_a_lap_alakjat(fmt, tajolas):
    """Kör: a kiírt névből visszaolvasva UGYANAZ a lapalak jön ki.

    Enélkül egy mentett kollázs újranyitva más alakú lappal jönne vissza —
    a `format` a `.cxf`-ben nem dísz, a helyreállítás ebből dolgozik."""
    assert page_ratio_of(format_text(fmt.key), tajolas) == pytest.approx(
        page_ratio(fmt.key, tajolas)
    )


def test_a_MENTETT_cxf_a_nevet_hordozza(tmp_path):
    """A kimenetig elvezetve: a lemezre írt `.cxf`-ben a NÉV áll.

    A név-számítás önmagában semmit nem ér, ha nem jut el a mentésig — a
    #1089 pont abból lett, hogy a `format` a képméretből született. A4-es
    lapot mentünk, és a fájlban `297:210`-nek kell állnia, nem `256:181`-nek.
    """
    from picasapy.app import collage_output
    from picasapy.collage.nodes import CollageNode
    from picasapy.collage.themes import NOBORDER
    from picasapy.collage.page_formats import page_ratio
    from support.jpeg_factory import make_jpeg

    kep = tmp_path / "a.jpg"
    make_jpeg(kep, size=(160, 120))
    arany = page_ratio("A4", "landscape")
    beallitas = collage_output.render_settings(
        theme="picturegrid",
        border=NOBORDER,
        spacing=0.0,
        shadows=False,
        page_ratio=arany,
        background_rgb=(255, 255, 255),
        frame_center=-1,
        seed=1,
        width=800,
    )
    node = CollageNode(
        path=str(kep),
        center_x=512.0,
        center_y=512.0 * arany,
        width=300.0,
        height=220.0,
        border=NOBORDER,
    )
    collage_output.render_collage(
        (node,), beallitas, tmp_path / "k.jpg", format_key="A4"
    )

    szoveg = (tmp_path / "k.cxf").read_text(encoding="utf-8")
    assert 'format="297:210"' in szoveg
    assert "256:181" not in szoveg
