#version 440

// GPU pontonkénti előnézeti szűrő-lánc (#22): finetune2/fill (LUT-textúra)
// + telítettség (sat) + fekete-fehér (bw) keverés. A LUT-ot és a
// gain/mix-uniformokat a CPU (picasapy.render.gpu_point_pipeline) állítja
// elő — ugyanaz a matematika, mint a numpy-s referencia-út
// (picasapy.render.tone/color), ezért a shader NEM önálló modell, hanem
// a CPU-eredmény GPU-n futtatott, pixel-hű alkalmazása.
//
// #696 (a #693 következménye): a `sat` szűrőnek KÉT külön ága van, és a
// pozitív ág NEM erősítés (ld. picasapy.render.saturation_positive) —
// erre semmilyen skalár `satGain` nem illeszthető. Ez a fájl ezért a
// pozitív ágon a natív, csatornánkénti gamma-modellt futtatja
// (applyPositiveSaturation), folytonos pow()-pal a natív fixpontos,
// 2048 elemű táblázat helyett. A KÉT modell pontos numpy-mása és a
// köztük lévő mért eltérés:
// picasapy.render.gpu_point_pipeline.simulate_positive_saturation_shader
// (ennek a docsztringje magyarázza a luma-floor és a ratio-clamp okát).

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float satGain;               // 1.0 = azonosság (a `sat` NEGATÍV ága)
    float satPositiveStrength;   // 0.0 = a negatív ág aktív; a `sat` POZITÍV ága: amount*3
    float bwMix;      // 0.0 = színes, 1.0 = teljes fekete-fehér keverés
};

layout(binding = 1) uniform sampler2D source;   // a szerkesztetlen forráskép
layout(binding = 2) uniform sampler2D lut;      // 256x1 RGB8 finetune2/fill LUT

const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114);

// #696: a `sat` POZITÍV ágának luma-súlyai MÁSOK, mint a fenti
// LUMA_WEIGHTS (Rec.601) — a natív kód itt (2R + 5G + B) >> 3 súlyozást
// használ (picasapy.render.saturation_positive docsztringje szerint ez
// szándékos, a két képletet TILOS összevonni).
const vec3 POSITIVE_SAT_LUMA_WEIGHTS = vec3(2.0, 5.0, 1.0) / 8.0;
// a három csatorna kitevő-szorzója (picasapy.render.saturation_positive.
// CHANNEL_EXPONENTS szó szerinti másolata — az egyezést teszt őrzi)
const vec3 POSITIVE_SAT_EXPONENT_SCALE = vec3(0.3, 0.7, 0.9);
// a natív LUT `x`-tartományának felső határa (picasapy.render.
// gpu_point_pipeline._POSITIVE_SATURATION_RATIO_CLAMP másolata)
const float POSITIVE_SAT_RATIO_CLAMP = 8.0;
const float POSITIVE_SAT_EPSILON = 1e-6;

// A `sat` POZITÍV ága (#696): csatornánkénti gamma a csatorna/luma
// arányon, a natív fixpontos modell (picasapy.render.saturation_positive.
// apply_positive_saturation) folytonos pow()-os közelítése. A pontos
// lépések (luma egész-osztása, ratio-vágás, 255 fölötti maxnormálás)
// megegyeznek a numpy-referenciával
// (gpu_point_pipeline.simulate_positive_saturation_shader) — ott
// dokumentált a két lépés indoklása, ami nélkül a modell durván szétesne.
vec3 applyPositiveSaturation(vec3 toned, float strength) {
    vec3 channel255 = toned * 255.0;
    // a natív kód `>> 3` egész-léptetése — NEM folytonos osztás, ld. a
    // numpy-referencia docsztringje
    float luma = floor(dot(channel255, POSITIVE_SAT_LUMA_WEIGHTS));
    if (luma <= 0.0) {
        // a natív kód a "majdnem fekete" (luma == 0 az egész osztás után)
        // pixelekhez nem nyúl
        return toned;
    }
    vec3 exponent = vec3(1.0) + strength * POSITIVE_SAT_EXPONENT_SCALE;
    vec3 ratio = min(channel255 / luma, POSITIVE_SAT_RATIO_CLAMP);
    vec3 gammaOut = pow(max(ratio, vec3(0.0)), exponent) * luma;
    float channelMax = max(max(gammaOut.r, gammaOut.g), gammaOut.b);
    vec3 normalized = channelMax > 255.0
        ? gammaOut * (255.0 / max(channelMax, POSITIVE_SAT_EPSILON))
        : gammaOut;
    return clamp(normalized / 255.0, 0.0, 1.0);
}

void main() {
    vec4 color = texture(source, qt_TexCoord0);

    // 1) finetune2/fill — csatornánként FÜGGETLEN LUT-mintavétel (ld. a
    // gpu_point_pipeline modul docsztringje: a CPU-lánc bizonyítottan
    // csatorna-vak, ezért a három külön mintavétel pontosan egyenértékű
    // a csatornánkénti LUT-alkalmazással).
    float r = texture(lut, vec2(color.r, 0.5)).r;
    float g = texture(lut, vec2(color.g, 0.5)).g;
    float b = texture(lut, vec2(color.b, 0.5)).b;
    vec3 toned = vec3(r, g, b);

    // 2) telítettség — a natív `sat` KÉT ága (#696, a #693 következménye):
    vec3 saturated;
    if (satPositiveStrength > 0.0) {
        // POZITÍV ág: csatornánkénti gamma, NEM erősítés (ld. fent)
        saturated = applyPositiveSaturation(toned, satPositiveStrength);
    } else {
        // NEGATÍV ág (és az azonosság): luma-tartó skalár erősítés
        // (picasapy.render.color.apply_saturation negatív ága:
        // ki = luma + gain*(be - luma))
        float luma = dot(toned, LUMA_WEIGHTS);
        saturated = mix(vec3(luma), toned, satGain);
        // (a fenti mix ekvivalens: luma + satGain*(toned-luma), mert
        // mix(a,b,t) = a + t*(b-a); itt a=luma, b=toned, t=satGain)
    }

    // 3) fekete-fehér keverés (picasapy.render.color.apply_bw: Rec.601 luma
    // mindhárom csatornára) — bwMix folytonos, hogy jövőbeli csúszka is
    // használhassa, az egykattintásos UI ma 0.0/1.0-t küld.
    vec3 finalColor = mix(saturated, vec3(dot(saturated, LUMA_WEIGHTS)), bwMix);

    fragColor = vec4(finalColor, color.a) * qt_Opacity;
}
