"""#6436: az „Újraindítás most” háttérmunka mellett sem vár korlátlanul.

A tulajdonos gépén a frissítés letöltése után az „Újraindítás most” gombra a
homokóra pörgött, de semmi nem történt: a frissítő addig várt, amíg minden
háttérmunka véget ér, és a háttérmunka nem ért véget."""

from __future__ import annotations

from types import SimpleNamespace

from picasapy.app import update_manager
from picasapy.app.busy_registry import get_app_busy_registry, reset_app_busy_registry
from picasapy.app.update_manager import UpdateController
from tests.support.varakozas import var_feltetelre


class _Beallitasok(dict):
    def value(self, key, default=None, type=None):  # noqa: A002
        return self.get(key, default)

    def setValue(self, key, value):  # noqa: N802
        self[key] = value


class _Kliens:
    def latest_release(self):
        raise AssertionError("nem kérdez le kiadást")


def _vezerlo(tmp_path, monkeypatch, esemenyek):
    telepites = tmp_path / "PicasaPy"
    telepites.mkdir()
    (telepites / "PicasaPyUpdateHelper.exe").write_bytes(b"seged")
    monkeypatch.setattr(
        update_manager, "_futtato", SimpleNamespace(executable=str(telepites / "PicasaPy.exe"))
    )
    monkeypatch.setattr(
        update_manager, "_inditsd_a_segedet",
        lambda args, *, emelt: esemenyek.append("seged") or True,
    )
    monkeypatch.setattr(update_manager, "mappa_irhato", lambda _m: True)
    monkeypatch.setattr(update_manager, "_kenyszeritett_kilepes_ha_beragad", lambda: None)
    from PySide6.QtCore import QCoreApplication

    monkeypatch.setattr(QCoreApplication, "quit", staticmethod(lambda: esemenyek.append("quit")))
    vezerlo = UpdateController(
        "1.0.0", settings=_Beallitasok(), client=_Kliens(), schedule=False,
        install_kind="windows",
    )
    vezerlo._download_path = tmp_path / "csomag.zip"
    return vezerlo


def test_futo_hattermunka_mellett_a_hatarido_utan_ujraindul(qt_app, tmp_path, monkeypatch):
    reset_app_busy_registry()
    monkeypatch.setattr(update_manager, "UJRAINDITAS_MAX_VARAKOZAS_MS", 300)
    esemenyek: list[str] = []
    vezerlo = _vezerlo(tmp_path, monkeypatch, esemenyek)
    get_app_busy_registry().begin()
    try:
        assert vezerlo.installWhenExiting(True) is True
        assert esemenyek == [], "azonnal indult, pedig a háttérmunka fut"
        assert var_feltetelre(qt_app, lambda: esemenyek == ["seged", "quit"], 3.0), (
            f"a háttérmunka miatt nem indult újra: {esemenyek}"
        )
    finally:
        get_app_busy_registry().end()
        reset_app_busy_registry()


def test_ha_a_hattermunka_hamar_veget_er_nem_var_a_hataridoig(qt_app, tmp_path, monkeypatch):
    reset_app_busy_registry()
    monkeypatch.setattr(update_manager, "UJRAINDITAS_MAX_VARAKOZAS_MS", 60_000)
    esemenyek: list[str] = []
    vezerlo = _vezerlo(tmp_path, monkeypatch, esemenyek)
    get_app_busy_registry().begin()
    assert vezerlo.installWhenExiting(True) is True
    get_app_busy_registry().end()
    try:
        assert var_feltetelre(qt_app, lambda: esemenyek == ["seged", "quit"], 3.0)
    finally:
        reset_app_busy_registry()


def test_a_probakornyezet_vegtelen_hattermunkat_indithat(qt_app, monkeypatch):
    """A CI önfrissítési próbája ezzel mutatja meg, hogy a soha véget nem érő
    háttérmunka mellett is megtörténik az újraindítás (a tulajdonos esete)."""
    reset_app_busy_registry()
    monkeypatch.setenv("PICASAPY_UPDATE_TEST_DIAGNOSTICS", "1")
    monkeypatch.setenv("PICASAPY_UPDATE_TEST_DIAGNOSTICS_DIR", "")
    monkeypatch.setenv("PICASAPY_UPDATE_TEST_BUSY", "1")
    monkeypatch.setattr(UpdateController, "_write_test_diagnostics", lambda self: None)
    try:
        UpdateController(
            "1.0.0", settings=_Beallitasok(), client=_Kliens(), schedule=False,
            install_kind="windows",
        )
        assert get_app_busy_registry().activeCount == 1
    finally:
        reset_app_busy_registry()


def test_a_csomagmero_a_vegtelen_hattermunkat_kapcsolja():
    from pathlib import Path

    forras = (
        Path(__file__).resolve().parents[2] / "packaging/windows/csomag_meres_frissites.py"
    ).read_text(encoding="utf-8")
    assert 'env["PICASAPY_UPDATE_TEST_BUSY"] = "1"' in forras
