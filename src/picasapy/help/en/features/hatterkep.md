# Desktop background

Set a photo or a completed collage as your desktop background in one
step.

## From a selected photo

Select one photo, then choose **Create** ▸ **Set as Desktop...**. The
command is disabled if nothing is selected. If several photos are
selected, the first one is used.

PicasaPy asks first: a **Confirm** window warns that the picture will
replace your current desktop background. **Set Desktop** (it has focus,
so `Enter` chooses it) sets the background; **No** cancels.

## From a collage

Choose **Desktop Background** in the collage panel to create the
collage and set it as your background immediately. See [Collages](kollazs.md).

## What happens

PicasaPy makes a copy of the photo in a dedicated backgrounds folder
and sets that copy as the wallpaper. The background remains in place if
you later rename, move, or delete the original photo.

The copy contains the edited, correctly oriented version: rotation,
mirroring, cropping, and effects are included, and a sideways original
is not left sideways. The original file remains unchanged.

The backgrounds folder sits beside the collage destination folder,
which is inside your photo folder by default, among the PicasaPy
project folders. If you move the collage destination, the background
copy moves there too.

The image is centered, without stretching or tiling, as in the original
Picasa.

## If the background cannot be set

On Windows, PicasaPy asks the operating system to set the background,
which usually succeeds. On Linux it tries common desktop environments,
including GNOME, KDE Plasma, the Raspberry Pi desktop, and wlroots-based
desktops such as labwc and Sway. KDE Plasma needs its wallpaper utility;
wlroots desktops need `swaybg`. If the required utility is missing,
automatic setup fails.

If none of the methods succeeds, PicasaPy tells you where it saved the
image so you can select it in your system's own settings. When setup
succeeds, a brief message confirms it.
