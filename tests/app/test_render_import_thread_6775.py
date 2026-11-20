"""#6775 őre: a render-csomag első betöltése a fő szálon, az első képkocka után,
az indulási háttérmunka előtt történik."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

from picasapy import lazy_import

REPO = Path(__file__).resolve().parents[2]


def test_az_elotoltes_az_inditas_elott_fut(monkeypatch):
    naplo: list[str] = []
    monkeypatch.setattr(lazy_import, "render_elore_betolt", lambda: naplo.append("render"))

    lazy_import.render_elotoltese_utan(lambda: naplo.append("inditas"))

    assert naplo == ["render", "inditas"]


def test_az_elotoltes_tenyleg_betolti_a_render_csomagot():
    program = (
        "import sys\n"
        "from picasapy.lazy_import import render_elore_betolt\n"
        "elotte = 'picasapy.render' in sys.modules\n"
        "render_elore_betolt()\n"
        "print(elotte, 'picasapy.render' in sys.modules)\n"
    )
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1"}
    ki = subprocess.run(
        [sys.executable, "-c", program], env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=120, check=True,
    )
    assert ki.stdout.split() == ["False", "True"]


def test_az_elso_kepkocka_utani_callback_az_elotoltesen_at_indit():
    forras = (REPO / "src/picasapy/app/application.py").read_text(encoding="utf-8")
    run = next(
        n for n in ast.walk(ast.parse(forras))
        if isinstance(n, ast.FunctionDef) and n.name == "run"
    )
    elso_kep = next(
        n for n in ast.walk(run)
        if isinstance(n, ast.FunctionDef) and n.name == "_on_first_frame"
    )
    utemezett = [
        h.args[1] for h in ast.walk(elso_kep)
        if isinstance(h, ast.Call) and isinstance(h.func, ast.Attribute)
        and h.func.attr == "singleShot" and len(h.args) >= 2
    ]
    assert any(
        isinstance(cb, ast.Lambda) and isinstance(cb.body, ast.Call)
        and isinstance(cb.body.func, ast.Name)
        and cb.body.func.id == "render_elotoltese_utan"
        and [a.id for a in cb.body.args if isinstance(a, ast.Name)] == ["_start_and_finish"]
        for cb in utemezett
    ), "az első képkocka utáni indítás a render-előtöltésen át fusson"


def test_az_elonezet_elso_render_importja_a_munkaszal_inditasa_elott_tortenik():
    program = r'''
import contextvars
import json
import sys
import threading
from importlib.abc import MetaPathFinder

from picasapy import lazy_import
from picasapy.app.edit_controller_preview_mixin import EditControllerPreviewMixin

assert "picasapy.render" not in sys.modules
main_thread = threading.get_ident()
import_threads = []

class RenderThreadGuard(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "picasapy.render":
            import_threads.append(threading.get_ident())
            if import_threads[-1] != main_thread:
                raise RuntimeError("a render első importja munkaszálról indult")
        return None

sys.meta_path.insert(0, RenderThreadGuard())

class Signal:
    def emit(self, *_args):
        pass

class Provider:
    def register(self, **_kwargs):
        lazy_import.lazy_callable("picasapy.render", "apply_filters")()

class Host:
    _preview_job = 0
    _provider = Provider()
    _previewRendered = Signal()
    editSaveFailed = Signal()

    def _start_background(self, worker, name):
        self.thread = threading.Thread(target=worker, name=name)
        self.thread.start()
        self.thread.join(timeout=60)
        assert not self.thread.is_alive(), "az előnézeti worker nem állt le"

    def _finish_preview_worker(self):
        pass

host = Host()
EditControllerPreviewMixin._start_preview_worker(
    host, (0, {}, contextvars.copy_context())
)
print(json.dumps({"main": main_thread, "imports": import_threads}))
'''
    env = {**os.environ, "PYTHONPATH": str(REPO / "src"), "PYTHONUTF8": "1"}
    ki = subprocess.run(
        [sys.executable, "-c", program], env=env, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert ki.returncode == 0, ki.stderr or ki.stdout
    eredmeny = json.loads(ki.stdout)
    assert eredmeny["imports"] == [eredmeny["main"]]
