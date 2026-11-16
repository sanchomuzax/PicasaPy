# Send photos by email

You can send selected photos through the email program installed on your
computer. PicasaPy prepares the attachments, then opens your email
program with a new message that already has the photos attached. You
write and send the message there.

Start in any of three ways: click the **E-Mail** button in the photo
tray, choose **File** ▸ **E-Mail...**, or press `Ctrl+E`. The shortcut
does not run while you are typing in a text field.

## What happens

1. Select the photos.
2. Start the email action from the button, menu, or `Ctrl+E`.
3. If more than 20 photos are selected, PicasaPy first asks in a
   **Confirm** window: "Email *N* files?". **Cancel** prepares nothing;
   **OK** continues with the photos that were selected when the question
   appeared.
4. PicasaPy prepares the attachments and resizes the photos if needed.
5. Your email program opens a new message with the photos attached.

PicasaPy has no message window of its own: you enter the recipient,
subject, and text in your email program. PicasaPy fills in the subject
and text based on the number of photos: for one photo the subject is
"a picture for you" and the text "You have been sent 1 picture.", for
more photos "*N* pictures for you" and "You have been sent *N*
pictures.". You can change them in your email program.

On Windows, PicasaPy passes the photos through the standard attachment
interface, so they arrive as attachments. PicasaPy does not send email
by itself: sending is up to you in your email program.

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

## Choose an email program

Until you choose otherwise, PicasaPy shows the **Select Email** page
before sending. The first entry shows the name of your computer's
default email program (for example Thunderbird or Outlook); if PicasaPy
cannot read it, the entry says **Native Mail Client**. Click it to close
the page and open a new message in that email program. **Google Mail** is
disabled because PicasaPy does not connect to a Google account.

Check the option to remember this choice and skip the dialog next time
to open your email program directly, without asking. You can restore the
prompt from the email preferences at any time.

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
On Windows, PicasaPy also names the email program's error: "Too many
file attachments to send.", "Attachment was not found", "Could not open
an attachment.", "Unknown recipient.", and in every other case "The email
could not be sent.". If you cancel sending in your email program yourself,
PicasaPy shows no error.
Attachment preparation errors are also shown at the top of the window.

An unfinished collage cannot be sent. Finish it first.
