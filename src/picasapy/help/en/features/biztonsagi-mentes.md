# Backing up photos

PicasaPy can copy your photos to another drive or a network share. It does
not move or change the originals.

Start with **Tools** ▸ **Back Up Pictures...**.

The backup does not open in a separate window. It appears in a panel that
slides up from the bottom of the library, in the same place as
[Create a Gift CD](ajandek-cd.md). The two panels cannot be open at the
same time; opening one closes the other. You can continue using the library
while the panel is open.

## What is included

The backup starts with the full contents of your watched folders - the
folders configured in [Folder Manager](mappakezelo.md). It does not depend
on your selection or the folder currently displayed. The set's file filter
and the folder checkboxes decide what is copied; see below.

## Backup sets

Each backup belongs to a set. The set remembers where it saved files and
which files were already copied, so the next run copies only new or changed
files. The first backup of a large library can take a while; later runs are
faster.

You can create several sets, for example, a full backup to an external hard
drive and a smaller one to a network folder.

The panel has two steps. In **Create a Set or use an existing one** on the
left, choose a set. In **Choose folders & albums to back up** on the right,
choose what to include.

Choose a set from the dropdown. Below it are **New Set...**, **Edit Set...**,
and **Delete Set**. The dropdown is hidden until you have at least one set.
**Delete Set** is hidden when only one set remains; you cannot delete the
last set, but you can edit it.

At the bottom of the panel, a line shows where the selected set was saved
and when it last ran. If it has not run yet, the status says so after the
destination. Progress appears in the same place while files are being
copied.

## Creating a set

Choose **New Set...** and enter four values:

- **Backup Set** - the name shown in the list. The field is filled in with
  the suggested name **My Backup Set**.
- **Backup type:** determines the output:
  - **Disk-to-disk backup (for external and network drives)** copies the
    photos into a folder.
  - **CD or DVD backup** creates disc-image files.
- **Save to:** the destination folder. Use **Choose...** to select it.
  This field can be changed only for disk-to-disk backups. For CD or DVD
  backups, PicasaPy chooses the location and shows it in the field: the
  `Picasa Backup\ISOs` folder inside your Pictures folder.
- **Files:** selects what to include:
  - **All file types** - photos, RAW files, and videos.
  - **All pictures (no movies)**.
  - **Only JPEGs with camera data** - JPEG files that contain the camera's
    name. Screenshots and downloaded pictures are left out.

The set form opens in a separate window titled **Backup Set**. Choose
**OK** to save it or **Cancel** to discard it. If PicasaPy cannot accept the
set, the form stays open, keeps your entries, and displays the reason.

**Edit Set...** opens the same fields for an existing set; you can also
change its type. The window is titled **Edit Backup Set**, and its closing
button is **Change**.

**Delete Set** asks for confirmation and includes the set's name. It does
not delete files already saved; it removes only the set's record.

## Choosing folders to include

While the backup panel is open, the whole library switches to backup mode
and shows only files that have not been backed up yet:

- The left pane is limited to folders that still contain files to copy.
  A folder that is fully backed up is hidden. This works in both flat and
  tree views. In tree view, unbacked folders appear expanded together with
  their parent folders so you can see where they are. Closing the panel
  restores the previous tree state.
- The photo grid also shows only files that have not been backed up yet.
  In a partially backed-up folder, only new and changed files appear.
  Closing the panel restores the previous grid and scroll position.

The panel explains that PicasaPy is showing files that have not previously
been backed up.

Each folder shown in the left pane has a checkbox. None are checked by
default, so choose what to include:

- check folders one at a time, or
- choose **Select All** to check every folder. **Select None** clears all
  the checkboxes.

Until at least one folder is checked, the **Backup** or **Burn** button is
disabled.

The list is prepared in the background while PicasaPy reads the library.
Until it is ready, **Calculating…** appears in its place. Changing sets
starts a new calculation. Large libraries can take a while to process, but
you can keep using the application.

Two messages can appear in place of the folder list:

- **Create a Set or use an existing one** - no set is selected yet, so
  PicasaPy has nothing to compare against.
- **All Files are backed up in this set** - every file in the set is already
  backed up, so there is nothing to copy. The same message appears in the
  photo grid.

## Running a backup

Choose a set, check the folders, and then choose the button.

The button says **Backup** when a set is selected. It starts the copy even
for a folder-based backup.

PicasaPy first counts how many files will be copied and displays the total.
For folder backups, it also estimates how many CDs or DVDs the data would
fill. For disc-image backups, it displays a message that files are being
written to an image.

During the copy, a progress bar appears in the panel, and a counter such as
“Copying (12/340) files” shows how far it has got. PicasaPy remains usable;
the copy runs in the background. When it finishes, the application reports
how many files were copied. The final message is **Backup Complete**, even
if there was nothing to copy.

### Stopping a backup

While a copy is running, a **Stop** button appears at the right edge of the
panel and the start button is disabled. If you choose **Stop**, PicasaPy
finishes the current file and then stops.

Stopping does not lose work. Files already copied are recorded, so the next
run continues with the ones that are still missing.

Only successfully copied files are recorded. If the backup stops on its
own - for example, because the destination is full or the network
connection is lost - the next run will copy the missing files.

## Folder or disc image

The backup set's type determines the output:

- A disk-to-disk set copies photos to the destination folder, which can be
  on an external drive, USB drive, or network share.
- A CD or DVD set creates disc-image files. A selector appears beside
  **Burn Disc**, letting you choose **To CD image (ISO)** or
  **To DVD image (ISO)**. This determines the size of each image. The
  selector appears only for this type of set.

If the library does not fit on one disc, PicasaPy creates several numbered
images, such as `picasapy-backup-01.iso`, `-02.iso`, and so on. Each image
is sized to fit on a physical disc. It contains photos in their original
folder structure, their `.picasa.ini` files, and a `files.txt` list in the
root, so you can browse the backup without PicasaPy.

You can mount an image or burn it with any disc-writing application.
PicasaPy does not burn discs itself.

At the end, PicasaPy reports how many files were saved and how many disc
images were created.

## Restoring a backup

You can restore photos from a backup inside PicasaPy, for example, on a new
computer or after losing the originals. The **Restore...** button appears
at the right of the backup panel, beside **Cancel**. It is hidden while a
copy is running and is available whether or not a set is selected.

The button opens **Restore Backup**:

1. Enter or select the backup location in the first field:
   - **Folder...** selects a backup folder, as created by a disk-to-disk
     backup.
   - **Disc image...** selects the first `.iso` file in a disc-image set.
     If the set contains numbered images such as
     `picasapy-backup-01.iso`, `-02.iso`, and so on, PicasaPy finds the
     matching files and restores from all of them.
2. Enter the destination folder in **Restore to:**, or choose **Choose...**
   to browse for it. PicasaPy creates the folder if it does not exist.
3. Choose **Restore**. **Cancel** closes the window. Both buttons are
   disabled while the restore is running.

PicasaPy restores photos and RAW files, not videos. It also restores each
folder's `.picasa.ini` file, preserving tags, stars, and edits. Files are
placed in their original folder structure.

PicasaPy does not overwrite an existing file. If the destination already
contains a file with the same name, that file is skipped and left untouched.
You can safely restore into a folder that already contains photos; only
missing files are copied. Files are copied only to the destination folder.
To see them in the library, add that folder to Folder Manager's watched
folders; see [Folder Manager](mappakezelo.md).

When the restore finishes, the window closes and the panel reports how many
files were restored and how many existing files were skipped.

Restoring runs in the background, so you can keep using PicasaPy.

If something goes wrong, the error appears in red and the window stays open
so you can fix it:

- “Select both a backup source and a restore folder.” - one of the fields
  is empty.
- “The backup could not be restored: ...” - the explanation identifies the
  problem, such as the selected folder or disc image not being a backup, or
  the backup containing no restorable photos.

PicasaPy also recognizes backups made by the original Picasa. You can
restore from its folders or disc images in the same way.

## What goes into the destination

- Photos in their original folder structure.
- A `.picasa.ini` file beside each folder's photos, preserving tags, stars,
  and edits. The backup is a complete archive on its own.
- A `files.txt` list in the destination root, with one line per copied
  file showing its path, size, and modification time. You can read it in
  any text editor without PicasaPy.

## What is not included

The original Picasa could burn CDs and DVDs. PicasaPy does not burn discs;
it creates a folder or disc-image file, which you can burn with any disc
writing application. PicasaPy can restore photos from the backup; see
above.
