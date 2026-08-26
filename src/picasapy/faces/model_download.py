"""Az arcfelismerő ONNX-modellek beszerzése — ELLENŐRZÖTT letöltéssel (#1496).

## Miért új modul, és miért ellenőriz

A `detector.download_model()`/`embedder.download_model()` a termékkódból
SEHONNAN nem hívódott (#1496 mérése), a `~/.local/share/picasapy/models/`
mappa létre sem jött. Friss telepítésen az „Arcok keresése…" gomb ezért
végig szürke maradt: a #1473 óta legalább megmondta, MIÉRT — de a
felhasználó (aki nem programozó) ettől még nem jutott modellhez.

A régi letöltő azonban **semmit nem ellenőrzött**: amit a kiszolgáló
adott, azt kiírta a modell helyére. Ez itt nem elméleti kockázat:

* Az OpenCV Zoo a modelleket **Git LFS**-ben tárolja. A
  `raw.githubusercontent.com` az ilyen fájlokra nem a modellt, hanem egy
  **131 bájtos szövegmutatót** ad (2026-08-26-i mérés: `content-length:
  131`); a valódi tartalmat a `media.githubusercontent.com` szolgálja ki,
  ahová a `github.com/…/raw/…` cím 302-vel átirányít. Egy elgépelt vagy
  elavult URL tehát némán egy szövegfájlt tenne a modell helyére.
* Egy félbeszakadt letöltésből fél modell marad. Az OpenCV ezt akár be is
  tölti, és a felismerés **némán, rosszul** működik — ez a legrosszabb
  fajta hiba: nincs hibaüzenet, csak rossz eredmény.

Ezért itt MINDEN letöltésre **méret + SHA-256** ellenőrzés fut, és a fájl
csak akkor kerül a helyére, ha mindkettő stimmel. A köztes írás
`.part` fájlba megy, ami hiba esetén törlődik — a már meglévő, működő
modellt egy elrontott újratöltés sem ronthatja el.

## Hálózat a termékkódban — PRECEDENS

A projektben eddig **egyetlen** hálózati hívás sem futott éles úton (a
`grep -rn "urllib\\|requests\\.\\|urlopen" src/` a `fileops/trash.py` és a
`mailer/command.py` `urllib.parse` — tehát tisztán sztringkezelés —
mellett csak ezt a két, hívatlan `download_model()`-t adta). Ez a modul
tehát új képességet vezet be, ezért:

* a letöltés SOHA nem indul magától — csak a felhasználó kifejezett
  gombnyomására (`FaceScanController.downloadModels`),
* a forrás **egyetlen, beállítható helyen** él
  (`PICASAPY_MODEL_BASE_URL` környezeti változó, ld. lent) — így a
  tesztek loopback-kiszolgálóra terelhetők, hálózat nélkül is,
* hiba SEHOL nem néma: minden ág megnevezett `status`-t ad vissza,
  kivétel nélkül.

## Licenc

| modell | fájl | méret | licenc |
|---|---|---|---|
| YuNet (detektálás) | `face_detection_yunet_2023mar.onnx` | 232 589 B | MIT |
| SFace (lenyomat) | `face_recognition_sface_2021dec.onnx` | 38 696 353 B | Apache-2.0 |

Mindkettő permisszív, tehát GPL-3.0-kompatibilis (a licencfájlok
2026-08-26-án az upstream repóból ellenőrizve). A modellek NEM kerülnek a
forrásfába és NEM részei a csomagnak — futásidőben, a felhasználó
adatmappájába töltődnek.
"""

from __future__ import annotations

import dataclasses
import hashlib
import http.client
import logging
import os
import threading
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from . import detector as _detector
from . import embedder as _embedder

logger = logging.getLogger(__name__)

#: A letöltés forrásának EGYETLEN beállítható fogantyúja. A modellek
#: relatív útvonala ehhez fűződik hozzá. A teszt ezt állítja a loopback-
#: kiszolgálójára — így a CI-nek hálózatra SOHA nincs szüksége.
MODEL_BASE_URL_ENV_VAR = "PICASAPY_MODEL_BASE_URL"

#: Az alapértelmezett forrás. SZÁNDÉKOSAN a `github.com/…/raw/…` alak: ez
#: 302-vel a `media.githubusercontent.com`-ra megy, ami a Git LFS valódi
#: tartalmát adja. A `raw.githubusercontent.com` UGYANERRE az útvonalra a
#: 131 bájtos LFS-mutatót adná — ezt az épség-ellenőrzés kifogná, de a
#: felhasználót fölöslegesen megbuktatná.
DEFAULT_MODEL_BASE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models"

#: Ekkora darabokban olvasunk — elég nagy, hogy a 37 MB-os SFace se
#: darabolódjon értelmetlenül sok részre, elég kicsi, hogy a haladásjelző
#: és a megszakítás finoman reagáljon.
_CHUNK_SIZE = 256 * 1024

#: A letöltés kimenetei. Sztring-konstansok (nem `Enum`): a hívó vezérlő
#: ezekre képezi a felhasználói mondatait, és így a Qt-jelzéseken is
#: átmennek konverzió nélkül.
STATUS_OK = "ok"
STATUS_CANCELLED = "cancelled"
STATUS_NETWORK = "network"
STATUS_CORRUPT = "corrupt"
STATUS_DISK = "disk"

#: `progress(letöltött_bájt, várt_összes_bájt)` — a hívó szálon hívódik.
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class ModelSpec:
    """Egy letölthető modell — MÉRETTEL és ELLENŐRZŐÖSSZEGGEL együtt.

    A `size_bytes`/`sha256` nem díszítés: enélkül a letöltés nem tudná
    megkülönböztetni a modellt egy fél fájltól vagy egy hibaoldaltól."""

    key: str
    filename: str
    relative_url: str
    size_bytes: int
    sha256: str
    license_name: str
    #: Emberi nyelvű megnevezés a felületnek (mit csinál ez a modell).
    purpose: str

    def default_path(self) -> Path:
        """A modell helye a felhasználó adatmappájában.

        MINDKÉT modell ugyanabba a mappába kerül (`detector.
        default_model_dir()`), ezért nevezhet meg a felületi üzenet
        egyetlen mappát."""
        return _detector.default_model_dir() / self.filename

    def masolat(self, **valtozasok) -> ModelSpec:
        """Módosított másolat — a mezők NEM íródnak felül (immutábilis).

        A teszteké: helyi kiszolgálóhoz kicsi tartalom kell, saját
        mérettel és összeggel."""
        return dataclasses.replace(self, **valtozasok)


DETECTOR_SPEC = ModelSpec(
    key="detector",
    filename=_detector.MODEL_FILENAME,
    relative_url=f"face_detection_yunet/{_detector.MODEL_FILENAME}",
    # 2026-08-26, `gh api repos/opencv/opencv_zoo/contents/…` → a Git LFS
    # mutató `oid`/`size` mezője. Az upstream fájl SOHA nem változik a
    # helyén (a dátum a nevében van), ezért ez rögzíthető.
    size_bytes=232589,
    sha256="8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
    license_name="MIT",
    purpose="face detection (YuNet)",
)

EMBEDDER_SPEC = ModelSpec(
    key="embedder",
    filename=_embedder.MODEL_FILENAME,
    relative_url=f"face_recognition_sface/{_embedder.MODEL_FILENAME}",
    size_bytes=38696353,
    sha256="0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
    license_name="Apache-2.0",
    purpose="face grouping (SFace)",
)

#: A sorrend számít: előbb a detektálás (227 KB), utána a lenyomat
#: (37 MB) — a felhasználó így a keresést már azelőtt elindíthatná, hogy a
#: nagyobb fájl megjön.
MODEL_SPECS: tuple[ModelSpec, ...] = (DETECTOR_SPEC, EMBEDDER_SPEC)


@dataclass(frozen=True)
class DownloadResult:
    """Egy modell letöltésének kimenete — SOHA nem kivétel, mindig érték."""

    status: str
    spec: ModelSpec
    path: Path | None = None
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == STATUS_OK


def model_base_url(base_url: str | None = None) -> str:
    """A forrás gyökere: a paraméter, a környezeti változó, vagy az
    alapértelmezés — ebben a sorrendben. A záró perjelet levágja."""
    forras = base_url or os.environ.get(MODEL_BASE_URL_ENV_VAR) or DEFAULT_MODEL_BASE_URL
    return forras.rstrip("/")


def model_url(spec: ModelSpec, base_url: str | None = None) -> str:
    """Egy modell teljes letöltési címe."""
    return f"{model_base_url(base_url)}/{spec.relative_url}"


def missing_specs() -> tuple[ModelSpec, ...]:
    """Azok a modellek, amelyek MOST nincsenek meg a lemezen.

    A meglétet a két csomag saját feloldója mondja meg
    (`detector.resolve_model_path` / `embedder.resolve_model_path`), tehát
    a `PICASAPY_FACE_MODEL`-lel máshová mutatott fájl is meglévőnek
    számít — nem töltünk le olyat, ami már megvan."""
    jelen = {
        "detector": _detector.resolve_model_path(),
        "embedder": _embedder.resolve_model_path(),
    }
    return tuple(spec for spec in MODEL_SPECS if jelen.get(spec.key) is None)


def total_missing_bytes() -> int:
    """A hiányzó modellek együttes mérete — ennyit kell letölteni."""
    return sum(spec.size_bytes for spec in missing_specs())


def _ellenorzes_hibaja(spec: ModelSpec, meret: int, digest: str) -> str:
    """A meghiúsult épség-ellenőrzés MEGNEVEZETT oka (naplóhoz, nem UI-hoz)."""
    if meret != spec.size_bytes:
        return (
            f"a letöltött fájl mérete {meret} bájt, a várt {spec.size_bytes} "
            f"helyett ({spec.filename})"
        )
    return (
        f"a letöltött fájl ellenőrzőösszege {digest}, a várt {spec.sha256} "
        f"helyett ({spec.filename})"
    )


def download_spec(
    spec: ModelSpec,
    *,
    dest: Path | str | None = None,
    base_url: str | None = None,
    url: str | None = None,
    timeout: float = 30.0,
    chunk_size: int = _CHUNK_SIZE,
    progress: ProgressCallback | None = None,
    cancel: threading.Event | None = None,
) -> DownloadResult:
    """EGY modell letöltése, méret- és SHA-256-ellenőrzéssel.

    SOHA nem dob kivételt: minden ág `DownloadResult`-tal tér vissza,
    megnevezett `status`-szal. A fájl csak akkor kerül a helyére, ha az
    ellenőrzés átment — addig `.part` kiterjesztésű ideiglenes fájlba
    írunk, amit minden hibaágon törlünk. Így egy már meglévő, működő
    modellt egy elrontott újratöltés sem ronthat el.

    A `progress` a HÍVÓ szálon hívódik, minden beolvasott darab után; a
    `cancel` esemény darabhatáron szakítja meg a letöltést. A
    `chunk_size` a tesztek fogantyúja: kicsi darabokkal a megszakítás és
    a haladásjelzés apró fájlon is megfigyelhető."""
    cel = Path(dest) if dest is not None else spec.default_path()
    reszleges = cel.with_suffix(cel.suffix + ".part")
    if cancel is not None and cancel.is_set():
        return DownloadResult(STATUS_CANCELLED, spec)

    cim = url or model_url(spec, base_url)
    try:
        cel.parent.mkdir(parents=True, exist_ok=True)
    except OSError as hiba:
        logger.warning("A modell mappája nem hozható létre (%s): %s", hiba, cel.parent)
        return DownloadResult(STATUS_DISK, spec, detail=str(hiba))

    letoltott = 0
    digest = hashlib.sha256()
    try:
        try:
            with urllib.request.urlopen(cim, timeout=timeout) as valasz:  # noqa: S310
                with reszleges.open("wb") as ki:
                    while True:
                        if cancel is not None and cancel.is_set():
                            return DownloadResult(STATUS_CANCELLED, spec)
                        darab = valasz.read(chunk_size)
                        if not darab:
                            break
                        ki.write(darab)
                        digest.update(darab)
                        letoltott += len(darab)
                        if letoltott > spec.size_bytes:
                            # Már biztosan nem a modell — felesleges
                            # végigtölteni (a 37 MB-os SFace helyén egy
                            # hibaoldal is lehet tetszőlegesen hosszú).
                            return DownloadResult(
                                STATUS_CORRUPT,
                                spec,
                                detail=_ellenorzes_hibaja(spec, letoltott, ""),
                            )
                        if progress is not None:
                            progress(letoltott, spec.size_bytes)
        except (OSError, ValueError, http.client.HTTPException) as hiba:
            # A `URLError`/`HTTPError` és a socket-hibák egyaránt `OSError`
            # leszármazottak, a megszakadt válasz pedig `HTTPException` —
            # a felhasználónak mindegyik ugyanaz: „nem érem el a forrást".
            # Hogy pontosan mi történt, azt a napló mondja meg.
            logger.warning(
                "Az arcfelismerő modell letöltése sikertelen (%s): %s", hiba, cim
            )
            return DownloadResult(STATUS_NETWORK, spec, detail=str(hiba))

        osszeg = digest.hexdigest()
        if letoltott != spec.size_bytes or osszeg != spec.sha256:
            indok = _ellenorzes_hibaja(spec, letoltott, osszeg)
            logger.warning(
                "Az arcfelismerő modell épség-ellenőrzése MEGBUKOTT: %s", indok
            )
            return DownloadResult(STATUS_CORRUPT, spec, detail=indok)

        try:
            # Az ellenőrzés átment — CSAK MOST kerülhet a helyére. Az
            # átnevezés atomi: félkész fájlt a betöltő SOHA nem lát.
            os.replace(reszleges, cel)
        except OSError as hiba:
            logger.warning("A letöltött modell nem tehető a helyére (%s): %s", hiba, cel)
            return DownloadResult(STATUS_DISK, spec, detail=str(hiba))
        return DownloadResult(STATUS_OK, spec, path=cel)
    finally:
        # A `.part` a sikeres átnevezéskor már nincs a helyén; minden más
        # ágon (hiba, megszakítás, kivétel) ITT takarítjuk el.
        reszleges.unlink(missing_ok=True)


def download_missing(
    *,
    base_url: str | None = None,
    timeout: float = 30.0,
    chunk_size: int = _CHUNK_SIZE,
    progress: ProgressCallback | None = None,
    cancel: threading.Event | None = None,
) -> tuple[DownloadResult, ...]:
    """A hiányzó modellek letöltése, ÖSSZESÍTETT haladásjelzéssel.

    Az első sikertelen modellnél megáll: hálózat nélkül értelmetlen
    másodszor is kivárni az időtúllépést a felhasználóval."""
    hianyzo = missing_specs()
    osszes = sum(spec.size_bytes for spec in hianyzo)
    eredmenyek: list[DownloadResult] = []
    eddig = 0
    for spec in hianyzo:
        eltolas = eddig

        def _reszhaladas(kesz: int, _varhato: int, eltolas: int = eltolas) -> None:
            if progress is not None:
                progress(eltolas + kesz, osszes)

        eredmeny = download_spec(
            spec,
            base_url=base_url,
            timeout=timeout,
            chunk_size=chunk_size,
            progress=_reszhaladas,
            cancel=cancel,
        )
        eredmenyek.append(eredmeny)
        if not eredmeny.ok:
            break
        eddig += spec.size_bytes
    return tuple(eredmenyek)
