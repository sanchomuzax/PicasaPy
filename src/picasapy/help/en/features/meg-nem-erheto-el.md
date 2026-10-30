# Features not yet available

PicasaPy follows the complete menu structure of the original Picasa 3.9
to make the interface familiar. Some items are therefore visible even
though they are not connected yet. These items are disabled and do
nothing when clicked.

This page lists what is currently unavailable so you do not have to
search for it.

> A gray item is not necessarily a missing feature. Working commands
> may also be disabled when they cannot be used in the current state,
> for example when no photo is selected or while you are in the viewer.
> Select a photo or return to the library and the command may become
> available. Only items listed on this page remain disabled.

## Not implemented yet

In the **Help** menu, **Help Contents and Index** (also available with
`F1`) and the keyboard-shortcuts page work. The first opens this help;
see [Built-in help](sugo.md). The other lists working shortcuts; see
[Keyboard shortcuts](billentyuk.md).

### Context menus

The Open With command in the viewer's context menu is not implemented.
It does work from the photo's context menu in the library; see
[File operations](fajlmuveletek.md).

### Options

Six of the eight tabs in **Options** work: **General**, **File Types**,
**E-Mail**, **Slideshow**, **Name Tags**, and **Print**. On the
**Network** tab, only logging works. These features are still disabled:
See [Settings](beallitasok.md) for details.

- Proxy fields and the **Automatically detect network settings**
  checkbox on **Network**.
- **Web Albums**, because Picasa Web Albums has been discontinued.
- Automatic updates and the **Send anonymous usage statistics**
  checkbox on **General**.
- **Send inline photos and captions (Outlook only)** on **E-Mail**.

## Discontinued online services

Google discontinued Picasa's online services in 2016. The matching
menu structure remains for familiarity, but these services are not
available and will not be implemented:

- Importing from Google Photos, ordering prints, and publishing to
  Blogger.
- Upload Manager, batch upload, and the legacy upload commands,
  including uploads to Google Photos, shared Web Albums, and YouTube.
- Picasa Web Albums upload, quick upload, disabling uploads, and other
  online actions.
- Picasa forums, online information, product release announcements,
  privacy policy, and terms of service.
- Checking for updates, which depended on a Google service.
- The Remote Desktop display mode, which was specific to Windows
  Remote Desktop and is not useful here.

The Google account sign-in text at the right of the menu bar is also a
remnant of the original layout and does not work.

The exception is the new Google Photos upload feature on the photo
tray, which uses your own Google client. See
[Upload to Google Photos](google-fotok.md). The legacy menu commands
listed above remain unavailable.

## Supported by the program, but not exposed in the interface

- Virtual albums in `.picasa.ini` are read and preserved, but cannot
  yet be browsed.
- Importing an old Picasa database: names, keywords, and locations
  can already be imported with **Tools**; see [Importing](importalas.md).
  Other data from the old database is not transferred yet.
- Writing contacts: PicasaPy can read the old Picasa contact list,
  but cannot write to it.
