#templatefile -v "1.0" -n "XML (gépi)" -d "Nem weboldal: album- és képadatok gépi feldolgozásra, egyetlen album.xml fájlban"
define exportFileName album.xml
include header.xml
loop imagelistelement.xml
include footer.xml
