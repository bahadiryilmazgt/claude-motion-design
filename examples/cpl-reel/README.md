# CPL reel (TR, 9:16, 30 s)

"Lead başı maliyet neden tek başına yeterli değildir?" A performance-marketing Reel/Short in Turkish: dark navy, gold and cream, built with the same `seek(t)` HTML engine as the Howseen example.

Final file: [`cpl-reel-final.mp4`](cpl-reel-final.mp4) (1080×1920, 30 fps, H.264 + AAC, −14 LUFS). Overview: [`contact.png`](contact.png). All campaign numbers are illustrative and labelled "Örnek veri" on screen.

| Time | Scene |
|---|---|
| 0–3.7 s | Hook: "Düşük CPL = Başarılı Reklam mı?", CPL card counting €25 → €10 with a falling sparkline and a −%60 chip, then the "Her zaman değil." hit on the music drop |
| 3.7–11 s | Campaign A funnel: 100 lead / €10 CPL → 20 qualified → 2 sales, gold particles thinning tier by tier, attention moving to "Sadece 2 satış", €500 per sale |
| 11–16.3 s | Campaign B beside A: 60 lead / €18 CPL → 30 → 8 sales, live sales bar chart |
| 16.3–17.8 s | Comparison: €10 CPL → 2 Satış vs €18 CPL → 8 Satış, 4× slam, cost per sale €500 vs €135 |
| 17.8–24.4 s | Metric chain CPL → Lead Kalitesi → Satış Oranı → Müşteri Edinme Maliyeti → Ciro/ROAS, "CPL sadece başlangıçtır." |
| 24.4–26.8 s | "Asıl soru: Bu lead'ler satışa dönüşüyor mu?" |
| 26.8–30 s | "Reklam performansını lead ile değil, sonuçla ölç." |

## Rebuild

```bash
pip install edge-tts numpy faster-whisper   # faster-whisper only for the intelligibility check
python fetch_assets.py                       # Mixkit music/SFX + fonts
python vo.py                                 # Turkish VO (tr-TR-EmelNeural) + word timings -> assets/vo/
python -m http.server 8771 &                 # serve the film
node render.mjs probe 1 8 16.6 29.7          # stills -> probe/sheet.png
for k in 0 1 2 3; do node render.mjs chunk $k 4 & done; wait   # 4 parallel chunks, 4 subframes/frame
node render.mjs encode                       # tmix motion blur -> out/video.mp4
python audio.py                              # VO + ducked music + SFX by peak -> out/audio.wav
ffmpeg -i out/video.mp4 -i out/audio.wav -map 0:v -map 1:a \
  -vf "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p" -c:v libx264 -crf 16 \
  -color_range tv -colorspace bt709 -c:a aac -b:a 256k -movflags +faststart -t 30 out/cpl-reel-final.mp4
```

Voice: Microsoft Edge neural TTS (Emel), CPL written "si-pi-el" so it is read the way Turkish marketers say it. Music: Mixkit "Cat Walk" (Arulo), started at 11.88 s so its drop lands on "Her zaman değil". SFX: Mixkit, plus synthesized counter ticks and thuds.
