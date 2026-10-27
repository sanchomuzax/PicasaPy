"""A PhotoViewer képpontos mérőjének CI-őrtesztje (#5952)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from PySide6.QtGui import QColor, QImage

from scripts import photo_viewer_screenshots as screenshot_script


GYOKER = Path(__file__).resolve().parents[3]
MERO = GYOKER / "scripts" / "photo_viewer_screenshots.py"
ROGZITETT_MTIME_NS = 1_577_836_800_000_000_000
ALLAPOTOK = (
    "main-library",
    "people-album",
    "menu-file",
    "menu-edit",
    "menu-view",
    "menu-folder",
    "menu-picture",
    "menu-create",
    "menu-tools",
    "menu-help",
    "toolbar",
    "tray",
    "slideshow",
    "undo-all-edits",
    "drop-geotag",
    "mainSplit-min",
    "mainSplit-max",
    "photo-viewer",
    "alapnezet",
    "bal-fiok-nyitva",
    "filmcsik",
    "szerkeszto-0",
    "szerkeszto-1",
    "szerkeszto-2",
    "szerkeszto-3",
    "szerkeszto-4",
    "szerkeszto-5",
    "szerkeszto-6",
    "arcreteg",
    "teljes-kepernyo",
)


def _png(path: Path, szinek: dict[tuple[int, int], QColor]) -> None:
    image = QImage(5, 4, QImage.Format.Format_RGBA8888)
    image.fill(QColor("#202020"))
    for (x, y), color in szinek.items():
        image.setPixelColor(x, y, color)
    assert image.save(str(path), "PNG")


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MERO), *args],
        cwd=GYOKER,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=120,
    )


def _assert_capture_waits_past_a_late_preview_frame() -> None:
    stale = QImage(4, 3, QImage.Format.Format_RGBA8888)
    stale.fill(QColor("#142536"))
    settled = QImage(4, 3, QImage.Format.Format_RGBA8888)
    settled.fill(QColor("#abcdef"))

    class _Alkalmazas:
        @staticmethod
        def processEvents() -> None:
            pass

    class _Ablak:
        def __init__(self) -> None:
            self.frame = 0

        def grabWindow(self) -> QImage:
            self.frame += 1
            return stale if self.frame <= 3 else settled

    eredmeny = screenshot_script._stabil_ablakkepernyo(
        _Ablak(), _Alkalmazas(), "alapnezet"
    )
    assert screenshot_script._kep_bajtok(eredmeny) == screenshot_script._kep_bajtok(
        settled
    )


@pytest.mark.parametrize("height", (695, 700, 705))
def test_capture_creates_visible_main_and_viewer_states(
    tmp_path: Path, height: int
) -> None:
    output = tmp_path / "kepek"
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"

    result = _run(
        "capture",
        "--output",
        str(output),
        "--width",
        "1024",
        "--height",
        str(height),
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    records = {record["name"]: record for record in manifest["states"]}
    assert manifest["sample_photo_mtimes_ns"] == [ROGZITETT_MTIME_NS] * 3
    assert tuple(records) == ALLAPOTOK
    assert manifest["requested_size"] == {"width": 1024, "height": height}
    assert manifest["actual_window_size"] == {"width": 1024, "height": height}
    assert records["alapnezet"]["window_size"] == manifest["actual_window_size"]

    required = {
        "main-library": {
            "mainSplit",
            "folderPane",
            "folderListView",
            "albumRepeater",
            "photoGrid",
        },
        "people-album": {
            "mainSplit",
            "folderPane",
            "personAlbumHeader",
            "personAlbumName",
            "photoGrid",
        },
        "menu-file": {"menuFileAddFolder"},
        "menu-edit": {"menuEditCut"},
        "menu-view": {"menuViewLibraryView"},
        "menu-folder": {"menuFolderSlideshow"},
        "menu-picture": {"menuPictureViewAndEdit"},
        "menu-create": {"menuCreateCollage"},
        "menu-tools": {"menuToolsFolderManager"},
        "menu-help": {"menuHelpContents"},
        "toolbar": {"mainToolbar", "toolbarImportButton"},
        "tray": {"trayBar", "trayMainBar", "trayStarButton"},
        "slideshow": {"slideshowView", "slideshowImage"},
        "photo-viewer": {"photoViewer", "viewerPhotoArea", "viewerImage"},
        "undo-all-edits": {"undoAllEditsDialogLoader", "undoAllEditsDialog"},
        "drop-geotag": {"dropGeotagDialogLoader", "dropGeotagConfirm"},
        "mainSplit-min": {"mainSplit", "folderPane", "photoGrid"},
        "mainSplit-max": {"mainSplit", "folderPane", "photoGrid"},
        "alapnezet": {"photoViewer", "viewerPhotoArea", "viewerImage"},
        "bal-fiok-nyitva": {"photoViewer", "viewerLeftDrawer", "viewerEditorPanel"},
        "filmcsik": {"photoViewer", "viewerFilmstrip", "viewerImage"},
        "arcreteg": {"photoViewer", "facesOverlay", "viewerImage"},
        "teljes-kepernyo": {"photoViewer", "viewerImage"},
    }
    for index, tab_name in enumerate(
        (
            "editTabFixes",
            "editTabFinetune",
            "editTabEffects",
            "editTabEffects2",
            "editTabEffects3",
            "editTabEffects4",
            "editTabLegacy",
        )
    ):
        required[f"szerkeszto-{index}"] = {"photoViewer", "viewerEditorPanel", tab_name}

    assert set(records) == set(ALLAPOTOK)
    for name, record in records.items():
        png = output / record["file"]
        assert png.is_file() and png.stat().st_size > 0, f"{name}: hiányzó/üres PNG"
        image = QImage(str(png))
        assert not image.isNull(), f"{name}: a PNG nem olvasható"
        assert image.width() > 0 and image.height() > 0
        sampled_colors = {
            image.pixelColor(x, y).rgba()
            for y in range(0, image.height(), max(1, image.height() // 16))
            for x in range(0, image.width(), max(1, image.width() // 16))
        }
        assert len(sampled_colors) > 8, f"{name}: a képernyőkép üresnek látszik"
        assert required[name] <= set(record["visible_object_names"]), (
            f"{name}: nem látható kulcsobjektum: "
            f"{sorted(required[name] - set(record['visible_object_names']))}"
        )
    assert records["alapnezet"]["left_drawer_width"] <= 2
    assert records["bal-fiok-nyitva"]["left_drawer_width"] > 200
    assert records["filmcsik"]["filmstrip_count"] > 0
    assert [records[f"szerkeszto-{index}"]["active_tab"] for index in range(7)] == list(
        range(7)
    )
    assert records["arcreteg"]["face_count"] > 0
    assert records["teljes-kepernyo"]["fullscreen"] is True
    assert records["main-library"]["folder_count"] > 0
    assert records["main-library"]["album_count"] > 0
    assert records["main-library"]["thumbnail_sampled_colors"] > 1
    assert records["people-album"]["thumbnail_sampled_colors"] > 1
    assert records["people-album"]["person_name"] == "Teszt Elek"
    assert QImage(str(output / "photo-viewer.png")) == QImage(
        str(output / "alapnezet.png")
    )
    assert records["tray"]["tray_item_count"] > 0
    assert records["mainSplit-min"]["folder_pane_width"] <= 243
    assert abs(
        records["mainSplit-max"]["folder_pane_width"]
        - (records["mainSplit-max"]["main_split_width"] - 240)
    ) <= 3


@pytest.mark.parametrize("height", (695, 700, 705))
def test_two_consecutive_captures_are_pixel_identical_in_all_states(
    tmp_path: Path, height: int
) -> None:
    _assert_capture_waits_past_a_late_preview_frame()
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    before = tmp_path / "elso"
    after = tmp_path / "masodik"

    for output in (before, after):
        result = _run(
            "capture",
            "--output",
            str(output),
            "--width",
            "1024",
            "--height",
            str(height),
            env=env,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    result = _run(
        "compare",
        "--before",
        str(before),
        "--after",
        str(after),
        "--diff-dir",
        str(tmp_path / "kulonbseg"),
    )

    sorok = result.stdout.splitlines()
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(sorok) == len(ALLAPOTOK)
    assert all(sor.endswith(": 0 eltérő képpont") for sor in sorok), result.stdout


def test_capture_waits_past_a_late_preview_frame() -> None:
    _assert_capture_waits_past_a_late_preview_frame()


def test_compare_reports_exact_pixel_count_rectangle_and_diff(tmp_path: Path) -> None:
    before = tmp_path / "elotte"
    after = tmp_path / "utana"
    diffs = tmp_path / "kulonbseg"
    before.mkdir()
    after.mkdir()
    _png(before / "alapnezet.png", {})
    _png(
        after / "alapnezet.png",
        {
            (1, 1): QColor("#ffffff"),
            (3, 2): QColor("#00ff00"),
        },
    )

    result = _run(
        "compare",
        "--before",
        str(before),
        "--after",
        str(after),
        "--diff-dir",
        str(diffs),
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "2 eltérő képpont" in result.stdout
    assert "x=1, y=1, szélesség=3, magasság=2" in result.stdout
    diff = QImage(str(diffs / "alapnezet.diff.png"))
    assert not diff.isNull()
    assert diff.pixelColor(1, 1) == QColor("#ff00ff")
    assert diff.pixelColor(3, 2) == QColor("#ff00ff")
    assert diff.pixelColor(0, 0).alpha() == 0


def test_compare_returns_zero_for_pixel_identical_pngs(tmp_path: Path) -> None:
    before = tmp_path / "elotte"
    after = tmp_path / "utana"
    before.mkdir()
    after.mkdir()
    pixels = {(2, 1): QColor("#123456")}
    _png(before / "filmcsik.png", pixels)
    _png(after / "filmcsik.png", pixels)

    result = _run(
        "compare",
        "--before",
        str(before),
        "--after",
        str(after),
        "--diff-dir",
        str(tmp_path / "kulonbseg"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 eltérő képpont" in result.stdout


def test_compare_cp1252_kimenettel_sem_hasal_el(tmp_path: Path) -> None:
    """#5971: Windowson a konzol cp1252; az ékezetes kimenet nem bukhat el rajta."""
    before = tmp_path / "elotte"
    after = tmp_path / "utana"
    before.mkdir()
    after.mkdir()
    pixels = {(2, 1): QColor("#123456")}
    _png(before / "filmcsik.png", pixels)
    _png(after / "filmcsik.png", pixels)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    result = _run(
        "compare", "--before", str(before), "--after", str(after),
        "--diff-dir", str(tmp_path / "kulonbseg"), env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 eltérő képpont" in result.stdout
