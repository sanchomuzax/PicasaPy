"""A `tools/golden/make_golden_kit.py` `synthetic_photos()` zajmentesítésének
tesztje (#278).

Háttér: a `synthetic_photos()` a szintetikus fotó-alapképekhez ±12
egyenletes zajt kevert (`rng.integers(-12, 12, ...)`). Ez a zaj a JPEG
újrakódolás (export/összehasonlítás körökben ismétlődő tömörítés) után
felfújja a golden-diffet: a chart-alapképek (élek, ábrák) pixelhűek
maradnak, a zajos fotó-alapképek viszont már küszöb feletti eltérést
mutatnak, holott a szűrő-implementáció maga helyes. A zaj eltávolítása
után a fotó-alapképeknek is stabilnak ("simának") kell maradniuk.

Mérőszám: a szomszédos (vízszintesen egymás melletti) pixelek abszolút
különbségének átlaga. A sima színátmenetes/elmosott alapon ennek a régi,
zajos kódnál kb. 6 körüli, zaj nélkül kb. 0-hoz közeli — ez a teszt tehát
BUKIK a régi (zajos) kódon, és ÁTMEGY az újon (RED → GREEN, #278)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "golden" / "make_golden_kit.py"
)


def _load_module():
    """A tools/golden/make_golden_kit.py betöltése fájlútvonalról (nincs a
    pythonpath-on — szándékosan eszköz, nem csomag)."""
    spec = importlib.util.spec_from_file_location("make_golden_kit", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("make_golden_kit", module)
    spec.loader.exec_module(module)
    return module


mgk = _load_module()


def _mean_horizontal_neighbor_diff(image: np.ndarray) -> float:
    """A vízszintesen szomszédos pixelek abszolút eltérésének átlaga —
    sima (zajmentes) színátmenetes/elmosott képen ennek közel nullának
    kell lennie; egyenletes zaj hozzáadása ezt az értéket a zaj
    nagyságrendjéig megemeli."""
    diff = np.abs(
        image[:, 1:, :].astype(np.int16) - image[:, :-1, :].astype(np.int16)
    )
    return float(diff.mean())


class TestSyntheticPhotosZajmentes:
    """#278: a synthetic_photos() JPEG-round-trip után is stabil (sima)
    alapképeket ad — a korábbi ±12-es egyenletes zaj eltávolítása/erős
    csökkentése után."""

    @pytest.mark.parametrize("index", [0, 1, 2])
    def test_szomszedos_pixelek_eltérése_kicsi(
        self, tmp_path: Path, index: int
    ) -> None:
        paths = mgk.synthetic_photos(tmp_path, n=1, start=index)
        image = mgk.imread_unicode(paths[0])
        assert image is not None

        atlag_elteres = _mean_horizontal_neighbor_diff(image)

        # a régi ±12-es zajjal ez az érték kb. 6 körüli volt (JPEG
        # round-trip után is) — az új, zajmentes/enyhe verzióban jóval
        # 1.0 alatt kell maradnia
        assert atlag_elteres < 1.0, (
            "a szintetikus fotó-alapkép szomszédos pixelei túl zajosak "
            f"(átlagos eltérés={atlag_elteres:.3f}) — #278: a synthetic_"
            "photos() zaja felfújja a golden-diffet"
        )

    def test_determinizmus_megmarad(self, tmp_path: Path) -> None:
        """A seed (115+i) alapú determinizmus a zaj eltávolítása után is
        megmarad: két azonos indexű generálás bitre azonos képet ad."""
        a_dir = tmp_path / "a"
        b_dir = tmp_path / "b"
        a_dir.mkdir()
        b_dir.mkdir()
        elso = mgk.synthetic_photos(a_dir, n=1, start=3)
        masodik = mgk.synthetic_photos(b_dir, n=1, start=3)
        img1 = mgk.imread_unicode(elso[0])
        img2 = mgk.imread_unicode(masodik[0])
        assert np.array_equal(img1, img2)
