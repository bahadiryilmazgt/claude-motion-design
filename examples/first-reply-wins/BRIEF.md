# First Reply Wins — director's brief and beat map

Silent 9:16 motion piece for Instagram Reels, 1080×1920, 30 fps, 45.71 s (20 bars at 105 BPM).
Story: a patient sees a clinic ad, writes the same WhatsApp message to five clinics, the first clinic to answer gets the appointment.
Message: in health tourism, reply speed = trust = patients.

Reference style: "Apple Watch product film meets luxury-hotel title sequence": navy velvet space, gold metal, frosted glass, one continuous camera.

## Grid
- 105 BPM → beat B = 0.5714 s, bar = 2.2857 s. Times below are in beats (×B for seconds).
- Music drop (resolution) = beat 44 = 25.14 s = the moment the first reply lands.

## Scenes and main messages (each ≥ 2 s sharp, inside the safe zone y 230–1536)

| Beats | Seconds | Scene | Main message | Camera |
|---|---|---|---|---|
| 0–8 | 0.00–4.57 | Ad in a gold phone, volumetric beam, dust | **Reklamınızı gördü.** (b2–b7.5) | slow push-in from far, phone turns toward camera |
| 8–16 | 4.57–9.14 | Ad slides out, chat in, she types and sends | **WhatsApp'tan yazdı.** (b9–b15) | macro push to the input field |
| 16–24 | 9.14–13.71 | The bubble leaves the phone and splits into 5, lands on 5 glass clinic lanes | **Aynı anda 5 kliniğe.** (b18.5–b23.5) | pull-back reveal |
| 24–44 | 13.71–25.14 | The race: timers count, "yazıyor…" flickers, giant clock ring behind | **Yarış başladı.** (b25–b31), **Her dakika önemli.** (b33.5–b41) | orbit, macro on the Aurelia timer, pull back on the build |
| 44–56 | 25.14–32.00 | DROP: Aurelia replies at 01:52, gold flash, fly-through into the chat, appointment card | **İlk cevap veren kazanır.** (b45–b52) | punch-in, fly-through, orbit |
| 56–64 | 32.00–36.57 | The other 4 answer hours later, steel grey | **Diğerleri için çok geç.** ("çok geç" in the one soft red, b58–b63.5) | pull back through the lanes |
| 64–80 | 36.57–45.71 | Lanes fly into depth, the clock becomes a gold ring | **Hız = Güven = Hasta** (stacked b64.5–b72), then **Sağlık turizminde ilk cevap kazanır.** (b73.5–end) | slow pull-back, drift |

Clinic names, the patient name (Elif) and every time on screen are fictional illustration.

## Layers
bg canvas (navy gradient, volumetric beams, dust, bokeh, liquid gold ribbons) → 3D world (CSS perspective camera: phone, glass lanes, clock ring, conversation, appointment card, ghost numbers) → fx canvas (trails, shockwave, bursts) → type (main messages, labels, equation) → fg canvas (near bokeh, lens flares, vignette, grain).

## Sound plan (all synthesized in `audio.py`, on the same beat grid)
- Music: 105 BPM, Bm–G–D–A. Intro bars 0–3 pads + sparse piano; bars 4–5 plucks enter; race bars 6–10 pulse bass, ticking hats, rising filter, riser into bar 11; drop bar 11 kick + full plucks + bright pads; bars 14–15 thinned, low; bars 16–19 warm piano chords, resolve on D, ring out.
- SFX (soft, never harsh): glass taps on text reveals, tap on the CTA, soft key clicks while typing, send swoosh + pop, 5 airy pops on the lane landings, clock ticks in the race, a bell chime on the first reply, shimmer on the appointment card, muted thuds on the late replies, one low soft tone on "çok geç", shimmer on the equation and the final sweep.
