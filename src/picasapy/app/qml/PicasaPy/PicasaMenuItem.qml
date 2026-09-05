import QtQuick
import QtQuick.Controls
// #757: az `IconLabel` a Qt saját, MNEMONIK-TUDATOS címkéjét
// (`QQuickMnemonicLabel`) hozza magával — pontosan azt, amit a sima
// `MenuItem` alapértelmezése is használ.
import QtQuick.Controls.impl

// #416: helyfoglaló (még be nem kötött) menüpont — a menü HELYE megvan, de
// funkció nincs mögötte. Ránézésre is látszódjon, mi működik és mi nem:
// - a felirat halványabb (Theme.textGray, a meglévő "letiltott" tokent
//   használjuk — a Theme.qml forró fájl, új tokent nem veszünk fel),
// - a sor jobb szélén egy kicsi, világosszürke pont jelenik meg.
//
// Csak a placeholder tételeknél használjuk — a MŰKÖDŐ menüpontok
// változatlanul a sima QtQuick.Controls `MenuItem`-et használják, ezért a
// kinézetük ettől a komponenstől nem változhat.
MenuItem {
    id: control

    // a szándék explicit jelölése (#416) — mindig true-val hívjuk a
    // PicasaMenuBar.qml-ben, hogy a forrásban is egyértelmű legyen, mely
    // tételek csak helyfoglalók
    property bool placeholder: true

    // #422: MEGSZŰNT szolgáltatás tétele — a tulajdonos döntése (2026-08-14),
    // hogy ezek a menüben maradnak, véglegesen szürkén: így a menü szerkezete
    // és a tételek helye egyezik az eredetivel, az izommemória működik.
    //
    // Miért nem `placeholder`: az azt jelenti, „még nincs bekötve" — ígéret a
    // jövőre, amit a sor végi pont is jelöl. Ezek viszont soha nem lesznek
    // bekötve, mert maga a SZOLGÁLTATÁS szűnt meg (a Picasa Webalbumok 2016-ban).
    // A `retired` ugyanúgy szürke és kattinthatatlan, de nem ígér semmit, és
    // nem számít bele a hátralévő munkába.
    //
    // Csak arra használjuk, aminek a szolgáltatása BIZONYÍTHATÓAN megszűnt —
    // a helyi funkciók (pl. a gyűjtemény jelszava) maradnak helyfoglalók.
    property bool retired: false

    // #1701: A PICASAPY SAJÁT parancsa — az eredeti Picasa 3-ban nem
    // létezett. A jelölés a tulajdonos döntése (2026-08-28,
    // `docs/decisions/sajat-funkciok-jelolese.md`), és szándékos eltérés
    // attól a korábbi szabálytól, hogy a felület pontosan úgy nézzen ki,
    // mint az eredeti.
    //
    // A jelölés a felirat KÉK SZÍNE, nem pötty a jobb szélen: a döntéslap
    // kimondja, hogy a jobb szél már foglalt — a feliratok gyorsbillentyűt
    // hordoznak (`"Új album…" + "\tCtrl+N"`), és azt a Qt oda igazítja.
    //
    // ⚠️ NEM keverendő a másik kettővel:
    //   `placeholder` = még nem működik · `retired` = volt, de kivezettük ·
    //   `sajat`       = az eredetiben SOHA nem is létezett.
    // És NEM jár olyan parancsra, ami az eredetiben létezik, csak nálunk
    // hibás — az jegy, nem jelölés.
    property bool sajat: false

    // A pötty/szín önmagában nem hordozhat információt (színvakság), ezért
    // a buboréksúgó KÖTELEZŐ, nem díszítés — a döntéslap így írja elő.
    //: A súgó szövege SAJÁT tulajdonságban is él, nem csak a csatolt
    //: `ToolTip.text`-ben: a csatolt tulajdonságot a teszt nem tudja
    //: kiolvasni (`property("ToolTip.text")` → null), tehát a
    //: kötelezőségét nem lehetne rajta őrizni.
    readonly property string sajatSugo: control.sajat
        ? qsTr("This is a PicasaPy addition — the original Picasa did not have it.")
        : ""

    ToolTip.visible: control.sajat && control.hovered
    ToolTip.text: control.sajatSugo

    // sem a helyfoglaló, sem a nyugdíjazott tétel nem kattintható
    enabled: !placeholder && !control.retired

    // #757: NEM sima `Text`. Amióta a feliratok az eredeti `&`-mnemonikkal
    // érkeznek (a `Picasa3i18n.dll` string-táblájából), egy sima `Text` az
    // ampersandot NYERSEN mutatná („&Mappa elrejtése"). Az `IconLabel`
    // belül `QQuickMnemonicLabel`-t rajzol — ugyanazt, amit a sima
    // `MenuItem` alapértelmezése —, tehát az `&` az aláhúzás helyét jelöli,
    // nem betűként látszik. A színezés és a jobb oldali térköz miatt kell
    // saját `contentItem`; ezt az `IconLabel` ugyanúgy tudja.
    contentItem: IconLabel {
        // #1750: HELY A JELÖLŐNEK. A Qt alapértelmezett `MenuItem`-je a
        // saját `contentItem`-jében kihagyja a jelölő (és az almenü-nyíl)
        // helyét; mi viszont saját `contentItem`-et adunk (#757, a
        // mnemonikus `&` miatt), és ez a behúzás kimaradt belőle. Emiatt a
        // felirat a tétel bal széléről indult — a jelölőnégyzet ALÓL.
        //
        // A tulajdonos képernyőmentése (v0.8.146) angol nyelven is mutatta,
        // tehát nem fordítás-hossz kérdése. A sima `MenuItem`-et használó
        // (működő) menüpontokon nem látszott: azok az alapértelmezett
        // `contentItem`-et kapják. Öt jelölőnégyzetes `PicasaMenuItem` volt
        // érintett.
        //
        // A behúzás FELTÉTELES — ez nem finomkodás: ha minden tétel kapna
        // behúzást, a jelölő nélküli sorok feliratai elcsúsznának a menü
        // többi sorához képest, és a hibát egy másikra cserélnénk.
        readonly property real jeloloHely: control.checkable && control.indicator
            ? control.indicator.width + control.spacing : 0
        readonly property real nyilHely: control.subMenu && control.arrow
            ? control.arrow.width + control.spacing : 0
        leftPadding: !control.mirrored ? jeloloHely : nyilHely
        text: control.text
        font: control.font
        // a nyugdíjazott tétel ugyanúgy halvány, mint a helyfoglaló — a
        // különbség csak a sor végi pont (ld. lent)
        color: control.placeholder || control.retired
            ? Theme.textGray
            : (control.sajat ? Theme.linkBlue : Theme.ink)
        alignment: Qt.AlignLeft | Qt.AlignVCenter
        // hely a jobb szélen a placeholder-pontnak, hogy ne fedjék egymást,
        // és (#1750) az almenü-nyílnak — tükrözött elrendezésben a jelölőnek
        rightPadding: (control.placeholder ? placeholderDot.width + 8 : 0)
            + (!control.mirrored ? nyilHely : jeloloHely)
    }

    Rectangle {
        id: placeholderDot
        objectName: "placeholderDot"
        // #422: a nyugdíjazott tételen NINCS pont — az folytatást ígérne,
        // holott a szolgáltatás megszűnt
        visible: control.placeholder && !control.retired
        width: 5
        height: 5
        radius: width / 2
        color: Theme.textGray
        anchors.right: control.right
        anchors.rightMargin: 8
        anchors.verticalCenter: control.verticalCenter
    }
}
