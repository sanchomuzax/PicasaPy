#templatefile -v "1.0" -n "Szürke keret" -d "PicasaPy galéria-sablon a(z) greyfrm kinézetében"
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
