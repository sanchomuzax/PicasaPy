"""#4122: a Border fedése és alfája a natív fixpontos képletet követi."""

from __future__ import annotations

import numpy as np

from picasapy.render import glimmer_frame_ops as frame_ops


# rontás-kontroll: glimmer_frame_ops._BORDER_Q_X_SLOPE = 0 → 1 failed.


def test_a_kulso_es_forrassarok_q_racs_a_spec_szerinti():
    kulso = np.array(
        [
            [2048, 1040, 544, 560, 1088, 2128],
            [1280, 272, -224, -208, 320, 1360],
            [1024, 16, -480, -464, 64, 1104],
            [1280, 272, -224, -208, 320, 1360],
            [2048, 1040, 544, 560, 1088, 2128],
            [3328, 2320, 1824, 1840, 2368, 3408],
        ],
        dtype=np.int64,
    )
    forras = np.array(
        [
            [512, 16, 32, 560],
            [256, -240, -224, 304],
            [512, 16, 32, 560],
            [1280, 784, 800, 1328],
        ],
        dtype=np.int64,
    )

    assert np.array_equal(frame_ops._border_q_racs(3), kulso)
    assert np.array_equal(frame_ops._border_q_racs(2), forras)


def test_a_ketto_harom_fedesi_pont_a_spec_csonkitasat_hasznalja():
    kulso = frame_ops._sarok_fedes(np.array([2128]), 1600, 3136)
    forras = frame_ops._sarok_fedes(np.array([512]), 256, 1024)

    assert (int(kulso[0]), int(forras[0])) == (167, 170)


def test_a_reszleges_alfa_es_az_opaque_kompozit_kulon_ellenorizheto():
    # A spec kontrollpéldája: A=0x20, C=175 mellett a rajzoló köztes pixele.
    koztes = frame_ops._kever_reszleges_argb(0xFF010101, 0x20010101, 175)
    assert koztes == 0xFE010001

    # A 0x20 és 0xff forrásalfa különböző, C-vel súlyozott alfát őriz;
    # mindkettőből 0xff lesz az opaque cél fölötti végső alfa.
    alfa_20 = frame_ops._fedett_forras_alfa(0x20, 175)
    alfa_ff = frame_ops._fedett_forras_alfa(0xFF, 175)
    assert (alfa_20, alfa_ff) == (21, 174)
    koztes_ff = frame_ops._kever_reszleges_argb(0xFF010101, 0xFF010101, 175)
    assert koztes_ff == 0xFE010001
    assert frame_ops._kompozit_alfa(0xFF, alfa_20) == 0xFF
    assert frame_ops._kompozit_alfa(0xFF, alfa_ff) == 0xFF
    assert frame_ops._kompozit_alfa(0xFF, (koztes_ff >> 24) & 0xFF) == 0xFF
