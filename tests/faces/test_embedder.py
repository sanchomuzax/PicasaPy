"""#26 (2. lépcső): az SFace lenyomat-számító hiánytűrő becsomagolása.

A hiányzómodell-eset mindig lefut. A csomagolt modell elérhetőségét és a
valódi SFace-számítást hálózat nélküli teszt is ellenőrzi."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import numpy as np
import pytest

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.faces import embedder as embedder_module
from picasapy.faces.embedder import (
    EMBEDDING_DIM,
    FaceEmbedder,
    MODEL_FILENAME,
    download_model,
    resolve_model_path,
)
from picasapy.faces.model_download import EMBEDDER_SPEC

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
        monkeypatch.setattr("picasapy.faces.embedder.bundled_model_path", lambda: None)
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
        monkeypatch.setattr("picasapy.faces.embedder.bundled_model_path", lambda: None)
        assert resolve_model_path() is None

    def test_bundled_model_precedes_a_downloaded_profile_copy(self, tmp_path, monkeypatch):
        """A csomag modellje legyen az elsődleges, a profilmappa tartalék."""
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        profile_model = tmp_path / "picasapy" / "models" / MODEL_FILENAME
        profile_model.parent.mkdir(parents=True)
        profile_model.write_bytes(b"korabbi letoltes")

        bundled_model = (
            Path(embedder_module.__file__).resolve().parent / "models" / MODEL_FILENAME
        )

        assert resolve_model_path() == bundled_model

    def test_env_var_overrides_default(self, tmp_path, monkeypatch):
        model = tmp_path / "sajat.onnx"
        model.write_bytes(b"nem valodi onnx, csak a letezes szamit")
        monkeypatch.setenv("PICASAPY_FACE_EMBED_MODEL", str(model))
        assert resolve_model_path() == model

    def test_env_var_pointing_to_missing_file_falls_back_to_bundled_model(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("PICASAPY_FACE_EMBED_MODEL", str(tmp_path / "nincs.onnx"))
        monkeypatch.setattr(
            "picasapy.faces.embedder.default_model_path",
            lambda: tmp_path / "meg-egy-hianyzo.onnx",
        )

        bundled_model = (
            Path(embedder_module.__file__).resolve().parent / "models" / MODEL_FILENAME
        )

        assert resolve_model_path() == bundled_model

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
        monkeypatch.setattr("picasapy.faces.embedder.bundled_model_path", lambda: None)
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


class TestBundledModelOffline:
    def test_clean_profile_loads_bundled_model_and_computes_face_embedding(
        self, tmp_path, monkeypatch
    ):
        """Üres profilban, letöltés nélkül is elérhető és használható az SFace."""
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "clean-profile"))
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *_args, **_kwargs: pytest.fail("a teszt nem kérhet hálózatot"),
        )

        bundled_model = (
            Path(embedder_module.__file__).resolve().parent / "models" / MODEL_FILENAME
        )
        assert bundled_model.is_file()
        assert EMBEDDER_SPEC.sha256 == "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
        assert hashlib.sha256(bundled_model.read_bytes()).hexdigest() == EMBEDDER_SPEC.sha256
        assert resolve_model_path() == bundled_model

        from picasapy.faces.model_download import missing_specs

        assert "embedder" not in {spec.key for spec in missing_specs()}

        # Önálló, arcot ábrázoló tesztminta: a keretet és az öt pontot ugyanúgy
        # adja át, ahogy a detektor kimenete kerül az SFace-hez.
        yy, xx = np.ogrid[:240, :240]
        image = np.full((240, 240, 3), 96, dtype=np.uint8)
        face = ((xx - 120) / 76) ** 2 + ((yy - 120) / 96) ** 2 <= 1
        image[face] = (182, 165, 145)
        for eye_x in (92, 148):
            eye = (xx - eye_x) ** 2 + (yy - 96) ** 2 <= 8**2
            image[eye] = (28, 28, 28)
        nose = (np.abs(xx - 120) <= 5) & (yy >= 105) & (yy <= 145)
        image[nose] = (125, 108, 92)
        mouth = ((xx - 120) / 25) ** 2 + ((yy - 164) / 6) ** 2 <= 1
        image[mouth] = (48, 42, 44)
        detection = FaceDetection(
            left=44,
            top=24,
            right=196,
            bottom=216,
            score=0.99,
            landmarks=FaceLandmarks(
                right_eye=(92.0, 96.0),
                left_eye=(148.0, 96.0),
                nose=(120.0, 128.0),
                mouth_right=(101.0, 164.0),
                mouth_left=(139.0, 164.0),
            ),
        )

        embedder = FaceEmbedder()
        assert embedder.available is True
        result = embedder.compute(image, detection)
        assert result is not None
        assert result.shape == (EMBEDDING_DIM,)
        assert result.dtype == np.float32
        assert np.isfinite(result).all()


_REAL_MODEL = resolve_model_path()


@pytest.mark.skipif(_REAL_MODEL is None, reason="Arc-lenyomat modell nincs a gépen — kihagyva.")
class TestRealModel:
    """A csomagolt SFace-szel, hálózat nélkül is futó számítási próba."""

    def test_compute_shape_on_blank_image(self):
        embedder = FaceEmbedder()
        assert embedder.available is True
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        result = embedder.compute(image, _DETECTION)
        assert result is not None
        assert result.shape == (EMBEDDING_DIM,)
        assert result.dtype == np.float32
