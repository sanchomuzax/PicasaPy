# PicasaPy — macOS Packaging

This directory contains the packaging tooling for building standalone macOS application bundles (`PicasaPy.app`) and installer disk images (`.dmg`).

Supported architectures:
1. **Apple Silicon / M1 (arm64)**: Native build for Apple Silicon Macs (M1, M2, M3, M4). Smaller package size, zero Rosetta overhead.
2. **Universal 2 (arm64 + x86_64)**: Fat binary bundle that runs natively on both Apple Silicon and legacy Intel Macs.

---

## Why Universal 2 Requires `lipo`

PyPI distributes certain heavy C-extension dependencies (specifically `opencv-python-headless`, `rawpy`, and `pillow`) as separate single-architecture wheels (`arm64` and `x86_64`) rather than `universal2` wheels. 

Running `pyinstaller --target-arch universal2` in a standard single-architecture Python environment fails because the installed dependency `.so`/`.dylib` files only contain a single architecture slice.

To produce a 100% compliant Apple Universal 2 application:
1. An `arm64` bundle is built.
2. An `x86_64` bundle is built.
3. `packaging/macos/merge_universal.py` merges all Mach-O binaries and shared libraries using Apple's `lipo -create` and applies ad-hoc code signing.

---

## Local Build Instructions

### Prerequisites
* macOS 12+ (Monterey or newer)
* Python 3.12+
* Command-line tools: `hdiutil`, `codesign`, `lipo` (bundled with macOS / Xcode CLT)

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies + PyInstaller
pip install $(python scripts/print_dependencies.py) pyinstaller

# 3. Build translations
python scripts/build_qm.py
```

### Build Apple Silicon / M1 (`arm64`)
```bash
./packaging/macos/build_macos.sh arm64
```
Output:
* `dist/PicasaPy.app`
* `packaging/dist/PicasaPy-<version>-macOS-arm64.dmg`

### Build Universal 2
```bash
./packaging/macos/build_macos.sh universal
```
Output:
* `dist/PicasaPy.app` (Fat binary containing both `arm64` and `x86_64`)
* `packaging/dist/PicasaPy-<version>-macOS-universal.dmg`

---

## Smoke Testing the Packaged App

PicasaPy includes a built-in headless smoke test flag `--onellenorzes` that initializes the application, loads the complete QML user interface, and exits with code 0:

```bash
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software ./dist/PicasaPy.app/Contents/MacOS/PicasaPy --onellenorzes
```

---

## Code Signing & Gatekeeper Notarization

The build scripts apply an **ad-hoc signature** (`codesign --force --deep -s -`) which satisfies macOS Apple Silicon kernel execution requirements.

For official public distribution outside the Mac App Store:
```bash
# Sign with your Apple Developer ID
codesign --force --deep --options runtime \
  --sign "Developer ID Application: Your Name (TEAMID)" \
  dist/PicasaPy.app

# Create DMG and sign DMG
hdiutil create -volname "PicasaPy" -srcfolder dist/PicasaPy.app -ov -format UDZO PicasaPy.dmg
codesign --sign "Developer ID Application: Your Name (TEAMID)" PicasaPy.dmg

# Submit for Apple Notarization
xcrun notarytool submit PicasaPy.dmg --keychain-profile "AC_PASSWORD" --wait
xcrun stapler staple PicasaPy.dmg
```
