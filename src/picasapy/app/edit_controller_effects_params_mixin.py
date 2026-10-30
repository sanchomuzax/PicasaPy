"""Paraméteres effektek: vezérlők, előnézet és alkalmazás (#6267)."""

from __future__ import annotations

from .edit_controller_shared import (
    _APPLICABLE_EFFECTS,
    _EFFECT_INI_NAMES,
    _EFFECT_PARAMS,
    EditSession,
    Slot,
    format_param_values,
    gyors_elonezet,
    has_params,
    resolve_effect_params,
)


class EditControllerEffectsParamsMixin:
    """Paraméteres effektek vezérlői, előnézete és alkalmazása (#6267)."""

    @Slot(str, result=bool)
    def effectHasParams(self, name: str) -> bool:
        """Nyíljon-e csúszkás alpanel a gombra kattintva?

        A paraméter nélküli effektek (Szépia, Fekete-fehér…) az eredeti
        Picasában is egy kattintással alkalmazódnak.
        """
        return has_params(name)


    @Slot(str, result="QVariant")
    def effectParams(self, name: str):
        """Az effekt vezérlői a QML-nek — LISTÁT adunk, nem tuple-t: a
        QML-oldalon a tuple NEM tömb (#232).

        #516: a képfüggő tartományokat (`CornerRadius` 0..min(W,H)/2 stb.)
        a JELENLEG szerkesztett kép valódi méretével számoljuk ki
        (`resolve_effect_params`) — nincs bebetonozott szám."""
        width, height = self._image_size if self._image_size else (None, None)
        return [
            {
                "key": param.key,
                "label": param.label,
                "kind": param.kind,
                "minimum": param.minimum,
                "maximum": param.maximum,
                "default": param.default,
                "step": param.step,
                "color": param.color,
            }
            for param in resolve_effect_params(name, width, height)
        ]


    @Slot(str, "QVariantList")
    def previewEffect(self, name: str, values) -> None:
        """Élő előnézet a csúszkák húzása közben: a képet a pillanatnyi
        értékekkel újrarendereli, de NEM ír ini-be és NEM tol undo-lépést
        (a previewFinetune mintájára, #20).

        #3862: a `gyors_elonezet()` blokk (a `previewTilt` mintájára) a
        Polaroid forgatását is a gyors mintavevőre váltja húzás közben — az
        `applyEffectWithParams` (elengedéskor/Alkalmaz) már a blokkon kívül,
        natívan renderel."""
        self._require_active()
        preview_session = self._session_with_effect(name, values)
        if preview_session is None:
            return
        with gyors_elonezet():
            self._register_preview(preview_session)
        self._bump_revision()


    @Slot()
    def discardEffectPreview(self) -> None:
        """Mégse: az előnézet elvetése, a mentett lánc visszaállítása."""
        self._require_active()
        self._register_preview()
        self._bump_revision()


    @Slot(str, "QVariantList")
    def applyEffectWithParams(self, name: str, values) -> None:
        """Alkalmaz: a beállított értékekkel fűzi a láncra (undo + mentés).

        Hiányzó vagy hiányos értéklistánál a katalógus alapértékei jönnek —
        így a gomb paraméter nélkül is ugyanazt adja, mint az `applyEffect`.
        """
        self._require_active()
        session = self._session_with_effect(name, values)
        if session is None:
            return
        self._push_undo(name.casefold())
        self._session = session
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    def _session_with_effect(self, name: str, values) -> EditSession | None:
        """A lánc az effekttel a végén; ismeretlen effektnél None.

        A hiányzó értékeket a katalógus alapértéke pótolja, a fölöslegeseket
        eldobjuk — a `filters=` sosem kaphat a katalógusnál több paramétert.
        """
        if not isinstance(name, str):
            return None
        key = name.casefold()
        if key not in _APPLICABLE_EFFECTS:
            return None
        width, height = self._image_size if self._image_size else (None, None)
        catalogue = resolve_effect_params(key, width, height)
        if not catalogue:
            # paraméter nélküli effekt: a meglévő, dokumentált alapérték-út
            return self._session.append_effect(
                _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
            )
        supplied = list(values) if values is not None else []
        resolved = [
            supplied[index]
            if index < len(supplied)
            else (param.color if param.kind == "color" else param.default)
            for index, param in enumerate(catalogue)
        ]
        try:
            formatted = format_param_values(resolved, catalogue, effect=key)
        except (TypeError, ValueError):
            return None
        return self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), ("1", *formatted)
        )
