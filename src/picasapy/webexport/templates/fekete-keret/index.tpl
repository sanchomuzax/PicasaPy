#templatefile -v "1.0" -n "Fekete keret" -d "PicasaPy galéria-sablon a(z) blackfrm kinézetében"
define exportFileName index.html
copy empty-index.html thumbnail-index0.html
include header.html
define exportFileName thumbnail-index.html
targetloop frameindex.tpl empty-target.html
define exportFileName index.html
targetloop imagetarget.tpl initialimageframe.html
include footer.html
copy style.css
copy assets/
