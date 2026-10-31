# Options, language, and appearance

## The Options dialog

Open it from **Tools** ▸ **Options**. It has nine tabs: **General**,
**E-Mail**, **File Types**, **Slideshow**, **Print**, **Network**,
**Web Albums**, **Name Tags**, and **Google Photos**. The first eight are
from the original Picasa; the Google Photos tab is a PicasaPy addition.

Seven tabs have working controls: General, E-Mail, File Types, Slideshow,
Print, Name Tags, and Google Photos. On the Network tab, only logging works;
the proxy controls are disabled. The Web Albums tab does not work because
Picasa Web Albums has been discontinued; it remains to match the original
Picasa layout. The anonymous-usage-statistics and automatic-update controls
on the General tab are disabled as well.

Two buttons appear at the bottom of the dialog, as in Picasa:

- **OK** (or `Enter`) saves changes made on the tabs and closes the dialog.
- **Cancel** (or `Esc`, or closing the window) discards the changes and
  leaves each setting as it was before you opened the dialog.

Settings therefore take effect only after you choose **OK**. **Cancel**
also discards changes to the cache-cleanup checkbox on the General tab.
Changing the interface language is not immediate, even after you choose
**OK**; see below.

If you make the window narrow, the tabs remain readable: the tab strip can
be scrolled horizontally with the `‹` and `›` arrows at its edges. The
selected tab scrolls into view automatically. The Google Photos tab may
also extend beyond the default window width; use `›` to reach it.

The dialog's labels, including disabled controls, use the original Picasa
wording. Some labels may not describe the behavior you expect from the
feature.

### General tab

**User interface:**

- **Use special effects** enables interface animations, such as the editor
  drawer sliding open and buttons pulsing. When it is off, changes happen
  immediately without animation. It is on by default.
- **Show tooltips** controls the small help labels that appear when you
  point to buttons and controls. It is on by default.
- **Single-click to exit Edit View** lets one click return to the library
  from the enlarged view, for both photos and videos. By default, you need
  to double-click. This option is off by default. Dragging a zoomed photo
  still moves it.

**Files:** the **Detect duplicates while importing** checkbox, the
**Delete from disk without confirmation** option, the
**Remove from album without confirmation** option, and **Clear cache files**;
see the sections below.

**Language:** see the next section.

**Import destination folder:** the default folder for imported photos. It
is your Pictures folder by default. Choose **Browse...** to select another
folder; that folder is then used when you open the Import window. See
[Import](importalas.md).

The privacy link opens Google's privacy page in your browser.

### Language

Choose the interface language with the language selector on the General
tab. The same choice is available from the Tools menu.

The first item in the list is **System Default**, followed by the language
configured on your computer in parentheses. If you choose it, PicasaPy
checks the system language each time it starts. Below it are 41 available
languages, each written in its own language (for example, English (US),
Magyar, and Deutsch). The interface is fully translated in all 41
languages, including PicasaPy's own labels. Standard dialog buttons such as
OK and Cancel also use the selected interface language rather than the
system language.

On first launch, PicasaPy offers to use your system language if it is not
English and is supported. A question with the program icon asks whether to
switch from English to the available system language. The question is in
English, as it was in the original Picasa. Choose **Yes** to start in the
system language and use System Default, so PicasaPy will follow any later
change to the computer's language. Choose **No** to keep the interface in
English. The question appears only once; you can change the language later.

After the first launch, a language change is not immediate. When you select
a language in Options or from the Tools menu, PicasaPy asks whether to
change the interface language and explains that the change will take
effect the next time the application starts. If you confirm, the choice is
saved (in the dialog, only after you choose **OK**) and takes effect on the
next launch. If you decline or choose **Cancel**, nothing changes. The
original Picasa behaves the same way.

The selector and menu checkmark show the requested language. After you
confirm a change, they therefore show the language that will be loaded next
time, even though it is not active yet.

### Confirming deletion

When **Delete from disk without confirmation** is enabled, PicasaPy no
longer asks before deleting a file. You can also change this in the delete
confirmation dialog with the **Don't ask again, always remove** checkbox.

### Detecting duplicates during import

When **Detect duplicates while importing** is enabled, PicasaPy skips photos
that are already in your library. It is enabled by default, as in the
original Picasa, and the application remembers if you turn it off. The
same setting appears as **Exclude Duplicates** in the Import window. Both
controls show the same value, so a change in either place appears in the
other.

### Clearing cached files

The **Clear cache files** checkbox on the General tab controls whether
PicasaPy removes cached thumbnails from disk when it exits. It is off by
default. A change remains a draft in the Options dialog until you choose
**OK**; **Cancel** discards it. There is no immediate cleanup: the cache is
cleared only when you close the application.

No photos are lost; thumbnails are rebuilt as needed. Folders may open more
slowly after the next launch until their thumbnails have been rebuilt.

### File Types tab

Under **Display JPEG files and:**, check the formats that the library
should include alongside JPEG: **.BMP**, **.GIF**, **.PNG**, **.TGA**,
**.TIF, .TIFF**, **.WEBP**, **.PSD (Photoshop)**, **RAW formats**,
**Movies (.AVI, .MPG, .ASF, .WMV)**, and **Quicktime Movies (.MOV)**. The
Movies label lists the four original Picasa formats, but PicasaPy also
includes other recognized video formats such as `.MP4`, `.M4V`, `.3GP`,
and `.MKV` in that category. Only `.MOV` belongs to the separate Quicktime
category. The **Supported Formats** link beside RAW formats lists the RAW
file extensions PicasaPy recognizes. JPEG is always included.

All formats are enabled by default, including GIF, PNG, and TGA. The
original Picasa disabled those three by default; PicasaPy does not, so an
update will not make existing photos disappear. If you have already
changed a checkbox, PicasaPy keeps your choice. A format you disable is no
longer added to the library the next time the folders are scanned; the
files remain on disk.

### Slideshow tab

- **Loop slideshow** starts the slideshow over when it reaches the end. It
  is off by default.
- **Play music tracks during slideshow** is on by default. Use
  **Browse...** beside **Select a folder of music tracks:** to choose a
  folder of music. The field is available only while music playback is
  enabled. If the open folder has its own music in its description, the
  slideshow uses it; see [Folder Manager](mappakezelo.md).

### Print tab

- **Available print sizes:** five lists set the five shortcuts below the
  size list in the Print window. The sixth button, **FullPage**, is fixed
  and does not appear in these lists. Defaults depend on your computer's
  regional settings. Metric defaults are 10 × 15, 13 × 18, 15 × 20, and
  20 × 25 cm, followed by Contact Sheet. Inch-based defaults are Wallet
  Size, 3.5 × 5, 4 × 6, 5 × 7, and 8 × 10. Your choices are saved.
- **Previews:** **Use high quality previews (slower)** makes print previews
  more accurate but takes longer.
- **Printer quality:** choose **Compatible (half-res)** (the default) or
  **High Quality (full-res)**. This setting applies when the Print window
  uses Normal mode. Optimized mode always prints at full resolution.
- **Print resampler quality:** choose **General (Lanczos-3)** (the default)
  or **Extra sharp (Lanczos-8)**. This is the filter used to resize the
  image for printing.

See [Printing](nyomtatas.md) for details about the print sizes.

### Network tab

PicasaPy does not use a proxy, so the **Proxy username:**,
**Proxy password:**, and **Automatically detect network settings** controls
are disabled and are not needed.

Logging is available. Choose one of five levels from **Network log level:**

- **Disable Logging** - no log is written.
- **Log errors only** - only failed downloads are recorded.
- **Minimal log information** (the default) - one short line per download.
- **Detailed log information** - also records details of the response and
  any redirects.
- **Log all network information** - also records the size of downloaded
  data.

The selected level is saved for the next launch. The **Log:** field shows
where the log is stored: in a file named `network.log` in the application
data folder. The location cannot be changed; the field is read-only, but
you can copy its text.

PicasaPy currently downloads only one item from the network: the face
recognition model, if it is missing from the installation. The log only
grows in that case, so check it if the download fails. See
[People and faces](emberek.md).

### Name Tags tab

- **Enable face detection** searches new photos for faces automatically in
  the background. It is on by default. Turning it off stops an automatic
  search that is running. See [People](emberek.md).
- **Enable suggestions:** lets PicasaPy suggest names for unnamed faces and
  group faces automatically after a search. It is on by default. Two
  sliders below it are available only when suggestions are enabled:
  - **Suggestion threshold:** a higher value requires a closer match before
    PicasaPy suggests a name.
  - **Clustering threshold:** a higher value applies a stricter rule when
    grouping faces.
  Both sliders range from 50 to 95 in steps of five and default to 85, as
  they do in the original Picasa. If you had already changed the clustering
  threshold, grouping continues to behave as before, even if the slider
  now displays a different number.
- **Store name tags in photo** writes face information to an XMP sidecar
  file beside the photo when you name a face. It is on by default.

The option to upload People album thumbnails to Google Contacts refers to
a discontinued service and is not part of the current interface.

### Google Photos tab

Enter your Google client details here and sign in to Google Photos so you
can upload the contents of the Photo Tray. See
[Upload to Google Photos](google-fotok.md).

## Configuring the Photo Viewer

**Tools** ▸ **Configure Photo Viewer...** opens a small window with two
checkboxes:

- **Fullscreen startup (requires restart of Photo Viewer to take effect)**
  is checked by default, and the choice is saved. The note in parentheses
  is misleading: you do not need to restart the application. The setting
  takes effect the next time you open the viewer. It applies only to the
  simplified viewer (the Photo Viewer), that is, when you open a picture
  file from outside the program: when checked, it opens full screen; when
  unchecked, it opens in a window. A picture opened from the library always
  stays in the program window, whatever the setting. Press `F11` in the viewer to
  switch between full screen and windowed mode. See
  [Viewing photos](nezegetes.md).
- **Use Color Management** is the same setting as the one under the View
  menu. Changing either control updates the other.

## Dark appearance

PicasaPy includes a dark appearance option that can be turned on or off.
Your choice is saved for the next launch.

## Display mode

The Display Mode submenu under View adjusts the picture for your screen:

- **Automatic**, **24-bit**, or **16-bit (dithered)** color depth. The
  16-bit option shows the image as it would appear on a 16-bit display,
  with consistent fine dithering in color gradients. See
  [Viewing photos](nezegetes.md).
- **LCD Whitepoint**.
- **Projector Mode**.
- A mode for showing overexposed pixels.
- **Mac Gamma (1.6)** or a linear gamma of 2.2.
- **Sepia** or **B&W**, which applies to the whole interface.

These modes change only what you see on screen; they do not modify your
files. The selected mode applies wherever a photo appears: thumbnails, the
viewer, and slideshows.

Like the original Picasa, PicasaPy also applies the mode to the interface
itself. Menus, bars, and backgrounds use the same mode as the photos, so
B&W or Sepia changes the program's appearance as well as the image.

## Use Color Management

The **Use Color Management** setting controls whether PicasaPy uses the
color profile embedded in a photo.

Many cameras and photo editors record the color space they used, such as
Adobe RGB instead of sRGB. If an application ignores the profile, the
photo may look washed out or too vivid. When color management is enabled,
PicasaPy converts the image for your display using that profile.

- It is off by default, and your choice is saved for the next launch.
- Its effect is visible in the viewer and editor. It does not change the
  image file or an exported copy.
- Nothing changes if the image has no profile or already uses sRGB, as is
  the case for most camera JPEGs.
- The image is rebuilt immediately after you change the setting.

## Settings that are remembered

PicasaPy saves these choices and restores them the next time it starts:

- window size and position, including whether it was maximized;
- the width of the left pane;
- the dark appearance and **Use Color Management** settings;
- the requested language, which takes effect on the next launch;
- folder and left-pane sorting;
- the thumbnail caption mode and caption bar state;
- the left pane's three view controls: its folder-view mode,
  **Simplified Tree View**, and **Show Thumbnails in Library**;
- whether hidden photos are shown;
- the most recently opened folder;
- quick tags and custom aspect ratios.

Thumbnail size is not saved, so you need to set it again each time you
start the application.

## About PicasaPy

The About entry under Help shows the exact program version. Include it when
you report a problem.

## Performance and diagnostic information

PicasaPy includes a small panel that shows processor and memory usage. Its
diagnostics control can save information about what the application is
doing to a file.

## Startup test mode

PicasaPy can write a detailed log on the next launch, including how long
each startup step takes. This can help diagnose a slow start. While the
mode is active, a notice in the menu bar says that startup logging is in
progress.

The log-sharing command is available only while this mode is active. It
opens a save dialog so you choose where the file goes; the suggested name
includes a timestamp. PicasaPy remembers the folder for next time and also
copies the saved file's path to the clipboard, ready to paste into a
message.

Previously, the log was written to a fixed network folder that most
computers could not access.

You can also enable startup test mode for one run with the `--tesztuzem`
command-line option:

```bash
./picasapy --tesztuzem ~/Pictures
```

## Customizing the header buttons

**Tools** ▸ **Configure Buttons...** controls which buttons appear in the
header above the photos and their order. The same window opens if you
right-click the output button row in the Photo Tray and choose
**Configure Buttons...**.

The dialog has two lists, **Available buttons:** and **Current buttons:**.
Use **Add >>** and **<< Remove** to move buttons between them, then use
**Move Up** and **Move Down** to change their order.

You can arrange four buttons this way: **Play Fullscreen Slideshow**,
**Select starred photos**, **Save edited photos to disk**, and
**Create Photo Collage**.

**Reset to Defaults** restores the original order. **Cancel** discards your
changes. The setting is saved for the next launch.
