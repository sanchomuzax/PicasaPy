"""A Picasa hasonlósági jellemzők és rangsor mért képletei (#5744)."""

from __future__ import annotations

import struct

import numpy as np
import pytest

from picasapy.dedup.similarity import (
    DEFAULT_RANK_MAX,
    SimilarityCandidate,
    edge_distance,
    edge_features,
    final_rank_key,
    histogram_distance,
    histogram_feature,
    rank_similarity_candidates,
    rgb565_distance,
    rgb565_feature,
    similarity_rank_sums,
)


def _feature(rgb=0, histogram_value=0, edge_value=0.0):
    return (
        (rgb,) * 64,
        (histogram_value,) * 216,
        (edge_value,) * 8,
    )


def test_rgb565_tavolsag_a_qemu_meres_vorose_zoldre_es_kekre():
    fekete = (0,) * 64
    vörös = (0xF800,) + fekete[1:]
    zöld = (0x07E0,) + fekete[1:]
    kék = (0x001F,) + fekete[1:]

    assert rgb565_distance(fekete, vörös) == pytest.approx(15.015625)
    assert rgb565_distance(fekete, zöld) == pytest.approx(62.015625)
    assert rgb565_distance(fekete, kék) == pytest.approx(15.015625)


def test_rgb565_jellemzo_a_spec_szerinti_8x8_kvantalo():
    bgr = np.zeros((8, 8, 3), dtype=np.uint8)
    bgr[0, 0] = (255, 128, 248)

    eredmény = rgb565_feature(bgr)

    assert eredmény[0] == 0xFC1F
    assert eredmény[1:] == (0,) * 63


def test_216_bajtos_tavolsag_a_qemu_normalizalt_histogram_ertekevel():
    qemu_histogram = [0] * 216
    for index, value in {
        85: 27,
        86: 124,
        91: 20,
        92: 90,
        121: 56,
        122: 255,
    }.items():
        qemu_histogram[index] = value

    assert histogram_distance((0,) * 216, tuple(qemu_histogram)) == pytest.approx(
        173692 / 216
    )


def test_216_bajtos_jellemzo_a_qemu_egypixeles_meresevel():
    bgr = np.array([[[100, 120, 140]]], dtype=np.uint8)

    eredmény = histogram_feature(bgr)

    assert {i: value for i, value in enumerate(eredmény) if value} == {
        85: 27,
        86: 124,
        91: 20,
        92: 90,
        121: 56,
        122: 255,
    }


def test_nyolc_float_tavolsag_a_qemu_5x5_meresevel():
    mért_x_y = struct.unpack("<f", struct.pack("<f", 0.0031894398853182793))[0]
    egyik = (mért_x_y, mért_x_y) + (0.0,) * 6

    assert edge_distance((0.0,) * 8, egyik) == pytest.approx(
        2 * mért_x_y**2
    )


def test_nyolc_float_jellemzo_a_qemu_masodik_kulonbsegeivel():
    yy, xx = np.mgrid[:5, :5]
    bgr = np.stack((xx**2, yy**2, xx**2 + yy**2), axis=-1).astype(np.uint8)

    eredmény = edge_features(bgr)

    assert eredmény == pytest.approx((0.0031894398853182793,) * 2)


def test_a_harom_tavolsag_rankosszege_rangsorol():
    minta = _feature()
    candidates = (
        SimilarityCandidate("A", _feature(edge_value=10), 0),
        SimilarityCandidate("B", _feature(histogram_value=10), 0),
        SimilarityCandidate("C", _feature(rgb=10), 0),
        SimilarityCandidate("D", _feature(rgb=4, histogram_value=4, edge_value=4), 0),
    )

    assert similarity_rank_sums(minta, candidates) == (
        ("A", 3),
        ("B", 4),
        ("C", 5),
        ("D", 6),
    )


def test_vegso_kulcs_a_spec_szerinti_sim_plusz_ketszer_time():
    assert final_rank_key(0, 2) == 4
    assert final_rank_key(3, 0) == 3


def test_rankmax_az_elore_rendezett_lista_elso_n_elemere_vag():
    minta = _feature()
    candidates = tuple(
        SimilarityCandidate(f"{i}", _feature(rgb=i), i)
        for i in range(3)
    )

    assert rank_similarity_candidates(minta, 0, candidates, rank_max=2) == (
        "0",
        "1",
    )


def test_rankmax_alapertelmezese_1000():
    minta = _feature()
    candidates = tuple(
        SimilarityCandidate(f"{i}", _feature(), i)
        for i in range(DEFAULT_RANK_MAX + 1)
    )

    találatok = rank_similarity_candidates(minta, 0, candidates)

    assert len(találatok) == 1000
    assert találatok[0] == "0"
    assert találatok[-1] == "999"
