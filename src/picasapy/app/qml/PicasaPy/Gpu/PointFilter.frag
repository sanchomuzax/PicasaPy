#version 440

// GPU pontonkénti előnézeti szűrő-lánc (#22): finetune2/fill (LUT-textúra)
// + telítettség (sat) + fekete-fehér (bw) keverés. A LUT-ot és a
// gain/mix-uniformokat a CPU (picasapy.render.gpu_point_pipeline) állítja
// elő — ugyanaz a matematika, mint a numpy-s referencia-út
// (picasapy.render.tone/color), ezért a shader NEM önálló modell, hanem
// a CPU-eredmény GPU-n futtatott, pixel-hű alkalmazása.

layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;

layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float satGain;   // 1.0 = azonosság (picasapy.render.color.saturation_gain)
    float bwMix;      // 0.0 = színes, 1.0 = teljes fekete-fehér keverés
};

layout(binding = 1) uniform sampler2D source;   // a szerkesztetlen forráskép
layout(binding = 2) uniform sampler2D lut;      // 256x1 RGB8 finetune2/fill LUT

const vec3 LUMA_WEIGHTS = vec3(0.299, 0.587, 0.114);

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

    // 2) telítettség: luma-tartó króma-erősítés (picasapy.render.color.
    // apply_saturation: ki = luma + gain*(be - luma))
    float luma = dot(toned, LUMA_WEIGHTS);
    vec3 saturated = mix(vec3(luma), toned, satGain);
    // (a fenti mix ekvivalens: luma + satGain*(toned-luma), mert
    // mix(a,b,t) = a + t*(b-a); itt a=luma, b=toned, t=satGain)

    // 3) fekete-fehér keverés (picasapy.render.color.apply_bw: Rec.601 luma
    // mindhárom csatornára) — bwMix folytonos, hogy jövőbeli csúszka is
    // használhassa, az egykattintásos UI ma 0.0/1.0-t küld.
    vec3 finalColor = mix(saturated, vec3(dot(saturated, LUMA_WEIGHTS)), bwMix);

    fragColor = vec4(finalColor, color.a) * qt_Opacity;
}
