# Search and filtering

## Search field

Type in the field at the right end of the toolbar to search as you
type. PicasaPy searches file names, captions, tags, and folder names. If
a folder name matches, all photos in that folder are included.

While you type, a suggestion list opens below the field, matching its
width. It shows folders and albums that match the text. Choosing one
opens that folder or album and clears the search. The left pane narrows
to matching folders and shows how many results each contains. A total
row appears in the Albums section, for example, `Results for “lake”
(12)`.

With the cursor still in the field, use the up and down arrow keys to
move through the suggestions. Press `Enter` to open the highlighted
item or `Esc` to close the list. If no suggestion is highlighted,
Enter does not choose one.

After searching, a green bar appears above the grid with **Back to View
All**. Click it to leave the search, clear the field, and restore the
full folder list in the left pane.

The `×` at the right end of the field clears the search and restores
the previous view.

Right-click the field for the usual text-editing commands: **Undo**,
**Cut**, **Copy**, **Paste**, **Delete**, and **Select All**.

### Search options panel

When you click the search field, or when it contains text, a small
`⌄` control appears beside it. Click it to open or close a panel; the
`Ctrl+F` shortcut opens the panel and moves focus to the field. The
panel shows a summary of results or the active filters, and provides
controls to show only photos with faces or only duplicate files. The
duplicate control works like the duplicate-file view; see
[Find duplicate photos](duplikatumok.md).

The panel can also be opened and closed from the View menu. A check
mark appears by that command while the panel is open.

## Search by color

You can search for a color by putting `color:` before its name in the
search field, for example:

```
color:blue
```

The supported colors are red, orange, yellow, green, blue, purple,
pink, black, white, and gray. Hungarian color names and the unaccented
Hungarian keyword also work.

Shortcuts for seven colors are available from the color-search submenu
under Tools ▸ Experimental. Choosing one enters the matching color
query in the search field and immediately shows photos with similar
colors. You can extend the query by typing more text.

Color and text can be combined: `color:blue vacation` finds photos
that are blue and also match “vacation”. Two different colors in one
query are combined with OR.

PicasaPy calculates colors for photos in the background. A newly added
photo may take a short time to appear in color search results.

## Toolbar filters

Four filters in the center of the toolbar narrow the current view. Only
the active filter appears selected:

- Star: show only starred photos.
- Face: show only photos where a face was found.
- Movie: show only videos.
- Globe: show only photos with a location.

A fifth, duplicate badge is normally hidden. It appears only while the
duplicate view is active and lets you leave that view. See
[Find duplicate photos](duplikatumok.md).

A green bar shows how many photos remain while filtering. Use **Back to
View All** to leave the filter.

The filter area hides in a narrow window so the toolbar stays on one
line. An inactive decorative control that used to appear at the end of
the filter bar was removed because it did nothing.

## The age slider

A small slider beside the filters limits results by age. Its hint says
“Filter by date range”, but it sets only an upper age limit: move it to
the right to keep newer photos. The misleading hint is inherited from
the original Picasa.

The green bar shows the active limit, for example “Photos no more than
9 weeks old”. PicasaPy chooses the unit - days, weeks, months, or years
 - based on the age.

Drag the slider fully left to turn the filter off. Switching to another
view, such as a star filter, search, or another folder, resets it to
the left and removes the age limit from the green bar.

## Find similar photos

Select a photo and press `Ctrl+F7` to find pictures similar to it. As
in the original Picasa, this command is not in the photo's right-click
menu. The results header shows the sample photo. Choose **Clear
Sample** or press `Ctrl+F8` to end the search.

PicasaPy uses the original Picasa method: it compares reduced color
images, color distribution, and edges, then ranks the library photos.
The ranking also considers how close in time a photo was taken to the
sample; nearer dates appear higher. The first 1000 results are shown.
The first search may take longer in a large library while PicasaPy
calculates image features. It saves them so later searches are faster.

This differs from duplicate search, which looks for identical files;
see [Find duplicate photos](duplikatumok.md).

## Save search results as an album

While viewing search results, use the command for saving search results
to create an album from the full result set. The album name starts with
the search text and can be changed later.

For more than 1000 results, PicasaPy asks before creating the album and
offers **Create Album**. With 1000 or fewer results, it creates the
album without asking.

The command is enabled only while viewing search results that contain
at least one photo.

## Selection commands

The **Edit** menu includes:

- **Select All** (`Ctrl+A`)
- **Select Starred**
- **Invert Selection** (`Ctrl+I`)
- **Clear Selection** (`Ctrl+D`)

You can also click to select, use `Ctrl`+click to add or remove one
photo, and `Shift`+click to select a range. Drag from an empty area of
the grid to draw a selection lasso.
