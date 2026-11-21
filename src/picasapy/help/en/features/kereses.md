# Search and filtering

## Search field

Type in the field at the right end of the toolbar to search as you
type. PicasaPy searches file names, captions, tags, folder names, album
names, and the author and copyright fields of the photo's EXIF data. If
a folder name matches, all photos in that folder are included; if an
album name matches, the album's photos are included.

You do not have to click the field first: when the thumbnail grid or the
folder list on the left has focus, typing a letter, digit, or symbol
puts it in the search field and starts the search. Accented letters and
keys pressed together with Ctrl or Alt do not start a search.

### How your text is read

- With several words, PicasaPy looks for all of them: `lake summer`
  returns only photos that match both words.
- A minus sign before a word excludes it: `lake -summer` returns lake
  photos without the summer ones.
- Periods, underscores, and most punctuation separate words.
- You can search by the date taken, separated by colons: `2019:03:08`
  finds a day, `2019:03` a month, and `2019` a year.
- Start the text with `tag:` to search only among tags. Without the
  prefix, file names, captions, tags, and folder names are searched too.
- While you type, PicasaPy waits until you pause before searching, so
  fast typing does not slow it down.

The field background shows the result: light green when there are
matches and light red when there are none. When hidden photos are not
shown, they are left out of the result count, the left pane, and the
green bar.

### Suggestion list

While you type, a suggestion list opens below the field, matching its
width. It lists matching words (tags and other search words), folders,
and albums. Word rows show how many photos contain the word, with the
more frequent words first. Only albums that contain photos appear.

- Click a word row to put the word and a space in the field and run the
  search.
- Choose a folder or album to open it; the search stays in place.

The left pane narrows to the folders that contain matches and shows how
many results each contains. A total row appears in the Albums section,
for example, `Results for “lake” (12)`. Counts above 1,000 use thousands
separators. When nothing matches, the bar shows **No matches**.

With the cursor still in the field, use the up and down arrow keys to
move through the suggestions, and press `Enter` to open the highlighted
item. If no suggestion is highlighted, Enter does not choose one.

### Leaving the search

- The first `Esc` only closes the suggestion list. The next `Esc` clears
  the search and keeps the cursor in the field.
- Pressing `Ctrl+F` a second time also closes the search.
- After searching, a green bar appears above the grid with **Back to
  View All**. Click it to leave the search.
- The `×` at the right end of the field clears the search.

Whichever way you leave, PicasaPy restores the folder and the photo
selection you had before searching, and the left pane shows the full
folder list again.

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

Filters work together with the text in the search field: while you also
search, only photos that match both the filter and the search remain.
Turning a filter off keeps the search text, and clearing the text keeps
the filter on. The movie filter works the same way: after clearing the
text, the movie view stays.

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

The slider works together with the search text. If you set it while
searching, the text stays in the field, and the slider stays where it
is when you change or clear the text. The right end of the green bar
then shows the limit after the “Date Range:” label.

Drag the slider fully left to turn the filter off. Switching to another
folder or another filter resets it to the left and removes the age
limit from the green bar.

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
