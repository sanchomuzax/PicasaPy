# The Library: folders, albums, and collections

The left pane is a map of your library. It can contain four kinds of entries.

Each kind has its own icon, so you can tell at a glance what you are looking at: a folder has a blue folder icon; a regular album has an orange book; **Starred photos** has a green book with a star; project folders created by the program (Collages, Movies, and Exported Pictures) have a purple book with a star; and a tag has a gray tag icon.

The check mark at **View** ▸ **Library View** shows that the main window is displaying the library. This option is always on. Its counterpart, **View** ▸ **Edit View** (Ctrl+3), opens the selected picture (or the first one if several are selected) in the viewer, where you can edit it—see [Viewing photos](nezegetes.md). **Picture** ▸ **View and Edit** does the same. Both commands are disabled when no picture is selected. **View** ▸ **Show Edit Controls** shows or hides the editor panel on the left side of the viewer—see [The editor](szerkeszto.md). In Library View this command is disabled and unchecked, as in the original Picasa; it can only be changed in the open viewer.

## Folders

The **Folders** group shows actual folders on disk. Renaming or moving one here changes it on disk too.

The pane has three display modes. Choose one from **View** ▸ **Folder View**:

- **Flat Folder View** — a single flat list, with one row per folder.
- **Tree View** — folders are nested according to their locations on disk.
- **Simplified Tree View** — a tree that shows only the branches containing your watched folders. Folders outside those branches are hidden. Within a branch, levels that only lead to another folder and contain no pictures are combined so long paths fit on one row. This command sits at the very bottom of the menu, separated from the other two.

Two small view buttons on the toolbar switch between the first two modes. A ▾ button next to them opens the same menu as **View** ▸ **Folder View**, so the view, sorting, and thumbnail options can all be controlled in one place. The two entry points stay in sync. The ▾ button is hidden in a narrow window; every option remains available from the menu bar.

After the sorting commands in this menu are three ways to sort the People list: **Sort People by Name**, **Sort People by Amount**, and **Sort People by Top 10**. A check mark shows which one is active. Below them, the **Shortcuts** submenu offers four destinations—**My Computer**, **Pictures**, **My Documents**, and **Desktop**—the same destinations shown at the top of the submenu (see “Where the tree starts” below).

In Tree View, right-clicking a folder row opens a menu based on the row. A folder that contains your own pictures (a real library folder) gets the full folder menu, as in the other views. A branch row that only leads to other folders and contains no pictures gets a shorter menu.

Right-clicking an empty part of the pane opens the pane's own menu. It contains:

- sorting commands (by name, size, recent changes, or reverse order), and sorting for the People list;
- **Simplified Tree View**;
- **Show Thumbnails in Library**, the same option as in **View** ▸ **Folder View**;
- a **Shortcuts** submenu containing **Desktop**. This jumps to the Desktop folder, just like **View** ▸ **Folder View** ▸ **Desktop**. The label comes from the original Picasa translation; it has nothing to do with keyboard shortcuts.

> Until the program knows which folders you watch, Simplified Tree View keeps the entire tree. It is safer to show too much than to hide your folders. Set watched folders in [Folder Manager](mappakezelo.md).

All three settings are remembered until the next time you start the program.

### Where the tree starts

Four destinations appear at the top of **View** ▸ **Folder View**. The original Picasa put them there too:

- **My Computer** shows the whole tree, with every folder.
- **Pictures**, **My Documents**, and **Desktop** also show the whole tree, but jump to and select the chosen folder.

The **Folders** label tells you where you are: “Default View” in the flat list, “My Computer” in Tree View, or the name of the folder at one of the three destinations.

If the selected folder is not on your computer, no error appears; the tree returns to My Computer. The selected starting point is remembered, so the program starts there next time.

You can change the pane width by dragging its divider, but not below a minimum width. That minimum matches the original Picasa.

### Which folder is which?

A folder row shows only its name, so two folders with the same name look alike. Point to a row and a tooltip shows the folder's full path. This can happen often: the duplicate finder creates a separate <code>Duplicates</code> subfolder in each source folder.

### Thumbnails instead of folder icons

Turn on **View** ▸ **Folder View** ▸ **Show Thumbnails in Library** to show a small thumbnail of a picture from each folder in place of its blue folder icon. A folder always gets the same picture, even after restarting. This is off by default, and your choice is remembered. The thumbnails appear quickly at startup because the program uses thumbnails already in its cache. A folder without a picture keeps its folder icon.

Thumbnails are always shown in Tree View, regardless of this option, so the menu command is disabled there. The option applies to the simple, single-level list.

The empty pane's **Show Thumbnails in Library** command controls the same option, so the two locations cannot get out of sync.

### Folder dates

The folder date appears in the folder header in the grid. It comes from the earliest photo in that folder: first from the photo's EXIF capture time, and, if that is missing—as it can be for generated pictures—from the file time. This means the header is not left blank for pictures without a capture time, and sorting by date can place those folders correctly too.

The program records the file time the first time it scans the picture and does not update it later. This is intentional: many things change a file's modification time, such as saving, copying, or using another program. Without a fixed value, the same picture could jump from the beginning of the grid to the end, and the date in the folder header could move. This does not affect pictures that have an EXIF capture time.

### Folder Properties

Right-click a folder row and choose **Edit Folder Description...**, or open the folder and choose **Folder** ▸ **Edit Folder Description...**, to open **Folder Properties**. Its fields are:

- **Name:** Change the folder name here. The **OK** button renames the folder on disk; its pictures, subfolders, and <code>.picasa.ini</code> move with it. If the name is already in use or invalid, or one of the folder's pictures is being edited, a window titled **Cannot Rename Folder** explains why, and nothing changes.
- **Date:** The folder date, formatted according to your language settings (for example, 2026-01-01 in English). The standard YYYY-MM-DD format is accepted too. Click the calendar icon at the right edge of the field (**Choose date**) to open a calendar underneath. Use the **Previous month** and **Next month** arrows to move between months, then click a day to put it in the field. **OK** saves the date. **Automatic date** clears the date you entered and restores the date of the earliest picture in the folder. If the date is invalid, **OK** is disabled and a line shows the expected format.
- **Music:** Use **Use music for Slideshow and Movie presentation:** and the **Browse...** button to choose an audio file (.mp3 or .wma on Windows; .mp3 or .m4a elsewhere). The music plays during a slideshow of the folder and in a movie made from the folder. The file field and button are enabled only when the check box is selected.
- **Description (optional):** The folder description.

**OK** saves the name, date, music, and description together, then closes the window. **Cancel** saves nothing.

Album Properties opens in the same window (see below). The **Place taken (optional):** field can only be edited for an album or when creating a folder; it is disabled for an existing folder.

### Split a folder

If pictures from two events are mixed in one folder—for example, a trip and then a birthday—you can split the folder in two. Select the picture that should start the new folder, right-click it, and choose **Split Folder Here...**.

**Folder Properties** opens with the new folder's details. Its name is **Untitled**, and its date is the selected picture's date. You can change these and enter a location, description, or music. After you click **OK**, the program creates a new folder next to the current one, in the same parent folder, and moves every picture from the selected one to the end of the folder into it. If the name is already taken, the program adds a number (_1, _2, and so on). **Cancel** makes no changes.

This command is available only in a folder, not in an album or a People album.

### Sorting folders

Sorting can be changed in the middle of **View** ▸ **Folder View** or from the pane's context menu:

- **Sort by Creation Date**
- **Sort by recent changes**
- **Sort by Size**
- **Sort by Name**
- **Reverse sort** — this can be combined with any of the other choices.

### Sorting pictures inside a folder

Right-click a folder and use **Sort Folder By** to sort its pictures by **Date**, **Name**, **Size**, or **Color**, or choose **Reverse order**.

Sorting is a one-time operation: the program sorts the pictures by the selected criterion and records that order as the folder's **Manual order** (see below). It affects only that folder; other folders keep their order. **Reverse order** reverses the current order. You can then adjust the pictures by dragging them.

Sorting by **Name** treats numbers as numbers: <code>photo2.jpg</code> comes before <code>photo10.jpg</code>, not after it. Uppercase and lowercase do not matter. Names starting with a number come first, followed by accented letters (or letters outside the English alphabet), then names starting with A through Z. So <code>Ábel.jpg</code> comes before <code>alma.jpg</code>. The original Picasa sorts this way too.

> The **Folder** ▸ sorting menu does something different: it decides the order of folders in the grid (by date, name, size, or **Sort by recent changes**). It does not change the order of pictures inside a folder.

Sorting by **Color** arranges pictures by their dominant color: colored pictures come first in rainbow order, followed by colorless pictures. The program analyzes colors in the background. If a folder was just scanned and the analysis is not ready, sorting by Color does nothing. Wait a moment and try again.

### Manual order: drag pictures where they belong

You can rearrange pictures with the mouse. Grab the selected pictures and drag them where they should go. The grid shows where they will land. If you move them only a little and drop them where they started, their order does not change.

Manual order is saved next to the pictures, in the folder's <code>.picasa.ini</code>. It survives the next restart and can be carried to another computer with the folder. **Sort Folder By** ▸ **Manual order** restores the saved order in the grid.

A drag always stays within one folder; you cannot sort pictures from several folders together. (Dragging a selection from the left pane onto another folder is a move, not a sort—see [File operations](fajlmuveletek.md).)

### Jump to the next folder from the scrollbar

At the top and bottom of the grid scrollbar there is a double arrow: **Previous album** and **Next album**. They jump to the previous or next header in the grid—that is, to the beginning of the previous or next folder or album—without scrolling through all the pictures. Hold either arrow down to repeat the jump.

## Albums

An album does not move files; it is just a collection of pictures. The same picture can appear in several albums.

- Create an album from the selected pictures with **File** ▸ **New Album...** (Ctrl+N), or choose **New Album...** from the pictures' context menu. The program does not ask for a name; it immediately creates an **Untitled** album from the selected pictures. You can rename it later (see below). Nothing happens if no pictures are selected.
- The toolbar's **+** button works differently, just as it does in the original Picasa: it opens **Album Properties** (the name field says **Untitled**) and, after you click **OK**, creates an empty album without the selected pictures. Add pictures later, for example by dragging them in. Album data is saved in a picture folder's <code>.picasa.ini</code>: if a folder is open in the left pane, it is saved there; in Timeline, search results, or an album view, it is saved to the selected picture's folder (or the highlighted picture's folder when nothing is selected). If there is no such folder, or it is not part of the library, the program says “An album must be saved in an indexed photo folder.” and no album is created.
- Add a picture to an existing album from the **Add to Album** submenu in its context menu. You can also use the album button on the Picture Tray, which opens a menu even when you do not have any albums of your own. Its rows are **Screensaver** (adds the selected pictures to the screensaver; see [Screensaver](kepernyovedo.md)), **Starred photos** (toggles the selected pictures' stars), your own albums, and **New Album...**. The last command opens **Album Properties** and, after you click **OK**, creates an album in the open folder with the selected pictures.
- Remove a picture with **Remove from Album**. The program asks for confirmation in a window called **Remove Items**; its button says **Remove Image** or **Remove Images** when several pictures are selected. The file is untouched; the picture is only removed from the album. You can turn off the confirmation in **Settings** ▸ **General** with “Remove from album without confirmation.”
- Drag pictures onto an existing album row to add them to that album. If you do not have any albums yet, a row under **Albums** says “You can drag and drop pictures here to make a new album.” Drop pictures there to create an album from them. While dragging, the destination row turns blue to show where the pictures will go.

**Starred photos** is a permanent album that shows every picture marked with a star.

### Changing an album's name and details

Right-click the album row and choose **Edit Album Description...** to open **Album Properties**. It has five fields: **Name**, **Date**, **Music:**, **Place taken (optional):**, and **Description (optional):**. The change is written to the <code>.picasa.ini</code> file in every folder that contains a member of the album.

The same window opens for folders (**Edit Folder Description...**); the original Picasa used one window for both. The fields are slightly different for folders (see **Folder Properties** above).

### Delete an album

Right-click the album row and choose **Delete Album**. The program asks, “Are you sure you want to delete the album ‘*name*’?” Confirm with the **Delete Album** button. The program removes the album from every folder's <code>.picasa.ini</code> where it was a member. The pictures remain in their folders, and other albums are untouched; only this collection is deleted.

### Sorting an album's pictures

Right-click the album row and use **Sort Album By** to sort its pictures once by **Date**, **Name**, or **Size**. Hold Shift while choosing to sort in descending order. **Reverse order** reverses the current order.

You can also rearrange an album's pictures by dragging them, just as you can in a folder.

The album order is saved alongside the pictures in <code>.picasa.ini</code>, so it is still there after a restart. It only affects this album; the order in the folders and other albums is unchanged.

### The Album menu in Album view

Commands in the **Folder** menu act on the open folder. When you open an album, the menu bar says **Album** in place of **Folder**, as in the original Picasa. Its first command, **Edit Album Description...**, opens **Album Properties** for the open album (see above). In Folder view, the same command edits the folder description.

When viewing an album or People album, the program remembers the folder you viewed earlier, but the **Locate on Disk**, Remove from Picasa..., **Move...**, and **Delete...** commands are disabled. This prevents them from accidentally affecting the previously viewed folder. To work with a folder, first click it in the left pane.

## Collections

Collections group folders under one name. Click a collection header in the pane to expand or collapse it.

- Choose **New Collection...** from a folder's context menu, in the **Move to Collection** submenu.
- Right-click a collection header to rename or remove it. Removing a collection does not affect your folders.
- The same menu has **Add/Change a password...** to lock the collection with a password (see below).

The program records which collection a folder belongs to in that folder's own <code>.picasa.ini</code>, as the original Picasa did. The grouping moves with the folder and remains after reinstalling the program. If you remove a collection, its folders return to **Folders on Disk**.

If you close the last open collection, the program warns you that the grid will be empty until you open something again.

### Password-protected collections

You can protect your own collections with a password, just like Hidden Folders.

1. Right-click the collection header and choose **Add/Change a password...**. The **Password Entry** window opens.
2. Enter a password, then enter it again in the **Please verify your password** field. While they differ, the window says **The passwords did not match.**
3. Click **Add/Change a password...**.

The collection is now locked: its header remains visible, but its folders disappear and their pictures are removed from the grid. To unlock it, choose the same command, enter the password, and click **Open**. If the password is wrong, the window stays open and says **Please provide a valid password**. Unlocking applies only to that collection and lasts until you close the program; the collection is locked again the next time you start it.

If a password is already set, two buttons are available after you enter the current password:

- **Add/Change a password...** lets you set a new password (enter it twice).
- **Remove the password** removes the lock.

Renaming the collection does not remove its password. The program saves the password in its own settings, not in the folders' <code>.picasa.ini</code> files, and stores only a fingerprint derived from the password, not the password itself. This hides pictures only inside PicasaPy: their files can still be opened with any file manager.

## Projects

The **Projects** group contains folders created by the program itself: Collages, **Movies**, and **Exported Pictures**. Your collages, movies, and exports appear here so you do not have to search for them.

**Exported Pictures** keeps track of the last twenty export destination folders. Folders deleted or renamed in your file manager are removed from the list automatically.

## Thumbnails

- **View** ▸ **Small Thumbnails** (Ctrl+1) and **Normal Thumbnails** (Ctrl+2) change the thumbnail size. For finer control, use the zoom slider at the right end of the Picture Tray. Exactly one of **Small Thumbnails**, **Normal Thumbnails**, and **Edit View** has a check mark: in Edit View it is the last one; otherwise it is the option for the current thumbnail size. If the slider is set between the two sizes, neither thumbnail command is checked.
- In **View** ▸ **Thumbnail Caption**, choose what appears below a picture: **None**, **Filename**, **Caption**, **Tags**, or **Resolution**.

### Small pictures are hidden by default

By default, the grid shows only larger pictures, as in the original Picasa. Very small pictures—such as an icon no longer than 200 pixels—or pictures with a very small area and an extremely narrow shape are hidden from the grid. Check this if a picture seems to have “disappeared” from a folder. It does not affect movies or entries without dimensions.

The **View** ▸ **Small Pictures** option also shows smaller pictures. With a check mark they are shown; without one (the default) they are not. The setting is remembered until the next time you start the program. It does not change the files; it only decides what appears in the grid.

### Display mode for thumbnails

The mode chosen in **View** ▸ **Display Mode**, including **16-bit (dithered)**, is used for thumbnails too. See [Viewing photos](nezegetes.md).

### Dragging a picture into another program

You can drag pictures from the grid or the Picture Tray into another program, such as an email or file manager window. The other program receives them as files: every picture in the selection, not just the one you grabbed. From the tray, the tray's own selection is sent, even if its pictures come from several folders. The program does not change the files during this operation. (Dragging between folders and albums is separate; see above.)

### The magnifier in the grid

There is a small magnifier button to the left of the zoom slider on the Picture Tray (its tooltip says “Magnifier—drag over pictures”). When enabled, the button has a blue background. Drag while holding the mouse button over a picture in the grid and a small window appears under the pointer. It shows the picture at full resolution, at 1:1, so it has more detail than the thumbnail itself. A click alone does nothing; you have to drag. Use the same button to turn it off.

### Quick preview with Ctrl+Alt

Hold Ctrl and Alt together in the grid to show the selected picture, enlarged, in a small separate window at the center of the screen. Release the keys to hide it. You can inspect a picture more closely without opening it in the viewer.

There are a few conditions:

- The selected picture is used, not the one under the mouse pointer.
- No preview appears for a movie.
- The grid must be wide enough (about 1024 pixels or more). It does not appear in a small window or a narrow grid.

## The Picture Tray

The tray at the bottom of the window always shows the current selection. The blue strip above it shows the number of pictures, their date range, and the space they take up.

The date appears in one of two forms. If all selected pictures are from the same day, one date is shown; if they span several days, the earliest and latest dates are shown. The size label follows the same rule. At the end of the strip, when there is something to show, the program lists which tags are in the selection and how many pictures have each tag (for example, “Tags: vacation (12)”). This part is omitted if the selection has no tags.

The tray is especially useful when you want to gather pictures from several folders, for example, for a collage:

- **Hold selected items** pins the current contents so they do not disappear when you move to another folder. After that, you can add more selections.
- **Clear Tray** empties the tray.

You can also drag pictures from the grid onto the tray. They are added when you release the mouse, and the tray keeps them as if you had chosen **Hold selected items**.

Ctrl+H does the same thing as the tray's hold-selection command: it pins the selection. It does not work in the viewer.

If you go from a collage page back to the library to collect more pictures, a strip appears above the tray with this message: “Select the items you want to add to the project's clip tray, then click Back to return to the project.” Use **Back to Collage** to return to the collage. The × at the right end of the strip hides the message only; the collage page stays open. See [Collages](kollazs.md).

The same strip appears if you go to the library with **Get more...** on the **Movie Maker** page. In that case, the button says **Back to Movie Maker**. See [Movies](mozgofilm.md).

### When you click an album

If you select an album in the left pane while no picture is selected, the tray shows one cover picture instead of thumbnails, along with the selection and picture count—for example, “Selected album—12 photos.” As soon as you select a picture, thumbnails take its place. In a People album, the tray also shows one picture: the person's portrait, with the number of pictures in the selected album. This does not apply to folders; their usual appearance does not change.

The tray has its own selection, independent of the grid. Click a picture in the tray to select it (a blue outline marks it); use Ctrl to add or remove one, and Shift to select a range. Selecting pictures in the grid does not clear the tray selection.

Right-click a picture in the tray to **View and Edit**, rotate it, **Locate on Disk**, open **Properties**, or **Remove Selection**. The last command removes the pictures selected in the tray from the tray. You can also pin the tray with **Hold Selection**.

The magnifier is at the right end of the tray. Click it, then drag over the pictures to see their details enlarged.

The tray's output buttons—**Print**, **E-Mail**, **Export**, **Collage**, and **Movie**—do not all fit in a narrow window. In that case, a **Get more...** button appears at the end of the row, and buttons that do not fit are available in a vertical column when you click it. The column uses the same icons and labels as the row, and a command is disabled when its button is disabled.

The green **Upload to Google Photos** button on the tray uploads all the pictures in the tray after you sign in through Settings. See [Upload to Google Photos](google-fotok.md).

Right-click the output buttons and choose **Configure Buttons...** to open the same window as **Tools** ▸ **Configure Buttons...** (see [Settings](beallitasok.md)).

## Changing picture dates

If a picture has the wrong date—for example, the camera clock was set incorrectly—you can fix it. Select the pictures, then choose **Tools** ▸ **Adjust Date and Time...**. The **Adjust Photo Date - %1 items** window (or **Adjust Photo Date** for one picture) shows the first picture's thumbnail and its **Current photo date**. The date and time appear in two separate gray, read-only fields, as in the original Picasa. You can enter a **New photo date** (click the date to open a calendar) and a **New photo time**. Choose one of two modes:

- **Adjust all photo dates by the amount** adds the difference between the first picture's old and new dates to the time of every selected picture. The time differences between pictures are preserved.
- **Set all photos to the same date and time** gives every picture the same date and time.

**OK** saves the change. While dates are being written, the **Setting photo dates** window shows a spinning indicator. It closes by itself when the work is done. As in the original Picasa, the new capture date is written into the picture file's EXIF data. The file's on-disk timestamps (for example, its modification time) are not changed. The <code>.picasa.ini</code> file is not changed either. The program then rereads the folder, so the grid, date sorting, and **Properties** panel show the new date. Since it is in the file, other programs can see it too.

Writing the EXIF date works for JPEG pictures. For files that cannot store a date—movies, pictures in other formats, or files that are write-protected—the program records the new date in its own catalog instead. PicasaPy shows and sorts by that date after a restart and folder rescan, but the file itself is unchanged, so other programs still see the old date.

## The Properties panel

The right-hand drawer opens and closes with Ctrl+0 or by clicking its narrow, normally invisible edge. Its **Properties** panel (also available with Alt+Enter or from the Picture Tray panel switch) shows details for the selected picture. At the top are **File Path**, **File Size**, and **Dimensions**. Below are capture details: **Camera Make**, model, capture and digitized dates, **File Date**, orientation, **Flash**, the **Lens** name, **Focal length**, **CCD Width**, **Exposure Time**, **Aperture**, **F Number**, ISO, **White balance**, **Metering Mode**, **Exposure Program**, **Compression**, **Color Space**, and **JPEG Quality**. The panel ends with **Keywords**, **People Tags** (the people named in the picture, with a count when a name appears more than once, such as “Anna (2)”), and GPS coordinates.

Right-click the panel to open its only command, **Edit Tags**, which opens the Tags panel.

When there is a selection, the panel also has a **Keywords** button beside the selection's tags. It opens the **Tags** window, with the picture's thumbnail, name, and date at the top and the **Tags:** list below. Enter a tag in **Add Tag:** and click **Add** to apply it to the selection. Select a tag in the list and click **Remove** to remove it. **Done** closes the window. If a selected picture is write-protected, the window says “Tags cannot be changed because the selection contains a read-only item.” and editing is disabled. Adding tags does not change the date of a picture without a capture date.

The order matches the original Picasa. If a value is not in the file, its row is not shown, so the panel is shorter or longer for each picture. For a movie, the three rows at the top are followed by movie details: **Movie Info** shows the format, **Movie Rate** shows frames per second (for example, 25 fps), and **Movie Length** shows the duration as minutes:seconds or, for longer movies, hours:minutes:seconds.

### The lens name

If the picture contains XMP data—which most editing programs write to the file—and that data has a lens name, the program shows that name and does not look further. This is the same order used by the original Picasa.

Otherwise, most cameras do not write the lens name in plain language; they store only an identifier. For pictures from Canon and Nikon cameras, the program resolves that identifier and shows the real lens name in the **Lens** row, using the same list as the original Picasa. If an identifier matches several lenses, it chooses among them using the focal length and aperture.

If the file contains a lens name but the lookup finds no match, the name from the file is kept. If there is no name there either, the program builds one from the focal length and aperture read from the file, for example, 18-55mm f/3.5-5.6. For other camera makers, the name in the file is used for now.

### Compression and white balance

The **Compression** row names the picture's storage format: **Uncompressed**, JPEG, LZW, JPEG 2000, **Deflate**, and manufacturer-specific raw formats such as **Nikon NEF Compressed**, **Sony ARW Compressed**, and **Pentax PEF Compressed**. It recognizes 36 codes in all. If the file contains an unknown code, the program shows the number.

The same applies to **White balance**: it shows **Auto** or **Manual**, and displays the number if the file stores another code. This way, the row is not left blank if the camera wrote something unusual.

## Hidden pictures

Hide a picture with **Picture** ▸ **Hide** or **Hide** in its context menu. The file stays on disk. **Picture** ▸ **Hide** hides only visible pictures in the selection; if the selection already contains a hidden picture, it does not reveal it.

To show hidden pictures, turn on **View** ▸ **Hidden Pictures**. Use **Picture** ▸ **Unhide** to reveal them. This reveals only hidden pictures in the selection; pictures that are already visible are not hidden. This command is available only if the selection contains a hidden picture; otherwise it is disabled. The picture's context menu has the same command, which changes to **Unhide** in place of **Hide**.

You can hide an entire folder too: select it, then choose **Folder** ▸ **Hide** or **Hide Folder** from the folder's context menu. In Album and People views there is no selected folder, so **Folder** ▸ **Hide** and **Folder** ▸ **Unhide** are disabled. The folder disappears from the left pane. Turn on **View** ▸ **Hidden Pictures** to find it under Hidden Folders. Restore it with **Folder** ▸ **Unhide** (available only for a hidden folder; disabled for a visible one) or with **Unhide Folder** in its context menu. To use the context menu, first turn on **View** ▸ **Hidden Pictures** and select the folder under Hidden Folders. The folder remains on disk.

Pictures in a hidden folder do not appear anywhere else either: search, filters (stars, movies, faces, and age), People view, Timeline, albums, the map, similar-picture and duplicate searches, slideshows, the screensaver, and the Picture Tray all leave them out. They appear only when **View** ▸ **Hidden Pictures** is on (and, if there is a password, after unlocking).

The hidden state is written to the folder's own <code>.picasa.ini</code>, as Picasa did. The folder therefore stays hidden when the program rescans the library, and folders hidden in the old Picasa appear hidden here too. If <code>.picasa.ini</code> cannot be written, the program tells you: the folder is hidden here, but Picasa will not see it as hidden. A folder that is unavailable, for example on a disconnected drive, cannot be shown again until it is available; it stays hidden in the meantime.

A hidden folder cannot be moved into a collection. Unhide it first.

### Password for hidden folders

You can lock Hidden Folders with a password. If a password is set, turning on **View** ▸ **Hidden Pictures** asks for it first.

If you do not have a password yet, the program asks after you hide a folder: “The ‘Hidden Folders’ collection is not password-protected. Would you like to set a password now?” **Add Password** opens the password window; **Don't Add Password** skips it. If you select the **Do not ask me again.** check box and choose not to add a password, the question will not appear again. Revealing a folder or turning on **View** ▸ **Hidden Pictures** does not show this question.

To set a password later:

1. Turn on **View** ▸ **Hidden Pictures**. A Hidden Folders header appears at the bottom of the left pane, but only if you have hidden folders.
2. Right-click the header and choose **Add/Change a password...**. (The header only responds to a right-click; it cannot be selected.) The **Password Entry** window opens, as it does for your own collections.
3. Enter the password twice, with the second entry in **Please verify your password**, then click **Add/Change a password...**. Until the two fields match, the button is disabled and the window says **The passwords did not match.**

Below the fields is a check box, **Stronger protection (Picasa cannot open it)**. It appears only for Hidden Folders.

- When unchecked (the default), the password is stored the same way as in the Windows version of Picasa. If you view the same folders in both programs, the password unlocks them in both.
- When checked, the password is stored more securely, but the Windows version of Picasa cannot unlock the hidden folders.

If a password is already set, the window asks for the current password. After entering it:

- **Open** shows the hidden pictures.
- **Add/Change a password...** lets you set a new password.
- **Remove the password** removes the lock.

If you enter the wrong password, the window stays open, says **Please provide a valid password**, and the folders remain hidden. You can try again right away.

> The password hides pictures only in the PicasaPy interface. The files remain on disk and can be opened with any file manager.

## File types the program can see

PicasaPy detects three kinds of files in watched folders:

- Photos — JPEG (.jpg, .jpeg, and .jpe), PNG, TIFF, BMP, GIF, PSD, TGA, and WebP.
- Raw photos — common manufacturer extensions such as CR2, NEF, ARW, DNG, ORF, RAF, and RW2 (see below).
- **Movies** — for example AVI, MOV, MP4, MKV, WMV, MPG, MPEG, 3GP, TS, M2V, OGG, and OGV.

Every other file, such as documents and audio recordings, remains invisible. The program does not index or change it.

### Raw files

Raw files are now displayed as pictures: in the grid, the large viewer, folder cover pictures, and the editor preview. Their thumbnails are also saved in the cache, so they load faster the next time.

You can use a raw file just like a JPEG: export it, find duplicates, search by color, make a collage or slideshow, save it for the web, import it, and search for faces.

Two things to know:

- Saving edits to a raw file is not supported; the program shows an error. Raw files cannot be written back, and the original Picasa did not do that either. Export the picture if you want a saved copy.
- If a raw file still cannot be opened (for example, because the camera model is unknown or the file is damaged), a placeholder appears in its place instead of a silent, empty image.

## When a folder is unavailable

If a watched folder is on a disconnected drive or an unavailable network share, PicasaPy does not forget it. Its pictures stay in the database and thumbnails come from the cache. The folder is marked, and the program tells you if you try to open or edit one of its pictures.

It is different if you delete a folder outside the program, for example in your file manager, while its drive is available. The folder and its pictures disappear from the left pane, as they do in the original Picasa. If you try to drag a picture to a folder that no longer exists, the program does not start a file operation.

