"""#626 natív Border-mérések: referencia-ág MMX ([d695d0]=1, [d695d4]=1).

A 15 eset 2053 kimeneti pixelének RGB bájtjait hasonlítja össze a natív
ARGB-mérések RGB csatornáival. A véletlen forrásképek pixeladatai is rögzítettek.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.glimmer_frame_ops import draw_border


_MMX_ESETEK = (
    {
        'name': 'c1_200_100_50__10_220_90',
        'width': 5,
        'height': 5,
        'radius': 2,
        'inner_thickness': 1,
        'outer_thickness': 1,
        'outer': (200, 100, 50),
        'inner': (10, 220, 90),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432 ffc86432 fe41b84d ff0adc5a ff0adc5a ff0adc5a ff0adc5a ff0adc5a
            fe4bb14b ffc86432 ffc86432 ff0adc5a ff18745d ff204060 ff204060 ff204060
            ff177e5d ff0adc5a ffc86432 ffc86432 ff0adc5a ff204060 ff204060 ff204060
            ff204060 ff1e4a5f ff0adc5a ffc86432 ffc86432 ff0adc5a ff204060 ff204060
            ff204060 ff204060 ff204060 ff0adc5a ffc86432 ffc86432 ff0adc5a ff18745d
            ff204060 ff204060 ff204060 ff177e5d ff0adc5a ffc86432 ffc86432 fe41b84d
            ff0adc5a ff10ac5b ff204060 ff10af5b ff0adc5a fe4bb14b ffc86432 ffc86432
            ffc86432 fe63a346 fe25c953 ff0adc5a fe28c853 fe689f45 ffc86432 ffc86432
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432
        """,
    },
    {
        'name': 'c2_30_140_220__250_240_20',
        'width': 7,
        'height': 7,
        'radius': 3,
        'inner_thickness': 1,
        'outer_thickness': 2,
        'outer': (30, 140, 220),
        'inner': (250, 240, 20),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fe5ba7a3 fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 fef6ee16 fe4fa2ae ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc fee4e626 ffcfcd22 ff23425e ff204060 ff204060 ff204060 ff2b485c
            ffdcd81e fed8e031 ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fffaf014 ff4c6350
            ff204060 ff204060 ff204060 ff204060 ff204060 ff5a6e4b fffaf014 ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc fffaf014 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff2e4b5a fffaf014 ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            fffaf014 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            fffaf014 ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fffaf014 ff4c6350 ff204060
            ff204060 ff204060 ff204060 ff204060 ff5a6e4b fffaf014 ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc fee4e626 ffcfcd22 ff23425e ff204060 ff204060 ff204060
            ff2b485c ffdcd81e fed8e031 ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fe5ba7a3
            fffaf014 fffaf014 ffa9af30 ff204060 ffacb12f fffaf014 fff6ee16 fe4fa2ae
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fe3e9abd feaacb5b fedfe32a
            fffaf014 fedde32c fea5c960 fe3596c5 ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc
        """,
    },
    {
        'name': 'c3_0_0_0__255_0_255',
        'width': 4,
        'height': 6,
        'radius': 1,
        'inner_thickness': 2,
        'outer_thickness': 1,
        'outer': (0, 0, 0),
        'inner': (255, 0, 255),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
            ff000000 ff000000 ff000000 fe470047 ffff00ff ffff00ff ffff00ff ffff00ff
            ffff00ff fefb00fb fe390039 ff000000 ff000000 fee700e7 ffff00ff ffff00ff
            ffff00ff ffff00ff ffff00ff ffff00ff fed900d9 ff000000 ff000000 ffff00ff
            ffff00ff ff204060 ff204060 ff204060 ff2d3b69 ffff00ff ffff00ff ff000000
            ff000000 ffff00ff ffff00ff ff204060 ff204060 ff204060 ff204060 ffff00ff
            ffff00ff ff000000 ff000000 ffff00ff ffff00ff ff204060 ff204060 ff204060
            ff204060 ffff00ff ffff00ff ff000000 ff000000 ffff00ff ffff00ff ff204060
            ff204060 ff204060 ff204060 ffff00ff ffff00ff ff000000 ff000000 ffff00ff
            ffff00ff ff204060 ff204060 ff204060 ff204060 ffff00ff ffff00ff ff000000
            ff000000 fee700e7 ffff00ff ffff00ff ff204060 ff204060 ffff00ff ffff00ff
            fed900d9 ff000000 ff000000 fe470047 ffff00ff ffff00ff ffff00ff ffff00ff
            ffff00ff fefb00fb fe390039 ff000000 ff000000 ff000000 fe250025 fea300a3
            fee100e1 fedf00df fe9d009d fe1b001b ff000000 ff000000 ff000000 ff000000
            ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
        """,
    },
    {
        'name': 'c4_12_200_99__240_30_60',
        'width': 9,
        'height': 8,
        'radius': 4,
        'inner_thickness': 1,
        'outer_thickness': 1,
        'outer': (12, 200, 99),
        'inner': (240, 30, 60),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 fe985e4a
            fff01e3c fff01e3c fff01e3c fff01e3c fff01e3c fff01e3c fff01e3c fe8e664c
            ff0cc863 ff0cc863 ff0cc863 fe826e4e fff01e3c ff7c3050 ff204060 ff204060
            ff204060 ff204060 ff204060 ff852f4e fff01e3c fe75784f ff0cc863 ff0cc863
            fff01e3c ff972c4b ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ffa42a48 fee7233c ff0cc863 ff0cc863 fff01e3c ff3e3b5a ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff4b3858 fff01e3c
            ff0cc863 ff0cc863 fff01e3c ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff2d3d5d fff01e3c ff0cc863 ff0cc863 fff01e3c
            ff3e3b5a ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff4b3858 fff01e3c ff0cc863 ff0cc863 fff01e3c ff972c4b ff204060 ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ffa42a48 fee7233c ff0cc863
            ff0cc863 fe826e4e fff01e3c ff7c3050 ff204060 ff204060 ff204060 ff204060
            ff204060 ff852f4e fff01e3c fe75784f ff0cc863 ff0cc863 ff0cc863 ff985e4a
            fff01e3c ffd72240 ff9d2b4a ff204060 ff9f2b49 ffdc213f fff01e3c ff8e664c
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 fe529356 feab5047 fed82e3f
            fff01e3c fed62f3f fea75348 fe4a9857 ff0cc863 ff0cc863 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff0cc863 ff0cc863
        """,
    },
    {
        'name': 'c5_77_33_150__5_200_120',
        'width': 6,
        'height': 10,
        'radius': 3,
        'inner_thickness': 3,
        'outer_thickness': 2,
        'outer': (77, 33, 150),
        'inner': (5, 200, 120),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 fe3f3e90 fe10ac7c ff05c878 ff05c878 ff05c878
            ff05c878 ff05c878 ff05c878 fe13a67d fe423691 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 fe453192 fe09bb79 ff05c878 ff05c878 ff05c878 ff05c878
            ff05c878 ff05c878 ff05c878 ff05c878 fe0db37a fe492794 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 fe1b9281 ff05c878 ff05c878 ff05c878 ff05c878 ff05c878
            ff05c878 ff05c878 ff05c878 ff05c878 ff05c878 fe1f8982 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff0aad73 ff1f4260 ff204060
            ff204060 ff1e4661 ff08b574 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff1a5b64 ff204060 ff204060
            ff204060 ff204060 ff186466 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff204060 ff204060 ff204060
            ff204060 ff204060 ff1e4961 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff1a5b64 ff204060 ff204060
            ff204060 ff204060 ff186466 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff05c878 ff05c878 ff05c878 ff0aad73 ff1f4260 ff204060
            ff204060 ff1e4661 ff08b574 ff05c878 ff05c878 ff05c878 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 fe1b9281 ff05c878 ff05c878 ff05c878 ff05c878 ff0e956f
            ff0e976f ff05c878 ff05c878 ff05c878 ff05c878 fe1f8982 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 fe453192 fe09bb79 ff05c878 ff05c878 ff05c878 ff05c878
            ff05c878 ff05c878 ff05c878 ff05c878 fe0db37a fe492794 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 fe3f3e90 fe10ac7c ff05c878 ff05c878 ff05c878
            ff05c878 ff05c878 ff05c878 fe13a67d fe423691 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 fe2e6689 fe169d7f fe0ab87a
            fe0bb77a fe179a7f fe2f6189 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
            ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196 ff4d2196
        """,
    },
    {
        'name': 'e1_clampK_3x3',
        'width': 3,
        'height': 3,
        'radius': 1,
        'inner_thickness': 1,
        'outer_thickness': 1,
        'outer': (40, 40, 200),
        'inner': (200, 250, 10),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8
            ffc8fa0a ffc8fa0a ffc8fa0a ffc8fa0a ffc8fa0a ff2828c8 ff2828c8 ffc8fa0a
            ff204060 ff204060 ff2a4b5a ffc8fa0a ff2828c8 ff2828c8 ffc8fa0a ff204060
            ff204060 ff204060 ffc8fa0a ff2828c8 ff2828c8 ffc8fa0a ffc8fa0a ff204060
            ffc8fa0a ffc8fa0a ff2828c8 ff2828c8 fe59698c fea7cf2f ffc8fa0a fea4cb32
            fe525f94 ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8 ff2828c8
            ff2828c8
        """,
    },
    {
        'name': 'e2_wide_12x4',
        'width': 12,
        'height': 4,
        'radius': 2,
        'inner_thickness': 2,
        'outer_thickness': 3,
        'outer': (250, 10, 120),
        'inner': (30, 30, 30),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 febb0f5e ff1e1e1e ff1e1e1e
            ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e
            ff1e1e1e ff1e1e1e ff1e1e1e fe201d1e fec70d62 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fe321b26 ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e
            ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e
            ff1e1e1e ff1e1e1e fe3e1a2a fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 ff1e1e1e ff1e1e1e ff1f3449 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff1f3245 ff1e1e1e
            ff1e1e1e fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 ff1e1e1e
            ff1e1e1e ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff204060 ff1f3d5b ff1e1e1e ff1e1e1e fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 ff1e1e1e ff1e1e1e ff1f3449
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff1f3245 ff1e1e1e ff1e1e1e fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fe321b26 ff1e1e1e ff1e1e1e ff1e2832 ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff1e2730
            ff1e1e1e ff1e1e1e fe3e1a2a fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 febb0f5e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e
            ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e fe201d1e
            fec70d62 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fed80c6a fe6c163e fe371b28 ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e ff1e1e1e
            ff1e1e1e ff1e1e1e ff1e1e1e fe391b29 fe71153f fee10b6d fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78 fffa0a78
            fffa0a78 fffa0a78 fffa0a78 fffa0a78
        """,
    },
    {
        'name': 'e3_B0_10x9',
        'width': 10,
        'height': 9,
        'radius': 3,
        'inner_thickness': 0,
        'outer_thickness': 2,
        'outer': (90, 180, 60),
        'inner': (240, 20, 200),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff4e9d43 ff20415f
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff22455e ff52a440
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff2b5758 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ff2f5e56 ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff23475d ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff204060 ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff204060 ff204060 ff204060 ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff2b5758 ff204060 ff204060 ff204060 ff204060 ff204060
            ff204060 ff204060 ff204060 ff2f5e56 ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff4e9d43 ff20415f ff204060 ff204060 ff204060 ff204060 ff204060 ff204060
            ff22455e ff52a440 ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff448949 ff204060 ff204060 ff204060 ff204060 ff458a48 ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
            ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c ff5ab43c
        """,
    },
    {
        'name': 'r0a_255_0_0__0_0_255',
        'width': 3,
        'height': 2,
        'radius': 0,
        'inner_thickness': 1,
        'outer_thickness': 2,
        'outer': (255, 0, 0),
        'inner': (0, 0, 255),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000
            ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000
            ffff0000 ffff0000 ffff0000 ffff0000 ff0000ff ff0000ff ff0000ff ff0000ff
            ff0000ff ffff0000 ffff0000 ffff0000 ffff0000 ff0000ff ff204060 ff204060
            ff204060 ff0000ff ffff0000 ffff0000 ffff0000 ffff0000 ff0000ff ff204060
            ff204060 ff204060 ff0000ff ffff0000 ffff0000 ffff0000 ffff0000 fe5f009f
            ff0000ff ff0000ff ff0000ff fe670097 ffff0000 ffff0000 ffff0000 ffff0000
            ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000
            ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000 ffff0000
        """,
    },
    {
        'name': 'r0b_30_140_220__250_240_20',
        'width': 5,
        'height': 7,
        'radius': 0,
        'inner_thickness': 3,
        'outer_thickness': 1,
        'outer': (30, 140, 220),
        'inner': (250, 240, 20),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014
            fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014 fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 ff1e8cdc ff1e8cdc
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014 fffaf014
            ff204060 ff204060 ff204060 ff204060 ff204060 fffaf014 fffaf014 fffaf014
            ff1e8cdc ff1e8cdc fffaf014 fffaf014 fffaf014 ff204060 ff204060 ff204060
            ff204060 ff204060 fffaf014 fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014
            fffaf014 fffaf014 ff204060 ff204060 ff204060 ff204060 ff204060 fffaf014
            fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014 fffaf014 ff204060
            ff204060 ff204060 ff204060 ff204060 fffaf014 fffaf014 fffaf014 ff1e8cdc
            ff1e8cdc fffaf014 fffaf014 fffaf014 ff204060 ff204060 ff204060 ff204060
            ff204060 fffaf014 fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014
            fffaf014 ff204060 ff204060 ff204060 ff204060 ff204060 fffaf014 fffaf014
            fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014 fffaf014 ff204060 ff204060
            ff204060 ff204060 ff204060 fffaf014 fffaf014 fffaf014 ff1e8cdc ff1e8cdc
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014
            ff1e8cdc ff1e8cdc fea7ca5e fffaf014 fffaf014 fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 fffaf014 fea0c664 ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc
        """,
    },
    {
        'name': 'r0c_12_200_99__240_30_60',
        'width': 4,
        'height': 3,
        'radius': 0,
        'inner_thickness': 0,
        'outer_thickness': 2,
        'outer': (12, 200, 99),
        'inner': (240, 30, 60),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff204060 ff204060 ff204060 ff204060 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff204060 ff204060 ff204060 ff204060 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff204060 ff204060 ff204060 ff204060 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863
            ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863 ff0cc863
        """,
    },
    {
        'name': 'r0d_0_0_0__255_0_255',
        'width': 2,
        'height': 2,
        'radius': 0,
        'inner_thickness': 1,
        'outer_thickness': 1,
        'outer': (0, 0, 0),
        'inner': (255, 0, 255),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ffff00ff
            ffff00ff ffff00ff ffff00ff ff000000 ff000000 ffff00ff ff204060 ff204060
            ffff00ff ff000000 ff000000 ffff00ff ff204060 ff204060 ffff00ff ff000000
            ff000000 fe9f009f ffff00ff ffff00ff fe970097 ff000000 ff000000 ff000000
            ff000000 ff000000 ff000000 ff000000
        """,
    },
    {
        'name': 'r0e_200_100_50__10_220_90',
        'width': 3,
        'height': 2,
        'radius': 0,
        'inner_thickness': 1,
        'outer_thickness': 2,
        'outer': (200, 100, 50),
        'inner': (10, 220, 90),
        'source_rgb': (32, 64, 96),
        'native_argb_hex': """\
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432 ffc86432 ffc86432 ffc86432 ff0adc5a ff0adc5a ff0adc5a ff0adc5a
            ff0adc5a ffc86432 ffc86432 ffc86432 ffc86432 ff0adc5a ff204060 ff204060
            ff204060 ff0adc5a ffc86432 ffc86432 ffc86432 ffc86432 ff0adc5a ff204060
            ff204060 ff204060 ff0adc5a ffc86432 ffc86432 ffc86432 ffc86432 fe51ae4a
            ff0adc5a ff0adc5a ff0adc5a fe56aa49 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
        """,
    },
    {
        'name': 'p1_random_5x5_R2',
        'width': 5,
        'height': 5,
        'radius': 2,
        'inner_thickness': 1,
        'outer_thickness': 1,
        'outer': (200, 100, 50),
        'inner': (10, 220, 90),
        'source_rgb_hex': """\
            bb3e73 0a44a6 c66c02 ff7b9e e93a02 28233f f6e0ba 89ff91 644f12 0594ea
            fb928e 80d582 80b573 9726ec 775426 8b56a8 972927 9b55fa 2ed7a5 51abd3
            5690d2 057ab8 c5194e 580357 74dabd
        """,
        'native_argb_hex': """\
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432 ffc86432 fe41b84d ff0adc5a ff0adc5a ff0adc5a ff0adc5a ff0adc5a
            fe4bb14b ffc86432 ffc86432 ff0adc5a ff7f736a ff0a44a6 ffc66c02 ffff7b9e
            ff8f7a25 ff0adc5a ffc86432 ffc86432 ff0adc5a ff28233f fff6e0ba ff89ff91
            ff644f12 ff0598e0 ff0adc5a ffc86432 ffc86432 ff0adc5a fffb928e ff80d582
            ff80b573 ff9726ec ff775426 ff0adc5a ffc86432 ffc86432 ff0adc5a ff5f838d
            ff972927 ff9b55fa ff2ed7a5 ff34bea2 ff0adc5a ffc86432 ffc86432 fe41b84d
            ff0adc5a ff08be76 ffc5194e ff209d59 ff0adc5a fe4bb14b ffc86432 ffc86432
            ffc86432 fe63a346 fe25c953 ff0adc5a fe28c853 fe689f45 ffc86432 ffc86432
            ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432 ffc86432
            ffc86432
        """,
    },
    {
        'name': 'p2_random_7x6_R3',
        'width': 7,
        'height': 6,
        'radius': 3,
        'inner_thickness': 2,
        'outer_thickness': 1,
        'outer': (30, 140, 220),
        'inner': (250, 240, 20),
        'source_rgb_hex': """\
            bb3e73 0a44a6 c66c02 ff7b9e e93a02 28233f f6e0ba 89ff91 644f12 0594ea
            fb928e 80d582 80b573 9726ec 775426 8b56a8 972927 9b55fa 2ed7a5 51abd3
            5690d2 057ab8 c5194e 580357 74dabd 7c2d95 eb8e67 1c74c0 08ab06 2ca79c
            b39e54 10821c 1687d1 365775 dcd842 bd8ea1 9c2226 c03ad7 ed93ce 525f1b
            029e45 cedc24
        """,
        'native_argb_hex': """\
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fea5c960
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fe9bc468
            ff1e8cdc ff1e8cdc ff1e8cdc fe90bf72 fffaf014 fffaf014 fffaf014 fffaf014
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fe84b97e ff1e8cdc ff1e8cdc
            fffaf014 fffaf014 ffedcd26 ff0d46a3 ffc66c02 ffff7b9e ffe93a02 ff322d3c
            fff9ed2a fffaf014 fef2eb1a ff1e8cdc ff1e8cdc fffaf014 fffaf014 ffa0fb77
            ff644f12 ff0594ea fffb928e ff80d582 ff80b573 ffb15bb2 fffaf014 fffaf014
            ff1e8cdc ff1e8cdc fffaf014 fffaf014 ff775426 ff8b56a8 ff972927 ff9b55fa
            ff2ed7a5 ff51abd3 ff6096c5 fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014
            fffaf014 ff369296 ffc5194e ff580357 ff74dabd ff7c2d95 ffeb8e67 ff579592
            fffaf014 fffaf014 ff1e8cdc ff1e8cdc fffaf014 fffaf014 ffcae211 ff2fa899
            ffb39e54 ff10821c ff1687d1 ff3f5e70 fff6ec1a fffaf014 fef2eb1a ff1e8cdc
            ff1e8cdc fe90bf72 fffaf014 fffaf014 fffaf014 ffe4ac5b ffed93ce ffbebc16
            fffaf014 fffaf014 fffaf014 fe84b97e ff1e8cdc ff1e8cdc ff1e8cdc fea5c960
            fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fffaf014 fe9bc468
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc fe61aa9e feb7d14f fee3e527
            fffaf014 fee1e429 feb3d052 fe5aa7a3 ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
            ff1e8cdc ff1e8cdc ff1e8cdc ff1e8cdc
        """,
    },

)


def _hex_pixels(adatok: str, szelesseg: int, magassag: int) -> np.ndarray:
    """A fixture hexaszövegét alakítja sorfolytonos képponttömbbé."""
    ertekek = [int(pixel, 16) for pixel in adatok.split()]
    assert len(ertekek) == szelesseg * magassag
    return np.asarray(ertekek, dtype=np.uint32).reshape(magassag, szelesseg)


def _eset_bajtra_egyezik_a_nativ_rgb_kimenettel(eset: dict[str, object]) -> bool:
    szelesseg = eset['width']
    magassag = eset['height']
    forras_hex = eset.get('source_rgb_hex')
    if forras_hex is None:
        kep = np.empty((magassag, szelesseg, 3), dtype=np.uint8)
        kep[:] = eset['source_rgb']
    else:
        forras = _hex_pixels(forras_hex, szelesseg, magassag)
        kep = np.stack(((forras >> 16) & 0xff, (forras >> 8) & 0xff, forras & 0xff), axis=-1).astype(np.uint8)

    eredmeny = draw_border(
        kep,
        eset['outer'],
        eset['inner'],
        eset['outer_thickness'],
        eset['inner_thickness'],
        eset['radius'],
    )
    vart_argb = _hex_pixels(
        eset['native_argb_hex'],
        szelesseg + 2 * (eset['outer_thickness'] + eset['inner_thickness']),
        magassag + 2 * (eset['outer_thickness'] + eset['inner_thickness']),
    )
    vart_rgb = np.stack(
        ((vart_argb >> 16) & 0xff, (vart_argb >> 8) & 0xff, vart_argb & 0xff),
        axis=-1,
    ).astype(np.uint8)

    return np.array_equal(eredmeny, vart_rgb)


def test_draw_border_bajtra_egyezik_a_15_mert_nativ_mmx_esettel():
    eltero_esetek = [
        eset['name']
        for eset in _MMX_ESETEK
        if not _eset_bajtra_egyezik_a_nativ_rgb_kimenettel(eset)
    ]

    assert not eltero_esetek, f"Eltérő natív MMX-kimenet: {', '.join(eltero_esetek)}"
