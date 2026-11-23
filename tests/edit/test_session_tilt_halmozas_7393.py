"""#7393: a Kiegyenesítés HALMOZ - a második Apply új `tilt` tagot fűz a lánc végére.

Az eredeti Picasa (job-913) két húzás és két Alkalmaz után két `tilt` tagot ír
a láncba: `filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;`.
"""

from __future__ import annotations

from picasapy.edit.session import EditSession
from picasapy.ini.filters import parse_filters


def _lanc(session: EditSession) -> list[tuple[str, tuple[str, ...]]]:
    return [(op.name, op.params) for op in session.ops]


def test_az_append_tilt_ures_lancon_egy_tagot_ir() -> None:
    session = EditSession(ops=()).append_tilt(0.391249, 0.0)

    assert _lanc(session) == [("tilt", ("1", "0.391249", "0.000000"))]


def test_az_append_tilt_a_meglevo_tilt_mellett_ujat_fuz_a_vegere() -> None:
    elso = EditSession(ops=()).append_tilt(0.391249, 0.0)

    masodik = elso.append_tilt(-0.399233, 0.0)

    assert _lanc(masodik) == [
        ("tilt", ("1", "0.391249", "0.000000")),
        ("tilt", ("1", "-0.399233", "0.000000")),
    ]


def test_az_append_tilt_a_nem_tilt_tagok_utan_is_a_lanc_vegere_kerul() -> None:
    session = EditSession(ops=tuple(parse_filters("tilt=1,0.2,0.000000;bw=1;")))

    uj = session.append_tilt(0.1, 0.0)

    assert [op.name for op in uj.ops] == ["tilt", "bw", "tilt"]


def test_az_append_tilt_nem_modositja_az_eredeti_munkamenetet() -> None:
    eredeti = EditSession(ops=tuple(parse_filters("tilt=1,0.2,0.000000;")))

    eredeti.append_tilt(0.1, 0.0)

    assert [op.params for op in eredeti.ops] == [("1", "0.2", "0.000000")]


def test_a_set_tilt_valtozatlanul_csere() -> None:
    """A `set_tilt` a többi hívónak marad: az első tilt helyén cserél."""
    session = EditSession(ops=tuple(parse_filters("tilt=1,0.2,0.000000;")))

    uj = session.set_tilt(0.5, 0.0)

    assert _lanc(uj) == [("tilt", ("1", "0.500000", "0.000000"))]
