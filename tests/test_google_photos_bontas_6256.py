"""A Google Fotók-modul bontása őrizze meg a régi homlokzatot és forrást."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import picasapy.google_photos as google_photos


_GYOKER = Path(__file__).resolve().parents[1]
_FORRAS = _GYOKER / "src" / "picasapy"
_MODULOK = (
    "google_photos.py",
    "google_photos_common.py",
    "google_photos_api.py",
    "google_photos_oauth.py",
)

# A bontás előtti google_photos.py legfelső szintű osztályainak és
# függvényeinek UTF-8 forrásszöveg-lenyomata a dekorátortól a záró sorig.
# AST-t csak a forrástartomány megkeresésére használunk; az ast.dump
# Python-verziónként eltérne.
_EREDETI_FORRAS_SHA256 = {
    "GooglePhotosError": "cd068cbac4b3e2d436b57b05199dafefcaf9cf51bb87052b3e968d65b71bd29e",
    "HttpResponse": "0c0c6cfd6b9dcd28ab8e129ca5bae1fce2ee24c44d1753b0333ad9691a82f09d",
    "HttpTransport": "33706b061402884ad6d109b4c1b5f45ea7b0285885c03b475060e6bccff7b82f",
    "UrllibTransport": "70dd0b0e2601316626b1769c094d66d4676f657bf94fcdf3954245b3da001362",
    "GooglePhotosApiClient": "25d11c4ba61ed5fd04635f3d45ed505809f9a64110a72b664a8e048fe6da02c0",
    "OAuthClient": "1d251b86ced95b097d948fd0419a5d6ab2ce2f04fed927320605f50e761b41f5",
    "CredentialStore": "6c7f2e4dfbfc7ede1c2615cddb95be262e261d98cd7a5ed997c1f6e81d92e064",
    "LoopbackOAuthSession": "060d96502193a7fbc2b78027b130c043bc51991187d04ddfdd8dba98d788dba0",
    "_prepare_photo": "3877bc02e88016d9640b1fd8c56162a822ed164fbf9ef0d9b02a58173282c2cc",
    "_safe_filename": "e3df9bd7a23cba8d66855d1eb98640c3f76dd47d996aa9b6c3712683fa42e997",
    "_response_has_quota_error": "7b42586ce2200082d495323152ea2bb5f94524285ea530fe432e9fcc4e4e3df5",
    "_oauth_error": "4708e9d6f0510d306bf098943b47b524f793d9594b562fcbb9ff5b80f8d4b3e2",
}

# A korábbi modul minden látható neve, az importált kompatibilitási nevekkel
# együtt. A google_photos importútvonalon ezek változatlanul elérhetők.
_EREDETI_NYILVANOS_NEVEK = {
    "BaseHTTPRequestHandler",
    "BytesIO",
    "Callable",
    "CredentialStore",
    "DEFAULT_UPLOAD_MAX_SIDE",
    "GOOGLE_OAUTH_AUTH_URL",
    "GOOGLE_OAUTH_REVOKE_URL",
    "GOOGLE_OAUTH_TOKEN_URL",
    "GOOGLE_PHOTOS_API_BASE_URL",
    "GOOGLE_PHOTOS_SCOPE",
    "GooglePhotosApiClient",
    "GooglePhotosError",
    "HTTPError",
    "HTTPServer",
    "HttpResponse",
    "HttpTransport",
    "Image",
    "ImageOps",
    "LoopbackOAuthSession",
    "MAX_BATCH_SIZE",
    "MAX_PHOTO_BYTES",
    "Mapping",
    "OAuthClient",
    "Path",
    "ProgressCallback",
    "Protocol",
    "Request",
    "Sequence",
    "URLError",
    "UnidentifiedImageError",
    "UrllibTransport",
    "annotations",
    "base64",
    "dataclass",
    "hashlib",
    "json",
    "keyring",
    "mimetypes",
    "parse_qs",
    "secrets",
    "threading",
    "time",
    "urlencode",
    "urlopen",
    "urlparse",
}


def _forras_hash(forras: bytes, node: ast.AST) -> str:
    sorok = forras.splitlines(keepends=True)
    eleje = min(
        [node.lineno, *(decorator.lineno for decorator in getattr(node, "decorator_list", []))]
    )
    reszlet = b"".join(sorok[eleje - 1 : node.end_lineno])
    return hashlib.sha256(reszlet).hexdigest()


def _definicio_hashok() -> dict[str, str]:
    lenyomatok: dict[str, str] = {}
    for nev in _MODULOK:
        utvonal = _FORRAS / nev
        if not utvonal.is_file():
            continue
        forras = utvonal.read_bytes().replace(b"\r\n", b"\n")  # windowsos checkout: CRLF (#6260)
        fa = ast.parse(forras.decode("utf-8"), filename=str(utvonal))
        for node in fa.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert node.name not in lenyomatok, f"többszörös definíció: {node.name}"
                lenyomatok[node.name] = _forras_hash(forras, node)
    return lenyomatok


def _ellenorizd_a_regi_nevteret() -> None:
    aktualis = {nev for nev in vars(google_photos) if not nev.startswith("_")}
    assert aktualis == _EREDETI_NYILVANOS_NEVEK, (
        "megváltozott a picasapy.google_photos nyilvános névtere: "
        f"hiányzik={sorted(_EREDETI_NYILVANOS_NEVEK - aktualis)}, "
        f"új={sorted(aktualis - _EREDETI_NYILVANOS_NEVEK)}"
    )


def _ellenorizd_a_forrashashokat() -> None:
    aktualis = _definicio_hashok()
    assert aktualis == _EREDETI_FORRAS_SHA256, (
        "a bontás előtti függvény/osztály forrásszövege megváltozott vagy hiányzik: "
        f"hiányzó/új={sorted(set(aktualis) ^ set(_EREDETI_FORRAS_SHA256))}; "
        "eltérő lenyomat="
        f"{sorted(nev for nev in aktualis.keys() & _EREDETI_FORRAS_SHA256.keys() if aktualis[nev] != _EREDETI_FORRAS_SHA256[nev])}"
    )


def _ellenorizd_a_modulhatarokat() -> None:
    hianyzik = [nev for nev in _MODULOK if not (_FORRAS / nev).is_file()]
    assert not hianyzik, f"hiányzó homlokzat vagy bontott modul: {hianyzik}"
    tulhosszu = {
        nev: len((_FORRAS / nev).read_text(encoding="utf-8").splitlines())
        for nev in _MODULOK
        if len((_FORRAS / nev).read_text(encoding="utf-8").splitlines()) >= 400
    }
    assert not tulhosszu, f"400 soros határt elérő Google Fotók-modulok: {tulhosszu}"


def _ellenorizd_a_patchpontokat() -> None:
    homlokzat = vars(google_photos)
    assert google_photos.CredentialStore.__init__.__globals__ is homlokzat
    assert google_photos.LoopbackOAuthSession._create_server.__globals__ is homlokzat
    assert google_photos.LoopbackOAuthSession._listen.__globals__ is homlokzat


def test_a_bontas_megorizza_a_regi_api_forrast_es_patchpontokat() -> None:
    _ellenorizd_a_regi_nevteret()
    _ellenorizd_a_forrashashokat()
    _ellenorizd_a_patchpontokat()
    _ellenorizd_a_modulhatarokat()
