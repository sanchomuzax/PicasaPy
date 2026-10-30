# Upload to Google Photos

Use the green button on the photo tray to upload the photos there to
your Google Photos library.

This is the only working upload path. Similar-looking items in the
menus, such as the upload command under **Tools**, are still
unavailable; see [Features not yet available](meg-nem-erheto-el.md).

## Before the first upload: create a Google client

The original Picasa uploaded through Google's own service, which has
been discontinued. PicasaPy therefore uses a Google client that you
create. In the Google developer console, create an OAuth client of the
desktop application type and enable Google Photos upload. Google will
give you a client ID and client secret. PicasaPy cannot perform this
setup for you.

Then open **Tools** ▸ **Options** in PicasaPy and enter the client ID
and secret in the Google Photos settings. Choose **Save**, then choose
**Sign in with Google Account**. A browser opens; sign in there and
grant access. When sign-in succeeds, the settings show that you are
connected.

The settings action and sign-in take effect immediately; you do not
need to choose **OK** in the Options window. PicasaPy stores the client
secret and sign-in in the system keyring when available, or otherwise
in your user settings. If you change only the client ID, leave the
secret field blank to keep the saved secret. For a new client ID, enter
the new secret and sign in again.

The sign-out action clears the saved sign-in. Sign in again before your
next upload.

### If sign-in fails

The settings show the reason. Common messages include:

- “Enter a valid OAuth client ID and client secret.” One of the fields
  is empty or invalid.
- “Could not open the system browser.” Set a default browser in your
  operating system.
- “Sign-in was cancelled.” or “Sign-in timed out. Try again.” The
  sign-in did not finish in the browser; try again.
- “Google sign-in failed. Check the OAuth client settings.” Check that
  the client is a desktop application and that Google Photos upload is
  enabled for it.

## Upload

1. Add the photos to the photo tray; see [The library](konyvtar.md).
2. Start the upload with the green tray button.

The button is disabled when you are not signed in, the tray is empty,
or an upload is already running.

PicasaPy uploads every photo in the tray, not only the photos selected
there. A small window shows progress, including which photo is being
prepared or uploaded. Use **Cancel** to stop. When the upload finishes,
the window reports completion and offers **Close**.

### What gets uploaded

- Photos go to your Google Photos library, not to an album. They are
  uploaded without captions and use their file names.
- If a photo's longer side is over 1600 pixels, PicasaPy resizes it to
  that length before uploading. Smaller photos are unchanged.
- PicasaPy uploads the file from disk. Save unsaved edits first if you
  want the edited version to be uploaded; choose **File** ▸ **Save**.

### If an upload fails

The window explains the reason and identifies the photo if one failed.
Common messages are:

- “Network error. Check your connection and try again.”
- “Your Google Photos sign-in has expired. Sign in again.” Sign in
  again in the Google Photos settings.
- “Maximum Upload Rate Exceeded.” Google has temporarily limited
  uploads; wait and try again later.
- “Google Photos is temporarily unavailable.” Try again later.
- “A photo could not be prepared for upload.” The file may be damaged
  or may not be an image.
- “This photo is too large to upload.”
- “There are no photos in the Photo Tray.”

## Related topics

- [The library and photo tray](konyvtar.md)
- [Settings](beallitasok.md)
- [Features not yet available](meg-nem-erheto-el.md)
