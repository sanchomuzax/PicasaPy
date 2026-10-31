# People and faces

PicasaPy finds faces in your pictures, groups faces that may belong to
the same person, and lets you name them. Names are stored in
`.picasa.ini`, so the original Picasa can read them too.

## Find faces

Choose **Tools** ▸ **Find Faces** to open the face-search dialog. It has
two steps:

1. **Find Faces** scans pictures and marks detected faces. Progress is
   shown, and you can cancel at any time. At the end, PicasaPy reports
   how many faces and pictures it found.
2. **Group Faces** puts faces that appear to belong to one person into
   groups.

If suggestions are enabled on the **Name Tags** tab in **Settings**
(the default), grouping starts automatically after a successful search.
Otherwise, start it yourself.

The face-detection model is installed with PicasaPy; no download is
normally needed. If the model is missing, the dialog offers **Download
the model**. If the file exists but cannot be loaded, PicasaPy reports
that and writes details to the application log.

Face search also runs in the background for new pictures by default.
Turn it off on the **Name Tags** tab in **Settings** (see
[Settings](beallitasok.md)). If the search cannot start, the reason is
written to the log. Detection rarely marks a face where there is none;
landscapes and other pictures without faces are normally left alone.

### Each picture is scanned only once

PicasaPy remembers which pictures have already been scanned and skips
them on later searches, including pictures where no face was found.
If a picture changes, for example because you edit or replace it, it is
scanned again.

Right-click a folder or album in the left pane and choose **Add Name
Tags** to search just its pictures instead of the whole library.
Face search can also be controlled for each folder in
[Folder Manager](mappakezelo.md). When search is disabled for a folder,
its pictures are marked as already checked so they will not be scanned
again.

## People panel

Open the panel from **View** ▸ **People**, or use the People button in
the photo tray. It has a header and a list of the named people in the
selected pictures. The header depends on the current view:

| Situation | Header |
|---|---|
| One selected picture or the viewer, with a named person | **In this photo:** |
| One selected picture with no names | **Who is in these photos?** |
| Several selected pictures with names | **People in these photos:** |
| A person's album | **Also in these photos:**, listing other people in the selected pictures |
| Several pictures with unnamed groups | **Unnamed groups of people:** |
| The Unnamed album in grouped view | **Unnamed people in these photos:** |

When there is nothing to list, an italic message explains what will
appear there. In a person's album, for example, it explains that people
appearing with the selected person will be listed.

The rows show face thumbnails. Named people have a cropped face and a
name; click the name to open that person's album. Unnamed detected faces
appear at the bottom with a face thumbnail and an **Add a name** field.
Type a name and press Enter:

- If the person already exists, the face is assigned immediately.
- For a new person, the people-management dialog opens with that name.
  The person is created only when you confirm there. Closing the dialog
  leaves everything unchanged.

You can also drag an unnamed face onto a named person in the list. A
small × on an unnamed face asks whether to move it to the Ignored People
album. The two buttons are **Ignore Person** (**Ignore People** for
several faces) and **Cancel**; `Enter` chooses to ignore. The same symbol appears on named rows, but has no effect there.

When PicasaPy suggests a name, it shows the name with a question mark.
Use the check mark to accept it and assign the face, or the X to reject
it and leave the face unnamed.

### While background face search is running

If the background search has not reached all selected pictures, the
header shows the current status instead of the usual text. It reports
that faces are loading for one or more files, that it is looking for
other people in a person's album, or that face data is being prepared in
the Unnamed album. Outside a person's album, it also shows how many
selected files remain unchecked. New faces appear in the list shortly
after they are detected. When all selected pictures have been checked,
the usual header returns.

### Add a person manually

If face search missed a face, select the picture and choose **Add a
person manually** at the bottom of the panel. PicasaPy opens the picture
in the viewer with a rectangle and a short guide:

1. Drag the rectangle over the face and adjust its sides.
2. Choose the **Add a name** field below it, type the name, and press
   Enter or select a suggested name.

Choose **Cancel** to leave manual face creation.

## Unnamed faces

The Unnamed entry in the left People group collects faces that do not
yet have names. It appears before the named people. Its count shows the
number of unnamed faces and is included in the group's total.

The first time you open the album, a welcome dialog explains how to
name or ignore a face and where to find suggestions. Choose **Close**;
it will not appear again. **Learn more...** opens the corresponding
original Picasa help page in your default browser, if that service is
still available. Picasa's online help has been discontinued, so the
information may no longer be there. A reference to signing in to a
Google account in that guide does not apply to PicasaPy. If the album is
empty, the same guide is shown in the People panel.

The album opens with faces grouped by likely person. Use **Expand
groups** to open the groups or **Group by face** to collapse them. The
header explains the next step; while groups are being calculated, it
shows a progress message. With groups expanded, you can assign a name to
several selected faces at once using **Add a name**, or move them aside
with **Ignore Selected**.

Each face also has its own **Add a name** field. As you type, a list of
existing people whose names match appears with their face thumbnails.
Matching starts at the beginning of name words: `an` can match Anna
Kiss or Kiss Andrea, but not Hanna. For several words, the words must
appear in order. Click a suggestion to assign it, use the up and down
arrows to choose one and press Enter, or press Enter with no suggestion
selected to open people management. A question mark beside a suggested
name can be clicked to accept it.

Choose **Ignore** for faces you do not want to name, such as passersby
or faces on posters. PicasaPy asks for confirmation; you can choose not
to be asked again. Ignored faces appear in the Ignored People album.
Switch to them with **Show ignored faces**. Select one or more and use
the control to restore them to the Unnamed album, or choose **Back to
Unnamed** to return. The ignored-faces row replaces the Unnamed row in
the left pane while you are viewing ignored faces. The Unnamed album
does not have a Look for more suggestions control; that is available in
a person's album.

### Ignoring faces is shared with original Picasa

PicasaPy records ignored faces beside the picture in `.picasa.ini`,
using the same marker as the original Picasa. Faces ignored in Picasa
therefore appear in the Ignored People album here, even if PicasaPy did
not detect them. Faces ignored in PicasaPy remain ignored in Picasa and
are not suggested again. The two applications use different detectors,
so their face boxes may differ. PicasaPy treats largely overlapping
boxes as the same face and does not show it twice.

## Manage people

Choose **Tools** ▸ **People Manager...** to open the address book of known
people. The list on the left is sorted by name and has a Search field
above it. Search matches the beginnings of name words, as in the
Add a name fields. New unsaved entries appear first, followed by names
beginning with the query, then other matches.

Use **New Person** to add an empty entry or **Delete Person** to remove
the selected one after confirmation. For the selected person, the dialog
shows the number of associated photos and provides editable contact ID,
name, and email fields. **Revert** discards changes to that person and
is enabled only after a change.

Choose **OK** to save or **Cancel** to discard. A person cannot be saved
with an empty name. If a name or email already exists, PicasaPy asks
whether to create a duplicate; choosing No returns to editing. If the
save fails, an error is shown. Names are stored in the shared contact
list, while only the `.picasa.ini` files in folders containing that
person are changed. An email address can be saved only for a person
already tagged in at least one folder.

Controls for syncing face tags with Google Web Albums, managing online
contacts, and refreshing contacts are disabled because the Google
service has ended.

## Faces in the viewer

Use **Show Faces** or F to display face boxes. **Edit Faces** or Shift+F
lets you name them. In that mode you can also add a face by drawing a
box and choosing the **Add a name** field below it. The box remains so
you can adjust it before naming. Ignored or invalid faces have no box;
a manually drawn box with no name is not saved.

Detected but unnamed faces are not outlined by default, but their
locations are clickable. Click one to show a thin gray box and a field
for entering its name. Press Enter or choose a suggested name to save;
Esc closes the field without saving. This works even when Edit Faces is
off. Hold Shift, Ctrl, or Alt while drawing to constrain the box ratio,
as described in [The Editor](szerkeszto.md).

Choose **Picture** ▸ **Reset Faces** to clear face boxes, names, and
ignored states on the selected pictures (the current picture in the
viewer), then search those pictures again in the background. The people
list is retained. There is no confirmation, so check the selection
first.

To reset the whole library as in Picasa, hold Ctrl while clicking the
command to clear all face data and people albums, then search all
pictures again. Hold Shift to clear people albums and names but leave
faces in the Unnamed album; ignored faces remain ignored. PicasaPy shows
a warning first. Choose Yes to continue or Cancel to stop. Ctrl takes
precedence if both keys are held. These actions cannot be undone.

## Share names with other applications

When you name a face, PicasaPy writes a small sidecar file with the face
location and name without changing the picture file. It writes two
standards so Windows Photo Gallery, digiKam, and Lightroom can read the
information. If writing a file fails, for example because the folder is
read-only, PicasaPy reports the problem; the name assignment remains.

### Write face information for a folder

The experimental XMP command can write the information for several
pictures at once. Its dialog warns that this can take a long time. Use
**Write Selected** for selected pictures, **Write Faces** for pictures
that contain faces, or **Write All**. Cancel closes the dialog without
writing. A progress panel shows how many pictures have been processed;
you can cancel and keep files already written. At the end, PicasaPy
reports the number written, skipped, and the first error, if any.

## The person album header

At the top of a person's album, the header shows the person's face and
name, then a strip of their faces and the pictures. **Remove** is
available when selected pictures have a face assigned or a suggestion
for that person. It removes the name after confirmation, or rejects the
suggestion. A nearby thumbnail control sets the selected face as the
person's picture; the same command is available in the context menu.

## Review suggestions in a person's album

A person's album shows both pictures already tagged with that person
and pictures where PicasaPy only suggests the match. Each picture
appears once even if several faces have the same suggestion.

When suggestions are waiting, the header offers an approve-all control
with the number pending and **Remove**, which rejects suggestions but
leaves the faces unnamed. A check-mark control selects all pictures
with a pending suggestion so you can review only those. When nothing
is pending, **Look for more suggestions** runs another search with a
temporarily lower recognition threshold; the saved setting is
unchanged.

You can select pictures in the grid and apply the controls only to the
selected pictures that have a suggestion for this person. Other
people's suggestions on the same pictures are unaffected. The button
labels and tooltips change to indicate that they apply to the
selection. If the selection has no pending suggestion for this person,
the controls apply to all pending suggestions as usual.

Two controls in the upper-right choose whether thumbnails zoom in on
the face or show the whole picture. The whole-picture view is the
default. This view choice carries over to other person albums until you
change it. For a small face, PicasaPy reads the crop from the original
file to keep it sharp; videos and RAW files keep their usual thumbnail.

A toggle beside these controls can show only pictures with pending
suggestions. Already named faces disappear from the grid while it is
on. The toggle remains available when there are no suggestions, so you
can leave the empty filtered view. Each time you open the album, the
filter starts off; after approving or rejecting suggestions, its current
state is retained while the grid refreshes.

## People albums

Two movie controls in a person's album open the [Movie Maker](mozgofilm.md)
with pictures from every non-empty person album, in album order, not just
the open album. The initial movie size is 1024 × 768 and is not remembered
for the next movie.

Use **Move to New Person...** to reassign a misidentified face, or
**Add to People Album** to assign it to an existing person. **Remove
from People Album** or Ctrl+Delete removes it from the album.

### Choose a person's picture

The left pane and People panel show a small face beside each person's
name. PicasaPy chooses one automatically, but you can select a better
one: in the person's album, right-click a picture and use the command
to set its face as the People album thumbnail. The chosen crop remains
beside the person's name after restarting. The command appears only in
that person's album and is enabled only for a picture where their face
is marked.

## Make a movie from faces

The **Create** ▸ **Movie** command for a People album opens
[Movie Maker](mozgofilm.md) without a selection. It uses pictures from
all non-empty People albums and is enabled when at least one person
exists. The command for faces in the selection opens
[Movie Maker](mozgofilm.md) with the selected pictures and starts at
1024 × 768.

For a face movie, the third Movie Maker tab is **Options** instead of
Clips, as in the original Picasa. It contains Dimensions, the caption,
crop, date, and low-resolution-face options, and the slide-order list.
These options are not on the Movie tab in this mode; their defaults are
unchanged. Each clip is framed around a face at the center. A picture
with several marked faces contributes a separate clip for each face;
pictures without a usable face are skipped. Enable the low-resolution
face option in [Movie Maker](mozgofilm.md) to skip faces that are too
small.
