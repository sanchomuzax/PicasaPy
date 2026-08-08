"""#26 (1. lépcső): a YuNet arc-detektor hiánytűrő becsomagolása.

KÖTELEZŐ szabály (issue #26): a modell hiányában futó eset MINDIG lefut
(CI-ben nincs garantált modellfájl) — a modellt igénylő méret/alak-
ellenőrzés `skipif`-fel kihagyva, ha a fájl ténylegesen nincs jelen."""

from __future__ import annotations

import logging

import numpy as np
import pytest

from picasapy.faces.detector import (
    FaceDetector,
    download_model,
    resolve_model_path,
)


class TestMissingModel:
    """A modell hiánya SOHA nem omlik/dob — tisztán kikapcsol."""

    def test_unavailable_without_model_file(self, tmp_path):
        detector = FaceDetector(model_path=tmp_path / "nincs-ilyen.onnx")
        assert detector.available is False

    def test_detect_returns_empty_tuple_without_model(self, tmp_path):
        detector = FaceDetector(model_path=tmp_path / "nincs-ilyen.onnx")
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        assert detector.detect(image) == ()

    def test_detect_survives_none_image(self, tmp_path):
        detector = FaceDetector(model_path=tmp_path / "nincs-ilyen.onnx")
        assert detector.detect(None) == ()

    def test_logs_info_when_no_model_resolvable(self, tmp_path, monkeypatch, caplog):
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.detector.default_model_path",
            lambda: tmp_path / "nincs-ilyen.onnx",
        )
        with caplog.at_level(logging.INFO):
            detector = FaceDetector()
        assert detector.available is False
        assert any("kikapcsolva" in record.message for record in caplog.records)


class TestModelPathResolution:
    def test_none_when_nothing_exists(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.detector.default_model_path",
            lambda: tmp_path / "nincs-ilyen.onnx",
        )
        assert resolve_model_path() is None

    def test_env_var_overrides_default(self, tmp_path, monkeypatch):
        model = tmp_path / "sajat.onnx"
        model.write_bytes(b"nem valodi onnx, csak a letezes szamit")
        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(model))
        assert resolve_model_path() == model

    def test_env_var_pointing_to_missing_file_falls_back(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(tmp_path / "nincs.onnx"))
        monkeypatch.setattr(
            "picasapy.faces.detector.default_model_path",
            lambda: tmp_path / "meg-egy-hianyzo.onnx",
        )
        assert resolve_model_path() is None


class TestDownloadModelNeverBlocksStartup:
    """`download_model` SOHA nem hívódik automatikusan — itt csak azt
    ellenőrizzük, hogy hálózat-hiba esetén sem dob kivételt, hanem
    csendesen False-t ad (a hívó felelőssége explicit meghívni)."""

    def test_unreachable_url_returns_false(self, tmp_path):
        result = download_model(
            dest=tmp_path / "model.onnx",
            url="http://127.0.0.1:1/nincs-ilyen-szolgaltatas",
            timeout=1.0,
        )
        assert result is False
        assert not (tmp_path / "model.onnx").exists()


_REAL_MODEL = resolve_model_path()


@pytest.mark.skipif(_REAL_MODEL is None, reason="Arcfelismerő modell nincs a gépen — kihagyva.")
class TestRealModel:
    """Csak akkor fut, ha a modellfájl ténylegesen a lemezen van (helyi
    fejlesztés/manuális letöltés) — a CI-ben SOHA (nincs garantált hálózat)."""

    def test_detect_shape_on_blank_image(self):
        detector = FaceDetector()
        assert detector.available is True
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = detector.detect(image)
        assert isinstance(result, tuple)
