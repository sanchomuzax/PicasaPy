import QtQuick
import QtQuick.Controls

// #710: a szerkesztő csúszka-feliratainak KÖZÖS stílusa. Csak a stílus van
// itt; az elhelyezést (`Layout.*`) a használó adja, mert panelenként más.
//
// #2626: a felirat a NORMÁL TINTA színét viszi, nem a másodlagos szürkét. A
// mérés a tulajdonos 2026-09-06 22:32-i A/B felvételén (`research/
// felirat-ki-bekapcsolva/`, a „Derítőfény" feliratra, azonos háttéren): az
// eredeti legsötétebb betű-képpontja 47 a 231-es háttéren (kontraszt 184), a
// miénk 122 a 225-ösön (kontraszt 103) — a `Theme.textGray` világos témán
// `#7a776f`, luminancia ~120, tehát pontosan ez a 122.
//
// Az eredetiben a felirat a csúszka FÖLÖTT, KÖZÉPRE igazítva áll (az
// `editlabel1..4` rétegek `textalign center`-je).
Label {
    horizontalAlignment: Text.AlignHCenter
    wrapMode: Text.WordWrap
    font.pixelSize: Theme.fontSize - 1
    color: Theme.ink
}
