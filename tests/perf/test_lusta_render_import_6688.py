"""A képszerkesztő csomag az első ablakkép előtt kimarad (#6688).

Az őr a #4913 mintáját követi: NEM időt mér, hanem a betöltött modulok
listáját olvassa ki egy külön processzben. Három szinten nézi meg:

1. az `application` modul importja után (a legolcsóbb próba);
2. a valódi indítás végén, amikor a felület (a vezérlők, a QML-motor, a
   főablak) már felépült, de az eseményciklus még el sem indult, vagyis az
   ablak első képkockája még nem rajzolódott ki;
3. a lustává tett modulok külön-külön importja után.

A 2. pont azért kell, mert az `application` importja önmagában keveset
mond: a vezérlők (`EditController`, `ThumbnailProvider`, ...) lustán
töltődnek be, és a `run()` az első képkocka előtt példányosítja őket, a QML
pedig az olvasott tulajdonságaikon át futtat kódot. Az a modul, amelyik a
`render` csomagot felhúzza, a felületen nem látszik, csak az indulási időben.

⚠️ Amit az őr NEM mér: azt, hogy az indulás gyorsabb lett-e, és azt, hogy a
csomag az ablak megjelenése UTÁN mikor töltődik be.

Az indulási úton álló, a renderelő igazságforrásából RÖGZÍTETT adatokat (a
régi effektek kínálata, az egygombos szűrők, a képpontot mozdító módok) a
`TestRogzitettAdatok` egyezteti a renderelővel: ha a renderelő kínálata
változik, ez bukik, és az érintett rögzített listát kell frissíteni.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_JELOLO = "PICASAPY_RENDER_LELTAR "

_IMPORT_PROGRAM = r"""
import json
import sys

import picasapy.app.application

print(json.dumps({
    "render": sorted(
        nev for nev in sys.modules if nev.startswith("picasapy.render")
    ),
}))
"""

#: A valódi indítás: a `run()` a felület felépülése UTÁN, az eseményciklus
#: indítása ELŐTT hívja a füstpróba-lépést (`--onellenorzes`). Ennek
#: pillanatában olvassuk ki a modullistát, majd a lépés rendesen lefut.
_INDITAS_PROGRAM = r"""
import json
import sys

import picasapy.app.application as alkalmazas

alkalmazas._ensure_application_helpers()
eredeti = alkalmazas._startup_step_smoke_test


def figyelo(state):
    leltar = {
        "render": sorted(
            nev for nev in sys.modules if nev.startswith("picasapy.render")
        ),
    }
    print("__JELOLO__" + json.dumps(leltar), flush=True)
    return eredeti(state)


alkalmazas._startup_step_smoke_test = figyelo
raise SystemExit(alkalmazas.run(["picasapy", "--onellenorzes", sys.argv[1]]))
""".replace("__JELOLO__", _JELOLO)

#: Modulonként: az első olyan modul nevét adja, amelynek importja után a
#: `picasapy.render` már betöltődött.
_MODULONKENTI_PROGRAM = r"""
import importlib
import json
import sys

elso_tettes = None
for nev in json.loads(sys.argv[1]):
    importlib.import_module(nev)
    if "picasapy.render" in sys.modules:
        elso_tettes = nev
        break
print(json.dumps(elso_tettes))
"""

#: A lusta hivatkozások az első HÍVÁSKOR betöltik a csomagot (az őr nem a
#: modulok megsérülésével zöld).
_ELSO_HASZNALAT_PROGRAM = r"""
import json
import sys

from picasapy.app import edit_preview
from picasapy.thumbs import cache

elotte = "picasapy.render" in sys.modules
edit_preview.chain_flags(["autolight"])
utana = "picasapy.render.registry" in sys.modules
cache.normalize_crop_ops((), None)
print(json.dumps([elotte, utana, "picasapy.render.chain" in sys.modules]))
"""

#: Az alkalmazás renderelője csak a tényleges szerkesztői előnézet indításakor
# töltődik be, és egy valós effekt módosítja is a képpontokat.
_SZERKESZTO_HASZNALAT_PROGRAM = r"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtGui import QGuiApplication

app = QGuiApplication([])
ut = Path(sys.argv[1]) / "photo.jpg"
Image.new("RGB", (16, 12), (80, 110, 130)).save(ut)

from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.app.edit_controller import EditController

provider = EditPreviewProvider()
controller = EditController(provider)
render_elotte = "picasapy.render" in sys.modules
controller.beginEdit("photo-1", str(ut))
assert controller.waitForBackgroundWorkers(30.0), "a kezdeti előnézet nem állt le"
app.processEvents()
elotte = provider.requestImage("photo-1", None, None)
elotte_pixel = elotte.pixelColor(0, 0).getRgb()

controller.applyEffect("sepia")
assert controller.waitForBackgroundWorkers(30.0), "az effekt előnézete nem állt le"
app.processEvents()
utana = provider.requestImage("photo-1", None, None)
utana_pixel = utana.pixelColor(0, 0).getRgb()

print(json.dumps({
    "render_before_editor": render_elotte,
    "render_after_effect": "picasapy.render" in sys.modules,
    "effect_chain": controller.effectChain,
    "pixel_changed": elotte_pixel != utana_pixel,
    "image_size": [utana.width(), utana.height()],
}))
"""

#: A lustává tett modulok: egyik importja sem húzhatja be a render csomagot.
_LUSTA_MODULOK = (
    "picasapy.app.application",
    "picasapy.app.edit_controller",
    "picasapy.app.edit_preview",
    "picasapy.app.edit_preview_cache",
    "picasapy.app.edit_preview_redeye",
    "picasapy.app.effect_thumbnails",
    "picasapy.app.effect_params",
    "picasapy.app.effect_slice",
    "picasapy.app.effect_slice_render",
    "picasapy.app.edit_action_names",
    "picasapy.app.display_mode_paint",
    "picasapy.app.display_photo_provider",
    "picasapy.app.theme_palette",
    "picasapy.app.timeline_background",
    "picasapy.app.save_controller",
    "picasapy.app.paint_mask_controller",
    "picasapy.app.print_controller_source_mixin",
    "picasapy.export",
    "picasapy.export.exporter",
    "picasapy.metadata.exif_belyegkep",
    "picasapy.thumbs.cache",
)


def _kornyezet(profil: Path | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_REPO / "src"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env["PYTHONUTF8"] = "1"
    if profil is not None:
        env.update(
            {
                "QT_QPA_PLATFORM": "offscreen",
                "QT_QUICK_BACKEND": "software",
                "PICASAPY_LANG": "en",
                "XDG_CONFIG_HOME": str(profil / ".config"),
                "XDG_DATA_HOME": str(profil / ".local" / "share"),
                "XDG_CACHE_HOME": str(profil / ".cache"),
            }
        )
    return env


def _futtasd(program: str, *args: str, env: dict[str, str], timeout: int):
    return subprocess.run(
        [sys.executable, "-c", program, *args],
        cwd=_REPO,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _utolso_json(process: subprocess.CompletedProcess):
    assert process.returncode == 0, process.stderr[-2000:]
    return json.loads(process.stdout.strip().splitlines()[-1])


def test_a_render_az_alkalmazasmodul_importjakor_nem_toltodik_be():
    betoltve = _utolso_json(_futtasd(_IMPORT_PROGRAM, env=_kornyezet(), timeout=120))

    assert not betoltve["render"], (
        "betöltődött az `application` importjakor: "
        f"render={betoltve['render'][:10]}"
    )


def test_a_render_az_elso_ablakkep_elott_nem_toltodik_be(tmp_path: Path):
    konyvtar = tmp_path / "library"
    konyvtar.mkdir()
    profil = tmp_path / "profile"
    profil.mkdir()

    process = _futtasd(
        _INDITAS_PROGRAM,
        str(konyvtar),
        env=_kornyezet(profil),
        timeout=int(os.environ.get("PICASAPY_STARTUP_SMOKE_TIMEOUT", "120")),
    )
    sorok = [
        sor[len(_JELOLO):]
        for sor in process.stdout.splitlines()
        if sor.startswith(_JELOLO)
    ]
    assert sorok, (
        "a felület felépülése nem jutott el a mérési pontig "
        f"(kilépési kód: {process.returncode}): {process.stderr[-2000:]}"
    )
    betoltve = json.loads(sorok[-1])

    assert not betoltve["render"], (
        "az ablak első képkockája előtt betöltődött: "
        f"render={betoltve['render'][:10]}"
    )


def test_a_lustava_tett_modulok_importja_nem_huzza_be_a_rendert():
    tettes = _utolso_json(
        _futtasd(
            _MODULONKENTI_PROGRAM,
            json.dumps(list(_LUSTA_MODULOK)),
            env=_kornyezet(),
            timeout=240,
        )
    )

    assert tettes is None, (
        f"a `{tettes}` importja behúzta a `picasapy.render` csomagot"
    )


def test_a_lusta_hivatkozasok_az_elso_hivaskor_betoltik_a_rendert():
    elotte, regiszter, lanc = _utolso_json(
        _futtasd(_ELSO_HASZNALAT_PROGRAM, env=_kornyezet(), timeout=120)
    )

    assert elotte is False, "a render importkor betöltődött"
    assert regiszter is True, "a `chain_flags` hívása nem töltötte be a regisztert"
    assert lanc is True, "a `normalize_crop_ops` hívása nem töltötte be a láncot"


def test_a_szerkeszto_elso_effektje_betolti_es_hasznalja_a_rendert(tmp_path: Path):
    eredmeny = _utolso_json(
        _futtasd(
            _SZERKESZTO_HASZNALAT_PROGRAM,
            str(tmp_path),
            env=_kornyezet(tmp_path / "profile"),
            timeout=120,
        )
    )

    assert eredmeny["render_before_editor"] is False
    assert eredmeny["render_after_effect"] is True
    assert eredmeny["effect_chain"] == "sepia=1;"
    assert eredmeny["pixel_changed"] is True
    assert eredmeny["image_size"] == [16, 12]


class TestRogzitettAdatok:
    """Az indulási úton álló, rögzített másolatok egyeznek a renderelővel."""

    def test_a_regi_effektek_kinalata(self):
        from picasapy.app.edit_controller_shared import _LEGACY_EFFECT_NAMES
        from picasapy.ini.legacy_effects import LEGACY_EFFECT_KEYS
        from picasapy.render.chain import can_offer_filter_control

        szamolt = tuple(
            sorted(key for key in LEGACY_EFFECT_KEYS if can_offer_filter_control(key))
        )

        assert _LEGACY_EFFECT_NAMES == szamolt

    def test_a_can_offer_filter_control_hida_a_renderelovel_egyezik(self):
        from picasapy.app.edit_controller_shared import can_offer_filter_control
        from picasapy.ini.legacy_effects import LEGACY_EFFECT_KEYS
        from picasapy.render.chain import can_offer_filter_control as valodi
        from picasapy.render.registry import FILTER_REGISTRY

        for nev in sorted(LEGACY_EFFECT_KEYS | set(FILTER_REGISTRY) | {"nincs-ilyen"}):
            assert can_offer_filter_control(nev) is valodi(nev), nev

    def test_az_egygombos_szurok(self):
        from picasapy.app.edit_controller_shared import one_click_keys
        from picasapy.render.registry import one_click_keys as valodi

        assert one_click_keys() == valodi()

    def test_a_kepponttot_mozdito_modok(self):
        from picasapy.app.display_mode_paint import (
            _PIXEL_AFFECTING_MODES,
            display_mode_changes_pixels,
        )
        from picasapy.render.display_modes import (
            PIXEL_AFFECTING_MODES,
            display_mode_changes_pixels as valodi,
        )

        assert _PIXEL_AFFECTING_MODES == PIXEL_AFFECTING_MODES
        for mod in (*PIXEL_AFFECTING_MODES, "", "none", "nincs-ilyen"):
            assert display_mode_changes_pixels(mod) is valodi(mod), mod

    def test_az_egyetlen_forras_nevek_azonosak_a_render_ujraexportjaval(self):
        from picasapy.ini import affine, flip, legacy_effects, text_overlay
        from picasapy.render import chain_geometry, chain_policy, text_fonts
        from picasapy.render import flip as render_flip
        from picasapy.render import legacy_effects as render_legacy

        assert chain_geometry.AZONOSSAG is affine.AZONOSSAG
        assert chain_geometry.Matrix is affine.Matrix
        assert chain_policy.DEAD_LEGACY_OPS is legacy_effects.DEAD_LEGACY_OPS
        assert render_legacy.LEGACY_EFFECTS is legacy_effects.LEGACY_EFFECTS
        assert render_legacy.LEGACY_EFFECT_KEYS is legacy_effects.LEGACY_EFFECT_KEYS
        assert text_fonts.DEFAULT_FAMILY is text_overlay.DEFAULT_FAMILY
        for nev in ("FLIP_HORIZONTAL", "FLIP_VERTICAL", "FLIP_MASK", "toggled_flip"):
            assert getattr(render_flip, nev) is getattr(flip, nev), nev

    def test_a_halott_effektek_tovabbra_is_a_katalogus_reszei(self):
        from picasapy.ini.legacy_effects import DEAD_LEGACY_OPS, LEGACY_EFFECT_KEYS

        assert DEAD_LEGACY_OPS <= LEGACY_EFFECT_KEYS


def test_a_regi_nevek_a_lusta_modulokon_tovabbra_is_elerhetok():
    """A modulszintű nevek (a tesztek foltozási pontjai) megmaradtak."""
    from picasapy.app import (
        application,
        edit_action_names,
        edit_preview,
        effect_slice,
        effect_thumbnails,
        save_controller,
    )
    from picasapy.thumbs import cache

    assert callable(application.clear_family_cache)
    assert edit_action_names.ACTION_LABELS["enhance"][0]
    assert effect_slice.EFFECT_VIEW_TYPES["autolight"] == "tone"
    for modul, nevek in (
        (edit_preview, ("apply_filters", "apply_text_overlay", "chain_flags")),
        (effect_thumbnails, ("apply_filters", "normalize_crop_ops")),
        (save_controller, ("apply_filters", "can_render_filter", "apply_flip")),
        (cache, ("apply_filters", "normalize_crop_ops", "elonezeti_arany")),
    ):
        for nev in nevek:
            assert callable(getattr(modul, nev)), f"{modul.__name__}.{nev}"
