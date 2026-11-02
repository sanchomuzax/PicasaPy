"""A csomagmérő közös futtató- és frissítési segédei."""

from __future__ import annotations

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import shutil
import sys
import threading
from pathlib import Path
import zipfile

_SIKER = "A főablak a splash után megjelent"

_INDULOABLAK = "Az indulóablak megjelent"

_SOR = re.compile(r"^(\S+) INFO picasapy\.startup: (.*)$")

_IDOKORLAT_MP = 120.0

def _futtatok(ertekek: list[str]) -> list[tuple[str, list[str]]]:
    """`nev=parancs,arg,...` párok. A vessző elválasztó, mert a windowsos
    útvonalban szóköz lehet, vessző nem."""
    eredmeny = []
    for ertek in ertekek:
        nev, _, parancs = ertek.partition("=")
        if not nev or not parancs:
            raise SystemExit(f"hibás --futtato: {ertek!r} (várt: nev=parancs,arg)")
        eredmeny.append((nev, [_resz(resz) for resz in parancs.split(",") if resz]))
    return eredmeny

def _resz(resz: str) -> str:
    """`@python` = a szkriptet futtató értelmező; a létező relatív út
    abszolúttá válik. Így a Git-bash MSYS-útvonalai (`/d/a/...`) sehol nem
    kerülnek a windowsos programok elé."""
    if resz == "@python":
        return sys.executable
    ut = Path(resz)
    return str(ut.resolve()) if not ut.is_absolute() and ut.exists() else resz

def _platform() -> str:
    """A futó platform fogantyúja, a helyi alparancs-teszthez is."""
    return sys.platform

def _sha256_fajl(ut: Path) -> str:
    digest = hashlib.sha256()
    with ut.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _keszits_frissitesi_zip(telepitesi_mappa: Path, cel: Path, verzio: str) -> Path:
    """A kész telepítési csomagból újabb verziójú tesztkiadást csomagol."""
    telepitesi_mappa = Path(telepitesi_mappa).resolve()
    cel = Path(cel)
    if not (telepitesi_mappa / "PicasaPy.exe").is_file():
        raise ValueError("a frissítési zip forrása nem teljes PicasaPy telepítési mappa")
    verziofajlok = list(telepitesi_mappa.rglob("_csomag_verzio.txt"))
    if len(verziofajlok) != 1:
        raise ValueError("a telepítési csomagban nem egyértelmű a PicasaPy verziófájlja")
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.unlink(missing_ok=True)
    with zipfile.ZipFile(cel, "w", compression=zipfile.ZIP_STORED) as archive:
        for ut in sorted(telepitesi_mappa.rglob("*")):
            if not ut.is_file():
                continue
            tag = Path("PicasaPy") / ut.relative_to(telepitesi_mappa)
            if ut == verziofajlok[0]:
                archive.writestr(tag.as_posix(), f"{verzio}\n")
            else:
                archive.write(ut, tag.as_posix())
    return cel

class _HelyiKiadasszerver:
    """Loopback Python HTTP-szerver a csomagolt updater valódi letöltéséhez."""

    _API_UT = "/repos/sanchomuzax/PicasaPy/releases/latest"
    _ZIP_UT = "/assets/PicasaPy-windows-x64.zip"
    _HASH_UT = "/assets/SHA256SUMS"

    def __init__(self, zip_ut: Path, verzio: str, *, server_factory=None) -> None:
        self.zip_ut = Path(zip_ut)
        self.verzio = verzio
        self.sha256 = _sha256_fajl(self.zip_ut)
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                base = f"http://127.0.0.1:{self.server.server_address[1]}"
                if self.path == owner._API_UT:
                    body = json.dumps(
                        {
                            "tag_name": f"v{owner.verzio}",
                            "body": "Windows update integration test",
                            "html_url": f"{base}/release",
                            "assets": [
                                {
                                    "name": "PicasaPy-windows-x64.zip",
                                    "browser_download_url": base + owner._ZIP_UT,
                                },
                                {
                                    "name": "SHA256SUMS",
                                    "browser_download_url": base + owner._HASH_UT,
                                },
                            ],
                        }
                    ).encode("utf-8")
                    self._send(body, "application/vnd.github+json")
                elif self.path == owner._HASH_UT:
                    body = (
                        f"{owner.sha256}  PicasaPy-windows-x64.zip\n"
                    ).encode("ascii")
                    self._send(body, "text/plain; charset=us-ascii")
                elif self.path == owner._ZIP_UT:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Length", str(owner.zip_ut.stat().st_size))
                    self.end_headers()
                    with owner.zip_ut.open("rb") as source:
                        shutil.copyfileobj(source, self.wfile, length=1024 * 1024)
                else:
                    self.send_error(404)

            def _send(self, body: bytes, content_type: str) -> None:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        self._handler_type = Handler
        factory = server_factory or ThreadingHTTPServer
        self._server = factory(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def api_url(self) -> str:
        port = self._server.server_address[1]
        return f"http://127.0.0.1:{port}{self._API_UT}"

    def __enter__(self) -> _HelyiKiadasszerver:
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)

_KEP_MAPPANKENT = 50

_BEALLITAS_KULCS = r"Software\PicasaPy\PicasaPy\export"

_EXPORT_ERTEK = "exportedfolders"

__all__ = (
    "_BEALLITAS_KULCS",
    "_EXPORT_ERTEK",
    "_HelyiKiadasszerver",
    "_IDOKORLAT_MP",
    "_INDULOABLAK",
    "_KEP_MAPPANKENT",
    "_SIKER",
    "_SOR",
    "_futtatok",
    "_keszits_frissitesi_zip",
    "_platform",
    "_resz",
    "_sha256_fajl",
)
