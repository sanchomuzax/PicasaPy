# Getting started

## Requirements

PicasaPy runs on both Linux and Windows. The Windows installer includes
everything. On Linux, you need Python 3.12 or newer and the Qt 6 graphics
libraries.

### Linux (Debian, Raspberry Pi OS)

Installing the system packages is the simplest option:

```bash
sudo apt install \
  python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtqml \
  python3-pyside6.qtquick python3-pyside6.qtquickcontrols2 python3-pyside6.qtwidgets \
  python3-pyside6.qtmultimedia python3-pyside6.qtprintsupport \
  python3-opencv python3-pil python3-piexif python3-watchdog \
  qml6-module-qtquick qml6-module-qtquick-controls \
  qml6-module-qtquick-layouts qml6-module-qtquick-templates qml6-module-qtquick-window \
  qml6-module-qtmultimedia \
  libegl1 libgl1 libxkbcommon0 libpulse0
```

The `python3-pyside6.qtprintsupport` package is needed for printing only
when you install Qt from the system packages; the `pip` version includes it.
The four `lib...` packages support graphics and audio and are usually already
installed on desktop systems.

Two more packages are recommended: `xdg-utils`, which lets the application
pass photos as attachments to your email program, and `cups-client` for
printing. The PicasaPy Debian package offers both as recommended packages.

When launched from source, the application builds its interface translations
on first run; it needs the `pyside6-lrelease` tool for this. The tool is
included with PySide6 installed through `pip`. If it is unavailable and the
translations have not been built yet, the interface appears in English. The
installer already includes the built translations.

### Windows

The recommended option is the installer. Each release includes a
`PicasaPy-Setup-<version>.exe` file: download it, run it, and you are ready.
You do not need to install Python; the application includes everything it
needs. The installer adds a Start menu entry and, if you choose, a desktop
shortcut. You can uninstall it from Apps and Features like any other program.
Find the installer on the project's Releases page.

If you prefer to run from source, you need Python 3.12 or newer and these
packages:

```powershell
pip install PySide6 opencv-python pillow piexif watchdog
```

The Windows build is experimental; development takes place on Linux.

## Launching the application

You can specify which folders to scan when starting the program:

```bash
./picasapy ~/Pictures
```

On Windows:

```powershell
python picasapy C:\Pictures
```

The application also starts without a folder argument. You can add watched
folders later in [Folder Manager](features/mappakezelo.md).

You can provide one or more image files instead of a folder:

```bash
./picasapy ~/Pictures/vacation.jpg
```

In this case, the application opens the photo directly in a simplified
viewer instead of loading the library. See [Viewing photos](features/nezegetes.md).
On Linux, the first launch registers PicasaPy for image file types, so it
also appears in the file manager's **Open With** list.

There is no other command-line interface; all operations are available in
the window.

## First launch

On first launch, PicasaPy asks where it should look for photos. You can
choose one of two options:

- Scan only Documents, Pictures, and Desktop - quick, and enough for most
  people.
- Scan the entire computer - useful if your photos are spread across several
  drives and folders.

If your computer is set to a language other than English and PicasaPy
supports it, the application asks once whether to switch to the system
language (Yes / No). You can change the language later in the language
selector under **Options** or from the Tools menu. See
[Settings, language, and appearance](features/beallitasok.md).

Scanning never moves or copies files. It only checks where they are.

If you used Picasa on this computer before, PicasaPy offers to import its
watched-folder settings. Choose the option to import those settings, or skip
the import.

You can use the application while the initial scan is running; photos appear
as they are found.

## The main window

From top to bottom:

### Menu bar

**File**, **Edit**, **View**, **Folder**, **Picture**, **Create**, **Tools**,
and **Help**. A disabled item is either not
implemented yet or unavailable in the current context - for example,
because no photo is selected or because you are in the viewer. In the latter
case, select a photo to enable the item. The
[Features not yet available](features/meg-nem-erheto-el.md) chapter lists
items that are not implemented. Press `F1` at any time to open this guide;
see [Built-in help](features/sugo.md).

Some menu items are shown in blue. These are PicasaPy additions that were
not part of the original Picasa, such as the dark theme option, face search,
and the performance monitor.

### Toolbar

On the left, the **Import** button, a control for creating an
album, two view buttons and a dropdown for folder-view options; in the
middle, filters for starred photos, photos with faces, videos, and geotags;
on the right, the **Search** field. In a narrow window the small buttons and
filters are hidden, while **Import** and **Search** remain. Everything is
still available from the menu bar.

### Left pane

Folders, albums, collections, and projects appear here. Choose what to show
in the thumbnail grid.

### Background activity indicator

A small indicator in the upper-right
corner appears only while the application is working in the background,
for example, scanning, searching for faces, or building the color index. A
spinner shows that work is in progress. If the operation can be stopped, a
stop button appears beside it; the application asks for confirmation before
stopping.

### Thumbnail grid

Thumbnails from the selected folder or album appear here. Click a photo to
select it, or double-click to open it in the viewer.

### Bottom area (Photo Tray)

A blue selection summary, the tray containing
the selected photos, and operation buttons: star, rotate, zoom, thumbnail
size, **Collage**, **Movie**, **Export**, **Print**, **E-Mail**, and the green
**Upload to Google Photos** button. See
[Upload to Google Photos](features/google-fotok.md). The viewer has three
zoom controls in this area as well.

### Right-hand drawer

The **Tags**, **People**, **Places**, and
**Properties** panels. Open it from the View menu, the tray buttons, or
`Ctrl+0`. It slides open and closed. You can also click the narrow
invisible strip along its left edge (at the right edge of the window when
the drawer is closed). There is one shared drawer and header; the header
shows the name of the panel currently displayed. On the left is the
**Switch between small/large side panel** button. On the right is the
**Close this side panel** button.

## Where your data is stored

PicasaPy does not modify your photos. It saves edits, stars, and captions in
the `.picasa.ini` file alongside the photos, in the same file used by the
original Picasa. Both applications can therefore use the same photo library.

PicasaPy also maintains a separate search database and thumbnail cache to
speed things up. Both can be rebuilt at any time. See
[The database](features/adatbazis.md).
