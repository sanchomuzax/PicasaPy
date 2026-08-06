#templatefile -v "1.0" -n "Fehér" -d "Egyszerű, fehér hátterű PicasaPy galéria-sablon (whitebg stílus)"
define exportFileName index.html
include header.html
include imagelistheader.html
loop imagelistelement.html
include imagelistfooter.html
include targetlistheader.html
targetloop imagetarget.tpl includedtarget.html
include targetlistfooter.html
include footer.html
copy style.css
copy assets/
