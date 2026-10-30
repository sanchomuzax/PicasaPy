# Printing

There are two print modes: prints at a chosen size, and a contact sheet
with many small pictures on one page. There is no separate mode switch:
**Contact Sheet** is one of the print sizes, as it was in Picasa.

## Print pictures

Select pictures, then choose **File** ▸ **Print...** (Ctrl+P), or use
the **Print** button in the photo tray.

Prints use the edited version of each picture, including its crop,
rotation, and effects, and respect the orientation recorded by the
camera. This is the same version used for export.

The dialog opens at a height suited to its contents. The **Print** and
**Close** buttons remain visible; on a small screen, scroll the options.

If no printer is installed, the dialog explains that one is needed for
printing. You can still print to PDF. On Linux, printing requires the
system print service (CUPS).

The dialog lets you set:

- **Printer:** - choose an available printer. Select **Print to a PDF
  file...** to save a PDF and enter its destination name.
- **Printer Setup** opens the selected printer's own page setup for
  paper size, orientation, and margins. The printer saves those choices
  for later. The button is disabled when printing to PDF.
- **Print size:** offers Picasa's print sizes in their original order:
  3 × 4, 3.5 × 5, 4 × 5, 4 × 6, 5 × 7, and 8 × 10 inches; 5 × 8 cm,
  9 × 13 cm, 10 × 15 cm, 13 × 18 cm, 15 × 20 cm, and 20 × 25 cm;
  Wallet, **CD Cover Size**, **Passport**, **Contact Sheet**, and
  **FullPage**. CD Cover Size is disabled. Contact Sheet means many
  small pictures on a page, as described below. FullPage is selected by
  default, and the choice is remembered.

  Six quick buttons appear below the list: five custom sizes and
  FullPage. Choose the five sizes on the **Print** tab in **Settings**
  ([Settings](beallitasok.md)). The defaults depend on the computer's
  regional measurement system, not the interface language.

  FullPage stays in English, as it did in the original Picasa.
- **Orientation:** choose **Auto**, **Portrait**, or **Landscape** for
  the whole print job. Auto keeps the paper in portrait orientation and
  rotates individual prints when that uses fewer sheets. Choose
  Portrait or Landscape to set the paper direction yourself.
- **Fit to page:** choose **Whole picture** or **Fill the page (crop)**.
  The latter fills the print area and crops the edges. Fill the page
  (crop) is the initial setting, as in Picasa. The preview updates when
  you change it.
- The number of copies per picture.

With Contact Sheet selected, the copies setting, small preview, and two
picture-quality lines are hidden; they do not apply. A **Columns:** field
appears instead. Printer, orientation, and fit remain available.

A line below the printer name shows the paper, its dimensions in
millimeters, and its orientation, for example `A4 - 210 × 297 mm,
portrait`. It updates as soon as you close Printer Setup.

The dialog shows how many pictures will be printed. Quality information
below reports the smallest picture's pixels per inch and whether it is
ready to print or should be reviewed. A picture is considered small if
the selected print size gives it less than 150 pixels per inch.

Choose **Normal** or **Optimized** quality:

- **Optimized** sends pictures to the printer at full resolution for
  sharper output, but takes longer and uses more memory.
- **Normal** is the default. It follows the **Printer quality:** option
  on the Print tab in [Settings](beallitasok.md): Compatible uses half
  resolution, while High quality uses full resolution.

The choice is remembered, and the preview updates when you change it.

### Review picture quality

If a picture may print poorly, choose **Review** to see every picture,
sorted from lowest quality, with its resolution and rating:

- Best quality: at least 150 pixels per inch;
- Good quality: 100-149 pixels per inch;
- Poor quality: below 100 pixels per inch.

You can remove selected pictures with **Remove Selected Items**, remove
all poor-quality pictures with **Remove Low Quality Pictures**, print
them anyway with **OK**, or choose **Cancel** and select another print
size. If removing poor-quality pictures would remove every picture,
PicasaPy asks first. **Remove** and stop closes the print dialog without
printing; **Don't Remove** leaves the selection unchanged.

When all pictures are ready, the dialog says so. If the settings cannot
produce a valid print, it reports the problem.

## Arrange prints on paper

The chosen print size is the size of each print, not the whole sheet.
Prints fill a grid from left to right. When a row is full, the next row
starts; when the page is full, printing continues on another sheet. For
example, an A4 sheet can hold two 10 × 15 cm prints.

PicasaPy distributes unused space evenly among the prints on each page.
A partly filled final row is left-aligned with the rows above it.

Copies per picture fill the same grid. Two pictures with two copies each
need four print spaces. Copies of a picture are placed together.

If a print size cannot fit on the paper at all, such as FullPage or a
size just larger than A4, PicasaPy prints one picture per sheet using
the whole printable area.

## Passport photos

**Tools** ▸ **Experimental** ▸ **Passport photo...** also opens this
dialog, with a face crop and Passport print size. See [Passport
photo](utlevelkep.md).

## Preview and page count

The small preview below the printer shows the actual sheet and its grid
of prints. When there are several pages, use the page controls below it
to see the current page and total page count before printing.

## Borders and captions

Choose **Border and Text Options** to set a border and caption for the
printed picture:

- Caption source - No text, Captions, File name, or Exif information;
- caption position - below the picture, on the picture, or on the border;
- font and size, plus **Wrap text**;
- **Border** - None, Max., Bottom only, or **Even width border**;
- **Text color** and **Border color**.

Choose **Apply** to update the preview. These choices are remembered.
They are unavailable for contact sheets, as the dialog explains.

## Printing progress

While printing, the dialog shows the current picture number, such as
`Printing: 2 / 12`, and the progress bar advances. This also applies to
PDF output. The **Print** button cannot start another job while one is
in progress.

## Contact sheets

Choose **Folder** ▸ **Print Contact Sheet...** (Ctrl+Shift+P) to put many
small pictures on a page. With nothing selected, it uses the pictures
in the open folder. Set the number of pictures in each row with
**Columns:**.

You can also choose **Contact Sheet** at the end of the Print size list.
There is no page preview in this mode, but the count tells you how many
pages will be printed. Contact Sheet mode is temporary: after closing
the dialog, Ctrl+P opens the usual size-based print view.

## Printer selection

PicasaPy has its own simple printer selector instead of the system's
native print dialog. Use **Printer Setup** for paper size, orientation,
and margins. Set printer-specific options such as duplex printing or
paper tray in the printer's own control panel, or in the PDF viewer
after printing to PDF.
