"""#26 (2. lépcső): az SFace lenyomat-számító hiánytűrő becsomagolása.

KÖTELEZŐ szabály (issue #26): a modell hiányában futó eset MINDIG lefut
(CI-ben nincs garantált modellfájl) — a modellt igénylő ellenőrzés
`skipif`-fel kihagyva, ha a fájl ténylegesen nincs jelen."""

from __future__ import annotations

import logging

import numpy as np
import pytest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.faces.embedder import (
    EMBEDDING_DIM,
    FaceEmbedder,
    download_model,
    resolve_model_path,
)

_LANDMARKS = FaceLandmarks(
    right_eye=(60.0, 80.0),
    left_eye=(120.0, 80.0),
    nose=(90.0, 110.0),
    mouth_right=(70.0, 140.0),
    mouth_left=(110.0, 140.0),
)
_DETECTION = FaceDetection(left=40, top=40, right=160, bottom=180, score=0.95, landmarks=_LANDMARKS)


class TestMissingModel:
    """A modell hiánya SOHA nem omlik/dob — tisztán kikapcsol, a detektálás
    (és minden más) változatlanul működik."""

    def test_unavailable_without_model_file(self, tmp_path):
        embedder = FaceEmbedder(model_path=tmp_path / "nincs-ilyen.onnx")
        assert embedder.available is False

    def test_compute_returns_none_without_model(self, tmp_path):
        embedder = FaceEmbedder(model_path=tmp_path / "nincs-ilyen.onnx")
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        assert embedder.compute(image, _DETECTION) is None

    def test_compute_survives_none_image(self, tmp_path):
        embedder = FaceEmbedder(model_path=tmp_path / "nincs-ilyen.onnx")
        assert embedder.compute(None, _DETECTION) is None

    def test_logs_info_when_no_model_resolvable(self, tmp_path, monkeypatch, caplog):
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.embedder.default_model_path",
            lambda: tmp_path / "nincs-ilyen.onnx",
        )
        with caplog.at_level(logging.INFO):
            embedder = FaceEmbedder()
        assert embedder.available is False
        assert any("kikapcsolva" in record.message for record in caplog.records)


class TestModelPathResolution:
    def test_none_when_nothing_exists(self, tmp_path, monkeypatch):
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.embedder.default_model_path",
            lambda: tmp_path / "nincs-ilyen.onnx",
        )
        assert resolve_model_path() is None

    def test_env_var_overrides_default(self, tmp_path, monkeypatch):
        model = tmp_path / "sajat.onnx"
        model.write_bytes(b"nem valodi onnx, csak a letezes szamit")
        monkeypatch.setenv("PICASAPY_FACE_EMBED_MODEL", str(model))
        assert resolve_model_path() == model

    def test_env_var_pointing_to_missing_file_falls_back(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PICASAPY_FACE_EMBED_MODEL", str(tmp_path / "nincs.onnx"))
        monkeypatch.setattr(
            "picasapy.faces.embedder.default_model_path",
            lambda: tmp_path / "meg-egy-hianyzo.onnx",
        )
        assert resolve_model_path() is None

    def test_uses_own_env_var_not_the_detector_one(self, tmp_path, monkeypatch):
        # a detektor és a lenyomat-modell KÜLÖN env-változóval bírálható
        # felül — nem eshetnek egymásba
        detector_model = tmp_path / "yunet.onnx"
        detector_model.write_bytes(b"nem valodi")
        monkeypatch.setenv("PICASAPY_FACE_MODEL", str(detector_model))
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.embedder.default_model_path",
            lambda: tmp_path / "nincs-ilyen.onnx",
        )
        assert resolve_model_path() is None


class TestDownloadModelNeverBlocksStartup:
    def test_unreachable_url_returns_false(self, tmp_path):
        result = download_model(
            dest=tmp_path / "model.onnx",
            url="http://127.0.0.1:1/nincs-ilyen-szolgaltatas",
            timeout=1.0,
        )
        assert result is False
        assert not (tmp_path / "model.onnx").exists()


_REAL_MODEL = resolve_model_path()


@pytest.mark.skipif(_REAL_MODEL is None, reason="Arc-lenyomat modell nincs a gépen — kihagyva.")
class TestRealModel:
    """Csak akkor fut, ha a modellfájl ténylegesen a lemezen van (helyi
    fejlesztés/manuális letöltés) — a CI-ben SOHA (nincs garantált hálózat)."""

    def test_compute_shape_on_blank_image(self):
        embedder = FaceEmbedder()
        assert embedder.available is True
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = embedder.compute(image, _DETECTION)
        assert result is not None
        assert result.shape == (EMBEDDING_DIM,)
        assert result.dtype == np.float32
