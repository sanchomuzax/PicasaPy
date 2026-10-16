"""#4422: a valódi GPU-próba csak elérhető Waylandon indulhat."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from tests.app.qml_functional import test_gpu_finetune_fokusz_3755 as gpu_test

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="A Wayland AF_UNIX socketes környezetpróba Windows alatt nem értelmezhető.",
)


class _TiltottSocket:
    def settimeout(self, _timeout: float) -> None:
        pass

    def connect(self, _path: str) -> None:
        raise PermissionError("Operation not permitted")

    def close(self) -> None:
        pass


class _ElertSocket:
    def settimeout(self, _timeout: float) -> None:
        pass

    def connect(self, _path: str) -> None:
        pass

    def close(self) -> None:
        pass


def _wayland_alap(monkeypatch, tmp_path, socket_factory) -> None:
    socket_path = tmp_path / "wayland-0"
    socket_path.touch()
    monkeypatch.setattr(gpu_test, "_HEADLESS", tmp_path)
    monkeypatch.setattr(gpu_test, "_socket_letrehoz", socket_factory)


def test_a_zarolt_wayland_socketnel_kihagyja_a_gpu_alfolyamatot(
    monkeypatch, tmp_path
) -> None:
    _wayland_alap(monkeypatch, tmp_path, lambda *_args: _TiltottSocket())
    monkeypatch.setattr(
        gpu_test,
        "_alfolyamat_futtat",
        lambda *_args, **_kwargs: pytest.fail("az elérhetetlen socketet kihagyná"),
    )

    with pytest.raises(pytest.skip.Exception, match="nem érhető el"):
        gpu_test.test_valodi_gpun_egerhuzassal(tmp_path)


def test_a_gpu_alfolyamat_nem_orokli_a_szoftveres_qt_quick_backendet(
    monkeypatch, tmp_path
) -> None:
    _wayland_alap(monkeypatch, tmp_path, lambda *_args: _ElertSocket())
    monkeypatch.setenv("QT_QUICK_BACKEND", "software")
    futtatas = {}

    def _futtat(*_args, **kwargs):
        futtatas["kornyezet"] = kwargs["env"]
        return SimpleNamespace(returncode=0, stdout="1 passed\n", stderr="")

    monkeypatch.setattr(gpu_test, "_alfolyamat_futtat", _futtat)
    gpu_test.test_valodi_gpun_egerhuzassal(tmp_path)

    assert "QT_QUICK_BACKEND" not in futtatas["kornyezet"]
