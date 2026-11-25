# Save, restore, and undo

By default, PicasaPy leaves your files untouched and stores edits in
the `.picasa.ini` file beside the photos. To write your changes into a
file - for example, to open or send the edited version elsewhere - use
the commands described here.

## Save

Choose **File** ▸ **Save** (`Ctrl+S`) to write selected photos to disk
with their edits.

The command is available only when a selected photo has unsaved edits,
as in the original Picasa. Otherwise the menu item, the **Save** button
above the photos, and `Ctrl+S` are disabled.

Before saving, PicasaPy asks **Save changes to disk?** and notes that
it will make a backup copy of each file. Choose **Save** to continue or
**Cancel** to leave the files unchanged. If you check **Do not ask me
again.** and then choose Save, PicasaPy will no longer ask. Choosing
Cancel does not apply that preference.

The backup stays in a separate subfolder beside the original and
preserves its modification date. It moves with the photo if you rename,
move, or copy it, so **Restore** still works at the new location. If
something would be overwritten at the destination, the operation does
not start; PicasaPy never overwrites another photo's preserved
original.

If a photo has an edit PicasaPy cannot render, such as an effect from an
older Picasa version, it warns you before saving. The edit will be
omitted from the file and its settings will be lost; this cannot be
undone.

After saving, restoring, or undoing a save, the grid and open viewer
refresh automatically. The editor reloads the file and edit list from
disk, so it shows the current file contents. If an operation fails, an
error dialog explains why.

If saving fails because of a disk problem (for example the file or
folder is read-only, or the disk is full), the error dialog's title is
**Error**, as in the original Picasa. Below the message you see the
file name and an `error(...)` number. This number is the original
Picasa's own error code, not the system's: 11 when you are not allowed
to write the file, 10 when the file or folder cannot be found, and
usually 2 in every other case, including a full disk. The name
collision and unsupported format dialogs also use the **Error** title.

If the finished picture cannot be put in place of the original (for
example because the file is read-only), your photo stays unchanged.
For a JPEG photo the finished, edited version is not lost: you find it
next to the photo with a name ending in `.jpg.jpg` (for example
`holiday.jpg.jpg`), as in the original Picasa. If a file with that name
already exists, it is not overwritten. No backup copy is made in this
case, because the original file did not change.

## Undo Save

After saving, choose **Undo Save** in the confirmation message to
restore the file to its state before that save. Your edits remain in
PicasaPy. This affects only the most recent save.

If the picture is open in the editor, after saving the editor's **Undo**
button reads **Undo Save**. Clicking it does the same: the file gets back
its state before the save, and your edits remain. Afterwards **Undo**
undoes the edits that remain (for example a straightening); if the only
change left is not an edit step (for example text on the picture), the
button is disabled. **Redo** is disabled.

## Save As and Save a Copy

- **File** ▸ **Save As...** writes the edited photo with a different
  name or in another location. JPEG and WebP are available.
- **File** ▸ **Save a Copy** writes an edited copy beside the original
  with a name chosen automatically. When several photos are selected,
  only the highlighted (focused) photo is copied.

If the chosen name is already in use, PicasaPy reports that it cannot
save another file with that name.
If the copy cannot be written because of a disk error, it says: "Unable
to save files due to a disk error. The disk may be full or read-only."

Both commands are disabled for a video and when no photo is selected.

## Restore

Choose **File** ▸ **Restore** to replace a file with its original
version from the save-time backup. This command is enabled only when
such a backup exists. It is available immediately after saving; you do
not need to change the selection.

PicasaPy asks for confirmation. For one photo it asks whether to
restore the original, with an extra **Undo Save** button that only
undoes the last save and keeps your edits (see above). For several photos
it asks "Revert to original version of these files?" and there is no
**Undo Save** button. Cancel has focus when the dialog opens, so an
accidental `Enter` does not restore anything.

If another program has changed a file since it was saved, PicasaPy warns
once more, because reverting also discards that change: "This file has
been changed outside of PicasaPy. Reverting will lose those changes."
(for several files "These files have changed..."), followed by "Do you
want to revert?". The buttons are **Revert Anyway** and **Cancel**;
**Cancel** has focus.

Reverting also clears the photo's rotation, mirroring, and text, so it
really appears in its original state.

A floating progress indicator appears while files are restored. If the
disk is full or read-only, PicasaPy reports that it could not restore
all files. After a successful restore, the grid simply shows the
original photo.

## Undo all Edits

Choose **Picture** ▸ **Undo all Edits** to clear the edit list without
changing the file. The photo returns to its original appearance. Besides
the edits, it also clears mirroring, text written on the photo, and the
edit history; the rotation stays.

The command is available only if the first edited photo in the selection
is not merely rotated. It is disabled when nothing is selected, when no
selected photo is edited, or when the first edited photo is only rotated.

PicasaPy asks for confirmation in a **Confirm** dialog. Choose
**Remove Edits** to continue or **No** to cancel. In the viewer, the
prompt refers to the current photo. If a photo has a red-eye correction,
PicasaPy warns that **Redo** cannot bring it back. The warning names the
affected photo or photos.

| Command | Affects | Are the edits lost? |
|---|---|---|
| Save | The file on disk | No, they are written into it |
| Undo Save | The last write to disk | No |
| Restore | The file on disk | Yes |
| Undo all Edits | Only the edit list | Yes; the file is unchanged |

## If saving fails

- A file-format error means PicasaPy cannot write that format.
- A replacement error means the destination file is busy or cannot be
  written; try another name.
- If the disk is full or read-only, PicasaPy reports the problem and
  identifies the affected file.
