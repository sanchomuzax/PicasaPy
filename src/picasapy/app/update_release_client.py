"""GitHub-kiadási adatok, verzió-összehasonlítás és hálózati kliens."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from collections.abc import Callable
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

REPOSITORY = "sanchomuzax/PicasaPy"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
WINDOWS_ASSET_NAME = "PicasaPy-windows-x64.zip"
UPDATE_API_ENV = "PICASAPY_UPDATE_API"


def _latest_release_api_url(environ: dict[str, str] | None = None) -> str:
    """Tesztben helyi API-ra irányít, éles alapértéket változatlanul hagyva."""
    source = os.environ if environ is None else environ
    override = str(source.get(UPDATE_API_ENV, "") or "").strip()
    if not override:
        return LATEST_RELEASE_API
    try:
        parsed = urlsplit(override)
        host = (parsed.hostname or "").casefold()
        port = parsed.port
    except ValueError as error:
        raise ValueError(
            "A PICASAPY_UPDATE_API csak helyi (127.0.0.1 vagy localhost) "
            "http-címet fogadhat el"
        ) from error
    if (
        parsed.scheme != "http"
        or host not in {"127.0.0.1", "localhost"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise ValueError(
            "A PICASAPY_UPDATE_API csak helyi (127.0.0.1 vagy localhost) "
            "http-címet fogadhat el"
        )
    return override


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    name: str
    download_url: str


@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    version: str
    notes: str
    url: str
    assets: tuple[ReleaseAsset, ...]

    def asset(self, name: str) -> ReleaseAsset | None:
        return next((asset for asset in self.assets if asset.name == name), None)


def _version_parts(value: str) -> tuple[tuple[int, ...], int, int] | None:
    """A kiadási verzió számait és előkiadási rangját adja vissza."""
    match = re.fullmatch(
        r"v?(\d+(?:\.\d+)*)(?:(?:-|\.)?(dev|a|alpha|b|beta|rc)(?:[.-]?(\d+))?)?"
        r"(?:\+[0-9A-Za-z.-]+)?",
        value.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    numbers = tuple(int(part) for part in match.group(1).split("."))
    stage = (match.group(2) or "").lower()
    stage_rank = {"dev": 0, "a": 1, "alpha": 1, "b": 2, "beta": 2, "rc": 3}
    return numbers, stage_rank.get(stage, 4), int(match.group(3) or 0)


def release_is_newer(latest: str, current: str) -> bool:
    """Igaz, ha a latest szemantikus kiadásverziója nagyobb a futónál."""
    newest = _version_parts(latest)
    installed = _version_parts(current)
    if newest is None or installed is None:
        return False
    width = max(len(newest[0]), len(installed[0]))
    left = (*newest[0], *(0 for _ in range(width - len(newest[0]))))
    right = (*installed[0], *(0 for _ in range(width - len(installed[0]))))
    return (left, newest[1], newest[2]) > (right, installed[1], installed[2])


def automatic_check_is_due(*, enabled: bool = True) -> bool:
    """Az automatikus keresés minden indításkor és időzítéskor fut, ha be van kapcsolva.

    #6379: a korábbi napi korlát miatt a napközben kiadott verziót a program
    csak másnap vette észre. Az értesítés verziónként egyszer jön
    (`NOTIFIED_VERSION_KEY`), így a gyakoribb keresés nem tolakodó.
    """
    return enabled


_HTML_MEGJEGYZES = re.compile(r"<!--.*?-->", re.DOTALL)
_KEPHIVATKOZAS = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_HIVATKOZAS = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_KIEMELES = re.compile(r"(\*\*|__|`)")
_LISTAJEL = re.compile(r"^(\s*)[*+-]\s+")
_CIMSOR = re.compile(r"^\s*#{1,6}\s*")


def olvashato_jegyzet(body: str) -> str:
    """A GitHub-kiadás Markdown-leírása olvasható sima szövegként (#6358).

    A frissítési ablak sima szöveget mutat: a címsor- és listajel, a
    kiemelés, a képhivatkozás és a rejtett megjegyzés kimarad, a
    hivatkozásból a felirata marad. Az egymást követő üres sorok egyre
    rövidülnek."""
    szoveg = _HTML_MEGJEGYZES.sub("", body or "")
    sorok: list[str] = []
    for sor in szoveg.splitlines():
        sor = _KEPHIVATKOZAS.sub("", sor)
        sor = _HIVATKOZAS.sub(r"\1", sor)
        sor = _CIMSOR.sub("", sor)
        sor = _LISTAJEL.sub(lambda m: m.group(1) + "• ", sor)
        sor = _KIEMELES.sub("", sor).rstrip()
        if not sor.strip() and (not sorok or not sorok[-1]):
            continue
        sorok.append(sor if sor.strip() else "")
    return "\n".join(sorok).strip()


class GitHubReleaseClient:
    """A GitHub Releases API és asset letöltésének behelyettesíthető kliensrétege."""

    def __init__(
        self,
        *,
        opener: Callable[..., object] | None = None,
        timeout: float = 8.0,
    ) -> None:
        self._opener = opener or urlopen
        self.timeout = timeout

    def _read(self, url: str, *, accept: str = "application/vnd.github+json") -> bytes:
        request = Request(
            url,
            headers={"Accept": accept, "User-Agent": "PicasaPy-updater"},
        )
        with self._opener(request, timeout=self.timeout) as response:
            return response.read()

    def latest_release(self) -> ReleaseInfo:
        """A GitHub `releases/latest` végpontjáról beolvassa a kiadás adatait."""
        raw = json.loads(self._read(_latest_release_api_url()).decode("utf-8"))
        assets = tuple(
            ReleaseAsset(str(asset["name"]), str(asset["browser_download_url"]))
            for asset in raw.get("assets", [])
            if asset.get("name") and asset.get("browser_download_url")
        )
        tag = str(raw.get("tag_name", "")).strip()
        if not tag:
            raise ValueError("A GitHub-kiadás nem tartalmaz verziócímkét")
        return ReleaseInfo(
            version=tag.removeprefix("v"),
            notes=str(raw.get("body", "") or ""),
            url=str(raw.get("html_url", "") or f"https://github.com/{REPOSITORY}/releases/latest"),
            assets=assets,
        )

    def download(
        self,
        asset: ReleaseAsset,
        *,
        progress: Callable[[int, int], None] | None = None,
    ) -> bytes:
        """Darabokban tölti le az assetet, opcionális bájt-haladás jelzéssel."""
        request = Request(asset.download_url, headers={"User-Agent": "PicasaPy-updater"})
        chunks: list[bytes] = []
        received = 0
        with self._opener(request, timeout=self.timeout) as response:
            total = int(response.headers.get("Content-Length", "0") or 0)
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)
                if progress:
                    progress(received, total)
        return b"".join(chunks)

    def download_to(
        self,
        asset: ReleaseAsset,
        destination: Path,
        *,
        progress: Callable[[int, int], None] | None = None,
    ) -> str:
        """Közvetlenül fájlba tölt, menet közben számolt SHA-256-tal (#6340).

        A Windows-csomag ~200 MB: a memóriába gyűjtés (`download`) a darabok
        és az összefűzött másolat miatt ennek a kétszeresét foglalná."""
        request = Request(asset.download_url, headers={"User-Agent": "PicasaPy-updater"})
        digest = hashlib.sha256()
        received = 0
        with self._opener(request, timeout=self.timeout) as response, destination.open(
            "wb"
        ) as out:
            total = int(response.headers.get("Content-Length", "0") or 0)
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                received += len(chunk)
                if progress:
                    progress(received, total)
        return digest.hexdigest()
