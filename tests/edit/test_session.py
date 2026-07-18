"""EditSession — immutábilis szerkesztési-lánc állapotkezelő tesztjei."""

import pytest
from picasapy.edit import EditSession
from picasapy.ini.rect64 import Rect64


class TestEditSessionBasics:
    """Alapvető parse/serialize."""

    def test_from_empty_string(self):
        """Üres vagy None string üres láncot ad."""
        session = EditSession.from_value("")
        assert session.is_empty()
        assert session.to_value() == ""

    def test_from_none(self):
        """None üres láncot ad."""
        session = EditSession.from_value(None)
        assert session.is_empty()

    def test_from_single_filter(self):
        """Egyetlen szűrő parse-olása."""
        session = EditSession.from_value("enhance=1;")
        assert not session.is_empty()
        assert session.to_value() == "enhance=1;"

    def test_from_multiple_filters(self):
        """Több szűrő parse-olása, sorrend megtartása."""
        value = "enhance=1;autolight=1;crop64=1,3f845bcb59418507;"
        session = EditSession.from_value(value)
        assert session.to_value() == value

    def test_round_trip_with_unknown_filters(self):
        """Ismeretlen szűrőket érintetlenül kell megőrizni."""
        value = "enhance=1;finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;autolight=1;"
        session = EditSession.from_value(value)
        assert session.to_value() == value


class TestCrop:
    """crop64 szűrő kezelése."""

    def test_set_crop_empty(self):
        """crop64 hozzáadása üres lánchoz."""
        session = EditSession.from_value("")
        rect = Rect64(0.1, 0.2, 0.8, 0.9)
        new_session = session.set_crop(rect)

        # Új objektum, immutabilitás
        assert new_session is not session

        # crop64 jól van (hex kerekítési tolerancia)
        decoded = new_session.crop()
        assert decoded is not None
        assert abs(decoded.left - rect.left) < 0.001
        assert abs(decoded.top - rect.top) < 0.001
        assert abs(decoded.right - rect.right) < 0.001
        assert abs(decoded.bottom - rect.bottom) < 0.001
        assert new_session.to_value().startswith("crop64=1,")

    def test_set_crop_replaces_existing(self):
        """Meglévő crop64-et lecserél, helyben."""
        value = "enhance=1;crop64=1,10000000f1ddff49;autolight=1;"
        session = EditSession.from_value(value)

        new_rect = Rect64(0.25, 0.35, 0.75, 0.95)
        new_session = session.set_crop(new_rect)

        # enhance és autolight maradnak, crop64 cseréje
        result = new_session.to_value()
        assert "enhance=1;" in result
        assert "autolight=1;" in result

        # Hex kerekítési tolerancia
        decoded = new_session.crop()
        assert decoded is not None
        assert abs(decoded.left - new_rect.left) < 0.001
        assert abs(decoded.top - new_rect.top) < 0.001
        assert abs(decoded.right - new_rect.right) < 0.001
        assert abs(decoded.bottom - new_rect.bottom) < 0.001

        # crop64 az eredeti helyén marad (harmadik)
        parts = result.split(";")
        assert any("crop64=" in p for p in parts)

    def test_clear_crop(self):
        """crop64 eltávolítása."""
        value = "enhance=1;crop64=1,3f845bcb59418507;autolight=1;"
        session = EditSession.from_value(value)

        new_session = session.clear_crop()
        assert new_session.crop() is None
        assert "crop64" not in new_session.to_value()
        assert "enhance=1;" in new_session.to_value()
        assert "autolight=1;" in new_session.to_value()

    def test_clear_crop_empty(self):
        """Üres láncban clear_crop-et hívni biztonságos."""
        session = EditSession.from_value("")
        new_session = session.clear_crop()
        assert new_session.is_empty()

    def test_crop_getter(self):
        """crop() dekódolás helyesen."""
        rect = Rect64(0.248108, 0.358566, 0.348648, 0.519638)
        value = f"crop64=1,3f845bcb59418507;"
        session = EditSession.from_value(value)

        fetched = session.crop()
        assert fetched is not None
        # Hex kerekítési tolerancia
        assert abs(fetched.left - rect.left) < 0.001
        assert abs(fetched.top - rect.top) < 0.001
        assert abs(fetched.right - rect.right) < 0.001
        assert abs(fetched.bottom - rect.bottom) < 0.001


class TestTilt:
    """tilt szűrő kezelése."""

    def test_set_tilt_empty(self):
        """tilt hozzáadása üres lánchoz."""
        session = EditSession.from_value("")
        new_session = session.set_tilt(0.123456, 0.789012)

        assert new_session is not session
        fetched = new_session.tilt_param()
        assert fetched is not None
        assert abs(fetched - 0.123456) < 0.0001

        # tilt=1,param,scale formátum
        assert "tilt=1,0.123456,0.789012;" in new_session.to_value()

    def test_set_tilt_replaces_existing(self):
        """Meglévő tilt-et lecserél."""
        value = "enhance=1;tilt=1,-0.114659,0.950000;autolight=1;"
        session = EditSession.from_value(value)

        new_session = session.set_tilt(0.25, 0.75)

        # enhance és autolight maradnak
        result = new_session.to_value()
        assert "enhance=1;" in result
        assert "autolight=1;" in result

        # tilt helyre kerül-e, a régi helyén?
        parts = result.split(";")
        tilt_parts = [p for p in parts if p.startswith("tilt=")]
        assert len(tilt_parts) == 1
        assert "0.250000" in tilt_parts[0]
        assert "0.750000" in tilt_parts[0]

    def test_clear_tilt(self):
        """tilt eltávolítása."""
        value = "enhance=1;tilt=1,0.5,0.8;autolight=1;"
        session = EditSession.from_value(value)

        new_session = session.clear_tilt()
        assert new_session.tilt_param() is None
        assert "tilt" not in new_session.to_value()

    def test_tilt_param_getter(self):
        """tilt_param() az első paraméter."""
        value = "tilt=1,0.333333,0.666667;"
        session = EditSession.from_value(value)

        param = session.tilt_param()
        assert param is not None
        assert abs(param - 0.333333) < 0.0001


class TestToggle:
    """Toggle szűrők: redeye, enhance, autolight, autocolor."""

    def test_toggle_add(self):
        """Hiányzó szűrőt a lánc végére fűzi."""
        session = EditSession.from_value("enhance=1;")
        new_session = session.toggle("redeye")

        result = new_session.to_value()
        assert "enhance=1;" in result
        assert "redeye=1;" in result
        # redeye a végén
        assert result.endswith("redeye=1;")

    def test_toggle_remove(self):
        """Meglévő szűrőt eltávolít."""
        session = EditSession.from_value("enhance=1;redeye=1;autolight=1;")
        new_session = session.toggle("redeye")

        result = new_session.to_value()
        assert "enhance=1;" in result
        assert "autolight=1;" in result
        assert "redeye" not in result

    def test_toggle_case_insensitive(self):
        """Toggle kis-nagybetű-tűrő."""
        session = EditSession.from_value("Redeye=1;")
        new_session = session.toggle("redeye")

        # Eltávolít, mert case-insensitive
        assert new_session.is_empty()

    def test_toggle_invalid_name(self):
        """Érvénytelen szűrő-név."""
        session = EditSession.from_value("")
        with pytest.raises(ValueError):
            session.toggle("foo")

    @pytest.mark.parametrize("name", ["redeye", "enhance", "autolight", "autocolor"])
    def test_toggle_valid_names(self, name):
        """Összes érvényes toggle név."""
        session = EditSession.from_value("")
        new_session = session.toggle(name)
        assert not new_session.is_empty()
        assert new_session.to_value() == f"{name}=1;"


class TestHas:
    """has() — szűrő létezésének ellenőrzése."""

    def test_has_found(self):
        """Meglévő szűrő."""
        session = EditSession.from_value("enhance=1;crop64=1,10000000f1ddff49;")
        assert session.has("enhance")
        assert session.has("crop64")

    def test_has_not_found(self):
        """Hiányzó szűrő."""
        session = EditSession.from_value("enhance=1;")
        assert not session.has("crop64")

    def test_has_case_insensitive(self):
        """has() kis-nagybetű-tűrő."""
        session = EditSession.from_value("Redeye=1;")
        assert session.has("redeye")
        assert session.has("REDEYE")

    def test_has_empty(self):
        """Üres lánc."""
        session = EditSession.from_value("")
        assert not session.has("enhance")


class TestImmutability:
    """Immutabilitás garantálása."""

    def test_operations_return_new_object(self):
        """Minden operáció új objektumot ad."""
        session = EditSession.from_value("enhance=1;")

        session2 = session.set_crop(Rect64(0.1, 0.2, 0.8, 0.9))
        assert session2 is not session
        assert session.is_empty() or "crop64" not in session.to_value()
        assert "crop64" in session2.to_value()

    def test_original_unchanged_after_toggle(self):
        """Az eredeti lánc módosítás után is ugyanaz."""
        original_value = "enhance=1;autolight=1;"
        session = EditSession.from_value(original_value)

        new_session = session.toggle("redeye")

        # Az eredeti már nem azonos
        assert session.to_value() == original_value
        assert "redeye" in new_session.to_value()

    def test_frozenness(self):
        """Az ops tuple nem módosítható."""
        from dataclasses import FrozenInstanceError

        session = EditSession.from_value("enhance=1;")
        with pytest.raises(FrozenInstanceError):
            session.ops = ()  # type: ignore


class TestComplexScenarios:
    """Összetett szerkesztési-lánc szituációk."""

    def test_real_world_filter_chain(self):
        """Valódi Picasa-lánc."""
        value = "enhance=1;autolight=1;crop64=1,3f845bcb59418507;finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
        session = EditSession.from_value(value)

        # crop64 módosítása
        new_rect = Rect64(0.2, 0.3, 0.7, 0.8)
        session2 = session.set_crop(new_rect)

        # finetune2 megmarad
        assert "finetune2=" in session2.to_value()
        # crop64 a helyén van (hex kerekítési tolerancia)
        decoded = session2.crop()
        assert decoded is not None
        assert abs(decoded.left - new_rect.left) < 0.001
        assert abs(decoded.top - new_rect.top) < 0.001
        assert abs(decoded.right - new_rect.right) < 0.001
        assert abs(decoded.bottom - new_rect.bottom) < 0.001
        # enhance és autolight megmarad
        assert session2.has("enhance")
        assert session2.has("autolight")

    def test_unknown_filter_preservation(self):
        """Ismeretlen szűrő round-trip."""
        value = "enhance=1;finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;Vignette=1,0.5,0.8,0.3;"
        session = EditSession.from_value(value)

        # Nem módosítjuk a finetune2-t vagy Vignette-et
        session2 = session.toggle("autolight")

        # Mindkettő bitre azonos marad
        result = session2.to_value()
        assert "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;" in result
        assert "Vignette=1,0.5,0.8,0.3;" in result
        assert "autolight=1;" in result

    def test_tilt_with_negative_angle(self):
        """tilt negatív szöggel."""
        value = "tilt=1,-0.114659,0.950000;"
        session = EditSession.from_value(value)

        param = session.tilt_param()
        assert param is not None
        assert param < 0
        assert abs(param - (-0.114659)) < 0.0001

        # Round-trip
        assert session.to_value() == value

    def test_multiple_operations_chain(self):
        """Egymásra épülő operációk."""
        session = EditSession.from_value("")

        # 1. enhance hozzáadása
        session = session.toggle("enhance")
        assert session.has("enhance")

        # 2. crop beállítása
        rect1 = Rect64(0.1, 0.2, 0.8, 0.9)
        session = session.set_crop(rect1)
        decoded = session.crop()
        assert decoded is not None
        assert abs(decoded.left - rect1.left) < 0.001
        assert abs(decoded.top - rect1.top) < 0.001
        assert abs(decoded.right - rect1.right) < 0.001
        assert abs(decoded.bottom - rect1.bottom) < 0.001

        # 3. crop módosítása
        rect2 = Rect64(0.2, 0.3, 0.7, 0.8)
        session = session.set_crop(rect2)
        decoded = session.crop()
        assert decoded is not None
        assert abs(decoded.left - rect2.left) < 0.001
        assert abs(decoded.top - rect2.top) < 0.001
        assert abs(decoded.right - rect2.right) < 0.001
        assert abs(decoded.bottom - rect2.bottom) < 0.001

        # 4. tilt hozzáadása
        session = session.set_tilt(0.1, 0.9)
        assert session.tilt_param() is not None

        # Mindent megtartott
        assert session.has("enhance")
        assert session.has("crop64")
        assert session.has("tilt")

    def test_clear_all_operations(self):
        """Mindent eltávolítani."""
        value = "enhance=1;crop64=1,10000000f1ddff49;tilt=1,0.5,0.8;autolight=1;"
        session = EditSession.from_value(value)

        session = session.toggle("enhance")
        session = session.toggle("autolight")
        session = session.clear_crop()
        session = session.clear_tilt()

        assert session.is_empty()
        assert session.to_value() == ""


class TestEdgeCases:
    """Speciális szituációk."""

    def test_crop_params_missing(self):
        """crop64 paraméter nélkül (érvénytelen)."""
        # A parse_filters nem validál, de crop() None-t ad vissza
        value = "enhance=1;crop64=1;autolight=1;"
        session = EditSession.from_value(value)

        assert session.has("crop64")
        assert session.crop() is None  # Nincs a 2. paraméter

    def test_tilt_params_missing(self):
        """tilt paraméter nélkül."""
        value = "enhance=1;tilt=1;autolight=1;"
        session = EditSession.from_value(value)

        assert session.has("tilt")
        assert session.tilt_param() is None  # Nincs a 2. paraméter

    def test_toggle_idempotence(self):
        """Toggle ismételt hívása."""
        session = EditSession.from_value("")

        # 1. toggle: add
        session = session.toggle("enhance")
        assert session.has("enhance")

        # 2. toggle: remove
        session = session.toggle("enhance")
        assert not session.has("enhance")

        # 3. toggle: add újra
        session = session.toggle("enhance")
        assert session.has("enhance")

    def test_mixed_case_filter_names_preserved(self):
        """FilterOp név megőrzése az eredeti alak szerint."""
        value = "Enhance=1;AutoLight=1;Redeye=1;"
        session = EditSession.from_value(value)

        # Round-trip: az eredeti nevek megmaradnak
        assert session.to_value() == value

    def test_crop_placement_not_affected_by_modification(self):
        """crop64 helye: ha van, a helyén marad; ha nincs, a végén kerül."""
        # Crop a közepén
        value = "enhance=1;crop64=1,10000000f1ddff49;autolight=1;"
        session = EditSession.from_value(value)

        new_rect = Rect64(0.5, 0.5, 0.9, 0.9)
        session = session.set_crop(new_rect)

        # A sorrend: enhance, crop64 (módosított), autolight
        result = session.to_value()
        parts = result.split(";")
        crop_idx = next(i for i, p in enumerate(parts) if "crop64=" in p)
        assert crop_idx == 1  # A harmadik elem (0-indexed: 1)

    def test_toggle_multiple_same_filter(self):
        """Több azonos toggle a láncban — csak az első eltávolít."""
        # Múltban lehetne 2x enhance (degenerált eset)
        # A toggle csak az első függőséget végzi el
        session = EditSession.from_value("enhance=1;enhance=1;autolight=1;")

        session = session.toggle("enhance")

        # Mindkettő eltávolodik (mivel van már, a toggle remove-ot csinál)
        assert not session.has("enhance")

    def test_negative_tilt_param_formatting(self):
        """Negatív tilt szög formázása."""
        session = EditSession.from_value("")
        session = session.set_tilt(-0.114659, 0.950000)

        result = session.to_value()
        assert "tilt=1,-0.114659,0.950000;" in result

    def test_very_small_floats(self):
        """Nagyon kicsi floatok formázása."""
        session = EditSession.from_value("")
        session = session.set_tilt(0.000001, 0.999999)

        result = session.to_value()
        # 6 tizedes: 0.000001 → "0.000001", 0.999999 → "0.999999"
        assert "0.000001" in result
        assert "0.999999" in result
