# Movies

A movie is a video made from selected photos. Each photo appears in
sequence for a set amount of time.

## Start a movie

Select photos, then start a new movie from the **Create** menu or use
the **Movie** button in the photo tray.

A movie-presentation command beside the collage control in a folder
header opens Movie Maker with every photo from that folder, not only
the selection. It is not shown in a People album, which has its own
movie controls.

Commands to create a movie from faces in the selection or from People
albums, and the movie buttons in a People album header, also open the
movie editor. See [People and faces](emberek.md).

## Movie Maker

Movie Maker opens on its own tab in the main window, beside the
library, like the collage editor. Use the tabs to switch views; click
the `×` on a tab to close it.

- The left settings column has tabs for **Movie**, **Slide**, and a
  clips view that shows the number of items in the movie. At the bottom
  are **Close** and **Create Movie**.
- The preview is on the right, with a black film frame on a dark gray
  background.
- A playback bar runs along the bottom, above the filmstrip.

## Movie settings

The top of the tab shows how many photos are selected.

- **Dimensions** sets the video resolution: 320 × 240, 640 × 480,
  800 × 600, 1024 × 768, 1600 × 1200, 1280 × 720 (720p), or 1920 ×
  1080 (1080p). The default is 640 × 480 and your choice is remembered
  for the next movie. A movie made from faces starts at 1024 × 768 and
  does not save that choice.
- **Transition style:** controls how one photo changes to the next:
  **Cut**, **Dissolve**, **Dissolve through black**, **Dissolve through
  white**, **Wipe** (from the left, right, top, bottom, or diagonally),
  **Push**, **Circle**, **Pan and Zoom**, **Pan and Zoom - face**,
  **Time Lapse**, and **Rectangle**. **Dissolve** is the default, and
  PicasaPy remembers your choice.
- **Overlap** sets the length of the transition in seconds, up to 90%
  of the slide duration.
- **Slide Duration:** sets how long each photo appears, from 1 to 300
  seconds in half-second steps. The default is 4.0 seconds, as in the
  original Picasa. PicasaPy remembers your choice.
- **Target file:** is optional. If left empty, PicasaPy chooses the
  destination and name. Use **Browse...** to choose them yourself. The
  output is an MP4 video.
- **Audio Track:** sets the movie music. Choose **Load…** to select
  an audio file or use **Delete** to remove it. Music assigned to the
  source folder is used by default (see [Folder Manager](mappakezelo.md)).
  For an album, PicasaPy uses music
  from its **Album Properties** if that file exists. The **Options**
  list controls what happens when the audio and photo durations differ:
  truncate the audio, fit photos to the audio, or repeat photos until
  the music ends. These controls are disabled when no audio track is
  set.
- Checkboxes can show captions and dates, crop photos to fill the full
  frame, or remove low-resolution faces. The last option affects only
  movies made from faces; it skips faces that are too small. In other
  movies, the setting is saved only in the project file. See
  [People and faces](emberek.md).
- **Ordering of Slides:** chooses **Best Transitions** (the default
  for a new movie), **Album Order**, or **Chronological**. Best
  Transitions sorts by capture time, as in the original Picasa; photos
  with unknown dates go last. If the time filter on the clips view is
  set, photos taken within that interval are grouped, such as frames
  from a burst. Within a group, the most similar photos are placed
  together.

Choose **Create Movie** to begin; you do not have to enter a target
file.

## Slide tab: text slides

You can add a text slide, such as a title or credits. Enter text on the
**Slide** tab, then set its font, size, and style. Styles include
**Centered**, **I'm Feeling Lucky**, **Caption**, **Caption - Classic**,
black or white gradient and transparent styles, **Scrolling Credits**,
left- or right-moving music-video text, and **Caption - Typewriter**.
You can also set bold or italic text, automatic outline, text color,
and background color.

Use **Insert Text Slide** to open the title-slide editor. Enter text,
choose the font, size, and style, review the preview, then choose
**Add**. Choose **Cancel** to discard it. The font style can be normal,
bold, italic, or bold italic. Use **Remove Selected Slide** to remove a
slide.

Three styles animate in the finished movie: **I'm Feeling Lucky**
slides and fades in from the side, **Scrolling Credits** rise from the
bottom toward the center, and **Caption - Typewriter** appears one
character at a time.

Text slides appear in the filmstrip by name. The list at the bottom of
the Slide tab lets you double-click to edit a slide, drag slides to
reorder them, or drag one outside the list to remove it.

## Clips tab: the filmstrip

The clips tab shows photos and text slides in movie order:

- **Get More...** returns to the library to select more photos while
  leaving Movie Maker open. Use **Back to Movie Maker** in the bar
  above the tray to return, then choose **Add selected clips** to append
  them to the movie.
- **Total Photos** controls how much of the selected set is used. A
  counter shows how many are currently included.
- The time filter does not yet remove photos from the movie. With
  **Best Transitions**, it controls which photos are grouped together
  and is saved in the movie project.
- **Recompute** rebuilds the filmstrip and switches to the Movie tab.
  Before it does so, PicasaPy always asks whether to remove all added
  text slides. If you check the do-not-ask-again option, it is saved
  only if you choose **Yes**; **No** or **Cancel** leaves the prompt
  enabled next time.
- **Add selected clips** appends photos selected in the library.
- **Remove selected clip** removes the selected photo or slide.
- **Play selected clip only** previews and renders only the selected
  photo.

An information line below the preview shows the selected photo or
slide's name, dimensions, and position in the movie, for example
`Text Slide 1024x768 pixels (3 / 12)`.

## Preview

The preview is on the right with its playback controls below. The
**Preview** button plays the movie and changes to **Pause** during
playback. The preview behaves like the finished movie:

- Photos follow the slide duration. Text slides appear after the
  photos with their saved text, font, and color.
- The selected transition appears between photos for the chosen
  **Overlap** time. Animated styles such as Push, Circle, and Pan and
  Zoom move as they do in the finished movie. The preview uses the
  movie resolution and the crop, caption, and date options.
- Changes to a text slide's text, font, or color appear almost
  immediately while typing.
- If an audio track is set, it plays with the preview. **Pause** stops
  it; closing the tab stops playback. Use the volume slider beside the
  playback bar to adjust preview volume. PicasaPy remembers the value.

On the Movie tab, **Back to selected slide** jumps to the selected
photo. Two controls show the movie at actual size without stretching,
or play it full-screen. Actual size (1:1) is on by default. PicasaPy
remembers your choice for the next movie.

## Default output location and name

If you do not choose a target file:

- PicasaPy saves in the movies folder under `Pictures/Picasa`. It uses
  the existing `Movies`, `Videos`, or localized movie folder if one is
  present. If it cannot create that folder, it uses the system Videos
  folder.
- The base file name follows the original Picasa name for the current
  interface language: `slideshowmovie` in English.
- If you already created a movie without a target file during this
  session, the next one uses the same folder and base name with a
  sequence number.
- If a file with that name already exists, PicasaPy adds a number to
  the end.

The output folder appears automatically in the Projects section of the
left pane.

## While the movie is being created

A progress indicator shows which photo is being processed. When the
movie is ready, PicasaPy reports where it was saved. It also reports
if creation failed. The movie appears in the movies folder under
Projects.

If you create another movie on the same tab, PicasaPy asks whether to
replace the existing file or create a new one. **Replace Existing**
overwrites the previous movie; **Create New** saves a separate file.
Choose **Cancel** or press `Esc` to stop without creating a movie.

## Reopen a movie for editing

Alongside the video, PicasaPy saves a project file (`.mxf`) in the same
format used by the original Picasa, corresponding to the collage
`.cxf` file. It stores photo order, slide duration, and transition
length.

Open a finished video in the viewer and choose **Edit Movie** to return
to its photos and settings. Its resolution starts at the default; the
dialog explains this.

## If a photo is missing

If some selected files were moved, renamed, or deleted before movie
creation, PicasaPy reports how many will be skipped and creates the
movie from the remaining photos.

## Save a frame from a video

To extract one image from a video instead of making a movie, use the
viewer. See [Viewing photos and videos](nezegetes.md).
