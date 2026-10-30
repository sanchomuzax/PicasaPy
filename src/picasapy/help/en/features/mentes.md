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

## Undo Save

After saving, choose **Undo Save** in the confirmation message to
restore the file to its state before that save. Your edits remain in
PicasaPy. This affects only the most recent save.

## Save As and Save a Copy

- **File** ▸ **Save As...** writes the edited photo with a different
  name or in another location. JPEG and WebP are available.
- **File** ▸ **Save a Copy** writes an edited copy beside the original
  with a name chosen automatically.

If the chosen name is already in use, PicasaPy reports that it cannot
save another file with that name.

## Restore

Choose **File** ▸ **Restore** to replace a file with its original
version from the save-time backup. This command is enabled only when
such a backup exists. It is available immediately after saving; you do
not need to change the selection.

PicasaPy asks for confirmation. For one photo it asks whether to
restore the original; for several photos it asks the same for all of
them. Choose **Restore** or **Cancel**. Cancel has focus when the
dialog opens, so an accidental `Enter` does not restore anything.

A floating progress indicator appears while files are restored. If the
disk is full or read-only, PicasaPy reports that it could not restore
all files. After a successful restore, the grid simply shows the
original photo.

## Undo all Edits

Choose **Picture** ▸ **Undo all Edits** to clear the edit list without
changing the file. The photo returns to its original appearance.

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
