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
    // csavarkulcs: a nyitott pofa bal fent, a nyél jobb lent.
    function paintWrench(ctx) {
        var cx = 4.3, cy = 4.5, r = 4.7
        ctx.strokeStyle = icon.strokeColor
        ctx.lineWidth = 3.2
        ctx.beginPath()
        ctx.moveTo(6.4, 6.6)
        ctx.lineTo(13.6, 13.9)
        ctx.stroke()
        ctx.fillStyle = icon.strokeColor
        ctx.beginPath()
        ctx.arc(cx, cy, r, 0, Math.PI * 2)
        ctx.fill()
        ctx.save()
        ctx.globalCompositeOperation = "destination-out"
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.lineTo(cx - r * 1.3, cy)
        ctx.lineTo(cx, cy - r * 1.3)
        ctx.closePath()
        ctx.fill()
        ctx.restore()
    }
    // nap: nyolc sugár, balra kitöltött korong és nyitott jobb fél.
    function paintSun(ctx) {
        var cx = 8.5, cy = 8.5
        ctx.strokeStyle = icon.strokeColor
        ctx.fillStyle = icon.strokeColor
        ctx.lineWidth = 1.5
        for (var i = 0; i < 8; i++) {
            var a = Math.PI * i / 4
            var diag = (i % 2 === 1)
            var r0 = diag ? 5.1 : 5.0
            var r1 = diag ? 7.1 : (i % 4 === 0 ? 8.2 : (i % 4 === 2 ? 7.4 : 8.2))
            ctx.beginPath()
            ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0)
            ctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1)
            ctx.stroke()
        }
        ctx.lineWidth = 1.6
        ctx.beginPath()
        ctx.arc(cx, cy, 4.4, 0, Math.PI * 2)
        ctx.stroke()
        ctx.beginPath()
        ctx.arc(cx, cy, 4.4, Math.PI * 0.5, Math.PI * 1.5)
        ctx.closePath()
        ctx.fill()
    }
    // ecset: nyele jobb fent, sörte bal lent; dx = vízszintes eltolás
    // (a tájképes négyzet mellett az ecset jobbra kerül)
    function paintBrush(ctx, dx, bristle, landscapeBrush) {
        ctx.strokeStyle = icon.strokeColor
        ctx.lineWidth = landscapeBrush ? 5.0 : 4.6
        ctx.beginPath()
        ctx.moveTo(dx + (landscapeBrush ? 19 : 18.5), landscapeBrush ? 0 : 0.5)
        ctx.lineTo(dx + (landscapeBrush ? 12 : 11.5), landscapeBrush ? 7 : 7.5)
        ctx.stroke()
        ctx.save()
        ctx.translate(10, 10)
        // #5959: a tájképen átfutó ecset sörtéjének félpixeles rajza a
        // zöld és kék háttérrel más élszínt ad; a mért kontúrt külön igazítjuk.
        var blueLandscape = icon.accentColor.b > icon.accentColor.g
        var bristleScaleX = landscapeBrush && blueLandscape ? 0.95 : 0.9
        ctx.scale(bristleScaleX, 0.9)
        ctx.translate(-10, -10)
        if (landscapeBrush)
            ctx.translate(0.5, -0.5)
        ctx.fillStyle = bristle
        ctx.beginPath()
        var bx = dx + 1
        ctx.moveTo(bx + 7.4, 7.9)
        ctx.lineTo(bx + 10.0, 9.8)
        ctx.bezierCurveTo(bx + 11.4, 12.9, bx + 8.7, 15.4, bx + 6.4, 16.4)
        ctx.lineTo(bx + 0.2, 15.6)
        ctx.lineTo(bx + 0.5, 14.7)
        ctx.bezierCurveTo(bx + 1.3, 11.7, bx + 4.5, 9.1, bx + 8.2, 8.3)
        ctx.closePath()
        ctx.fill()
        ctx.restore()
    }
    // A tájképes négyzet és a felhő az eredeti helyen, mért háromsávos színnel.
    function paintLandscape(ctx) {
        var x = 4, y = 0, s = 16, r = 2.5
        var green = icon.accentColor.g > icon.accentColor.b
        var topColor = green ? "#bfd6b3" : "#a6cfe3"
        var middleColor = green ? "#8eb77a" : "#62aacf"
        var bottomColor = green ? "#9abf88" : "#73b3d4"
        ctx.beginPath()
        ctx.moveTo(x + r, y)
        ctx.lineTo(x + s - r, y)
        ctx.quadraticCurveTo(x + s, y, x + s, y + r)
        ctx.lineTo(x + s, y + s - r)
        ctx.quadraticCurveTo(x + s, y + s, x + s - r, y + s)
        ctx.lineTo(x + r, y + s)
        ctx.quadraticCurveTo(x, y + s, x, y + s - r)
        ctx.lineTo(x, y + r)
        ctx.quadraticCurveTo(x, y, x + r, y)
        ctx.closePath()
        ctx.save()
        ctx.clip()
        ctx.fillStyle = topColor
        ctx.fillRect(x, y, s, 5)
        ctx.fillStyle = middleColor
        ctx.fillRect(x, y + 5, s, 6)
        ctx.fillStyle = bottomColor
        ctx.fillRect(x, y + 11, s, 5)
        ctx.restore()
        ctx.fillStyle = icon.fleckColor
        ctx.beginPath()
        ctx.moveTo(x + 3.5, 5.6)
        ctx.quadraticCurveTo(x + 3.5, 3.4, x + 6.2, 3.4)
        ctx.quadraticCurveTo(x + 7.6, 2.4, x + 9.2, 3.6)
        ctx.quadraticCurveTo(x + 12, 3.8, x + 12, 5.6)
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
            icon.paintBrush(ctx, 5, icon.strokeColor, true)
        } else {
            icon.paintBrush(ctx, 0, icon.strokeColor, false)
        }
        ctx.restore()
    }
}
