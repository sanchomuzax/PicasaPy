# Effects

The effects are on tabs 3-7 of the editor. They are non-destructive: you
can undo them at any time, and they do not change the original file.

For an effect with sliders, its controls appear in the panel after you
select it. **Apply** commits the settings; **Cancel** discards them.

Effects follow the original Picasa calculations. In this version,
several effects - including **Neon**, **Lomo-ish**, **Local Contrast**,
and **HDR-ish** - now look closer to the original. If a photo edited in
an older PicasaPy version looks slightly different with one of these
effects, that is why; your saved settings have not changed.

A blue badge in the corner of a tile marks an effect that applies in one
click, with no settings to adjust.

The color chooser for **Polaroid**, **1960s**, and **Rounded Edges** is
called **Background Color**. It controls the background around the
photo.

Some effects also have a color chooser beside their sliders. For
example, **Neon** lets you choose the color of the glowing edges; red is
the default. **Filtered B&W** starts with white on a new photo, as it
did in the original Picasa. If the photo already has this effect, the
panel opens with the last color used.

The small tile preview shows the photo's current state. If you have
already edited the photo - for example, made it black and white - the
tiles start from that version and add their own effect. After each time
you select **Apply**, all previews update to show the new state. This
lets you see the result before choosing an effect, rather than seeing
how it would look on the untouched photo.

## Effects tab (tab 3)

| Effect | What it does |
|---|---|
| Sharpen | Emphasizes edges |
| Sepia | Adds a warm, aged tone |
| B&W | Removes color |
| Warmify | Warms skin tones |
| Film Grain | Adds film grain; adjustable with a slider |
| Tint | Applies a single-color tint with the **Tint Color** chooser (light blue by default) and **Fade** slider |
| Saturation | Adjusts color intensity |
| Soft Focus | Blurs the image while keeping a central point sharp |
| Glow | Adds a soft, luminous effect |
| Filtered B&W | Converts to black and white using a color filter |
| Focal B&W | Leaves one spot in color and makes the rest black and white; use the **Size** and **Sharpness** sliders |
| Graduated Tint | Applies a colored gradient from one edge; the **Feather** slider starts at 0.25 |

## Creative tab (tab 4)

| Effect | What it does |
|---|---|
| Fade | Shifts colors as in cross-processing |
| Duo-tone | Maps the image to a transition between two colors |
| HDR-ish | Simulates a high-dynamic-range image |
| Heat Map | Maps brightness to heat-map colors |
| Holga-ish | Emulates an inexpensive plastic camera |
| Infrared Film | Simulates infrared photography |
| Invert | Creates a negative image |
| Lomo-ish | Adds strong contrast and color with dark corners |
| Orton-ish | Creates a soft, glowing, painterly look |
| Posterize | Reduces the image to a few colors sampled from the photo |
| 1960s | Applies colors associated with the decade |
| Cinemascope | Adds a wide cinematic look and color treatment |

### Posterize uses colors from the photo

**Posterize** does not switch to a fixed palette. It looks at the colors
in the photo, selects a few, and replaces each pixel with the closest
one. The same settings therefore give different results on different
photos: a sunset gets warm bands, while a forest image gets greens.

The boundaries between color areas are not perfectly sharp. The program
softens the image slightly before choosing the colors, as the original
Picasa did.

## Artistic tab (tab 5)

| Effect | What it does |
|---|---|
| Boost | Increases color and contrast |
| Border | Adds a frame around the photo |
| Comic | Creates a comic-book look with a halftone pattern; adjust **Color Brush**, **Dot Density**, and **Dot Fade** |
| Drop Shadow | Adds a shadow behind the photo |
| Focal Zoom | Magnifies a point with radial blur; adjust **Zoominess** and **Focal Size** |
| Museum Matte | Adds a picture-frame-style mat |
| Neon | Draws glowing edges in a chosen color |
| Pencil Sketch | Simulates a pencil drawing; adjust **Radius**, **Strength**, and **Fade** |
| Pixelate | Breaks the image into large pixels; adjust **Pixel Size**, **Blend Mode**, and **Fade** |
| Polaroid | Tilts the photo in a white Polaroid frame |
| Soften | Softens and blurs the photo; adjust **Softness** and **Fade** |
| Vignette | Darkens the corners |

### Polaroid frame and background

**Polaroid** crops the photo to a square, adds a white frame that is
narrower at the sides and wider at the bottom, casts a shadow, and tilts
the result. A positive **Rotate** value tilts it clockwise.

**Background Color** changes the area around the tilted photo where the
shadow appears; it does not recolor the frame. The frame remains white
for every background color, just as in the original Picasa.

### Soften at zero strength

When **Soften** is set to zero, the photo remains unchanged. It does
not become softer or darker. The original Picasa behaved the same way.

### Pixelate sliders

**Pixelate** has three sliders: **Pixel Size**, **Blend Mode**, and
**Fade**. Pixel Size controls the size of the blocks. Fade controls how
much of the original photo shows through.

Blend Mode controls how the pixelated version combines with the
original. It has ten positions, from left to right: Add, Darken,
Difference, Hard Light, Lighten, Multiply, Overlay, Screen, Subtract,
and Normal at the far right. Normal is the default and simply covers
the photo with the pixelated version. These are the original Picasa
blend modes. Their names do not appear on the slider; the handle's
position shows which one is selected.

## Additional effects (tab 6)

These effects are available in the Picasa engine, but did not have
buttons in the original Picasa 3.9 interface:

| Effect | What it does |
|---|---|
| Film Grain | Same as the effect on the Effects tab (listed twice) |
| Local Contrast | Emphasizes local detail |
| Matte | Adds a muted, matte finish |
| Night Vision | Adds a green night-vision look |
| Rounded Edges | Rounds the corners |

## Legacy effects (tab 7)

These filters come from older Picasa versions. Most no longer have a
button in the current Picasa interface, but they may still be present in
older `.picasa.ini` files. PicasaPy recognizes and preserves them.

The tab lists 21 such filters. Sixteen can be applied: select one just
as you would another effect. The remaining five stay visible but are
disabled because their pixel-level behavior has not yet been
reverse-engineered. They remain visible so you know when an older photo
contains one of them.

**Linear Blur** previously had no visible effect on most photos; it now
works. It keeps one side sharp and blurs the other, with a transition
between them. The strength depends on where the handle is positioned
horizontally. Moving it only up and down along the center line does
not apply blur. The original Picasa behaved the same way.

## Drag the focus point on the photo

For effects centered on a point - **Soft Focus**, **Focal B&W**,
**Graduated Tint**, **Radial Tint**, **Focal Zoom**, and **Focal
Pixelate** - you can also drag the center of the effect on the photo.
While the effect's slider panel is open, a white-ring marker shows the
focus point and the pointer becomes a crosshair. Click or drag with the
left mouse button to move the center. The marker jumps to that point,
and the **Center X** and **Center Y** sliders follow it.

For **Graduated Tint**, the marker also has a short line showing the
gradient direction. It turns slightly as the point moves horizontally.

## Sliders that scale with the photo

The upper limit of five sliders is based on the photo's dimensions
rather than a fixed number:

- **Focal Pixelate** ▸ **Radius**
- **Focal Zoom** ▸ **Focal Size**
- **Rounded Edges** ▸ **Corner Radius**
- **Border** ▸ **Corner Radius** and **Caption Height**

These sliders display pixel values, but the value saved to `.picasa.ini`
is a percentage of the range, as in the original Picasa. This makes
the same setting look proportional on large and small photos.

As a result, values saved in an older PicasaPy version as pixel
counts are now read as percentages, so a few photos may look different.
Move the slider again to correct the appearance. Edits
created in the original Picasa continue to display correctly.

## Four effects that work on the whole image without a brush

**Boost**, **Pixelate**, **Soften**, and **Tint** work without a brush:
in the editor, in the thumbnail, and during export, they affect the
whole photo. One older eye effect can be painted. Its brush control
appears only on photos whose saved settings already include that effect,
for example a photo edited in Picasa. See [The editor](szerkeszto.md)
for details.

## Hidden pairs: the Shift key

Ten tiles switch to a different effect when you hold Shift while
switching to the relevant tab. Their labels and previews also change,
so you can see the alternative. The original Picasa behaved the same
way.

| Tab | Tile by default | With Shift |
|---|---|---|
| Effects | Sharpen | Sharpen (Old) |
| Effects | Film Grain | Film Grain (Old) |
| Effects | Tint | Tint (Old) |
| Effects | Glow | Glow (Old) |
| Effects | Graduated Tint | Radial Tint |
| Creative | Heat Map | Night Vision |
| Artistic | Vignette | Matte |
| Artistic | Border | Rounded Edges |
| Artistic | Pixelate | Focal Pixelate |
| Additional effects | Film Grain | Film Grain (Old) |

**Glow (Old)** opens a slider panel like other effects; adjust it with
**Intensity** and **Radius**.

**Focal Pixelate** pixelates only the area around a point, leaving a
spot in the photo sharp and gradually pixelating outward. Selecting it
opens its own slider panel:

- Drag the on-image disc to choose the area that stays sharp.
- **Impact** controls pixel size.
- **Radius** controls the size of the sharp area.
- **Edge Hardness** controls how sharply the image changes from sharp
  to pixelated.
- **Fade** controls how much of the original photo shows through.
- **Reverse** swaps the areas: inside the circle becomes pixelated and
  outside remains sharp.

The change is immediate: while you are on an effects tab, hold Shift
to switch the labels on the ten tiles; release it to restore the
defaults.

The tile previews change too. While Shift is held they show the
alternative effects, and when you release it they return to the default
previews.

Shift has no effect on the other tiles.

## Apply effects to several photos

You can apply some effects to several photos at once from **Picture** ▸
**Batch Edit**. See [Batch editing](csoportos-szerkesztes.md).
