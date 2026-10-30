# Passport photo

Passport Photo crops a face from a picture to an identification-photo
size, then opens the print dialog. It does not change the original
picture: the crop is written to a separate temporary file, and the
photo library is left unchanged.

## Use it

1. Select one picture containing exactly one face.
2. In PicasaPy's experimental tools menu, choose **Passport photo...**.
3. PicasaPy finds the face, crops the picture, and opens it in the
   [Print](nyomtatas.md) dialog.

If several pictures are selected, the command uses the first one. It is
disabled when nothing is selected.

Face detection runs in the background, so the application remains
usable while a large picture is processed.

## How the crop works

The crop is square and centered horizontally on the face. It leaves
headroom equal to one third of the face height and includes space for
the shoulders equal to six tenths of the face height. Near an edge, the
crop extends only as far as the picture boundary, so it may not be a
perfect square. The original Picasa behaves the same way.

If you rotated the picture in PicasaPy, the crop uses the rotated view,
as shown in the viewer.

## Passport print settings

The print dialog opens with these settings:

- **Print size:** is **Passport**, a 2 × 2 inch (about 5 × 5 cm) print.
  Passport is also available in the print-size list, but choosing it
  there does not crop a face; only this command creates a face crop.
- **Fit to page:** is set to **Fill the page (crop)**.
- The current number of copies per picture is kept. For a new print job
  the default is one.

The page holds as many passport photos as fit, arranged in a grid.

These temporary settings do not replace your usual print settings. The
next standard print dialog restores the previous fit, copy count, and
remembered print size.

## If it does not work

| Message | Meaning |
|---|---|
| **Can't find any faces** | PicasaPy did not find exactly one face; it found none or more than one. |
| **The picture could not be read.** | The picture file could not be opened. |
| **The cropped picture could not be saved.** | The crop could not be written to the temporary file. |

For a picture with several faces, the original Picasa also uses the same
message and has no separate one. The dialog asks **Try another picture?**
Choose a picture with one clearly visible face. Choose **OK** to close
the dialog; the original picture is unchanged.

If PicasaPy cannot find a face that you can see, adding a face with the
[viewer face-box editor](emberek.md) does not help: Passport Photo always
detects the face itself.
