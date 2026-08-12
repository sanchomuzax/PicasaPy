import QtQuick

// A szerkesztő fülsávjának SAJÁT rajzolású ikonjai (#338): csavarkulcs, nap
// és ecset — `Canvas`-on, hogy a rajz mindig ugyanúgy nézzen ki, és a színe
// is szabályozható legyen (ez adja a három ecset-fül „színben
// megkülönböztetve" követelményét, amit egy fix színű emoji-glif nem tudna).
//
// #496: az `EditorPanel.qml` inline `component`-jéből önálló fájlba emelve —
// a fájl a 800 soros korlát fölé nőtt. A rajz és a tulajdonságok
// VÁLTOZATLANOK.
Canvas {
    id: icon
    property string kind: "wrench"   // "wrench" | "sun" | "brush"
    property color strokeColor: Theme.iconInk
    // ecset-füleknél a sörte színe (a 3./4./5. fül megkülönböztetése)
    property color accentColor: strokeColor
    // apró minta-pötty a sörtén (zöld/kék fülnél "levél"/"felhő" folt);
    // "transparent" = nincs
    property color fleckColor: "transparent"
    onKindChanged: requestPaint()
    onStrokeColorChanged: requestPaint()
    onAccentColorChanged: requestPaint()
    onFleckColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        var ctx = getContext("2d")
        ctx.reset()
        ctx.clearRect(0, 0, width, height)
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        var w = width, h = height
        if (icon.kind === "wrench") {
            // nyél: bal-alsó → jobb-felső átló
            ctx.strokeStyle = icon.strokeColor
            ctx.lineWidth = Math.max(2, w * 0.14)
            ctx.beginPath()
            ctx.moveTo(w * 0.20, h * 0.85)
            ctx.lineTo(w * 0.58, h * 0.45)
            ctx.stroke()
            // fej: nyitott gyűrű (csavarkulcs-száj) a nyél végén
            ctx.beginPath()
            ctx.arc(w * 0.68, h * 0.32, w * 0.20, Math.PI * 0.15, Math.PI * 1.65)
            ctx.lineWidth = Math.max(2, w * 0.12)
            ctx.stroke()
        } else if (icon.kind === "sun") {
            ctx.fillStyle = icon.strokeColor
            ctx.beginPath()
            ctx.arc(w * 0.5, h * 0.5, w * 0.20, 0, Math.PI * 2)
            ctx.fill()
            ctx.strokeStyle = icon.strokeColor
            ctx.lineWidth = Math.max(1.5, w * 0.08)
            var rays = 8
            for (var i = 0; i < rays; i++) {
                var a = (Math.PI * 2 * i) / rays
                var innerR = w * 0.30
                var outerR = w * 0.46
                ctx.beginPath()
                ctx.moveTo(w * 0.5 + Math.cos(a) * innerR, h * 0.5 + Math.sin(a) * innerR)
                ctx.lineTo(w * 0.5 + Math.cos(a) * outerR, h * 0.5 + Math.sin(a) * outerR)
                ctx.stroke()
            }
        } else if (icon.kind === "brush") {
            // nyél
            ctx.strokeStyle = icon.strokeColor
            ctx.lineWidth = Math.max(2, w * 0.12)
            ctx.beginPath()
            ctx.moveTo(w * 0.28, h * 0.14)
            ctx.lineTo(w * 0.56, h * 0.48)
            ctx.stroke()
            // sörte (ékalakú folt, a fül szín-tokenjével — plain/zöld/kék)
            ctx.fillStyle = icon.accentColor
            ctx.beginPath()
            ctx.moveTo(w * 0.56, h * 0.50)
            ctx.lineTo(w * 0.82, h * 0.60)
            ctx.lineTo(w * 0.86, h * 0.82)
            ctx.lineTo(w * 0.66, h * 0.90)
            ctx.lineTo(w * 0.50, h * 0.68)
            ctx.closePath()
            ctx.fill()
            if (icon.fleckColor.toString() !== "#00000000"
                    && icon.fleckColor.toString() !== "transparent") {
                ctx.fillStyle = icon.fleckColor
                ctx.beginPath()
                ctx.arc(w * 0.70, h * 0.74, w * 0.06, 0, Math.PI * 2)
                ctx.fill()
            }
        }
    }
}
