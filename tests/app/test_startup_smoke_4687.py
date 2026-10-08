"""#4687: a valós forrásindítás a splash után megjeleníti a főablakot."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from support.jpeg_factory import make_jpeg


@pytest.mark.parametrize("library_state", ("clean", "existing_faces"))
def test_a_fooldal_a_splash_utan_megjelenik_offscreenen(
    library_state: str, tmp_path: Path
) -> None:
    repo = Path(__file__).resolve().parents[2]
    case_dir = tmp_path / library_state
    library = case_dir / "library"
    library.mkdir(parents=True)

    if library_state == "existing_faces":
        photo = library / "a.jpg"
        make_jpeg(photo, size=(640, 480))
        (library / ".picasa.ini").write_text(
            "[Contacts2]\n8e62b2035b74b477=Ada Lovelace;;\n\n"
            "[a.jpg]\nfaces=rect64(3f845bcb59418507),8e62b2035b74b477\n",
            encoding="utf-8",
        )

    profile = case_dir / "profile"
    profile.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "PICASAPY_LANG": "en",
        }
    )
    subprocess_timeout = float(env.get("PICASAPY_STARTUP_SMOKE_TIMEOUT", "30"))
    if os.name == "nt":
        env.update(
            {
                "USERPROFILE": str(profile),
                "APPDATA": str(profile / "AppData" / "Roaming"),
                "LOCALAPPDATA": str(profile / "AppData" / "Local"),
                "TEMP": str(profile / "Temp"),
                "TMP": str(profile / "Temp"),
            }
        )
    else:
        env.update(
            {
                "XDG_CONFIG_HOME": str(profile / ".config"),
                "XDG_DATA_HOME": str(profile / ".local" / "share"),
                "XDG_CACHE_HOME": str(profile / ".cache"),
            }
        )

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(repo / "picasapy"),
                "--indulasellenorzes",
                str(library),
            ],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=subprocess_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(f"az indulási füstpróba nem zárult le időben: {error}")

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "startup-smoke passed: main window shown after splash" in output
    assert "PySide6" in output and "Qt" in output

    logs = list(profile.rglob("errorlog.txt"))
    assert len(logs) == 1, "az indulásnak a tesztprofil hibanaplójába kell írnia"
    log = logs[0].read_text(encoding="utf-8")
    assert re.search(r"^\d{4}-\d\d-\d\dT[^ ]+ INFO picasapy\.startup:", log, re.M)
    for stage in (
        "PySide6",
        "Korai indulási hibanapló elérhető",
        "Felület-betűtípus betöltése elkezdődött",
        "Felület-betűtípus betöltve",
        "Index megnyitása elkezdődött",
        "Main.qml betöltése elkezdődött",
        "Első főablak-képkocka; a rács megjelent",
        "Induláskori könyvtárszinkron indítása",
        "Az induláskori könyvtárszinkron befejeződött",
        "A főablak a splash után megjelent",
    ):
        assert stage in log, f"hiányzik az indulási naplóból: {stage}"
