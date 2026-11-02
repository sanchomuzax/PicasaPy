#!/usr/bin/env python3
"""Merge arm64 and x86_64 macOS application bundles into a Universal 2 bundle.

Usage:
    python merge_universal.py <arm64_app> <x86_64_app> <output_app>

Heavy Python C-extensions (such as OpenCV, rawpy, pillow) are distributed on PyPI
as separate arm64 and x86_64 wheels rather than universal2 wheels. This utility
combines standalone arm64 and x86_64 PicasaPy.app bundles into a single Universal 2
fat bundle using Apple's `lipo` tool and re-signs the resulting bundle.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def is_macho(path: Path) -> bool:
    """Return True if path is a Mach-O binary recognised by lipo."""
    if not path.is_file() or path.is_symlink():
        return False
    try:
        proc = subprocess.run(
            ["lipo", "-info", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return proc.returncode == 0
    except OSError:
        return False


def get_architectures(path: Path) -> set[str]:
    """Return set of architectures in a Mach-O binary ('x86_64', 'arm64', etc.)."""
    try:
        proc = subprocess.run(
            ["lipo", "-info", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        output = proc.stdout.strip()
        # Output looks like: "Non-fat file: ... is architecture: arm64"
        # or "Architectures in the fat file: ... are: x86_64 arm64"
        if "are:" in output:
            return set(output.split("are:")[-1].split())
        if "architecture:" in output:
            return set(output.split("architecture:")[-1].split())
        return set()
    except (subprocess.SubprocessError, OSError):
        return set()


def merge_bundles(arm64_app: Path, x86_app: Path, output_app: Path) -> None:
    if not arm64_app.is_dir():
        raise FileNotFoundError(f"arm64 bundle not found: {arm64_app}")
    if not x86_app.is_dir():
        raise FileNotFoundError(f"x86_64 bundle not found: {x86_app}")

    print(f"Preparing Universal bundle at: {output_app}")
    if output_app.exists():
        if output_app.is_dir():
            shutil.rmtree(output_app)
        else:
            output_app.unlink()

    # Base copy from arm64
    shutil.copytree(arm64_app, output_app, symlinks=True)

    merged_count = 0
    skipped_count = 0

    for out_file in output_app.rglob("*"):
        if not out_file.is_file() or out_file.is_symlink():
            continue

        if not is_macho(out_file):
            continue

        rel = out_file.relative_to(output_app)
        x86_file = x86_app / rel

        if not x86_file.is_file():
            print(f"Warning: {rel} missing in x86_64 bundle, keeping arm64 slice only")
            continue

        if not is_macho(x86_file):
            continue

        out_archs = get_architectures(out_file)
        x86_archs = get_architectures(x86_file)

        if "x86_64" in out_archs and "arm64" in out_archs:
            # Already universal
            skipped_count += 1
            continue

        if "arm64" in out_archs and "x86_64" in x86_archs:
            # Combine arm64 and x86_64 slices with lipo
            tmp_out = out_file.with_name(out_file.name + ".lipo_tmp")
            try:
                subprocess.run(
                    ["lipo", "-create", str(out_file), str(x86_file), "-output", str(tmp_out)],
                    check=True,
                )
                tmp_out.replace(out_file)
                merged_count += 1
            except subprocess.SubprocessError as err:
                if tmp_out.exists():
                    tmp_out.unlink()
                print(f"Error merging {rel}: {err}", file=sys.stderr)
                raise

    print(f"Merged {merged_count} Mach-O binaries into Universal fat binaries (already universal: {skipped_count}).")

    # Strip Apple quarantine and Finder extended attributes before code signing
    subprocess.run(["xattr", "-cr", str(output_app)], check=False)

    # Re-sign the bundle ad-hoc
    print("Re-signing the Universal bundle...")
    subprocess.run(
        ["codesign", "--force", "--deep", "-s", "-", str(output_app)],
        check=True,
    )

    main_bin = output_app / "Contents" / "MacOS" / "PicasaPy"
    if main_bin.is_file():
        archs = get_architectures(main_bin)
        print(f"Universal bundle created successfully. Main binary architectures: {', '.join(sorted(archs))}")
        if not ({"arm64", "x86_64"} <= archs):
            raise RuntimeError(f"Main binary does not contain both arm64 and x86_64: {archs}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm64_app", type=Path, help="Path to arm64 PicasaPy.app")
    parser.add_argument("x86_64_app", type=Path, help="Path to x86_64 PicasaPy.app")
    parser.add_argument("output_app", type=Path, help="Target path for Universal PicasaPy.app")
    args = parser.parse_args()

    merge_bundles(args.arm64_app, args.x86_64_app, args.output_app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
