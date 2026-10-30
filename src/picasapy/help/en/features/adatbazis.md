# The database: location, moving, and compacting

## What the application stores, and where

PicasaPy stores data in three places:

1. Beside the photos, in each folder - in the `.picasa.ini` file. It
   contains everything associated with a photo: its star, caption, edits,
   face names, and geotag. This is the source of truth. If you copy the
   folder elsewhere, all of this information goes with it.

   The original Picasa uses the same file, so both applications can use the
   same photo library. PicasaPy also preserves data it does not understand,
   so Picasa settings are not lost.

2. A search database - used to speed up searches and filters. It is only
   a cache and can be rebuilt from the photos at any time.

3. A thumbnail cache - so large photos do not have to be read again to
   display their thumbnails.

The search database and thumbnail cache are stored in the system's usual
data and cache folders.

## Moving the database

If your system drive is running out of space, you can move the database and
cache elsewhere. Choose the database-location option from the **Tools** menu.

The dialog shows the database's current location. Use **Browse...** to
choose a new one. The default-location control restores the original
location.

The move is scheduled for the next time you start the application. You can
close the dialog right away; the files are not copied yet. At the next
launch, a progress window appears while the database is moved. The
application waits until then so it does not copy files that are still in
use, and it starts from the new location without needing another restart.

You can cancel a scheduled move from the same dialog.

The old copy is moved to the Trash, not permanently deleted, as in the
original Picasa. If no Trash is available, the old database stays where it
is and PicasaPy tells you.

PicasaPy checks the destination first: it must be a folder, it must be
empty, and it must not be on a network drive. If any check fails, nothing
is changed.

## Compacting the database

Over time, the database file can grow because of space left by deleted
records. Compacting it reclaims that space.

The operation can be cancelled safely. If you cancel, the database remains
unchanged. If there is no space to reclaim, PicasaPy tells you that no work
is needed.

## If the database is busy

When a folder is being refreshed, another task - such as face detection or
database compaction - may be using the database. PicasaPy does not fail. It
tells you that syncing the folder will continue later, then retries
automatically after a few seconds. You do not need to do anything.

## If the database is damaged

Your photos are safe: important data is stored in the `.picasa.ini` files
beside them. If the database is damaged, delete its contents, restart
PicasaPy, and let it scan the watched folders again.
