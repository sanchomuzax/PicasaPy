# Upload to Google Photos

Use the green button on the photo tray to upload the photos there to
your Google Photos library.

This is the only working upload path. Similar-looking items in the
menus, such as the upload command under **Tools**, are still
unavailable; see [Features not yet available](meg-nem-erheto-el.md).

## Sign in

Click **Sign in with Google Account** at the right side of the menu bar.
A browser opens. Sign in there and grant access. After sign-in, the menu
bar shows your account status. Click it to open the menu and sign out.

If the PicasaPy package does not include a built-in Google client,
clicking the link shows a short message: **Google sign-in is not available
in this version yet.** Click OK to close it. The sign-in button on the
**Google Photos** tab of **Options** uses the same built-in client.

The tab also shows **Privacy Policy** and **Terms of Service** links, which
open in your browser.

## Advanced: use your own Google client

Most people do not need to configure a Google client. If you need your
own, open the **Google Photos** tab of **Options** and expand **Advanced: use your
own Google client (optional)**. Enter the OAuth client ID and client
secret, then choose **Save**. Start sign-in from the tab or the menu bar.

For your own client, create an OAuth client of the desktop app type
in the Google developer console and enable Google Photos upload. Google
provides the two values. The built-in PicasaPy client needs no user setup
in packaged builds. When running from source, set
`PICASAPY_GOOGLE_CLIENT_ID` and `PICASAPY_GOOGLE_CLIENT_SECRET` to use it.

PicasaPy stores your client secret and sign-in in the system keyring
when available, or otherwise in your user settings. If you change only
the client ID, leave the secret field blank to keep the saved secret.
For a new client ID, enter the new secret and sign in again.

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
