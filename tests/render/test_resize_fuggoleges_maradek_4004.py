"""#4004: a függőleges ytResampler négyes maradékának kerekítése."""

import numpy as np

from picasapy.render import glimmer_ops


def test_fuggoleges_menet_a_maradekoszlopokbol_kihagyja_a_255_ot(monkeypatch):
    """S=16129 esetén a négyes főciklus 1-et, a maradék 0-t ad."""

    def kuszob_sulyok(be_meret, ki_meret, doboz, lanczos=False):
        assert be_meret == 2
        indices = np.tile(np.array([[0, 1]], dtype=np.intp), (ki_meret, 1))
        weights = np.tile(np.array([[16129, 254]], dtype=np.int32), (ki_meret, 1))
        return indices, weights

    monkeypatch.setattr(glimmer_ops, "_tengely_sulyok", kuszob_sulyok)

    mert = []
    vart = []
    for maradek in range(4):
        width = 4 + maradek
        kep = np.zeros((2, width, 3), dtype=np.uint8)
        kep[0, :, :] = 1

        eredmeny = glimmer_ops._tengely_menten(
            kep, ki_meret=1, tengely=0, doboz=True
        )

        mert.append(eredmeny[0, :, 0].tolist())
        vart.append([1] * (width - maradek) + [0] * maradek)

    assert mert == vart
