"""#4442: a GlowImageOperation natív színes keverőtagja."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from picasapy.render.belso_ragyogas import inner_glow, ragyogas_maszk, ragyogas_suly


_QEMU_KONTROLLOK = [
    (
        0.0,
        (160, 80, 40),
        (160, 80, 40),
        (160, 80, 40),
        "50e70080785638cd72a030ade47f74020c2b86920ea88186f6116ff6efef8cee",
    ),
    (
        1.0,
        (214, 35, 17),
        (199, 47, 23),
        (160, 80, 40),
        "68ee9d48118944f5791e810296d9d360c9ba47330862ddcb10a427a3bdfe6c06",
    ),
    (
        1.1,
        (219, 30, 15),
        (203, 44, 22),
        (160, 80, 40),
        "5c0f3aec710643c85e491b50954293b3aec5f3984d86c2adac5b42c406e66715",
    ),
    (
        2.0,
        (255, 0, 0),
        (238, 14, 7),
        (160, 80, 40),
        "4b30fe634d38fcf4f4cbb039bf09a3d759999c324cefff9aa1b0216e762d764f",
    ),
    (
        3.0,
        (255, 0, 0),
        (255, 0, 0),
        (160, 80, 40),
        "a1ac7ad25bb6c5ef3cb31da0bcd6ad7986044a3a419124bc39beef702e49b80b",
    ),
]


def test_a_teljes_felbontasu_kimenet_bajtra_egyezik_a_qemu_kontrollokkal() -> None:
    """Mind az öt spec-kimenet: RGB-pontok és a teljes 196 bájtos BGRA-puffer."""
    kep = np.full((7, 7, 3), (160, 80, 40), dtype=np.uint8)
    hibak: list[str] = []

    for strength, sarok, szel, kozep, qemu_sha256 in _QEMU_KONTROLLOK:
        eredmeny = inner_glow(kep, (255, 0, 0), 2, 2, strength)

        mertek = (tuple(eredmeny[0, 0]), tuple(eredmeny[0, 1]), tuple(eredmeny[3, 3]))
        vart_pontok = (sarok, szel, kozep)
        if mertek != vart_pontok:
            hibak.append(f"strength={strength}: RGB-pontok {mertek} != {vart_pontok}")

        bgra = np.empty((7, 7, 4), dtype=np.uint8)
        bgra[..., :3] = eredmeny[..., ::-1]
        bgra[..., 3] = 255
        aktualis_hash = hashlib.sha256(bgra.tobytes()).hexdigest()
        if aktualis_hash != qemu_sha256:
            hibak.append(f"strength={strength}: SHA-256 {aktualis_hash} != {qemu_sha256}")

    assert not hibak, "\n".join(hibak)


@pytest.mark.parametrize(
    "szin",
    ((255, 0, 0), (0, 255, 0), (0, 0, 255)),
    ids=("voros", "zold", "kek"),
)
def test_a_szines_tag_mindharom_csatornan_a_nativ_kerekites(
    szin: tuple[int, int, int],
) -> None:
    """`forrás >> 8` + a spec kerekített `glow / 255` tagja, opaque kontrollon."""
    kep = np.full((7, 7, 3), (40, 80, 160), dtype=np.uint8)
    e = ragyogas_suly(ragyogas_maszk(7, 7, 2, 2), 1.0).astype(np.int64)
    alpha = np.full_like(e, 255)

    # A 0x00bcc206–0x00bcc220 által mért beta, majd a 0x00bcbd60 színes tagja.
    u_alpha = alpha * e + 128
    beta = (u_alpha + (u_alpha >> 8)) >> 8
    u_glow = np.asarray(szin, dtype=np.int64) * beta[..., None] + 128
    glow = (u_glow + (u_glow >> 8)) >> 8
    forras = ((256 - e[..., None]) * kep.astype(np.int64)) >> 8
    vart = (forras + glow).astype(np.uint8)

    np.testing.assert_array_equal(inner_glow(kep, szin, 2, 2, 1.0), vart)
