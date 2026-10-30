# Exporting photos

Export creates new files in another folder, including the edits you
made. It leaves your original photos untouched.

## Export to a folder

Start with **File** ▸ **Export Picture to Folder...** (`Ctrl+Shift+S`) or
the **Export** button in the photo tray.

You can choose the destination folder and resize the photos by setting
the pixel length of the longer side. You can keep the **Original Size**
or choose a smaller size. A note beside the slider describes the
expected file size and quality.

For image quality, choose **Auto**, **Normal**, **Maximum**, or
**Minimum**, or set a custom value with the slider. Maximum writes a
JPEG with full color resolution (4:4:4); Auto preserves the source
JPEG's color subsampling. For movies, choose **First frame** to export
the first frame as an image, or **Full movie (no resizing)**.

You can also add a watermark with your name, a web address, or a
copyright notice. To preserve the order when the destination folder is
sorted by name, add numbers to the file names.

PicasaPy updates the exported image metadata: its modification time
becomes the export time, its dimensions reflect the output size, and
missing author and capture-time fields are filled in. Camera metadata
is preserved. For JPEGs larger than 300 pixels, PicasaPy also writes an
embedded preview, as the original Picasa did. If the metadata is too
large to fit with that preview, EXIF camera data is omitted from the
exported file, also matching the original Picasa behavior.

If the destination folder already exists, PicasaPy asks before
overwriting it. At the end it reports how many photos were exported and
whether any failed. Exported folders remain available in the project
area of the left pane.

## Export as an HTML page

Create a web gallery with thumbnails that open the larger photo. Start
with **Folder** ▸ **Export as HTML Page...** or the folder's context
menu.

Choose a **Web page title:** and a destination **Folder:**. The
suggested first-use destination is `Picasa HTML Exports` inside your
user's Documents folder on Windows, and inside your photo folder on
other systems. It is only a suggestion: PicasaPy creates it after you
choose **Export**, and you can change it.

Choose one of the seven built-in templates (see below), then set the
size of the large photos: **Original Size**, **1024 pixels (for large
monitors)**, **800 pixels (for large Web pages)**, **640 pixels (for Web
pages)** (the default), or **320 pixels (for email)**. The template
controls the thumbnail size and any shadow.

For movies, choose **First frame** to place a still image on the page,
or **Full movie** to link from a thumbnail of the first frame to a copy
of the unchanged movie file. A movie that PicasaPy cannot read is left
out.

The size, movie option, destination, and selected template are
remembered until the next export. Choose **Export** to create the
files; the window reports how many it wrote and where. Choose
**Cancel** to close the window.

### The seven templates

The list shows seven templates in the same order and with the same names
as the original Picasa. Selecting one displays its description and a
small preview. The first three use a two-page layout: a thumbnail index
opens each large photo on its own page. The next three show thumbnails
in a scrollable strip on the left and the large photo on the right in a
single page. Their backgrounds are grey, black, and white; the first
three use plain tiles and the next three use framed tiles.

The final **XML Code** option is not a web gallery. It writes one
`album.xml` file with the album and photo data for another program to
process; it does not create a gallery that opens in a browser.

### Custom templates

You can use your own `.tpl` templates alongside the built-in ones. Put
each template in a separate subfolder under
`.local/share/picasapy/webexport/templates` in your user folder. Each
subfolder needs an `index.tpl` file; an optional `preview.svg` supplies
the small preview image.

Custom templates appear after the built-in ones the next time the
window opens. Their displayed name comes from the template header or,
if there is none, the subfolder name. If a custom subfolder has the same
name as a built-in template, the built-in one is used and the custom
one is hidden. The window adjusts to its contents so that **Export** is
visible at the default size.

## Publish via FTP

Choose **Tools** ▸ **Experimental** ▸ **Publish via FTP...** to upload a
web gallery to an FTP server instead of saving it on your computer. The
window is similar to the HTML export window. Choose an **FTP account:**
instead of a destination folder, and use **Manage...** beside it to
edit accounts. Set the **Page title:** and choose a **Template:** from
the drop-down list, which also shows a preview and description. Photo
size and movie options are the same as for HTML export.

### Add an FTP account

If you have not added an account, the account-management window opens
when you start publishing. Later, open it with **Manage...**. Enter an
**Account name:**, **FTP server:**, **Username:**, **Password:**, and
**Remote folder:**. PicasaPy creates the remote folder if it does not
exist.

Choose **New** for an empty form, **Delete** to remove the selected
account, **Save** to save it, or **Cancel** to close the window. When
editing an existing account, leave the password blank to keep the
stored one.

The password is stored in the computer's system keyring, not in
PicasaPy's own settings. If no keyring is available, PicasaPy reports
the problem and cannot save the account.

### Upload

Select an account and choose **Publish**. PicasaPy creates the gallery
and uploads its files to the account's remote folder. It reports the
number of uploaded files and the account used. Existing remote files
are not removed; files with matching names are overwritten. If an
upload fails, for example because the password is wrong or the server
cannot be reached, PicasaPy explains the problem.

> Uploads use traditional, unencrypted FTP on the standard port 21.
> The password and files travel across the network without encryption.
> FTPS and SFTP are not supported.

## Export face information to sidecar files

The face-information command in **Tools** ▸ **Experimental** writes
sidecar files beside photos in the current folder, containing the names
and locations of named faces for other photo managers. It does not
change the image files. See [People and faces](emberek.md).

## Google Earth

The Google Earth export command in **Tools** writes a file from photos
with location data that Google Earth can open. See
[Locations and geotags](helyek.md).
