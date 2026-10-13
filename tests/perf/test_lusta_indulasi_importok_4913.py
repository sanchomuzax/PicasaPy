"""A ritka műveletek moduljai az első használatig maradjanak ki (#4913)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_LELTAR_PROGRAM = r"""
import json
import sys

import picasapy.app.application

py_fajlok = {
    getattr(modul, "__file__", None) or ""
    for modul in list(sys.modules.values())
    if getattr(modul, "__file__", None)
}
ritka = sorted(
    nev
    for nev in sys.modules
    if nev.startswith((
        "picasapy.collage.",
        "picasapy.dedup.",
        "picasapy.printing.",
        "picasapy.webexport.",
        "picasapy.mailer.",
        "picasapy.pmpimport.",
    ))
)
print(json.dumps({"python_fajlok": len(py_fajlok), "ritka": ritka}))
"""
_DEDUP_IMPORT_PROGRAM = r"""
import json
import sys

import picasapy.app.dedup_controller

print(json.dumps(sorted(
    nev for nev in sys.modules
    if nev.startswith("picasapy.dedup.")
    and nev != "picasapy.dedup.fastkey"
)))
"""

_ELSO_HASZNALATIG_KIHAGYANDO = {
    "picasapy.collage.contact_sheet",
    "picasapy.collage.frames",
    "picasapy.collage.multi_exposure",
    "picasapy.collage.packing",
    "picasapy.collage.regular_grid",
    "picasapy.dedup.api",
    "picasapy.dedup.exact",
    "picasapy.dedup.originhash",
    "picasapy.dedup.phash",
    "picasapy.dedup.similar",
    "picasapy.dedup.slowkey",
    "picasapy.printing.contact_sheet",
    "picasapy.printing.dpi",
    "picasapy.printing.grid_layout",
    "picasapy.printing.layout",
    "picasapy.printing.options",
    "picasapy.printing.resample",
    "picasapy.webexport.catalog",
    "picasapy.webexport.context",
    "picasapy.webexport.engine",
    "picasapy.webexport.images",
    "picasapy.webexport.sizes",
    "picasapy.webexport.tpl_lang",
    "picasapy.mailer.mapi",
    "picasapy.pmpimport.db3_atvetel",
    "picasapy.pmpimport.importer",
    "picasapy.pmpimport.table",
}


def _futtasd_importot(program: str):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_REPO / "src"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env["PYTHONUTF8"] = "1"
    process = subprocess.run(
        [sys.executable, "-c", program],
        cwd=_REPO,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert process.returncode == 0, process.stderr[-2000:]
    return json.loads(process.stdout.strip().splitlines()[-1])


def _indulasi_leltar() -> dict:
    return _futtasd_importot(_LELTAR_PROGRAM)


def test_ritka_csomagok_az_alkalmazas_elso_hasznalataig_kimaradnak():
    leltar = _indulasi_leltar()
    betoltve = set(leltar["ritka"])
    betoltve_maradjon = sorted(_ELSO_HASZNALATIG_KIHAGYANDO & betoltve)

    assert not betoltve_maradjon, (
        "ritka csomagok töltődtek be az alkalmazás modul-importjakor: "
        f"{betoltve_maradjon}"
    )
    # A helyi alapmérés 685 Python-fájl volt (#4913). A plafon ettől még
    # külön őrként 700 marad a test_indulas_io_terheles_1653.py fájlban.
    assert leltar["python_fajlok"] <= 655, (
        "az indulási importlánc nem csökkent legalább 30 modullal a helyi "
        f"685-ös alapméréshez képest: {leltar['python_fajlok']}"
    )


def test_dedup_algoritmusok_a_kereses_elso_hasznalataig_kimaradnak():
    betoltve = _futtasd_importot(_DEDUP_IMPORT_PROGRAM)

    assert not betoltve, (
        "a DedupController-modul betöltötte a dedup-magot az első keresés "
        f"előtt: {betoltve}"
    )
