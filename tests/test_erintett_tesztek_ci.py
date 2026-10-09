"""PR-en csak az érintett app-tesztek futnak (`run_tests.erintett_app_tesztek`).

2026-10-09: 41 nyitott PR állt, mert minden PR a teljes készletet futtatta
négy darabban (PR-enként ~70 futtatóperc). A teljes készlet a main-en fut.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_UT = Path(__file__).resolve().parents[1] / "scripts" / "run_tests.py"
_spec = importlib.util.spec_from_file_location("run_tests_erintett", _UT)
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)

_TESZTEK = [f"tests/app/test_t{i}.py" for i in range(10)]
_TARTALOM = {
    "tests/app/test_t0.py": "PhotoViewer betöltése",
    "tests/app/test_t1.py": "edit_controller.EditController",
    "tests/app/test_t2.py": "picasapy_hu.ts fordítás",
}


def _olvas(ut: str) -> str:
    return _TARTALOM.get(ut, "semmi")


def _valaszt(valtozott):
    return rt.erintett_app_tesztek(_TESZTEK, valtozott, _olvas)


def test_a_qml_valtozas_a_ra_hivatkozo_tesztet_valasztja():
    assert _valaszt(["src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"]) == [
        "tests/app/test_t0.py"
    ]


def test_a_valtozott_tesztfajl_maga_is_fut():
    valasztott = _valaszt(["tests/app/test_t7.py", "changelog.d/1.md"])
    assert valasztott == ["tests/app/test_t7.py"]


def test_forditas_valtozasnal_az_i18n_tesztek_futnak():
    assert "tests/app/test_t2.py" in _valaszt(["src/picasapy/app/i18n/picasapy_hu.ts"])


def test_kozos_seged_vagy_nem_app_forras_a_teljes_keszletet_adja():
    for ut in (
        "tests/app/qml_functional/_fomenu_4420_menu.py",
        "tests/app/conftest.py",
        "src/picasapy/render/chain.py",
        "pyproject.toml",
    ):
        assert _valaszt([ut]) == _TESZTEK, ut


def test_ismeretlen_valtozasnal_a_teljes_keszlet():
    assert _valaszt(None) == _TESZTEK
    assert _valaszt([]) == _TESZTEK


def test_tul_szeles_kivalasztasnal_a_teljes_keszlet():
    mind = {t: "Main" for t in _TESZTEK}
    assert rt.erintett_app_tesztek(
        _TESZTEK, ["src/picasapy/app/qml/Main.qml"], lambda u: mind[u]
    ) == _TESZTEK


def test_a_futtato_es_a_workflow_valtozasa_nem_teljes_keszlet():
    assert _valaszt(["scripts/run_tests.py", ".github/workflows/ci.yml"]) == []


def test_a_darab_fetch_depth_kifejezese_nem_esik_vissza_1_re():
    """2026-10-09: a `&& 0 || 1` mindig 1-et adott (a 0 hamis), így a PR-darab
    alap nélkül maradt, és a teljes készletet futtatta egy darabban."""
    wf = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "teszt-darabok.yml"
    sor = next(s for s in wf.read_text(encoding="utf-8").splitlines()
               if s.strip().startswith("fetch-depth:"))
    assert "&& 0 ||" not in sor and "'0'" in sor, sor
