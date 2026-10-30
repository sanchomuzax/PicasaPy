# Find duplicate photos

There are two ways to work with duplicates, each for a different
purpose:

- The duplicate view quickly shows which photos have copies in your
  library. It is for browsing.
- PicasaPy also has a separate duplicate-management dialog that guides
  you through cleanup and sends unwanted photos to the system Trash.

Both are in **Tools** ▸ **Experimental**. The original Picasa also put
its duplicate command in the Experimental submenu.

## The duplicate view

Choose **Tools** ▸ **Experimental** ▸ **Show Duplicate Files**. This does
not open a window: the grid switches to a filtered view that shows only
photos with copies in the library.

The search scans the whole library and may take a few seconds. A yellow
progress bar appears while it runs. When the scan is complete, the green
results bar shows **Duplicate Files** to indicate that this view is
active.

The small filter panel beside the search field also has a control for
showing only duplicate files; see [Search and filtering](kereses.md).

Leave the view in either of these ways:

- Use **Back to View All** on the green bar, or
- Click the duplicate badge among the search-bar filters. The badge,
  shown as two overlapping pages, appears only in this view; it cannot
  turn the view on. To enable the view, use the menu command or press
  `Ctrl+F6`. This matches the original Picasa behavior.

### What counts as a duplicate

Picasa uses a fingerprint calculated from the beginning and end of each
file. Two photos count as duplicates when those fingerprints match; the
file names and full contents are not compared. This lets the scan stay
fast in a large library because it does not read every file from start
to finish.

Only identical files appear in this view. To find photos that look
similar but are not identical, use [Search for similar photos](kereses.md).

## Duplicate cleanup

The separate duplicate-management dialog is a PicasaPy addition; the
original Picasa did not have this tool. Its menu item is shown in blue.

### Choose where to search

Choose either **Whole library** or **This folder and its subfolders**
as the search location. Start the scan with its button. The program
first analyzes the photos, then compares the files. Progress remains
visible, and you can interrupt the scan with **Cancel**. Cancelling
also works if the scan finishes at that moment; groups already found
are kept.

If there are no results, the dialog reports that it found no duplicates.

### Review the results

Results are grouped into exact file copies and photos that look very
similar but are not identical. For similar photos, a distance value
shows how much they differ: a smaller value means a closer match.

Expand a group to see its photos, then choose which one to keep.

### Remove the extras

The action for removing the other photos in a group keeps the selected
photo and moves the rest to the system Trash. It does not permanently
delete them; you can restore them from the Trash later.

The dialog shows how many photos are selected so you can review the
scope before acting.

## During import

The import window's **Exclude Duplicates** option skips photos that are
already in your library. The same setting is available under **Tools**
▸ **Options** ▸ **General**, as **Detect duplicates while importing**.
Both controls represent the same setting. It is on by default.
