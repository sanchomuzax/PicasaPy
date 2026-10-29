# Screensaver

The screensaver starts a full-screen slideshow of your photos. On
Linux, you can configure and preview it in PicasaPy. If your desktop
environment supports it, it can also start automatically after the
computer has been idle for a while (see below).

## Add photos

Select photos and use the command for adding them to the screensaver.
PicasaPy appends them to the private **Selected Pictures** list. A
photo is never added twice.

If you do this while viewing an album, PicasaPy asks whether to add all
photos from the selected album. Choose **Yes** to add them, or **No**
or **Cancel** to leave the list unchanged. The confirmation also
appears if none of the selected photos was new; the count will be zero.

## Configure

Choose **Tools** ▸ **Configure Screensaver...** to open its settings:

- **Display photos from:** Select folders, albums, or **Selected
  Pictures**. The slideshow uses the checked sources. If no source
  contains a photo, the window explains that there is nothing to show.
- **Visual effect:** Choose **Crop**, **Dissolve**, **Dissolve through
  black**, **Dissolve through white**, or **Pan and Zoom**.
- **Change pictures every:** Set an interval between 1 and 30 seconds.
- **Show captions** displays photo captions in the slideshow.
- **Start when the computer is idle for**: Set a delay in minutes,
  from 1 to 120, after which the screensaver starts automatically.
- **Preview** starts the slideshow. It is disabled until a checked
  source contains a photo.

Choose **OK** or **Cancel** to close the window. Your selections are
saved as you make them.

## Preview

The preview fills the screen and repeatedly shows photos from the
checked sources. Any key press, mouse movement, or click exits and
returns to the previous window size. The screensaver does not play
music. If none of the selected sources has an available photo, PicasaPy
reports that.

## Start after the computer has been idle

Enable **Start when the computer is idle for** in the configuration
window. The setting takes effect immediately, requires no new login,
and remains enabled the next time you log in. It uses the same sources,
effects, and timing as the preview. Any key press, mouse movement, or
click exits the slideshow. The main PicasaPy window does not need to be
running.

This works on wlroots-based Wayland desktops — labwc (the Raspberry Pi
OS default), sway, Wayfire, river, Hyprland, and niri — when `swayidle`
is installed. It is included by default on Raspberry Pi OS; other
systems may need the `swayidle` package. The checkbox is disabled on
other desktop environments and explains why. GNOME, KDE, and X11
desktops use their own screensaver managers, which PicasaPy cannot
reliably integrate with. If `swayidle` is missing, PicasaPy asks you to
install it.

PicasaPy creates one file in your user settings:
`~/.config/autostart/picasapy-screensaver.desktop`. At login, it starts
a `swayidle` watcher that runs `picasapy --screensaver` after the
specified idle delay. The watcher also starts immediately when you
enable the setting. When you disable it, PicasaPy removes the file and
stops its own watcher. It does not change other `swayidle` settings,
such as turning off the display.

The Raspberry Pi OS labwc desktop and most full desktop environments
run autostart entries automatically. A minimal desktop such as plain
sway may not run entries from `~/.config/autostart`; in that case the
watcher works for the current session, but you must start it again
after logging in next time. Its command is in the file's `Exec=` line.

You can also start the slideshow from a terminal with
`picasapy --screensaver`. If none of the checked sources has a photo,
no window opens and the program explains why.
