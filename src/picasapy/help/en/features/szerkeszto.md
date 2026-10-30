# The Editor and its seven tabs

## Non-destructive editing

PicasaPy never overwrites your picture file by itself. Edits are stored
as instructions in the folder's `.picasa.ini` file and recalculated
whenever the picture is displayed. The original file stays unchanged
until you save an edited copy (see [Save and Revert](mentes.md)).

## Open the editor

Open a picture in the viewer. The panel on the left is the editor; it
has seven tabs:

| Tab | Purpose |
|---|---|
| **Common Fixes** | Frequently used edits |
| **Fine Tuning** | Adjust light and color with sliders |
| **Effects** | The standard set of effects |
| **Creative** | Additional effects |
| **Artistic** | Stronger effects for a particular look |
| **More Effects** | Effects available in the engine but not in the original Picasa interface |
| **Legacy Effects** | Filters carried over from older Picasa versions |

A blue badge on tiles in tabs 3–7 marks one-click effects. See
[Effects](effektek.md) for the full list and details.

The detailed list is available in [Effects](effektek.md).

## Hide the left panel

The viewer's editor panel can be hidden to make more room for the
picture. **View** ▸ **Show Edit Controls** toggles it, as does the small
left/right arrow at the center of the panel edge. The two controls share
the same state, which is remembered until the next application start.
Ctrl+9 toggles the panel while the viewer is open. The menu command is
disabled in the library view and has no check mark there.

## Show or hide text on a picture

When a picture has text, the Text tile shows a **Show Text** checkbox.
Turning it off hides the text without removing it. The **Picture** ▸
**Batch Edit** submenu offers the same command for several pictures at
once; see [Batch Edit](csoportos-szerkesztes.md).

## Slow effects and the preview

Some effects require substantial processing, including Sharpen, Film
Grain, Glow, Cross Process, Comic Book, Drop Shadow, HDR-ish, Holga-ish,
Lomo-ish, Neon, Orton-ish, Pencil Sketch, and Posterize. Their previews
are calculated in the background instead of immediately as you drag a
slider:

- The window remains usable: menus open and sliders move while the
  calculation runs.
- The picture updates when processing finishes. Until then, the previous
  preview remains visible; a short pause means PicasaPy is working, not
  frozen.
- A progress indicator appears in the blue bar at the bottom.

Some effects produce the right result only at full resolution. Grain,
pixelation, and focus magnification, for example, depend on the
picture's actual size. PicasaPy calculates them at the original
resolution and then scales the preview down, so it matches the saved
file. Large pictures can take longer.

## The left panel while an effect is open

When a slider-based effect is open with **Apply** and **Cancel** buttons,
the rest of the left panel is temporarily unavailable. Clicking another
tab does not switch it: the panel is dimmed and the effect preview stays
open. This matches the original Picasa. Press Esc to discard the effect.

## Effect order matters

Edits are applied in the order you add them. This matters when adding a
frame or crop: later effects, such as Sepia or Vignette, also affect the
frame. Picasa works the same way.

The editor preview matches the image used for saving, exporting, and
thumbnails. Paint applied with the legacy eye-effect brush is included
in a saved picture, but is not yet included in exports or thumbnails.
See the brush-painting section below.

## The right-side panels while editing

The Tags, People, Places, and Properties panels remain available in the
editor. Open them with the four panel controls in the photo tray, from
the **View** menu, or with Ctrl+0. You can tag photos, name a face, or
check picture information without leaving the editor.

## Common fixes

Hover over an editor button or effect tile to see a tooltip explaining
it. Tooltips for effects such as Crop and Sepia use the original Picasa
text. Apply, Cancel, Undo, and Redo also have tooltips.

Nine common controls are available:

- **Crop** opens the separate crop tool.
- **Straighten** levels a tilted horizon with a slider.
- **Red Eye** corrects red eyes.
- **I'm Feeling Lucky** applies a general one-click correction.
- **Auto Contrast** adjusts highlights and shadows automatically.
- **Auto Color** neutralizes color automatically.
- **Retouch** removes a spot with a brush.
- **Text** adds text to the picture.
- **Fill Light** brightens dark areas with a slider.

### Where to find Apply and Cancel

Crop, Retouch, Text, and Red Eye have their own **Apply** and **Cancel**
buttons in the left panel. Straighten is different: its slider and
buttons float in a bar over the picture.

### Straighten

When Straighten opens, a grid appears over the picture to help align the
horizon. The bar is at the bottom of the picture and remains horizontal
even when the photo is rotated. **APPLY** is on the left and **CANCEL** on
the right. The viewer switches to the fitted view and remains there
after you close the tool.

Dragging the slider changes only the preview. **APPLY** saves the
straightening and adds it to the edit history only if the value changed.
**CANCEL**, Esc, navigation, or closing the viewer restores the picture
as it was when the tool opened. While Straighten is open, the left panel
is disabled and its Undo/Redo row is hidden. After applying, Undo is
available and identifies the edit.

## Crop

Choose **Crop** to place a crop frame over the picture. Drag its corners
or sides to resize it, or drag inside it to move it.

- The aspect-ratio list includes freehand, the current ratio, square
  (CD cover), common print sizes, A4, and screen ratios such as 4:3,
  16:10, 16:9, and 5:3. Choose the command for a custom ratio to enter
  width and height and give it a name. A preview explains the ratio.
  Enter fractional values with a comma or decimal point. Custom ratios
  appear under their own heading. Select one and use the trash control
  to delete it after confirmation; built-in ratios cannot be deleted.
  The list also shows the crop's pixel dimensions and the picture's
  current dimensions.
- **Rotate** swaps the ratio's width and height.
- Suggested crops appear as up to three small previews, composed around
  detail, color, horizon, or faces. The previews have no titles or
  captions; the image shows the proposed crop.
- **Preview** shows the result. **Apply** saves the crop
  non-destructively, **Cancel** discards it, and **Reset** removes a
  crop that was already applied.

### Constrain the crop ratio while dragging

Hold a key while drawing a new frame to constrain its ratio:

| Key | Ratio |
|---|---|
| Shift | The picture's own ratio |
| Ctrl | One third wider |
| Alt | One half wider |

Shift does not make a square unless the picture is square; the original
Picasa behaves the same way. If you hold more than one key, Alt takes
precedence over Ctrl, and Ctrl over Shift. The constraint is temporary
and ends as soon as you release the key. While drawing, it overrides the
ratio selected in the list; resizing a completed frame uses the list
setting again. The same keys constrain red-eye and face-addition frames.

## Red Eye

Choose **Auto** to find red eyes automatically. PicasaPy reports whether
it found any and draws a square around each corrected eye, including
automatically corrected ones. Click inside a square to undo only that
correction. **Reset** undoes all automatic fixes.

Automatic correction is limited to eyes in detected faces; it does not
change unrelated red objects such as a lamp or clothing. If face
detection is unavailable, PicasaPy searches the whole picture as
before. If the detector gives an implausible eye position, that face is
skipped while the other corrections continue.

If Straighten has rotated the picture, the panel warns that red-eye
frames may be inaccurate. Undo Straighten first, correct the eyes, and
straighten again if needed.

You can also drag a frame around an eye. Shift, Ctrl, and Alt constrain
its ratio as described above. The panel counts the marked areas. Undo
removes the last one; Reset removes them all. Click inside a frame to
remove just that mark. The pointer changes over a removable frame. If
frames overlap, the most recently added one is on top. These operations
work before applying the correction; afterward, the correction is part
of the picture and the frames are gone. A control hides the square
outlines to show the result clearly.

## Retouch

Use the **Brush Size** slider to set the spot size. Click the area to
repair, move the pointer to preview the replacement, then click again
to apply it. A circle shows the brush size; after the first click, the
target and source circles remain visible until the repair finishes.
When zoomed in, hold Ctrl and drag to pan. The panel reports the number
of repaired spots.

Retouching matches the source texture, such as skin or grass, while
adjusting its brightness and color to the target area. This helps it
blend in even when the source was lighter or darker. **Undo Patch** and
**Redo Patch** move through individual repairs; **Reset** removes them
all.

## Text

Click the picture where the text should appear and type. A picture can
have several text boxes: after applying one, click elsewhere to add
another. Click an existing box to select it, then edit or move it or
change its settings. **Apply** updates the selected box.

You can set the font and size, bold, italic, or underline; align text
left, center, or right; choose text and outline colors and outline
thickness; adjust transparency; or show only the outline without a fill.
The size list contains Picasa's sixteen sizes, from 8 to 96, with 12 as
the default. Text size is relative to the picture height, not the
screen, so it keeps the same proportions on larger pictures. Resizing a
box selects the nearest size in the list. Set outline thickness
continuously; zero removes the outline.

**Copy Caption** inserts the picture's existing caption as text. The
control for removing all existing text clears the text boxes.

Text settings, including font, size, bold, outline thickness, and
colors, are stored in `.picasa.ini`. The caption therefore looks the
same next time and in Windows Picasa.

### Copy text to other pictures

Use **Edit** ▸ **Copy Text** on a selected picture that has text added
with the Text tool. Select the destination pictures and choose **Edit**
▸ **Paste Text**. The text is applied to every selected picture,
replacing matching text there. Text is not added to videos. Paste Text
is available after copying text, or when the first selected picture
already has text that can be copied to the others.

## Color picker and recent colors

Effect color pickers, such as the one for Neon, show five recent colors
below the palette, with the newest first. They remain available until
the next application start. The Text tool has the same recent colors
for text and outline color, shown in smaller swatches beside its
palette.

Choose **Pick Color** to open the larger color picker, arranged like
Picasa's. It shows five recent colors, then thirty preset swatches, and
a large field for selecting hue and brightness. Empty recent-color
slots are dim and unavailable. Click or drag in the field to choose a
color; it takes effect immediately and is added to the recent list.

You can also sample a color from the picture with the eyedropper. The
pointer becomes a crosshair; click a pixel to use its color. It is
added to recent colors, and the eyedropper turns off after one click.

## Brush painting: where the legacy eye effect applies

Only the legacy eye effect can be painted. Boost, Pixelate, Soften, and
Tint apply to the whole picture in the editor, thumbnails, and exports.
The legacy effect has no tile of its own. Its brush controls appear only
for a picture that already has this effect in its settings, such as a
picture edited in Picasa:

- The brush-size slider changes the pointer circle.
- Paint over the picture to mark where the effect should apply.
- Check Eraser to remove painted areas; its size control is then shown.

Painted areas exist only for the editor session. They are discarded
when you switch pictures and are not yet saved in the effect data.
Original Picasa stores those brush strokes; PicasaPy does not support
that storage yet.

When saving from the editor with **File** ▸ **Save**, Save a Copy, or
**Save As...**, the output includes the painted effect, including on
rotated or mirrored pictures. The other listed effects cannot be
painted and continue to affect the whole image. The current painted
legacy effect is baked into the saved picture, but its brush strokes
are not retained in the effect data.

## Fine Tuning

Sliders adjust Fill Light, Highlights, Shadows, and Color Temperature.
Two one-click corrections adjust exposure and color. Neutral Color
Picker lets you sample a neutral gray point in the picture so PicasaPy
can correct the colors around it.

## Histogram

The histogram below the editor shows the distribution of light in the
picture. Nearby, the photo information includes camera name, focal
length and its 35 mm equivalent, shutter speed, aperture, and ISO. If
the file has no EXIF information, PicasaPy reports that. Flash
information is in the Properties panel, as it was in Picasa.

## Undo

**Undo** and **Redo** in the viewer move backward and forward through
edits one step at a time. **Picture** ▸ **Undo All Edits** removes all
edits from the selected pictures in one step.
