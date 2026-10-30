# Collages

A collage combines several photos into one new image.

## Start a collage

Select photos, then use the collage command under **Create** or the
**Collage** button in the photo tray. If nothing is selected, PicasaPy
asks you to select photos in the library or add them to the tray.

The collage opens on its own tab with the editor panel on the left.

## Collage types

Choose a type from the collage-type selector:

| Type | Result |
|---|---|
| **Picture Pile** | Photos scattered on top of one another |
| **Mosaic** | Photos fill the page |
| **Frame Mosaic** | A mosaic with a highlighted center photo |
| **Grid** | Regular rows and columns |
| **Contact Sheet** | Thumbnails with a heading |
| **Multiple Exposure** | Photos layered over one another |

## Settings

On the settings tab:

- **Page Format** sets the collage size and aspect ratio. Options include
  the current display, standard or widescreen monitor, full page, A4,
  letter paper, CD cover, square, small or large print, digital frame,
  and a custom size. You can add a custom aspect ratio.
- Choose **Portrait** or **Landscape** orientation.
- **Grid Spacing** sets the gaps between photos. It is available for
  **Mosaic**, **Frame Mosaic**, and **Grid**. The value updates while
  you drag; the layout is rearranged when you stop or release the
  slider.
- **Draw Shadows** is unavailable for **Multiple Exposure**.
- **Show Captions** adds captions on photos with an **Instant Camera**
  border. The caption appears in the white strip below the photo. When
  disabled, no captions are drawn.
- **Set as Frame Center** chooses the highlighted center photo for
  **Frame Mosaic**.

## Arrange photos in the collage

Drag a photo to move it.

In **Picture Pile**, a ring appears around the selected photo. Drag its
handle to rotate and resize the photo together. Hold `Ctrl` during the
drag to disable rotation, or `Alt` to disable resizing when you want to
change only one.

Buttons at the right edge move a photo forward or backward in the pile,
one position at a time or all the way to the top or bottom. These side
controls appear only when a photo is selected.

Use the small controls at the left edge, or the **Align Rotation**
submenu in the photo's context menu, to straighten a rotated photo or
turn it by 90, 180, or 270 degrees.

**Shuffle Pictures** swaps the positions of photos while keeping the
size and orientation of the gaps. It is disabled for **Contact Sheet**
and **Multiple Exposure**.

**Scramble Collage** creates a completely new random layout. It is
available only in **Picture Pile**; other types determine photo
positions through their layout.

Use **Clear Selection** (`Ctrl+D`) or **Select All** (`Ctrl+A`) to
change the selection. The remove control (`Del`) takes selected photos
out of the collage.

Free rotation with the on-photo ring is available only in **Picture
Pile**. In the other five types, the layout determines each photo's
position and orientation. Rotation alignment still works where a photo
can be selected, including grid layouts. In **Multiple Exposure**,
photos are layered and cannot be selected; right-clicking an empty part
of the canvas does not open a menu.

## Background

The **Background Options** box is available for every type except
**Multiple Exposure**. Choose **Solid Color** and use the color chooser.
It works like the editor's effect color chooser, with five recent
colors, thirty swatches, and a color field; the color field has slightly
different shades. The chosen color is also added to recent colors. See
[The editor](szerkeszto.md).

Choose **Use Image** to use a selected photo as the background, or use
**Set as Background** from the photo's context menu.

## Picture borders

The **Picture Borders** selector appears for **Picture Pile** and
**Contact Sheet**. Other types determine their own borders. Choose
**None**, **White Border**, or **Instant Camera**.

In **Picture Pile**, a border stays inside the space reserved for the
photo, so a bordered photo occupies the same area as one without a
border.

When **Show Captions** is enabled, the caption appears in the white
strip at the bottom of an **Instant Camera** border. PicasaPy chooses a
dark gray caption on a light background and white on a dark background.
Accented characters display correctly. If the caption does not fit,
PicasaPy uses a smaller font rather than cutting it off.

## Clips tab

The third tab shows which photos are used in the collage. Use it to add
or remove photos, or use the more-photos control to bring in another
group from the library.

## Create and save

Choose **Create Collage** to render the final image. PicasaPy reports
where it saved it. Finished collages go into the Collages project
folder in the left pane.

PicasaPy watches the Collages and Movies folders when they are inside
your watched folders. A new file appears there within a few seconds,
even if it was created by an older Picasa on another computer or on a
network drive.

If you edit a collage that already exists, choose whether to replace it
with **Replace Existing** or create another copy with **Create New**.
Collages are always saved in the Collages album. **Cancel** leaves the
editor open without saving.

The **Desktop Background** button in the panel creates the collage and
sets it as your desktop background in one step. See [Desktop
background](hatterkep.md).

If PicasaPy cannot create the collage preview, the creation window
explains the error.

## Drafts

PicasaPy saves an unfinished collage. When you return, it offers to
restore or discard the draft. The **Restore** button undoes all changes
to the collage. When you close the tab, you can choose **Save Draft**
or **Discard Changes**.
