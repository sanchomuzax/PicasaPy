"""A Vámpírszem festett vonásainak veszteségmentes ini-modellje (#4097)."""

import struct

import pytest

from picasapy.ini import (
    FilterOp,
    RawStroke,
    parse_reanimated_eye_color,
    parse_filters,
    serialize_filters,
    serialize_reanimated_eye_color,
)


def _f32(value: float) -> float:
    return struct.unpack("!f", struct.pack("!f", value))[0]


def _op(*records: str) -> FilterOp:
    return FilterOp("ReanimatedEyeColor", ("1", "6", "20", *records))


AABBA_RECORDS = (
    "0.370000:0.11:17:1:0.07:0.31:0.1|0.2|0.3|0.4",
    "0.610000:0.22:91:1:0.5|0.6",
    "0.830000:0.33:45:0:0.13:0.77:0.7|0.8|0.9|0.95|0.15|0.25",
    "0.500000:0.44:0:0:0.35|0.45|0.55|0.65",
    "0.250000:0.55:180:1:0.07:0.31:0.05|0.06",
)

ABABA_RECORDS = (
    "0.370000:0.11:17:1:0.07:0.31:0.1|0.2",
    "0.610000:0.22:91:1:0.07:0.31:0.5|0.6",
    "0.830000:0.33:45:1:0.07:0.31:0.7|0.8",
    "0.500000:0.44:0:1:0.07:0.31:0.35|0.45",
    "0.250000:0.55:180:1:0.07:0.31:0.05|0.06",
)


class TestSpecGolden4097:
    def test_aabba_sor_bajtra_azonos_es_orokli_a_stilusazonossagot(self):
        modell = parse_reanimated_eye_color(_op(*AABBA_RECORDS))
        vissza = serialize_reanimated_eye_color(modell)

        assert vissza.params[3:] == AABBA_RECORDS
        assert serialize_filters((vissza,)) == (
            "ReanimatedEyeColor=1,6,20," + ",".join(AABBA_RECORDS) + ";"
        )
        assert [len(record.split(":")) for record in vissza.params[3:]] == [
            7,
            5,
            7,
            5,
            7,
        ]
        vonasok = modell.strokes
        assert vonasok[1].style.style_id == vonasok[0].style.style_id
        assert vonasok[3].style.style_id == vonasok[2].style.style_id
        assert vonasok[4].style.style_id != vonasok[0].style.style_id

    def test_ababa_azonos_erteku_de_kulon_stilusobjektumokat_ir_ki(self):
        modell = parse_reanimated_eye_color(_op(*ABABA_RECORDS))
        vissza = serialize_reanimated_eye_color(modell)

        assert vissza.params[3:] == ABABA_RECORDS
        assert serialize_filters((vissza,)) == (
            "ReanimatedEyeColor=1,6,20," + ",".join(ABABA_RECORDS) + ";"
        )
        assert [len(record.split(":")) for record in vissza.params[3:]] == [
            7,
            7,
            7,
            7,
            7,
        ]
        stilusok = [vonas.style for vonas in modell.strokes]
        assert len({stilus.style_id for stilus in stilusok}) == 5
        assert len({(stilus.size, stilus.hardness) for stilus in stilusok}) == 1
        assert {stilus.mode for stilus in stilusok} == {1}

    def test_float32_es_msvc_szamu_kitevok_formazasa(self):
        rekord = "0.370000:1e-005:1.23457e+006:1:1e-005:1.23457e+006:-0|1e-005"
        vissza = serialize_reanimated_eye_color(
            parse_reanimated_eye_color(_op(rekord))
        )

        assert vissza.params[3] == rekord
        vonas = parse_reanimated_eye_color(_op(rekord)).strokes[0]
        assert vonas.alpha == _f32(0.37)
        assert vonas.style.size == _f32(1e-5)
        assert vonas.style.hardness == _f32(1_234_570)
        assert vonas.points[0].x == _f32(-0.0)

    @pytest.mark.parametrize(
        ("token", "vart"),
        [("2", 1), ("-1", 1), ("1.9", 1), ("0.9", 0)],
    )
    def test_mod_atol_szerint_logikai(self, token, vart):
        parsed = parse_reanimated_eye_color(
            _op(f"0.5:0.25:0:{token}:0.07:0.15:0.1|0.2")
        )

        assert parsed.strokes[0].style.mode == vart
        assert serialize_reanimated_eye_color(parsed).params[3] == (
            f"0.500000:0.25:0:{vart}:0.07:0.15:0.1|0.2"
        )

    def test_nincs_tartomanyellenorzes_a_megerositett_peldan(self):
        rekord = "7.5:-3:1000:1:0.1:0.2:5|-6"
        parsed = parse_reanimated_eye_color(_op(rekord))
        vonas = parsed.strokes[0]

        assert (vonas.alpha, vonas.spacing, vonas.rotation) == (
            _f32(7.5),
            _f32(-3),
            _f32(1000),
        )
        assert (vonas.style.size, vonas.style.hardness) == (_f32(0.1), _f32(0.2))
        assert [(pont.x, pont.y) for pont in vonas.points] == [
            (_f32(5), _f32(-6))
        ]
        assert serialize_reanimated_eye_color(parsed).params[3] == (
            "7.500000:-3:1000:1:0.1:0.2:5|-6"
        )


class TestAszimmetrikusSorok4097:
    @pytest.mark.parametrize(
        "rekord",
        [
            "0.37:0.11:17:1",  # nulla pont, 4 rész
            "0.37:0.11:17:1:0.07:0.31",  # nulla pont, 6 rész
            "0.37:0.11:17:1:0.07:0.31:0.1|0.2:extra",  # 8 rész
            "0.37:0.11:17:1:0.1|0.2",  # első, stílus nélküli 5 rész
        ],
    )
    def test_az_eredeti_altal_elutasitott_sor_nyersen_megmarad(self, rekord):
        parsed = parse_reanimated_eye_color(_op(rekord))

        assert len(parsed.strokes) == 1
        assert isinstance(parsed.strokes[0], RawStroke)
        assert parsed.strokes[0].raw == rekord
        assert serialize_reanimated_eye_color(parsed).params[3] == rekord

    def test_a_nyers_rekord_mellett_mas_vonas_es_filtermezok_is_megmaradnak(
        self,
    ):
        sor = (
            "bw=1;ReanimatedEyeColor=1,6,20,"
            "0.500000:0.25:0:1:0.07:0.15:0.1|0.2,"
            "0.37:0.11:17:1,"
            "0.800000:0.5:90:0:0.07:0.15:0.3|0.4;future=1,x;"
        )
        ops = parse_filters(sor)
        op = next(item for item in ops if item.name == "ReanimatedEyeColor")
        updated = tuple(
            serialize_reanimated_eye_color(parse_reanimated_eye_color(item))
            if item.name == "ReanimatedEyeColor"
            else item
            for item in ops
        )

        assert isinstance(parse_reanimated_eye_color(op).strokes[1], RawStroke)
        assert serialize_filters(updated) == sor
