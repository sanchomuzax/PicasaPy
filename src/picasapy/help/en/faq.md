# Frequently asked questions and error messages

## General questions

### Does PicasaPy modify my photos?

No. It saves edits to the `.picasa.ini` file alongside your photos and
reapplies them whenever an image is displayed. It writes to the image file
only when you explicitly choose **File** ▸ **Save**; it makes a backup first.

One exception is captions: PicasaPy also writes them to a JPEG's IPTC fields
so other applications can read them.

### Can I still use the old Picasa with the same photos?

Yes. Both applications read and write the same `.picasa.ini` file, and
PicasaPy preserves data it does not understand. It is best not to edit the
same folder in both applications at the same time.

If you create a collage or movie in the old Picasa, it appears in PicasaPy
after a few seconds, even if it was made on another computer and the photos
are on a network drive. On network drives, the application may not be
notified when another computer changes other folders. In that case, use
**Refresh Thumbnails** from the folder's context menu to scan it again.

### Why are so many menu items disabled?

The menus show the full structure of the original Picasa, but some features
are not implemented yet. See the full list in
[Features not yet available](features/meg-nem-erheto-el.md).

### Where are my photos if I delete the database?

They stay where they are. The database is only used to speed things up;
important data is stored alongside the photos. You can delete the database
and restart the application. It will scan the watched folders again.

### How do I switch from Hungarian to English?

Choose English (US) in the language selector under **Options** or from the Tools
menu. PicasaPy asks you to confirm; the change takes effect the next time
you start the application. See
[Settings, language, and appearance](features/beallitasok.md).

### The interface is in English when I run from source, even though I chose Hungarian

When run from source, the application builds the translations on first
launch. It looks for `pyside6-lrelease`; if the tool is unavailable, the
interface remains in English. Install PySide6 with `pip` (which includes the
tool), then restart the application. This does not affect the installed
version. See [Getting started](getting-started.md).

## Error messages

### The application will not start: the Qt 6 Wayland plugin is missing

On a Wayland desktop, the application needs an extra system package to open
a window. It now tells you what is missing and how to fix it instead of
stopping with a Qt error in English. Run this command in a terminal:

```bash
sudo apt install qt6-wayland
```

The `qtwayland5` package is for Qt 5 and cannot be used by PicasaPy.

### “A background task is still running ... If you exit now, it will stop and will not resume later.”

This appears when background work is still running as you exit, for example
an export, web export, batch effect, or face search. Choose the option to
exit to cancel the work; it will not resume the next time you start the
application. Choose the option to continue if you want to return and wait
for the work to finish.

The same confirmation appears if you close the window with its X button.
It cannot be disabled because work could otherwise be lost.

### “This folder is currently unavailable...”

An external drive or network share is disconnected. The photo list and
thumbnails remain available, but you cannot open or edit the files right
now. Reconnect the drive and continue; you do not need to scan it again.

### “%1 photo(s) could not be found and will not be displayed.”

Another application may have moved, renamed, or deleted the files. If they
were moved, add their new location in [Folder Manager](features/mappakezelo.md)
and PicasaPy will find them.

### “One or more photos could not be rotated because of the file type.”

Videos cannot be rotated, and non-destructive rotation is unavailable for
some image formats.

### “This video cannot be played.”

The Qt Multimedia module may be missing, or the system may not recognize the
video format. On Linux, install `qml6-module-qtmultimedia` and
`python3-pyside6.qtmultimedia`; install `libpulse0` for audio as well.

### “The map component (QtLocation) is unavailable.”

The Qt module used to display maps is missing. You can still read and delete
geotags, but the map will not appear.

### “PicasaPy could not initialize Google Maps. Check your internet connection.”

The map in the Places panel is downloaded from the internet, and the
application could not reach it. Check your connection. Your geotags are
unaffected. See [Places](features/helyek.md).

### “Install a printer to print.”

No printer is configured on the computer. You can still print to PDF. To
print on paper, set up a printer in your system settings. See
[Printing](features/nyomtatas.md).

### “Could not export the clip”

PicasaPy could not save the selected part of the video to a file. The
original video is unchanged. Clip export is not supported on Linux. See
[Viewing photos](features/nezegetes.md).

### “These photos have edits that PicasaPy cannot display yet”

The `.picasa.ini` file contains an effect from an older version of Picasa.
PicasaPy preserves the setting but cannot render it. If you save the photo,
the setting will be lost permanently. It may be best to leave the photo
unedited instead. See [Older effects](features/effektek.md).

### “The file could not be saved because of a file-format error.”

PicasaPy cannot write this image format. Try **File** ▸ **Save As...** and save
it as JPEG or WebP.

This is expected for a RAW file: PicasaPy cannot write RAW files, just as the
original Picasa could not. Your edits are still saved in the folder's
`.picasa.ini` file, and you can export the photo as a JPEG at any time.

### “The file cannot be saved. A file with that name already exists.”

A file with the selected name already exists. Choose another name.

### “The photo cannot be replaced. Try another file name.”

The destination file is in use, or you do not have permission to write to
it.

### After saving, restoring, or undoing a save

After **Save**, **Revert**, or **Undo Save**, the open photo immediately
shows the state stored on disk. If the operation fails, PicasaPy opens an
error dialog and identifies the affected file. It does not fail silently.

### Disk error while saving

If the disk is full or read-only, PicasaPy identifies the affected file.
Free some space or check the folder's permissions.

### “There are no files on the clipboard to paste.”

You chose **Edit** ▸ **Paste**, but there are no files on the clipboard. Copy
or cut photos first, either in PicasaPy or in your file manager.

### “None of your photos have this tag.”

You entered a tag in the dialog for displaying a tag as an album, but none
of your photos has that tag. Tags must match exactly: searching for “summer”
will not find “vacation.”

### The wallpaper image was created, but the desktop background was not set

The image was created, but PicasaPy could not access the desktop settings.
This can happen on some Linux desktops. On Windows, the operating system
sets the background. The message tells you where the image was saved; choose
it manually in your system settings. See
[Desktop wallpaper](features/hatterkep.md).

### No printable photo / Some photos could not be printed

The first message means that no photo is selected. The second means that the
listed files could not be read; check that they still exist.

### No face found / More than one face appears in the photo

These messages appear in **Passport photo**, together with the question
**Try another picture?**. A passport photo must contain exactly one face.
Choose a photo with a single, clearly visible face. See
[Passport photo](features/utlevelkep.md).

### The photo could not be read / The cropped photo could not be saved

These messages are also from **Passport photo**. The first means that the
image file could not be opened; check that it still exists and can be read.
The second means that the crop could not be written to a temporary file,
usually because the disk is full.

### Select photos in the library or add them to the Photo Tray first

You need at least one photo to create a collage or movie.

### The collage or movie could not be created

The most common causes are that you do not have write permission for the
destination folder or that one of the source files has disappeared. Choose
another destination and try again.

### No geotagged photos are available to export

None of the selected photos has a location. Use the globe filter to see
whether any of your photos have geotags.

### Automatic red-eye correction did not find red eyes

PicasaPy did not find red eyes in the photo. Select the eyes manually by
dragging a rectangle around them in the red-eye panel.

### Face search or grouping failed

The face-search dialog reports why a search or grouping operation stopped.
The face-recognition model is installed with the application, so it is
rarely missing. If it is missing, the dialog offers a way to download it.
If the model file exists but PicasaPy cannot load it, the dialog reports
that too. Details are available in the application log. If automatic face
search cannot start in the background, the reason is written to the log as
well.

### “Syncing *N* folder(s) will continue later.”

This is not an error. If PicasaPy is doing a lot of work with the database,
for example searching for faces during an import, it briefly queues a
folder refresh and retries automatically. You do not need to do anything.
The old `database is locked` error no longer appears.

### A search failed while importing settings from Picasa

This appears if there is a problem while PicasaPy searches for an older
Picasa installation. The message includes the type and details of the
error. You can still choose a folder manually to show PicasaPy where to
look.

### The folder is read-only or the disk is full

If PicasaPy cannot write to the `.picasa.ini` file beside your photos, it
reports the error and its cause. This can happen when changing a folder
description or date, editing keywords, or pasting all effects.

If you see this message, the change was not written to disk. Make the folder
writable or free some disk space, then try again.

### “No EXIF data is available.”

The image file does not contain camera information. This is not an error;
it is common with edited or downloaded photos.

## If something still goes wrong

If the application does not start, check its `errorlog.txt` file. PicasaPy
records each startup step there, so you can see how far it got. On Linux the
file is in `~/.local/share/picasapy/`; on Windows it is in
`%LOCALAPPDATA%\PicasaPy\`. If you moved the database, the log is in that
location. It also records the PySide6 and Qt versions. PicasaPy does not
yet support PySide6 6.12 or newer and displays a warning if it detects one.

PicasaPy also includes diagnostic and test-mode controls that can save or
collect details about what the application is doing. If startup is slow,
enable the option that logs the next launch, restart the application, and
then use the log-sharing command to send the log.
