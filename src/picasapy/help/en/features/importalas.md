# Importing

## Import from a source

This is the main way to bring photos into the library, from a memory
card, camera, or any folder.

Start the import from the toolbar button or the File menu. Choose a
source at the top of the dialog; recent sources are offered as well.
The dialog shows how many photos and videos it found.

The **Browse...** button opens a small menu:

- **Folder...** lets you choose an entire folder as the source.
- **Files...** lets you select individual files from a folder. The
  **Import Files/Folder** dialog allows multiple selections. Its filter
  can show **Picture and Movie Files**, **Picture Files**, or **All
  Files**. The source field shows the first file and how many more you
  selected. Only existing photo and movie files allowed by the **File
  Types** setting are imported.

When a memory card or USB drive is connected, a list of **Removable
drives** also appears beside the source field on Windows and Linux.
Choose one to make it the source; PicasaPy scans it immediately. The
list is hidden when no removable drive is connected.

### Choose what to import

- Click a thumbnail to include or exclude that item. The include-all
  and exclude-all controls change every item at once.
- The duplicate-exclusion option skips files already in your library.
- Use **File Types** to choose photos, movies, both, or all files.

### Choose where files go

Choose a destination folder with **Browse...**, or select one used
previously. The dialog opens with the default destination, which is
your Pictures folder unless changed in **Options** ▸ **General**. The
default can be changed in [Settings](beallitasok.md).

Choose the name of the subfolder that will hold the imported files:
enter a name, organize them by the date taken (YYYY-MM-DD), or use a
folder named with today's date. The date option shows the current date
in the label; the created folder uses that date, for example
`2026-01-31 (today)`.

For a custom folder name, enter one name before starting the import. It
must be a single folder name: paths outside the destination, full paths,
and characters that are invalid in folder names are rejected. While
the name field is empty, the import cannot start and the dialog asks
you to enter a name or select an existing folder.

### After copying

Choose what happens to the source after copying:

- Leave the card unchanged (the default).
- Delete only the photos that were copied.
- Delete everything from the card.

PicasaPy asks for confirmation before either deletion option. The
deletion cannot be undone, and removed files do not go to Trash.

For deleting everything, the warning lists how many files will be
deleted after import, how many will be skipped because they are already
in your library, and how many PicasaPy does not recognize. Unrecognized
files are also deleted; these may include camera sidecar files and
other files on the card, not only photos.

If PicasaPy has not scanned the source yet, it reports that the number
of files is unknown instead of guessing. Wait for the scan to finish
before confirming.

### During import

A progress bar shows the current item and the transfer speed. At the
end, PicasaPy reports how many photos were imported and how many failed.

## Capture from a webcam

A small camera control beside the view buttons in the toolbar opens the
capture window. Use it to take a still photo or record a video with your
computer's camera.

The live camera image appears in the center. While the camera is
connecting, the window reports that state; if no camera is available,
it says so. Use the snapshot control to save a still image. Start
recording with **Record**; while recording, the button becomes
**Stop**. **Pause** and **Resume** pause and continue the recording.

The settings let you choose the **Camera**, **Audio** source, and
**Size**: 320 × 240, 640 × 480, 800 × 600, or 1280 × 720. **Apply**
accepts the settings; **Cancel** discards them. The selection is
remembered and used for still photos and videos. The camera control in
the top row returns to the live image.

Use the previous and next controls to move between recorded clips; the
play control starts playback. Choose **Done** to close the window,
stopping an active recording first.

Still images and clips are saved in `Pictures/Picasa/Captured Videos`.
The window reports if it cannot prepare the folder or if capture fails.

## Add a file or folder

The File menu can add one or more specific files to the library. Its
folder command opens the [Folder Manager](mappakezelo.md), where you
can add a watched folder.

## Drag and drop

You can drag photos or folders directly onto the application window.
PicasaPy adds them and shows progress.

## Transfer watched folders from Picasa

If Picasa was used on this computer, PicasaPy can find its watched
folders and offer to add them, so you do not have to configure them
again. Choose the transfer action to add the list or skip it for now.
If detection finds nothing, or the folders are elsewhere, use the
manual folder picker.

This dialog appears automatically at first startup. You can open it
again later from the Folder Manager.

## Import data from an older Picasa installation

If you used Picasa on this computer, PicasaPy can import names,
keywords, and locations stored there for your photos. Use the import
action under **Tools**.

The dialog starts the transfer and reports its progress. When it
finishes, it summarizes the folders updated, the keywords, locations,
and names imported, and the photos it left alone because data was
already present.

The transfer never overwrites existing data. It leaves existing
keywords and locations unchanged. For faces, it keeps each existing
face and adds faces missing from the photo. You can repeat the transfer
at any time: it continues with folders not yet handled and does not
create duplicates.

If Picasa stored more than one record for a photo, PicasaPy uses the
record modified most recently. Large Picasa databases are also
processed quickly, and album membership is imported.

In addition to names, keywords, and locations, the transfer brings in:

- Faces Picasa found but did not assign to anyone. These go into the
  Unnamed album so you can name them. Names for assigned faces come
  from Picasa's contact list, including names changed after the faces
  were first tagged.
- The manual photo order in folders and albums.
- Changed dates for videos and video locations.

If you used a password for hidden folders in Picasa, it is imported
only when you have not already set a password in PicasaPy. Your
existing password is never overwritten. See “The hidden-folder
password” in [The library](konyvtar.md).

If no old Picasa data is found on the computer, the dialog reports it.

### Choose a Picasa data folder manually

By default, leave the Picasa2 data-folder field empty and PicasaPy
searches for the data itself. If the data is elsewhere — for example,
in a copied `Picasa2` folder or on a Windows drive accessed from Linux
— enter or browse to that folder.

Because Picasa stored Windows paths, also map the old paths to the
photos' current location:

- Enter the Windows path prefix Picasa used, such as `C:/Pictures`.
- Enter the matching local folder, such as `/home/user/Pictures`.

Both mapping fields are required when you choose a data folder
manually. The dialog reports an error if either one is empty.
