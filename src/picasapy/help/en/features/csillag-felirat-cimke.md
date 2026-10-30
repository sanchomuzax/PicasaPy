# Stars, captions, and tags

All three are stored alongside the photos in `.picasa.ini`, so the image
file itself is not changed — except that captions are also written into
JPEG files (see below).

If a folder has no `.picasa.ini`, the program can also read stars and
captions from the older, capitalized `Picasa.ini` file. This preserves
data in folders last used with a very old version of Picasa. The first
time you save anything in such a folder, the program creates a new
`.picasa.ini` and copies every entry from the old file into it; the
old `Picasa.ini` is left untouched. Backups, saved originals of edited
photos, and move-based imports also account for the old file, so its data
is preserved in those operations too.

## Stars

A star is a quick way to mark a photo. You can add or remove one in these
ways:

- Click **Add/Remove Star** in the photo tray. It applies to every photo
  in the selection.
- Press `F4` to do the same thing, either in the library or in the
  viewer. If the tray button is disabled, F4 will do nothing too.
- During a slideshow, use the star control on the toolbar.

The **Starred Photos** album in the left pane gathers starred pictures,
and the star filter on the toolbar can bring them into view. If you
delete a photo from this album, the program only removes its star. The
file stays on disk and disappears from the album view. Choose **Edit** ▸
**Select Starred** to select all starred photos in the current view at
once.

## Captions

A caption is a short line of text displayed beneath a photo. In the
viewer, click the band along the bottom of the image to enter one. If
there is no caption yet, the band prompts you to add one.
Press Enter to save or Esc to discard your changes.

There is a small control at each end of the band:

- The control on the left shows or hides the band. It displays a light
  square with two lines when the band is visible, and an empty square
  when it is hidden. The control stays in place while the band is
  hidden, so you can use it to bring the band back.
- The control on the right clears the caption without asking for
  confirmation. It is disabled when the caption is empty.

In the grid, use **View** ▸ **Thumbnail Caption** ▸ **Caption** to display
captions below the thumbnails.

### Copying a caption to several photos

**Edit** ▸ **Copy Text** and **Paste Text** copy text placed on an image with
the **Text** tool, rather than the caption (see [The editor](szerkeszto.md)).
This works the same way as in the original Picasa. There is no menu
command for applying a caption to several photos at once; enter it for
each photo separately.

PicasaPy also writes captions to the JPEG file's IPTC field, so other
programs can read them.

## Tags

Tags are shown in the **Tags** panel on the right. Open or close it from **View**,
press `Ctrl+T`, or use the Tags control in the photo tray. Ctrl+T also
closes the panel.

- Select one or more photos, type a tag in the entry field, then press
  Enter or click the adjacent **+** control. The tag is applied to every
  selected photo.
- The panel shows which tags belong to the selection. A heading above
  the list explains its scope: for one selected photo it shows that
  photo's name and its tags; for several photos it lists the tags in the
  current selection; when every photo in the displayed album is
  selected, it indicates that the selection covers the whole album.
- Tag order follows the original Picasa behavior: the tag used on the
  most photos in the selection appears first. Tags used equally often
  are listed in reverse alphabetical order (Z to A).
- Right-click a tag to open a menu with **Remove this tag**, **Search
  for items with this tag**, and **Add this tag to entire selection**,
  in that order. The search puts the tag in the search field and
  immediately shows matching photos. Clear the search field to return
  to the full view.

### Applying a tag to many photos

When more than 30 photos are selected, the program asks for confirmation
before adding a tag: “You have a fairly large number of items selected.
Are you sure you want to apply this tag to all (*N*) items?” Click
**OK** to apply it to the selection, or **Cancel** to leave the photos
unchanged. The confirmation applies whether you use the entry field, a
quick-tag button, or **Add this tag to entire selection** in the tag
context menu. The program captures the selection when the question
appears, so the target set cannot change while you decide.

### When a selected photo is read-only

Tags are stored in `.picasa.ini` next to the photo, so they cannot be
changed in a read-only folder. The panel warns you before you start
typing: “Tags cannot be changed because the selection includes a
read-only item.” The entry field, add control, and quick-tag buttons are
disabled in this situation.

Even one read-only photo triggers the warning. Remove it from the
selection to tag the other photos.

### Create an album from a tag

Choose **Tools** ▸ **Experimental** ▸ **Show tag as album...** to create a
regular album from a tag. Enter the tag, and the program gathers every
photo that has it.

Tags are matched as whole values, so “summer” does not include
“summer-holiday”. If no photo has the tag, the program tells you so.

This is not a live filter. The album is independent once created and
stays in the left pane.

### Quick Tags

At the bottom of the panel, ten buttons hold your most-used tags. Click
one to apply its tag to the selection immediately.

An unused button displays a **?**. Hover over it to see the hint “Click
to configure quick tags”. Clicking it opens an informational message
that explains how to assign a tag to the button; it does not change any
photos.

Use **Configure Quick Tags** to set the buttons. Open the dialog with
the gear control beside the Quick Tags heading; its hint has the same
name. You can reserve the top two buttons for recently used tags. A new
tag moves to the first button, the previous first moves to the second,
and the previous second is removed. If you use a tag already on either
button, their order stays the same. A button in the dialog can also
fill empty slots with your frequently used tags. When tracking recent
tags is turned off, quick-tag use is not recorded; tags used while it is
off will not appear in those slots if you turn it on later.
