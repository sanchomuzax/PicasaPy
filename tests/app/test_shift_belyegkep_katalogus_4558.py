"""#4558: a Shift-tel előhozott MÁSODLAGOS effektek bélyegképe is készül.

A kilenc kétmódú csempe másodlagos kulcsa (`ui-audit-editor.md`, „A második
tokent a SHIFT billentyű kapcsolja”) mind szerepel a bélyegkép-katalógusban,
és mindegyikre valódi (nem helyőrző) kép készül.

⚠️ Spec szerint azonos kezelőjű párok (ezeknél a bélyegkép képpontra AZONOS,
ezért nem képpont-eltérést állítunk, hanem azt, hogy a kulcs külön
katalóguselem; a csempe kulcsváltását a QML-teszt méri):
- `unsharp` ↔ `unsharp2` — `filters-decoded.md` 463. sor: „`unsharp=1` =
  `unsharp2=1,0.600000` — bitre azonos”;
- `glow` ↔ `glow2` — `filters-decoded.md` 2229. sor („`glow` = `glow2`”,
  ugyanaz a kezelő, `0x008f8f70`) és `picasa-ini-format.md` 174. sor.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from picasapy.app.effect_thumbnails import EFFECT_NAMES
from picasapy.index import open_index, photos_in_folder, sync_tree

#: (elsődleges, másodlagos) — a csempe-tábla szerint.
PAROK = [
    ("unsharp2", "unsharp"),
    ("picnikgrain", "grain"),
    ("picniktint", "tint"),
    ("glow2", "glow"),
    ("dir_tint", "radtint"),
    ("heatmap", "nightvision"),
    ("vignette", "matte"),
    ("pixelate", "picnikfocalpixelate"),
    ("border", "roundededges"),
]
#: filters-decoded.md:463 és :2229 szerint bitre azonos párok
SPEC_BITRE_AZONOS = {("unsharp2", "unsharp"), ("glow2", "glow")}


@pytest.fixture
def szolgaltato(qt_app, tmp_path):
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider

    lib = tmp_path / "kepek"
    lib.mkdir()
    # texturált, színes kép: sima felületen a pixelate/glow párok
    # értelmetlenül azonosak lennének
    y, x = np.indices((200, 320), dtype=np.uint16)
    rgb = np.empty((200, 320, 3), dtype=np.uint8)
    rgb[..., 0] = (x * 3 + y) % 256
    rgb[..., 1] = (y * 2 + x // 2) % 256
    rgb[..., 2] = ((x // 16 + y // 16) % 2) * 220 + 20
    Image.fromarray(rgb, "RGB").save(
        lib / "a.jpg", format="JPEG", quality=95, subsampling=0
    )
    with open_index(tmp_path / "i.db") as conn:
        sync_tree(conn, lib)
        rekordok = photos_in_folder(conn, lib)
    regiszter = {str(r.id): r for r in rekordok}
    return EffectThumbnailProvider(regiszter.get), str(rekordok[0].id)


def _bajtok(kep) -> bytes:
    return kep.convertToFormat(kep.Format.Format_RGB888).constBits().tobytes()


@pytest.mark.parametrize("elso,masodik", PAROK)
def test_minden_masodlagos_kulcs_szerepel_a_katalogusban(elso, masodik):
    assert elso in EFFECT_NAMES
    assert masodik in EFFECT_NAMES


@pytest.mark.parametrize("elso,masodik", PAROK)
def test_minden_masodlagos_kulcsra_valodi_belyegkep_keszul(
    szolgaltato, elso, masodik
):
    prov, fid = szolgaltato
    kep = prov.requestImage(f"{fid}/{masodik}", None, None)
    assert not kep.isNull()
    assert (kep.width(), kep.height()) != (16, 16), f"{masodik}: helyőrző jött"


@pytest.mark.parametrize(
    "elso,masodik", [p for p in PAROK if p not in SPEC_BITRE_AZONOS]
)
def test_a_masodlagos_belyegkep_elter_az_elsodlegestol(szolgaltato, elso, masodik):
    prov, fid = szolgaltato
    a = prov.requestImage(f"{fid}/{elso}", None, None)
    b = prov.requestImage(f"{fid}/{masodik}", None, None)
    assert _bajtok(a) != _bajtok(b), f"{elso} és {masodik} képe azonos"


@pytest.mark.parametrize("elso,masodik", sorted(SPEC_BITRE_AZONOS))
def test_a_spec_szerint_azonos_par_kulon_kulcs_de_azonos_kep(
    szolgaltato, elso, masodik
):
    """A KULCS külön katalóguselem; a képpont-egyezést a spec írja elő."""
    prov, fid = szolgaltato
    assert elso in EFFECT_NAMES and masodik in EFFECT_NAMES and elso != masodik
    a = prov.requestImage(f"{fid}/{elso}", None, None)
    b = prov.requestImage(f"{fid}/{masodik}", None, None)
    assert _bajtok(a) == _bajtok(b)
