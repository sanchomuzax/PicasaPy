"""QML-cache előállítási és indulási mérési segédek (#6374)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import time


class QmlWarmupError(RuntimeError):
    """A QML-előfordító gyermekfolyamata nem tudott elindulni vagy befejeződni."""


def _naplo_vege(naplo: Path, sorok: int = 8) -> str:
    try:
        return "\n".join(naplo.read_text(encoding="utf-8").splitlines()[-sorok:])
    except OSError:
        return "(a napló nem olvasható)"


def melegitsd_qml_cache(
    parancs: Sequence[str],
    kornyezet: Mapping[str, str],
    *,
    timeout: float = 180.0,
) -> str:
    """Az adott alkalmazásprofilban futtatja a QML-előfordítást."""
    env = dict(kornyezet)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    naplo = Path(env.get("TEMP") or env.get("TMPDIR") or "/tmp") / "picasapy-qml-elofordit.txt"
    naplo.parent.mkdir(parents=True, exist_ok=True)
    naplo.write_text("", encoding="utf-8")
    env["PICASAPY_QML_ELOFORDIT_NAPLO"] = str(naplo)
    try:
        result = subprocess.run(
            [*(str(elem) for elem in parancs), "--qml-elofordit"],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise QmlWarmupError(
            "a QML-előfordítás nem fejeződött be; a haladásnapló vége:\n"
            + _naplo_vege(naplo)
        ) from error
    if result.returncode != 0:
        raise QmlWarmupError(
            f"a QML-előfordítás {result.returncode} kilépőkóddal állt le; "
            "a haladásnapló vége:\n" + _naplo_vege(naplo)
        )
    return result.stdout.strip()


@dataclass(frozen=True)
class FrissitesiIndulasiIdok:
    """A sikeres önfrissítést követő indulás két naplózott ideje."""

    qml_betoltes_ms: float
    foablak_splash_utan_ms: float


_QML_SOR = re.compile(
    r"^\s*([\d.]+) ms\s+QML betöltése \(Main\.qml\) \(([\d.]+) ms\)\s*$"
)
_FOABLAK_SOR = re.compile(
    # a főablak első kirajzolt képkockája az indulási idővonalon (application.run)
    r"^\s*([\d.]+) ms\s+az ablak első kirajzolt képkockája(?:\s+\([\d.]+ ms\))?\s*$"
)


def _indulasi_idok(szoveg: str) -> FrissitesiIndulasiIdok | None:
    qml_ms = None
    foablak_ms = None
    for sor in szoveg.splitlines():
        qml = _QML_SOR.match(sor)
        if qml is not None:
            qml_ms = float(qml.group(2))
        foablak = _FOABLAK_SOR.match(sor)
        if foablak is not None:
            foablak_ms = float(foablak.group(1))
    if qml_ms is None or foablak_ms is None:
        return None
    return FrissitesiIndulasiIdok(qml_ms, foablak_ms)


def frissitesi_indulasi_idok(
    naplo: Path,
    *,
    timeout: float = 15.0,
    poll_interval: float = 0.05,
) -> FrissitesiIndulasiIdok:
    """Határidőig várja a friss program két indulási időjelzését."""
    naplo = Path(naplo)
    deadline = time.monotonic() + timeout
    while True:
        try:
            meres = _indulasi_idok(naplo.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            meres = None
        if meres is not None:
            return meres
        if time.monotonic() >= deadline:
            raise TimeoutError("a frissített program indulási naplója hiányos")
        time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))


def frissitesi_indulasi_hiba(
    meres: FrissitesiIndulasiIdok, hatar_mp: float = 5.0
) -> str | None:
    """Az 5 másodperces QML- és főablak-megjelenési kapu."""
    if meres.qml_betoltes_ms > hatar_mp * 1000:
        return (
            f"a Main.qml betöltése {meres.qml_betoltes_ms:.0f} ms, "
            f"a határ {hatar_mp:.1f} s"
        )
    if meres.foablak_splash_utan_ms > hatar_mp * 1000:
        return (
            f"a főablak a splash után {meres.foablak_splash_utan_ms / 1000:.2f} s "
            f"alatt jelent meg, a határ {hatar_mp:.1f} s"
        )
    return None


def frissitesi_indulasi_kapu(naplo: Path, *, timeout: float = 15.0) -> bool:
    """Kiírja és ellenőrzi az önfrissítés utáni első indulás két idejét."""
    try:
        meres = frissitesi_indulasi_idok(naplo, timeout=timeout)
    except TimeoutError as error:
        print(f"  ❌ frissites: {error}", flush=True)
        return False
    print(
        "  frissítés utáni első indulás: "
        f"QML betöltése (Main.qml) {meres.qml_betoltes_ms:.0f} ms; "
        "főablak a splash után "
        f"{meres.foablak_splash_utan_ms / 1000:.2f} s",
        flush=True,
    )
    hiba = frissitesi_indulasi_hiba(meres)
    if hiba is not None:
        print(f"  ❌ frissites: {hiba}", flush=True)
        return False
    return True


def windows_indulasi_naplo(kornyezet: Mapping[str, str] | None = None) -> Path:
    """A Windows-profil legutóbbi indítási naplója."""
    from .platform_storage import default_storage_paths

    env = os.environ if kornyezet is None else kornyezet
    return default_storage_paths("win32", environ=env).data / "indulas-utolso.txt"
