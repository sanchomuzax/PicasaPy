import QtQuick

// GPU-gyorsított pontonkénti előnézeti réteg (#22): a finetune2/fill
// (Fill Light/Highlights/Shadows/Color Temperature), a telítettség és a
// fekete-fehér szűrők élő csúszka-húzás közbeni előnézetét futtatja a
// GPU-n, a `PointFilter.frag` shaderrel. ÖNÁLLÓ komponens — a hívó
// (jelenleg egyik controller sem) köti be a forrásképet és az
// uniformokat; a bekötési igényt ld. a #22 jegy jelentésében.
//
// A CPU-s numpy-út (`picasapy.render`) MARAD az igazságforrás: ez a
// réteg csak az INTERAKTÍV húzás alatti előnézetet gyorsítja, a
// Alkalmaz/Mentés/Export-út változatlanul a CPU-t hívja. `lutTexture`
// forrása a `picasapy.render.gpu_point_pipeline.build_finetune2_lut()` —
// a hívó ebből épít egy 256×1 RGB8 `QImage`-et és tölti be `Image`-ként
// (`source`/`cache: false`, hogy csúszka-húzásnál frissüljön).
ShaderEffect {
    id: root
    objectName: "gpuPointFilterPreview"

    // a szerkesztetlen (vagy a lánc korábbi, nem-GPU-s tagjaival már
    // renderelt) forráskép — a hívó tölti (pl. Image.source: "image://…")
    property alias sourceItem: sourceProxy.sourceItem
    // 256×1 RGB8 LUT-textúra (finetune2/fill kompozit) — a hívó tölti a
    // gpu_point_pipeline.build_finetune2_lut() eredményéből épített képpel
    property alias lutItem: lutProxy.sourceItem

    // a picasapy.render.gpu_point_pipeline.PointPipelineUniforms mezői
    property real satGain: 1.0
    property real bwMix: 0.0

    ShaderEffectSource {
        id: sourceProxy
        hideSource: false
        live: true
        visible: false
    }
    ShaderEffectSource {
        id: lutProxy
        hideSource: false
        live: true
        visible: false
        smooth: false
        // a LUT egzakt indexelést igényel — bilineáris simítás elmosná a
        // szomszédos LUT-bejegyzéseket, ezért a hívónak a forrás Image-en
        // is `smooth: false`-t kell beállítania (ld. a jegy jelentése)
    }

    property variant source: sourceProxy
    property variant lut: lutProxy

    // #402: a relatív URL a beágyazó modul felől rossz mappára oldódott
    // (a felhasználó gépén a PicasaPy/ gyökérben kereste a .qsb-t) — a
    // Qt.resolvedUrl e fájl (Gpu/) helyéhez képest ad ABSZOLÚT URL-t.
    fragmentShader: Qt.resolvedUrl("PointFilter.frag.qsb")

    // #402: néma fallback shader-hibánál is — ha a shader nem tölthető be
    // (hiányzó/sérült .qsb), a réteg elrejti magát, a CPU-előnézet marad.
    readonly property bool shaderOk: status !== ShaderEffect.Error
}
