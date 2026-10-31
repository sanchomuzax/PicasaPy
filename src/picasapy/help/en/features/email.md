# Send photos by email

You can send selected photos through the email program installed on your
computer. PicasaPy prepares the attachments; you write the message in
your own program. When you choose **Send**, that program opens a new
message with the photos attached.

Start in any of three ways: click the **E-Mail** button in the photo
tray, choose **File** ▸ **E-Mail...**, or press `Ctrl+E`. The shortcut
does not run while you are typing in a text field.

## What happens

1. Select the photos.
2. Start the email action from the button, menu, or `Ctrl+E`.
3. PicasaPy prepares the attachments and resizes the photos if needed.
4. An email composition window opens.
5. Choose **Send** to open a new message in your email program with the
   photos attached.

On Windows, PicasaPy passes the photos through the standard attachment
interface, so they arrive as attachments. The message opens in your
email program for you to send; PicasaPy does not send email by itself.

On Linux, the `xdg-utils` package must be installed to pass attachments
to the email program. It is usually present on desktop systems.

Attachments always contain the edited version of each photo,
including rotation, mirroring, and other edits, just as when exporting
([Export](exportalas.md)). **Original Size** skips resizing but still
includes edits. The original file is not changed.

PicasaPy prepares the attachments in a temporary folder on your
computer. They are not kept forever: when the program starts, it removes
copies from earlier sends so they do not accumulate on disk. It leaves
copies created within the last hour in place in case another PicasaPy
window is still sending a message.

## Compose the message

Enter the recipient in **To:** and the subject in **Subject:**, then
write the message below. The attachments appear as thumbnails in a row.
Select a thumbnail and use the adjacent remove control to drop that
attachment; the photo remains on disk.

Choose **Discard** to close the window without sending, or **Send** to
hand the message to your email program. You can leave the recipient
blank and enter it in that program instead.

Right-click the **To:** field to toggle **Auto-Complete**. It is on by
default, and PicasaPy remembers your choice.

## Choose an email program

Until you choose otherwise, PicasaPy first shows the **Select Email**
page the first time you send. The first entry shows the name of
your computer's default email program (for example Thunderbird or
Outlook); if PicasaPy cannot read it, the entry says **Native Mail
Client**. Confirm it to open a new message in that email program. **Google Mail** is
disabled because PicasaPy does not connect to a Google account.

Check the option to remember this choice and skip the dialog next time
to open the message composer directly. You can restore the prompt from
the email preferences at any time.

## Email preferences

Open **Tools** ▸ **Options** to change the email preferences:

- Choose **Let me choose each time I send pictures** to show the
  selection page on every send, or **Use this computer's default email
  program** to open that program directly. The Google account option is
  disabled.
- Set the maximum long-edge size for multiple photos. The current
  pixel value appears beside the control.
- For a single photo, use the same size as for multiple photos or keep
  **Original Size**.
- For videos, choose whether to attach the **First frame** as a still
  image or the **Full movie**. The program remembers your choice.

The option **Send inline photos and captions (Outlook only)** is
disabled; it is not implemented yet.

Choose **OK** to save these preferences or **Cancel** to discard them.
See [Settings](beallitasok.md).

## If sending does not start

If no email program is configured on your system, PicasaPy displays a
message. If an email program is available but cannot accept attachments,
it opens a blank message without the photos and reports the problem.
Attachment preparation errors are also shown at the top of the window.

An unfinished collage cannot be sent. Finish it first.
