"""#6383: a Windows-frissítési mérés helyi kiadási kiszolgálója."""

from __future__ import annotations

import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import zipfile

_UT = Path(__file__).resolve().parents[1] / "packaging" / "windows" / "csomag_meres.py"
_spec = importlib.util.spec_from_file_location("csomag_meres_6383", _UT)
csomag_meres = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(csomag_meres)


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
    monkeypatch.setattr(csomag_meres, "_platform", lambda: "linux")

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
