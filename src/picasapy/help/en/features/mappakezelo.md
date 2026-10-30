# Folder manager and watched folders

PicasaPy shows only folders you add to it. These are the watched
folders.

## Folder manager

Open the folder manager from **Tools** or from the File menu's
add-folder command.

The left side shows the **Folder List**. The right side contains
settings for the current folder. Its introductory text explains that
you can choose whether PicasaPy searches each folder for photos and
watches it for new ones. If no folder is selected, the panel asks you
to select one from the left.

### Settings for each folder

- **Scan Always** watches the folder and automatically finds new
  photos.
- **Scan Once** scans the folder now without watching it afterward.
- Removing a folder from PicasaPy hides it from the view and leaves all
  files on disk. PicasaPy asks for confirmation if it is a watched
  folder, because new files saved there will no longer be added
  automatically.
- The face-detection setting controls whether PicasaPy searches that
  folder for faces. It applies to the folder and its subfolders.

Choose **OK** to save changes or **Cancel** to discard them.

If you try to watch an entire drive, PicasaPy warns that it may slow
the system and recommends choosing several subfolders instead.

### Turning off face detection

When you choose **OK**, PicasaPy asks whether it should remove all
faces and name tags from the folders where face detection was disabled.

- If you confirm, faces found automatically by PicasaPy are removed
  from those folders and their subfolders. Photos are marked so that
  the next face search skips them.
- Names and face boxes that you added in Picasa are kept; PicasaPy
  does not change those personal details.
- If you choose **No**, none of the changes are saved and the folder
  manager remains open.

The skip marker remains even if you later turn face detection back on.
There is no command to clear the marker for an entire folder. To reset
selected photos, use the face-reset command, which removes their faces
and markers and searches them again.

### If a folder cannot be added

The folder manager explains the problem. It reports if the folder is
already watched, cannot be opened because it does not exist or you do
not have permission, or another error occurred.

The **Help** button opens a short explanation that can be read without
leaving the dialog.

## Unavailable folders

If a watched folder is on a network share or external drive that is
currently disconnected, the pane reports that it is unavailable. The
folder stays in the database and its thumbnails remain available from
the cache.

You can browse these photos, but cannot open or edit them. Everything
works again automatically after the drive is reconnected.

## Folder commands in the pane

Right-click a folder for commands to select all its photos, invert or
clear the selection, refresh thumbnails, hide or show the folder, or
open it in the file manager.

**Sort Folder By** offers date, name, size, color, manual order, and
reverse order. It sorts the photos in the folder once; see
[The library](konyvtar.md).

**Edit Folder Description...** opens **Folder Properties**, where you
can change the folder name, date, slideshow and movie music, and
description. For the currently open folder, the same description
editor is available from **Folder** ▸ **Edit Description...**. See
[The library](konyvtar.md).

Other commands can move the folder to a collection, move or delete the
folder, remove it from the PicasaPy view without deleting its files, or
export it as an HTML page.
