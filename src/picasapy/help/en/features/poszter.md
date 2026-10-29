# Make a Poster

A poster splits one picture across several sheets. Print the sheets and
join them to make a larger poster.

## Start

Select a picture, open **Create**, then choose **Make a &Poster...**. If you
selected several pictures, the first one is used.

The **Poster Settings** dialog has three options:

- **Poster size:** from 200% to 1000%, in steps of 100%. The percentage
  sets the number of rows and columns: 200% makes 2 × 2 sheets, 300%
  makes 3 × 3, and 1000% makes 10 × 10.
- **Paper size:** choose a sheet size. The available choices depend on
  your regional measurement system. The last choice is remembered. For
  now, this setting does not change how the picture is split.
- **Overlap tiles** extends neighboring sheets over one another by 10%
  of the sheet size, making it easier to join them.

The dialog suggests cropping the picture to the paper's aspect ratio
first if you do not want any part of it to be cut off.

Choose **OK** to create the sheets or **Cancel** to stop.

## Result

The sheets are saved beside the source picture in the same folder. Each
filename starts with the column and row numbers, starting from zero,
followed by the original filename. For example, a 200% poster made from
`summer.png` creates `0-0-summer.jpg`, `1-0-summer.jpg`, `0-1-summer.jpg`,
and `1-1-summer.jpg`. The first number is the column, so `1-0` is the
sheet at the right of the top row.

Sheets are always saved as high-quality JPEGs, as in the original
Picasa. The source picture is not changed. The poster uses the edited
picture, including its crop, rotation, and effects, and respects the
orientation recorded by the camera.

When the work is done, a dialog lists the saved poster sheets. If the
picture could not be read or the folder could not be written, the dialog
reports the failure. Large pictures can take a while to process, but
PicasaPy remains usable and stops waiting after two minutes.

To print the sheets, select them in the library and use [Print](nyomtatas.md).
