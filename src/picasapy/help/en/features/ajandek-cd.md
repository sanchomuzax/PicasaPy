# Create a Gift CD...

**Create** ▸ **Create a Gift CD...** is the original Picasa feature for making a
gift disc. Collect photos in the Photo Tray, give the disc a name, choose an
image size, and PicasaPy packages them into one file that you can burn to a
disc.

PicasaPy does not burn discs. It creates an ISO image file (`.iso`) that you
can burn with any disc-writing application or mount and view directly. This
is the only difference from the original: your system's disc-writing
application handles the burning.

## Photos come from the Photo Tray

Gift CD uses the items in the Photo Tray, not the selection in the grid,
just like collage and movie creation. First collect the photos in the tray.
You can add photos from several folders with **Hold selected items**; then
open the Gift CD feature. The panel explains that checked items will be
copied to the gift CD.

With an empty tray, **Burn Disc** is disabled because there is nothing to
include.

## The panel

The panel opens at the bottom of the library and has two steps. The same
panel is used to [back up photos](biztonsagi-mentes.md), so the two tasks
cannot be open at the same time. Opening the backup panel closes the Gift CD
panel, but the Photo Tray contents are kept.

### Selection and settings

- **Add More...** returns to the library so you can add items to the tray.
  Items already collected remain there.
- **Photo Size** sets the length of the photo's longer side on the disc:
  Original Size, 640x480, 800x600, or 1600x1200. Smaller sizes let you fit
  more photos on a disc and open them faster on the recipient's computer.

### Name the Gift CD

- **CD Name** becomes the disc's name and can contain up to 16 characters.
  The field prevents longer names. If you leave it empty, the file name is
  also used as the disc name.

On the right, **Burn Disc** starts the operation. **Cancel** returns to the
library, like Add More...; neither action clears the Photo Tray.

## Creating the disc image

When you choose **Burn Disc**, PicasaPy first asks where to save the file.
The dialog opens in your Pictures folder and offers ISO files. You do not
need to enter the extension; PicasaPy adds `.iso` to the file name.

The work then runs in the background. Resizing and assembling the image can
take several minutes when the tray contains many photos. While it runs, you
cannot start another burn.

When it finishes, the **CD Done** window shows the path to the completed
file:

- **Show CD** opens the file's location in your file manager.
- **Close** closes the window.

If some photos could not be included, the window reports how many. The
other files are still added; one damaged file does not stop the whole
operation.

If no photo could be added, PicasaPy reports that the disc image could not
be created.

## What is included

- All photos are placed in one folder named `Pictures`.
- Photos are saved as JPEGs with your edits applied. Cropping, rotation,
  and effects appear as they do in the grid. Other image formats are
  converted to JPEG.
- Movies are copied without modification.

The disc does not contain:

- `.picasa.ini` files, so captions and tags are not included. The gift CD
  contains the photos, not your database.
- A web page or slideshow application.
- PicasaPy itself. The original Picasa could add its installer to the disc;
  PicasaPy does not have that option.

## Related topics

- [The library and Photo Tray](konyvtar.md)
- [Exporting to a folder](exportalas.md) - for copying out files only
- [Backing up photos](biztonsagi-mentes.md) - for making an archive
