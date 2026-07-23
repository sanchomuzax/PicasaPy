@echo off
rem ============================================================
rem  PicasaPy indito (#190/sagabol szuletett kenyelem):
rem  dupla kattintasra FRISSIT (git pull) es INDITJA az appot.
rem  Asztali parancsikonhoz: jobb klikk erre a fajlra ->
rem  Kuldes -> Asztal (parancsikon letrehozasa).
rem ============================================================
cd /d "%~dp0"

rem -- melyik python van a gepen? (Store-os python3 vagy sima python)
set PY=python3
where python3 >nul 2>nul || set PY=python
where %PY% >nul 2>nul || (
    echo HIBA: nem talalok Pythont. Telepitsd a Microsoft Store-bol
    echo a "Python 3.12"-t, majd inditsd ujra ezt a fajlt.
    pause
    exit /b 1
)

echo === PicasaPy frissitese (git pull) ===
git pull
if errorlevel 1 (
    echo FIGYELEM: a frissites nem sikerult - a mostani verzioval indulok.
)

echo === Fuggosegek ellenorzese (elso alkalommal lassabb) ===
%PY% -m pip install --user --quiet PySide6 opencv-python pillow piexif watchdog

echo === PicasaPy inditasa ===
set PYTHONPATH=src
%PY% -m picasapy.app
if errorlevel 1 (
    echo.
    echo A PicasaPy hibaval allt le - a fenti uzenetet masold be Claude-nak.
    pause
)
