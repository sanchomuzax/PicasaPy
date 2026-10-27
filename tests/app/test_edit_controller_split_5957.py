"""A #5957-es belső felosztás maradjon témák szerint különálló."""

from __future__ import annotations

import inspect

from picasapy.app.edit_controller import EditController


_TEMAK = {
    "beginEdit": "EditControllerSessionMixin",
    "undoLabel": "EditControllerHistoryMixin",
    "persistChain": "EditControllerSaveMixin",
    "_register_preview": "EditControllerPreviewMixin",
    "applyCrop": "EditControllerCropMixin",
    "applyRetouch": "EditControllerRetouchMixin",
    "runRedeyeAuto": "EditControllerRedeyeMixin",
    "applyText": "EditControllerTextMixin",
    "applyEffect": "EditControllerEffectsMixin",
}


def test_vezérlő_tematikus_mixinekből_áll() -> None:
    """A QML-híd maradjon egy osztály, a témák külön mixinekben éljenek."""
    mro_nevek = {osztaly.__name__ for osztaly in EditController.__mro__}

    for metodus, mixin in _TEMAK.items():
        assert mixin in mro_nevek, f"hiányzó témamixin: {mixin}"
        tulajdonos = next(
            osztaly for osztaly in EditController.__mro__
            if osztaly.__name__ == mixin
        )
        assert metodus in tulajdonos.__dict__, (
            f"{metodus} nem a {mixin} témamixinből érkezik"
        )


def test_konstruktor_alairasa_valtozatlan() -> None:
    assert str(inspect.signature(EditController)) == (
        "(provider: 'EditPreviewProvider', parent=None, *, slot: 'str' = '', "
        "settings: 'QSettings | None' = None) -> 'None'"
    )


def test_a_qt_metaobjektum_orokli_a_qml_feluletet() -> None:
    meta = EditController.staticMetaObject

    for nev in ("previewSource", "undoLabel", "redeyeRegions",
                "textOverlayItems", "effectChain"):
        assert meta.indexOfProperty(nev) >= 0, f"hiányzó QML-tulajdonság: {nev}"
    for jel in ("revisionChanged()", "editSaveFailed(QString)"):
        assert meta.indexOfSignal(jel) >= 0, f"hiányzó QML-jelzés: {jel}"
    for metodus in (
        "beginEdit(QString,QString)",
        "applyCrop(double,double,double,double)",
        "runRedeyeAuto()",
        "applyText()",
        "applyEffect(QString)",
    ):
        assert meta.indexOfMethod(metodus) >= 0, (
            f"hiányzó QML-metódus: {metodus}"
        )
