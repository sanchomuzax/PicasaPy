"""#6383: a Windows-frissítési mérés helyi kiadási kiszolgálója."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import zipfile

_UT = Path(__file__).resolve().parents[1] / "packaging" / "windows" / "csomag_meres.py"
_spec = importlib.util.spec_from_file_location("csomag_meres_6383", _UT)
csomag_meres = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(csomag_meres)
frissites_modul = importlib.import_module("csomag_meres_frissites")


def _csomag(gyoker: Path) -> Path:
    install = gyoker / "PicasaPy-installed"
    (install / "_internal" / "picasapy").mkdir(parents=True)
    (install / "PicasaPy.exe").write_bytes(b"installed-exe")
    (install / "PicasaPyUpdateHelper.exe").write_bytes(b"installed-helper")
    (install / "_internal" / "picasapy" / "_csomag_verzio.txt").write_text(
        "1.2.3\n", encoding="utf-8"
    )
    return install


def test_a_felajanlott_zip_verzioja_nagyobb_es_a_csomagbol_indul(tmp_path):
    install = _csomag(tmp_path)
    archive = csomag_meres._keszits_frissitesi_zip(install, tmp_path / "update.zip", "1.2.4")

    with zipfile.ZipFile(archive) as zf:
        assert "PicasaPy/PicasaPy.exe" in zf.namelist()
        assert zf.read("PicasaPy/_internal/picasapy/_csomag_verzio.txt") == b"1.2.4\n"
        assert zf.read("PicasaPy/PicasaPyUpdateHelper.exe") == b"installed-helper"


def test_a_helyi_http_szerver_a_kiadast_a_zipet_es_a_sha256sumst_adja(tmp_path):
    install = _csomag(tmp_path)
    archive = csomag_meres._keszits_frissitesi_zip(install, tmp_path / "update.zip", "1.2.4")

    class FakeServer:
        def __init__(self, address, handler_type):
            self.server_address = ("127.0.0.1", 43127)
            self.handler_type = handler_type
            self.daemon_threads = False

        def serve_forever(self):
            pass

        def shutdown(self):
            pass

        def server_close(self):
            pass

    server = csomag_meres._HelyiKiadasszerver(
        archive,
        "1.2.4",
        server_factory=FakeServer,
    )

    def get(path):
        handler = server._handler_type.__new__(server._handler_type)
        handler.server = server._server
        handler.path = path
        handler.wfile = BytesIO()
        headers = {}
        handler.send_response = lambda status: headers.setdefault("status", status)
        handler.send_header = lambda key, value: headers.setdefault(key, value)
        handler.end_headers = lambda: None
        handler.send_error = lambda status: headers.setdefault("status", status)
        handler.do_GET()
        return headers, handler.wfile.getvalue()

    api_headers, api_body = get(server._API_UT)
    release = json.loads(api_body)
    assets = {asset["name"]: asset["browser_download_url"] for asset in release["assets"]}
    zip_headers, downloaded_zip = get(server._ZIP_UT)
    hash_headers, manifest_data = get(server._HASH_UT)
    manifest = manifest_data.decode("ascii")

    assert release["tag_name"] == "v1.2.4"
    assert release["html_url"].startswith("http://127.0.0.1:")
    assert assets["PicasaPy-windows-x64.zip"].startswith("http://127.0.0.1:")
    assert api_headers["Content-Type"] == "application/vnd.github+json"
    assert zip_headers["Content-Type"] == "application/zip"
    assert hash_headers["Content-Type"] == "text/plain; charset=us-ascii"
    assert downloaded_zip == archive.read_bytes()
    assert f"{hashlib.sha256(downloaded_zip).hexdigest()}  PicasaPy-windows-x64.zip" in manifest


def test_a_frissites_alparancs_windowson_kivul_tiszta_kihagyas(tmp_path, monkeypatch):
    monkeypatch.setattr(frissites_modul, "_platform", lambda: "linux")

    assert csomag_meres.main(
        [
            "frissites",
            "--futtato",
            f"telepitett={tmp_path / 'PicasaPy.exe'}",
            "--munka",
            str(tmp_path / "work"),
            "--elvart-verzio",
            "1.2.3",
        ]
    ) == 0


def _pillanat(at: float, x: float) -> dict:
    return {
        "pid": 7,
        "at": at,
        "objects": [
            {"name": "gomb", "visible": True, "rect": {"x": x, "y": 10, "width": 40, "height": 20}}
        ],
    }


def test_a_mozgo_gombra_csak_megallas_utan_kattint(monkeypatch, tmp_path):
    """#6383: a párbeszéd megjelenéskor még mozog; az első látható helyre
    kattintva a próba mellé kattintott. Csak nyugalomban kattinthat."""
    import time as ido

    most = ido.time()
    korok = iter(
        [
            [_pillanat(most - 0.5, 100), _pillanat(most - 0.3, 300), _pillanat(most - 0.1, 500)],
            [_pillanat(most - 0.5, 608), _pillanat(most - 0.3, 608), _pillanat(most - 0.1, 608)],
        ]
    )
    monkeypatch.setattr(frissites_modul, "_diagnosztika", lambda _m: next(korok))
    monkeypatch.setattr(frissites_modul, "_falido", lambda: most)
    monkeypatch.setattr(frissites_modul, "_szunet", lambda _mp: None)
    kattintasok = []
    monkeypatch.setattr(
        frissites_modul, "_valodi_eger_kattintas", lambda obj, pid: kattintasok.append(obj["rect"]["x"])
    )

    obj = csomag_meres._stabil_kattintas(
        tmp_path, 7, lambda s: csomag_meres._objektum(s, "gomb"), "gomb"
    )

    assert kattintasok == [608]
    assert obj["rect"]["x"] == 608


def test_az_ujrainditott_program_elso_kerdeset_continue_zarja(monkeypatch, tmp_path):
    """#6383: a frissített program könyvtár-paraméter nélkül indul, ezért az
    első indítás modális kérdése eltakarja a menüt; a próba lezárja."""
    gomb = {
        "name": "initialScanContinue",
        "visible": True,
        "rect": {"x": 730, "y": 463, "width": 78, "height": 24},
    }
    most = 1000.0
    pillanatok = [{"pid": 9, "at": most - d, "objects": [gomb]} for d in (0.5, 0.3, 0.1)]
    monkeypatch.setattr(frissites_modul, "_diagnosztika", lambda _m: pillanatok)
    monkeypatch.setattr(frissites_modul, "_falido", lambda: most)
    monkeypatch.setattr(frissites_modul, "_szunet", lambda _mp: None)
    kattintasok = []
    monkeypatch.setattr(
        frissites_modul, "_valodi_eger_kattintas", lambda obj, pid: kattintasok.append(obj["name"])
    )

    assert csomag_meres._elso_inditasi_kerdes_lezarasa(tmp_path, 9) is True
    assert kattintasok == ["initialScanContinue"]


def test_kerdes_nelkul_nincs_kattintas(monkeypatch, tmp_path):
    monkeypatch.setattr(frissites_modul, "_diagnosztika", lambda _m: [])
    monkeypatch.setattr(frissites_modul, "_szunet", lambda _mp: None)
    kattintasok = []
    monkeypatch.setattr(
        frissites_modul, "_valodi_eger_kattintas", lambda obj, pid: kattintasok.append(obj)
    )

    assert csomag_meres._elso_inditasi_kerdes_lezarasa(tmp_path, 9, varakozas_mp=0.05) is False
    assert kattintasok == []
