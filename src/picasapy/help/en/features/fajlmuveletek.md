# File operations: rename, move, and delete

These commands affect the files on disk, not just the current view.
PicasaPy asks for confirmation before each operation.

## Open in another editor

Use the command in the **File** menu to open the selected photos in your
system's default application — the same one that opens when you
double-click a photo in the file manager. PicasaPy does not ask you to
choose an editor. It opens a separate window for each selected file. If
some files cannot be opened, a message reports how many failed. This
command is disabled until a photo is selected.

## Rename

Choose **File** ▸ **Rename...** (`F2`), or use the photo's context menu.
The **Rename Files** window opens for one photo or several. With one
photo, its current name, without the extension, is selected in the name
field so you can replace it. Type the new name. When renaming several
photos, PicasaPy adds a sequence number only when a name is already in
use (see below).

Under **Include in filename:** you can include the **Date** and **Image
resolution**. A sample below shows the format, using a fixed example
such as `Vacation 08-01-2004 2-30-45 PM 640x480.jpg`; it does not show
the selected photo's own data. The completed names use each photo's
actual date and resolution. Do not enter a file extension; each file
keeps its own.

The **Rename** button is disabled if the field is empty or unchanged.
Press `Enter` in the field to accept the new name, or choose **Cancel**
or press `Esc` to stop. After renaming one photo, it stays selected so
you can continue working with it.

- **Date** adds the photo's capture date and time, down to the second,
  formatted according to your system's locale. Characters that cannot
  be used in file names, such as a colon or slash, become hyphens. If a
  photo has no capture date, its name has no date component.
- The name field rejects file-name characters that are not allowed:
  `\ / : * ? " < > |`.
- PicasaPy remembers the state of the two checkboxes and restores it
  the next time the window opens.

### Numbering names that are already in use

PicasaPy processes photos one by one. If a proposed name is available,
it uses it without a number. If a file with that name already exists in
the folder, including one renamed earlier in the same operation, it
adds the next available three-digit number: `Vacation.jpg`,
`Vacation-001.jpg`, `Vacation-002.jpg`. If the entered name already
ends in a hyphen and number, such as `Vacation-5`, the next number
continues from it when that name is taken (`Vacation-006`). If you
include the **Date** and photos were taken at different times, their
names will already differ and no number is needed.

If renaming stops partway through, for example because a file is locked,
the files already renamed stay as they are. The error identifies the
completed files and the file where the operation stopped. Check that
file and its intended new name. The view refreshes to show what is on
disk.

## Move

You can move selected photos into a new folder or drag them onto a
folder in the left pane. To create a folder, open its **Folder
Properties** window. Its name initially reads **Untitled** and its date
is set to today. You can also enter a place, description, and music.
The folder and move are created after you choose **OK**; **Cancel**
leaves everything unchanged. An empty name, an invalid character, or an
existing folder name prevents the move.

A progress indicator shows which file is being moved.

### Drag and drop

Select photos in the grid, drag them, and drop them on a folder row in
the left pane. The destination row is highlighted during the drag. The
photos move without a confirmation prompt. If a file with the same name
already exists there, the incoming photo is given a new name; the
existing file is never overwritten. This works in both the flat folder
list and the tree view.

You can also drag a whole folder onto another folder in the left pane.
It becomes a subfolder there, with its contents.

If the destination already contains a file with the same name, choose
**Rename Duplicates** to give the incoming files new names, or **Skip
Duplicates** to leave them out. PicasaPy never overwrites or deletes an
existing destination file, including when it rolls back an interrupted
move. Rollback only removes files created by that operation.

The backup copy made when a photo was edited moves with it, so
restoring the original still works in the new location; see
[Save and restore](mentes.md).

### If a move is interrupted

A move may stop because a file is locked, the destination is not
writable, or another drive disappears. In that case the photo stays in
its original location and PicasaPy removes its incomplete copy from the
destination. A failed move therefore does not leave two copies of the
same photo. The same protection applies when moving a file to Trash,
restoring it, or moving a preserved original.

## Copy, cut, and paste

**Edit** ▸ **Copy** (`Ctrl+C`) and **Cut** (`Ctrl+X`) put the files on
the system clipboard so you can paste them elsewhere in the file
manager.

**Edit** ▸ **Paste** (`Ctrl+V`) copies files from the clipboard into the
currently selected folder. The files may come from the file manager or
from either PicasaPy command above. A cut file is moved; a copied file
is copied.

If a file with the same name already exists in the destination folder,
the pasted photo gets a new name. Nothing is overwritten. Paste is
disabled when the clipboard is empty. If it becomes empty before the
operation, PicasaPy explains why nothing happened. In a text field, for
example while renaming, `Ctrl+V` pastes text into the field instead of
files.

## Delete

Choose **File** ▸ **Delete from Disk** (`Delete`) or use the photo's
context menu. In the viewer, press `Ctrl+Delete`. When the photo was
opened from an album, that shortcut removes it from the album only.

The command's label depends on the current view. In an album it removes
the photo from that album; in a People album it removes it from that
album. These actions leave the file untouched. In a folder, the command
deletes the file from disk.

PicasaPy asks for confirmation. The dialog is titled **Delete Items**.
If the system Trash is available, it offers to move the file there, with
a **Delete Image** button for one photo or **Delete Items** for several.
If Trash is unavailable, such as on some network or removable drives,
the file is permanently deleted after a separate warning. The button is
then **Delete File** or **Delete Files**.

The **Cancel** button has focus when the dialog opens, so pressing
`Enter` by accident does not delete anything. The option **Don't ask
again, always remove** turns off future confirmations. The same
preference can be changed under **Tools** ▸ **Options** ▸ **General**.

## Locate a file on disk

Choose **File** ▸ **Locate on Disk** (`Ctrl+Enter`) to open the photo's
folder in the file manager. If no photo is selected, `Ctrl+Enter` opens
the current folder instead; it has no effect in an album or People
view.

The photo's context menu has the same **Locate on Disk** command. If
one photo is selected and PicasaPy has kept its pre-edit original, the
menu offers both **File on Disk** and **Locate Original on Disk**. The
first opens the folder containing the current file; the second opens
the location of the preserved original. With multiple photos, or when
there is no preserved original, the submenu is not shown. This matches
the original Picasa behavior.

In album and People views there is also a command to return to the
photo's own folder. It is not shown in a folder view, where the photo
is already in its folder.

Other context-menu commands include:

- **Open File** opens the photo in the system's default application.
- **Open With** lets you choose an application. On Windows it opens the
  system's “Open with” dialog. On Linux, a submenu lists applications
  associated with the file type; choose **Open With...** to select one
  in a dialog, then choose **Open**. If none is associated, the dialog
  says so. The viewer's **Open With** command is not implemented yet.
- **Copy Full Path** copies the file path to the clipboard.

## Folders

The folder context menu lets you move an entire folder. If the move
stops, the folder remains in its original location and no incomplete
copy remains at the destination. For one step that cannot be rolled
back, the error explains where the contents are.

The delete-folder command removes the folder from disk and asks for
confirmation because it also deletes subfolders. The remove-from-library
command hides the folder from PicasaPy while leaving its files in place.
