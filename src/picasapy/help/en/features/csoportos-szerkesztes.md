# Batch editing and the effects clipboard

## Batch Edit

Select several photos, then choose **Picture** ▸ **Batch Edit**. The
operation you choose from the submenu is applied to every selected
photo:

- **Rename...** (F2) - rename the selected photos; see [File
  operations](fajlmuveletek.md).
- **Rotate Clockwise** and **Rotate Counterclockwise**.
- **Auto Contrast**.
- **Auto Color**.
- **I'm Feeling Lucky**.
- **Sepia**.
- **Sharpen**.
- **Warmify**.
- **Film Grain**.
- **B&W**.
- **Auto Red Eye Correction**.

The submenu groups its items with separators: rename first, then rotate,
automatic corrections, effects, and finally red-eye correction.

A progress bar appears while the operation runs, and you can cancel it.

Selected videos are skipped: they get no effect and are not rotated. If
the selection included a video, an information window points this out
when the work is done. If nothing is selected, PicasaPy tells you the
same way and does nothing.

In the viewer, the menu applies to the open photo only. It does not
affect the selection left in the grid. If the photo is open in the
editor, **Auto Contrast**, **Auto Color**, **I'm Feeling Lucky**,
**Sepia**, **B&W**, **Warmify**, and **Film Grain** do the same as the
editor's matching tile: the editor switches to that tile's tab and the
effect is applied to the open photo at once. A single **Undo** removes
it. **Sharpen** opens the same settings panel as its tile; the photo
changes only after you click **Apply** there. Where the tile cannot be
used at the moment (for example while Crop or Straighten is open), the
menu command does nothing either. While an effect's settings panel is
open in the editor, the **Picture** menu items and the **Batch Edit**
submenu are disabled; they become available again when you close the
panel.

### Show or hide text

The submenu has separate **Show Text** and **Hide Text** commands for
the text overlay on selected photos. They hide or show the overlay
without deleting it. Photos without text are left alone. With photos
selected, both commands are always available, even if none of the
photos has text on it. The editor has a **Show Text** checkbox
for an individual photo; see [The editor](szerkeszto.md).

To reverse a batch operation, use the batch undo command. It reverses
the whole batch in one step.

## Effects clipboard

After editing a photo, you can copy its edits to other photos:

1. Select the edited photo and choose **Edit** ▸ **Copy All Effects**.
   Select only one photo: if several are selected, an **Info** window
   asks you to choose one (**Please select a single picture to copy the
   effects from.**) and nothing is copied.
2. Select the photos to receive the edits, then choose **Edit** ▸
   **Paste All Effects**.

The paste command is available only when there are effects to paste.

Use the undo command to reverse the last paste operation.

## Rotation

Rotation is non-destructive: it records the change without rewriting
the file. You can rotate a photo in these ways:

- Use either of the rotation buttons in the photo tray.
- Choose **Rotate Clockwise** or **Rotate Counterclockwise** from the
  photo's context menu.
- Press `Ctrl+R` or `Ctrl+Shift+R`.
- During a slideshow, use the two rotate buttons on the control bar (the
  shortcuts do not rotate during a slideshow).

Videos cannot be rotated.

## Undo all edits

**Picture** ▸ **Undo all Edits**, or the same command in a photo's
context menu, removes every edit from the selected photos and restores
their original appearance. The program asks for confirmation.
