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
        monkeypatch.setattr(
            "picasapy.faces.detector.bundled_model_path", lambda: None
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
        monkeypatch.setattr(
            "picasapy.faces.detector.bundled_model_path", lambda: None
        )
        assert resolve_model_path() is None

    def test_env_var_overrides_default(self, tmp_path, monkeypatch):
        model = tmp_path / "sajat.onnx"
        model.write_bytes(b"nem valodi onnx, csak a letezes szamit")
        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(model))
        assert resolve_model_path() == model

    def test_env_var_pointing_to_missing_file_falls_back_to_bundled(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(tmp_path / "nincs.onnx"))
        monkeypatch.setattr(
            "picasapy.faces.detector.default_model_path",
            lambda: tmp_path / "meg-egy-hianyzo.onnx",
        )
        from picasapy.faces.detector import bundled_model_path

        assert resolve_model_path() == bundled_model_path()

    def test_bundled_model_is_last_fallback(self, tmp_path, monkeypatch):
        from picasapy.faces import detector

        monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
        monkeypatch.setattr(
            detector, "default_model_path", lambda: tmp_path / "user" / "missing.onnx"
        )
        bundled = tmp_path / "package" / detector.MODEL_FILENAME
        bundled.parent.mkdir()
        bundled.write_bytes(b"packaged-model")
        monkeypatch.setattr(
            detector, "bundled_model_path", lambda: bundled, raising=False
        )

        assert resolve_model_path() == bundled
        user_model = tmp_path / "user.onnx"
        user_model.write_bytes(b"user-model")
        monkeypatch.setattr(detector, "default_model_path", lambda: user_model)
        env_model = tmp_path / "env.onnx"
        env_model.write_bytes(b"env-model")
        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(env_model))
        assert resolve_model_path() == env_model

        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(tmp_path / "env-missing.onnx"))
        # A felhasználói modell megelőzi a csomagolt modellt hibás környezeti
        # útvonal esetén.
        assert resolve_model_path() == user_model


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
