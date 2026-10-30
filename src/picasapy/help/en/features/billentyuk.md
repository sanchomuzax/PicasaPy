# Keyboard shortcuts

This page lists only shortcuts that work. Shortcuts shown for disabled menu
items do nothing.

Two general rules from the original Picasa apply:

- Shortcuts do not run while you are typing. When a text field has focus - 
  for example, search, rename, or a caption - the key belongs to that field.
  `Ctrl+A` selects the field's text, the arrow keys move within it, and
  `Enter` or `Esc` acts on the field.
- Library shortcuts work in the library. `Ctrl+A`, `Ctrl+D`, `Ctrl+I`, and
  `Ctrl+H` do nothing while you are in the enlarged viewer; the viewer has
  its own shortcuts.

## File

| Shortcut | Action |
|---|---|
| `Ctrl+N` | Create a new album |
| `Ctrl+O` | Add a file to Picasa |
| `Ctrl+M` | **Import From...** |
| `Ctrl+S` | **Save** |
| `Ctrl+Shift+S` | **Export Picture to Folder...** |
| `Ctrl+P` | **Print...** |
| `Ctrl+E` | **E-Mail...** - see [Email](email.md) |
| `Ctrl+Shift+P` | **Print Contact Sheet...**, even when nothing is selected; it prints the open folder |
| `Ctrl+Enter` | **Locate on Disk**; when nothing is selected, it opens the current folder in the file manager |
| `F2` | **Rename...** |
| `Delete` | **Delete from Disk** in the grid; in an album or People album, it removes the photo from the collection instead |
| `Ctrl+Delete` | **Delete from Disk** in the viewer; for a photo opened from an album or People album, it removes it from the collection instead |

## Editing and selection

| Shortcut | Action |
|---|---|
| `Ctrl+A` | **Select All** |
| `Ctrl+D` | **Clear Selection** |
| `Ctrl+I` | **Invert Selection** |
| `Ctrl+C` | **Copy** |
| `Ctrl+X` | **Cut** |
| `Ctrl+V` | **Paste** into the selected folder |
| `Ctrl+R` | **Rotate Clockwise** |
| `Ctrl+Shift+R` | **Rotate Counterclockwise** |
| `Ctrl+Shift+H` | Mirror the selected photos horizontally |
| `Ctrl+Shift+V` | Mirror the selected photos vertically |
| `Ctrl+Shift+B` | Convert the selected photos to black and white |
| `Ctrl+Shift+E` | Apply **I'm Feeling Lucky** to the selected photos |
| `Ctrl+H` | Keep the Photo Tray selection; this is the **Hold selected items** control. See [The library](konyvtar.md). It does not work in the viewer. |

Mirroring has no menu item in the original Picasa either; it is available
only from the keyboard. It affects the selected photos, or the photo
currently shown in the viewer. Pressing the same shortcut again reverses
the change. Mirroring does not alter the image file: the setting is stored
in the `.picasa.ini` file beside the photo and is reflected in thumbnails,
saving, exports, email attachments, and web exports.

When a text field has focus, `Ctrl+V` pastes text into the field instead of
using the photo command.

With the mouse, use `Ctrl`+click to add or remove individual photos,
`Shift`+click to select a range, or drag from an empty part of the grid to
select photos with a lasso.

## View and panels

| Shortcut | Action |
|---|---|
| `Ctrl+1` | **Small Thumbnails** |
| `Ctrl+2` | **Normal Thumbnails** |
| `Ctrl+4` | **Slideshow** |
| `Ctrl+5` | Timeline: a full-screen presentation of your folders. See [Viewing photos](nezegetes.md). |
| `Ctrl+T` | Open or close the Tags panel |
| `Ctrl+K` | Open the Tags panel, same as `Ctrl+T` |
| `Ctrl+0` | Show or hide the right-hand panel |
| `Ctrl+3` | Open the selected photo in the viewer |
| `Ctrl+F` | Move focus to the search field |
| `F3` | Move focus to the search field, same as `Ctrl+F`; it does not work in the viewer |
| `F4` | Add or remove a star on the selected photos, like the star button in the Photo Tray. It also works in the viewer, but not during a slideshow or while typing. |
| `Ctrl+F6` | Switch to the duplicate view |
| `Ctrl+F7` | **Find Similar Pictures** |
| `Ctrl+F8` | Clear the similarity sample |
| `F5` | Refresh the open folder: scan for changes on disk and update the view and search results |
| `Alt+Enter` | Open **Properties** |
| Hold `Ctrl+Alt` | Show a large preview of the selected photo in a separate window. See [The library](konyvtar.md). |

`Ctrl+3` does the same thing as **View** ▸ **Edit View** and
**Picture** ▸ **View and Edit**: it opens the selected photo in the viewer.
The two menu items are enabled only when a photo is selected.

`Ctrl+0` closes whichever right-hand panel is open - Tags, Places,
Properties, or People - and restores that same panel when you open the
drawer again.

## Tabs

The library and open projects (collages and movies) appear as tabs at the
top of the window. You can switch between them with the keyboard:

| Shortcut | Action |
|---|---|
| `Ctrl+Tab` | Next tab |
| `Ctrl+Shift+Tab` | Previous tab |
| `Ctrl+Right Arrow` | Next tab |
| `Ctrl+Left Arrow` | Previous tab |
| `Ctrl+W` | Close the current project tab |
| `Esc` | Close the current project tab, when a project tab is active |

Tab switching wraps around: after the last tab, it returns to the library.
The library tab cannot be closed. If a tab has unsaved changes, PicasaPy
asks before closing it.

## Sliders

When a slider has focus, `+` and `=` increase its value; `-` and `_`
decrease it. Each key press changes the slider by 2% of its full range.
This works on the sliders in the editor's third, fourth, and fifth tabs - 
**Effects**, **Creative**, and **Artistic** - and on the **Straighten**
slider. It does not work on sliders in other views.

## While dragging a selection frame

When cropping, marking red-eye areas, or adding a face, hold a key to
constrain the frame's aspect ratio:

| Key | Ratio |
|---|---|
| `Shift` | The photo's own aspect ratio (not a square) |
| `Ctrl` | One-third wider than that |
| `Alt` | One-half wider than that |

`Alt` overrides the other keys; `Ctrl` overrides `Shift`. Releasing the
key immediately removes the constraint.

## In the viewer

| Shortcut | Action |
|---|---|
| `F` | **Show Faces** |
| `Shift+F` | **Edit Faces** |
| `Ctrl+9` | Hide or show the left editor panel |
| `F11` | Toggle full-screen mode; it has no effect during a slideshow |
| `Esc` | Return to the library |
| `Enter` | Return to the library when viewing one still photo with no editing tool open. With single-click exit enabled, while viewing a video, or while comparing two photos, it advances to the next photo instead. |
| `Ctrl+F9` | Quickly move through the folder to the end. Any manual page change or closing the viewer stops it. |

## During a slideshow

| Shortcut | Action |
|---|---|
| `Space` | Pause or resume |
| `Right Arrow` or `Enter` | Next photo |
| `Left Arrow` | Previous photo |
| `Ctrl+R` | **Rotate Clockwise** |
| `Ctrl+Shift+R` | **Rotate Counterclockwise** |
| `Esc` | Exit |

## While editing a collage

| Shortcut | Action |
|---|---|
| `Ctrl+A` | **Select All** |
| `Ctrl+D` | **Clear Selection** |
| `Delete` | Remove the selected photos from the collage |

## Screenshots (Windows only)

While PicasaPy is running on Windows, `Print Screen` captures a screenshot
even if you are working in another application's window:

| Shortcut | What it captures |
|---|---|
| `Print Screen` | The entire screen |
| `Ctrl+Print Screen` | The foreground window |
| `Alt+Print Screen` | The window under the pointer |

The image is saved as a BMP in the `Picasa\Screen Captures` subfolder of
your Pictures folder. Its name includes the captured window's title and the
time; a full-screen capture is named `Fullscreen capture`. The folder
appears in the Projects section of the left pane. PicasaPy shows a
notification saying **Screenshot saved** when the file is ready.

This feature does not work on Linux because the operating system does not
let an application monitor other windows' keyboard shortcuts. There,
`Print Screen` behaves according to your system settings.

## Help

| Shortcut | Action |
|---|---|
| `F1` | Open this guide |
| `Shift+F1` | Open the help chapter for the part of the interface under the pointer. See [Built-in help](sugo.md). |

## Context menus (right-click)

Context-menu items match the original Picasa. Some items now work:

- *Left pane, folder list:* **Show Thumbnails in Library** is a checked
  toggle. The Desktop shortcut switches the folder tree to Desktop.
- *Viewer:* if a photo has a preserved original on disk, the **Search**
  submenu contains **File on Disk** and **Locate Original on Disk**.
  Otherwise, it contains only **Search**.
- *Photo Tray:* **Hold selected items** does the same thing as `Ctrl+H`.

## Menu access keys

Most menu items have an underlined letter. Press `Alt` and the underlined
letter to open a menu, then press the underlined letter of an item to
select it. The underlined letters depend on the current interface
language.

The built-in shortcut list under Help shows the shortcuts that currently
work, grouped by menu. It updates when the shortcut bindings change; this
page explains what each one does.
