"""GPU élő-előnézet bekötés (#22): `GpuPointFilterPreview` a `photo` fölött,
a finetune-csúszkák AKTÍV húzása alatt.

Ez a fájl a FALLBACK-ágat teszteli — ez fut CI-ban is (nincs `/dev/dri`,
tehát `GraphicsInfo.api` sosem RHI-alapú a teszt-futtatókörnyezetben, ld.
a #22 jegy jelentése). A tényleges GPU-renderelést a
`tests/app/test_gpu_point_filter_shader.py` bizonyítja (valódi RHI-n SKIP
nélkül fut, ld. ott). Itt azt bizonyítjuk, hogy:

- a réteg réteg LÉTREJÖN a QML-fában (bekötve, nem elfelejtve), de
- GPU-képtelen környezetben SOSEM válik láthatóvá — a húzás a rendes,
  teljes CPU-előnézeten (`previewFinetune`) megy át, mint eddig, és
- a húzás VÉGén (finetuneCommit) minden állapot (aktív-jelző, mentés)
  helyesen visszaáll.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject


class TestGpuFinetuneFallback:
    def _open_viewer(self, window, qt_app, index=0):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", index)
        qt_app.processEvents()
        return viewer

    def test_gpu_layer_exists_but_hidden_without_rhi(self, qml_app, qt_app):
        window, _, _engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        gpu_layer = window.findChild(QObject, "gpuFinetunePreview")
        assert gpu_layer is not None, "gpuFinetunePreview nem található"
        # a teszt-futtatókörnyezetben (offscreen/software) nincs RHI —
        # a réteg emiatt sosem látható, a `photo` marad a látható forrás
        assert viewer.property("gpuFinetuneEligible") is False
        assert gpu_layer.property("visible") is False

    def test_dragging_fill_light_uses_cpu_fallback(self, qml_app, qt_app):
        """GPU-képtelen környezetben a húzás a rendes CPU-előnézetet
        frissíti, MINDEN mozdulatnál — semmi nem törik a GPU hiánya miatt."""
        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        image = window.findChild(QObject, "viewerImage")
        edit = engine.rootContext().contextProperty("editController")

        source_before = image.property("source").toString()
        slider = panel.findChild(QObject, "finetuneFillSlider")
        slider.setProperty("value", 0.4)
        qt_app.processEvents()

        assert viewer.property("gpuFinetuneActive") is True
        # a `photo` forrása MINDEN CPU-út lépésnél frissül (?rev= bumpol) —
        # ez bizonyítja, hogy tényleg a rendes previewFinetune futott, nem
        # a GPU-only gyors út (ami NEM bumpolná a revisiont)
        assert image.property("source").toString() != source_before
        assert edit.property("fillLight") == pytest.approx(0.0)  # csak commitkor mentődik

    def test_commit_resets_active_flag_and_saves(self, qml_app, qt_app, tmp_path):
        window, _, engine = qml_app
        viewer = self._open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        edit = engine.rootContext().contextProperty("editController")

        slider = panel.findChild(QObject, "finetuneFillSlider")
        slider.setProperty("value", 0.4)
        qt_app.processEvents()
        assert viewer.property("gpuFinetuneActive") is True

        slider.setProperty("pressed", True)
        qt_app.processEvents()
        slider.setProperty("pressed", False)
        qt_app.processEvents()

        assert viewer.property("gpuFinetuneActive") is False
        assert edit.property("fillLight") == pytest.approx(0.4)
        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "finetune2=" in ini_text

    def test_gpu_sources_available_on_empty_chain(self, qml_app, qt_app):
        """Üres lánccal nyitott képnél a `gpuPrefixSource`/`gpuLutSource`
        MÁR eligible-URL-t ad — a lánc üres esetén a GPU-fedezet
        feltétele triviálisan teljesül (`EditSession.gpu_finetune_prefix`)."""
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        edit = engine.rootContext().contextProperty("editController")
        assert edit.property("gpuPrefixSource").startswith("image://editpreview/")
        assert "gpuprefix=1" in edit.property("gpuPrefixSource")
        assert "gpulut=1" in edit.property("gpuLutSource")

    def test_viewer_close_clears_gpu_sources(self, qml_app, qt_app):
        window, _, engine = qml_app
        self._open_viewer(window, qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        edit = engine.rootContext().contextProperty("editController")
        assert edit.property("gpuPrefixSource") == ""
        assert edit.property("gpuLutSource") == ""
