"""A hálózati napló szintjei és a modell-letöltés naplózása (#5145).

Az eredeti options.fen „Network” fülének legördülője öt szintet kínál (0-4):
0 nincs napló, 1 csak a hibák, 2 HTTP-összefoglaló, 3 fejlécek és
átirányítás, 4 a válasz mérete. Az alapérték 2 (a dekompilált kód a `LogLevel`
kulcsot ezzel a 2-es alapértékkel olvassa).

Lefedve:
- a szint beolvasása: szám, sztring, hibás és kívülről érkező érték;
- a szintenkénti tartalom a naplófájlban;
- a valódi letöltés (loopback-kiszolgáló) a beállított szinten naplóz, és
  szint 0-n a naplófájl sem jön létre.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from picasapy import network_log
from picasapy.faces.model_download import (
    DETECTOR_SPEC,
    STATUS_NETWORK,
    STATUS_OK,
    download_spec,
)
from tests.faces.test_model_download_1496 import _Kiszolgalo

URL = "http://127.0.0.1:9/modell.onnx"


@pytest.fixture
def naplo(tmp_path):
    """A naplófájl helye; a teszt végén a naplózó kikapcsol (modul-állapot)."""
    fajl = tmp_path / "network.log"
    yield fajl
    network_log.configure(0, None)


def _sorok(fajl) -> list[str]:
    if not fajl.exists():
        return []
    return fajl.read_text(encoding="utf-8").splitlines()


def _valasz(status: int = 200, final_url: str = URL, headers=None):
    """Egy urlopen-válasz helyettesítője: a naplózó csak ezeket a mezőket olvassa."""
    return SimpleNamespace(
        status=status,
        headers=headers if headers is not None else {"Content-Type": "application/octet-stream"},
        geturl=lambda: final_url,
    )


class TestSzintBeolvasas:
    @pytest.mark.parametrize(
        ("ertek", "varas"),
        [
            (3, 3),
            ("3", 3),
            (0, 0),
            ("4", 4),
            (9, 4),
            (-1, 0),
            (None, 2),
            ("", 2),
            ("nem-szam", 2),
        ],
    )
    def test_az_ertek_a_szintre_kerul(self, ertek, varas):
        assert network_log.read_level(ertek) == varas

    def test_az_alapertek_ketto(self):
        assert network_log.DEFAULT_LEVEL == 2


class TestSzintenkentiTartalom:
    def test_0_szinten_semmi_nem_keletkezik(self, naplo):
        network_log.configure(0, naplo)

        network_log.log_failure(URL, OSError("nincs kapcsolat"))
        network_log.log_response(URL, _valasz(final_url=URL + "?atiranyitva"))
        network_log.log_size(URL, 123)

        assert not naplo.exists(), "0-s szinten nem szabad naplófájlt nyitni"

    def test_1_szinten_csak_a_hiba_kerul_be(self, naplo):
        network_log.configure(1, naplo)

        network_log.log_failure(URL, OSError("nincs kapcsolat"))
        network_log.log_response(URL, _valasz())
        network_log.log_size(URL, 123)

        sorok = _sorok(naplo)
        assert len(sorok) == 1
        assert "Error: nincs kapcsolat" in sorok[0]

    def test_2_szinten_az_osszefoglalo_kerul_be_fejlec_nelkul(self, naplo):
        network_log.configure(2, naplo)

        network_log.log_response(URL, _valasz(headers={"X-Teszt": "igen"}))
        network_log.log_size(URL, 123)

        szoveg = "\n".join(_sorok(naplo))
        assert f"Stream summary: GET request: {URL} (200)" in szoveg
        assert "X-Teszt" not in szoveg
        assert "Response size" not in szoveg

    def test_3_szinten_a_fejlecek_es_az_atiranyitas_is_bekerul(self, naplo):
        network_log.configure(3, naplo)
        atiranyitott = URL + "?uj=1"

        network_log.log_response(URL, _valasz(final_url=atiranyitott, headers={"X-Teszt": "igen"}))

        szoveg = "\n".join(_sorok(naplo))
        assert "X-Teszt: igen" in szoveg
        assert f"Redirected to URL: {atiranyitott}" in szoveg

    def test_4_szinten_a_valasz_merete_is_bekerul(self, naplo):
        network_log.configure(4, naplo)

        network_log.log_size(URL, 4096)

        assert any("Response size: 4096 bytes" in sor for sor in _sorok(naplo))


class TestValodiLetoltes:
    def _spec(self, payload: bytes):
        return DETECTOR_SPEC.masolat(
            size_bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest()
        )

    def test_2_szinten_a_letoltes_osszefoglaloja_a_naploba_kerul(self, naplo, tmp_path):
        payload = b"ONNX-nek-latszo-tartalom" * 40
        spec = self._spec(payload)
        network_log.configure(2, naplo)

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            eredmeny = download_spec(
                spec, dest=tmp_path / spec.filename, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert eredmeny.status == STATUS_OK, eredmeny.detail
        szoveg = "\n".join(_sorok(naplo))
        assert f"GET request: {kiszolgalo.alap_url}/{spec.relative_url} (200)" in szoveg

    def test_4_szinten_a_letoltott_meret_is_bekerul(self, naplo, tmp_path):
        payload = b"ONNX-nek-latszo-tartalom" * 40
        spec = self._spec(payload)
        network_log.configure(4, naplo)

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            download_spec(
                spec, dest=tmp_path / spec.filename, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert any(f"Response size: {len(payload)} bytes" in sor for sor in _sorok(naplo))

    def test_hiba_eseten_1_szinten_a_hiba_bekerul(self, naplo, tmp_path):
        spec = self._spec(b"x")
        network_log.configure(1, naplo)

        # Zárt portra: nincs kiszolgáló, a kapcsolódás hibát ad.
        eredmeny = download_spec(
            spec, dest=tmp_path / spec.filename, base_url="http://127.0.0.1:9", timeout=2.0
        )

        assert eredmeny.status == STATUS_NETWORK
        assert any("Error: " in sor for sor in _sorok(naplo))

    def test_0_szinten_a_letoltes_nem_ir_naplot(self, naplo, tmp_path):
        payload = b"ONNX-nek-latszo-tartalom" * 40
        spec = self._spec(payload)
        network_log.configure(0, naplo)

        with _Kiszolgalo({"/" + spec.relative_url: payload}) as kiszolgalo:
            download_spec(
                spec, dest=tmp_path / spec.filename, base_url=kiszolgalo.alap_url, timeout=5.0
            )

        assert not naplo.exists()
