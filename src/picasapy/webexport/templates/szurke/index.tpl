#templatefile -v "1.0" -n "Szürke" -d "PicasaPy galéria-sablon a(z) greybg kinézetében"
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
