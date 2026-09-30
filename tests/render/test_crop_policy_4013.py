"""#4013: a képszekció crop= kulcsa választja ki a megjelenített vágást."""

import logging

import pytest

from picasapy.ini.filters import parse_filters
from picasapy.ini.photo_crop import PhotoCropReader
from picasapy.ini.rect64 import decode_rect64
import picasapy.render as render

# rontás-kontroll: picasapy.ini.rect64._SCALE = 131072 → 1 failed


_FILTERS = (
    "crop64=1,10101010;"
    "Border=1,20,5,0,00000000,00ffffff,0;"
    "crop64=1,3c3c8c8c;"
    "Vignette=1,35,1.4,0,00000000;"
)


def test_crop_nelkul_minden_crop64_elmarad_es_a_tobbi_sorrendje_marad():
    ops = parse_filters(_FILTERS)

    effective = _normalize_crop_ops(ops, None)

    assert [op.name for op in effective] == ["Border", "Vignette"]


def test_crop_a_lancbeli_utolso_crop64_et_helyben_csereli():
    ops = parse_filters(_FILTERS)
    crop = "rect64(20002000a000a000)"

    effective = _normalize_crop_ops(ops, crop)

    assert [op.name for op in effective] == ["crop64", "Border", "crop64", "Vignette"]
    assert effective[0] == ops[0]
    assert effective[1] == ops[1]
    assert effective[2].params[1] == crop
    assert effective[3] == ops[3]
    assert decode_rect64(crop).right == pytest.approx(0.625)


def test_ervenytelen_crop_eseten_a_lanc_valtozatlanul_fut_tovabb(caplog):
    ops = parse_filters(_FILTERS)

    with caplog.at_level(logging.WARNING):
        effective = _normalize_crop_ops(ops, "1,2,3,4,5;")
        _normalize_crop_ops(ops, "1,2,3,4,5;")

    assert effective == ops
    warnings = [
        record
        for record in caplog.records
        if "érvénytelen crop=" in record.message.casefold()
    ]
    assert len(warnings) == 1


def test_olvashatatlan_ini_eseten_a_lanc_valtozatlan_marad():
    ops = parse_filters(_FILTERS)

    effective = _normalize_crop_ops(ops, None, crop_ini_readable=False)

    assert effective == ops


def test_ervenytelen_crop_azonos_kepen_csak_egyszer_figyelmeztet(caplog, tmp_path):
    ops = parse_filters(_FILTERS)
    image_key = str(tmp_path / "kep.jpg")

    with caplog.at_level(logging.WARNING):
        _normalize_crop_ops(ops, "nem-rect64", warning_key=image_key)
        _normalize_crop_ops(ops, "nem-rect64", warning_key=image_key)

    warnings = [
        record for record in caplog.records if "érvénytelen crop=" in record.message.casefold()
    ]
    assert len(warnings) == 1


def test_olvashatatlan_ini_naplojat_a_normalizalo_nem_ismetli(caplog):
    ops = parse_filters(_FILTERS)

    with caplog.at_level(logging.WARNING):
        _normalize_crop_ops(ops, None, crop_ini_readable=False)

    assert not any("nem olvasható" in record.message for record in caplog.records)


def test_photo_crop_reader_olvashatatlan_ini_csak_egyszer_figyelmeztet(
    caplog, monkeypatch, tmp_path
):
    import picasapy.ini.photo_crop as photo_crop

    def unreadable(_path):
        raise OSError("teszt olvasási hiba")

    monkeypatch.setattr(photo_crop, "load_or_empty", unreadable)
    reader = PhotoCropReader()
    ini_path = tmp_path / ".picasa.ini"

    with caplog.at_level(logging.WARNING):
        for _ in range(2):
            crop, readable = reader.read(ini_path, "kep.jpg")
            assert (crop, readable) == (None, False)
            _normalize_crop_ops(
                parse_filters(_FILTERS), crop, crop_ini_readable=readable
            )

    warnings = [
        record
        for record in caplog.records
        if "forrás .picasa.ini fájlja nem olvasható" in record.message
    ]
    assert len(warnings) == 1


def _normalize_crop_ops(*args, **kwargs):
    operation = getattr(render, "normalize_crop_ops", None)
    assert callable(operation), "a közös crop-normalizáló még hiányzik"
    return operation(*args, **kwargs)
