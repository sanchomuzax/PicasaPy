# Places and geotags

A geotag records where a photo was taken. Many cameras and phones add
one to the file automatically; you can add one to other photos yourself.

## The Places panel

Open **View** ▸ **Places**, or use the Places button in the photo tray.
The map shows markers for photos with a location, and the number of
located photos appears above it.

To assign a place, select photos in the grid and right-click that point
on the map. Every selected photo receives that location.

Click a marker to select the photo and filter the grid to located
photos, just as with the globe filter on the toolbar. Use **Back to View
All** on the green bar, or turn off the globe filter, to restore the
full view.

Each marker shows a thumbnail from one of its photos. Clicking it opens
a popup with the number of photos at that location. The popup lets you
select those photos in the grid or clear their location data. Clearing
may require confirmation when more than five photos are affected.
Click the marker again to close the popup.

### Drag a photo onto the map

You can also drag photos from the grid onto the map. PicasaPy asks you
to confirm placing them at the destination. If a photo already has a
location, the confirmation asks whether to move it. When you drag a
selection, all selected photos are included. Choose **(OK)** to assign
the destination or **Cancel** to leave them unchanged.

### Loading and internet connection

Map tiles are downloaded from the internet. While the map loads, the
panel displays a loading message and the original Picasa progress
image. If there is no connection and the map cannot load, the panel
reports that Google Maps could not be initialized and asks you to check
your connection. This message uses the original Picasa wording.

The panel has a control for clearing locations from selected photos;
it shows how many photos are affected. The same action is available
from **Tools** ▸ **Geotag** ▸ **Clear Geotags**.

### Confirmation for larger selections

PicasaPy asks for confirmation in two cases, to prevent an accidental
change to many photos:

- Changing the location when more than 20 photos are selected.
- Clearing geotags when more than five selected photos actually have a
  location.

With fewer photos, the operation runs without asking.

> If the Qt map component is not installed, the panel explains that
> maps are unavailable but geotags can still be edited. Existing
> locations can still be read and cleared.

### Search places and choose a map type

Under the **Search** label, the panel has a text field and a search
button. This is not a search of the map service: it sends no network
request. PicasaPy searches your located photos by file name, caption,
tags, and folder name. Only markers for matching photos remain on the
map, and the located-photo count updates to match. Press Enter or use
the button to search. Clear the field and search again to restore every
marker. This search cannot set a location; use the map's right-click
action for that.

A map-type selector appears beside the photo count. Available types
depend on the map component on your system. If none is available, the
selector displays **Map**.

## Filter by location

The globe filter on the toolbar shows only photos that have a location.
It is enabled only when at least one such photo exists.

## Google Earth

The **Tools** ▸ **Geotag** submenu contains these commands:

- **Export to Google Earth File** writes a file from selected photos
  with locations that Google Earth can open. PicasaPy reports how many
  photos were included; if none of the selected photos has a location,
  it reports that no file was written.
- **View in Google Earth...** does the same and then opens the file in
  Google Earth installed on your computer.
