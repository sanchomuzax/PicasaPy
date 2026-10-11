import QtQuick

// A szerkesztő fülsávjának SAJÁT rajzolású ikonjai (#338): csavarkulcs, nap
// és ecset — `Canvas`-on, hogy a rajz mindig ugyanúgy nézzen ki, és a színe
// is szabályozható legyen (ez adja a három ecset-fül „színben
// megkülönböztetve" követelményét, amit egy fix színű emoji-glif nem tudna).
//
// #496: az `EditorPanel.qml` inline `component`-jéből önálló fájlba emelve —
// a fájl a 800 soros korlát fölé nőtt.
//
// #4846: a rajz az eredeti Picasa 3.9 fülsávjának irányát és formáját követi
// (SAJÁT rajz, a respack-grafika nem használható): a csavarkulcs feje bal
// fent, az ecset sörtéje bal lent, a nap korongjának jobb fele üres, a 4–5.
// fül ikonja tájképes négyzet bal fent + az ecset jobb lent.
Canvas {
    id: icon
    property string kind: "wrench"   // "wrench" | "sun" | "brush"
    property color strokeColor: Theme.iconInk
    // ecset-füleknél a sörte színe (a 3./4./5. fül megkülönböztetése)
    property color accentColor: strokeColor
    // a tájképes négyzet felhője (4./5. fül); ha nem átlátszó, az ikon
    // tájképes négyzet + ecset: a négyzet az `accentColor` színű, az ecset
    // sötét. "transparent" = sima ecset, a sörte az `accentColor`-ral.
    property color fleckColor: "transparent"
    onKindChanged: requestPaint()
    onStrokeColorChanged: requestPaint()
    onAccentColorChanged: requestPaint()
    onFleckColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    // #4552/#4846: minden ikon SAJÁT TERVEZÉSI dobozban (képpont) készül, és a
    // rajz pontosan kitölti — a vonalvégekkel együtt. Az ikon mérete
    // fülenként más (15×16 … 25×19), ezért a tervezési doboz a vászonra
    // nyújtva kerül (két tengelyen külön), így a mért befoglaló doboz egyezik
    // a vászonnal, nem a rajz körüli üres szegéllyel.
    readonly property bool landscape: icon.fleckColor.a > 0
    function designSize() {
        if (icon.kind === "wrench") return [15, 16]
        if (icon.kind === "sun") return [17, 18]
        return icon.landscape ? [25, 19] : [20, 19]
    }
    function contentBounds(w, h) {
        var d = icon.designSize()
        return [0, 0, d[0], d[1]]
    }
    // csavarkulcs: feje bal fent (a nyitott száj a bal-felső irányba néz),
    // nyele jobb lent
    function paintWrench(ctx) {
        ctx.strokeStyle = icon.strokeColor
        ctx.lineWidth = 3.2
        ctx.beginPath()
        ctx.moveTo(6.5, 6.5)
        ctx.lineTo(13.4, 14.4)
        ctx.stroke()
        ctx.fillStyle = icon.strokeColor
        ctx.beginPath()
        ctx.moveTo(4.8, 4.8)
        ctx.arc(4.8, 4.8, 4.8, Math.PI * 1.5, Math.PI * 2.8)
        ctx.closePath()
        ctx.fill()
    }
    // nap: 8 sugár (a négy főirányú hosszabb), a korong körvonala, a BAL
    // fele kitöltve, a jobb fele üres
    function paintSun(ctx) {
        var cx = 8.5, cy = 9
        ctx.strokeStyle = icon.strokeColor
        ctx.fillStyle = icon.strokeColor
        ctx.lineWidth = 1.6
        for (var i = 0; i < 8; i++) {
            var a = Math.PI * i / 4
            var diag = (i % 2 === 1)
            var r0 = diag ? 5.6 : 5.4
            var r1 = diag ? 7.0 : 7.7
            ctx.beginPath()
            ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0 * 1.0)
            ctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1 * 1.1)
            ctx.stroke()
        }
        ctx.lineWidth = 1.4
        ctx.beginPath()
        ctx.arc(cx, cy, 4.0, 0, Math.PI * 2)
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(cx, cy, 4.0, Math.PI * 0.5, Math.PI * 1.5)
        ctx.closePath()
        ctx.fill()
    }
    // ecset: nyele jobb fent, sörte bal lent; dx = vízszintes eltolás
    // (a tájképes négyzet mellett az ecset jobbra kerül)
    function paintBrush(ctx, dx, bristle) {
        ctx.strokeStyle = icon.strokeColor
        ctx.lineWidth = 3.4
        ctx.beginPath()
        ctx.moveTo(dx + 18.2, 1.8)
        ctx.lineTo(dx + 10.6, 9.6)
        ctx.stroke()
        ctx.fillStyle = bristle
        ctx.beginPath()
        ctx.moveTo(dx + 11.2, 8.4)
        ctx.lineTo(dx + 14.2, 11.4)
        ctx.bezierCurveTo(dx + 12.8, 14.6, dx + 7.4, 18.2, dx + 1.4, 18.8)
        ctx.bezierCurveTo(dx + 0.2, 16.4, dx + 3.0, 12.6, dx + 7.4, 11.4)
        ctx.closePath()
        ctx.fill()
    }
    // tájképes négyzet (4./5. fül): a fül színe + fehér felhő
    function paintLandscape(ctx) {
        var r = 3.5
        ctx.fillStyle = icon.accentColor
        ctx.beginPath()
        ctx.moveTo(r, 0)
        ctx.lineTo(15 - r, 0)
        ctx.quadraticCurveTo(15, 0, 15, r)
        ctx.lineTo(15, 15 - r)
        ctx.quadraticCurveTo(15, 15, 15 - r, 15)
        ctx.lineTo(r, 15)
        ctx.quadraticCurveTo(0, 15, 0, 15 - r)
        ctx.lineTo(0, r)
        ctx.quadraticCurveTo(0, 0, r, 0)
        ctx.closePath()
        ctx.fill()
        ctx.fillStyle = icon.fleckColor
        ctx.beginPath()
        ctx.moveTo(3.5, 5.6)
        ctx.quadraticCurveTo(3.5, 3.4, 6.2, 3.4)
        ctx.quadraticCurveTo(7.6, 2.4, 9.2, 3.6)
        ctx.quadraticCurveTo(12, 3.8, 12, 5.6)
        ctx.closePath()
        ctx.fill()
    }
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.clearRect(0, 0, width, height)
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        var d = icon.designSize()
        ctx.save()
        ctx.scale(width / d[0], height / d[1])
        if (icon.kind === "wrench") {
            icon.paintWrench(ctx)
        } else if (icon.kind === "sun") {
            icon.paintSun(ctx)
        } else if (icon.landscape) {
            icon.paintLandscape(ctx)
            icon.paintBrush(ctx, 5, icon.strokeColor)
        } else {
            icon.paintBrush(ctx, 0, icon.accentColor)
        }
        ctx.restore()
    }
}
