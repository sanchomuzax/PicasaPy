# Viewing photos and videos

## The single-photo viewer

Double-click a photo in the grid to open it in the viewer. You can also
choose **View** ▸ **View and Edit** (Ctrl+3), or **Picture** ▸ **View and
Edit**. Return to the library with **Return to organized thumbnails** or
Esc. The button's tooltip explains where it goes.

Enter also returns to the library when one still picture is open and no
editing tool is active. If single-click exit is enabled, or you are
viewing a video or two photos side by side, Enter advances to the next
photo instead.

On the **General** tab in **Settings**, enable the option to exit the
editing view with one click to return to the library by clicking a still
photo once. PicasaPy waits for the double-click interval first. A
double-click also exits, including on Windows, without reopening the
viewer. This does not apply to side-by-side photos or while Straighten
is open. When zoomed in, dragging still pans the picture. In a video,
pressing the picture area exits immediately when this option is enabled;
otherwise a double-click exits.

At the bottom and edges of the viewer:

- **Previous Photo** and **Next Photo** move through the folder. Hold a
  button to keep moving; release it to stop. Moving stops at the end of
  the folder. Ctrl+F9 starts continuous advance: the viewer moves on as
  each photo loads until it reaches the end. Manual navigation or
  closing the viewer stops it.
- A filmstrip between the navigation buttons shows nearby pictures.
- The viewer has a button to start a slideshow.
- **Show Faces** (F) and **Edit Faces** (Shift+F) show or change detected
  face boxes.
- **Straighten**, **Undo**, and **Redo** are quick editing controls.
- A small pale square in the lower-left corner toggles the caption bar
  (see [Captions](csillag-felirat-cimke.md)). The square remains visible
  when the bar is hidden, so you can turn it back on.

### Full screen: F11

F11 switches the viewer to full screen; press it again to restore the
previous window size. It affects the open viewer only. A slideshow
controls its own full-screen state.

To open the viewer in full screen automatically, use the full-screen
startup option in **Configure Photo Viewer...** (see
[Settings](beallitasok.md)).

### The filmstrip

The strip at the bottom of the viewer shows small pictures from the
folder between the navigation buttons. It always reserves space for
seven pictures, even in a smaller folder. The current picture stays in
the center while the strip moves; empty positions appear at the folder's
ends. A two-color frame marks the current thumbnail. You cannot drag
the strip; click a thumbnail to open that picture.

Ctrl+Delete deletes the current picture from disk, after confirmation.
When you opened it from an album or People album, this removes it from
that album instead and leaves the file in place. The context-menu
command then reads **Remove from Album**.

Choose **View** ▸ **Library View** to return to the library. This command
is disabled while already in the library.

### Menus in the viewer

While the viewer is open, commands in the File, Edit, and Picture menus
act on the one picture currently displayed. This includes saving,
exporting, renaming, deleting, hiding, rotating, applying batch-edit
effects, copying or pasting effects, and resetting faces. The commands
remain available and do not affect the selection left in the grid. If
you hide the picture, the grid selection remains.

After saving or reverting, the viewer displays the updated picture from
disk. Right-click the picture to access the same commands as in the
grid, including rotate, save, revert, hide, locate on disk, properties,
and delete from disk.

## Open a picture from the file manager

If you start PicasaPy with a picture file, such as with the file
manager's Open with command or by giving the filename at startup (see
[Getting started](../getting-started.md)), PicasaPy opens a simplified
viewer instead of loading the library, much like the original Picasa
Photo Viewer. The full-screen startup option in Settings applies here
too.

The viewer displays only the files you specified. If you supplied
several, including files from different folders, use the arrows to move
between them. The filmstrip and side panels for Properties, Tags,
Places, and People are hidden. A separate toolbar at the bottom
provides:

- **Zoom In**, **Zoom Out**, and **Zoom to 1:1**;
- **Edit in PicasaPy**, which closes this viewer and starts the full
  application with your library;
- **Previous Photo**, **Play Slideshow**, and **Next Photo**;
- **Rotate Counterclockwise**, **Rotate Clockwise**, and **Star**. A
  starred photo shows its star in the viewer; the Star button toggles
  the mark;
- a button that opens the picture's context menu.

**Quick Upload** is disabled because Picasa's online services have been
discontinued. Close the simplified viewer, for example with Esc, to
continue in the normal library view.

## Compare two photos side by side

Three view controls beside the playback button at the bottom of the
viewer choose how many pictures to show:

| Control | What it does |
|---|---|
| **Show only one picture** | The normal single-photo view. |
| **Show two different pictures** | Two different photos side by side for comparison. |
| **Show the same picture twice** | Two independent edits of one photo, shown together. |

In the two-different-photo view, the earlier photo is on the left and
the next photo in filmstrip order is on the right (or the previous one
if there is no next photo). The left side is selected; in a vertical
layout, the top is selected. Both photos show their saved edits, just as
they do in the grid.

Two more controls appear:

- **Switch focus between the pictures** selects the active side. Its
  upper corner displays **Selected**.
- **Switch between horizontal and vertical layout** places the photos
  side by side or one above the other.

The selected side determines where commands apply. Editing effects,
undo, saving, zoom, face boxes, and editor tools such as crop, retouch,
text, and red-eye work on that photo. The blue information bar also
describes the selected photo. Navigation, captions, mirroring, and
Ctrl+Delete affect the selected side only; the other photo stays in
place. Both photos are highlighted in the filmstrip. Click a thumbnail
to replace the active side's photo, or click the other photo to switch
focus.

### Two edits of one photo

This mode begins with the same current photo on both sides. Edit one,
switch focus, and try a different edit on the other. The edits remain
independent and are kept in memory until you choose which version to
save to disk.

When you switch focus, unfinished work stays with its side. Painting an
effect with a brush, for example, remains available when you return to
that side. Switching focus closes any open tool: crop, straighten,
retouch, red-eye, or text.

### Confirming an open editing tool

If you have made changes in an editing tool, PicasaPy asks before
discarding them. The confirmation dialog lets you apply the changes as
if you had chosen **Apply**, or discard them. You can also choose not to
be asked again and always apply changes.

This can happen when entering a side-by-side mode or switching focus.
When switching focus, **Cancel** is also available; it leaves the tool
open and keeps the current side selected. Straighten closes without a
prompt.

### Leave side-by-side mode

If the two sides have different edits, PicasaPy asks which version to
keep when you leave this mode, navigate to another photo, exit the
viewer, or close the application. In a horizontal layout, choose Left
or Right; in a vertical layout, choose Top or Bottom. Enter confirms
the selected side. **Cancel** returns to the comparison with both
versions intact. If only one side was edited, or both sides ended up
the same, PicasaPy keeps the edited version without asking. Videos
cannot be compared in this mode.

## Zoom in the viewer

The zoom controls are on the bottom toolbar, before the panel buttons:
**Fit Photo inside viewing area**, **Display Photo at actual size**, and
a zoom slider between them and beyond. The slider's center is exactly
100% (1:1); the right end is 4×. It snaps to actual size. You cannot
zoom out below the fitted view or in beyond 4×.

Drag a zoomed picture to pan it. Double-click to return to the fitted
view. If single-click exit is enabled, the double-click instead exits
the viewer. Zoom is unavailable for video and while cropping.

### Navigator

When zoomed beyond the fitted view, a small navigator appears in a
corner of the picture. It shows the whole picture, with a blue frame
around the visible area and the rest dimmed. The zoom level appears
below it. Drag the frame to move around the zoomed picture. Click the
× in the corner to hide the navigator. It appears again after you return
to the fitted view and zoom in once more.

Editing tools can also work while zoomed: the legacy eye-effect brush,
red-eye, retouch, text, and face marking follow the pointer over the
zoomed picture. If no tool is open, dragging pans. In the comparison
view, click the other picture to switch focus. Straighten's Apply and
Cancel controls and slider remain usable. Tools that affect the whole
picture start in the fitted view and leave it there when closed.

The viewer loads a picture at its actual dimensions and does not enlarge
small pictures first. This saves memory for small and tall phone photos
and helps avoid graphics-texture limits.

## Blue information bar

In the library, the blue bar describes the selection. In the viewer it
describes the current photo, or the selected side in comparison mode:
folder and filename, date, pixel dimensions, file size, position in the
folder, and tags.

If the text does not fit, the folder name is first removed from the
filename. If that is not enough, the middle of the filename is replaced
by an ellipsis; its start and end, including the extension, remain
visible. Other information is not shortened.

## Slideshow

Start a slideshow from **View** ▸ **Slideshow**, **Folder** ▸ **View
Slideshow**, the viewer's slideshow button, or Ctrl+4. It fills the
entire application window. The menu bar, toolbar, and photo tray hide
until you exit.

| Key | Action |
|---|---|
| Space | Pause or resume |
| Right arrow or Enter | Next photo |
| Left arrow | Previous photo |
| Ctrl+R | Rotate clockwise |
| Ctrl+Shift+R | Rotate counterclockwise |
| Esc | Exit |

When you exit, the grid and viewer return to the photo where the
slideshow stopped. The slideshow follows changes to the photo list. If
the current photo is removed, it advances to the next one, wrapping to
the start at the end. If the order changes, it keeps the current photo
and continues from there. An empty list stops the slideshow.

### Slideshow controls

Move the pointer to show the control bar at the bottom. It hides after a
few seconds; while the pointer is over it, it stays visible. The bar
provides Exit, previous, play/pause, next, and rotate controls. Previous
and next respond once on press and do not repeat when held. Rotations
made during the slideshow are saved.

Depending on the display's color depth and how the slideshow started,
the bar shows either a Timeline button or a transition selector. A
caption-mode control cycles between the caption, filename, and no text.
A Star control toggles the photo's star. Use minus and plus to set the
display time from 1 to 20 seconds; holding either button repeats the
change. The transition, caption mode, and display time are remembered
for the next slideshow and until the application is restarted.

Click the narrow strip at the top of the displayed photo to pause or
resume. It does not cover or hide the picture.

### Transitions

The selector offers Picasa's seven slideshow transitions, in order:
Cut, Pan and Zoom, Dissolve, Wipe, Circle, Push, and Rectangle. Pan and
Zoom moves within a photo for the slide duration rather than between
photos. It pans between two randomly chosen crops, so it does not
always zoom toward the center.

If a saved transition is no longer available, the slideshow uses
Dissolve. Other transitions, such as the face-zoom effect, are available
in the [Movie](mozgofilm.md) editor.

## Timeline

Choose **View** ▸ **Timeline** (Ctrl+5) to see an animated, full-screen
overview of your library. Each folder and album with pictures is a card
with stacked-photo imagery, its name, and a month and year, such as
July 2024. Cards are ordered by the oldest capture date in each folder
or album. Items with no capture dates appear at the end without a date;
empty albums and hidden photos do not appear. Timeline always opens at
the first card.

Use the left and right arrows or the bar's arrow buttons to move between
cards. Drag the bottom slider to move farther through time; the first
and last library dates appear at its ends. Press Space or the play
button to start a slideshow of the current folder or album. Press Esc
or use the close button to exit. On return, the library opens the last
folder or album shown, with its first photo selected.

## Display mode

The display mode selected from **View** applies to thumbnails, the
viewer (both photos in comparison mode), and the slideshow. Projector
mode therefore applies wherever it is most useful. See
[Settings](beallitasok.md) for the mode list.

The 16-bit dithered mode simulates a 16-bit color display by adding a
fine dither to smooth gradients. It looks consistent for the same
picture and affects only the displayed picture, not the interface or
your files. Automatic and 24-bit modes do not dither.

## Videos

Video files appear in the grid like photos and play in the viewer. Qt
Multimedia is required for playback; without it, PicasaPy continues to
run and displays a message in place of the player. Use the toolbar
filter to show only videos. Opening a video in the viewer starts it
automatically, as in the original Picasa.

### Video controls

Two rows appear below the video. The upper trim bar has Start Point and
End Point handles. The lower row has playback, a seek slider, trim
buttons, two view-mode buttons, elapsed time, and volume. The volume
setting is remembered until the next application start.

- The 1:1 control shows the video at its actual size without stretching,
  centered and cropped if it does not fit. Press again to return to the
  fitted view.
- **Play full screen** switches the application window to full screen;
  press again to restore its previous size.

### Video panel

When a video is open, the left editor panel shows a video panel instead
of photo-editing tabs. It has three commands:

- **Reset Start and End** clears the trim and restores the full video.
  It is disabled if there is no trim. PicasaPy asks whether to remove
  all movie edits; choose Remove edits to clear the trim points.
- **Take Snapshot** saves the currently displayed frame (see below).
- **Export Clip** is available only for a trimmed video.

### Trim a video

Use the two trim buttons to set the start and end at the current frame,
or drag the handles on the trim bar. Playback then stays within the
selected section: it seeks to the start, stops at the end, and the seek
slider moves only within that range.

On Windows and macOS, Export Clip saves the trimmed section as a new
MP4 in the exported-video-clips folder under `Pictures/Picasa`. It adds
a number if a file with that name already exists and does not overwrite
it. If export fails, PicasaPy reports the error. The original video is
unchanged. On Linux, saving a clip to a file is not supported, but the
trim remains and playback still uses the selected section.

Trim points are stored in the folder's `.picasa.ini` in the same format
as the original Picasa. Both applications therefore see the same trim;
existing Picasa data is preserved.

### Save a frame from a video

Choose **Take Snapshot** to save the current frame as a JPEG in the
captured-video-clips folder under `Pictures/Picasa`, using the video
filename. If that name already exists, PicasaPy adds `-001`, `-002`,
and so on.

The frame uses the video's original resolution and JPEG quality 85,
not the size currently shown on screen. PicasaPy reports progress and
whether the save succeeded. If the folder did not exist, the program
creates it and marks it as one of its project folders, as the original
Picasa did.
