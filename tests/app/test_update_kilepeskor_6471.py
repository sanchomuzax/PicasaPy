"""#6471: a kilépéskori frissítésnek látható nyoma van, és a sorsa kiderül.

A tulajdonos (2026-11-03): a „Telepítés kilépéskor” gomb „nem csinál
semmit”, a felirata értelmezhetetlen. A gomb most „Frissítés kilépéskor”, a
megnyomása után a verziójelző mutatja, hogy a frissítés vár, és a #6458
eredményjelzője már a gomb megnyomásakor „vár” állapotba kerül: ha a segéd
el sem indul vagy félúton leáll, a következő indulás ezt is kiírja.
"""

from __future__ import annotations

import json

from picasapy.app import update_eredmeny
from types import SimpleNamespace

from picasapy.app import update_manager
from tests.app.test_frissitoseged_indulas_6458 import _vezerlo


def _jelzo(monkeypatch, tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    monkeypatch.setattr(update_eredmeny, "jelzo_utvonal", lambda: jelzo)
    return jelzo


def test_a_gomb_utan_a_frissites_varakozik_es_a_jelzo_rogziti(monkeypatch, tmp_path):
    jelzo = _jelzo(monkeypatch, tmp_path)
    monkeypatch.setattr(update_manager, "_platform", lambda: "win32")
    controller, install_dir = _vezerlo(monkeypatch, tmp_path)
    exe = install_dir / "PicasaPy.exe"
    monkeypatch.setattr(update_manager, "_futtato", SimpleNamespace(executable=str(exe)))
    monkeypatch.setattr(update_manager, "_inditsd_a_segedet", lambda _args, **_kw: True)

    assert controller.installWhenExiting(False) is True

    assert controller.installScheduled is True
    adat = json.loads(jelzo.read_text(encoding="utf-8"))
    assert adat["ok"] == update_eredmeny.NEM_FUTOTT
    assert adat["vart"] == controller.availableVersion


def test_ha_a_seged_nem_indul_nincs_varakozo_jelzo(monkeypatch, tmp_path):
    jelzo = _jelzo(monkeypatch, tmp_path)
    monkeypatch.setattr(update_manager, "_platform", lambda: "win32")
    controller, install_dir = _vezerlo(monkeypatch, tmp_path)
    exe = install_dir / "PicasaPy.exe"
    monkeypatch.setattr(update_manager, "_futtato", SimpleNamespace(executable=str(exe)))
    monkeypatch.setattr(update_manager, "_inditsd_a_segedet", lambda _args, **_kw: False)

    assert controller.installWhenExiting(False) is False

    assert controller.installScheduled is False
    assert not jelzo.exists(), "a sikertelen indítás után nincs mire várni"


def test_el_sem_indult_seged_a_kovetkezo_indulaskor_kiderul(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird_varakozik(jelzo, "1.0.30")

    assert update_eredmeny.olvasd_es_torold(jelzo, "1.0.29") == update_eredmeny.NEM_FUTOTT
    assert not jelzo.exists()


def test_sikeres_jelzes_de_regi_verzio_fut(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird_varakozik(jelzo, "1.0.30")
    update_eredmeny.ird(jelzo, siker=True, ok="")

    assert update_eredmeny.olvasd_es_torold(jelzo, "1.0.29") == update_eredmeny.VERZIO


def test_sikeres_frissites_utan_csend(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird_varakozik(jelzo, "1.0.30")
    update_eredmeny.ird(jelzo, siker=True, ok="")

    assert update_eredmeny.olvasd_es_torold(jelzo, "1.0.30") == ""


def test_a_seged_kudarca_felulirja_a_varakozast(tmp_path):
    jelzo = tmp_path / "frissites-eredmeny.json"
    update_eredmeny.ird_varakozik(jelzo, "1.0.30")
    update_eredmeny.ird(jelzo, siker=False, ok=update_eredmeny.FAJL_FOGLALT)

    assert update_eredmeny.olvasd_es_torold(jelzo, "1.0.29") == update_eredmeny.FAJL_FOGLALT
