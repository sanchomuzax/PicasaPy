# What's changed?

A user-focused changelog: only changes you can see on screen. The detailed, developer-facing changelog is in the program's <code>CHANGELOG.md</code> file.

## 2026-10-29

### Appearance

- **View** ▸ **Dark Theme** now draws the whole interface in dark colors. Buttons, indicators, input fields, the timeline, the Tags panel, and the video player controls all follow the dark theme. See [Settings](features/beallitasok.md).
- While the map in the Places panel loads, a custom-drawn progress indicator appears. See [Places](features/helyek.md).

### Language

- On a computer whose language is not English, the first-run window that offers to use the system language appears again. This prompt had previously stopped appearing. See [Getting started](getting-started.md).

## 2026-10-28

### Upload

- The green **Upload to Google Photos** button on the Picture Tray now works: it uploads the tray's pictures to your own Google Photos account. To use it, enter your Google client details on the new **Google Photos** tab in **Settings**, then sign in. See [Upload to Google Photos](features/google-fotok.md).

### Settings

- All file formats are now enabled by default on the **File Types** tab, including .GIF, .PNG, and .TGA. After an update, people who had never changed these options will no longer find their PNG, GIF, or TGA pictures missing. See [Settings](features/beallitasok.md).

### Saving

- In the save confirmation window, the check box now has the original label **Do not ask me again.** The backup also preserves the original file's modification date. See [Saving](features/mentes.md).

### Other

- On Windows, saving from the photo viewer and saving <code>.picasa.ini</code> files work more reliably.
- The editor tab icons now use the original Picasa colors and positions.

## 2026-10-27

### Settings

- The **Clear cache files** check box is saved only when you click **OK**; **Cancel** discards the change. See [Settings](features/beallitasok.md).

### Export

- Templates 4–6 in Export as HTML Page (single-page) now show everything in one window: a scrollable thumbnail strip on the left and the large picture on the right. See [Export](features/exportalas.md).

### Editing

- Suggested crops in the **Crop** panel now appear as small previews without titles or captions, as in the original. See [The editor](features/szerkeszto.md).
- The **Filtered BW** effect now starts with white for a new picture. If the picture already has this effect, the panel opens with its existing color. See [Effects](features/effektek.md).

### File operations

- When renaming several pictures, **Rename Files** adds a number to the end of a name only when that name is already taken. The number has three digits (-001, -002, and so on). A name conflict no longer stops the entire rename operation. See [File operations](features/fajlmuveletek.md).

### Tags

- The top two buttons in the Quick Tags bar keep the two most recently used tags. A new tag moves to the first position, and the previous first tag moves to the second. See [Stars, captions, and tags](features/csillag-felirat-cimke.md).

### Passport photos

- If a picture contains several faces, **Passport photo** now displays **Can't find any faces**, as the original does. See [Passport photos](features/utlevelkep.md).

### Importing from the old Picasa

- Repeating the import no longer creates duplicates. It runs quickly even with a large database and reads all album memberships. See [Import](features/importalas.md).

## 2026-10-26

### Settings

- The **Settings** window now has **OK** and **Cancel** buttons at the bottom instead of **Close**. **OK** saves changes; **Cancel** discards them. See [Settings](features/beallitasok.md).
- On the **General** tab, the **Clear cache files** check box replaces the earlier cache-clearing button. When selected, the program clears the thumbnail cache as it exits.
- On the **File Types** tab, labels now match the original. In a new installation, .GIF, .PNG, and .TGA are disabled by default. Your choices are kept if you have already changed them.
- The original row labels now appear on the **E-Mail** and **Web Albums** tabs.

### Export

- The Export as HTML Page window now lists all seven templates with their original Picasa names, descriptions, and previews. The button is called **Export**. See [Export](features/exportalas.md).

### Editing and saving

- **Edit** ▸ **Copy Text** and **Paste Text** now copy text written on a picture with the **Text** tool to other pictures, as in the original. These commands are no longer for copying picture captions. See [The editor](features/szerkeszto.md).
- **File** ▸ **Save**, Ctrl+S, and the **Save** button in the header are enabled only when there are unsaved edits. See [Save and restore](features/mentes.md).
- In the restore prompt, **Cancel** gets focus, and for one picture the original question is shown. The confirmation for **Undo all Edits** now uses the original title, text, and buttons.

### Library and albums

- The Picture Tray's album button works even when you do not have any albums of your own. Its menu offers **Screensaver**, **Starred photos**, your albums, and **New Album...**. See [The Library](features/konyvtar.md).
- The toolbar's new album button now creates an album in the selected picture's folder in Timeline, search results, and album views too. The program explains when it cannot do so.
- **Picture** ▸ **Unhide** and **Folder** ▸ **Unhide** are enabled only for hidden items.
- **View** ▸ **Show Edit Controls** is disabled and unchecked in Library View.

### File operations

- **File** ▸ **Move to New Folder...** opens **Folder Properties** with the name **Untitled**. See [File operations](features/fajlmuveletek.md).
- The **Rename** button in the **Rename Files** window is disabled while the name is empty or unchanged.
- In the delete confirmation, **Cancel** gets focus and the check box says **Don't ask again, always remove**.
- The **Adjust Photo Date** window shows the current date and time in two gray fields.

### Other

- In the simplified viewer (opened with an image file), a starred picture has a star, and the **Star** button removes it. See [Viewing photos](features/nezegetes.md).
- Checkable menu commands no longer have an empty box before their check mark. Disabled buttons and fields now have gray labels.

## 2026-10-25

### Opening pictures from a file manager

- When started with an image file (using the file manager's **Open With** command or by passing the picture's name), the program opens it immediately in a simplified viewer with its own toolbar. The **Edit in PicasaPy** button opens the full program. See [Viewing photos](features/nezegetes.md) and [Getting started](getting-started.md).

### Library and albums

- Your own collections can now be locked with a password. **Add/Change a password...** in the collection header's context menu now works. See [The Library](features/konyvtar.md).
- Hidden Folders uses the same new **Password Entry** window for its password. Use **Open** to unlock; changing or removing the password requires the current password. After you hide a folder, the program offers to let you set a password.
- The toolbar's **+** button opens **Album Properties** and creates an empty album, as in the original Picasa.
- **Timeline** now shows albums as cards too. Each card shows a month and year. When you exit, the library reopens the folder or album you last viewed. See [Viewing photos](features/nezegetes.md).

### Tags and search

- The **Tags** panel sorts tags by frequency, then by reverse alphabetical order. A tag's context menu shows its commands in the original order. See [Stars, captions, and tags](features/csillag-felirat-cimke.md).
- **Find Similar Pictures** now ranks results using the original Picasa method and returns up to 1,000 matches. See [Search and filters](features/kereses.md).

### Export and printing

- New: **Tools** ▸ **Experimental** ▸ **Publish via FTP...** uploads a web export to an FTP account. See [Export](features/exportalas.md).
- Export as HTML Page now remembers the destination folder and template.
- The **Print** window now offers **Normal** and **Optimized** modes. Optimized mode prints at full resolution. See [Printing](features/nyomtatas.md).

### Other

- The large color picker for effects, text, and collage backgrounds now matches the original Picasa layout: five recent colors, thirty swatches, and a color field. See [The editor](features/szerkeszto.md).
- When renaming one picture, the **Rename Files** window now opens with its current name selected.
- A frame saved from a video uses JPEG quality 85. While it is being saved, the viewer shows what it is doing.

## 2026-10-24

### Timeline and slideshow

- **View** ▸ **Timeline** (Ctrl+5) now works: an animated, full-screen presentation in which your folders follow one another as cards, arranged by date. Move between them with the slider or arrow keys; press Space to start a slideshow of a folder. See [Viewing photos](features/nezegetes.md).
- On a 16-bit or 32-bit display, **Timeline** appears in the slideshow bar in place of the transition selector, as in the original.
- Click the narrow strip at the very top of the displayed picture to pause or resume the slideshow.

### Printing

- The print-size list now offers every size from the original Picasa, in its original order, with both inches and centimeters. **CD Cover Size** is disabled. See [Printing](features/nyomtatas.md).
- The dialog starts with **Fill the page (crop)** selected, and the preview updates immediately when you change the fit.
- If all pictures are low quality, **Remove Low Quality Pictures** asks for confirmation first, because removing them also cancels printing.
- Printing a **Passport photo** keeps the selected number of copies. See [Passport photos](features/utlevelkep.md).

### Movies

- The **Slide Duration:** value defaults to 4 seconds and can be set from 1 to 300 seconds. The program remembers it, along with the selected transition style. See [Movies](features/mozgofilm.md).
- If no destination file is selected, the movie gets the original Picasa default name in the interface language (in Hungarian, <code>diavetites_jellegu_film</code>). The next movie uses the previous one's name and folder.
- **Recompute** always asks for confirmation, even if there is no text slide.
- Settings for movies made from faces have moved to a separate **Options** tab. See [People](features/emberek.md).

### Editing and tags

- A color picker beside the effects now has an eyedropper: click the picture to use the clicked pixel's color for the effect. See [The editor](features/szerkeszto.md).
- If keeping recent tags is turned off in Quick Tags, quick-tagging no longer adds the tag to the recent list.

### Files and dates

- The **Example:** row in **Rename Files** now shows the fixed sample from the original Picasa. See [File operations](features/fajlmuveletek.md).
- The date editor is titled **Adjust Photo Date** for one picture, and includes the number of items for several. It also shows when it is saving. See [The Library](features/konyvtar.md).

### On Windows

- The `Print Screen` key saves a screenshot in the <code>Screenshots</code> folder. This does not work on Linux. See [Keyboard shortcuts](features/billentyuk.md).

## 2026-10-23

### Slideshow

- Slideshow display time is now at most 20 seconds, as in the original Picasa (it used to be 30). At one second, the slider says “1 second.” See [Viewing: viewer, slideshow, video](features/nezegetes.md).
- The `◀` and `▶▶` buttons on the control bar now move as soon as you press them and do not repeat while held down.

### People and faces

- The **Cluster threshold:** slider on **Settings** ▸ **Name Tags** now starts at 85, as in the original. This does not change grouping: the previously saved value still applies, even though the slider may show a different number. See [Settings](features/beallitasok.md).

### Menus

- The **Tools** ▸ **Upload** submenu now opens and shows its original three commands (Google Photos, shared web albums, and YouTube). All three services have been discontinued, so the commands are disabled. See [Features not yet available](features/meg-nem-erheto-el.md).
- The discontinued **Upload to Picasa Web Albums...** command has been removed from the album context menu. It remains disabled in the picture context menu.

### Fixes

- If a thumbnail cannot temporarily be read from the cache, the program creates it again instead of marking the photo as damaged.

## 2026-10-22

### People and faces

- The search box in People Manager... and the name suggestions under faces now match the beginning of each word, as in the original Picasa. Typing “an” suggests both “Anna Kiss” and “Kiss Andrea.” Suggestions appear after the first keystroke, and you can choose one with the arrow keys. See [People and faces](features/emberek.md).
- The program asks before **Delete Person**. An empty name shows **Invalid Person**. When you add a person whose name or email address already exists, the program asks you to confirm. **Revert** is available only for a person you have changed.

### Settings

- **Detect duplicates while importing** is now selected by default on the **General** tab. See [Settings](features/beallitasok.md).
- The two email program choices on the **E-Mail** tab now appear in the original order, with **Let me choose each time I send pictures** first.
- The five size selectors on the **Print** tab no longer include FullPage, which has its own button. In metric locales, the defaults now match the original: 10 × 15, 13 × 18, 15 × 20, and 20 × 25 cm, plus **Contact Sheet**. See [Printing](features/nyomtatas.md).

### Posters

- Poster pages are always made as JPEGs, and their filenames put the column number before the row number, as in the original Picasa. See [Posters](features/poszter.md).

### Sorting and export

- Sorting by **Name** now follows the original Picasa order: names starting with accented letters come before names starting with A through Z. See [The Library](features/konyvtar.md).
- If a picture's metadata is too large, EXIF is omitted from the exported picture, as in the original. See [Export](features/exportalas.md).

### Fix

- After you rotate a picture with the Picture Tray's rotate button, its thumbnail immediately appears rotated in both the tray and the grid.

## 2026-10-21

### Renaming

- `F2` and **File** ▸ **Rename...** now open **Rename Files** for a single picture too, with the **Date** and **Image resolution** check boxes. Press Enter to rename; the picture remains selected afterward. See [File operations](features/fajlmuveletek.md).

### People and faces

- **Delete People Album** no longer removes the person from the list of names; it only removes that name from the person's faces. The confirmation window now matches the original Picasa (**Delete Album** / **Cancel**), and Enter activates Cancel. See [People and faces](features/emberek.md).
- The header of a person's album now shows the person's portrait and name as in the original, with a strip of faces below. The header also has **Remove** and a thumbnail-setting button.
- The ignored-face row (Ignored people) appears only in the ignored view, in place of Unnamed. The count in the group header now includes only visible rows.
- The Unnamed view's header, title, and name field now match the original. The view has a gray background and no longer slips under the left pane the first time it opens.
- Tiles for Unnamed and ignored faces now load even if the picture is not in the open album.

### Movies

- In a movie made from faces, every clip is framed around the face. **Remove Low Resolution Faces** skips faces that are too small. See [Movies](features/mozgofilm.md).
- The **Best Transitions** sort now puts pictures in capture-time order, as in the original Picasa.

### Slideshow

- Cropping during **Pan and Zoom** in the slideshow is now closer to the original Picasa.

## 2026-10-19

### Movies

- Movie Maker now opens as a tab in the main window beside the Library, like the collage page, instead of in a separate window. The tab is called **Movie Maker**. Settings are on three tabs at the left, with the preview on the right, and the player controls and filmstrip at the bottom. Use **Get more...** on the Clips tab to collect pictures in the library; the button above the tray, **Back to Movie Maker**, returns you to the movie. See [Movies](features/mozgofilm.md).
- The preview's actual-size (1:1) mode is now on by default, and the program remembers if you turn it off.
- Without an audio track, the **Delete** button and audio settings list are disabled.

### People and faces

- In the **Unnamed** name suggestions, clicking a person now immediately assigns that name to the face. See [People and faces](features/emberek.md).
- The ignored-faces view header says **Ignored people** and shows the number of faces. **Stop ignoring** appears only when a face is selected.
- The number of ignored faces in the left pane updates immediately after you ignore one.
- The Unnamed header buttons now use the original Picasa font size and are gray when unavailable.
- When you select a person's album, the tray shows the person's portrait and the selected album's picture count, as it does for other albums.

### Editing and effects

- Brightness, sharpness, and saturation adjustments saved by the old Picasa as directed edits now appear on the picture.
- If a picture's saved edits contain an effect the program does not recognize, later edits are no longer applied, as in the original Picasa.
- The old Picasa's rainbow-bar effect now appears on the picture when it was applied there.
- The background color shows through transparent parts of the **Polaroid** frame if an earlier effect left a transparent area.

### Other

- The program now calls itself **PicasaPy** everywhere. References to the original Picasa, such as when importing data, still say Picasa. The inflected form of the name was also fixed in several languages.
- The map in the Places panel now shows the original Picasa loading indicator while it loads.
- The size of the current selection in the status bar now uses a suitable unit: bytes, KB, MB, GB, or TB.

## 2026-10-18

### People and faces

- In the **People** panel on the right, pressing Enter on an existing name assigns it to the face immediately; the People Manager... window opens only for a new name. In the **Unnamed** album, the window still opens every time. See [People and faces](features/emberek.md).
- Expanded groups in Unnamed now have a **Type a name** field and an **Ignore Selected** button in the header, so you can name or set aside several selected faces at once.
- The **Learn more...** button in the welcome window opens the original Picasa help page in your browser, in the interface language.
- A broken face entry no longer hides the picture's other faces, and a named face no longer appears a second time as unnamed.
- Shift-clicking **Reset Faces** now clears every name and puts the faces back in Unnamed. Faces you ignored remain ignored.
- Contacts from the old Picasa now show the same name throughout the interface.
- Searching in People Manager... now clears the selection from people who are removed by the filter.

### Importing old Picasa data

- The import now includes faces that the old Picasa could not link to a person; they go into Unnamed. It also fills in faces missing from a picture even when that picture already has face data. See [Import](features/importalas.md).

### Slideshow and movies

- The slideshow transition selector now offers the original seven Picasa transitions: Cut, Pan and Zoom, Dissolve, Wipe, Circle, Push, and Square. **Pan and Zoom** now moves between two random crops instead of always zooming toward the center. See [Viewing photos](features/nezegetes.md).
- **Best Transitions** in Movie Maker now takes picture capture times into account and is the default for a new movie. See [Movies](features/mozgofilm.md).

### Saving and restoring

- A progress indicator (**Reverting Files.**) now appears during **File** ▸ **Revert**. A disk error displays an error message. The command is available as soon as saving finishes. See [Saving](features/mentes.md).
- On Windows, saving no longer fails if another process, such as thumbnail generation, briefly has the picture open.

### Library, search, and files

- Search now suggests albums as well as folders. The list opens below the field at the same width, and album matches are grouped under Albums. See [Search](features/kereses.md).
- A folder deleted outside the program now disappears from the left pane, including on Windows. See [The Library](features/konyvtar.md).
- In the **Rename** window, Enter accepts the change and Esc cancels it.
- On Linux, **Open With** in a picture's context menu is now a submenu listing the programs associated with that picture type. Two context menu commands now use their original labels: **Undo all Edits** and **Block from Uploading**. The latter refers to a discontinued service and remains disabled. See [File operations](features/fajlmuveletek.md).

### Other

- The first-run language prompt now uses the original English question and the program icon. If you choose Yes, the interface continues to follow the system language. See [Settings](features/beallitasok.md).
- The size selected in **Settings** for webcam capture is now actually applied. See [Import](features/importalas.md).

## 2026-10-17

### People and faces

- The **Unnamed** album now follows the original Picasa layout. The first time you open it, a welcome window appears. Each face has its own name field, which suggests existing people with their portraits as you type. The header and left pane show the number of faces, and Unnamed appears first in the People group. See [People and faces](features/emberek.md).
- Naming a face, whether in Unnamed or in the People panel, always opens People Manager... If a person with that name already exists, it is selected; click **Choose** to assign the face.
- You can also name an unnamed face by dragging it onto a named person in the People panel.
- **Set as People Album Thumbnail** now works: you can choose the portrait shown beside the person's name.
- The People album context menu has new **Invert Selection** and **Refresh Thumbnails** commands. Selection commands now show their keyboard shortcuts too.

### Library, folders, and albums

- **Split Folder Here...** now works: every picture from the selected one to the end of the folder moves to a new sibling folder. See [The Library](features/konyvtar.md).
- **Sort Album By** now works: you can sort an album's pictures once by date, name, or size, and the order is saved.
- **Sort Folder By** in a folder's context menu now sorts the folder's pictures once and saves that order as the manual order. Sorting by name treats numbers as numbers.
- **Folder** ▸ **Sort by recent changes** can be clicked again.
- Dragging works across the interface: drag selected pictures onto a folder in the left pane to move them there, even in Tree View; onto an album to add them; and onto the tray to keep them there. You can move a folder onto another folder and rearrange an album's pictures by dragging. Pictures dropped back in their original position keep their order. See [File operations](features/fajlmuveletek.md).
- In Tree View, the arrow beside a folder once again expands or collapses its branch.
- Hold Ctrl+Alt to show a large preview of the selected picture in a separate window, when the grid is wide enough.
- **View** ▸ **Search Options** now works. It opens and closes the same panel as the button beside the search field. See [Search](features/kereses.md).
- The **Properties** panel now has rows for **File Date**, **CCD Width**, **Aperture**, **JPEG Quality**, and **People Tags**.
- Adjust Date and Time... no longer changes the file's on-disk timestamps. For movies and other files that cannot store a date, the program records the new date in its own catalog and shows it after a restart.
- Removing a picture from **Starred photos** only removes its star; the file stays on disk.

### Viewing

- In the viewer, `Ctrl+F9` keeps moving through pictures to the end of the folder. See [Viewing photos](features/nezegetes.md).
- When single-click exit is off, Enter returns from a still picture to the library.
- **Undo all Edits** now works again in the photo context menu and in the viewer.

### Editing and movies

- **Retouch** now matches the brightness and color of the area around a blemish, so the repair blends in. See [The editor](features/szerkeszto.md).
- In **Add Custom Aspect Ratio**, you can enter a fractional value with a decimal comma.
- The **I'm Feeling Lucky**, **Scrolling Credits**, and **Caption - Typewriter** text slides now move in movies. See [Movies](features/mozgofilm.md).
- Several effects, including **Film Grain** and **Border**, now match the original Picasa more closely.

### Import

- **Import from Picasa** now also brings in the manual picture order of folders and albums, and the modified dates and locations of movies. See [Import](features/importalas.md).

### Settings and interface

- The logging level now works on **Settings** ▸ **Network**. See [Settings](features/beallitasok.md).
- The interface is now complete in all 41 languages, including standard buttons in dialogs.
- The four buttons in **Configure Buttons** are visible and clickable again.
- Titles are visible in the Help topic list again. Clicking a topic switches its content and starts at the top.
- The main window remains usable while startup checks network folders, and shows which step is in progress.

## 2026-10-13

### Hidden folders

- Hidden folders are recorded in the folder's own <code>.picasa.ini</code>, as in Picasa. They stay hidden when the program rescans the library, and folders hidden in Picasa appear hidden here too.
- Pictures in hidden folders stay hidden elsewhere too. Search, filters, People view, Timeline, albums, the map, slideshow, screensaver, and Picture Tray all leave them out unless **View** ▸ **Hidden Pictures** is turned on. See [The Library](features/konyvtar.md).
- **Import from Picasa** also brings in the old Picasa hidden-folder password if you have not set one here. See [Import](features/importalas.md).

### File operations

- When renaming several files, **Date** now adds both the capture date and time to the name, replacing forbidden characters with hyphens. The name field rejects characters that are not allowed in filenames, and the two check boxes keep their settings. See [File operations](features/fajlmuveletek.md).
- In the viewer, **Ctrl+Delete** and the context menu command for a picture opened from an album or People album now remove it from the album instead of deleting it from disk. See [Viewing photos](features/nezegetes.md).

### Library

- Small thumbnails beside folders in the left pane now appear faster at startup.

## 2026-10-12

### Keyboard shortcuts

- `F3` moves to the search field (like Ctrl+F). `F4` adds a star to the selected pictures or removes their stars. See [Keyboard shortcuts](features/billentyuk.md).

### Import and export

- You can now import individual files too. Choose **Folder...** or **Files...** from the menu on the **Browse...** button. See [Import](features/importalas.md).
- HTML export now has one size selector, set to 640 pixels by default. Movies can appear on the page as a **First frame** or as a **Full movie**. The two shadow check boxes are gone; the template supplies the shadow. See [Export](features/exportalas.md).

### Editing

- On the Effects tab, pressing Shift now switches the small preview for tiles that have two effects. See [Effects](features/effektek.md).
- The **Add Custom Aspect Ratio** window now uses the original labels. Custom ratios appear under **Custom Aspect Ratios**, and you can remove one with the trash button beside the list. See [The editor](features/szerkeszto.md).
- The icons on the editor tab bar now match the original size and design.

### People and movies

- The People panel header shows when face search is still running in the background on selected pictures and how many files remain unchecked. See [People](features/emberek.md).
- Movie Maker's preview now plays the selected transition, and text slides update while you type. See [Movies](features/mozgofilm.md).

## 2026-10-11

### Viewer and slideshow

- When you zoom in, a navigator window in the corner shows which part of the picture is visible. Drag its blue frame to move around. See [Viewing photos](features/nezegetes.md).
- The slideshow transition selector now offers all 22 transitions from the original Picasa, including Wipe, Push, Circle, Square, and Accelerate.
- A video opened in the viewer starts playing automatically.
- On Windows and macOS, **Export Clip** saves the trimmed segment as an MP4 file. Linux is still unsupported.

### Editing

- The editor buttons and effect tiles now show the original Picasa tooltips when you point to them. See [The editor](features/szerkeszto.md).
- You can choose colors for text, outlines, and effects from a full color picker. Recent colors are available for the Text tool too.
- **Redeye** now draws a box around eyes fixed automatically. You can undo these fixes one by one, and **Reset** also undoes the automatic fixes.
- Three quick crop buttons that were not in the original have been removed from **Crop**. Suggested crops remain.
- The **Comicize** sliders now have their original names: **Color Brush**, **Dot Density**, and **Dot Fade**. See [Effects](features/effektek.md).

### People, places, and tags

- In the People panel, you can accept a suggested name for an unnamed face with the ✓ button or dismiss it with ✗. A **Add a person manually** button and instructions are now available too. See [People and faces](features/emberek.md).
- When there are no unnamed faces, the People panel shows the original instructions.
- Markers on the **Places** map now show thumbnails and open a popup when clicked, with Find these photos in Picasa and **Erase location info**. After confirmation, you can drag pictures from the grid to the map to assign a location. The panel shows “Loading map...” while it loads and an error if you are offline. See [Places](features/helyek.md).
- The **+** and gear buttons in the Tags panel now have tooltips, and the quick-tag row says **Quick Tags:**. See [Stars, captions, and tags](features/csillag-felirat-cimke.md).
- The **Keywords** button in the Properties panel opens the **Tags** window. For movies, the panel also shows their format, frame rate, and duration. See [The Library](features/konyvtar.md).

### Library and menus

- **Delete Album** now works in an album's context menu. After confirmation, the album is removed from every folder, while the pictures remain.
- A calendar opens beside the **Date** field in **Folder Properties**, and the date is shown in your language's format.
- The **View** ▸ **Folder View** menu (and the ▾ button) now includes the three People sorting options and the **Shortcuts** submenu.
- **Open With** in a picture's context menu lets you choose a program to open the picture. See [File operations](features/fajlmuveletek.md).
- You can right-click the Picture Tray's output buttons to open **Configure Buttons...**.

### Import, email, printing, and old data

- Import can use a connected memory card or USB drive as a source (**Removable drives**). Import does not start if you enter a folder name but leave it empty, and the name can contain only one folder name. See [Import](features/importalas.md).
- **Import from Picasa** works with a Picasa 2 data folder you select manually, including one accessed through a mapped drive.
- On Windows, email now attaches pictures through the standard interface of your email program. See [Email](features/email.md).
- The Print window now fits its contents. **Print** and **Close** are always visible, and on a computer without a printer the window explains what to do. See [Printing](features/nyomtatas.md).
- The old file named <code>Picasa.ini</code> is migrated into the new <code>.picasa.ini</code> the first time you save. Backup and move-and-import operations preserve it too.
- When launched from source, the program now builds interface translations on its own. See [Getting started](getting-started.md).

## 2026-10-10

### New features

- Pictures can now be restored from a backup folder or ISO image set inside the program. Choose Restore from **Tools** ▸ Back Up Pictures...; existing files are not overwritten. See [Backing up pictures](features/biztonsagi-mentes.md).
- Web export now offers your own <code>.tpl</code> templates too. See [Export](features/exportalas.md).
- You can add several text boxes to one picture with the **Text** tool. Click an existing box to select and edit it. The font list now shows the font families installed on your computer. See [The editor](features/szerkeszto.md).

### Viewer

- `F11` switches the viewer to full screen; press it again to return. See [Viewing photos](features/nezegetes.md).
- Hold `◀` or `▶` to keep moving through pictures.
- The filmstrip has seven slots and keeps the picture you are viewing in the center, outlined with two colors.
- For a video, a video panel replaces the tab bar on the left. It has commands to restore the trim (with confirmation), take a snapshot, and export a clip.
- The full-screen startup option in **Tools** ▸ **Configure Photo Viewer...** now takes effect without a restart. See [Settings](features/beallitasok.md).

### Editing and effects

- **Redeye** warns when a picture has been rotated with Straighten. Automatic redeye correction no longer gets stuck on an invalid eye location.
- The **Crop** aspect-ratio list now shows the pixel dimensions of the frame and picture.
- The **Retouch** brush circle now appears on the picture at the cursor, target, and source.
- The text alignment buttons now have three distinct symbols.
- Holding Shift on the Glow tile opens a separate slider panel with **Intensity** and **Radius**. **Graduated Tint** now uses 0.25 for **Feather** by default; **Focal BW** has a **Size** slider. The color swatches for Polaroid, 1960s, and Rounded Edges are called **Background Color**. See [Effects](features/effektek.md).
- Effect tiles now show the updated picture after you apply an effect.

### People and places

- Click a recognized, unnamed face in the viewer to open a frame and a **Type a name** field. See [People and faces](features/emberek.md).
- The People album context menu now has **Delete People Album** (with confirmation) and **Edit People Album...**.
- **Add name tags** in a folder or album context menu now searches for faces only in that folder or album's pictures.
- Selecting suggestions in a person's album now works on Windows too.
- Click a marker in **Places** to show pictures connected to that location in the grid. The search field says **Search**. See [Places](features/helyek.md).

### Library, search, and menus

- You can use the keyboard to navigate suggestions under the search bar (`↓`/`↑`, `Enter`, `Esc`). After searching, click **Back to View All** in the green bar to leave the search. See [Search](features/kereses.md).
- Only active filters are now shown as enabled. The age filter resets when you switch views, and the nonfunctional “▤” icon has been removed.
- In Tree View, right-clicking a folder row with pictures opens the full folder menu. See [The Library](features/konyvtar.md).
- Check marks in the **View** menu now show which thumbnail options are active.
- In Album and People views, **Folder** ▸ **Hide** and **Unhide** are disabled.
- More... shows buttons that do not fit in a vertical column. The Picture Tray's ★ button tooltip now appears above the star.
- Right-clicking the Properties panel opens the Tags panel.
- Stars and captions are now read from the old <code>Picasa.ini</code> file too. See [Stars, captions, and tags](features/csillag-felirat-cimke.md).
- **Picture** ▸ **Batch Edit** now follows the original order, with **Rename...** (F2) first. See [Batch editing](features/csoportos-szerkesztes.md).
- Commands in **Tools** ▸ **Experimental** are now in their original order.
- PicasaPy's own menu commands now have a blue marker. See [Getting started](getting-started.md).
- **Help** ▸ **Keyboard Shortcuts** opens a list of working shortcuts. **Help** ▸ **Check for Updates** is disabled because that service has ended. See [Keyboard shortcuts](features/billentyuk.md).

### Movies, screensaver, wallpaper, and email

- Movie Maker's preview now shows the transition and text slide, and plays the audio track with a volume slider. A movie button now appears beside the collage button in a folder header. Album music plays during the album's slideshow and movie. See [Movies](features/mozgofilm.md).
- In an album view, the program asks before adding pictures to the screensaver. See [Screensaver](features/kepernyovedo.md).
- The desktop wallpaper is now made from the edited picture in its correct orientation. See [Desktop wallpaper](features/hatterkep.md).
- Temporary picture copies made for email are deleted when the program starts. See [Email](features/email.md).

## 2026-10-09

### Editing and effects

- For effects that focus on a point—Soft Focus, Focal BW, Graduated Tint, Radial Tint, Focal Zoom, and Focal Pixelate—you can drag the focus point on the picture, and the Center sliders follow it. See [Effects](features/effektek.md).
- You can choose a color for **Tint** with **Tint Color**. The default is light blue, as in the original.
- The **Pencil Sketch** panel has **Radius**, **Strength**, and **Fade** sliders.
- New commands in **Picture** ▸ **Batch Edit**: **Sepia** and **BW**. See [Batch editing](features/csoportos-szerkesztes.md).
- In Edit View, `Ctrl+9` hides or shows the panel on the left.

### Viewer and menus

- In the open viewer, **File**, **Edit**, and **Picture** menus now act on the open picture and are enabled. See [Viewing photos](features/nezegetes.md).
- **View** ▸ **Library View** returns from the viewer to the library.
- On Windows, double-clicking closes the viewer even when single-click exit is enabled, and the viewer does not reopen. After saving, the viewer shows the saved picture.
- In Album view, the **Folder** menu is replaced by **Album**, with **Edit Album Description...**. See [The Library](features/konyvtar.md).
- **Picture** ▸ **Hide** no longer reveals pictures that are already hidden in the selection.
- `F5` refreshes the open folder and search results.
- With nothing selected, `Ctrl+Enter` shows the open folder in the file manager, and `Ctrl+Shift+P` opens contact-sheet printing for the folder. See [Keyboard shortcuts](features/billentyuk.md).
- **Tools** ▸ **Experimental** ▸ Search for... now has a seventh command, **BW** color search. See [Search](features/kereses.md).

### People and faces

- Naming a face in the People panel now opens People Manager... for a new name. The new person is created only after confirmation.
- Ctrl-clicking or Shift-clicking **Picture** ▸ **Reset Faces** now affects the whole library and shows a warning first. On Windows, it also works correctly for selected pictures. See [People](features/emberek.md).
- After face search, the program groups faces automatically when suggestions are enabled.
- Write faces to XMP... first asks whether to apply to selected pictures, pictures with faces, or all pictures.
- A new button in a person's album header selects all pictures with suggestions at once.

### Movies

- **Create** ▸ **Movie** ▸ **From People Albums...** makes a movie from pictures across all People albums. See [Movies](features/mozgofilm.md).
- If you make another movie in the same window, the program asks whether to replace the existing one or create a new one.
- **Show Captions** uses captions written in PicasaPy. A description in the file is used only when there is no picture caption.

### Printing, posters, wallpaper, and email

- Printing and posters now use the edited picture in its correct orientation. See [Printing](features/nyomtatas.md) and [Posters](features/poszter.md).
- Desktop wallpaper now works on KDE Plasma and labwc/Sway desktops. See [Desktop wallpaper](features/hatterkep.md).
- Email now reports when no email program is configured. **Auto-Complete** in the To field's context menu is now a checkable option, and the program remembers your choice. See [Email](features/email.md).

### Library

- **Tools** ▸ **Adjust Date and Time...** now updates the picture file's EXIF date and file time, as in the original, for JPEG pictures. Other programs see the new date too. See [The Library](features/konyvtar.md).
- A folder's collection assignment is stored in its <code>.picasa.ini</code>, so it moves with the folder.
- On Windows, the program now detects a folder rename that changes only uppercase or lowercase letters.
- If startup runs into trouble, the error log now shows how far the program got. See [Frequently asked questions](faq.md).

## 2026-10-08

### New features

- **Create** ▸ **Make a Poster...** splits a picture across several pages so you can print it large. See [Posters](features/poszter.md).
- **Create** ▸ **Add to Screensaver...** and **Tools** ▸ **Configure Screensaver...** now work on Linux too. See [Screensaver](features/kepernyovedo.md).
- **File** ▸ **E-Mail...** (Ctrl+E) opens an email composer with fields for recipients, subject, and attachments. Full-size attachments use the edited picture too. For a video, you can attach its first frame or the whole movie. See [Email](features/email.md).
- **File** ▸ **Open File(s) in an Editor** (Ctrl+Shift+O) opens pictures in the system's default program. See [File operations](features/fajlmuveletek.md).
- **Tools** ▸ **Adjust Date and Time...** changes the selected pictures' dates. The new date is also used in exports. See [The Library](features/konyvtar.md).
- You can capture from a webcam with the `◉` button on the toolbar. See [Import](features/importalas.md).
- Movie Maker now has three tabs, transitions, sizes, an audio track, text slides, and a filmstrip editor. It asks before discarding manually added slides. See [Movies](features/mozgofilm.md).

### Settings

- Six of the eight **Settings** tabs now work: **General**, **File Types**, **E-Mail**, **Slideshow**, **Name Tags**, and **Print**. See [Settings](features/beallitasok.md).
- The language selector now offers all 41 languages, and the program offers the system language on first launch.
- New: **Tools** ▸ **Configure Photo Viewer...**, with a **Use Color Management** option.
- Import now suggests the destination folder set in Settings. See [Import](features/importalas.md).

### People and faces

- The **People** panel on the right shows faces from the selected picture, and you can name an unknown face there. See [People](features/emberek.md).
- **Tools** ▸ People Manager... now opens.
- **Picture** ▸ **Reset Faces** now works: it removes faces from selected pictures and then searches for them again.
- Face recognition is installed with the program, works without a download, and runs in the background by default. It no longer mistakes landscape features for faces.
- The movie button in a People album and the face-based command under **Create** ▸ **Movie** open Movie Maker.
- The “database is locked” error is gone. If the database is busy, the program tells you and retries on its own. See [Frequently asked questions](faq.md).

### Library

- You can rename a folder in **Folder Properties** by changing its **Name**. You can also choose music for the folder's slideshow and movie. See [The Library](features/konyvtar.md).
- **View** ▸ **Small Pictures** hides small pictures by default, as in the original Picasa.
- **Folder** ▸ **Hide Folder** and **Unhide Folder**, as well as **Picture** ▸ **Unhide**, now work.
- The left pane's context menu now has **Show Thumbnails in Library** and **Shortcuts** ▸ **Desktop**.
- Pictures dragged from the grid or tray into another program are sent as files.
- In Album view, delete, move, and remove commands in the **Folder** menu are disabled, so they cannot accidentally affect the folder you viewed earlier.
- **View** ▸ **Edit View** and **Picture** ▸ **View and Edit** (Ctrl+3) open the selected picture in the viewer.

### Viewing

- In side-by-side view, paging, captions, deleting, and mirroring apply to the selected side's picture. See [Viewing photos](features/nezegetes.md).
- With single-click exit on, you can return to the library from a still picture with one click.
- The slideshow follows a picture when it is deleted or reordered.
- Videos now have **Display Photo at actual size** and **Play full screen** buttons, and the trimming bar says **Start Point** and **End Point**.
- **View** ▸ **Display Mode** ▸ **16-bit (dithered)** now works.

### Editor

- **Straighten** now shows a grid and has **APPLY** and **CANCEL** buttons. Changes are saved only when you click Apply. See [The editor](features/szerkeszto.md).
- **View** ▸ **Show Edit Controls** hides or shows the left panel, and the program remembers your choice.
- The color picker remembers the five most recent colors.
- Automatic redeye correction now works only on the eyes of recognized faces.
- **Picture** ▸ **Batch Edit** ▸ **Show Text** now works. See [Batch editing](features/csoportos-szerkesztes.md).
- Effects now look even closer to the original Picasa.

### Captions, tags, and files

- **Paste Text** asks before replacing an existing picture caption. See [Stars, captions, and tags](features/csillag-felirat-cimke.md).
- Before tagging more than 30 pictures, the program asks for confirmation.
- Moving files never overwrites an existing destination file. If batch renaming partly fails, the program names the files it did rename. See [File operations](features/fajlmuveletek.md).
- Save, restore, and undoing a save refresh the view; errors now open an error window. See [Saving](features/mentes.md).

### Printing and export

- Quality is shown beside each picture as Best, Good, or Bad. If a picture is too small, you can remove it, print it anyway, or choose another size. See [Printing](features/nyomtatas.md).
- The size list now uses metric or inch units according to your system locale. New sizes include 3 × 4 and 4 × 5 inches, and 15 × 20 cm.
- **Maximum** export quality saves full color resolution. Exported pictures now get updated metadata and a thumbnail. See [Export](features/exportalas.md).

### Search and places

- The panel beside the search field now has **Show only photos with faces** and **Show duplicate files only** buttons. See [Search and filters](features/kereses.md).
- The Places panel now has a **Search for an address:** field and a map type selector. See [Places and geotags](features/helyek.md).

### Keyboard

- Keyboard shortcuts no longer fire while you are typing. Ctrl+E and Ctrl+H are new. See [Keyboard shortcuts](features/billentyuk.md).

## 2026-09-28

### New: passport photos

- **Tools** ▸ **Experimental** ▸ **Passport photo...** finds the face in a selected picture and crops a square around it, leaving space above the head and room for the shoulders below. It opens the print view with the **Passport** print size (2 × 2 inches). The picture itself is not changed; the crop is made in a temporary file. The program tells you if there is no face or more than one face. See [Passport photos](features/utlevelkep.md).

### Printing

- Print sizes and **Contact Sheet** are now in a single list. The separate layout selector has been removed because the original Picasa did not have one. Contact Sheet is the last item. When you choose it, a column-count field appears, and the number-of-copies, small preview, and two picture-quality rows disappear because they do not apply to contact sheets.
- The list offers six metric sizes in the Hungarian interface (5 × 8, 9 × 13, 10 × 15, 13 × 18, and 20 × 25 cm, plus FullPage), or six inch sizes in English. The inch list used to have five sizes and was missing full page.
- The dialog opens at **FullPage** by default, as in the original.
- Contact Sheet mode is no longer sticky: after you close it, the next Ctrl+P opens size-based printing again. See [Printing](features/nyomtatas.md).

### Viewer: two pictures side by side

- In side-by-side mode, **Show two different pictures** now puts the picture you were viewing on the left and the next picture on the right. The left picture is selected. This used to be reversed.
- The selected side is now used throughout: zoom, face frames, editor tools, and the blue information strip at the bottom all belong to the selected picture. You can switch focus by clicking the other picture beside the segment control.
- If you have started work in an open tool (Crop, Retouch, Text, or Redeye), the program no longer discards it silently. A **Confirm Edit** prompt asks whether to apply or discard changes; you can silence it with “Don't ask me again.” The prompt also appears when entering side-by-side mode or switching focus. When switching focus, there is a **Cancel** option too.
- The live preview on the fine-tuning sliders now appears for portrait pictures too, and in side-by-side mode it is drawn on the focused side.
- 1:1 zoom is now accurate for rotated pictures too.
- The side-by-side buttons and **Selected** marker, zoom slider thickness and handle, top toolbar, and bottom bar now match the original Picasa design. The grid scrollbar has moved to the right edge. See [Viewing photos](features/nezegetes.md).

### Backing up pictures

- While the backup panel is open, the whole library shows only content that has not been backed up yet. The left pane is narrowed to folders that still have unbacked files (and their expanded parent folders in Tree View), while the grid shows only those files. A separate folder strip used to appear above the panel. Closing the panel restores everything, including the scroll position.
- The backup plan is prepared in a background thread, so the window no longer freezes while the program counts what will be copied. **Cancel** still works during this step; copying does not start.
- The button that starts a backup is called **Backup**, or **Burn** when there is no set. **Cancel** stops a copy already in progress.
- On Windows, detection of folders with unbacked files is now reliable. A different capitalization of a drive letter (C: or c:) no longer confuses the program. See [Backing up pictures](features/biztonsagi-mentes.md).

### People

- Ignoring a face is now also written to the picture's <code>.picasa.ini</code>, with the same marker as the original Picasa. The **Ignored people** album now includes faces you ignored in Picasa, and Picasa sees faces you ignore here as ignored too. See [People and faces](features/emberek.md).

### Deleting and removing

- **Remove from Album** now asks for confirmation (**Remove Items**). You can turn this off on **Settings** ▸ **General**; the option used to be disabled.
- The **Delete from Disk** prompt now says where the file will go: the Trash, or permanently if it cannot be moved there, for example on a network share. In the latter case, it also says that the action cannot be undone. See [File operations](features/fajlmuveletek.md).

### Settings

- The eight tabs no longer squeeze together until their labels are unreadable in a narrow window. The tab bar scrolls horizontally with `‹` and `›` arrows at its edges. Long Hungarian check-box labels now wrap instead of pushing the page wider. See [Settings](features/beallitasok.md).

### Effects: colors and geometry now match the original

The following effects now produce the same picture as the original Picasa. The same settings can therefore look different from earlier PicasaPy versions:

- **Film Grain** now uses a fixed pattern, so the same settings always produce the same picture, and its blending matches the original.
- **Night Vision**, **Holga-ish**, **Cinemascope**, and **1960s** now use the original random sequence for their noise layers. Their automatic contrast adjustment samples only a sparse set of pixels, as the original did. A thin dark or light detail therefore no longer shifts the tone of the whole picture. **Pencil Sketch** uses this contrast adjustment too.
- **Boost**, **Lomo-ish**, and **Cross Process** now apply brightness before contrast, as the original did.
- The **Orton-ish** brightness slider now moves in smaller steps, as its description says.
- **Border** now uses concentric curves at the corners, and the caption strip height follows the original calculation.
- **Polaroid** now uses the original shadow offset, surrounding margin, and rotation.
- **Pixelate** and **Focal Zoom** now break the picture into blocks using the original Picasa downsampling method, so the block edges and colors match too.

Face-data lines written to <code>.picasa.ini</code> now also match the original Picasa exactly, with no extra semicolon at the end.

## 2026-09-27

### Printing

- The print-size list now works as expected: the program places pictures in a grid on the paper, and fits as many as possible. For example, an A4 page can hold two 10 × 15 cm pictures. Pictures that do not fit move to the next page. Previously, each picture got its own page. The preview shows the actual page and can be paged through when there are several, so you can see how many sheets will be used.
- With **Auto** orientation, the paper stays in portrait orientation. The program rotates the print if that uses fewer pages. Previously, it rotated the paper.
- The two picture-quality rows use the original Picasa wording. If the settings do not result in valid printing, the error is now explained in Hungarian. See [Printing](features/nyomtatas.md).

### Backing up pictures

- Backups now run in a panel that slides out from the bottom of the library instead of a separate window, in the same place as Gift CD. Only one of these panels can be open at a time.
- New step: choose which folders to back up. Folders with files that have not been backed up appear above the panel, each with a check box. None is selected by default, so the backup does not start until you choose folders. Use **Select All Pictures** to select them with one click. The list is prepared in the background; Calculating... appears while it is being built.
- The button that starts a backup is now **Burn Disc**; it also starts a copy to a folder. The final message is always **Backup Complete**.
- The **Delete Set** prompt now includes the set's name. As in the original, you cannot delete the only set; you can only change it. See [Backing up pictures](features/biztonsagi-mentes.md).

### Viewer: the same picture twice

- The “show the same picture twice” mode in side-by-side view now gives you two independent edits. Both sides start from the picture's current state, and you can edit them separately to compare two versions. Previously, the left side showed the unedited picture and only the right side could be changed.
- When you exit, the program asks which version to keep (**Left** or **Right**, or **Top** or **Bottom**). **Cancel** does not discard anything. The question appears on every way out: changing modes, paging, closing the viewer, or exiting the program. Neither side's work is silently lost.
- An unfinished brush stroke stays with its side when you switch focus. If you have painted an effect with a brush and switch to the other side, the stroke remains where you left it. See [Viewing photos](features/nezegetes.md).

### People

- A new pair of controls in a person's album header switches between tiles zoomed in on the face and the whole picture. For a small face, the crop is read from the original file to keep it sharp.
- The **People** panel now has one header and one list, as in the original: the named people in the selected pictures. The separate “Also in these photos:” section is gone, and the header text changes to match the current view. See [People and faces](features/emberek.md).

### Editor

- **Focal Pixelate**, the Shift counterpart to Pixelate, now opens its own slider panel with **Strength**, **Radius**, **Edge Hardness**, and **Fade**, plus an Invert check box. You can drag the circle on the picture. Previously, it used only the program defaults.
- Five sliders whose maximum depends on picture size—Focal Pixelate's **Radius**, Focal Zoom's **Focal Size**, the **Corner Radius** for Rounded Edges and Border, and Border's **Caption Height**—are now stored in <code>.picasa.ini</code> as a percentage of their range, as in the original Picasa. This makes edits from the original display correctly. If you set these sliders in an earlier version of PicasaPy, those pictures may look different; adjust the sliders again. See [Effects](features/effektek.md).

### Effects matched to the original

The settings you already saved for these effects are unchanged; only the way they are rendered changes.

- **Tint**, **Cross Process**, and **Neon** now color pictures using the original Picasa method. The program calculates gray differently and uses a custom lookup table, so saturated blue and yellow areas show a clear difference.

### Language selection

- The **Language** selector and **Tools** ▸ **Language** menu now work like the original Picasa. The list starts with **System Default**, and languages appear in their own languages, such as English (US) and Magyar. The program asks before switching. The change takes effect the next time you start it; the running interface does not change language. See [Settings](features/beallitasok.md).

### Picture details

- The **Lens** row in the **Properties** panel now checks XMP data written to the picture first. Most editing programs store the lens name there. The camera identifier is resolved only if no name is present in the XMP data.
- The **Compression** row now recognizes 36 formats instead of four, including compression types for raw files. It shows the number for an unknown code. **White balance** works the same way; previously the row disappeared when the camera stored an unusual code.
- Some **Properties** values, such as **Orientation** and **Exposure Program**, appeared in English in the Hungarian interface—for example, “Normal” instead of “Normál.” This is fixed, as are the information strip and age filter labels. See [The Library](features/konyvtar.md).

### Captions and messages

- Twenty-five confirmation and warning messages now use the original Picasa wording. Changes that affect the help include: after saving, the button is **Undo Save** (formerly “Undo Last Save”); the prompt before discarding edits names the picture if redeye correction was applied; the prompt for files that cannot be loaded lists their filenames; and the collage replacement prompt explains that collages are saved in the Collages album.
- Thirty-nine labels in **Settings** now use the official wording too. The right side of **Folder Manager** also has its original instructions. See [Saving](features/mentes.md) and [Folder Manager](features/mappakezelo.md).

### Other

- In **Print**, **Folder Manager**, **Settings**, **Import from Source**, and Export as HTML Page windows, Shift+F1 opens the relevant help chapter; F1 opens the table of contents. Help appears in a separate window in front of the dialog. See [Built-in help](features/sugo.md).
- The **Unnamed** album now shows the original instructions under its header, including a “please wait” message while grouping is being calculated.
- The message and buttons in the “Get more” collection bar are now centered rather than aligned to the right edge.

## 2026-09-26

### Gift CD

- **Create** ▸ Create a Gift CD... is now available. It makes one disc image from the pictures collected in the Picture Tray. Choose a name (up to 16 characters) and picture size; the program puts the pictures, including their edits, in a folder called <code>Pictures</code> on the disc. Movies are copied unchanged. It does not burn a disc; you can burn the finished <code>.iso</code> with any disc-burning program or mount it. The **CD Done** window has a **Show CD** button that opens the file's location. See [Gift CD](features/ajandek-cd.md).

### Backup

- **New Set...** now lets you choose a backup format: **CD or DVD backup** creates disc image files, while the other type copies pictures into a folder. The choice is saved with the set, so you do not have to select it every time. For a CD/DVD backup, the program sets the destination for the disc images to <code>Pictures/Picasa Backup/ISO</code>.
- The **Backup** button starts the backup again. For a while, clicking it did nothing at all. See [Backing up pictures](features/biztonsagi-mentes.md).
- The button for choosing the destination folder is now called **Choose...**, the official wording.

### Effects matched to the original

The settings you already saved for these effects are unchanged; only the way they are rendered changes.

- **Soft Focus**, **Orton-ish**, **Pencil Sketch**, **Holga-ish**, **Lomo-ish**, and **Infrared Film** now use the same blur as the original Picasa. The result can look different, especially around the edges of the picture.
- **Soft Focus** no longer changes the picture at zero strength. It used to darken every pixel slightly even though no blur was needed.
- Where an effect blends two pictures together, such as Soft Focus or Pixelate, the calculation now follows the original Picasa formula. The result can differ by a shade or two, exactly as it did in the original.

### Faster

- The **Cross Process** preview is now prepared in the background, so the window does not freeze while it calculates. See [The editor](features/szerkeszto.md).

### Properties

- The **Lens** row in **Properties** now shows the real lens name for pictures from Nikon cameras too, not just the identifier, as it already did for Canon. If a lens is not in the list, the row shows a name built from its focal length and aperture, for example, 18-55mm f/3.5-5.6. See [The Library](features/konyvtar.md).

### Menus and labels

- Disabled menu commands now actually look gray, even when they are unavailable only because nothing is selected. Previously they looked black like active commands, so it was not clear that they would not respond.
- More labels now use the official Picasa wording. Changes that affect the help include: the slideshow bar says **Display Time** and shows “seconds” beside the number; the entry field in the Tags panel says “Enter a tag to add:”; and import destination selection offers **Enter Folder Title**, Date Created, and today's date.
- When adding a face manually, the on-screen instructions now say to finish by pressing Enter or clicking a suggested name. The redeye success message now explains that you can undo a change by clicking its box and select missed red eyes manually.

## 2026-09-25

### People

- You can now decide which suggestions to accept in a person's album one by one. Select pictures in the grid; the accept button changes to **Confirm** and applies only to suggestions for selected pictures. **Remove** works the same way. With nothing selected, both commands still apply to all suggestions. See [People and faces](features/emberek.md).

### Effects matched to the original

The settings you already saved for these effects are unchanged; only the way they are rendered changes.

- **Posterize** now chooses a few colors from the picture itself instead of replacing pixels with a fixed set of colors. The same setting can therefore produce different colors in different pictures. Edges between color patches are softer, as in the original.
- **Comicize** now follows the original effect, so the contours and halftone dots fall in different places.
- **Drop Shadow** transparency now matches the original. The difference in the picture is small.
- The program now renders smoothing left in an old picture's edits as the original did, even if there is no button for it in the current interface.

### Faster

- **Auto Contrast**, **Color Temperature**, **I'm Feeling Lucky**, and **Warmify** now finish much sooner. The picture follows the slider or click almost immediately. The result is the same; it is just ready sooner.

### Other

- **Back to Library** in the viewer now has a tooltip that explains what it does.
- Three more tooltips—the magnifier, the folder-view settings button, and the cancel button for “Get more”—now use the original Picasa wording.

## 2026-09-24

### Hidden folders

- You can now set the Hidden Folders password in the interface: right-click the Hidden Folders header in the left pane and choose **Set/Change Password...**. The password lock existed before, but there was no way to open it. See [The Library](features/konyvtar.md).

### Editor

- When you paint a paintable effect onto a picture with a brush (Boost, Pixelate, Soft Focus, or Tint), the saved file now shows the effect only where you painted it, including on rotated and mirrored pictures. Previously, the saved picture showed the effect across the whole image. (Export and the grid thumbnail still show it across the whole picture for now.)
- The **Pixelate** **Blend Mode** slider now changes the result. Previously, you could move it but the output did not change.

### Effects matched to the original

The settings you already saved for these effects are unchanged; only the way they are rendered changes.

- **Polaroid** now has the original white frame. **Outer Color** now colors the background behind the rotated picture instead of the frame. Positive values on the **Rotate** slider now rotate clockwise; they used to rotate the other way.
- **Infrared Film** now blends its green glow differently, so its result is much closer to the original Picasa.
- **1960s** now uses the original color curves, giving the picture a warmer, more faded base.
- **Cross Process** now preserves the picture's brightness during the final yellow tint, as the original did.
- **Radial Tint**, the Shift counterpart to Graduated Tint, now uses the same radial transition as **Soft Focus** and **Focal BW**, so the width of the soft edge matches the original.

## 2026-09-23

### People

- A person's album now shows suggestions that have not been decided yet, not only pictures that already have a name assigned. You can see what is done and what still needs your attention in one place.
- A new toggle button in the header, Show only suggestions (when toggled on), filters the grid to undecided pictures. Each time you open the album, the filter starts off.
  
### Editor

- The **Artistic** tab now has a Shift counterpart for the **Pixelate** tile: **Focal Pixelate**. Instead of pixelating the whole picture, it keeps a spot around one point sharp and pixelates more as you move away from it. Ten tiles now have a hidden counterpart.
- Small previews on several effect tiles used to show the unchanged picture. They now show what the effect actually does.
- The frame thickness for **Border** and **Museum Matte** is now proportional to the picture in both the editor preview and effect tiles, so the preview matches the saved picture.
- **Drop Shadow** now blurs the shadow by the same amount per pixel as the original Picasa.

### Picture details

- The **Lens** row in the **Properties** panel now shows the real lens name for pictures from Canon cameras, even when the file stores only an identifier. It uses the same list as the original Picasa. For other makers, the name in the file is still used for now.

### Other

- The progress window shown while saving a collage now follows the original Picasa layout and stays inside the canvas area.
- Old pictures edited with the **Blur** step in the original Picasa now appear here as they did there too. This effect has no button in the current interface; it occurs only in edits made to older pictures.

## 2026-09-22

### Menus

- Keyboard shortcuts in menus, such as Ctrl+Delete, now line up in a column at the right edge of each row, as in the original Picasa, instead of sticking to the end of the label.
- In Folder view, a picture's context menu no longer has empty space where album and People commands would be. Those commands appear only in Album and People views; elsewhere the menu closes up.

### Effects: closer to the original

- **Heat Map** no longer fades to gray. It now uses the same vivid heat-map colors as the original Picasa.
- **Duo-Tone** now distributes the transition between its two colors across the picture as the original did.
- **Drop Shadow** now enlarges the picture by exactly the amount needed for the shadow, which appears in the same place with the same blur as in the original.
- The **Highlights** and **Shadows** sliders in **Fine Tuning** now match the original Picasa. This is also visible on pictures edited earlier in Picasa.

## 2026-09-21

### Raw photos

- Pictures from .cr2, .nef, .arw, .dng, and other raw files now appear in the grid, large viewer, folder covers, and editor preview. You can export a raw file, find duplicates or colors in it, and use it in a collage, slideshow, or web export. Saving edits back to a raw file is still unsupported; the program shows an error. See [The Library](features/konyvtar.md).

### Sorting and folders

- **Manual order**: you can rearrange pictures in the grid with the mouse. The order is saved beside the folder, so it remains there and moves with the folder to another computer.
- A **Previous album** and **Next album** arrow at either end of the grid scrollbar jumps to the previous or next header. Hold it down to repeat.
- You can now choose where the folder tree starts in **View** ▸ **Folder View**: **My Computer**, **Pictures**, **My Documents**, or **Desktop**. The Folders label tells you where you are, and the choice is remembered until the next start.
- **New Album...** no longer asks for a name. It immediately creates an **Untitled** album, as in the original Picasa. You can edit the album's name, date, place, and description later with **Edit Album Description...**.

### In the viewer

- **Show two different pictures** now works for comparing two photos side by side. A new button switches between horizontal and vertical layout, and every command—including editing and adding to an album—acts on the selected side.
- You can now trim a video by setting its start and end points from the control bar, and restore the original trim. The video file itself is not changed; the trim points are saved in the same format used by the original Picasa.
- You can save the current video frame as a JPEG in the Captured Videos folder, at the video's own resolution.
- The slideshow control bar no longer disappears while you are using it, and the − and + buttons for slide time repeat while held down.

### Editing

- You can paint **Boost**, **Pixelate**, **Soft Focus**, and **Tint** onto a picture with a brush to choose where each effect applies. Use the eraser to take it back. (For now, painting appears only in the live preview; the saved picture still shows the effect over the whole image.)
- Edits now run in the order you applied them. For example, sepia after a frame now colors the frame too, as in the original. What you see in the editor is what is saved to the file.
- The **Straighten** slider has moved above the picture. **Crop**, **Retouch**, **Text**, and **Redeye** keep their Apply/Cancel buttons in their own panels.
- The **Focal Zoom** sliders now use the original names, **Zoominess** and **Focal Size**, and focal size now follows the picture's dimensions.
- **Lomo-ish** and **Holga-ish** now have better dark edges. **Color Temperature** follows the original calculation, strongly brightened pictures no longer show stripes, and rotation and mirroring work together in the right direction.

### People

- From a person's album header, you can now approve all name suggestions or discard them.
- **Find more suggestions** lowers the recognition threshold once to find more possible names; it does not change the saved setting.

### Import and export

- **Tools** ▸ **Import from Picasa...** can bring names, keywords, and locations from the old Picasa database. Existing data is never overwritten, and you can repeat the import at any time.
- Backups can now be disc images in CD or DVD ISO format. If a collection does not fit on one disc, the program creates several numbered images. You do not need a disc burner; use any burning program to write the images to discs.
- When printing, you can set the caption source and position, font, colors, wrapping, and border. The current page number is shown while printing.

### Interface

- **Tools** ▸ **Configure Buttons...** lets you choose which buttons appear in the header above pictures and in what order.
- A background-task indicator appears in the upper-right corner only while the program is working. You can stop the current task there too.
- Display modes (black and white, sepia, projector, and gamma) now affect the whole interface, not just the photos.
- Startup is about one second faster: the collage editor is built only when you first open it.
- Tooltips now appear in many more places, with a consistent look and the same 0.6-second delay as the original Picasa.

### Database

- Moving the database now happens on the next start. The button schedules the move and can be undone; the copy runs at the next startup and does not require another restart. The old copy goes to the Recycle Bin.

## 2026-09-13

### Two pictures side by side in the viewer

- Three small segments now appear in the viewer's bottom bar. **Show the same picture twice** compares edits: the picture before editing is on the left and the current version is on the right. Use the fourth segment, **Switch focus between the pictures**, to switch sides. The active one says **Selected**.
- **Show two different pictures** is visible but disabled for now, so it does not look broken. See [Viewing photos](features/nezegetes.md).

### Use Color Management

- A new working option in **View** uses the color profile embedded in a picture, such as Adobe RGB, to adjust it for your screen. It is off by default, and your choice is remembered until the next start. Your picture files are unchanged. See [Settings](features/beallitasok.md).
- **Mac Gamma (1.6)** and **Linear Gamma (2.2)** used to produce the same result. This is fixed.

### Simplified Tree View

- **View** ▸ **Folder View** ▸ **Simplified Tree View** now actually filters the tree to show only branches with watched folders, as the original Picasa did. Previously, it only combined long paths and never hid a folder. Until the program knows which folders you watch, it keeps the whole tree. See [The Library](features/konyvtar.md).

### Backup

- Copying now runs in the background, so the window remains usable.
- A progress bar and a counter such as “Copying files (12/340)” show how far it has got.
- A new **Cancel** button stops a backup without losing work. The next run continues with the missing files.
- When you start a backup, the program now estimates how many CDs or DVDs would be needed. It still does not burn discs. See [Backing up pictures](features/biztonsagi-mentes.md).

### Editor

- Effects that take a lot of calculation—Sharpen, Film Grain, Glow, Comicize, Drop Shadow, HDR-ish, Holga-ish, Lomo-ish, Neon, Orton-ish, Pencil Sketch, and Posterize—now calculate in the background while you drag a slider. The window does not freeze; the picture updates when the calculation finishes, and the blue bar at the bottom shows that work is in progress.
- For effects that require full resolution, the preview is now made at the picture's original size before being reduced. You see the same result that will be saved.
- **Neon** now has a color picker so you can choose the glow color. It used to have an “Intensity” slider that actually controlled the strength of the effect.
- The two **Soft Focus** sliders now have accurate names: blur strength and effect strength. One was called “Radius” even though it changed something else. The tile is now named **Soften**; the help used to call it “Soft Focus” (translated from a different name).

### Collage

- Snap rotation alignment—the small button row on the left and **Align Rotation** submenu—now works in every layout, not just Picture Pile. It used to be disabled for grid layouts. See [Collages](features/kollazs.md).

### Right-hand drawer

- The drawer now slides open and closed, returning its space to the library when closed.
- A narrow, invisible strip along its edge also toggles it, so you can open or close it with the mouse as well as from the menu, tray, or Ctrl+0.

### Minor change

- View buttons, toolbar filters, editor tabs, and viewer navigation buttons now take effect when pressed, not released, as in the original Picasa.

### Windows installer

- Every release now has a setup program, <code>PicasaPy-Setup-&lt;version&gt;.exe</code>. Download and run it; you do not need to install Python. It adds a Start menu entry and, if you choose, a desktop shortcut. You can uninstall it from Programs and Features. See [Getting started](getting-started.md).

## 2026-09-12

### Backing up pictures: a new chapter

- **Tools** ▸ Back Up Pictures... now works. Create a named backup set that says where to save and what to include: all file types, all pictures without movies, or only JPEGs with camera data. The set remembers what it has copied, so later runs copy only new or changed files.
- The backup includes <code>.picasa.ini</code> files beside the pictures and puts a <code>files.txt</code> list in the destination root. The program cannot write to CDs or DVDs; the destination is always a folder. See [Backing up pictures](features/biztonsagi-mentes.md).

### Slideshow

- The slideshow now fills the whole window; the menu bar, toolbar, and Picture Tray disappear while it plays.
- You can choose a transition in the control bar: Cut, Dissolve, Dissolve Through Black, Dissolve Through White, or **Pan and Zoom**.
- Use the − and + buttons to set **Slide Duration:** from 1 to 30 seconds.
- A button cycles through three caption modes: show the caption, show the filename, or show neither.
- The program remembers all three choices for the next slideshow.
- A transition now shows the picture that was immediately before it, and the incoming picture inherits the outgoing slide's zoom and rotation.

### One right-hand drawer replaces four panes

- The Tags, People, Places, and Properties panels now switch inside the same drawer with one shared header. The header shows the current panel's name in the middle, **Switch between small/large side panel** on the left, and **Close this side panel** on the right.
- Previously, each of the four panels had its own width and header.

### Mirroring

- Two new shortcuts: `Ctrl+Shift+H` mirrors selected pictures horizontally, and `Ctrl+Shift+V` mirrors them vertically (in the viewer, the picture as you see it). Press the same shortcut again to undo the mirror. There is no menu command, as in the original Picasa.
- Mirroring is saved in the picture's <code>.picasa.ini</code>. It appears in thumbnails, saved pictures, exports, email attachments, and web exports.

### Sort by color

- **Sort Folder By** now has a fourth option, **Color**: colored pictures come first in rainbow order, followed by colorless ones.

### Web export

- There are now seven templates instead of one: three background colors (white, gray, black), each with plain and mat-framed tiles, plus a new XML template that writes one data file instead of a web page.
- Each template has a small preview illustration.
- The destination folder is filled in for you: Picasa HTML Exports inside your Pictures folder.

### Editor

- In **Redeye**, you can now remove one frame by clicking inside it. If frames overlap, the most recently added one is removed.
- Hold `Shift` while you are on the Effects tab to switch effect tiles immediately.
- The instructions in **Crop**, **Redeye**, and **Retouch** are now more complete. Retouch instructions explain that you can hold `Ctrl` and pan over a zoomed picture.
- Sepia, unsharp mask, vignette, and drop shadow now use the original Picasa calculations, so they look closer to the original.

### Security and warnings

- When you exit, the program asks if background work, such as export or face search, is still running. This also applies to the window's X button, and cannot be disabled.
- Choosing **Delete everything on card** during import now gives a detailed warning: how many files will be deleted, how many skipped as duplicates, and how many the program does not recognize. If the source has not been fully scanned yet, the program says so instead of guessing a number.
- The **Tags** panel now warns you before editing if the selection includes a write-protected picture.

### Settings

- The cache-clearing command on the **General** tab now works: the program asks first, then tells you how much space it freed. Thumbnails are recreated as needed.
- Smaller thumbnails now appear noticeably faster because they are generated at several sizes.

### Videos

- Five extensions used to be silently missed during scanning: .tp, .ts, .m2v, .ogg, and .ogv. Their files were in the folder but did not appear in the grid. The file chooser for adding videos now recognizes the same list.
- Playback now honors start and end points set for a video in the old Picasa: it jumps to the start and stops at the end. You still cannot set those points in the PicasaPy interface.

### Fixes

- Desktop wallpaper now works on Windows too.
- On a Wayland desktop, the program now explains that the <code>qt6-wayland</code> package is missing instead of stopping with an English error.
- Portrait orientation is now taken into account when displaying pictures. They fit correctly in a collage, 1:1 zoom is accurate, and the resolution label is correct.
- Folder rows in the left pane now show one thumbnail instead of a stack, and always show it in Tree View. The menu command is disabled there.
- **Paste Text** now applies a caption to the entire selection in one pass, so no picture is missed.
- The effect tile badge no longer shows the number “1” all the time; it is now in the corner of the tile.
- Capture details beside the histogram now use shorter, photography-style forms (6.7 mm, f/1.7, 2.5 s). Flash information appears only in Properties, as in the original Picasa.
- The right-hand drawer now aligns to the right edge, so its size toggle works in either direction.

## 2026-09-11

### Duplicates: a new, faster view

- **Tools** ▸ **Experimental** ▸ **Show Duplicate Files** now takes you to a filtered view instead of opening a window. The grid shows only pictures with duplicates. Leave with **Back to View All** in the green bar or the duplicate badge in the search bar. The shortcut is `Ctrl+F6`.
- The old duplicate manager is still available under a separate command, **Manage Duplicates...**.
- **Cancel** in the manager no longer gets stuck if the search finishes at that moment.

### Search

- The toolbar's time slider now works: drag it to the right to keep newer pictures in the grid. The green bar says what you filtered, for example, “Pictures up to 9 weeks old.” The left edge turns it off.
- Six colors can now be searched from a menu under **Tools** ▸ **Experimental** ▸ Search for....
- You can turn all search results into an album with **Tools** ▸ **Experimental** ▸ Save search results....
- You can now right-click the search field to use Paste, Copy, and other text commands.

### Tags and captions

- You can make a regular album from a tag with **Tools** ▸ **Experimental** ▸ **Show tag as album...**.
- **Edit** ▸ **Copy Text** and **Paste Text** now work. You can copy one picture caption across a whole series.
- The blue strip above the Picture Tray shows which tags are in the selection and how many pictures have each. Dates and sizes use a shorter form when the pictures are from the same day.

### Faces

- When you name a face, the program now writes the face's location and name beside the picture so other photo programs can recognize it. The picture file itself is unchanged.
- You can do this for a whole folder with **Tools** ▸ **Experimental** ▸ Write faces to XMP.... Progress is shown, and you can stop with **Cancel**.

### Desktop wallpaper

- A new help chapter explains this feature. **Create** ▸ Set as Desktop... sets a selected picture as your wallpaper. The **Desktop Background** button in the collage panel uses a collage instead. Both make a copy and center the picture.

### File operations

- **Edit** ▸ **Paste** (Ctrl+V) now works. Files copied to the clipboard are put in the selected folder. If a name is already taken, the files get new names; nothing is overwritten.

### New shortcuts

- `Ctrl+3` opens the selected picture in the viewer. `Ctrl+F6` opens the duplicate view, `Ctrl+F7` finds similar pictures, and `Ctrl+F8` clears the similarity sample. `Ctrl+Shift+B` converts selected pictures to black and white; `Ctrl+Shift+E` applies “I'm Feeling Lucky.”

### Appearance

- Entries in the left pane now have their own icons: folders are blue instead of yellow, regular albums are orange books, Starred photos is a green book with a star, project folders are purple books with a star, and tags are gray tags.
- When you select an album with no picture selected, the Picture Tray shows a cover picture and the number of pictures in it.
- Drop-down lists and scrollbars now match the original Picasa design.
- The interface fades behind questions that open in the editor, making it clear what needs an answer.
- Labels in the text overlay panel now sit beside their controls. The transparency slider is labeled **Transparency**.
- The **Invert Colors** tile now has the blue badge used for effects that apply with one click.

### Settings

- The **Detect duplicates while importing** check box on **Settings** ▸ **General** now works and shows the same setting as **Exclude Duplicates** in the importer.

### Speed

- Startup is a little faster. Some windows in the large view are now built only when they are needed.

## 2026-09-10

### File operations: interrupted moves no longer leave damage

- If moving a picture failed because the file was locked or the folder was write-protected, the copy used to remain at the destination while the original stayed in place. You ended up with two pictures and no warning about the extra copy. The program now removes the incomplete copy and leaves the picture where it was. The same protection applies when moving a file to the Trash, restoring it, or moving preserved originals.
- If moving a folder stopped partway through, a partly copied folder used to remain at the destination. The next attempt then stopped because a folder with that name already existed. Now nothing is created at the destination until copying has finished.

### Slideshow

- **View** ▸ **Display Mode**, including **Projector Mode**, now affects the slideshow too. Previously it was visible only in the large viewer and thumbnails, even though Projector Mode is for projection.

### Toolbar

- The `▾` button beside the two view buttons is back. It opens the folder view settings, the same menu as **View** ▸ **Folder View**, so the two locations cannot get out of sync.

### Collage

- **Align Rotation** in the right-click menu is now disabled for layouts that do not rotate (Mosaic, Frame Mosaic, Grid, Contact Sheet, and Multiple Exposure). The menu used to offer four angles even though clicking them did nothing. The program's behavior has not changed; the menu now shows what is available.
- In Picture Pile, pictures with white borders no longer exceed their allotted space. The border used to grow outward, making these pictures 5–10% too large. Polaroid frames and pictures without frames are unchanged.
- Collages and movies made in the old Picasa now appear automatically after a few seconds. On a network drive, they used to take minutes because the program received no notification of changes made by another computer.

### Minor changes

- When you drag pictures onto the albums list, the destination row now turns blue with white text, as in the original. Previously only the text turned green.
- Startup is slightly faster: seven confirmation windows are now built only when they are needed. The interface behavior is unchanged.

## 2026-09-09

### Faces: no more unnecessary rescanning

- Face search now remembers which pictures it has checked and skips them next time. It used to check pictures without faces again every time because it did not record that it had already scanned them. If a picture changes, it is checked again as expected.
- If you turn off face recognition for a folder in **Folder Manager**, the program asks when you click **OK**, then deletes faces it found in that folder and its subfolders. Names and face frames added in Picasa remain; they are your data.
- Pictures in a folder with face recognition turned off are marked so the search will not run on them again. The mark stays after you turn recognition back on, as it does in the original Picasa.

### Editor

- **Linear Blur** (on the Legacy Effects tab) used to do nothing for most pictures: the boundary between sharp and blurred areas always fell in the center, where the original Picasa leaves the picture alone. It now has a visible effect.
- **Glow**, **Soft Focus**, and **Linear Blur** now use the original Picasa blur calculation. They look closer to the original, though the difference is barely visible to the eye.

### Collage

- The **Contact Sheet** layout now follows the original Picasa's measured formula for cell size and vertical picture alignment.

### Saving

- Saving no longer writes an <code>originhash</code> line to the picture's <code>.picasa.ini</code>. The value written before was not in a format used by the original Picasa. Existing lines are still left untouched.

### Minor changes

- Slider handles now have diagonal shading, as in the original, and a suitable color in the dark theme.
- The **Undo** and **Redo** buttons no longer change height based on the system font. If the label does not fit, the text shrinks and wraps to at most two lines.
- The face-removal question in Folder Manager now says “skipped folders” instead of “excluded folders.”

## 2026-09-08

### Crop, redeye, and adding faces: constrain proportions with keys

- While drawing a new frame, hold `Shift` to constrain it to the picture's aspect ratio, `Ctrl` to make it one third wider, or `Alt` to make it half again as wide. Alt overrides everything; Ctrl overrides Shift. Releasing the key immediately frees the proportions.
- Shift uses the picture's own aspect ratio, not a square, as in the original Picasa.
- The same three keys work for redeye frames and when manually adding faces.

### Viewer: the blue information strip

- Text that does not fit now shortens instead of being cut off at the edge. The folder name is first removed from the filename; then an ellipsis appears in the middle of the filename. The end of the name, including its extension, stays visible.

### Effects and picture quality

- **Graduated Tint** now looks like the original Picasa. Stronger settings used to produce a noticeably different result.
- Thumbnails now use the original Picasa downsampling method, so large reductions look less jagged and show clearer details. Existing thumbnails remain as they are; the new method is visible for them only after the picture changes.
- **Comicize** is noticeably faster, with virtually no change to its appearance.
- On Windows, thumbnails sometimes used different smoothing in the importer, duplicate finder, and unnamed-face window than in the grid. This is fixed.

### Collages and movies

- Saving a collage or movie no longer rewrites the folder's Picasa data. It used to rewrite every line in <code>.picasa.ini</code>. In older non-Unicode files, accented captions turned into question marks, and the Picasa data header could be duplicated. Existing lines are now left unchanged.

## 2026-09-07

### Viewer: zoom

- The three zoom controls—Fit, **Display Photo at actual size**, and the slider—have moved to the bottom toolbar, before the panel buttons.
- **Display Photo at actual size** now uses the picture's real pixels. An internal limit used to allow zooming in three or four times too far.
- The slider's center is exactly 100% and snaps there, making it easier to find. Its right edge is 400%.

### Viewer: caption bar and information strip

- The caption bar now runs along the bottom of the picture, with the caption in the center and the delete button at the right.
- The on/off switch stays visible in the lower-left corner even when the bar is off; previously it was almost impossible to bring it back.
- The blue information strip now shows the date and tags, and again shows the picture's position in the sequence.

### The right-hand drawer is available while editing

- The Tags, People, and Places panels now also open in the editor. Previously their buttons looked pressed but nothing happened.

### Editor

- Nine effect tiles now switch to another effect if you hold Shift while changing tabs. The label switches too, so you can see what you will get. Examples include Sharpen → Sharpen (legacy) and Vignette → Matte. See [Effects](features/effektek.md) for the full list.
- The crop aspect-ratio list now matches the original Picasa: paper sizes in centimeters (5×8, 9×13, 10×15, 13×18, 20×25), A4, and screen ratios 4:3, 16:10, 16:9, and 5:3.
- **Comicize** now looks closer to the original Picasa.

### Library

- The grid's magnifier now shows a 1:1 crop from the full-resolution picture. It used to enlarge a reduced thumbnail.
- The program now recognizes .jpe pictures and .mpeg videos.
- The program records a file's timestamp on the first scan and does not update it later. Pictures without a capture date no longer jump around in the grid after each save or copy.

### Files and saving

- A backup copy made when saving now moves with the picture. **Restore** still works after renaming, moving, or copying it.
- A copy no longer takes over another picture's forgotten backup. Previously, a newly copied picture could end up with an unrelated picture's old version as its “original.”
- Snapshots from successive saves are now stored separately, so a picture whose own name ends in something like <code>…2.jpg</code> cannot accidentally be overwritten by another picture's old version.

### Errors that used to disappear silently

- If a folder is write-protected or the disk is full, the program now reports the error instead of showing a saved state on screen. This applies to folder descriptions, folder dates, keywords, and **Paste All Effects**.
- When reading old Picasa data files, the program now detects damaged or mixed-up columns and reports the problem instead of importing a wrong value.

### Testing

- **Help** ▸ **Send Log...** now always asks where to save the log, remembers the selected folder, and copies the file path to the clipboard. It used to save to a hard-coded network folder that most computers could not access.

### Minor changes

- Labels in checkable menu commands no longer overlap their check boxes.
- The Picture Tray's More... button now has its missing icon.
- The restored window size now respects the minimum, so Windows no longer shows a warning every time the program starts.
- The **Settings** ▸ **E-Mail** tab now uses the original Picasa wording for the mail-program choice.

## 2026-09-05

### Printing

- A new **Printer Setup** button opens the selected printer's own page setup window for paper size, orientation, and margins. Settings you accept there are used the next time you print. The button is disabled when printing to PDF.
- A line under the printer name tells you what paper will be used: its name, size in millimeters, and orientation.

### Text on pictures

- Font size now offers the original Picasa's sixteen sizes, from 8 to 96, instead of a percentage. The size follows the picture's height.
- Two saving problems are fixed: captions used to be saved in bold every time, and outline thickness was always lost. Both are now saved as set. The **Outline thickness** slider can be adjusted continuously.

### Editor

- Effect tile previews now use the picture's current state. If you have made it black and white, the tiles use that picture as their base. They used to show the raw photo.
- The range and default values of seven effect sliders now match the original Picasa. Some can now be dragged in the negative direction for the opposite effect, which was not available in the interface before.

### Keyboard

- `Ctrl+0` opens and closes the right-hand panel and remembers which tab was open. `Ctrl+F` moves to the search field; `Ctrl+K` opens the Tags panel.
- `Ctrl+Tab`, `Ctrl+Shift+Tab`, `Ctrl+←`, and `Ctrl+→` move between tabs in a loop. `Ctrl+W` closes the current project tab.
- On a slider, **+** or `=` increases the value; `−` or `_` decreases it.
- Most menu commands now have an underlined letter, as in the original Hungarian Picasa. Press it with `Alt` to open the menu.

### Menus

- The duplicate finder has moved under **Tools** ▸ **Experimental** and uses its original name, **Show Duplicate Files**. The database move command is now labeled **Choose database location...**.
- Check marks on checkable menu commands now reflect their state. A check mark used to turn off while the panel remained open.

### Library

- The program now detects and indexes WebP pictures.
- Point to a folder row to see the folder's full path in a tooltip, which helps distinguish folders with the same name.
- Folders containing pictures without a capture date now get a date from the file timestamp, so they are no longer undated in the grid.
- You can no longer drag the left pane narrower than the minimum used by the original Picasa.
- If all output buttons do not fit, a More... button appears at the end of the row, with the remaining buttons below it.

## 2026-09-04

### Help opens from the program

- Press `F1` or choose **Help** ▸ **Help Contents and Index** to open this help, even when offline.
- **Back** and **Contents** buttons help you navigate. Blue links in the text open the linked chapter.
- Search now returns one row per chapter, with its title and a short excerpt. If a word appears several times, the number of matches is shown. Previously, the same title appeared repeatedly in the list.

### Left pane

- The three view options—folder view, **Simplified Tree View**, and **Show Thumbnails in Library**—are now remembered until the next start. Previously, they reset every time you opened the program.
- With thumbnails on, folder rows now show a small stack of pictures from the folder instead of the yellow folder icon.
- **Simplified Tree View** has moved to the bottom of **View** ▸ **Folder View**, as in the original Picasa.
- Folder rows no longer stay empty when thumbnails are on.
- **Projects** folders no longer appear twice in the pane.

### Movies

- A **Target file:** is no longer required. Leave it blank and the program saves to a movies folder in the <code>Picasa</code> subfolder of your Pictures folder, using the source folder's name and a number if needed to avoid a conflict.

### Picture Tray

- The tray has its own selection. Click a picture in the tray to select it (Ctrl and Shift work too). **Remove Selection** now acts on those pictures, not the grid selection.

### Places

- The program asks before changing the location of more than twenty pictures or removing geotags from more than five.
- Location data is now written to <code>.picasa.ini</code> more accurately, so the Windows version of Picasa places the picture at the same location on the map.

### Editor

- The introduction on the **Legacy Effects** tab no longer claims that none of the inherited filters can be used; sixteen of the twenty-one can still be applied.
- **Film Grain** and **Tint** now call the original Picasa primary filter. Film Grain therefore opens a slider panel, and its blue badge is gone.
- The chosen font and bold setting in the Text tool are now saved to <code>.picasa.ini</code>. Previously, every caption was written in bold Arial.

### Email

- On a fresh installation, **Send pictures by email** appears on the first send, with a “Don't ask again” check box. This dialog used to appear only if you had opened Settings first.

## 2026-09-03

### Collages

- **Show Captions** now affects the finished collage. Previously, captions written on Polaroid borders stayed visible even after you turned it off.
- Accented letters in captions now appear correctly. They used to be replaced by question marks.
- Caption color now follows the background: dark gray on a light background and white on a dark one, so captions remain readable on a dark collage. Caption size and position now match the original Picasa too.
- Moving the **Grid Spacing** slider no longer freezes the interface for Mosaic and Frame Mosaic. Rearranging happens after you stop moving the slider.

## 2026-09-02 — first help release

This is the first complete version of the help. It describes the current state of the program, rather than one specific update (the 0.8 series).

What PicasaPy can do today:

- **Library** — watched folders, three folder views, albums, collections, projects, hidden pictures, and unavailable folders.
- Viewing photos — single-picture viewer with comparison mode, slideshow, and video playback.
- **Search** — by filename, caption, tag, or folder name; search by color (such as <code>color:blue</code>); four toolbar filters; and similar-picture search.
- Organizing — stars, picture captions, tags, and quick tags.
- **People** — face search and grouping, naming, ignored faces, and the People panel.
- **Places** — map-based geotagging and Google Earth export.
- Editor — seven tabs: common fixes, fine tuning, four effect tabs, and legacy effects. Crop, straighten, redeye, retouch, text tool, and histogram.
- Batch work — batch editing, effect clipboard, and nondestructive rotation.
- Saving — saving with backups, Save As, saving a copy, restoring, and undoing the last save.
- Import and export — import from source, export to folder, create an HTML page, print to paper or PDF, print contact sheets, and send by email.
- **Create** — collages with six layouts and movies.
- Maintenance — duplicate finder, Folder Manager, moving and compacting the database.
- Appearance — dark theme, display modes, and Hungarian and English languages.

See [Features not yet available](features/meg-nem-erheto-el.md) for a list of things PicasaPy cannot do yet.
